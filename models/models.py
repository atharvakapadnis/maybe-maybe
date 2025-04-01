from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

# Base for the models
Base = declarative_base()

# Task 1: Person Table (LinkedIn Connection)
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True) 
    contact_name = Column(String, nullable=False)
    contact_role = Column(String, nullable=False)
    contact_company = Column(String, nullable=False)
    message_sent = Column(Text, nullable=True)  # Stores the connection request message sent to the person

# Task 2: Connection Request for Job Inquiry
class JobInquiry(Base):
    __tablename__ = "job_inquiries"
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    contact_name = Column(String, nullable=False)
    contact_role = Column(String, nullable=False)
    date_reached_out = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    message_sent = Column(Text, nullable=False)
    
    # Relationship back to JobApplication
    job_application = relationship("JobApplication", back_populates="job_inquiries")

# Shared Job Details Table: Job Application
class JobApplication(Base):
    __tablename__ = "job_applications"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    job_description = Column(Text, nullable=False)
    date_applied = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships to resume suggestions, cover letter, and inquiries
    resume_suggestion = relationship("ResumeSuggestion", back_populates="job_application", uselist=False)
    cover_letter = relationship("CoverLetter", back_populates="job_application", uselist=False)
    job_inquiries = relationship("JobInquiry", back_populates="job_application")

# Task 3: Resume Optimization
class ResumeSuggestion(Base):
    __tablename__ = "resume_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    suggestions = Column(Text)
    
    # Link back to the job application
    job_application = relationship("JobApplication", back_populates="resume_suggestion")

# Task 4: Cover Letter Generation
class CoverLetter(Base):
    __tablename__ = "cover_letters"
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    cover_letter = Column(Text, nullable=False)
    
    # Link back to the job application
    job_application = relationship("JobApplication", back_populates="cover_letter")