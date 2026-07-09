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
- `GET /v1/demo`
- `POST /v1/judge-test`

The public workflow is intentionally small: health check, read skill, evaluate action.
