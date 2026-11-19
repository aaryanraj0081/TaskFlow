import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User

router = APIRouter()
bearer = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.environ["TASKFLOW_JWT_SECRET"]
if len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("TASKFLOW_JWT_SECRET must have at least 32 bytes")

ALGORITHM = "HS256"
SESSION_SECONDS = 3600
SESSION_COOKIE = "taskflow_session"
API_ORIGIN = os.getenv("TASKFLOW_API_ORIGIN", "http://localhost:8000").rstrip("/")
APP_URL = os.getenv("TASKFLOW_APP_URL", "http://localhost:8501").rstrip("/") + "/"


def account_info(account: User):
    role = account.role.strip().title()
    if role not in {"Admin", "User"}:
        raise HTTPException(403, "Invalid account role")
    return {"username": account.username, "role": role}


def verify_credentials(form: OAuth2PasswordRequestForm, db: Session):
    account = db.query(User).filter(User.email == form.username.strip()).one_or_none()
    password = form.password.encode("utf-8")
    try:
        matches = (
            account is not None
            and len(password) <= 72
            and bcrypt.checkpw(password, account.password.encode())
        )
    except ValueError:
        matches = False

    if not matches:
        raise HTTPException(
            401, "Invalid email or password", {"WWW-Authenticate": "Bearer"}
        )

    account_info(account)
    return account


def make_token(account: User):
    return jwt.encode(
        {
            "sub": str(account.id),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def current_account(token: str = Depends(bearer), db: Session = Depends(get_db)):
    unauthorized = HTTPException(
        401, "Sign in again to continue", {"WWW-Authenticate": "Bearer"}
    )
    try:
        claims = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        account_id = int(claims["sub"])
    except (JWTError, ValueError, TypeError):
        raise unauthorized from None

    if not 1 <= account_id <= 2_147_483_647:
        raise unauthorized

    account = db.get(User, account_id)
    if account is None:
        raise unauthorized

    account_info(account)
    return account


def require_admin(account: User = Depends(current_account)):
    if account_info(account)["role"] != "Admin":
        raise HTTPException(403, "Admin access required")
    return account


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    account = verify_credentials(form, db)
    return {
        "access_token": make_token(account),
        "token_type": "bearer",
        **account_info(account),
    }


@router.get("/me")
def me(account: User = Depends(current_account)):
    return account_info(account)


def require_same_origin(request: Request):
    if request.headers.get("origin") != API_ORIGIN:
        raise HTTPException(403, "Invalid request origin")


LOGIN_FORM = """
<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TaskFlow sign in</title>
<main><h1>TaskFlow sign in</h1>
<form method="post">
<p><label>Email <input type="email" name="username" autocomplete="username" required></label></p>
<p><label>Password <input type="password" name="password" autocomplete="current-password" required></label></p>
<button type="submit">Sign in</button>
</form></main></html>
"""


@router.get("/browser-login", response_class=HTMLResponse)
def browser_login_form():
    return LOGIN_FORM


@router.post("/browser-login", dependencies=[Depends(require_same_origin)])
def browser_login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        account = verify_credentials(form, db)
    except HTTPException as exc:
        if exc.status_code == 401:
            html = LOGIN_FORM.replace(
                "<form",
                '<p role="alert">Invalid email or password.</p><form',
                1,
            )
            return HTMLResponse(html, status_code=401)
        raise

    response = RedirectResponse(APP_URL, status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        make_token(account),
        max_age=SESSION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=API_ORIGIN.startswith("https://"),
    )
    return response


@router.get("/browser-logout", response_class=HTMLResponse)
def browser_logout_form():
    return """<!doctype html><html lang="en"><meta charset="utf-8">
<title>TaskFlow sign out</title><h1>Sign out of TaskFlow?</h1>
<form method="post"><button type="submit">Sign out</button></form></html>"""


@router.post("/browser-logout", dependencies=[Depends(require_same_origin)])
def browser_logout():
    response = RedirectResponse(APP_URL, status_code=303)
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        samesite="lax",
        secure=API_ORIGIN.startswith("https://"),
    )
    return response