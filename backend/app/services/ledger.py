import json
import hashlib
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

class LedgerPersistenceError(Exception):
    pass

class LedgerService:
    def __init__(self, ledger_path: Optional[Path] = None):
        if ledger_path is not None:
            self.ledger_path = Path(ledger_path)
        else:
            self.ledger_path = Path(__file__).parent.parent / "demo_data" / "ledger_history.json"
        self.lock = threading.RLock()
        self._ensure_ledger_file()

    def _ensure_ledger_file(self):
        if not self.ledger_path.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file_path = None
            try:
                temp_dir = self.ledger_path.parent
                with tempfile.NamedTemporaryFile('w', dir=temp_dir, delete=False, suffix=".tmp") as temp_file:
                    temp_file_path = Path(temp_file.name)
                    json.dump([], temp_file)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_file_path, self.ledger_path)
            except Exception as e:
                if temp_file_path and temp_file_path.exists():
                    try:
                        os.unlink(temp_file_path)
                    except Exception:
                        pass
                raise LedgerPersistenceError(f"Failed to initialize ledger file: {e}") from e

    def _get_history_strict(self) -> List[Dict[str, Any]]:
        """
        Strictly reads the history from the ledger file. Raises LedgerPersistenceError
        on missing, unreadable, or invalid JSON, or if the root is not a list.
        """
        if not self.ledger_path.exists():
            raise LedgerPersistenceError(f"Ledger file does not exist: {self.ledger_path}")
        try:
            with open(self.ledger_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise LedgerPersistenceError(f"Failed to decode ledger JSON: {e}") from e
        except Exception as e:
            raise LedgerPersistenceError(f"Failed to read ledger file: {e}") from e

        if not isinstance(data, list):
            raise LedgerPersistenceError("Invalid ledger format: root must be a list")
        return data

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Returns the history ledger records. Safe version for the UI (swallows exceptions).
        """
        try:
            return self._get_history_strict()
        except Exception:
            return []

    def generate_record(
        self,
        original_code: str,
        rule_id: Optional[str],
        template_id: Optional[str],
        patch_1: Optional[str],
        patch_2: Optional[str],
        gate_decision: str
    ) -> Dict[str, Any]:
        """
        Generates a cryptographic ledger record of the pipeline run.
        """
        orig_hash = hashlib.sha256((original_code or "").encode("utf-8")).hexdigest()
        p1_hash = hashlib.sha256((patch_1 or "").encode("utf-8")).hexdigest() if patch_1 else ""
        p2_hash = hashlib.sha256((patch_2 or "").encode("utf-8")).hexdigest() if patch_2 else ""

        record_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Include record_id and timestamp in the ledger_hash payload
        payload = f"{record_id}|{timestamp}|{orig_hash}|{rule_id or ''}|{template_id or ''}|{p1_hash}|{p2_hash}|{gate_decision}"
        ledger_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return {
            "record_id": record_id,
            "timestamp": timestamp,
            "original_code_hash": orig_hash,
            "rule_id": rule_id,
            "template_id": template_id,
            "patch_run_1_hash": p1_hash if patch_1 else None,
            "patch_run_2_hash": p2_hash if patch_2 else None,
            "gate_decision": gate_decision,
            "ledger_hash": ledger_hash,
            "evidence_persisted": False
        }

    def save_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atomically saves the record to the history ledger file and verifies it by reading it back.
        """
        # Create a separate persisted_record copy with evidence_persisted=True before serialization
        persisted_record = dict(record)
        persisted_record["evidence_persisted"] = True

        with self.lock:
            history = self._get_history_strict()
            history.insert(0, persisted_record)  # Newest first
            history = history[:50]

            temp_file_path = None
            try:
                temp_dir = self.ledger_path.parent
                with tempfile.NamedTemporaryFile('w', dir=temp_dir, delete=False, suffix=".tmp") as temp_file:
                    temp_file_path = Path(temp_file.name)
                    json.dump(history, temp_file, indent=2)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_file_path, self.ledger_path)
            except Exception as e:
                if temp_file_path and temp_file_path.exists():
                    try:
                        os.unlink(temp_file_path)
                    except Exception:
                        pass
                raise LedgerPersistenceError(f"Failed to write ledger history file: {e}") from e

            # Read the saved ledger back using strict mode and verify the newest record
            try:
                saved_history = self._get_history_strict()
                if not saved_history:
                    raise LedgerPersistenceError("Verification failed: saved history is empty.")

                newest_record = saved_history[0]
                expected_id = persisted_record["record_id"]
                expected_hash = persisted_record["ledger_hash"]
                expected_timestamp = persisted_record["timestamp"]

                if (newest_record.get("record_id") != expected_id or
                    newest_record.get("ledger_hash") != expected_hash or
                    newest_record.get("timestamp") != expected_timestamp or
                    newest_record.get("evidence_persisted") is not True):
                    raise LedgerPersistenceError("Verification failed: newest record in saved ledger does not match the persisted record.")
            except Exception as e:
                if not isinstance(e, LedgerPersistenceError):
                    raise LedgerPersistenceError(f"Verification readback failed: {e}") from e
                raise

        return persisted_record

    def record_run(
        self,
        original_code: str,
        rule_id: Optional[str],
        template_id: Optional[str],
        patch_1: Optional[str],
        patch_2: Optional[str],
        gate_decision: str
    ) -> Dict[str, Any]:
        """
        Generates and saves a cryptographic ledger record of the pipeline run.
        """
        record = self.generate_record(
            original_code=original_code,
            rule_id=rule_id,
            template_id=template_id,
            patch_1=patch_1,
            patch_2=patch_2,
            gate_decision=gate_decision
        )
        return self.save_record(record)
