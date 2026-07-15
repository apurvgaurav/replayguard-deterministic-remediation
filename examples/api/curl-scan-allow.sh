#!/usr/bin/env bash

# ReplayGuard API example: ALLOW path
# This shows ReplayGuard used as a backend verification service.

curl -X POST http://127.0.0.1:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "scenario_id": "sql_injection",
    "code": "query = \"SELECT * FROM users WHERE id = \" + user_id"
  }'
