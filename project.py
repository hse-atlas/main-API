from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()


# Модель для входящих данных при создании и редактировании проекта
class Project(BaseModel):
    name: str
    description: str


# Модель для ответа, где id располагается первым
class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str


# Простое хранилище для проектов (словарь). В будущем надо подключить бд.
projects_db = {}
next_id = 1


@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: Project):
    """
    Создание нового проекта.
    Ожидается JSON:
    {
        "name": "Название проекта",
        "description": "Описание проекта"
    }
    """
    global next_id
    new_project = project.dict()
    new_project["id"] = next_id
    projects_db[next_id] = new_project
    next_id += 1
    return new_project


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project: Project):
    """
    Редактирование существующего проекта.
    Принимает JSON с новыми данными и идентификатор проекта в URL.
    """
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Проект не найден")

    updated_project = project.dict()
    updated_project["id"] = project_id
    projects_db[project_id] = updated_project
    return updated_project


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int):
    """
    Удаление проекта по его идентификатору.
    """
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Проект не найден")

    del projects_db[project_id]
    return None
