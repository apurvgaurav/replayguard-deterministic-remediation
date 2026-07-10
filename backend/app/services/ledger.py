import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from typing import Optional

class LedgerService:
    def __init__(self):
        self.ledger_path = Path(__file__).parent.parent / "demo_data" / "ledger_history.json"
        self._ensure_ledger_file()

    def _ensure_ledger_file(self):
        if not self.ledger_path.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "w") as f:
                json.dump([], f)

    def get_history(self) -> List[Dict[str, Any]]:
        try:
            with open(self.ledger_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

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
        # Calculate individual SHA-256 hashes
        orig_hash = hashlib.sha256((original_code or "").encode("utf-8")).hexdigest()
        p1_hash = hashlib.sha256((patch_1 or "").encode("utf-8")).hexdigest() if patch_1 else ""
        p2_hash = hashlib.sha256((patch_2 or "").encode("utf-8")).hexdigest() if patch_2 else ""

        # Create audit chain hash
        payload = f"{orig_hash}|{rule_id or ''}|{template_id or ''}|{p1_hash}|{p2_hash}|{gate_decision}"
        ledger_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        record = {
            "timestamp": datetime.now().isoformat(),
            "original_code_hash": orig_hash,
            "rule_id": rule_id,
            "template_id": template_id,
            "patch_run_1_hash": p1_hash if patch_1 else None,
            "patch_run_2_hash": p2_hash if patch_2 else None,
            "gate_decision": gate_decision,
            "ledger_hash": ledger_hash
        }

        # Append to history file
        history = self.get_history()
        history.insert(0, record)  # Newest first
        
        # Cap at 50 records to prevent bloating
        history = history[:50]
        
        try:
            with open(self.ledger_path, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error writing to ledger history file: {e}")

        return record
