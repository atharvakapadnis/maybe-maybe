import os
from fastapi import FastAPI, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from mcp.fastmcp import FastMCP
from sqlalchemy import text
from dotenv import load_dotenv
import openai
from tools.task1_connection import generate_linkedin_connection_request

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the FastAPI app
app = FastAPI()
# Create databse tables on startup
init_db()
# Initialize MCP server for Agentic tasks
mcp = FastMCP("AgenticTasks")

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