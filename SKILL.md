# RoboAgent Guard

Deterministic safety and privacy gate that lets agents evaluate and adapt mobile-robot actions before a digital twin applies them, with human escalation only for exceptional uncertainty.

## Base URL

PUBLIC_BASE_URL

## What This Service Does

RoboAgent Guard checks a proposed mobile-robot action for authorization, replay, freshness, physical safety, SLAM reliability, and privacy risk. It returns a deterministic decision: `approve`, `approve_with_constraints`, `modify`, `block`, or `request_human_approval`. The normal path is agent-autonomous: the calling agent can continue, constrain, replace, or stop the action from the response alone. Human review is an exception path for stale evidence or unresolved uncertainty.

## Autonomy Model

- Default mode: no routine human intervention.
- The agent may proceed automatically on `approve`.
- The agent may proceed automatically with returned `constraints` on `approve_with_constraints`.
- The agent may proceed automatically with only `recommended_action` on `modify`.
- The agent must execute nothing on `block`.
- The agent asks a human only when `decision` is `request_human_approval` or `human_approval_required` is true.

## How The Agent Should Use This

1. Call `GET /health` first.
2. Read `GET /capabilities` to confirm supported actions and decisions.
3. Before any mobile-robot action, call `POST /v1/evaluate` with fresh robot, perception, and privacy metadata.
4. If the decision is `approve`, execute the original action.
5. If the decision is `approve_with_constraints`, execute the original action while honoring `constraints`.
6. If the decision is `modify`, do not execute the original action; execute only `recommended_action`.
7. If the decision is `block`, execute nothing.
8. Ask a human only if `human_approval_required` is true or the decision is `request_human_approval`.
9. Never retry the same `request_id` or `nonce`.
10. Do not send images. Camera use is represented only by metadata flags such as `share_raw_camera`, `face_data_present`, and `privacy_filter_applied`.

## Decision Meanings

- `approve`: execute the original action.
- `approve_with_constraints`: execute the original action while honoring returned constraints.
- `modify`: execute only the returned `recommended_action`.
- `block`: execute nothing; the digital twin does not apply the action.
- `request_human_approval`: pause execution and ask a human for review because evidence is stale or uncertainty cannot be resolved automatically.

## Evaluation Request Fields

Required top-level JSON fields for `POST /v1/evaluate`:

- `request_id`
- `nonce`
- `timestamp`
- `caller`
- `action`
- `robot_state`
- `perception`
- `privacy`
- `simulation_seed`

Optional top-level JSON fields:

- `evaluation_time`
- `approval`
- `client_risk_score`
- `safety_approved`
- `metadata`

Use a timezone-aware timestamp. Use a unique `request_id` and `nonce` for every production evaluation.
If `evaluation_time` is omitted, the service treats `timestamp` as the deterministic evaluation snapshot time. To explicitly test stale evidence, provide `evaluation_time` later than `timestamp`.

## Endpoints

### GET /

Returns the browser dashboard for optional demo inspection. Agents do not need this page for routine operation.

Example:

```bash
curl --fail PUBLIC_BASE_URL/
```

Example response:

```html
<!doctype html>
<html lang="en">...</html>
```

### GET /health

Returns service health and version.

Example:

```bash
curl --fail PUBLIC_BASE_URL/health
```

Example response:

```json
{"status":"ok","service":"roboagent-guard","version":"1.0.0"}
```

### GET /healthz

Alias for `GET /health`. This is useful for hosting platform health checks.

Example:

```bash
curl --fail PUBLIC_BASE_URL/healthz
```

Example response:

```json
{"status":"ok","service":"roboagent-guard","version":"1.0.0"}
```

### GET /SKILL.md

Returns this agent-facing Markdown file.

Example:

```bash
curl --fail PUBLIC_BASE_URL/SKILL.md
```

Example response:

```markdown
# RoboAgent Guard

Deterministic safety and privacy gate that evaluates mobile-robot actions before a digital twin applies them.
```

### GET /skill.md

Lowercase alias for `GET /SKILL.md`. Use this if a registry or agent expects lowercase skill paths.

Example:

```bash
curl --fail PUBLIC_BASE_URL/skill.md
```

Example response:

```markdown
# RoboAgent Guard

Deterministic safety and privacy gate that evaluates mobile-robot actions before a digital twin applies them.
```

### GET /capabilities

Returns policy version, supported actions, supported decisions, required fields, and built-in scenarios.

Example:

```bash
curl --fail PUBLIC_BASE_URL/capabilities
```

Example response:

