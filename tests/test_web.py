from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_page_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "PharmaSuite Pro" in r.text


def test_elements_118():
    data = client.get("/api/v1/elements").json()
    assert len(data) == 118
    assert data[0]["symbol"] == "H"


def test_svg_and_3d():
    svg = client.post("/api/v1/compounds/svg", json={"smiles": "c1ccccc1"}).json()["svg"]
    assert "<svg" in svg
    mb = client.post("/api/v1/compounds/3d", json={"smiles": "CC(=O)Oc1ccccc1C(=O)O"}).json()["molblock"]
    assert "M  END" in mb


def test_formulation_maillard_alert():
    body = {"api": "dopamine", "api_pct": 5, "excipients": [{"key": "lactose", "pct": 70}]}
    res = client.post("/api/v1/formulation/check", json=body).json()
    assert any(a[1] == "rule_maillard" for a in res["alerts"])


def test_substructure_benzene():
    res = client.post("/api/v1/substructure", json={"fragment": "c1ccccc1"}).json()
    assert len(res["matches"]) >= 5
