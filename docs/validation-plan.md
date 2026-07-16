# ReplayGuard Validation Plan

ReplayGuard is currently a focused prototype.

The MVP proves the core trust-gate workflow:

detect issue
→ apply deterministic remediation
→ replay remediation
→ compare outputs
→ record evidence
→ return ALLOW, BLOCK, or REVIEW

The next step is not to overclaim production adoption.

The next step is to validate the trust-gate pattern with stronger evidence.

---

## Validation goals

ReplayGuard should be evaluated across four dimensions:

1. Technical correctness
2. Developer workflow fit
3. Enterprise governance value
4. AI-agent remediation relevance

The goal is to determine whether evidence-backed verification can improve trust in automated remediation workflows.

---

## Near-term validation steps

### 1. Expert review

Share the prototype and video with:

- professors
- senior engineers
- Principal Engineers
- AppSec engineers
- DevSecOps practitioners
- AI product leaders

Ask whether the trust-gate framing is meaningful and whether ALLOW / BLOCK / REVIEW maps to real software delivery concerns.

### 2. Benchmark expansion

Expand beyond selected demo cases.

Potential benchmark dimensions:

- more vulnerability categories
- more languages
- deterministic vs non-deterministic remediation behavior
- replay match rate
- review routing rate
- false positive and false negative behavior
- gate latency

### 3. AI-agent remediation testing

Test the workflow with patches proposed by AI coding tools or remediation agents.

The purpose is to separate patch generation from patch trust.

The AI may propose a fix.

ReplayGuard should verify whether that fix can be replayed, compared, evidenced, and gated.

### 4. CI/CD gate simulation

Simulate ReplayGuard as a pull-request or deployment gate.

Possible gate outcomes:

- ALLOW: replay matched and evidence was recorded
- BLOCK: replay mismatch or failed verification
- REVIEW: no deterministic remediation path available

### 5. Pilot-style evaluation

A future pilot can test ReplayGuard against real or representative repositories.

The pilot should measure whether the system improves control, auditability, and review routing around automated remediation.

---

## Potential validation metrics

A mature ReplayGuard-style product could be measured by:

- replay match rate
- unstable automated changes blocked
- unsupported cases routed to human review
- evidence coverage
- CI/CD gate latency
- policy violation trend
- developer override rate
- reviewer acceptance rate
- remediation category coverage
- false positive and false negative rates

---

## What validation should not claim prematurely

This prototype should not claim:

- production adoption
- complete security coverage
- replacement of SAST tools
- replacement of human review
- full AI-agent implementation
- full CI/CD plugin maturity
- guarantee of secure code

The correct claim is narrower and stronger:

ReplayGuard demonstrates how automated remediation can be verified through replay evidence before trust is granted.

---

## Validation thesis

The prototype is intentionally focused.

The validation path is broader.

ReplayGuard should be tested as a trust boundary between automated patch generation and software delivery workflows.

The central question is:

Can automated remediation create enough evidence to be trusted before it moves forward?
