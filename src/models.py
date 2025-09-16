from sqlalchemy import Column, Integer, String, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base class to define tables
Base = declarative_base()

# Database connection (SQLite file)
engine = create_engine("sqlite:///jobs.db", future=True)

# Session factory
SessionLocal = sessionmaker(bind=engine, future=True)

# Table definition
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    link = Column(String)
    status = Column(String, default="interested", nullable=False)
    deadline = Column(Date)
    notes = Column(String)

# Function to create tables
def init_db():
    Base.metadata.create_all(engine)