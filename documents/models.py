from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    author: str
    content: str