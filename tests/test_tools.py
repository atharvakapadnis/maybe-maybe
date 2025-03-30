# tests/test_tools.py

import os
import io
import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Import our MCP tool functions
from tools.task1_connection import generate_linkedin_connection_request
from tools.task2_inquiry import linkedin_job_inquiry_request
from tools.task3_resume_optimization import resume_optimization
from tools.task4_cover_letter import generate_cover_letter_initial, generate_cover_letter_final

# Import the FastAPI app for integration tests
from app.main import app

# Create a TestClient for FastAPI endpoint testing
client_app = TestClient(app)

# Dummy helper classes to simulate OpenAI responses
class DummyMessage:
    def __init__(self, content):
        self.content = content

class DummyChoice:
    def __init__(self, message):
        self.message = message

class DummyResponse:
    def __init__(self, choices):
        self.choices = choices

class TestMCPTools(unittest.TestCase):

    def test_available_routes(self):
        # Ensure our routes match our expected routes
        routes = [route.path for route in app.routes]
        expected_routes = [
            '/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc',
            '/', '/test-db', '/task1/linkedin-request', '/task2/job-inquiry',
            '/task3/resume-optimization-pdf', '/task4/cover-letter'
        ]
        for route in expected_routes:
            self.assertIn(route, routes, f"Route {route} not found in {routes}")

    # --- Task 1: LinkedIn Connection Request ---
    @patch("tools.task1_connection.client.chat.completions.create")
    def test_task1_linkedin_connection_request(self, mock_create):
        dummy = DummyResponse([DummyChoice(DummyMessage("Test LinkedIn Request."))])
        mock_create.return_value = dummy
        output = generate_linkedin_connection_request("Alice", "Experienced in data science.")
        self.assertEqual(output, "Test LinkedIn Request.")
        self.assertTrue(len(output) <= 300)

    # --- Task 2: LinkedIn Job Inquiry Request ---
    @patch("tools.task2_inquiry.client.chat.completions.create")
    def test_task2_linkedin_job_inquiry_request(self, mock_create):
        dummy = DummyResponse([DummyChoice(DummyMessage("Test Job Inquiry Request."))])
        mock_create.return_value = dummy
        output = linkedin_job_inquiry_request("Bob", "Expert in cloud computing.", "Job posting details here.")
        self.assertEqual(output, "Test Job Inquiry Request.")
        self.assertTrue(len(output) <= 300)

    # --- Task 3: Resume Optimization Suggestions ---
    @patch("tools.task3_resume_optimization.client.chat.completions.create")
    def test_task3_resume_optimization(self, mock_create):
        dummy = DummyResponse([DummyChoice(DummyMessage("Test resume optimization suggestions."))])
        mock_create.return_value = dummy
        output = resume_optimization("Test resume text.", "Test job description.")
        self.assertEqual(output, "Test resume optimization suggestions.")

    # --- Task 4: Cover Letter Initial (Sufficient Context) ---
    @patch("tools.task4_cover_letter.client.chat.completions.create")
    def test_task4_generate_cover_letter_initial_sufficient_context(self, mock_create):
        # Simulate output that is a final cover letter (does not start with "FOLLOW-UP:")
        dummy = DummyResponse([DummyChoice(DummyMessage("Test Cover Letter with sufficient context."))])
        mock_create.return_value = dummy
        result = generate_cover_letter_initial("Detailed resume text.", "Detailed job description.")
        self.assertIn("cover_letter", result)
        self.assertFalse(result.get("follow_up_needed", False))
    
    # --- Task 4: Cover Letter Initial (Insufficient Context) ---
    @patch("tools.task4_cover_letter.client.chat.completions.create")
    def test_task4_generate_cover_letter_initial_insufficient_context(self, mock_create):
        dummy_output = 'FOLLOW-UP: ["What draws you to this company or role personally?","Are there any projects from your resume you’d like to emphasize more?"]'
        dummy = DummyResponse([DummyChoice(DummyMessage(dummy_output))])
        mock_create.return_value = dummy
        result = generate_cover_letter_initial("Generic resume text.", "Generic job description.")
        self.assertTrue(result.get("follow_up_needed"))
        self.assertIsInstance(result.get("questions"), list)
    
    # --- Task 4: Cover Letter Final Generation ---
    @patch("tools.task4_cover_letter.client.chat.completions.create")
    def test_task4_generate_cover_letter_final(self, mock_create):
        dummy = DummyResponse([DummyChoice(DummyMessage("Test Final Cover Letter."))])
        mock_create.return_value = dummy
        output = generate_cover_letter_final("Detailed resume text.", "Detailed job description.", "Follow-up answers.")
        self.assertEqual(output, "Test Final Cover Letter.")

    # --- Integration Test: PDF-based Resume Optimization Endpoint using an actual resume PDF ---
    def test_pdf_resume_optimization_endpoint_with_actual_resume(self):
        # Replace with the actual path to your resume PDF
        pdf_path = "tests/data/my_resume.pdf"
        if not os.path.exists(pdf_path):
            self.skipTest("Actual resume PDF not found at tests/data/my_resume.pdf")
        with open(pdf_path, "rb") as f:
            actual_pdf = f.read()

        response = client_app.post(
            "/task3/resume-optimization-pdf",  # Updated endpoint
            files={"resume_file": ("my_resume.pdf", actual_pdf, "application/pdf")},
            data={"job_description": "Test job description for PDF input."}
        )
        self.assertEqual(response.status_code, 200, f"Response status: {response.status_code}. Response content: {response.content}")
        json_resp = response.json()
        self.assertIn("suggestions", json_resp)

if __name__ == "__main__":
    unittest.main()