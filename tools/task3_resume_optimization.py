import os
import openai
from dotenv import load_dotenv
from mcp.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Create a global OpenAI Client
client = openai.Client(api_key = os.getenv("OPENAI_API_KEY"))

# Initialize MCP
mcp = FastMCP("Agentic Tasks")

@mcp.tool()
def resume_optimization(resume_text: str, job_description: str) -> str:
    """
    Generates resume optimization suggestions based on the provided resume text and job description.
    The suggestions should:
      - Identify relevant keywords, phrases, and requirements from the job description.
      - Recommend natural ways to incorporate these into the existing resume.
      - Suggest rewording, emphasizing, or reordering existing projects, experiences, or skills.
      - Avoid fabricating any new information.
    """
    prompt = f"""
You are an expert in resume optimization and improving ATS compatibility.
The user has provided their current resume and a job description.
Provide clear, concise, and impactful suggestions to improve the resume.
Focus on:
- Identifying key keywords, phrases, and requirements from the job description.
- Recommending how to naturally incorporate these into the existing resume.
- Suggesting where existing projects, experiences, or skills can be reworded, emphasized, or reordered.
Do not invent any new experiences, skills, or projects.

Resume:
{resume_text}

Job Description:
{job_description}

Provide your suggestions:
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides resume optimization suggestions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    suggestions = response.choices[0].message.content.strip()
    return suggestions