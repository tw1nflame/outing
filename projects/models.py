from pydantic import BaseModel


class ProjectUpdate(BaseModel):
    title: str
