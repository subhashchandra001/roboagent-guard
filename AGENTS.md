# RoboAgent Guard — Codex Development Instructions

## Mission

Build and maintain a complete, hosted-ready deterministic agent service named:

RoboAgent Guard: Making Invisible Robot Risk Visible through Agentic Digital Twins

The service evaluates proposed mobile-robot actions for authorization, replay and freshness, physical risk, SLAM reliability, and privacy risk.

## Product Requirement

A previously unfamiliar AI agent must be able to discover and successfully operate the service using only `SKILL.md`.

## Architecture Constraint

Use one FastAPI deployment. Specialized agents are internal Python components, not separate network services. Do not require ROS, Gazebo, a physical robot, a database, Redis, external LLMs, external APIs, or paid services.

## Determinism

- Safety and privacy decisions must be deterministic.
- Use injected timestamps in tests.
- Use seeded random generators.
- Never use unseeded randomness.
- Never use wall-clock time in simulation transitions.
- Identical inputs and seeds must produce byte-identical traces.

## Safety Rules

- Hard constraints override weighted scores.
- Never trust client-provided risk classifications or a plain text `safety_approved` claim.
- Never allow an LLM to make the final decision.
- Never execute blocked actions in the digital twin.
- When decision is `modify`, execute only the recommended replacement action.

## Privacy Rules

- Do not accept or store actual images.
- Represent camera use using metadata flags.
- Block unauthorized raw-camera sharing.
- Block private-zone raw storage.
- Require redaction or anonymization when identifiable data is shared.
- Keep retention limits explicit.

## API Requirements

Implement `GET /`, `/health`, `/SKILL.md`, `/capabilities`, `/.well-known/agent.json`, `POST /v1/evaluate`, `POST /v1/evaluate/batch`, `GET /v1/scenarios`, `POST /v1/scenarios/{scenario_name}/run`, `GET /v1/evaluations/{evaluation_id}`, and `GET /v1/demo`.

## Completion Definition

Do not stop after skeleton files. The work is complete only when the service starts locally, endpoints work, scenarios run, judge and determinism checks pass, audit verification passes, tests pass, Ruff passes, Pyright passes, documentation is complete, and Render deployment files are ready.
