import datetime
import os
from fastapi import Depends, HTTPException, Request
from templates import templates
from db import Document, get_db
from documents.models import DocumentCreate
from sqlalchemy.orm import Session
from fastapi import APIRouter
from pathlib import Path
import aiofiles
import aiofiles.os
import graphrag.api as api
from graphrag.config.load_config import load_config
import shutil
import pandas as pd
import asyncio
from asyncio import Lock

# Создаем объекты для блокировки множественных запросов
autocomplete_locks = {}
chat_locks = {}
indexing_locks = {}


router = APIRouter()

BASE_DIR = Path("rag")

@router.post("/api/project/{project_id}/document")
async def create_document(project_id: int, data: DocumentCreate, db: Session = Depends(get_db)):
    # создаём запись в базе
    new_doc = Document(
        title=data.title,
        update_date=datetime.date.today(),
        project_id=project_id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # создаём нужную папку, если не существует: rag/{project_id}/input
    project_input_dir = BASE_DIR / str(project_id) / "input"
    project_input_dir.mkdir(parents=True, exist_ok=True)

    # путь к файлу
    file_path = project_input_dir / f"{new_doc.id}.txt"

    # асинхронное сохранение файла
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(data.content)

    return {"status": "ok", "id": new_doc.id}


@router.delete("/api/project/{project_id}/document/{document_id}")
async def delete_document(project_id: int, document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter_by(id=document_id, project_id=project_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден.")

    db.delete(document)
    db.commit()

    file_path = BASE_DIR / str(project_id) / "input" / f"{document_id}.txt"
    try:
        await aiofiles.os.remove(str(file_path))
    except FileNotFoundError:
        pass  # если файла нет, ничего не делаем

    return {"status": "deleted"}


@router.get('/projects/{project_id}/document/{document_id}')
def document_endpoint(request: Request, document_id: int, project_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not document:
        return {"error": "Document not found"}

    content_path = BASE_DIR / str(project_id) / "input" / f"{document.id}.txt"
    if content_path.exists():
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "Документ не найден в папке."

    document_data = {
        'id': document.id,
        'title': document.title,
        'created_date': document.update_date.strftime('%Y-%m-%d'),
        'content': content
    }
    return templates.TemplateResponse("document.html", {'request': request, 'document': document_data, 'project_id': project_id})


@router.get('/project/{project_id}/documents')
def documents_endpoint(request: Request, project_id: int, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return templates.TemplateResponse("documents.html", {'request': request, 'documents': documents, 'project_id': project_id})


@router.post('/projects/{project_id}/index')
async def indexing(request: Request, project_id: int, db: Session = Depends(get_db)):
    if project_id in indexing_locks and indexing_locks[project_id].locked():
        raise HTTPException(status_code=429, detail="Индексация уже запущена")
    
    if project_id not in indexing_locks:
        indexing_locks[project_id] = Lock()
    
    async with indexing_locks[project_id]:
        target_dir = Path(f"rag/{project_id}")
        target_dir.mkdir(parents=True, exist_ok=True)

        # Пути к исходным файлам
        settings_file = Path("rag/settings/settings.yaml")
        env_file = Path("rag/settings/.env")
        prompts_dir = Path("rag/settings/prompts")

        # Пути к целевым файлам
        target_settings_file = target_dir / "settings.yaml"
        target_env_file = target_dir / ".env"
        target_prompts_dir = target_dir / "prompts"

        try:
            # Копируем файлы, если они ещё не существуют
            if not target_settings_file.exists():
                shutil.copy2(settings_file, target_settings_file)

            if not target_env_file.exists():
                shutil.copy2(env_file, target_env_file)

            # Копируем папку prompts, если её нет
            if not target_prompts_dir.exists():
                shutil.copytree(prompts_dir, target_prompts_dir)

            graphrag_config = load_config(Path(f"rag/{project_id}"))
            index_result = await api.build_index(config=graphrag_config)
            return {"status": "indexing completed"}
        except Exception as e:
            print(f"Error in indexing: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/project/{project_id}/autocomplete")
async def autocomplete_document(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    if project_id in autocomplete_locks and autocomplete_locks[project_id].locked():
        raise HTTPException(status_code=429, detail="Previous request is still processing")
    
    if project_id not in autocomplete_locks:
        autocomplete_locks[project_id] = Lock()
    
    async with autocomplete_locks[project_id]:
        text = data.get('text', '')
        
        project_dir = Path(f"rag/{project_id}")
        if not project_dir.exists():
            raise HTTPException(status_code=400, detail="Project not indexed yet")
            
        try:
            # Загружаем необходимые файлы
            entities = pd.read_parquet(f"{project_dir}/output/entities.parquet")
            communities = pd.read_parquet(f"{project_dir}/output/communities.parquet")
            community_reports = pd.read_parquet(f"{project_dir}/output/community_reports.parquet")
            text_units = pd.read_parquet(f"{project_dir}/output/text_units.parquet")
            relationships = pd.read_parquet(f"{project_dir}/output/relationships.parquet")
            
            # Загружаем конфигурацию
            graphrag_config = load_config(project_dir)
            
            # Выполняем local search
            response, context = await api.local_search(
                config=graphrag_config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                covariates=None,
                community_level=2,
                response_type="Multiple Paragraphs",
                query= "Context: \n" + text + '\n' + 'Write the continuation'
            )
            
            print("Local Search Response:", response)
            
            return {
                "suggestion": response
            }
            
        except Exception as e:
            print(f"Error in autocomplete: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/project/{project_id}/chat")
async def chat_endpoint(project_id: int, data: dict):
    if project_id in chat_locks and chat_locks[project_id].locked():
        raise HTTPException(status_code=429, detail="Previous request is still processing")
    
    if project_id not in chat_locks:
        chat_locks[project_id] = Lock()
    
    async with chat_locks[project_id]:
        current_message = data.get('current_message', '')
        messages = data.get('messages')

        lines = ''

        for message in messages:
            lines += message + '\n'

        
        project_dir = Path(f"rag/{project_id}")
        if not project_dir.exists():
            raise HTTPException(status_code=400, detail="Project not indexed yet")
            
        try:
            # Загружаем необходимые файлы
            entities = pd.read_parquet(f"{project_dir}/output/entities.parquet")
            communities = pd.read_parquet(f"{project_dir}/output/communities.parquet")
            community_reports = pd.read_parquet(f"{project_dir}/output/community_reports.parquet")
            
            # Загружаем конфигурацию
            graphrag_config = load_config(project_dir)
            
            # Выполняем global search
            response, context = await api.global_search(
                config=graphrag_config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type="Multiple Paragraphs",
                query="Previous chat history: \n" + lines + "\nCurrent question \n" + current_message + "\nAnswer it"
            )
            
            print("Global Search Response:", response)
            
            return {
                "message": response,
                "type": "assistant"
            }
            
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            raise HTTPException(status_code=429, detail=str(e))