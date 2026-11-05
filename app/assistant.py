"""AI tutor for pharmacy and chemistry questions. Needs ANTHROPIC_API_KEY to be set on the server."""
import os
import time
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.accounts import current_user

router = APIRouter(prefix="/api/v1")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("ASSISTANT_MODEL", "claude-haiku-4-5")
SYSTEM_PROMPT = (
    "You are a patient tutor for pharmacy and chemistry students. Explain reaction mechanisms, "
    "drug properties, formulation concepts and pharmaceutical calculations clearly and step by step. "
    "Answer in the same language as the question. You do not give medical advice or dosing for "
    "patients; for clinical questions, recommend consulting a qualified professional."
)
QUESTIONS_PER_HOUR = 20
_asked = defaultdict(list)


class AskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)


@router.post("/assistant/ask")
def ask(body: AskIn, user: dict = Depends(current_user)):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Assistant is not configured yet (missing API key).")

    now = time.time()
    recent = [t for t in _asked[user["id"]] if now - t < 3600]
    if len(recent) >= QUESTIONS_PER_HOUR:
        raise HTTPException(status_code=429, detail="Hourly question limit reached. Try again later.")
    recent.append(now)
    _asked[user["id"]] = recent

    try:
        resp = httpx.post(
            API_URL,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": MODEL,
                "max_tokens": 800,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": body.question}],
            },
            timeout=30,
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not reach the assistant service.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Assistant service returned an error.")

    blocks = resp.json().get("content", [])
    answer = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    return {"answer": answer}
