# ReplayGuard Product Vision

## Product thesis

ReplayGuard is a verification layer for automated code remediation.

As AI-assisted development becomes more common, enterprises will need controls that verify automated changes before those changes enter merge or deployment workflows.

---

## Category

ReplayGuard fits into an emerging category:

AI trust infrastructure for software automation.

It is not a replacement for scanners, tests, or code review.

It is a trust gate around automated remediation.

---

## Problem

Automated code fixes can be produced by:

- AI coding agents
- SAST auto-fix tools
- internal remediation scripts
- refactoring tools
- human-created templates
- platform automation

But enterprises still need to know:

- what issue was detected
- what remediation was applied
- whether the fix is reproducible
- whether evidence was recorded
- whether the change should be allowed, blocked, or reviewed

---

## Product value

ReplayGuard provides:

- reproducibility checking
- byte-level comparison
- evidence recording
- gate decisioning
- human review routing
- integration potential with CI/CD workflows

---

## Primary users

- DevSecOps teams
- platform engineering teams
- security engineering teams
- AI governance teams
- compliance teams
- software engineering leaders

---

## MVP

The current MVP demonstrates:

- FastAPI backend
- React/Vite dashboard
- selected remediation scenarios
- deterministic templates
- replay verification
- byte-level comparison
- ledger-style evidence
- ALLOW / BLOCK / REVIEW decisions
- API, SDK, CI/CD, mobile, and AI-agent example patterns

---

## Future product surface

ReplayGuard can become:

- ReplayGuard API
- ReplayGuard SDK
- ReplayGuard GitHub Action
- ReplayGuard Jenkins plugin
- ReplayGuard Evidence Ledger
- ReplayGuard Policy Gate
- ReplayGuard Review Router

---

## Why now

AI-assisted development is increasing the speed of software change.

The faster automated changes move, the more important it becomes to verify, reproduce, and audit them before they propagate.

---

## Strategic positioning

ReplayGuard moves automated remediation from:

> looks safe

to:

> verified under replay
