# tools/task2_inquiry.py

import os
import openai
from dotenv import load_dotenv
from mcp.fastmcp import FastMCP

# Load environment variables (OPENAI_API_KEY, etc.)
load_dotenv()

# Create a global OpenAI Client with your API key
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# def mcp_tool_decorator(func):
#     """
#     Example decorator if your 'mcp.tool()' is not directly importable.
#     Adjust as needed if you already have @mcp.tool() available.
#     """
#     return func
mcp = FastMCP("Agentic Tasks")

@mcp.tool()
def linkedin_job_inquiry_request(name: str, about_section: str = "", job_posting: str = "") -> str:
    """
    Generates a short LinkedIn job inquiry request (<300 characters).
    Incorporates the person's name, optional About section, and the job posting.
    Emphasizes that the user has already applied for the role.
    """

    user_content = f"""
You are an expert at writing short, personalized LinkedIn connection requests.
The user has already applied to a job at the person's company and wants to connect with {name}.

Requirements:
- Must remain under 300 characters total.
- Mention {name}'s background (from 'about_section') if available.
- State that the user has already applied for the job.
- Politely ask if they'd be open to a brief conversation.

About section: {about_section}
Job posting: {job_posting}

Write a concise, friendly LinkedIn connection request under 300 characters.
    """

    # Call the Chat Completions endpoint
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
    )

    # Extract the generated text
    message = response.choices[0].message.content.strip()

    # Enforce 300-character limit
    if len(message) > 300:
        message = message[:300].rstrip()

    return message
