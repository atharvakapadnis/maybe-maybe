import streamlit as st
import requests

# Base URL for your FastAPI backend (ensure your backend is running at this address)
BASE_URL = "http://127.0.0.1:8000"

# Page Title and Welcome Message
st.title("Job Application Helper")
st.write("This application is to help job seekers streamline some of the tasks they would do on a regular basis.")

# --- Task 1: General LinkedIn Connection Request ---
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

# --- Separator and New Job Application Button ---
st.markdown("---")
# ------------------------------------------
# Job Application Setup using st.session_state
# ------------------------------------------
# Initialize session state for new application if not already set
if "new_application" not in st.session_state:
    st.session_state.new_application = False

# Button to start new job application setup
if not st.session_state.new_application:
    if st.button("Start a new job application"):
        st.session_state.new_application = True

# Once new_application is True, show the application details form
if st.session_state.new_application:
    st.markdown("### New Job Application Setup")
    st.write("Enter common job application details that will be used for Tasks 2, 3, and 4.")
    with st.form("job_application_form"):
        job_description = st.text_area("Enter Job Description:", height=150)
        company = st.text_input("Enter Company:")
        job_title = st.text_input("Enter Job Title:")
        resume_file = st.file_uploader("Upload Resume (PDF):", type=["pdf"])
        submitted_app = st.form_submit_button("Save Application Details")
    
    if submitted_app:
        st.session_state.job_description = job_description
        st.session_state.company = company
        st.session_state.job_title = job_title
        if resume_file is not None:
            st.session_state.resume_file = resume_file.getvalue()  # Save PDF bytes
        st.success("Job application details saved!")
        st.markdown("#### Saved Application Details")
        st.write("Job Description:", st.session_state.job_description)
        st.write("Company:", st.session_state.company)
        st.write("Job Title:", st.session_state.job_title)
        if "resume_file" in st.session_state:
            st.write("Resume PDF uploaded: Yes")

    # Show the three buttons only if application details are saved
    if (
        st.session_state.get("job_description")
        and st.session_state.get("company")
        and st.session_state.get("job_title")
        and st.session_state.get("resume_file")
    ):
        st.markdown("---")
        st.markdown("## Next Steps for Your Job Application")
        col1, col2, col3 = st.columns(3)

        # Task 3: Resume Suggestions Integration
        if col1.button("Resume Suggestions"):
            st.write("Parsing current application data to Task 3 (Resume Optimization)...")
            files = {
                "resume_file": (
                    "resume.pdf",
                    st.session_state.resume_file,
                    "application/pdf"
                )
            }
            data = {
                "job_description": st.session_state.job_description,
                "company": st.session_state.company,
                "job_title": st.session_state.job_title,
                "date_applied": ""  # optional: can be set if needed
            }
            try:
                response = requests.post(
                    f"{BASE_URL}/task3/resume-optimization-pdf", files=files, data=data
                )
                if response.status_code == 200:
                    result = response.json()
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

        # Task 4: Cover Letter Generation (placeholder for now)
        if col2.button("Cover Letter Generation"):
            st.write("Parsing current application data to Task 4 (Cover Letter Generation)...")
            # Integration will be similar to Task 3, calling /task4/cover-letter endpoint

        # Task 2: Insider Connection Request (placeholder for now)
        if col3.button("Insider Connection Request"):
            st.write("Parsing current application data to Task 2 (LinkedIn Job Inquiry Request)...")
            # Integration will call /task2/job-inquiry endpoint with stored application details
