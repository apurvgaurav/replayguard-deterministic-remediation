# ReplayGuard 90-Second Demo Script

This is the script I will use for a short demo video or live walkthrough.

The goal is not to show every technical detail. The goal is to make the main idea clear:

> A code fix should not move forward only because it looks correct. It should be replayed, compared, and recorded first.

---

## Opening

AI can suggest code fixes.

But before a fix moves forward, we need to know whether it can be reproduced.

That is the idea behind ReplayGuard.

ReplayGuard is a prototype based on my issued U.S. patent. It demonstrates deterministic code remediation with replay verification, byte-level comparison, ledger-style evidence, and merge gate decisioning.

---

## Scene 1 — Show the dashboard

On screen:

ReplayGuard dashboard with Backend API Active.

Voiceover:

ReplayGuard takes a vulnerable code sample and runs it through a simple workflow: detect the issue, apply a deterministic remediation template, replay the patch, compare both outputs, record evidence, and then decide whether the change should move forward.

---

## Scene 2 — SQL Injection success path

On screen:

Select `SQL Injection via Concatenation`.

Voiceover:

Here I am starting with a SQL injection-style example where a query is built through string concatenation.

ReplayGuard detects the issue and maps it to a deterministic remediation template.

On screen:

Show Original Vulnerable Code and Deterministic Remediated Code.

Voiceover:

The system creates a remediated version using a parameterized query pattern.

---

## Scene 3 — Replay verification

On screen:

Show Patch Run 1 Hash, Patch Run 2 Hash, and Byte-Level Comparison: MATCH.

Voiceover:

The important part is not just that a patch was created.

ReplayGuard runs the remediation twice and compares both outputs byte-for-byte.

Here, both replay outputs match.

Because the replay matched, the system records ledger evidence and allows the change.

On screen:

Show `Merge Gate: ALLOW`.

---

## Scene 4 — Replay mismatch block path

On screen:

Select `Replay Mismatch - Block Merge`.

Voiceover:

Now I am showing the failure path.

In this scenario, the second replay output does not match the first one.

On screen:

Show Byte-Level Comparison: MISMATCH and different patch hashes.

Voiceover:

ReplayGuard blocks the change because the remediation output was not reproducible.

This is important because a trust gate should not only approve changes. It should also know when to stop them.

On screen:

Show `Merge Gate: BLOCK`.

---

## Scene 5 — No template review path

On screen:

Select `No Template - Human Review Required`.

Voiceover:

Not every detected issue should be automatically patched.

Here, ReplayGuard detects unsafe eval usage, but no deterministic remediation template is available.

So the system does not invent a fix. It routes the change to human review.

On screen:

Show `Merge Gate: REVIEW`.

---

## Scene 6 — Audit ledger

On screen:

Show clean ledger with three rows: ALLOW, BLOCK, REVIEW.

Voiceover:

The ledger shows the core idea in one place.

A verified fix can move forward.

A replay mismatch is blocked.

And an issue without a deterministic template goes to review.

---

## Closing

ReplayGuard is my prototype for moving code remediation from “looks safe” to “verified under replay.”

The broader direction I am exploring is evidence-backed software automation: before automated code changes are trusted, they should be reproduced, compared, and recorded.
