import os
import json
import openai
import io
from dotenv import load_dotenv
from mcp.fastmcp import FastMCP

# Load environment variables (including OPENAI_API_KEY)
load_dotenv()

# Create a global OpenAI Client using the new client interface (>=1.0.0)
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize MCP instance
mcp = FastMCP("AgenticTasks")

@mcp.tool()
def generate_cover_letter_initial(resume_text: str, job_description: str) -> dict:
    """
    Checks if sufficient context is provided to generate a personalized cover letter.
    If sufficient, returns the cover letter.
    If not, returns follow-up questions in a JSON array.
    """
    prompt = f"""
You are an expert cover letter writer. Given the resume and job description below, decide whether all necessary context for writing a personalized cover letter is provided.
Necessary context includes:
- Why the user is interested in this company/role.
- The user's tone preference (e.g., professional, friendly, passionate).
- Specific projects or achievements to emphasize.

If all necessary context is provided, output the cover letter in plain text (max 1 page) that includes the portfolio link: https://atharvakapadnis.vercel.app.
If any critical context is missing, output exactly: "FOLLOW-UP:" followed by a JSON array of follow-up questions.
Do not include any extra text.

Resume:
{resume_text}

Job Description:
{job_description}

Respond as described.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates cover letters or follow-up questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    output = response.choices[0].message.content.strip()
    if output.startswith("FOLLOW-UP:"):
        # Parse the JSON array following "FOLLOW-UP:"
        try:
            questions_str = output[len("FOLLOW-UP:"):].strip()
            questions = json.loads(questions_str)
            return {"follow_up_needed": True, "questions": questions}
        except Exception:
            return {"follow_up_needed": True, "questions": ["Please provide additional context such as your interest in the role, preferred tone, and key projects to emphasize."]}
    else:
        return {"cover_letter": output}

@mcp.tool()
def generate_cover_letter_final(resume_text: str, job_description: str, follow_up_answers: str) -> str:
    """
    Generates the final personalized cover letter using the resume, job description,
    and additional context provided in follow-up answers.
    """
    prompt = f"""
You are an expert cover letter writer. Using the resume, job description, and additional context provided below,
generate a personalized, engaging cover letter (max 1 page) that:
- Highlights relevant skills, achievements, and projects.
- Aligns with the company's mission, values, and goals.
- Showcases why the user is excited about the role.
- Includes the portfolio link: https://atharvakapadnis.vercel.app.
- Reflects the user's personality and tone based on the additional context.

Resume:
{resume_text}

Job Description:
{job_description}

Additional Context (follow-up answers):
{follow_up_answers}

Generate the cover letter accordingly.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes personalized cover letters."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    cover_letter = response.choices[0].message.content.strip()
    return cover_letter
