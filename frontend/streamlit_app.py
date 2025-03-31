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
    st.markdown("### Job Details")
    st.write("Enter common job application details that will be used for generating resume suggestions, drafting cover letter and connection requests. ")
    with st.form("job_application_form"):
        job_description = st.text_area("Enter Job Description:", height=150)
        company = st.text_input("Enter Company Name:")
        job_title = st.text_input("Enter Job Title:")
        resume_file = st.file_uploader("Upload Resume (PDF):", type=["pdf"])
        submitted_app = st.form_submit_button("Save Application Details")
    
    if submitted_app:
        st.session_state.job_description = job_description
        st.session_state.company = company
        st.session_state.job_title = job_title
        st.success("Job application details saved!")
        st.markdown("#### Saved Application Details")
        st.write("Job Description:", st.session_state.job_description)
        st.write("Company:", st.session_state.company)
        st.write("Job Title:", st.session_state.job_title)
        if "resume_file" in st.session_state:
            st.write("Resume PDF uploaded succsesfully.")

st.markdown("---")
st.markdown("## Next Steps")

# Create three columns for the buttons
col1, col2, col3 = st.columns(3)

if col1.button("Resume Suggestions"):
    # For now, simply display a message
    st.write("Parsing current application data to Task 3 (Resume Optimization)...")
    # (Later, you can call the Task 3 endpoint using the session data, e.g., st.session_state.resume_file, st.session_state.job_description, st.session_state.company, st.session_state.job_title)

if col2.button("Cover Letter Generation"):
    st.write("Parsing current application data to Task 4 (Cover Letter Generation)...")
    # (Later, this will call the Task 4 endpoint using the stored resume text, job description, company, and job title)

if col3.button("Insider Connection Request"):
    st.write("Parsing current application data to Task 2 (LinkedIn Job Inquiry Request)...")
    # (Later, this will trigger the Task 2 endpoint using the stored job application details and the person's info)
