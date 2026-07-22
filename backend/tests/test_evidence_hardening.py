import json
import os
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.main import app
from app.services.ledger import LedgerService, LedgerPersistenceError

client = TestClient(app)

def test_ledger_service_write_failure_raises_error(tmp_path, monkeypatch):
    """
    Verify that LedgerService.record_run propagates filesystem errors
    by raising a LedgerPersistenceError when the atomic replace operation fails.
    """
    test_path = tmp_path / "ledger_history_test.json"
    service = LedgerService(ledger_path=test_path)

    def mock_replace(src, dst):
        raise OSError("Simulated replace/rename failure")

    with monkeypatch.context() as m:
        m.setattr(os, "replace", mock_replace)
        with pytest.raises(LedgerPersistenceError):
            service.record_run(
                original_code="print('hello')",
                rule_id=None,
                template_id=None,
                patch_1=None,
                patch_2=None,
                gate_decision="REVIEW"
            )

def test_saved_json_contains_evidence_persisted_true(tmp_path):
    """
    Verify that the saved JSON file actually contains evidence_persisted=True and record_id.
    """
    test_path = tmp_path / "ledger_history_test.json"
    service = LedgerService(ledger_path=test_path)

    record = service.record_run(
        original_code="print('hello')",
        rule_id=None,
        template_id=None,
        patch_1=None,
        patch_2=None,
        gate_decision="REVIEW"
    )

    # Read the file directly to verify serialization
    with open(test_path, "r") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["ledger_hash"] == record["ledger_hash"]
    assert data[0]["record_id"] == record["record_id"]
    assert data[0]["evidence_persisted"] is True

def test_repeated_run_validates_newest_record_id(tmp_path, monkeypatch):
    """
    Verify that readback verification checks both ledger_hash AND record_id,
    preventing an older identical record from falsely satisfying verification.
    """
    test_path = tmp_path / "ledger_history_test.json"
    service = LedgerService(ledger_path=test_path)

    # 1. Write the first record
    rec1 = service.record_run(
        original_code="print('hello')",
        rule_id="rule_1",
        template_id="temp_1",
        patch_1="patch_1",
        patch_2="patch_2",
        gate_decision="ALLOW"
    )

    # 2. Generate a second identical record (same hashes, but different record_id)
    rec2 = service.generate_record(
        original_code="print('hello')",
        rule_id="rule_1",
        template_id="temp_1",
        patch_1="patch_1",
        patch_2="patch_2",
        gate_decision="ALLOW"
    )

    assert rec1["record_id"] != rec2["record_id"]

    # Manually force rec2 to have the same ledger_hash as rec1 to test that
    # readback verification still blocks it because of the record_id mismatch.
    rec2["ledger_hash"] = rec1["ledger_hash"]

    # Mock replace to do nothing (so the file on disk is not updated and remains [rec1])
    def dummy_replace(src, dst):
        pass

    with monkeypatch.context() as m:
        m.setattr(os, "replace", dummy_replace)
        with pytest.raises(LedgerPersistenceError) as exc_info:
            service.save_record(rec2)

        assert "Verification failed" in str(exc_info.value)

def test_concurrent_writes(tmp_path):
    """
    Verify that concurrent writes using ThreadPoolExecutor do not cause any race conditions,
    every returned record_id is unique, every returned record exists in the saved ledger,
    and all saved records have evidence_persisted=True.
    """
    test_path = tmp_path / "ledger_history_test.json"
    service = LedgerService(ledger_path=test_path)

    num_threads = 10

    def write_record(index):
        return service.record_run(
            original_code=f"print('hello from thread {index}')",
            rule_id=f"rule_{index}",
            template_id=f"temp_{index}",
            patch_1=f"patch_{index}",
            patch_2=f"patch_{index}",
            gate_decision="ALLOW"
        )

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(write_record, i) for i in range(num_threads)]
        results = [f.result() for f in futures]

    assert len(results) == num_threads

    # Assert that all returned record_ids are unique
    record_ids = {r["record_id"] for r in results}
    assert len(record_ids) == num_threads

    # Read the saved ledger directly
    with open(test_path, "r") as f:
        saved_history = json.load(f)

    assert len(saved_history) == num_threads

    # Assert that every returned record exists in the saved ledger and evidence_persisted is True
    for result_record in results:
        saved_record = next((rec for rec in saved_history if rec.get("record_id") == result_record["record_id"]), None)
        assert saved_record is not None
        assert saved_record["ledger_hash"] == result_record["ledger_hash"]
        assert saved_record["evidence_persisted"] is True
        assert result_record["evidence_persisted"] is True

def test_simulated_ledger_persistence_failure_blocks_allow(monkeypatch):
    """
    Verify that if a scan would normally be ALLOWed but ledger persistence fails
    (due to os.replace failure), ReplayGuard blocks the merge and returns
    EVIDENCE_PERSISTENCE_FAILED.
    """
    payload = {
        "code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return db.execute(query)',
        "language": "python",
        "simulate_non_determinism": False
    }

    # 1. Normal case: scan is ALLOWed and evidence is verified
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gate_decision"] == "ALLOW"
    assert data["reason_code"] == "EVIDENCE_VERIFIED"
    assert data["ledger_record"]["evidence_persisted"] is True

    # 2. Hardening case: Mock replace operation to raise OSError
    def mock_replace(src, dst):
        raise OSError("Simulated write failure")

    with monkeypatch.context() as m:
        m.setattr(os, "replace", mock_replace)
        response = client.post("/api/scan", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify it returns BLOCK and reason_code EVIDENCE_PERSISTENCE_FAILED
        assert data["gate_decision"] == "BLOCK"
        assert data["reason_code"] == "EVIDENCE_PERSISTENCE_FAILED"
        assert data["ledger_record"]["evidence_persisted"] is False
        assert "Ledger persistence failed" in data["explanation"]
