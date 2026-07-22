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
        "code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)',
        "language": "python",
        "simulate_non_determinism": True
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["gate_decision"] == "BLOCK"
    assert data["reason_code"] == "REPLAY_MISMATCH"
    assert data["matched_rule"] is not None
    assert data["matched_rule"]["id"] == "rule_sql_injection"
    assert data["applied_template_id"] == "template_sql_injection"
    assert data["patch_run_1"] != data["patch_run_2"]
    assert data["comparison"]["is_match"] is False
    assert data["comparison"]["run_1_hash"] != data["comparison"]["run_2_hash"]
    assert data["explanation"] == "Replay mismatch detected. Merge blocked because remediation output was not reproducible."

def test_mismatch_flag_toggle_behavior():
    code = 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)'

    # 1. simulate_non_determinism = False -> ALLOW and EVIDENCE_VERIFIED
    payload_false = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": False
    }
    res_false = client.post("/api/scan", json=payload_false)
    assert res_false.status_code == 200
    data_false = res_false.json()
    assert data_false["gate_decision"] == "ALLOW"
    assert data_false["reason_code"] == "EVIDENCE_VERIFIED"

    # 2. simulate_non_determinism = True -> BLOCK and REPLAY_MISMATCH
    payload_true = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": True
    }
    res_true = client.post("/api/scan", json=payload_true)
    assert res_true.status_code == 200
    data_true = res_true.json()
    assert data_true["gate_decision"] == "BLOCK"
    assert data_true["reason_code"] == "REPLAY_MISMATCH"
