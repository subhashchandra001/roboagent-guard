# Skill Agent Test

`scripts/run_judge_test.py --local` acts as an unfamiliar agent:

1. Reads `/SKILL.md`.
2. Checks `/health`.
3. Verifies documented endpoints.
4. Sends a safe request.
5. Sends an unsafe request.
6. Confirms safe approval and unsafe modification or block.
