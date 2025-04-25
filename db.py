import enum
from sqlalchemy import Column, Integer, String, Date, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os
from sqlalchemy import Column, Integer, Enum

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    documents = relationship("Document", back_populates="project")

# class IndexingStatusEnum(str, enum.Enum):
#     not_started = "not_started"
#     in_progress = "in_progress"
#     done = "done"
#     failed = "failed"

# class ProjectIndexingStatus(Base):
#     __tablename__ = "project_indexing_status"

#     project_id = Column(Integer, primary_key=True, index=True)
#     status = Column(Enum(IndexingStatusEnum), default=IndexingStatusEnum.not_started)

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    update_date = Column(Date, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))

    project = relationship("Project", back_populates="documents")


DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




def init_db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
   
    session.close()

init_db()  # Инициализация базы данных


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()