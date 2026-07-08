# Deployment

Render deployment is configured in `render.yaml`.

Build command:

```bash
pip install uv && uv sync --frozen --no-dev
```

Start command:

```bash
uv run uvicorn roboagent_guard.app:app --host 0.0.0.0 --port $PORT
```

Set `PUBLIC_BASE_URL` to the final HTTPS service URL, `POLICY_VERSION=1.0.0`, and `AUDIT_PATH=/tmp/roboagent-guard-audit.jsonl`.

After deployment:

```bash
uv run python scripts/smoke_test_live.py --base-url https://YOUR-SERVICE.onrender.com
uv run python scripts/run_judge_test.py --base-url https://YOUR-SERVICE.onrender.com
```

Also confirm both skill URLs work:

```bash
curl --fail https://YOUR-SERVICE.onrender.com/SKILL.md
curl --fail https://YOUR-SERVICE.onrender.com/skill.md
```

For the full NandaHack Phase 2 submission checklist, see `docs/submission-checklist.md`.
