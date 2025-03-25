from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from mcp.fastmcp import FastMCP
from sqlalchemy import text

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