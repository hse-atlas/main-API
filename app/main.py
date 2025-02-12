from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware

# Импорт моделей и сессии из вашего модуля create_db
from app.create_db import Project, User, SessionLocal


# ----------------------------------------------------------------------------
# Создаем единый экземпляр приложения FastAPI
# ----------------------------------------------------------------------------
app = FastAPI(title="API для управления проектами и пользователями", debug=True)

# Настраиваем CORS (из второго файла)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Разрешаем все домены
    allow_credentials=True,
    allow_methods=["*"],    # Разрешаем все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],    # Разрешаем все заголовки
)


# ----------------------------------------------------------------------------
# Pydantic-модели (проект)
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# Pydantic-модели (пользователь)
# ----------------------------------------------------------------------------
class UserBase(BaseModel):
    login: str
    email: str
    password: str
    project_id: int


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    login: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True


class UsersProjectOut(BaseModel):
    project_id: int
    project_name: str
    project_description: str
    users: List[UserOut]


# ----------------------------------------------------------------------------
# Зависимость для получения сессии БД
# ----------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------------------------
# Эндпоинты CRUD для проектов (из первого файла)
# ----------------------------------------------------------------------------

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
    В JSON можно передать поля:
    {
        "name": "Новое название проекта",
        "description": "Новое описание проекта"
    }
    """
    db_project = db.query(Project).filter(Project.owner_id == owner_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")

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
    # При статусе 204 тело ответа не возвращается
    return


@app.get("/projects/owner/{owner_id}", response_model=List[ProjectOut])
def list_projects(owner_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список всех проектов, принадлежащих администратору с заданным owner_id.
    """
    projects = db.query(Project).filter(Project.owner_id == owner_id).all()
    if not projects:
        raise HTTPException(status_code=404, detail="Проекты не найдены")
    return projects


# ----------------------------------------------------------------------------
# Эндпоинты CRUD для пользователей (из второго файла)
# ----------------------------------------------------------------------------

@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Создает нового пользователя.
    Ожидается JSON:
    {
        "login": "Логин пользователя",
        "email": "Email пользователя",
        "password": "Пароль",
        "project_id": ID проекта, к которому привязан пользователь
    }
    """
    project = db.query(Project).filter(Project.id == user.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    db_user = User(
        login=user.login,
        email=user.email,
        password=user.password,
        project_id=user.project_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Возвращает пользователя по его ID.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user


@app.get("/users/project/{project_id}", response_model=UsersProjectOut)
def get_users_by_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    users = db.query(User).filter(User.project_id == project_id).all()
    return UsersProjectOut(
        project_id=project.id,
        project_name=project.name,
        project_description=project.description,
        users=users
    )


@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    Обновляет данные пользователя по его ID.
    Ожидается JSON с обновляемыми полями (login, email, password).
    Поле project_id изменять не допускается.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.login is not None:
        db_user.login = user.login
    if user.email is not None:
        db_user.email = user.email
    if user.password is not None:
        db_user.password = user.password

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Удаляет пользователя по его ID.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(db_user)
    db.commit()
    return  # При статусе 204 тело ответа не возвращается


# ----------------------------------------------------------------------------
# Точка входа в приложение
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
