# RoboAgent Guard

## Making Invisible Robot Risk Visible through Agentic Digital Twins

RoboAgent Guard is a FastAPI service that evaluates proposed mobile-robot actions for authorization, replay/freshness, physical risk, SLAM reliability, and privacy risk. It returns `approve`, `approve_with_constraints`, `modify`, `block`, or `request_human_approval`, then simulates approved or modified actions in a deterministic digital twin.

This is the main NandaHack service submission: a hosted API plus `SKILL.md` that an unfamiliar AI agent can use without human guidance.

For a complete architecture, flow, code map, endpoint, command, testing, and deployment guide, read [`docs/technical-report.md`](docs/technical-report.md).

For final NandaHack Phase 2 submission steps, registry fields, live endpoint lines, and video-demo guidance, read [`docs/submission-checklist.md`](docs/submission-checklist.md) and [`docs/video-demo-script.md`](docs/video-demo-script.md).

## Quickstart

```bash
uv sync
uv run uvicorn roboagent_guard.app:app --host 127.0.0.1 --port 8000 --reload
```

Check:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/SKILL.md
curl --fail http://127.0.0.1:8000/skill.md
curl --fail http://127.0.0.1:8000/capabilities
```

## Primary Workflow

1. `GET /health`
2. `GET /SKILL.md`
3. `POST /v1/evaluate`
4. Execute only the returned `recommended_action` when the decision is `modify`.
5. Execute nothing when the decision is `block`.

## Demo

```bash
uv run python scripts/run_demo.py --scenario normal_navigation --seed 42
uv run python scripts/run_demo.py --scenario low_light_high_speed --seed 42
uv run python scripts/run_demo.py --scenario unauthorized_camera_request --seed 42
uv run python scripts/run_demo.py --scenario combined_safety_privacy_crisis --seed 42
uv run python scripts/run_judge_test.py --local
```

## Required Endpoints

- `GET /`
- `GET /health`
- `GET /SKILL.md`
- `GET /skill.md`
- `GET /healthz`
- `GET /capabilities`
- `GET /.well-known/agent.json`
- `POST /v1/evaluate`
- `POST /v1/evaluate/batch`
- `GET /v1/scenarios`
- `POST /v1/scenarios/{scenario_name}/run`
- `GET /v1/evaluations/{evaluation_id}`
- `GET /v1/demo`
- `POST /v1/judge-test`

## Quality Gates

```bash
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q
uv run pytest --cov=roboagent_guard --cov-report=term-missing
```

## Deployment

Render is configured in `render.yaml`.

Build command:

```bash
pip install uv && uv sync --frozen --no-dev
```

Start command:

```bash
uv run --no-sync uvicorn roboagent_guard.app:app --host 0.0.0.0 --port $PORT
```

Set:

```text
PUBLIC_BASE_URL=https://YOUR-SERVICE.onrender.com
POLICY_VERSION=1.0.0
AUDIT_PATH=/tmp/roboagent-guard-audit.jsonl
```

## Limitations

RoboAgent Guard is currently a deterministic, simulation-based prototype. It validates agent coordination, safety policies, SLAM-aware supervisory logic, privacy controls, replay resistance, and digital-twin behavior without requiring a physical robot. It has not yet been validated as a safety-certified controller or through physical TurtleBot4 experiments. ROS 2 and real-robot evaluation are planned as future work.
