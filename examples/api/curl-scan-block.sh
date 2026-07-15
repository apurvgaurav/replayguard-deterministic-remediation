#!/usr/bin/env bash

# ReplayGuard API example: BLOCK path
# This shows how a replay mismatch would stop an automated remediation flow.

curl -X POST http://127.0.0.1:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "scenario_id": "replay_mismatch_block",
    "code": "query = \"SELECT * FROM users WHERE id = \" + user_id"
  }'
