from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sql_injection_mismatch():
    payload = {
        "code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)',
        "language": "python",
        "simulate_non_determinism": True
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["gate_decision"] == "BLOCK"
    assert data["matched_rule"] is not None
    assert data["matched_rule"]["id"] == "rule_sql_injection"
    assert data["applied_template_id"] == "template_sql_injection"
    assert data["patch_run_1"] is not None
    assert data["patch_run_2"] is not None
    # Replays must mismatch
    assert data["patch_run_1"] != data["patch_run_2"]
    assert data["comparison"]["is_match"] is False
    assert data["comparison"]["diff"] is not None
    assert "ReplayGuard Non-Deterministic Seed" in data["patch_run_2"]
    assert data["comparison"]["run_1_hash"] != data["comparison"]["run_2_hash"]
    assert data["ledger_record"]["gate_decision"] == "BLOCK"

def test_replay_mismatch_block_scenario():
    payload = {
        "code": 'query = "SELECT * FROM users WHERE id = " + user_id',
        "language": "python",
        "simulate_non_determinism": False
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["gate_decision"] == "BLOCK"
    assert data["matched_rule"] is not None
    assert data["matched_rule"]["id"] == "rule_sql_injection"
    assert data["applied_template_id"] == "template_sql_injection"
    assert data["patch_run_1"] != data["patch_run_2"]
    assert data["comparison"]["is_match"] is False
    assert data["explanation"] == "Replay mismatch detected. Merge blocked because remediation output was not reproducible."
