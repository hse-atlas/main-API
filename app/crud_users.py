from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.create_db import User, Project, SessionLocal

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="API для управления пользователями", debug=True)

# Разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все домены (можно указать конкретные)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Разрешаем все заголовки
)

# ---------------------------
# Pydantic-схемы для пользователя
# ---------------------------
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
# Эндпоинты CRUD для пользователей
# ---------------------------

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


@app.get("/users/project/{project_id}", response_model=List[UserOut])
def get_users_by_project(project_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список пользователей, привязанных к конкретному проекту по project_id.
    """
    users = db.query(User).filter(User.project_id == project_id).all()
    if not users:
        raise HTTPException(status_code=404, detail="Пользователи для данного проекта не найдены")
    return users


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


# ---------------------------
# Запуск приложения
# ---------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.crud_users:app", host="127.0.0.1", port=8000, reload=True)
