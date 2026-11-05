"""Calls the FastAPI backend. Raises on network errors or HTTP errors."""
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def analyze_remote(smiles, timeout=5):
    body = json.dumps({"smiles": smiles}).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + "/api/v1/compounds/properties",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))
