import os
import io
import datetime
import PyPDF2
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
import openai

from app.database import SessionLocal, init_db
from mcp.client import mcp_instance as mcp

from tools.task1_connection import generate_linkedin_connection_request
from tools.task2_inquiry import linkedin_job_inquiry_request
from tools.task3_resume_optimization import resume_optimization
from tools.task4_cover_letter import generate_cover_letter_initial, generate_cover_letter_final

from models.models import Person, JobApplication, ResumeSuggestion, CoverLetter, JobInquiry

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Agentic Tasks API"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_connection": result}

# ---------------------------
# Task 1: LinkedIn Connection Request (Person Table)
# ---------------------------
class LinkedInRequest(BaseModel):
    name: str
    role: str
    company: str
    about_section: str | None = None

@app.post("/task1/linkedin-request")
def create_linkedin_request_endpoint(request: LinkedInRequest, db: Session = Depends(get_db)):
    generated_message = generate_linkedin_connection_request(
        name=request.name,
        about_section=request.about_section or ""
    )
    person = Person(
        contact_name=request.name,
        contact_role=request.role,
        contact_company=request.company,
        message_sent=generated_message
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return {
        "message": generated_message,
        "person_id": person.id,
        "length": len(generated_message)
    }

# ---------------------------
# Task 2: LinkedIn Job Inquiry Request (JobInquiry Table)
# ---------------------------
class LinkedInJobInquiryRequest(BaseModel):
    name: str
    role: str
    company: str
    about_section: str | None = None
    job_posting: str

@app.post("/task2/job-inquiry")
def create_job_inquiry(request: LinkedInJobInquiryRequest, db: Session = Depends(get_db)):
    generated_message = linkedin_job_inquiry_request(
        name=request.name,
        about_section=request.about_section or "",
        job_posting=request.job_posting
    )
    # Create a new JobApplication record
    job_app = JobApplication(
        company=request.company,
        job_title="Job Inquiry",  # Default title for inquiry applications
        job_description=request.job_posting,
        date_applied=datetime.datetime.utcnow()
    )
    db.add(job_app)
    db.commit()
    db.refresh(job_app)
    
    # Create a new JobInquiry record referencing the JobApplication
    job_inquiry = JobInquiry(
        job_application_id=job_app.id,
        contact_name=request.name,
        contact_role=request.role,
        date_reached_out=datetime.datetime.utcnow(),
        message_sent=generated_message
    )
    db.add(job_inquiry)
    db.commit()
    db.refresh(job_inquiry)
    return {
        "message": generated_message,
        "job_inquiry_id": job_inquiry.id,
        "length": len(generated_message)
    }

# ---------------------------
# Task 3: Resume Optimization Suggestions (ResumeSuggestion Table)
# ---------------------------
# This endpoint accepts a PDF file for the resume.
@app.post("/task3/resume-optimization")
async def resume_optimization_pdf(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    company: str = Form(...),
    job_title: str = Form(...),
    date_applied: str = Form(None),  # Format: YYYY-MM-DD, optional
    db: Session = Depends(get_db)
):
    try:
        file_contents = await resume_file.read()
        pdf_stream = io.BytesIO(file_contents)
        reader = PyPDF2.PdfReader(pdf_stream)
        extracted_text = ""
        for page in reader.pages:
            text_page = page.extract_text()
            if text_page:
                extracted_text += text_page
        suggestions = resume_optimization(
            resume_text=extracted_text,
            job_description=job_description
        )
        if date_applied:
            date_obj = datetime.datetime.strptime(date_applied, "%Y-%m-%d")
        else:
            date_obj = datetime.datetime.utcnow()
        job_app = JobApplication(
            company=company,
            job_title=job_title,
            job_description=job_description,
            date_applied=date_obj
        )
        db.add(job_app)
        db.commit()
        db.refresh(job_app)
        resume_sugg = ResumeSuggestion(
            job_application_id=job_app.id,
            suggestions=suggestions
        )
        db.add(resume_sugg)
        db.commit()
        db.refresh(resume_sugg)
        return {
            "suggestions": suggestions,
            "job_application_id": job_app.id,
            "resume_suggestion_id": resume_sugg.id
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------------------
# Task 4: Cover Letter Generation (CoverLetter Table)
# ---------------------------
# For this endpoint, we accept a PDF resume and additional context if needed.
@app.post("/task4/cover-letter")
async def cover_letter_endpoint(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    company: str = Form(...),
    job_title: str = Form(...),
    follow_up_answers: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        file_contents = await resume_file.read()
        pdf_stream = io.BytesIO(file_contents)
        reader = PyPDF2.PdfReader(pdf_stream)
        resume_text = ""
        for page in reader.pages:
            text_page = page.extract_text()
            if text_page:
                resume_text += text_page
        if not follow_up_answers:
            result = generate_cover_letter_initial(
                resume_text=resume_text,
                job_description=job_description
            )
            if result.get("follow_up_needed"):
                return {"follow_up_needed": True, "questions": result.get("questions", [])}
            else:
                cover_letter_text = result.get("cover_letter")
        else:
            cover_letter_text = generate_cover_letter_final(
                resume_text=resume_text,
                job_description=job_description,
                follow_up_answers=follow_up_answers
            )
        # Save cover letter and associated job application in the database.
        job_app = JobApplication(
            company=company,
            job_title=job_title,
            job_description=job_description,
            date_applied=datetime.datetime.utcnow()
        )
        db.add(job_app)
        db.commit()
        db.refresh(job_app)
        cover_letter_record = CoverLetter(
            job_application_id=job_app.id,
            cover_letter=cover_letter_text
        )
        db.add(cover_letter_record)
        db.commit()
        db.refresh(cover_letter_record)
        return {
            "cover_letter": cover_letter_text,
            "job_application_id": job_app.id,
            "cover_letter_id": cover_letter_record.id,
            "length": len(cover_letter_text)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})