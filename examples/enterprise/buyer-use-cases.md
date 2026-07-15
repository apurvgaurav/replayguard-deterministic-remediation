# ReplayGuard Enterprise Use Cases

ReplayGuard is positioned as trust infrastructure for automated software change.

## Potential users

- DevSecOps teams
- Platform engineering teams
- Security engineering teams
- AI governance teams
- Regulated software companies
- CI/CD platform owners
- AI coding tool vendors

## Use case 1 — AI-assisted remediation gate

An AI coding assistant proposes a code fix. ReplayGuard verifies whether the remediation is reproducible before the change is allowed to move forward.

## Use case 2 — SAST auto-fix verification

A scanner detects an issue and proposes an automated fix. ReplayGuard runs replay verification and records evidence before merge.

## Use case 3 — CI/CD release control

A pull request contains an automated remediation candidate. ReplayGuard acts as a gate that returns ALLOW, BLOCK, or REVIEW.

## Use case 4 — Compliance evidence

ReplayGuard records hashes, matched rules, template IDs, comparison outcomes, and decisions. This creates evidence for why an automated change was allowed, blocked, or routed to review.

## Use case 5 — Human review routing

If no deterministic remediation template exists, ReplayGuard returns REVIEW instead of inventing a fix.

## Product thesis

Enterprises will not only need tools that generate code. They will need trust gates that verify automated code changes before those changes propagate.
