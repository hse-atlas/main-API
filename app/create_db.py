from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Админ может иметь много проектов
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("admins.id"), nullable=False)

    # Добавляем связь для владельца проекта
    owner = relationship("Admin", back_populates="projects")
    # Проект может иметь множество пользователей
    users = relationship("User", back_populates="project")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Пользователь принадлежит проекту
    project = relationship("Project", back_populates="users")


def init_db():
    Base.metadata.create_all(bind=engine)
    print("База данных и таблицы созданы.")


if __name__ == '__main__':
    init_db()
