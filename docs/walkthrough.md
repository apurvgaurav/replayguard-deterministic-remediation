# ReplayGuard Walkthrough

This walkthrough explains how to run the prototype and what to look for during the demo.

ReplayGuard shows one main idea:

> A code fix should not move forward only because it looks correct. It should be replayed, compared, and recorded first.

---

## 1. Start the backend

From the project root:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
Backend API docs:
http://127.0.0.1:8000/docs
Health check:
http://127.0.0.1:8000/api/health
2. Start the frontend

Open a second terminal window.

From the project root:
cd frontend
npm install
npm run dev
Open the Vite URL shown in the terminal.

It is usually:
http://localhost:5174/
If Vite uses another port, use the URL shown in Terminal.

At the top of the app, confirm:
Backend API Active
3. Run the SQL Injection scenario

Select:
SQL Injection via Concatenation
Click:
Run ReplayGuard Pipeline
Expected result:
Merge Gate: ALLOW
What to notice:

* ReplayGuard detects the vulnerable SQL pattern.
* It applies a deterministic remediation template.
* Patch run 1 and patch run 2 match.
* The patch hashes match.
* Ledger evidence is recorded.
* The gate allows the change.

This is the success path.
4. Run the Hardcoded Secret scenario

Select:
Hardcoded API Key Credential
Click:
Run ReplayGuard Pipeline
Expected result:
Merge Gate: ALLOW
What to notice:

* ReplayGuard detects a hardcoded secret.
* The remediated code uses an environment variable lookup.
* Replay verification passes.
* Ledger evidence is recorded.
5. Run the Unsafe Shell scenario

Select:
Unsafe Shell Execution
Click:
Run ReplayGuard Pipeline
Expected result:
Merge Gate: ALLOW
What to notice:

* ReplayGuard detects unsafe shell execution.
* The remediation changes the command structure.
* Replay verification passes.
* Ledger evidence is recorded.
6. Run the Replay Mismatch scenario

Select:
Replay Mismatch - Block Merge
Click:
Run ReplayGuard Pipeline
Expected result:
Merge Gate: BLOCK
What to notice:

* Patch run 1 and patch run 2 do not match.
* The hashes are different.
* Byte-level comparison reports a mismatch.
* The gate blocks the change.

This is one of the most important parts of the prototype.

ReplayGuard is not just approving changes. It can stop a change when the evidence does not support it.
7. Run the No Template scenario

Select:
No Template - Human Review Required
Click:
Run ReplayGuard Pipeline
Expected result:
Merge Gate: REVIEW
What to notice:

* ReplayGuard detects unsafe eval() usage.
* No deterministic remediation template is available.
* The system does not invent a fix.
* The gate routes the issue to human review.

This matters because not every issue should be automatically patched.
8. Show the clean ledger view

To create a clean audit ledger screenshot, clear the ledger first.

Then run only these three scenarios:
SQL Injection via Concatenation → ALLOW
Replay Mismatch - Block Merge → BLOCK
No Template - Human Review Required → REVIEW
The ledger should show:
ALLOW
BLOCK
REVIEW
This screenshot is useful because it shows the full decision model in one place.
What the walkthrough demonstrates

The walkthrough demonstrates this flow:
detect the issue
apply a deterministic fix
replay the fix
compare both outputs
record evidence
make a gate decision
The prototype is intentionally focused.

It does not try to fix every possible code issue. It shows how replay verification can create stronger evidence before an automated code change is trusted.
