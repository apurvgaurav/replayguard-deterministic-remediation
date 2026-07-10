from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sql_injection_scenario_remediation():
    payload = {
        "code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)',
        "language": "python",
        "scenario_id": "sql_injection",
        "simulate_non_determinism": False
    }

    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["gate_decision"] == "ALLOW"
    assert data["matched_rule"]["id"] == "rule_sql_injection"
    assert data["applied_template_id"] == "template_sql_injection"
    assert data["comparison"]["is_match"] is True
    assert data["patch_run_1"] == data["patch_run_2"]
    assert data["ledger_record"]["gate_decision"] == "ALLOW"


def test_hardcoded_secret_remediation():
    payload = {
        "code": 'def connect_api():\n    API_KEY = "abc123secret"\n    return connect(API_KEY)',
        "language": "python",
        "scenario_id": "hardcoded_secret",
        "simulate_non_determinism": False
    }

    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["gate_decision"] == "ALLOW"
    assert data["matched_rule"]["id"] == "rule_hardcoded_secret"
    assert data["applied_template_id"] == "template_hardcoded_secret"
    assert "os.getenv" in data["remediated_code"]
    assert data["comparison"]["is_match"] is True


def test_unsafe_shell_remediation():
    payload = {
        "code": 'import subprocess\n\ndef cleanup_temp(path):\n    subprocess.run("rm -rf " + path, shell=True)',
        "language": "python",
        "scenario_id": "unsafe_shell",
        "simulate_non_determinism": False
    }

    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["gate_decision"] == "ALLOW"
    assert data["matched_rule"]["id"] == "rule_unsafe_shell"
    assert data["applied_template_id"] == "template_unsafe_shell"
    assert 'shell=False' in data["remediated_code"]
    assert data["comparison"]["is_match"] is True
