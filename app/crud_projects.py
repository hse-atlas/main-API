from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.create_db import Project, SessionLocal

app = FastAPI(title="API для управления проектами")


# ---------------------------
# Pydantic-схемы
# ---------------------------
class ProjectBase(BaseModel):
    name: str
    description: str
    owner_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    # При обновлении изменять owner_id не нужно, т.к. по нему мы ищем проект.
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int

    class Config:
        from_attributes = True


# ---------------------------
# Зависимость для получения сессии БД
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# Эндпоинты
# ---------------------------

@app.post("/projects/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Создает новый проект.
    Ожидается JSON:
    {
        "name": "Название проекта",
        "description": "Описание проекта",
        "owner_id": id_админа
    }
    """
    db_project = Project(
        name=project.name,
        description=project.description,
        owner_id=project.owner_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.put("/projects/owner/{owner_id}", response_model=ProjectOut)
def update_project(owner_id: int, project: ProjectUpdate, db: Session = Depends(get_db)):
    """
    Обновляет проект.
    В JSON можно передать любые изменяемые поля:
    {
        "name": "Новое название проекта",
        "description": "Новое описание проекта"
    }
    """
    db_project = db.query(Project).filter(Project.owner_id == owner_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Обновляем только поля name и description
    if project.name is not None:
        db_project.name = project.name
    if project.description is not None:
        db_project.description = project.description

    db.commit()
    db.refresh(db_project)
    return db_project


@app.delete("/projects/owner/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(owner_id: int, db: Session = Depends(get_db)):
    """
    Удаляет проект, найденный по owner_id.
    """
    db_project = db.query(Project).filter(Project.owner_id == owner_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    db.delete(db_project)
    db.commit()
    return  # При статусе 204 тело ответа не возвращается


@app.get("/projects/owner/{owner_id}", response_model=List[ProjectOut])
def list_projects(owner_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список всех проектов, принадлежащих администратору с заданным owner_id.
    """
    projects = db.query(Project).filter(Project.owner_id == owner_id).all()
    if not projects:
        raise HTTPException(status_code=404, detail="Проекты не найдены")
    return projects


# ---------------------------
# Запуск приложения
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("crud_projects:app", host="127.0.0.1", port=8000, reload=True)
