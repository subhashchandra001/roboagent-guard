# Implementation Plan

## Phase Checklist

- [x] Configure `pyproject.toml` for Ruff, Pyright, pytest, and coverage.
- [x] Implement strict Pydantic request and response models.
- [x] Implement decision enums, role policy, thresholds, and stable hashing.
- [x] Implement authorization, replay, freshness, token, physical-risk, SLAM, privacy, and supervisor agents.
- [x] Implement deterministic digital-twin state transitions.
- [x] Add ten YAML scenarios and shared scenario runner.
- [x] Add hash-chained JSONL audit store and verifier.
- [x] Add NANDA Town-style trace export.
- [x] Implement FastAPI discovery, health, capabilities, evaluation, batch, scenario, demo, and judge endpoints.
- [x] Write `SKILL.md` so an unfamiliar agent can use the service without README context.
- [x] Add scripts for demo, judge, determinism, audit verification, trace export, and live smoke testing.
- [x] Add tests across unit, API, integration, adversarial, property, determinism, and e2e folders.
- [x] Add Render deployment configuration.

## NandaHack Main-Event Alignment

The project focuses on the 80% main-event requirement: a hosted service that agents can use on their own. The warm-up NANDA Town work remains separate; this repository exports optional NANDA-style traces only to demonstrate continuity.
