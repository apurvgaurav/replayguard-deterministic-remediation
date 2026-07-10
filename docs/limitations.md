# ReplayGuard Limitations

ReplayGuard is a prototype.

It is meant to demonstrate the replay-verification workflow behind the patent, not to claim full production coverage.

The current version is intentionally narrow. That is by design.

---

## 1. Limited scenario coverage

The prototype supports selected Python examples:

- SQL injection through string concatenation
- hardcoded API key
- unsafe shell execution
- replay mismatch
- unsafe eval routed to review

It does not cover all vulnerability types.

---

## 2. Simple rule engine

The current rule engine uses simple pattern-based detection.

A stronger version would need deeper parsing, stronger AST analysis, taint-flow tracking, and better rule coverage.

---

## 3. Template-based remediation is narrow

ReplayGuard currently applies deterministic remediation templates for selected examples.

That is useful for showing the concept, but it is not the same as handling every possible real-world code pattern.

The point of the prototype is not broad automatic fixing.

The point is to show that when a deterministic fix is applied, it should be replayed, compared, and recorded before it moves forward.

---

## 4. Local demo ledger

The ledger in this prototype is local demo storage.

It records useful evidence for the demo, including hashes and gate decisions, but it should not be treated as a full audit system.

A production version would need stronger storage, signing, access control, retention policy, and integration with enterprise logging or compliance systems.

---

## 5. No live CI/CD integration yet

The frontend shows a merge gate decision: `ALLOW`, `BLOCK`, or `REVIEW`.

That represents the CI/CD decision point, but the current prototype is not wired into a live GitHub Actions, Jenkins, GitLab, or enterprise release pipeline.

That would be a logical next step.

---

## 6. Security claims are limited

ReplayGuard does not guarantee that code is secure.

It does not replace secure coding, code review, testing, SAST tools, or human security review.

The prototype demonstrates one layer: replay verification and evidence recording for selected deterministic remediation scenarios.

---

## 7. Why the prototype still matters

Even with the limitations, the prototype makes the core idea visible:

> automated remediation should create evidence before it earns trust.

For me, that is the important direction.

As AI-assisted development becomes more common, software teams will need more than fast code generation. They will need stronger ways to verify, reproduce, and audit automated changes.
