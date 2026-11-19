import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from database import Base, engine
from routes import analytics, login, signup, tasks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if engine.dialect.name == "mysql":
        constraints = inspect(engine).get_unique_constraints("tasks")
        if not any(
            set(item["column_names"]) == {"ques_no", "task_date"}
            for item in constraints
        ):
            raise RuntimeError("Apply the tasks unique constraint described in README.md")
    yield


app = FastAPI(title="TaskFlow API", lifespan=lifespan)
for module in (signup, login, tasks, analytics):
    app.include_router(module.router)


@app.exception_handler(SQLAlchemyError)
def database_error(request: Request, exc: SQLAlchemyError):
    logger.error("Database request failed: %s", type(exc).__name__)
    if isinstance(exc, OperationalError):
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    return JSONResponse(status_code=500, content={"detail": "Database request failed"})


@app.exception_handler(RequestValidationError)
def invalid_request(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
        for item in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})