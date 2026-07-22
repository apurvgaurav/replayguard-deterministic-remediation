import hashlib
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app, ledger_service, replay_controller
from app.models import LedgerRecord
from app.services.comparator import ByteComparator
from app.services.ledger import LedgerPersistenceError
from app.services.template_engine import TemplateEngine


template_engine = TemplateEngine()
client = TestClient(app)


def test_deterministic_template_hashing():
    """
    Verify template hash calculation is deterministic and matches canonical json structure.
    """
    template = {
        "id": "test_template",
        "rule_id": "test_rule",
        "version": "2.4.1",
        "search_pattern": "foo",
        "replace_pattern": "bar",
        "expected_match_count": 1
    }
    hash_1 = template_engine.compute_template_hash(template)

    # Re-ordered keys, same data -> must produce identical hash due to sort_keys=True
    template_reordered = {
        "expected_match_count": 1,
        "replace_pattern": "bar",
        "search_pattern": "foo",
        "version": "2.4.1",
        "rule_id": "test_rule",
        "id": "test_template"
    }
    hash_2 = template_engine.compute_template_hash(template_reordered)
    assert hash_1 == hash_2

    # Verify matches manual canonical JSON hashing
    canonical_str = json.dumps(template, sort_keys=True, separators=(",", ":"))
    expected_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    assert hash_1 == expected_hash


def test_template_metadata_propagation():
    """
    Verify scan response propagates actual template version, hash, and postconditions status.
    Assert template_hash equals compute_template_hash(actual_template).
    Verify ledger_record fields match top-level response fields.
    """
    code = 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)'
    payload = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": False
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["gate_decision"] == "ALLOW"
    assert data["reason_code"] == "EVIDENCE_VERIFIED"
    assert data["applied_template_id"] == "template_sql_injection"
    assert data["template_version"] == "1.0.0"
    assert data["template_postconditions_passed"] is True

    # Validate template_hash equals compute_template_hash(actual_template)
    actual_template = template_engine.get_template_for_rule("rule_sql_injection")
    assert actual_template is not None
    expected_hash = template_engine.compute_template_hash(actual_template)
    assert data["template_hash"] == expected_hash

    # Validate consistency between top-level scan response and ledger record
    assert data["ledger_record"]["reason_code"] == data["reason_code"]
    assert data["ledger_record"]["template_version"] == data["template_version"]
    assert data["ledger_record"]["template_hash"] == data["template_hash"]
    assert data["ledger_record"]["template_postconditions_passed"] == data["template_postconditions_passed"]


def test_ledger_record_persistence():
    """
    Verify reason_code and template metadata are properly written to and verified by LedgerService.
    """
    # 1. ALLOW Scenario
    code = 'def connect_api():\n    AWS_KEY = "aws_access_key_xyz123"\n    return connect(AWS_KEY)'
    payload = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": False
    }
    res = client.post("/api/scan", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Get the newest record from saved ledger
    history = ledger_service.get_history()
    newest = history[0]

    assert newest["record_id"] == data["ledger_record"]["record_id"]
    assert newest["gate_decision"] == "ALLOW"
    assert newest["reason_code"] == "EVIDENCE_VERIFIED"
    assert newest["template_version"] == "1.0.0"
    assert newest["template_hash"] is not None
    assert newest["template_postconditions_passed"] is True
    assert newest["evidence_persisted"] is True


def test_legacy_ledger_record_compatibility():
    """
    Verify that old ledger records missing new Phase 3 properties can still be read
    and parsed by LedgerRecord Pydantic model without throwing validation errors.
    """
    legacy_data = {
        "timestamp": "2026-07-09T20:25:00.983118",
        "original_code_hash": "60361c36d8123d1c3f58f642b5a821dbdb47be29522d94e2672caf5941e4d5e9",
        "rule_id": "rule_unsafe_shell",
        "template_id": "template_unsafe_shell",
        "patch_run_1_hash": "70a12e9b3316efd18e658c44cd79a72569f1426b64de086fa02b385bd8a9a1b3",
        "patch_run_2_hash": "70a12e9b3316efd18e658c44cd79a72569f1426b64de086fa02b385bd8a9a1b3",
        "gate_decision": "ALLOW",
        "ledger_hash": "cdf8757b83bd7d2a5d980004aabd96895c5405c909440855ba7b4c7d77f66395",
        "evidence_persisted": True,
        "record_id": "abc-123"
    }

    record = LedgerRecord(**legacy_data)
    assert record.record_id == "abc-123"
    assert record.reason_code is None
    assert record.template_version is None
    assert record.template_hash is None
    assert record.template_postconditions_passed is None


def test_correct_unified_diff_line_separation():
    """
    Regression test: Ensure removed and added lines are always separated by newlines,
    even if the inputs have no trailing newline character.
    """
    comparator = ByteComparator()

    patch_1 = 'def get_user(user_id):\n    return db.execute(query, params)'
    patch_2 = 'def get_user(user_id):\n    return db.execute(query)\n# ReplayGuard Controlled Fault Injection: abc'

    res = comparator.compare(patch_1, patch_2)
    assert res["is_match"] is False

    diff = res["diff"]
    assert diff is not None

    lines = diff.split("\n")
    # Verify diff headers and line change markings are separate items
    assert "--- patch_run_1.py" in lines
    assert "+++ patch_run_2.py" in lines
    # Ensure lines are separate and prefix matches
    assert "-    return db.execute(query, params)" in lines
    assert "+    return db.execute(query)" in lines
    assert "+# ReplayGuard Controlled Fault Injection: abc" in lines

    # Ensure no coalesced lines exist in the diff
    for line in lines:
        assert "-    return db.execute(query, params)+" not in line
        assert "+    return db.execute(query)+" not in line


def test_controlled_fault_injection_label():
    """
    Verify the fault injection label matches the renamed Phase 3 specification.
    """
    code = 'import subprocess\n\ndef clean(path):\n    subprocess.run("rm -rf " + path, shell=True)'
    payload = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": True
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["gate_decision"] == "BLOCK"
    assert data["reason_code"] == "REPLAY_MISMATCH"
    assert "ReplayGuard Controlled Fault Injection" in data["patch_run_2"]
    assert "ReplayGuard Non-Deterministic Seed" not in data["patch_run_2"]


def test_review_metadata_showing_not_run():
    """
    Verify review metadata has template_version=None, template_hash=None,
    and template_postconditions_passed=None (indicating not run).
    """
    code = "eval('1 + 1')"
    payload = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": False
    }
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["gate_decision"] == "REVIEW"
    assert data["reason_code"] == "NO_TEMPLATE"
    assert data["applied_template_id"] is None
    assert data["template_version"] is None
    assert data["template_hash"] is None
    assert data["template_postconditions_passed"] is None


