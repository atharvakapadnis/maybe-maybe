import streamlit as st
import requests

# Base URL for your FastAPI backend (ensure your backend is running at this address)
BASE_URL = "http://127.0.0.1:8000"

# ================================
# Page Title and Welcome Message
# ================================
st.title("Job Application Helper") 
st.write("This application is designed to help job seekers streamline tasks like generating connection requests, optimizing resumes, and creating cover letters.")

# ================================
# Task 1: General LinkedIn Connection Request
# ================================
st.header("Generate a General LinkedIn Connection Request")
with st.form("task1_form"):
    name = st.text_input("Enter Name:")
    role = st.text_input("Enter Role:")
    company = st.text_input("Enter Company:")
    about_section = st.text_area("About Section (Optional):", height=150)
    task1_submitted = st.form_submit_button("Generate Connection Request")

if task1_submitted:
    if not name or not role or not company:
        st.error("Please fill in the required fields: Name, Role, and Company.")
    else:
        payload = {
            "name": name,
            "role": role,
            "company": company,
            "about_section": about_section
        }
        try:
            response = requests.post(f"{BASE_URL}/task1/linkedin-request", json=payload)
            if response.status_code == 200:
                result = response.json()
                st.success("Generated Connection Request:")
                st.write(result["message"])
                st.info(f"Message Length: {result['length']} characters")
            else:
                st.error("Error generating connection request. Please try again.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# ================================
# Job Application Setup - Save New Job Application
# ================================
st.markdown("---")
st.header("Start a New Job Application")
st.write("Enter common job application details. These will be used for Tasks 2, 3, and 4.")

with st.form("job_application_form"):
    job_description = st.text_area("Enter Job Description:", height=150)
    app_company = st.text_input("Enter Company:")
    job_title = st.text_input("Enter Job Title:")
    date_applied = st.text_input("Enter Date Applied (YYYY-MM-DD, optional):")
    resume_file = st.file_uploader("Upload Resume (PDF):", type=["pdf"])
    submitted_app = st.form_submit_button("Save Application Details")

if submitted_app:
    if not job_description or not app_company or not job_title or not resume_file:
        st.error("Please fill in all required fields and upload your resume PDF.")
    else:
        # Call the /job-application endpoint to create a new job application record
        payload = {
            "job_description": job_description,
            "company": app_company,
            "job_title": job_title,
            "date_applied": date_applied  # If empty, backend will default
        }
        try:
            response = requests.post(f"{BASE_URL}/job-application", json=payload)
            if response.status_code == 200:
                result = response.json()
                st.success("Job application details saved!")
                st.session_state.job_application = result  # Save full details
                st.session_state.job_application_id = result.get("job_application_id")
                st.session_state.job_description = result.get("job_description")
                st.session_state.company = result.get("company")
                st.session_state.job_title = result.get("job_title")
                st.session_state.date_applied = result.get("date_applied")
                st.session_state.resume_file = resume_file.getvalue()  # Save PDF bytes
                st.markdown("#### Saved Application Details")
                st.write("Job Description:", st.session_state.job_description)
                st.write("Company:", st.session_state.company)
                st.write("Job Title:", st.session_state.job_title)
                st.write("Date Applied:", st.session_state.date_applied)
                st.write("Resume PDF uploaded: Yes")
            else:
                st.error("Error saving job application details. Please try again.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# ================================
# Next Steps: Show Task Buttons if Job Application is Saved
# ================================
if st.session_state.get("job_application_id") and st.session_state.get("resume_file"):
    st.markdown("---")
    st.markdown("## Next Steps for Your Job Application")
    col1, col2, col3 = st.columns(3)

    # ----- Task 3: Resume Optimization Suggestions -----
    if col1.button("Resume Suggestions"):
        # Check if cached suggestions exist
        if st.session_state.get("resume_suggestions"):
            st.success("Cached Resume Optimization Suggestions:")
            st.write(st.session_state.resume_suggestions)
            st.info(
                f"Job Application ID: {st.session_state.job_application_id}, "
                f"Resume Suggestion ID: {st.session_state.resume_suggestion_id}"
            )
        else:
            st.write("Processing Task 3 (Resume Optimization)...")
            files = {
                "resume_file": (
                    "resume.pdf",
                    st.session_state.resume_file,
                    "application/pdf"
                )
            }
            data = {
                "job_application_id": st.session_state.job_application_id,
                "job_description": st.session_state.job_description
            }
            try:
                response = requests.post(f"{BASE_URL}/task3/resume-optimization", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.resume_suggestions = result["suggestions"]
                    st.session_state.resume_suggestion_id = result["resume_suggestion_id"]
                    st.success("Resume Optimization Suggestions:")
                    st.write(result["suggestions"])
                    st.info(
                        f"Job Application ID: {result['job_application_id']}, "
                        f"Resume Suggestion ID: {result['resume_suggestion_id']}"
                    )
                else:
                    st.error("Error optimizing resume. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # ----- Task 4: Cover Letter Generation -----
    if col2.button("Cover Letter Generation"):
        # Check if cached cover letter exists
        if st.session_state.get("cover_letter_result"):
            st.success("Cached Generated Cover Letter:")
            st.write(st.session_state.cover_letter_result)
            st.info(f"Cover Letter Length: {len(st.session_state.cover_letter_result)} characters")
        else:
            files = {
                "resume_file": (
                    "resume.pdf",
                    st.session_state.resume_file,
                    "application/pdf"
                )
            }
            data = {
                "job_application_id": st.session_state.job_application_id,
                "job_description": st.session_state.job_description,
                "company": st.session_state.company,
                "job_title": st.session_state.job_title,
                "follow_up_answers": ""  # initially empty
            }
            try:
                response = requests.post(f"{BASE_URL}/task4/cover-letter", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("follow_up_needed"):
                        st.session_state.cover_letter_data = data
                        st.session_state.cover_letter_files = files
                        st.session_state.cover_letter_questions = result.get("questions", [])
                        st.session_state.cover_letter_initial = True
                    else:
                        st.session_state.cover_letter_result = result["cover_letter"]
                        st.success("Generated Cover Letter:")
                        st.write(result["cover_letter"])
                        st.info(f"Cover Letter Length: {result['length']} characters")
                    # If follow-up is required, follow-up form will be displayed below.
                else:
                    st.error("Error generating cover letter. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Follow-Up Form for Cover Letter Generation (if needed)
    if st.session_state.get("cover_letter_initial") and st.session_state.get("cover_letter_questions"):
        st.warning("Additional context is required for your cover letter:")
        st.write("Follow-Up Questions:")
        for question in st.session_state.cover_letter_questions:
            st.write("- " + question)
        with st.form("follow_up_form"):
            follow_up = st.text_area("Enter additional context here:")
            submitted_follow_up = st.form_submit_button("Submit Follow-Up Answers")
        if submitted_follow_up:
            st.session_state.cover_letter_data["follow_up_answers"] = follow_up
            try:
                response2 = requests.post(f"{BASE_URL}/task4/cover-letter", files=st.session_state.cover_letter_files, data=st.session_state.cover_letter_data)
                if response2.status_code == 200:
                    result2 = response2.json()
                    st.session_state.cover_letter_result = result2["cover_letter"]
                    st.success("Generated Cover Letter:")
                    st.write(result2["cover_letter"])
                    st.info(f"Cover Letter Length: {result2['length']} characters")
                    st.session_state.cover_letter_initial = False
                    st.session_state.pop("cover_letter_data")
                    st.session_state.pop("cover_letter_files")
                    st.session_state.pop("cover_letter_questions")
                else:
                    st.error("Error generating cover letter with follow-up answers. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # ----- Task 2: Insider Connection Request -----
    # Use a session flag to persist the form.
    if "show_task2_form" not in st.session_state:
        st.session_state.show_task2_form = False

    if col3.button("Insider Connection Request"):
        st.session_state.show_task2_form = True

    if st.session_state.get("show_task2_form"):
        st.markdown("### Insider Connection Request Details")
        with st.form("task2_form"):
            contact_name = st.text_input("Contact Name:")
            contact_role = st.text_input("Contact Role:")
            contact_about = st.text_area("Contact About Section (Optional):", height=100)
            contact_job_posting = st.text_area("Job Posting Details:", value=st.session_state.job_description, height=100)
            submitted_task2 = st.form_submit_button("Generate Insider Connection Request")
        if submitted_task2:
            if not contact_name or not contact_role or not st.session_state.company or not contact_job_posting:
                st.error("Please fill in the required fields: Contact Name, Contact Role, Company, and Job Posting.")
            else:
                payload = {
                    "job_application_id": st.session_state.job_application_id,
                    "contact_name": contact_name,
                    "contact_role": contact_role,
                    "about_section": contact_about,
                    "job_posting": contact_job_posting
                }
                try:
                    response = requests.post(f"{BASE_URL}/task2/job-inquiry", json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Generated Insider Connection Request:")
                        st.write(result["message"])
                        st.info(f"Message Length: {result['length']} characters")
                    else:
                        st.error("Error generating job inquiry request. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
