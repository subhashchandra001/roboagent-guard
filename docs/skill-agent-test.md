# Skill Agent Test

`scripts/run_judge_test.py --local` acts as an unfamiliar agent:

1. Reads `/SKILL.md`.
2. Checks `/health`.
3. Verifies documented endpoints.
4. Sends a safe request.
5. Sends an unsafe request.
6. Confirms safe approval and unsafe modification or block.
7. Confirms routine outcomes require no human intervention; escalation is only for `request_human_approval`.

The hosted API also exposes the same idea directly:

- `POST /v1/agent-skill-test`: returns a step-by-step pass/fail proof that the service can be used from `SKILL.md` alone.
- `POST /v1/compose/mission-plan`: returns a pass/fail proof that another autonomous workflow can compose RoboAgent Guard before taking robot actions.
