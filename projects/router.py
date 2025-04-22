from fastapi import APIRouter, Depends, HTTPException, Request
from templates import templates
from db import Project, get_db
from projects.models import ProjectUpdate
from sqlalchemy.orm import Session

router = APIRouter()


@router.post('/api/projects/')
async def create_project(data: ProjectUpdate, db: Session = Depends(get_db)):
    new_project = Project(title=data.title)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"id": new_project.id, "title": new_project.title}


@router.put('/api/projects/{project_id}')
async def rename_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    project.title = data.title
    db.commit()
    return {"id": project.id, "title": project.title}


@router.delete('/api/projects/{project_id}')
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    db.delete(project)
    db.commit()
    return {"detail": "Проект удален"}

@router.get('/project/{project_id}')
def project_endpoint(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}
    return templates.TemplateResponse("project.html", {'request': request, 'title': project.title, 'project_id': project.id})