```json
{
  "service": "roboagent-guard",
  "policy_version": "1.0.0",
  "supported_actions": ["navigate", "stop", "slow_down", "rotate", "relocalize", "save_map", "update_map", "share_sensor_summary", "share_raw_camera", "disable_storage", "return_to_base"],
  "supported_decisions": ["approve", "approve_with_constraints", "modify", "block", "request_human_approval"],
  "autonomy_model": {"default": "agent_autonomous", "human_intervention": "exception_only"},
  "required_fields": ["request_id", "nonce", "timestamp", "caller", "action", "robot_state", "perception", "privacy", "simulation_seed"],
  "optional_fields": ["evaluation_time", "approval", "client_risk_score", "safety_approved", "metadata"],
  "scenario_names": ["combined_safety_privacy_crisis", "hidden_low_slam_confidence", "low_light_high_speed", "low_light_slow_motion", "normal_navigation", "person_in_private_zone", "replayed_approved_action", "slam_degradation", "unauthorized_camera_request", "uneven_surface_high_blur"]
}
```

### GET /.well-known/agent.json

Returns an agent card with service metadata and primary endpoint information.

Example:

```bash
curl --fail PUBLIC_BASE_URL/.well-known/agent.json
```

Example response:

```json
{
  "name": "RoboAgent Guard",
  "description": "Evaluates proposed mobile-robot actions for physical, SLAM, authorization, replay, and privacy risks.",
  "version": "1.0.0",
  "base_url": "PUBLIC_BASE_URL",
  "skill_url": "PUBLIC_BASE_URL/SKILL.md",
  "health_url": "PUBLIC_BASE_URL/health",
  "capabilities_url": "PUBLIC_BASE_URL/capabilities",
  "primary_endpoint": {"method": "POST", "path": "/v1/evaluate"},
  "authentication": {"required": false, "note": "Hackathon demonstration service. Caller authorization is represented in the request and verified against demonstration policy."}
}
```

### POST /v1/evaluate

Evaluates one proposed mobile-robot action and returns the decision trace.

Example:

```bash
curl --fail -X POST PUBLIC_BASE_URL/v1/evaluate \
  -H 'Content-Type: application/json' \
  --data '{"request_id":"safe-REPLACE-WITH-UNIQUE-ID","nonce":"safe-nonce-REPLACE-WITH-UNIQUE-ID","timestamp":"2026-07-04T16:00:00Z","caller":{"id":"planner-01","role":"planner","authorized_actions":["navigate","stop","relocalize"]},"action":{"type":"navigate","linear_speed_mps":0.15,"angular_speed_rps":0.0,"target":{"x":1.0,"y":0.0},"save_map":false,"share_raw_camera":false,"store_sensor_data":false,"recipient_id":null},"robot_state":{"battery_percent":80.0,"emergency_stop_available":true,"nearest_obstacle_m":2.0,"surface":"smooth","pitch_disturbance_deg":1.0,"roll_disturbance_deg":1.0},"perception":{"illumination_lux":150.0,"blur_score":0.1,"slam_inlier_ratio":0.9,"localization_confidence":0.95,"map_entropy":0.1,"sensor_age_ms":100},"privacy":{"person_detected":false,"private_zone":false,"face_data_present":false,"privacy_filter_applied":false,"recipient_authorized":false,"retention_seconds":0},"approval":{"token":null},"simulation_seed":42}'
```

Example response:

```json
{
  "evaluation_id": "eval-30a74d1160b5",
  "request_id": "safe-REPLACE-WITH-UNIQUE-ID",
  "decision": "approve",
  "risk_level": "low",
  "risk_score": 0.045,
  "slam_risk_score": 0.03166666666666667,
  "privacy_risk_score": 0.0,
  "authorization_passed": true,
  "freshness_passed": true,
  "replay_detected": false,
  "human_approval_required": false,
  "recommended_action": {"type": "navigate", "linear_speed_mps": 0.15, "angular_speed_rps": 0.0, "target": {"x": 1.0, "y": 0.0}, "save_map": false, "share_raw_camera": false, "store_sensor_data": false, "recipient_id": null},
  "constraints": [],
  "reasons": ["Caller is authorized.", "Obstacle clearance and motion risk are acceptable.", "SLAM reliability is high.", "No privacy-sensitive collection was requested.", "Request is fresh and unique."],
  "violation_codes": [],
  "policy_version": "1.0.0"
}
```

### POST /v1/evaluate/batch

Evaluates a batch of 1 to 25 proposed mobile-robot actions.

Example:

```bash
curl --fail -X POST PUBLIC_BASE_URL/v1/evaluate/batch \
  -H 'Content-Type: application/json' \
  --data '{"requests":[{"request_id":"batch-safe-REPLACE-WITH-UNIQUE-ID","nonce":"batch-safe-nonce-REPLACE-WITH-UNIQUE-ID","timestamp":"2026-07-04T16:00:00Z","caller":{"id":"planner-01","role":"planner","authorized_actions":["navigate","stop","relocalize"]},"action":{"type":"navigate","linear_speed_mps":0.15,"angular_speed_rps":0.0,"target":{"x":1.0,"y":0.0},"save_map":false,"share_raw_camera":false,"store_sensor_data":false,"recipient_id":null},"robot_state":{"battery_percent":80.0,"emergency_stop_available":true,"nearest_obstacle_m":2.0,"surface":"smooth","pitch_disturbance_deg":1.0,"roll_disturbance_deg":1.0},"perception":{"illumination_lux":150.0,"blur_score":0.1,"slam_inlier_ratio":0.9,"localization_confidence":0.95,"map_entropy":0.1,"sensor_age_ms":100},"privacy":{"person_detected":false,"private_zone":false,"face_data_present":false,"privacy_filter_applied":false,"recipient_authorized":false,"retention_seconds":0},"approval":{"token":null},"simulation_seed":42}]}'
```

