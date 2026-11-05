import os
import tempfile

os.environ["PHARMA_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _token(name):
    r = client.post("/api/v1/auth/register", json={"username": name, "password": "secret123"})
    return r.json()["token"]


def test_assistant_requires_login():
    assert client.post("/api/v1/assistant/ask", json={"question": "What is an ester?"}).status_code == 401


def test_assistant_without_key_says_not_configured():
    t = _token("ai_user")
    r = client.post("/api/v1/assistant/ask", json={"question": "What is an ester?"},
                    headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 503


def test_login_locks_after_repeated_failures():
    _token("lock_user")
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"username": "lock_user", "password": "wrong1"})
    r = client.post("/api/v1/auth/login", json={"username": "lock_user", "password": "wrong1"})
    assert r.status_code == 429
