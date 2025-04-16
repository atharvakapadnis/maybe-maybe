import os
import io
import datetime
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

import PyPDF2
from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
import openai

from app.database import SessionLocal, init_db
from mcp.client import mcp_instance as mcp
from mcp.fastapi_integration import register_mcp_tools
from tools.task1_connection import generate_linkedin_connection_request
from tools.task2_inquiry import linkedin_job_inquiry_request
from tools.task3_resume_optimization import resume_optimization
from tools.task4_cover_letter import (
    generate_cover_letter_initial,
    generate_cover_letter_final,
)
from models.models import (
    Person,
    JobApplication,
    ResumeSuggestion,
    CoverLetter,
    JobInquiry,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ensure that API key is set
if not openai.api_key:
    logger.error("OPENAI_API_KEY is not set in the environment variables")


# Define startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown: Close any resources
    logger.info("Application shutting down")


# Create the FastAPI app
app = FastAPI(
    title="Job Application Helper API",
    description="API for helping with job applications",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register MCP tools with FastAPI
register_mcp_tools(app, mcp, prefix="/tools")


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}


# Test database connection
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        # Execute a simple query
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful"}
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )


# ---------------------------
# Utility functions
# ---------------------------
async def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        pdf_stream = io.BytesIO(pdf_file)
        reader = PyPDF2.PdfReader(pdf_stream)
        extracted_text = ""
        for page in reader.pages:
            text_page = page.extract_text()
            if text_page:
                extracted_text += text_page
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Error extracting text from PDF: {str(e)}"
        )


# ---------------------------
# New Endpoint: Save Job Application
# ---------------------------
class JobApplicationRequest(BaseModel):
    job_description: str
    company: str
    job_title: str
    date_applied: Optional[str] = None


@app.post("/job-application")
def save_job_application(request: JobApplicationRequest, db: Session = Depends(get_db)):
    try:
        if request.date_applied:
            date_obj = datetime.datetime.strptime(request.date_applied, "%Y-%m-%d")
        else:
            date_obj = datetime.datetime.utcnow()
        job_app = JobApplication(
            company=request.company,
            job_title=request.job_title,
            job_description=request.job_description,
            date_applied=date_obj,
        )
        db.add(job_app)
        db.commit()
        db.refresh(job_app)
        return {
            "job_application_id": job_app.id,
            "company": job_app.company,
            "job_title": job_app.job_title,
            "job_description": job_app.job_description,
            "date_applied": str(job_app.date_applied),
        }
    except Exception as e:
        logger.error(f"Error saving job application: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error saving job application: {str(e)}"
        )


# Get all job applications
@app.get("/job-applications")
def get_job_applications(db: Session = Depends(get_db)):
    try:
        job_apps = db.query(JobApplication).all()
        return [
            {
                "job_application_id": job_app.id,
                "company": job_app.company,
                "job_title": job_app.job_title,
                "job_description": job_app.job_description,
                "date_applied": str(job_app.date_applied),
            }
            for job_app in job_apps
        ]
    except Exception as e:
        logger.error(f"Error retrieving job applications: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving job applications: {str(e)}"
        )


# Get job application by ID
@app.get("/job-application/{job_application_id}")
def get_job_application(job_application_id: int, db: Session = Depends(get_db)):
    try:
        job_app = (
            db.query(JobApplication)
            .filter(JobApplication.id == job_application_id)
            .first()
        )
        if job_app is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job application with ID {job_application_id} not found",
            )
        return {
            "job_application_id": job_app.id,
            "company": job_app.company,
            "job_title": job_app.job_title,
            "job_description": job_app.job_description,
            "date_applied": str(job_app.date_applied),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job application: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving job application: {str(e)}"
        )


# ---------------------------
# Task 1: LinkedIn Connection Request (Person Table)
# ---------------------------
class LinkedInRequest(BaseModel):
    name: str
    role: str
    company: str
    about_section: Optional[str] = None


