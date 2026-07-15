"""
ReplayGuard SDK-style example.

This is not a published SDK yet.
It shows how ReplayGuard could be used by a developer workflow,
internal platform service, or AI-agent remediation pipeline.
"""

from dataclasses import dataclass


@dataclass
class ReplayGuardResult:
    decision: str
    reason: str
    ledger_hash: str


def verify_patch(code: str, source: str, policy: str = "strict-replay") -> ReplayGuardResult:
    """
    Example SDK-style wrapper.

    In a production version, this function would call the ReplayGuard API,
    submit code and metadata, and return the verification decision.
    """

    # Placeholder example response.
    # The current prototype exposes this behavior through the FastAPI backend.
    return ReplayGuardResult(
        decision="ALLOW",
        reason="Replay matched. Evidence recorded.",
        ledger_hash="sha256:example_ledger_hash",
    )


if __name__ == "__main__":
    input_code = 'query = "SELECT * FROM users WHERE id = " + user_id'

    result = verify_patch(
        code=input_code,
        source="ai_coding_agent",
        policy="strict-replay",
    )

    if result.decision == "ALLOW":
        print("ReplayGuard Gate: ALLOW")
        print("Action: allow merge candidate to continue")
    elif result.decision == "BLOCK":
        print("ReplayGuard Gate: BLOCK")
        print("Action: stop automated change")
    else:
        print("ReplayGuard Gate: REVIEW")
        print("Action: request human review")

    print(f"Reason: {result.reason}")
    print(f"Ledger hash: {result.ledger_hash}")
