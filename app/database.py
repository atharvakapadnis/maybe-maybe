from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base

DATABASE_URL = "sqlite:///./agentic_tasks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocomit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadat.create_all(bind=engine)