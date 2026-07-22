from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Scenario(BaseModel):
    id: str
    name: str
    description: str
    language: str
    code: str
    simulate_non_determinism: bool = False

class ScanRequest(BaseModel):
    code: str
    language: str
    simulate_non_determinism: bool = False

class RuleMatch(BaseModel):
    id: str
    name: str
    pattern: str
    severity: str
    description: str

class ComparisonResult(BaseModel):
    is_match: bool
    diff: Optional[str] = None
    size_diff_bytes: int
    run_1_hash: str
    run_2_hash: str

class LedgerRecord(BaseModel):
    timestamp: str
    original_code_hash: str
    rule_id: Optional[str] = None
    template_id: Optional[str] = None
    patch_run_1_hash: Optional[str] = None
    patch_run_2_hash: Optional[str] = None
    gate_decision: str
    ledger_hash: str
    evidence_persisted: bool = False
    record_id: Optional[str] = None

class ScanResponse(BaseModel):
    original_code: str
    remediated_code: Optional[str] = None
    patch_run_1: Optional[str] = None
    patch_run_2: Optional[str] = None
    matched_rule: Optional[RuleMatch] = None
    applied_template_id: Optional[str] = None
    comparison: ComparisonResult
    ledger_record: LedgerRecord
    gate_decision: str  # ALLOW, BLOCK, REVIEW
    explanation: Optional[str] = None
    reason_code: str
