import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import Signup

router = APIRouter()


@router.post("/signup")
def signup(user: Signup, db: Session = Depends(get_db)):
    email = str(user.email)

    record = User(
        username=user.username,
        email=email,
        password=bcrypt.hashpw(
            user.password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8"),
        role="User",
    )

    try:
        db.add(record)
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.query(User.id).filter(User.email == email).first():
            raise HTTPException(
                status_code=409,
                detail="Email already exists",
            ) from None
        raise

    db.refresh(record)
    return {
        "id": record.id,
        "username": record.username,
        "email": record.email,
    }