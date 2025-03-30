import os
import io
import openai
import PyPDF2
import datetime
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from mcp.client import mcp_instance
from dotenv import load_dotenv

#Import Tools
from tools.task1_connection import generate_linkedin_connection_request
from tools.task2_inquiry import linkedin_job_inquiry_request
from tools.task3_resume_optimization import resume_optimization
from tools.task4_cover_letter import generate_cover_letter_initial, generate_cover_letter_final

from models.models import Person, JobApplication, ResumeSuggestion, CoverLetter, JobInquiry

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the FastAPI app
app = FastAPI()
# Create databse tables on startup
init_db()

# Dependency to get DB session
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
def test_db(db:Session = Depends(get_db)):
    # Simple test to check connection
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_connection":result}

# Pydantic model for taks 1
class LinkedInRequest(BaseModel):
    name:str
    role: str
    company: str
    about_section: str | None = None

# FastAPI Route for Task 1
@app.post("/task1/linkedin-request")
def create_linkedin_request_endpoint(request: LinkedInRequest, db: Session = Depends(get_db)):
    """
    Endpoint to generate a LinkedIn connection request.
    Expects JSON with 'name' and optional 'about_section'.
    """
    generated_message = generate_linkedin_connection_request(
        name=request.name,
        about_section=request.about_section or ""
    )
    person = Person(
        name = request.name,
        role=request.role,
        company=request.company,
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

# Pydantic model for task 2
class LinkedInJobInquiryRequest(BaseModel):
    name: str
    role: str
    company: str
    about_section: str | None = None
    job_posting: str

# FastAPI Route for Task 2
@app.post("/task2/job-inquiry")
def create_job_inquiry(request: LinkedInJobInquiryRequest, db:Session = Depends(get_db)):
    """
    Endpoint to generate a LinkedIn connection request for a job inquiry.
    Expects JSON with 'name', optional 'about_section', and 'job_posting'.
    """
    generated_message = linkedin_job_inquiry_request(
        name=request.name,
        about_section=request.about_section or "",
        job_posting=request.job_posting
    )
    # Check if the person already exists
    person = db.query(Person).filter(Person.name == request.name, Person.company == request.company).first()
    if not person:
        person = Person(
            name=request.name,
            role=request.role,
            company=request.company,
            message_sent=""
        )
        db.add(person)
        db.commit()
        db.refresh(person)
    # Create a JobApplication record using the job posting as job_description; using a default job_title.
    job_app = JobApplication(
        company=request.company,
        job_title="Job Inquiry",
        job_description=request.job_posting,
        date_applied=datetime.date.today()
    )
    db.add(job_app)
    db.commit()
    db.refresh(job_app)
    # Create a JobInquiry record linking the person and job application
    job_inquiry = JobInquiry(
        person_id=person.id,
        job_application_id=job_app.id,
        date_reached_out=datetime.date.today(),
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

# FastAPI Route for Task 3
@app.post("/task3/resume-optimization-pdf")
async def resume_optimization_pdf(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    company: str = Form(...),
    job_title: str = Form(...),
    date_applied: str = Form(None),  # Format YYYY-MM-DD; optional
    db: Session = Depends(get_db)
):
    """
    Accepts a PDF file for the resume and a job description.
    Extracts text from the PDF and generates optimization suggestions.
    """
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
        # Parse date_applied or default to today
        if date_applied:
            date_obj = datetime.datetime.strptime(date_applied, "%Y-%m-%d").date()
        else:
            date_obj = datetime.date.today()
        # Create a new JobApplication record
        job_app = JobApplication(
            company=company,
            job_title=job_title,
            job_description=job_description,
            date_applied=date_obj
        )
        db.add(job_app)
        db.commit()
        db.refresh(job_app)
        # Create a ResumeSuggestion record linked to the job application
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
    
# Pydantic model for integrated cover letter task
class CoverLetterRequest(BaseModel):
    resume_text: str
    job_description: str
    company: str
    job_title: str
    follow_up_answers: str | None = None

# Fast API route for Task 4
@app.post("/task4/cover-letter")
def integrated_cover_letter_endpoint(request: CoverLetterRequest, db: Session = Depends(get_db)):
    """
    Single endpoint to handle cover letter generation.
    If 'follow_up_answers' is provided, generates the final cover letter.
    If not, generates an initial response which may be a cover letter or a set of follow-up questions.
    """
    if request.follow_up_answers is None:
        result = generate_cover_letter_initial(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        if result.get("follow_up_needed"):
            return {
                "follow_up_needed": True,
                "questions": result.get("questions", [])
            }
        else:
            cover_letter_text = result.get("cover_letter")
    else:
        cover_letter_text = generate_cover_letter_final(
            resume_text=request.resume_text,
            job_description=request.job_description,
            follow_up_answers=request.follow_up_answers
        )
    # Create a new JobApplication record
    job_app = JobApplication(
        company=request.company,
        job_title=request.job_title,
        job_description=request.job_description,
        date_applied=datetime.date.today()
    )
    db.add(job_app)
    db.commit()
    db.refresh(job_app)
    # Create a CoverLetter record linked to the job application
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