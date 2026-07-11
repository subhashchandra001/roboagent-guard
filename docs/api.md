# API

Required endpoints:

- `GET /`
- `GET /health`
- `GET /healthz`
- `GET /SKILL.md`
- `GET /skill.md`
- `GET /capabilities`
- `GET /.well-known/agent.json`
- `POST /v1/evaluate`
- `POST /v1/evaluate/batch`
- `GET /v1/scenarios`
- `POST /v1/scenarios/{scenario_name}/run`
- `GET /v1/evaluations/{evaluation_id}`
- `GET /v1/receipts/{evaluation_id}`
- `POST /v1/receipts/verify`
- `GET /v1/demo`
- `GET /v1/readiness`
- `POST /v1/judge-test`
- `POST /v1/agent-skill-test`
- `POST /v1/compose/mission-plan`

The public workflow is intentionally small: health check, read skill, evaluate action, then optionally fetch and verify a decision receipt.
The extra demo endpoints prove runtime readiness, the judge path, and composability without requiring a second deployment.
