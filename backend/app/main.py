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
from app.services.ledger import LedgerService
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
    
    if matched_rule_dict:
        matched_rule = RuleMatch(**matched_rule_dict)
        rule_id = matched_rule.id
        rule_id = matched_rule.id
        
        # 2. Run independent patch generation replays
        patch_run_1, patch_run_2 = replay_controller.run_replays(
            rule_id=rule_id,
            code=code_input,
            simulate_non_determinism=req.simulate_non_determinism
        )
        
        # Check if template was actually applied
        if patch_run_1 is not None:
            applied_template_id = f"template_{rule_id.split('rule_')[-1]}"
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

    # 4. Gate Decision
    gate_decision = MergeGate.decide(
        rule_matched=matched_rule is not None,
        template_applied=applied_template_id is not None,
        is_replay_match=is_match
    )
    
    # 5. Record run to ledger
    ledger_rec_dict = ledger_service.record_run(
        original_code=code_input,
        rule_id=matched_rule.id if matched_rule else None,
        template_id=applied_template_id,
        patch_1=patch_run_1,
        patch_2=patch_run_2,
        gate_decision=gate_decision
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
        is_mismatch_scenario = (normalize_code(code_input).strip() == 'query = "SELECT * FROM users WHERE id = " + user_id')
        if is_mismatch_scenario:
            explanation = "Replay mismatch detected. Merge blocked because remediation output was not reproducible."
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
        explanation=explanation
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

