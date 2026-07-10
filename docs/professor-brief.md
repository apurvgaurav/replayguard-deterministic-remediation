# ReplayGuard: Deterministic Code Remediation with Replay Verification

## What I built

ReplayGuard is a working prototype based on my issued U.S. Patent **US 12,670,085 B1**.

The prototype demonstrates a narrow but important workflow:

> detect a code issue, apply a deterministic fix, replay it, compare both outputs, record evidence, and then decide whether the change should move forward.

This is not a production security product. It is a focused prototype to make the patent easier to understand as a working system.

---

## Why this matters

AI-assisted software development is making code changes faster. That is useful, but speed alone is not enough.

If an automated tool suggests or applies a fix, teams still need to know:

- what issue was detected
- what rule or template produced the fix
- whether the same fix can be reproduced
- whether both replay outputs match byte-for-byte
- whether evidence was recorded before the change moved forward

ReplayGuard explores this trust problem through a local full-stack prototype.

---

## Patent-backed idea

The work is based on selected concepts from:

**US 12,670,085 B1 — Deterministic Offline Code Remediation with Ledger-Verified Replay and Template-Based Patch Generation**

The main idea I am demonstrating is not just “detect a vulnerability” or “generate a fix.”

The main idea is:

> a remediation should earn trust only after it can be replayed, compared, and recorded.

---

## What the prototype demonstrates

ReplayGuard supports three gate outcomes:

- `ALLOW` — remediation replay matched and evidence was recorded
- `BLOCK` — replay mismatch was detected
- `REVIEW` — an issue was detected, but no deterministic remediation template was available

Current demo scenarios:

1. SQL Injection via Concatenation → `ALLOW`
2. Hardcoded API Key Credential → `ALLOW`
3. Unsafe Shell Execution → `ALLOW`
4. Replay Mismatch - Block Merge → `BLOCK`
5. No Template - Human Review Required → `REVIEW`

The most important part of the demo is that the system does not only approve. It can also block or route work to review when the evidence is not strong enough.

---

## Research questions I want feedback on

I would value feedback on these questions:

1. How should automated code remediation be verified before it is trusted?
2. Where does deterministic replay fit in AI-assisted software development?
3. What kind of evidence trail is useful for automated code changes?
4. Which part has stronger research potential: replay verification, template-based remediation, auditability, or human review routing?
5. What would be needed to turn this from a prototype into a stronger applied systems project?

---

## Where this could go next

Possible next directions:

- stronger AST and taint-flow analysis
- broader vulnerability coverage
- real CI/CD integration
- signed or external ledger storage
- policy-based merge gates
- evaluation on real-world code examples
- research paper around reproducible remediation for AI-assisted software workflows

---

## What feedback I am looking for

I am mainly looking for feedback on the technical direction and research framing.

The broader question I am trying to explore is:

> How should automated code changes be verified before they are trusted, especially as AI-assisted development becomes more common?

I want to keep the prototype honest and focused, while shaping it into a stronger research and product direction.
