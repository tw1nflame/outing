from sqlalchemy import Column, Integer, String, Date, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    documents = relationship("Document", back_populates="project")


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    update_date = Column(Date, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))

    project = relationship("Project", back_populates="documents")


DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




def init_db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    # Добавим данные, если пусто
    if not session.query(Project).first():
        project1 = Project(title="123")
        project2 = Project(title="321")
        session.add_all([project1, project2])
        session.commit()

        doc1 = Document(
            title="Отчет за 2023 год",
            author="Иванов И.И.",
            update_date=datetime.date(2023, 12, 31),
            project_id=project1.id
        )
        doc2 = Document(
            title="Техническое задание",
            author="Петров П.П.",
            update_date=datetime.date(2023, 11, 15),
            project_id=project1.id
        )
        session.add_all([doc1, doc2])
        session.commit()

        os.makedirs("documents", exist_ok=True)

        with open(f"documents_storage/{doc1.id}.txt", "w", encoding="utf-8") as f:
            f.write("Это содержимое Отчета за 2023 год.")

        with open(f"documents_storage/{doc2.id}.txt", "w", encoding="utf-8") as f:
            f.write("Это содержимое Технического задания.")

    session.close()

init_db()  # Инициализация базы данных


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()