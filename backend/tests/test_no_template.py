from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_template_review():
    payload = {
        "code": "def process_data(data):\n    # Simple non-vulnerable function\n    val = data.get('val', 0)\n    return val * 10",
        "language": "python",
        "simulate_non_determinism": False
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["gate_decision"] == "REVIEW"
    assert data["matched_rule"] is None
    assert data["applied_template_id"] is None
    assert data["patch_run_1"] is None
    assert data["patch_run_2"] is None
    assert data["comparison"]["is_match"] is True  # Treated as match since no patches are generated
    assert data["comparison"]["diff"] is None
    assert data["ledger_record"]["gate_decision"] == "REVIEW"

def test_no_template_review_scenario():
    payload = {
        "code": "eval(user_input)",
        "language": "python",
        "simulate_non_determinism": False
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["gate_decision"] == "REVIEW"
    assert data["matched_rule"] is not None
    assert data["matched_rule"]["id"] == "rule_unsafe_eval"
    assert data["applied_template_id"] is None
    assert data["remediated_code"] is None
    assert data["patch_run_1"] is None
    assert data["patch_run_2"] is None
    assert data["comparison"]["is_match"] is False
    assert data["explanation"] == "Violation detected, but no deterministic remediation template is available. Human review required."
