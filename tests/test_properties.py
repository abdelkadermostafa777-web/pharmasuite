from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_aspirin_properties():
    r = client.post("/api/v1/compounds/properties", json={"smiles": "CC(=O)Oc1ccccc1C(=O)O"})
    assert r.status_code == 200
    data = r.json()
    assert data["formula"] == "C9H8O4"
    assert abs(data["molecular_weight"] - 180.16) < 0.05
    assert data["passes_lipinski"] is True


def test_invalid_smiles_returns_422():
    r = client.post("/api/v1/compounds/properties", json={"smiles": "not_a_molecule((("})
    assert r.status_code == 422
