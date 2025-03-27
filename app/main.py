import os
import io
from fastapi import FastAPI, Depends, Body, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from mcp.fastmcp import FastMCP
from sqlalchemy import text
from dotenv import load_dotenv
import openai
import PyPDF2

#Import Tools
from tools.task1_connection import generate_linkedin_connection_request
from tools.task2_inquiry import linkedin_job_inquiry_request
from tools.task3_resume_optimization import resume_optimization
from tools.task4_cover_letter import generate_cover_letter_initial, generate_cover_letter_final

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the FastAPI app
app = FastAPI()
# Create databse tables on startup
init_db()
# Initialize MCP server for Agentic tasks
mcp = FastMCP("Agentic Tasks")

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
    about_section: str | None = None

# FastAPI Route for Task 1
@app.post("/task1/linkedin-request")
def create_linkedin_request_endpoint(request: LinkedInRequest):
    """
    Endpoint to generate a LinkedIn connection request.
    Expects JSON with 'name' and optional 'about_section'.
    """
    generated_message = generate_linkedin_connection_request(
        name=request.name,
        about_section=request.about_section or ""
    )
    return {
        "message": generated_message,
        "length": len(generated_message)
    }

# Pydantic model for task 2
class LinkedInJobInquiryRequest(BaseModel):
    name: str
    about_section: str | None = None
    job_posting: str

# FastAPI Route for Task 2
@app.post("/task2/job-inquiry")
def create_job_inquiry(request: LinkedInJobInquiryRequest):
    """
    Endpoint to generate a LinkedIn connection request for a job inquiry.
    Expects JSON with 'name', optional 'about_section', and 'job_posting'.
    """
    generated_message = linkedin_job_inquiry_request(
        name=request.name,
        about_section=request.about_section or "",
        job_posting=request.job_posting
    )
    return {
        "message": generated_message,
        "length": len(generated_message)
    }

# Pydantic model for task Task 3
class ResumeOptimizationRequest(BaseModel):
    resume_text: str
    job_description: str

# FastAPI Route for Task 3
@app.post("/task3/resume-optimization")
def resume_optimization_endpoint(request: ResumeOptimizationRequest):
    suggestions = resume_optimization(
        resume_text=request.resume_text,
        job_description=request.job_description
    )
    return {"suggestions": suggestions}

# New endpoint for PDF-based resume optimization
@app.post("/task3/resume-optimization-pdf")
async def resume_optimization_pdf(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Accepts a PDF file for the resume and a job description.
    Extracts text from the PDF and generates optimization suggestions.
    """
    try:
        file_contents = await resume_file.read()

        # Use PyPDF2 to extract text
        reader = PyPDF2.PdfReader(io.BytesIO(file_contents))
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() or ""

            # Generate suggestions using the extracted text and job description
            suggestions = resume_optimization(
                resume_text=extracted_text,
                job_description=job_description
            )
            return {"suggestions": suggestions}
    except Exception as e:
        return JSONResponse(status_code = 500, content={"error": str(e)})
    
# Pydantic model for initial cover letter requet
class CoverLetterRequest(BaseModel):
    resume_text: str
    job_description: str

@app.post("/task4/cover-letter")
def cover_letter_initial_endpoint(request: CoverLetterRequest):
    """
    Endpoint to generate a personalized cover letter.
    Returns either:
      - A cover letter (if sufficient context is provided), OR
      - A set of follow-up questions (if critical context is missing).
    """
    result = generate_cover_letter_initial(
        resume_text=request.resume_text,
        job_description=request.job_description
    )
    return result

#Pydantic modell for final cover letter request
class CoverLetterFinalRequest(BaseModel):
    resume_text: str
    job_description: str
    follow_up_answers: str  # Answers provided by the user to the follow-up questions

@app.post("/task4/cover-letter-complete")
def cover_letter_final_endpoint(request: CoverLetterFinalRequest):
    """
    Endpoint to generate the final cover letter after receiving follow-up answers.
    """
    cover_letter = generate_cover_letter_final(
        resume_text=request.resume_text,
        job_description=request.job_description,
        follow_up_answers=request.follow_up_answers
    )
    return {"cover_letter": cover_letter, "length": len(cover_letter)}