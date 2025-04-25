from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from templates import templates
from db import Project, Document, get_db
from documents.router import router as documents_router
from projects.router import router as projects_router



app = FastAPI()
app.include_router(documents_router)
app.include_router(projects_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def main_page(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return templates.TemplateResponse("main_page.html", {'request': request, 'projects': projects})






















