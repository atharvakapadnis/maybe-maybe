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
                "date_applied": ""  # optional
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
            # Prepare files and form data using session_state values.
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
                "follow_up_answers": ""  # initially empty
            }
            try:
                # Call the Task 4 endpoint with no follow-up answers
                response = requests.post(f"{BASE_URL}/task4/cover-letter", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    # If additional context is required, save intermediate state and display follow-up form.
                    if result.get("follow_up_needed"):
                        st.session_state.cover_letter_data = data
                        st.session_state.cover_letter_files = files
                        st.session_state.cover_letter_questions = result.get("questions", [])
                        st.session_state.cover_letter_initial = True
                    else:
                        st.success("Generated Cover Letter:")
                        st.write(result["cover_letter"])
                        st.info(f"Cover Letter Length: {result['length']} characters")
                else:
                    st.error("Error generating cover letter. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

        # If the initial cover letter call indicated that follow-up is needed,
        # display the follow-up questions and a form for additional context.
        if st.session_state.get("cover_letter_initial") and st.session_state.get("cover_letter_questions"):
            st.warning("Additional context is required for your cover letter:")
            st.write("Follow-Up Questions:")
            for question in st.session_state.cover_letter_questions:
                st.write("- " + question)
            with st.form("follow_up_form"):
                follow_up = st.text_area("Enter additional context here:")
                submitted_follow_up = st.form_submit_button("Submit Follow-Up Answers")
            if submitted_follow_up:
                # Update stored data with follow-up answers and re-call the endpoint.
                st.session_state.cover_letter_data["follow_up_answers"] = follow_up
                try:
                    response2 = requests.post(f"{BASE_URL}/task4/cover-letter", files=st.session_state.cover_letter_files, data=st.session_state.cover_letter_data)
                    if response2.status_code == 200:
                        result2 = response2.json()
                        st.success("Generated Cover Letter:")
                        st.write(result2["cover_letter"])
                        st.info(f"Cover Letter Length: {result2['length']} characters")
                        # Clear stored follow-up state
                        st.session_state.cover_letter_initial = False
                        st.session_state.pop("cover_letter_data")
                        st.session_state.pop("cover_letter_files")
                        st.session_state.pop("cover_letter_questions")
                    else:
                        st.error("Error generating cover letter with follow-up answers. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        # Task 2: Insider Connection Request (placeholder for now)
        if "show_task2_form" not in st.session_state:
            st.session_state.show_task2_form = False

    # When the user clicks the button, set the flag to show the form
        if col3.button("Insider Connection Request"):
            st.session_state.show_task2_form = True

        # If the flag is True, show the Task 2 form
        if st.session_state.get("show_task2_form"):
            st.markdown("### Insider Connection Request Details")
            with st.form("task2_form"):
                contact_name = st.text_input("Contact Name:")
                contact_role = st.text_input("Contact Role:")
                contact_about = st.text_area("Contact About Section (Optional):", height=100)
                # Pre-fill job posting with the saved job_description
                contact_job_posting = st.text_area("Job Posting Details:", value=st.session_state.job_description, height=100)
                submitted_task2 = st.form_submit_button("Generate Insider Connection Request")
            if submitted_task2:
                if not contact_name or not contact_role or not st.session_state.company or not contact_job_posting:
                    st.error("Please fill in the required fields: Contact Name, Contact Role, Company, and Job Posting.")
                else:
                    payload = {
                        "name": contact_name,
                        "role": contact_role,
                        "company": st.session_state.company,
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