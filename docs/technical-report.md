# RoboAgent Guard Technical Report

## 1. Introduction

RoboAgent Guard is a deterministic FastAPI service for evaluating proposed mobile-robot actions before anything is applied in a digital twin. It makes hidden robot risks visible by combining authorization checks, replay and freshness protection, physical safety scoring, SLAM reliability analysis, privacy policy enforcement, deterministic simulation, and audit logging.

The project is intentionally self-contained. It does not require ROS, Gazebo, a real robot, Redis, a database, external APIs, paid services, or external LLMs. A previously unfamiliar agent or engineer should be able to discover and operate the service from `SKILL.md`, the API discovery routes, and this report.

## 2. System Goals

The service answers one core question: should a requested robot action be allowed, modified, blocked, or escalated before the digital twin applies it?

The autonomy goal is minimum human intervention. Agents are expected to use the response directly for routine operation: execute approved actions, honor constraints, replace unsafe actions with `recommended_action`, or execute nothing on `block`. Human review is reserved for stale evidence or uncertainty that the deterministic policy cannot safely resolve.

Primary decisions:

- `approve`: execute the requested action.
- `approve_with_constraints`: execute the requested action while returning operational constraints.
- `modify`: execute only the recommended safer replacement action.
- `block`: execute nothing; return a safe stop recommendation.
- `request_human_approval`: exception path; do not execute until fresh evidence or human approval is available.

Hard constraints always override weighted scores. The service never trusts client-provided risk scores or plain text safety claims, and no LLM makes the final decision.

## 3. Runtime Architecture

RoboAgent Guard uses one FastAPI deployment. Specialized agents are internal Python components:

```text
HTTP request
  -> FastAPI route
  -> schema and image-payload validation
  -> replay and freshness guards
  -> authorization agent
  -> physical risk agent
  -> SLAM reliability agent
  -> privacy agent
  -> supervisor decision
  -> deterministic digital twin
  -> audit chain and NANDA-style trace
  -> JSON response
```

Important runtime files:

- `src/roboagent_guard/app.py`: FastAPI app, discovery endpoints, evaluation endpoints, scenario endpoints, demo endpoint, judge endpoint.
- `src/roboagent_guard/simulator/runner.py`: orchestration engine for all guards, agents, supervisor, twin, audit, and trace export.
- `src/roboagent_guard/agents/authorization.py`: role/action authorization checks.
- `src/roboagent_guard/agents/physical_risk.py`: obstacle, speed, surface, disturbance, and battery risk.
- `src/roboagent_guard/agents/slam_reliability.py`: illumination, blur, inlier ratio, confidence, entropy, and sensor-age risk.
- `src/roboagent_guard/agents/privacy.py`: raw camera, face data, private zone, storage, retention, and recipient policy.
- `src/roboagent_guard/agents/supervisor.py`: final deterministic decision and recommended replacement action.
- `src/roboagent_guard/security/replay_guard.py`: duplicate `request_id`, duplicate `nonce`, and blocked-action replay detection.
- `src/roboagent_guard/security/freshness.py`: timestamp and sensor-age checks with request-injected deterministic evaluation time.
- `src/roboagent_guard/security/input_safety.py`: rejects actual image-like payloads; camera use is represented by metadata flags only.
- `src/roboagent_guard/simulator/digital_twin.py`: deterministic state transition using seeded random generation only.
- `src/roboagent_guard/audit/store.py`: append-only audit records with chained hashes.
- `static/index.html`: browser console for running demos and inspecting traces.

## 4. Data Model

The main request type is `EvaluationRequest` in `src/roboagent_guard/models/requests.py`.

Required fields:

- `request_id`: unique request identifier.
- `nonce`: unique anti-replay nonce.
- `timestamp`: timezone-aware timestamp.
- `caller`: caller id, role, and authorized action list.
- `action`: requested robot action and metadata flags.
- `robot_state`: battery, emergency stop, obstacle distance, surface, pitch, and roll.
- `perception`: illumination, blur, SLAM confidence data, map entropy, and sensor age.
- `privacy`: person/private-zone/face/filter/recipient/retention context.
- `simulation_seed`: deterministic seed.

Optional fields:

