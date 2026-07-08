# NANDA Integration

This repository is the full RoboAgent Guard service. The NANDA Town warm-up PR is
the lightweight 80% integration slice: a deterministic `roboagent_guard`
scenario plus trace validators that make robot safety and privacy evidence
visible inside NANDA Town traces.

## Scope Split

The NANDA Town slice should prove that a scenario emits robot-risk and
privacy-sensitive messages, and that validators fail when those trace messages
do not carry visible review/filtering markers.

The full service in this repository goes further:

- It evaluates structured requests with Pydantic models.
- It does not trust client-provided `safety_approved`, risk score, or metadata
  claims.
- It enforces authorization, replay/freshness, physical-risk, SLAM, privacy, and
  approval-token checks before the digital twin transitions.
- It never executes blocked actions in the twin, and `modify` applies only the
  recommended replacement action.
- It stores hash-chained audit records and exports NANDA-style traces.

## Trace Validator Caveat

Plain trace markers such as `risk_checked=nav-1` or
`privacy_filtered=vision-1` are useful audit evidence, but they are not proof of
authentic approval. The warm-up validators should document this explicitly. They
catch missing or mismatched visible evidence; the full RoboAgent Guard service is
responsible for deterministic policy decisions.

## Recommended Warm-Up Validator Coverage

The NANDA Town PR should include tests for:

- safe robot and privacy messages passing validation;
- robot autonomy messages without safety markers failing;
- privacy-sensitive messages without privacy markers failing;
- marker/action ID mismatches failing for safety and privacy paths;
- no-op traces failing so the guard is actually exercised;
- broadcast robot messages being checked;
- misleading client claims not being treated as authoritative approval.

## Local Demo Path

Run the full service:

```bash
uv run uvicorn roboagent_guard.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

The dashboard calls the live API and demonstrates:

- `normal_navigation`: safe approval and twin execution;
- `low_light_high_speed`: modified action;
- `unauthorized_camera_request`: privacy block;
- `combined_safety_privacy_crisis`: hard block across authorization, physical
  risk, SLAM, freshness, and privacy evidence.

For continuity, each audited evaluation can export a NANDA Town-style JSONL
trace under `artifacts/nanda_traces/` with planner-to-service and
service-to-planner messages.
