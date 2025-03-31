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
if st.button("Start a new job application"):
    st.markdown("### Job Application Flow (Coming Soon)")
    st.write("Tasks 2, 3, and 4 for job applications will be implemented in the next phase of development.")
