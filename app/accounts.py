"""Accounts (register, login, sessions) and per-user favorites."""
import os
import secrets
import sqlite3
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from rdkit import Chem

from app import db, security

router = APIRouter(prefix="/api/v1")
db.init_db()

INSTRUCTOR_CODE = os.environ.get("INSTRUCTOR_CODE", "pharma-teacher")

MAX_FAILED_LOGINS = 5
LOCK_WINDOW_SECONDS = 600
_failed_logins = defaultdict(list)


def _check_not_locked(key):
    now = time.time()
    _failed_logins[key] = [t for t in _failed_logins[key] if now - t < LOCK_WINDOW_SECONDS]
    if len(_failed_logins[key]) >= MAX_FAILED_LOGINS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a few minutes.")


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field("student", pattern="^(student|instructor)$")
    invite_code: str | None = None


class LoginIn(BaseModel):
    username: str
    password: str


class FavoriteIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    smiles: str = Field(..., min_length=1, max_length=500)


def _token_from_header(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[7:].strip()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    token = _token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")
    with db.session() as c:
        row = c.execute(
            "SELECT u.id, u.username, u.role FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    return dict(row)


def require_instructor(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    return user


def _new_session(row):
    token = secrets.token_urlsafe(32)
    with db.session() as c:
        c.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, row["id"]))
    return {
        "token": token,
        "user": {"id": row["id"], "username": row["username"], "role": row["role"]},
    }


@router.post("/auth/register")
def register(body: RegisterIn):
    _check_not_locked("register:" + body.username.strip().lower())
    if body.role == "instructor" and body.invite_code != INSTRUCTOR_CODE:
        raise HTTPException(status_code=403, detail="Invalid instructor code")
    pw_hash, salt = security.hash_password(body.password)
    try:
        with db.session() as c:
            cur = c.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                (body.username, pw_hash, salt, body.role),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")
    return _new_session({"id": user_id, "username": body.username, "role": body.role})


@router.post("/auth/login")
def login(body: LoginIn):
    key = body.username.strip().lower()
    _check_not_locked(key)
    with db.session() as c:
        row = c.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    if row is None or not security.verify_password(body.password, row["password_hash"], row["salt"]):
        _failed_logins[key].append(time.time())
        raise HTTPException(status_code=401, detail="Wrong username or password")
    _failed_logins[key] = []
    return _new_session(row)


@router.delete("/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    token = _token_from_header(authorization)
    if token:
        with db.session() as c:
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"ok": True}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user


@router.get("/favorites")
def list_favorites(user: dict = Depends(current_user)):
    with db.session() as c:
        rows = c.execute(
            "SELECT id, name, smiles FROM favorites WHERE user_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/favorites")
def add_favorite(body: FavoriteIn, user: dict = Depends(current_user)):
    if Chem.MolFromSmiles(body.smiles) is None:
        raise HTTPException(status_code=422, detail="Invalid SMILES string")
    with db.session() as c:
        cur = c.execute(
            "INSERT INTO favorites (user_id, name, smiles) VALUES (?, ?, ?)",
            (user["id"], body.name, body.smiles),
        )
        fid = cur.lastrowid
    return {"id": fid, "name": body.name, "smiles": body.smiles}


@router.delete("/favorites/{fid}")
def delete_favorite(fid: int, user: dict = Depends(current_user)):
    with db.session() as c:
        c.execute("DELETE FROM favorites WHERE id = ? AND user_id = ?", (fid, user["id"]))
    return {"ok": True}
