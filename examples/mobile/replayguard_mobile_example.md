# Mobile / API Secret Example

This example shows why ReplayGuard is not limited to one backend code snippet.

Mobile and web applications often interact with APIs, payment systems, identity systems, and backend services. If secrets or credentials are handled poorly, automated remediation may be needed.

Example issue:

const API_KEY = "live_mobile_prod_key_123";

ReplayGuard-style flow:

Hardcoded secret detected
→ deterministic remediation template selected
→ patch run 1 generated
→ patch run 2 generated
→ outputs compared byte-for-byte
→ evidence recorded
→ gate returns ALLOW, BLOCK, or REVIEW

Why this matters:

The risk is not only that a secret exists. The risk is that an automated fix may be trusted without evidence. ReplayGuard focuses on verifying the remediation before it moves forward.
