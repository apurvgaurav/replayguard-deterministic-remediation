import json
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import Scenario, ScanRequest, ScanResponse, RuleMatch, ComparisonResult, LedgerRecord
from app.services.rule_engine import RuleEngine
from app.services.replay import ReplayController
from app.services.comparator import ByteComparator
from app.services.gate import MergeGate
from app.services.ledger import LedgerService, LedgerPersistenceError
from app.services.normalize import normalize_code

app = FastAPI(title="ReplayGuard API", description="Deterministic Remediation and Replay Verification Engine")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototype, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rule_engine = RuleEngine()
replay_controller = ReplayController()
comparator = ByteComparator()
ledger_service = LedgerService()

SCENARIOS_PATH = Path(__file__).parent / "demo_data" / "scenarios.json"

@app.get("/api/scenarios", response_model=List[Scenario])
def get_scenarios():
    try:
        with open(SCENARIOS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenarios: {e}")

@app.post("/api/scan", response_model=ScanResponse)
def scan_code(req: ScanRequest):
    code_input = req.code
    
    # 1. Scan for vulnerability using rule engine
    matched_rule_dict = rule_engine.scan(code_input)
    
    matched_rule = None
    applied_template_id = None
    patch_run_1 = None
    patch_run_2 = None
    is_match = False
    diff_text = None
    size_diff = 0
    run_1_hash = ""
    run_2_hash = ""

    template_version = None
    template_hash = None
    template_postconditions_passed = None

    if matched_rule_dict:
        matched_rule = RuleMatch(**matched_rule_dict)
        rule_id = matched_rule.id

        template_status = {}
        # 2. Run two deterministic remediation passes
        patch_run_1, patch_run_2 = replay_controller.run_replays(
            rule_id=rule_id,
            code=code_input,
            simulate_non_determinism=req.simulate_non_determinism,
            status=template_status
        )

        template_version = template_status.get("template_version")
        template_hash = template_status.get("template_hash")
        template_postconditions_passed = template_status.get("template_postconditions_passed")

        # Check if template was actually applied
        template = replay_controller.template_engine.get_template_for_rule(rule_id)
        if patch_run_1 is not None and template:
            applied_template_id = template.get("id")
        else:
            applied_template_id = None

        # 3. Perform byte-level comparison
        comp_res = comparator.compare(patch_run_1, patch_run_2)
        is_match = comp_res["is_match"]
        diff_text = comp_res["diff"]
        size_diff = comp_res["size_diff_bytes"]
        run_1_hash = comp_res["run_1_hash"]
        run_2_hash = comp_res["run_2_hash"]
    else:
        # If no vulnerability is detected, we don't apply templates or replay
        # But we still compute the original hash for audit
        run_1_hash = comparator.compute_sha256(normalize_code(code_input))
        run_2_hash = run_1_hash
        is_match = True
        diff_text = None
        size_diff = 0

    # 4. Determine candidate status and tentative decision
    if matched_rule is not None and applied_template_id is not None:
        if template_postconditions_passed is not True:
            tentative_decision = "BLOCK"
            tentative_reason = "TEMPLATE_ATTESTATION_FAILED"
            is_allow_candidate = False
        elif not is_match:
            tentative_decision = "BLOCK"
            tentative_reason = "REPLAY_MISMATCH"
            is_allow_candidate = False
        else:
            tentative_decision = "ALLOW"
            tentative_reason = "EVIDENCE_VERIFIED"
            is_allow_candidate = True
    elif matched_rule is None:
        tentative_decision = "REVIEW"
        tentative_reason = "NO_RULE_MATCH"
        is_allow_candidate = False
    else:  # applied_template_id is None
        tentative_decision = "REVIEW"
        tentative_reason = "NO_TEMPLATE"
        is_allow_candidate = False

    evidence_persisted = False
    ledger_rec_dict = None

    # 5. Record run to ledger
    try:
        ledger_rec_dict = ledger_service.record_run(
            original_code=code_input,
            rule_id=matched_rule.id if matched_rule else None,
            template_id=applied_template_id,
            patch_1=patch_run_1,
            patch_2=patch_run_2,
            gate_decision=tentative_decision,
            reason_code=tentative_reason,
            template_version=template_version,
            template_hash=template_hash,
            template_postconditions_passed=template_postconditions_passed
        )
        evidence_persisted = ledger_rec_dict.get("evidence_persisted", False)
    except LedgerPersistenceError:
        evidence_persisted = False

    # Determine final gate decision using MergeGate.decide
    gate_decision = MergeGate.decide(
        rule_matched=matched_rule is not None,
        template_applied=applied_template_id is not None,
        is_replay_match=is_match,
        evidence_persisted=evidence_persisted,
        template_postconditions_passed=template_postconditions_passed is True
    )

    # Determine final reason code
    if is_allow_candidate:
        if evidence_persisted:
            reason_code = "EVIDENCE_VERIFIED"
        else:
            reason_code = "EVIDENCE_PERSISTENCE_FAILED"
    else:
        reason_code = tentative_reason

    # Ensure ledger record is populated
    if ledger_rec_dict is None:
        # Fallback record on write failure
        ledger_rec_dict = ledger_service.generate_record(
            original_code=code_input,
            rule_id=matched_rule.id if matched_rule else None,
            template_id=applied_template_id,
            patch_1=patch_run_1,
            patch_2=patch_run_2,
            gate_decision=gate_decision,
            reason_code=reason_code,
            template_version=template_version,
            template_hash=template_hash,
            template_postconditions_passed=template_postconditions_passed
        )

    ledger_record = LedgerRecord(**ledger_rec_dict)

    comparison = ComparisonResult(
        is_match=is_match,
        diff=diff_text,
        size_diff_bytes=size_diff,
        run_1_hash=run_1_hash,
        run_2_hash=run_2_hash
    )

    # Generate contextual explanation
    remediated_code = patch_run_1
    explanation = None
    if gate_decision == "ALLOW":
        if matched_rule:
            if matched_rule.id == "rule_sql_injection":
                explanation = "Deterministic SQL parameterization applied to prevent SQL injection."
            elif matched_rule.id == "rule_hardcoded_secret":
                explanation = "Hardcoded credential replaced with environment variable loading via os.getenv."
            elif matched_rule.id == "rule_unsafe_shell":
                explanation = "Unsafe shell=True subprocess run replaced with safe list-based execution."
            else:
                explanation = f"Deterministic remediation applied successfully for rule {matched_rule.name}."
        else:
            explanation = "No issues detected. Code is safe."
    elif gate_decision == "BLOCK":
        if reason_code == "REPLAY_MISMATCH":
            explanation = "Replay mismatch detected. Merge blocked because remediation output was not reproducible."
        elif reason_code == "EVIDENCE_PERSISTENCE_FAILED":
            explanation = "Safety Violation: Ledger persistence failed. Merging blocked."
        elif reason_code == "TEMPLATE_ATTESTATION_FAILED":
            explanation = "Safety Violation: Template replay attestation failed. Merging blocked."
        else:
            explanation = "Safety Violation: Replay verification detected non-deterministic patch generation. Merging blocked."
    elif gate_decision == "REVIEW":
        if matched_rule:
            explanation = "Violation detected, but no deterministic remediation template is available. Human review required."
        else:
            explanation = "No matching deterministic remediation template available. Code routed to manual security review."

    return ScanResponse(
        original_code=code_input,
        remediated_code=remediated_code,
        patch_run_1=patch_run_1,
        patch_run_2=patch_run_2,
        matched_rule=matched_rule,
        applied_template_id=applied_template_id,
        comparison=comparison,
        ledger_record=ledger_record,
        gate_decision=gate_decision,
        explanation=explanation,
        reason_code=reason_code,
        template_version=template_version,
        template_hash=template_hash,
        template_postconditions_passed=template_postconditions_passed
    )

@app.get("/api/ledger", response_model=List[LedgerRecord])
def get_ledger():
    try:
        history = ledger_service.get_history()
        return [LedgerRecord(**record) for record in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load ledger history: {e}")

@app.post("/api/ledger/clear")
def clear_ledger():
    try:
        with open(ledger_service.ledger_path, "w") as f:
            json.dump([], f)
        return {"status": "success", "message": "Ledger history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear ledger history: {e}")

@app.get("/")
def root():
    return {
        "service": "ReplayGuard backend",
        "status": "running",
        "message": "Use /docs for API documentation"
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "ReplayGuard backend"}

@app.get("/api/health")
def api_health():
    return {"status": "ok", "service": "ReplayGuard backend"}

