# ReplayGuard Architecture

ReplayGuard focuses on one practical problem in automated remediation:

> before a code patch moves forward, can we reproduce it, compare it, and keep evidence of what happened?

This document explains the current prototype architecture.

---

## System overview

ReplayGuard is a local full-stack prototype.

It has two main parts:

```text
frontend/  React/Vite dashboard
backend/   FastAPI service
The frontend is used to select scenarios, run the pipeline, and view the result.

The backend performs the scan, remediation, replay verification, comparison, ledger recording, and gate decisioning.
End-to-end flow

The main workflow is:
Code input
→ rule detection
→ deterministic remediation template
→ patch run 1
→ patch run 2
→ byte-level comparison
→ ledger evidence
→ merge gate decision
The merge gate returns one of three outcomes:
ALLOW   replay matched and evidence was recorded
BLOCK   replay mismatch was detected
REVIEW  issue was detected, but no deterministic remediation template was available
Backend components

The backend is built with FastAPI.

Main files:
backend/app/main.py
backend/app/models.py
backend/app/services/rule_engine.py
backend/app/services/template_engine.py
backend/app/services/replay.py
backend/app/services/comparator.py
backend/app/services/ledger.py
backend/app/services/gate.py
Rule engine

The rule engine detects selected demo patterns:

* SQL injection through string concatenation
* hardcoded API key
* unsafe shell execution
* unsafe eval usage

The current implementation is intentionally simple. It is enough to demonstrate the workflow, but it is not a full SAST engine.

Template engine

The template engine maps selected rules to deterministic remediation templates.

Examples:

* SQL string concatenation → parameterized query pattern
* hardcoded API key → environment variable lookup
* unsafe shell command → list-based subprocess call

If no deterministic template exists, the system returns REVIEW.

Replay engine

The replay engine runs the remediation process twice.

The goal is to check whether the same input, rule, and template produce the same output.

If both runs match, the change can be allowed.

If the outputs differ, the change is blocked.

Comparator

The comparator checks patch run 1 and patch run 2 byte-for-byte.

It also generates hashes for both outputs.

The prototype uses this comparison to decide whether replay verification passed.

Ledger service

The ledger service records evidence for each run.

A ledger record includes:

* original code hash
* matched rule
* template id
* patch run 1 hash
* patch run 2 hash
* gate decision
* ledger hash
* timestamp

This is local demo storage, not an enterprise audit system.

Gate service

The gate service returns:

* ALLOW when replay matches
* BLOCK when replay mismatch occurs
* REVIEW when an issue is detected but no deterministic template is available
API endpoints

Current backend endpoints:
GET  /api/health
GET  /api/scenarios
POST /api/scan
GET  /api/ledger
POST /api/ledger/clear
POST /api/scan

This is the main endpoint.

Input:
{
  "code": "query = \"SELECT * FROM users WHERE id = \" + user_id",
  "language": "python",
  "scenario_id": "sql_injection"
}
Output includes:

* original code
* remediated code
* matched rule
* applied template
* patch run 1
* patch run 2
* comparison result
* ledger record
* gate decision
* explanation
Frontend components

The frontend is built with React/Vite.

It provides:

* scenario selector
* code input panel
* pipeline run button
* merge gate result
* before/after code comparison
* replay verification section
* ledger evidence section
* audit ledger table

The UI is designed to make the trust-gate story visible without requiring someone to read the backend code first.
Demo scenarios

Current scenarios:

1. SQL Injection via Concatenation → ALLOW
2. Hardcoded API Key Credential → ALLOW
3. Unsafe Shell Execution → ALLOW
4. Replay Mismatch - Block Merge → BLOCK
5. No Template - Human Review Required → REVIEW

These are intentionally selected to show success, failure, and human review paths.
MVP versus future version

Current MVP

The MVP demonstrates:

* selected rule detection
* deterministic template remediation
* replay verification
* byte-level comparison
* ledger-style evidence
* ALLOW / BLOCK / REVIEW gate decisions
* frontend and backend integration
* backend tests

Future version

A stronger version would need:

* deeper AST parsing
* taint-flow analysis
* broader language support
* real CI/CD integration
* signed or external ledger storage
* policy-based gate rules
* stronger test coverage
* evaluation on real-world code examples
Architecture takeaway

ReplayGuard is not trying to be a complete security scanner.

The prototype shows a narrower idea:

when automated remediation is used, the output should be reproducible, comparable, and recorded before the change is trusted.
