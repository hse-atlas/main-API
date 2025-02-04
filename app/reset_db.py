from app.create_db import engine, Base


def reset_database():
    # Удаляем все таблицы
    Base.metadata.drop_all(bind=engine)
    print("Все таблицы удалены.")

    # Создаем таблицы заново
    Base.metadata.create_all(bind=engine)
    print("Все таблицы созданы заново.")


if __name__ == "__main__":
    reset_database()