@app.post("/task1/linkedin-request")
def create_linkedin_request_endpoint(
    request: LinkedInRequest, db: Session = Depends(get_db)
):
    try:
        generated_message = generate_linkedin_connection_request(
            name=request.name, about_section=request.about_section or ""
        )
        person = Person(
            contact_name=request.name,
            contact_role=request.role,
            contact_company=request.company,
            message_sent=generated_message,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return {
            "message": generated_message,
            "person_id": person.id,
            "length": len(generated_message),
        }
    except Exception as e:
        logger.error(f"Error creating LinkedIn request: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating LinkedIn request: {str(e)}"
        )


# ---------------------------
# Task 2: LinkedIn Job Inquiry Request (JobInquiry Table)
# ---------------------------
class LinkedInJobInquiryRequest(BaseModel):
    job_application_id: int
    contact_name: str
    contact_role: str
    about_section: Optional[str] = None
    job_posting: str


@app.post("/task2/job-inquiry")
def create_job_inquiry(
    request: LinkedInJobInquiryRequest, db: Session = Depends(get_db)
):
    try:
        # Check if job application exists
        job_app = (
            db.query(JobApplication)
            .filter(JobApplication.id == request.job_application_id)
            .first()
        )
        if job_app is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job application with ID {request.job_application_id} not found",
            )

        generated_message = linkedin_job_inquiry_request(
            name=request.contact_name,
            about_section=request.about_section or "",
            job_posting=request.job_posting,
        )
        job_inquiry = JobInquiry(
            job_application_id=request.job_application_id,
            contact_name=request.contact_name,
            contact_role=request.contact_role,
            date_reached_out=datetime.datetime.utcnow(),
            message_sent=generated_message,
        )
        db.add(job_inquiry)
        db.commit()
        db.refresh(job_inquiry)
        return {
            "message": generated_message,
            "job_inquiry_id": job_inquiry.id,
            "length": len(generated_message),
            "job_application_id": request.job_application_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job inquiry: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating job inquiry: {str(e)}"
        )


# ---------------------------
# Task 3: Resume Optimization Suggestions (ResumeSuggestion Table)
# ---------------------------
@app.post("/task3/resume-optimization")
async def resume_optimization_pdf(
    resume_file: UploadFile = File(...),
    job_application_id: int = Form(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Check if job application exists
        job_app = (
            db.query(JobApplication)
            .filter(JobApplication.id == job_application_id)
            .first()
        )
        if job_app is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job application with ID {job_application_id} not found",
            )

        file_contents = await resume_file.read()
        extracted_text = await extract_text_from_pdf(file_contents)

        suggestions = resume_optimization(
            resume_text=extracted_text, job_description=job_description
        )
        resume_sugg = ResumeSuggestion(
            job_application_id=job_application_id, suggestions=suggestions
        )
        db.add(resume_sugg)
        db.commit()
        db.refresh(resume_sugg)
        return {
            "suggestions": suggestions,
            "job_application_id": job_application_id,
            "resume_suggestion_id": resume_sugg.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing resume: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error optimizing resume: {str(e)}"
        )


# ---------------------------
# Task 4: Cover Letter Generation (CoverLetter Table)
# ---------------------------
@app.post("/task4/cover-letter")
async def cover_letter_endpoint(
    resume_file: UploadFile = File(...),
    job_application_id: int = Form(...),
    job_description: str = Form(...),
    company: str = Form(...),
    job_title: str = Form(...),
    follow_up_answers: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        # Check if job application exists
        job_app = (
            db.query(JobApplication)
            .filter(JobApplication.id == job_application_id)
            .first()
        )
        if job_app is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job application with ID {job_application_id} not found",
            )

        file_contents = await resume_file.read()
        resume_text = await extract_text_from_pdf(file_contents)

        if not follow_up_answers:
            result = generate_cover_letter_initial(
                resume_text=resume_text, job_description=job_description
            )
            if result.get("follow_up_needed"):
                return {
                    "follow_up_needed": True,
                    "questions": result.get("questions", []),
                }
            else:
                cover_letter_text = result.get("cover_letter")
        else:
            cover_letter_text = generate_cover_letter_final(
                resume_text=resume_text,
                job_description=job_description,
                follow_up_answers=follow_up_answers,
            )

        cover_letter_record = CoverLetter(
            job_application_id=job_application_id, cover_letter=cover_letter_text
        )
        db.add(cover_letter_record)
        db.commit()
        db.refresh(cover_letter_record)

        return {
            "cover_letter": cover_letter_text,
            "job_application_id": job_application_id,
            "cover_letter_id": cover_letter_record.id,
            "length": len(cover_letter_text),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error generating cover letter: {str(e)}"
        )