Example response:

```json
{
  "results": [
    {
      "request_id": "batch-safe-REPLACE-WITH-UNIQUE-ID",
      "decision": "approve",
      "risk_level": "low",
      "recommended_action": {"type": "navigate", "linear_speed_mps": 0.15}
    }
  ]
}
```

### GET /v1/scenarios

Lists built-in deterministic scenarios and their expected decisions.

Example:

```bash
curl --fail PUBLIC_BASE_URL/v1/scenarios
```

Example response:

```json
[
  {"name": "normal_navigation", "expected_decision": "approve", "description": "Safe nominal navigation."},
  {"name": "combined_safety_privacy_crisis", "expected_decision": "block", "description": "Combined physical, SLAM, privacy, and authorization crisis."}
]
```

### POST /v1/scenarios/{scenario_name}/run

Runs one built-in deterministic scenario. Use this for demos and quick validation.

Example:

```bash
curl --fail -X POST 'PUBLIC_BASE_URL/v1/scenarios/normal_navigation/run?seed=42'
```

Example response:

```json
{
  "request_id": "normal-navigation",
  "decision": "approve",
  "risk_level": "low",
  "risk_score": 0.045,
  "recommended_action": {"type": "navigate", "linear_speed_mps": 0.15},
  "digital_twin": {"action_applied": true}
}
```

### GET /v1/evaluations/{evaluation_id}

Retrieves an evaluation created during the current process lifetime.

Example:

```bash
curl --fail PUBLIC_BASE_URL/v1/evaluations/eval-18ee54408a7c
```

Example response:

```json
{
  "evaluation_id": "eval-18ee54408a7c",
  "request_id": "normal-navigation",
  "decision": "approve",
  "risk_level": "low"
}
```

### GET /v1/demo

Runs a small demo pack containing safe, modified, and blocked cases.

Example:

```bash
curl --fail PUBLIC_BASE_URL/v1/demo
```

Example response:

```json
{
  "service": "roboagent-guard",
  "scenarios": {
    "normal_navigation": {"decision": "approve", "risk_score": 0.045, "recommended_action": "navigate"},
    "low_light_high_speed": {"decision": "modify", "risk_score": 0.65, "recommended_action": "relocalize"},
    "unauthorized_camera_request": {"decision": "block", "risk_score": 1.0, "recommended_action": "stop"},
    "combined_safety_privacy_crisis": {"decision": "block", "risk_score": 1.0, "recommended_action": "stop"}
  }
}
```

### POST /v1/judge-test

Runs a lightweight local judge sanity check: a safe request must approve and a crisis request must block.

Example:

```bash
curl --fail -X POST PUBLIC_BASE_URL/v1/judge-test
```

Example response:

```json
{"passed": true, "safe_decision": "approve", "unsafe_decision": "block"}
```

## Recommended Agent Workflow

Use this exact flow when controlling or simulating a robot action:

1. Call `GET /health`.
2. Call `GET /capabilities`.
3. Build a fresh `POST /v1/evaluate` payload with a unique `request_id` and `nonce`.
4. Submit the action before execution.
5. Read `decision`, `recommended_action`, `constraints`, `reasons`, and `digital_twin.action_applied`.
6. If `decision` is `modify`, execute only `recommended_action`.
7. If `decision` is `block`, execute nothing.
8. If `decision` is `request_human_approval`, ask a human supervisor before proceeding. This is an exception path, not the normal operating path.

## Safe Test Call

This call should return `decision: approve`:

```bash
curl --fail -X POST 'PUBLIC_BASE_URL/v1/scenarios/normal_navigation/run?seed=42'
```

## Crisis Test Call

This call should return `decision: block`:

```bash
curl --fail -X POST 'PUBLIC_BASE_URL/v1/scenarios/combined_safety_privacy_crisis/run?seed=42'
```

## Error Recovery

- If HTTP `422` is returned, fix invalid or missing fields and use a new `request_id` and `nonce`.
- If a freshness violation appears, collect fresh robot/perception state and submit a new request.
- If a replay violation appears, do not reuse the same request ID or nonce.
- If raw camera or private-zone storage is blocked, remove raw sharing/storage or apply privacy filters.

## Agent Success Checklist

- [ ] `GET /health` returned `ok`.
- [ ] `GET /capabilities` returned supported actions and decisions.
- [ ] `POST /v1/evaluate` was called before robot execution.
- [ ] Unique `request_id` and `nonce` were used.
- [ ] `modify` caused replacement with `recommended_action`.
- [ ] `block` caused no execution.
- [ ] Human escalation happened only when `decision` was `request_human_approval` or `human_approval_required` was true.
