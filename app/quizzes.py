"""Quizzes: instructors create them, students take them, instructors see the results."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import db
from app.accounts import current_user, require_instructor

router = APIRouter(prefix="/api/v1")


class QuestionIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    choices: list[str] = Field(..., min_length=2, max_length=6)
    answer: int = Field(..., ge=0)


class QuizIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    questions: list[QuestionIn] = Field(..., min_length=1, max_length=50)


class SubmitIn(BaseModel):
    answers: list[int]


def _load(qid):
    with db.session() as c:
        row = c.execute("SELECT id, owner_id, title, questions_json FROM quizzes WHERE id = ?", (qid,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return row, json.loads(row["questions_json"])


@router.post("/quizzes")
def create_quiz(body: QuizIn, user: dict = Depends(require_instructor)):
    for q in body.questions:
        if q.answer >= len(q.choices):
            raise HTTPException(status_code=422, detail=f"Answer index out of range: {q.text}")
    payload = json.dumps([q.model_dump() for q in body.questions], ensure_ascii=False)
    with db.session() as c:
        cur = c.execute(
            "INSERT INTO quizzes (owner_id, title, questions_json) VALUES (?, ?, ?)",
            (user["id"], body.title, payload),
        )
        qid = cur.lastrowid
    return {"id": qid}


@router.get("/quizzes")
def list_quizzes(user: dict = Depends(current_user)):
    with db.session() as c:
        rows = c.execute("SELECT id, title, questions_json FROM quizzes ORDER BY id DESC").fetchall()
    return [{"id": r["id"], "title": r["title"], "count": len(json.loads(r["questions_json"]))} for r in rows]


@router.get("/quizzes/{qid}")
def get_quiz(qid: int, user: dict = Depends(current_user)):
    row, questions = _load(qid)
    if user["role"] != "instructor":
        questions = [{"text": q["text"], "choices": q["choices"]} for q in questions]
    return {"id": row["id"], "title": row["title"], "questions": questions}


@router.post("/quizzes/{qid}/submit")
def submit_quiz(qid: int, body: SubmitIn, user: dict = Depends(current_user)):
    row, questions = _load(qid)
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=422, detail="Answer count does not match the questions")
    correct = [q["answer"] for q in questions]
    score = sum(1 for given, right in zip(body.answers, correct) if given == right)
    with db.session() as c:
        c.execute(
            "INSERT INTO attempts (quiz_id, user_id, score, total) VALUES (?, ?, ?, ?)",
            (qid, user["id"], score, len(questions)),
        )
    return {"score": score, "total": len(questions), "correct": correct}


@router.get("/quizzes/{qid}/results")
def quiz_results(qid: int, user: dict = Depends(require_instructor)):
    row, _ = _load(qid)
    if row["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the quiz owner can see results")
    with db.session() as c:
        rows = c.execute(
            "SELECT a.score, a.total, a.created_at, u.username FROM attempts a "
            "JOIN users u ON u.id = a.user_id WHERE a.quiz_id = ? ORDER BY a.id DESC",
            (qid,),
        ).fetchall()
    return [dict(r) for r in rows]
