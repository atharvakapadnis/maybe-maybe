# test_models.py
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, Person, JobApplication, ResumeSuggestion, CoverLetter, JobInquiry

# Configure a test SQLite database (you can use another DB engine if needed)
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Create all tables defined in your models.py
Base.metadata.create_all(bind=engine)

# Create a new session for interacting with the database
session = SessionLocal()

# --- Testing the Person table (Task 1) ---
# Create a sample person record for a LinkedIn connection request
person = Person(
    name="Alex Johnson",
    role="Data Scientist",
    company="Tech Corp",
    message_sent="Hi Alex, I came across your profile and was really impressed by your work in AI-driven solutions. Let's connect!"
)
session.add(person)
session.commit()

# Query and print the person record to verify
queried_person = session.query(Person).filter_by(name="Alex Johnson").first()
print("Person Table Entry:")
print(f"Name: {queried_person.name}, Role: {queried_person.role}, Company: {queried_person.company}, Message: {queried_person.message_sent}")

# --- Testing the JobApplication, ResumeSuggestion, and CoverLetter tables (Tasks 2, 3, 4) ---
# Create a sample JobApplication record
job_app = JobApplication(
    company="Tech Corp",
    job_title="Data Scientist",
    job_description="Looking for an experienced Data Scientist with a focus on predictive analytics and machine learning.",
    date_applied=date.today()
)
session.add(job_app)
session.commit()

# Create a sample ResumeSuggestion record linked to the job application
resume_suggestion = ResumeSuggestion(
    job_application_id=job_app.id,
    suggestions="Emphasize your experience in predictive analytics and include measurable results."
)
session.add(resume_suggestion)
session.commit()

# Create a sample CoverLetter record linked to the job application
cover_letter = CoverLetter(
    job_application_id=job_app.id,
    cover_letter="Dear Hiring Manager, I am excited to apply for the Data Scientist role at Tech Corp..."
)
session.add(cover_letter)
session.commit()

# Create a sample JobInquiry record linking the person to the job application
job_inquiry = JobInquiry(
    person_id=queried_person.id,
    job_application_id=job_app.id,
    date_reached_out=date.today(),
    message_sent="Hi, I'm reaching out regarding the Data Scientist role at Tech Corp. I'd love to learn more about your team."
)
session.add(job_inquiry)
session.commit()

# Query and print job application details along with linked resume suggestion and cover letter
queried_job_app = session.query(JobApplication).filter_by(job_title="Data Scientist").first()
print("\nJob Application Entry:")
print(f"Company: {queried_job_app.company}, Job Title: {queried_job_app.job_title}, Date Applied: {queried_job_app.date_applied}")

# Resume Suggestion
if queried_job_app.resume_suggestion:
    print("Resume Suggestion:")
    print(queried_job_app.resume_suggestion.suggestions)

# Cover Letter
if queried_job_app.cover_letter:
    print("Cover Letter:")
    print(queried_job_app.cover_letter.cover_letter)

# Job Inquiry linking the person and job application
queried_inquiry = session.query(JobInquiry).filter_by(person_id=queried_person.id).first()
print("\nJob Inquiry Entry:")
print(f"Message Sent: {queried_inquiry.message_sent}")

# Close the session when done
session.close()
