# AI Agent Patch Verification Example

ReplayGuard is not another AI code generator.

It is a verification layer that can sit downstream of AI coding agents, SAST auto-fix tools, internal scripts, or human-created remediation candidates.

## Concept

An AI coding agent may propose a fix.

ReplayGuard asks a different question:

Can the proposed remediation be replayed, compared, evidenced, and gated before it moves forward?

## Example flow

AI coding agent proposes a patch
→ ReplayGuard receives the candidate remediation context
→ deterministic remediation policy is applied
→ patch run 1 is generated
→ patch run 2 is generated
→ outputs are compared byte-for-byte
→ ledger-style evidence is recorded
→ gate returns ALLOW, BLOCK, or REVIEW

## Why this matters

AI-generated code may look correct, but appearance is not enough for enterprise trust.

ReplayGuard treats automated fixes as untrusted until they survive replay verification.

## Key point

The AI can propose. ReplayGuard verifies whether the change has earned trust.
