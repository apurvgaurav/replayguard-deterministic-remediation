# Sample ReplayGuard Pull Request Gate Output

This file shows how ReplayGuard gate decisions could appear in a pull-request or CI/CD workflow.

This is an integration pattern, not a published production plugin.

---

## Example 1: ALLOW

ReplayGuard Trust Gate: ALLOW

Reason:

Replay matched and evidence was recorded.

Required action:

The remediation may proceed to the next CI/CD stage for the selected scenario.

Evidence summary:

- Rule: SQL Injection
- Template: template_sql_injection
- Replay comparison: MATCH
- Gate decision: ALLOW
- Evidence status: Recorded

---

## Example 2: BLOCK

ReplayGuard Trust Gate: BLOCK

Reason:

Replay mismatch detected. The first remediation output and replay output did not match.

Required action:

Do not merge automatically. Route to human review or rerun after deterministic remediation is fixed.

Evidence summary:

- Rule: SQL Injection
- Template: template_sql_injection
- Replay comparison: MISMATCH
- Gate decision: BLOCK
- Evidence status: Failed replay verification

---

## Example 3: REVIEW

ReplayGuard Trust Gate: REVIEW

Reason:

No deterministic remediation path is available for the detected issue.

Required action:

Route to human review. Do not invent an automated fix.

Evidence summary:

- Rule: Unsafe Eval
- Template: Not available
- Replay comparison: Not applicable
- Gate decision: REVIEW
- Evidence status: Human review required

---

## CI/CD principle

ReplayGuard should not be used as a claim that all code is secure.

It should be used as a gate that asks whether automated remediation produced enough replay evidence to move forward.

The CI/CD question is:

Should this automated fix be allowed, blocked, or routed to human review?
