from datetime import date
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

Status = Literal["Pending", "Completed"]
Difficulty = Literal["Easy", "Medium", "Hard"]
Question = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9 _./-]*$",
    ),
]


def iso_date(value):
    if type(value) is date:
        return value
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() == value:
                return parsed
        except ValueError:
            pass
    raise ValueError("Use an ISO date in YYYY-MM-DD format")


ISODate = Annotated[date, BeforeValidator(iso_date)]


class Signup(BaseModel):
    username: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def email_fits_column(cls, value):
        if len(value) > 100:
            raise ValueError("Email must be at most 100 characters")
        return value

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class TaskCreate(BaseModel):
    task_date: ISODate
    ques_no: Question


class TaskDifficulty(BaseModel):
    difficulty: Difficulty


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ques_no: str
    task_date: date
    status: Status
    difficulty: Difficulty | None
    completed_at: date | None
    created_at: date | None

    @field_validator("status", mode="before")
    @classmethod
    def read_status(cls, value):
        return "Completed" if (value or "").strip().lower() == "completed" else "Pending"

    @field_validator("difficulty", mode="before")
    @classmethod
    def read_difficulty(cls, value):
        label = (value or "").strip().title()
        return label if label in {"Easy", "Medium", "Hard"} else None