# auth_service.py

from datetime import datetime, timedelta

from fastapi import FastAPI, APIRouter, HTTPException, status, Response, Depends
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Session

# Импортируем объекты из create_db.py
from create_db import SessionLocal, User


# ------------------------------------------------------------------------------
# Настройки приложения
# ------------------------------------------------------------------------------
class Settings(BaseSettings):
    SECRET_KEY: str = "your_secret_key_here"  # Рекомендуется задать через .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    class Config:
        env_file = ".env"


settings = Settings()

# ------------------------------------------------------------------------------
# Функции для хеширования паролей и создания JWT-токена
# ------------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# ------------------------------------------------------------------------------
# Pydantic-схемы для входных данных
# ------------------------------------------------------------------------------
class UserRegisterData(BaseModel):
    email: EmailStr = Field(..., description="Почта пользователя")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль (от 5 до 50 символов)")
    login: str = Field(..., min_length=3, max_length=50, description="Логин пользователя")


class UserLoginData(BaseModel):
    email: EmailStr = Field(..., description="Почта пользователя")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль (от 5 до 50 символов)")


# ------------------------------------------------------------------------------
# Зависимость для получения сессии БД
# ------------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------------------
# FastAPI роутер и эндпоинты
# ------------------------------------------------------------------------------
router = APIRouter(prefix="/api/v1/AuthService", tags=["Auth API"])


@router.post("/user_register/{project_id}")
def user_register(
        project_id: int,
        user_data: UserRegisterData,
        db: Session = Depends(get_db)
) -> dict:
    """
    Регистрация пользователя в рамках проекта с id=project_id.
    Проверяется уникальность email и login.
    """
    # Проверяем, что нет пользователя с таким email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail already registered"
        )

    # Проверяем, что нет пользователя с таким login
    if db.query(User).filter(User.login == user_data.login).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        login=user_data.login,
        password=hashed_password,
        project_id=project_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registration completed!"}


@router.post("/user_login/{project_id}")
def user_login(
        project_id: int,
        user_data: UserLoginData,
        response: Response,
        db: Session = Depends(get_db)
) -> dict:
    """
    Авторизация пользователя в рамках проекта с id=project_id.
    Если пользователь найден, пароль верный и он привязан к данному проекту,
    возвращается JWT-токен.
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if user.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with the specified project"
        )

    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {"access_token": access_token, "refresh_token": None}


# ------------------------------------------------------------------------------
# Инициализация приложения FastAPI
# ------------------------------------------------------------------------------
app = FastAPI(debug=True)


@app.get("/")
def home_page():
    return {"message": "AuthService for users is working"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("user_login_and_register:app", host="0.0.0.0", port=8000, reload=True)
