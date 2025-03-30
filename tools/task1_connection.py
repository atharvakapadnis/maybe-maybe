import os
import openai
from dotenv import load_dotenv
from mcp.client import mcp_instance as mcp

# Load environment variables (OPENAI_API_KEY, etc.)
load_dotenv()

# Create a global OpenAI Client with your API key
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

@mcp.tool()
def generate_linkedin_connection_request(name: str, about_section: str = "") -> str:
    """
    Generates a short LinkedIn connection request (<300 characters)
    using the new OpenAI client interface (>=1.0.0).
    """
    user_content = f"""
You are an expert at writing short, personalized LinkedIn connection requests.
The user wants to connect with {name}. If there's an About section, mention it.
The message must be under 300 characters total.

About section: {about_section}

Write a concise, friendly LinkedIn connection request referencing their background.
Ensure it's under 300 characters.
    """

    # Call the Chat Completions endpoint
    response = client.chat.completions.create(
        model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
        max_tokens=100
    )

    # Extract the generated text
    message = response.choices[0].message.content.strip()

    # Safety check for 300 characters
    if len(message) > 300:
        message = message[:300].rstrip()

    return message
