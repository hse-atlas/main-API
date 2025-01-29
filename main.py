from fastapi import FastAPI

app = FastAPI()


# Главная страница
@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в мой REST API"}


# Получение данных о пользователе
@app.get("/users/{user_id}")
def read_user(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}


# Создание нового пользователя
@app.post("/users/")
def create_user(name: str):
    return {"message": f"Пользователь {name} создан"}


# Обновление данных пользователя
@app.put("/users/{user_id}")
def update_user(user_id: int, name: str):
    return {"message": f"Пользователь {user_id} теперь {name}"}


# Удаление пользователя
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    return {"message": f"Пользователь {user_id} удален"}
