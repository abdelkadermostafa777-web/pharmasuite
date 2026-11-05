import os
import tempfile

os.environ["PHARMA_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _register(name, role="student", code=None):
    body = {"username": name, "password": "secret123", "role": role}
    if code:
        body["invite_code"] = code
    return client.post("/api/v1/auth/register", json=body)


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_me():
    r = _register("student_one")
    assert r.status_code == 200
    token = r.json()["token"]
    assert client.get("/api/v1/auth/me", headers=_auth(token)).json()["username"] == "student_one"
    assert _register("student_one").status_code == 409
    bad = client.post("/api/v1/auth/login", json={"username": "student_one", "password": "wrong"})
    assert bad.status_code == 401


def test_protected_routes_need_login():
    assert client.get("/api/v1/favorites").status_code == 401


def test_favorites_roundtrip():
    token = _register("fav_user").json()["token"]
    r = client.post("/api/v1/favorites", json={"name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}, headers=_auth(token))
    assert r.status_code == 200
    fid = r.json()["id"]
    assert len(client.get("/api/v1/favorites", headers=_auth(token)).json()) == 1
    client.delete(f"/api/v1/favorites/{fid}", headers=_auth(token))
    assert client.get("/api/v1/favorites", headers=_auth(token)).json() == []


def test_instructor_quiz_flow():
    assert _register("teacher_bad", "instructor", "wrong").status_code == 403
    code = os.environ.get("INSTRUCTOR_CODE", "pharma-teacher")
    t_token = _register("teacher_one", "instructor", code).json()["token"]
    quiz = {"title": "Basics", "questions": [{"text": "2+2?", "choices": ["3", "4"], "answer": 1}]}
    s_quiz_token = _register("student_quiz").json()["token"]
    assert client.post("/api/v1/quizzes", json=quiz, headers=_auth(s_quiz_token)).status_code == 403
    qid = client.post("/api/v1/quizzes", json=quiz, headers=_auth(t_token)).json()["id"]
    s_token = _register("student_two").json()["token"]
    detail = client.get(f"/api/v1/quizzes/{qid}", headers=_auth(s_token)).json()
    assert "answer" not in detail["questions"][0]
    res = client.post(f"/api/v1/quizzes/{qid}/submit", json={"answers": [1]}, headers=_auth(s_token)).json()
    assert res["score"] == 1 and res["total"] == 1
    rows = client.get(f"/api/v1/quizzes/{qid}/results", headers=_auth(t_token)).json()
    assert rows[0]["username"] == "student_two"