def test_ledger_record_tamper_verification_fails():
    """
    Verify that mutating saved ledger record fields (like reason_code)
    while keeping the ledger_hash intact causes verification readback to fail.
    """
    record = ledger_service.generate_record(
        original_code="foo",
        rule_id="rule_sql_injection",
        template_id="template_sql_injection",
        patch_1="bar",
        patch_2="bar",
        gate_decision="ALLOW",
        reason_code="EVIDENCE_VERIFIED"
    )

    tampered_record = dict(record)
    tampered_record["evidence_persisted"] = True
    tampered_record["reason_code"] = "MUTATED_VALUE_XYZ"

    with patch.object(ledger_service, "_get_history_strict", side_effect=lambda: [dict(tampered_record)]):
        with pytest.raises(LedgerPersistenceError) as exc_info:
            ledger_service.save_record(record)
        assert "recomputed ledger hash does not match stored ledger hash" in str(exc_info.value)


def test_aggregate_postconditions_failed_when_run_2_fails():
    """
    Verify aggregate template_postconditions_passed is False, and final gate
    decision is BLOCK with TEMPLATE_ATTESTATION_FAILED, even when patch bytes match.
    """
    call_count = 0

    def mock_apply(rule_id, code, status=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            if status is not None:
                status["template_id"] = "template_sql_injection"
                status["template_version"] = "1.0.0"
                status["template_hash"] = "hash_abc"
                status["template_postconditions_passed"] = True
            return "def safe_code():\n    pass"
        else:
            if status is not None:
                status["template_id"] = "template_sql_injection"
                status["template_version"] = "1.0.0"
                status["template_hash"] = "hash_abc"
                status["template_postconditions_passed"] = False
            return "def safe_code():\n    pass"

    with patch.object(replay_controller.template_engine, "apply_remediation", side_effect=mock_apply):
        status_dict = {}
        p1, p2 = replay_controller.run_replays("rule_sql_injection", "some code", status=status_dict)
        assert status_dict["template_postconditions_passed"] is False
        assert p1 == p2

    # Verify api endpoint block gate decision and reason_code
    call_count = 0
    code = 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)'
    payload = {
        "code": code,
        "language": "python",
        "simulate_non_determinism": False
    }
    with patch.object(replay_controller.template_engine, "apply_remediation", side_effect=mock_apply):
        response = client.post("/api/scan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["comparison"]["is_match"] is True
        assert data["ledger_record"]["evidence_persisted"] is True
        assert data["ledger_record"]["reason_code"] == "TEMPLATE_ATTESTATION_FAILED"
        assert data["gate_decision"] == "BLOCK"
        assert data["reason_code"] == "TEMPLATE_ATTESTATION_FAILED"
        assert data["template_postconditions_passed"] is False
