from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal,engine
from sqlalchemy.orm import Session
from models import User, Task, Base
from datetime import date
from pydantic import BaseModel
from typing import Literal

router = APIRouter()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/tasks/today")
def get_today_tasks(db: Session = Depends(get_db)):
    today = date.today()

    tasks = (
        db.query(Task)
        .filter(Task.task_date == today)
        .order_by(Task.id.asc())
        .all()
    )

    return [
        {
            "id": task.id,
            "ques_no": task.ques_no,
            "task_date": task.task_date.isoformat(),
            "status": task.status,
            "difficulty": task.difficulty,
            "completed_at": (
                task.completed_at.isoformat()
                if task.completed_at else None
            )
        }
        for task in tasks
    ]


class TaskUpdate(BaseModel):
    status: Literal["Pending", "Completed"]
    difficulty: Literal["Easy", "Medium", "Hard"] | None = None


@router.patch("/tasks/{task_id}")
def update(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.status = data.status
    task.difficulty = data.difficulty

    if task.status == "Completed":
        if task.completed_at is None:
            task.completed_at = date.today()
    else:
        task.completed_at = None

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "ques_no": task.ques_no,
        "task_date": task.task_date.isoformat(),
        "status": task.status,
        "difficulty": task.difficulty,
        "completed_at": (
            task.completed_at.isoformat()
            if task.completed_at else None
        )
    }