# ReplayGuard CI/CD Gate Example

This folder shows how ReplayGuard could be positioned as a CI/CD merge gate.

The current prototype runs locally through FastAPI and the React dashboard. A future production version could expose a command-line interface or GitHub Action that runs during pull requests.

Conceptual flow:

Pull request opened
→ automated remediation candidate detected
→ ReplayGuard verification runs
→ replay outputs compared
→ evidence recorded
→ merge gate returns ALLOW, BLOCK, or REVIEW

Example gate outcomes:

ALLOW   replay matched and evidence was recorded
BLOCK   replay mismatch detected
REVIEW  no deterministic remediation template available

This example is intentionally illustrative. It shows the integration pattern, not a published GitHub Action.
