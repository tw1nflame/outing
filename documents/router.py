import datetime
import os
from fastapi import Depends, HTTPException, Request
from templates import templates
from db import Document, get_db
from documents.models import DocumentCreate
from sqlalchemy.orm import Session
from fastapi import APIRouter
# import graphrag.api as api
# from graphrag.config.load_config import load_config
from pathlib import Path



router = APIRouter()

@router.post("/api/project/{project_id}/document")
async def create_document(project_id: int, data: DocumentCreate, db: Session = Depends(get_db)):
    # создаём запись в базе
    new_doc = Document(
        title=data.title,
        author=data.author,
        update_date=datetime.date.today(),
        project_id=project_id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # создаём папку, если не существует
    os.makedirs('documents_storage', exist_ok=True)

    # асинхронное сохранение файла
    file_path = f'documents_storage/{new_doc.id}.txt'
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(data.content)

    return {"status": "ok", "id": new_doc.id}

import aiofiles.os

@router.delete("/api/project/{project_id}/document/{document_id}")
async def delete_document(project_id: int, document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter_by(id=document_id, project_id=project_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден.")

    db.delete(document)
    db.commit()

    file_path = f"documents_storage/{document_id}.txt"
    try:
        await aiofiles.os.remove(file_path)
    except FileNotFoundError:
        pass  # если файла уже нет — молча игнорируем

    return {"status": "deleted"}

@router.get('/projects/{project_id}/document/{document_id}')
def document_endpoint(request: Request, document_id: int, project_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not document:
        return {"error": "Document not found"}

    content_path = f"documents_storage/{document.id}.txt"
    if os.path.exists(content_path):
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "Документ не найден в папке."

    document_data = {
        'id': document.id,
        'title': document.title,
        'author': document.author,
        'created_date': document.update_date.strftime('%Y-%m-%d'),
        'content': content
    }
    return templates.TemplateResponse("document.html", {'request': request, 'document': document_data, 'project_id': project_id})

@router.get('/project/{project_id}/documents')
def documents_endpoint(request: Request, project_id: int, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return templates.TemplateResponse("documents.html", {'request': request, 'documents': documents, 'project_id': project_id})


# @router.post('/projects/{project_id}/index')
# async def indexing(request: Request, project_id: int, db: Session = Depends(get_db)):
    
#     documents = db.query(Document).filter(Document.project_id == project_id).all()
    
#     if not documents:
#         raise HTTPException(status_code=404, detail="Проект не содержит документов")
    
#     file_paths = [
#         str(Path(f"documents_storage/{doc.id}.txt"))
#         for doc in documents
#         if await aiofiles.os.path.exists(f"documents_storage/{doc.id}.txt")
#     ]

#     rag_dir = Path(f"rag/{project_id}")
#     rag_dir.mkdir(parents=True, exist_ok=True)
    

#     graphrag_config = load_config(rag_dir)
#     graphrag_config.document_directory = str(rag_dir)
    
#     index_result = await api.build_index(
#         config=graphrag_config,
#         files=file_paths
#     )
    
#     return {"status": "indexing started"}