- `evaluation_time`: optional timezone-aware evaluation snapshot time for explicit freshness testing.
- `approval.token`: approval token, if available.
- `client_risk_score`: accepted as input but ignored for final safety decisions.
- `safety_approved`: accepted as input but ignored for final safety decisions.
- `metadata`: small arbitrary metadata map. Image-like keys such as `image`, `frame`, `camera_frame`, and `base64_image` are rejected.

## 5. Request Flow

`POST /v1/evaluate` performs the production evaluation flow:

1. Read raw JSON.
2. Reject actual image-like payloads.
3. Validate against Pydantic schemas.
4. Check replay guard for repeated request IDs, nonces, or blocked action evidence.
5. Check freshness against `evaluation_time` when supplied, otherwise against the request `timestamp` as the deterministic snapshot time.
6. Consume approval token if present.
7. Run authorization, physical risk, SLAM reliability, privacy, and replay/freshness components.
8. Let the supervisor combine component outputs.
9. Apply the digital twin only for `approve`, `approve_with_constraints`, or `modify`.
10. For `modify`, apply only the recommended replacement action.
11. Do not apply anything for `block` or `request_human_approval`.
12. Write audit and trace data.
13. Return the complete decision trace.

`POST /v1/evaluate/batch` applies the same model validation and embedded image rejection to every request in the batch.

Scenario/demo routes use an isolated replay guard so the UI examples are repeatable. The production `/v1/evaluate` and `/v1/evaluate/batch` routes keep replay memory strict.

## 6. Endpoint Reference

Discovery and UI:

- `GET /`: static browser console.
- `GET /health`: service health and version.
- `GET /SKILL.md`: agent-facing operating instructions.
- `GET /skill.md`: lowercase alias for registries or agents that expect this path.
- `GET /capabilities`: supported policy version, actions, decisions, autonomy model, required fields, optional fields, and scenarios.
- `GET /.well-known/agent.json`: agent card.
- `GET /docs`: OpenAPI UI generated by FastAPI.

Evaluation:

- `POST /v1/evaluate`: evaluate one action request.
- `POST /v1/evaluate/batch`: evaluate 1 to 25 action requests.
- `GET /v1/evaluations/{evaluation_id}`: retrieve an evaluation produced during the current process lifetime.

Scenarios and demos:

- `GET /v1/scenarios`: list built-in scenarios and expected decisions.
- `POST /v1/scenarios/{scenario_name}/run?seed=42`: run a deterministic scenario.
- `GET /v1/demo`: run the demo pack.
- `POST /v1/judge-test`: local pass/fail sanity check for safe and unsafe examples.

## 7. Built-In Scenarios

Scenario YAML files live under `scenarios/`.

Current scenarios:

- `normal_navigation`: expected `approve`.
- `low_light_slow_motion`: expected `approve_with_constraints`.
- `low_light_high_speed`: expected `modify`.
- `uneven_surface_high_blur`: expected `modify`.
- `slam_degradation`: expected `modify`.
- `person_in_private_zone`: expected `approve_with_constraints`.
- `unauthorized_camera_request`: expected `block`.
- `replayed_approved_action`: expected `block`.
- `hidden_low_slam_confidence`: expected `modify`.
- `combined_safety_privacy_crisis`: expected `block`.

## 8. Determinism Rules

The service is deterministic by design:

- Tests and engine logic use injected timestamps.
- The digital twin uses `random.Random(seed)`, never unseeded randomness.
- No wall-clock time is used in simulation transitions.
- Same inputs and seeds produce byte-identical traces.
- Replay state is explicit and deterministic within a process.

Deterministic trace identity is based on the request ID, nonce, seed, and decision. The full response includes a `trace_hash` computed from the response payload.

## 9. Digital Twin Behavior

The digital twin is deliberately lightweight and deterministic:

- `stop`: speed becomes zero.
- `slow_down`: speed is capped at 0.15 m/s.
- `relocalize`: speed becomes zero and SLAM/confidence improve with seeded pseudo-random increments.
- `navigate`: position moves toward the target by at most the requested speed and battery decreases deterministically.
- `return_to_base`: position returns to origin and battery decreases slightly.
- Blocked actions are not applied.

## 10. Privacy and Image Policy

Actual images are not accepted or stored. Camera use is represented using metadata flags:

- `share_raw_camera`
- `store_sensor_data`
- `face_data_present`
- `privacy_filter_applied`
- `recipient_authorized`
- `retention_seconds`

Policy behavior:

- Unauthorized raw-camera sharing is blocked.
- Raw storage in private zones is blocked.
- Face data sharing without a filter is blocked.
- Long retention is modified with a `reduce_retention` control.
- Private-zone/person contexts are allowed only with conservative constraints when no hard block is triggered.

## 11. Frontend Console

The static UI in `static/index.html` provides:

- service health and policy summary;
- quick safe, crisis, and full-demo buttons;
- scenario selection and expected-decision display;
- final decision, risk level, risk bars, replay status, and digital twin status;
- component-level cards for authorization, physical risk, SLAM, privacy, and replay/freshness;
- full JSON trace output and copy button.

The UI calls only local API endpoints and does not require external assets.

## 12. Local Setup

Prerequisites:

- Python 3.12 or newer.
- `uv`.

Install and run:

```bash
uv sync
uv run uvicorn roboagent_guard.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Run with the package entry point:

```bash
uv run roboagent-guard
```

## 13. Useful Commands

Run the full test suite:

```bash
uv run pytest
```

Run API tests:

```bash
uv run pytest tests/api/test_endpoints.py
```

Run lint:

```bash
uv run ruff check .
```

Run type checks:

```bash
uv run pyright
```

Verify one scenario determinism:

```bash
uv run python scripts/verify_determinism.py --scenario normal_navigation --seed 42
```

Run a scenario from the command line:

```bash
uv run python scripts/run_demo.py --scenario low_light_slow_motion --seed 42
```

Verify the audit chain:

```bash
uv run python scripts/verify_audit_chain.py
```

Run judge check locally:

```bash
uv run python scripts/run_judge_test.py --local
```

If uv cannot write to its default cache in a restricted environment, redirect the cache:

```bash
uv --cache-dir /tmp/uv-cache run pytest
```

## 14. Deployment

Render deployment files are present:

- `render.yaml`
- `pyproject.toml`
- `uv.lock`

The service reads `PORT` in `src/roboagent_guard/app.py` when using the `roboagent-guard` entry point. For hosted deployments, set:

```text
PUBLIC_BASE_URL=https://your-service.example
AUDIT_PATH=artifacts/traces/audit.jsonl
NANDA_TRACE_DIR=artifacts/nanda_traces
```

No external database, Redis, ROS, Gazebo, or third-party model service is required.

## 15. Verification Performed

During the latest hardening pass, these checks were run successfully:

```bash
uv run pytest
uv run pytest tests/api/test_endpoints.py
uv run ruff check .
uv run pyright
uv --cache-dir /tmp/uv-cache run python scripts/verify_determinism.py --scenario <each scenario> --seed 42
uv run python scripts/verify_audit_chain.py
uv run python scripts/run_demo.py --scenario low_light_slow_motion --seed 42
uv run python scripts/run_judge_test.py --local
```

Live endpoint verification was also performed against a local uvicorn server. The following endpoints returned `200` and behaved as expected:

- `/`
- `/health`
- `/SKILL.md`
- `/capabilities`
- `/.well-known/agent.json`
- `/v1/scenarios`
- `/v1/demo`
- `/docs`
- every `POST /v1/scenarios/{scenario_name}/run?seed=42`
- `GET /v1/evaluations/{evaluation_id}`
- `POST /v1/judge-test`

## 16. Fixes From The Hardening Pass

The pass corrected these issues:

- Scenario and demo routes now use isolated replay guards, so the browser console remains repeatable while production evaluation remains strict.
- `/v1/judge-test` now isolates safe and unsafe judge examples, so repeated judge checks do not poison themselves through replay memory.
- Embedded image-like payloads are rejected at the `EvaluationRequest` model layer, so both single and batch evaluation enforce the no-actual-images rule.
- `/capabilities` now uses the active app settings instead of constructing separate settings.
- The UI now includes component cards, safer HTML text rendering, clearer demo status, and a more polished operational dashboard.

## 17. Troubleshooting

If a request returns `422`, check schema shape, timestamp timezone, numeric bounds, and prohibited image-like keys.

If a request returns `block` with replay codes, send a new `request_id` and `nonce`. Do not retry production requests with the same nonce.

If a scenario demo unexpectedly blocks in the UI, restart the server and confirm the code includes isolated scenario/demo replay guards.

If audit verification fails, inspect `artifacts/traces/audit.jsonl` for manual edits or interrupted writes.

If deterministic checks fail, confirm no unseeded random calls or wall-clock simulation transitions were introduced.
