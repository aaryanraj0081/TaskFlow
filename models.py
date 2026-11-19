from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(500), nullable=False)
    role = Column(String(50), nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("ques_no", "task_date", name="uq_tasks_question_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ques_no = Column(String(100), nullable=False)
    task_date = Column(Date, nullable=False)
    status = Column(String(50), default="Pending", nullable=True)
    difficulty = Column(String(50), default="", nullable=True)
    completed_at = Column(Date, nullable=True)
    created_at = Column(Date, nullable=True)

class TaskProgress(Base):
    __tablename__ = "task_progress"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    difficulty = Column(String(50), nullable=False)
    completed_at = Column(Date, nullable=False)