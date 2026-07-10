# NandaHack Phase 2 Submission Checklist

Use this file to track the final hosted submission.

Current public URL:

```text
https://roboagent-guard.onrender.com
```

## Current Local Status

- [x] One FastAPI service.
- [x] `GET /SKILL.md` served by the app.
- [x] `GET /skill.md` lowercase alias served by the app.
- [x] Required local endpoints implemented.
- [x] Deterministic safety, SLAM, privacy, replay, freshness, and digital-twin logic implemented.
- [x] Local tests, Ruff, Pyright, audit verification, and scenario checks pass.
- [x] Render deployment file exists.
- [x] Agent-facing `SKILL.md` includes endpoint descriptions, curl examples, and example responses.
- [x] Browser-visible SkillMD judge PASS test implemented.
- [x] Composability demo implemented as an autonomous mission-planner workflow.

## Pending Hosted Submission Work

- [x] Deploy the service to a public HTTPS host.
- [x] Set `PUBLIC_BASE_URL` on the host to the final deployed URL.
- [x] Run `uv run python scripts/smoke_test_live.py --base-url https://roboagent-guard.onrender.com`.
- [x] Run `uv run python scripts/run_judge_test.py --base-url https://roboagent-guard.onrender.com`.
- [x] Confirm `https://roboagent-guard.onrender.com/SKILL.md` returns Markdown with the public base URL, not localhost.
- [x] Confirm `https://roboagent-guard.onrender.com/skill.md` also works.
- [x] Submit or resubmit the NANDA Skills Registry entry.
- [x] Confirm the registry card appears.
- [x] Confirm the registry card badge says `link responded`.
- [ ] Record the required video demo.
- [ ] Submit the required Google form before the deadline.

## Recommended Hosting

Recommended first choice: Render free web service.

Reasons:

- The repository already has `render.yaml`.
- Render supports Python web services on the free instance type.
- The app does not need persistent disk, database, Redis, or external services.
- Cold start is acceptable for this hackathon if you warm the service before testing.

Important Render free-tier notes:

- Free web services can spin down after idle time and may take about a minute to spin up again.
- The local filesystem is ephemeral on redeploy/restart/spin-down.
- This app is compatible because audit data is not required as persistent user data for judging.

Other possible hosts:

- Railway: convenient Python deployment, but current free/trial availability can depend on account status and credits.
- Fly.io: strong for always-on services, but setup is more involved and may require billing configuration.
- Vercel: excellent for serverless/static apps, but FastAPI as a long-running ASGI app is less direct than Render.

## Skills Registry Fields

Skill name:

```text
RoboAgent Guard
```

Your name or team:

```text
Subhash Chandra
```

Email:

```text
subhashc.iisc@gmail.com
```

GitHub username:

```text
subhashchandra001
```

One line description:

```text
Deterministic safety and privacy gate that evaluates mobile-robot actions before a digital twin applies them.
```

Source type:

```text
Hosted link
```

Hosted `.md` link:

```text
https://roboagent-guard.onrender.com/skill.md
```

Tags:

```text
robotics, safety, privacy, digital-twin, slam, replay, agents
```

Current registry API record:

```text
69e663b6-eb2d-4bdc-bad9-63f61b121890
```

## Endpoint Lines To Paste In Registry

```text
GET https://roboagent-guard.onrender.com/health
GET https://roboagent-guard.onrender.com/healthz
GET https://roboagent-guard.onrender.com/SKILL.md
GET https://roboagent-guard.onrender.com/skill.md
GET https://roboagent-guard.onrender.com/capabilities
GET https://roboagent-guard.onrender.com/.well-known/agent.json
POST https://roboagent-guard.onrender.com/v1/evaluate
POST https://roboagent-guard.onrender.com/v1/evaluate/batch
GET https://roboagent-guard.onrender.com/v1/scenarios
POST https://roboagent-guard.onrender.com/v1/scenarios/normal_navigation/run?seed=42
GET https://roboagent-guard.onrender.com/v1/receipts/{evaluation_id}
POST https://roboagent-guard.onrender.com/v1/receipts/verify
GET https://roboagent-guard.onrender.com/v1/demo
POST https://roboagent-guard.onrender.com/v1/judge-test
POST https://roboagent-guard.onrender.com/v1/agent-skill-test
POST https://roboagent-guard.onrender.com/v1/compose/mission-plan
```

## Live Verification Commands

Warm the service:

```bash
curl --fail https://roboagent-guard.onrender.com/health
```

Run complete live smoke test:

```bash
uv run python scripts/smoke_test_live.py --base-url https://roboagent-guard.onrender.com
```

Run live judge-style test:

```bash
uv run python scripts/run_judge_test.py --base-url https://roboagent-guard.onrender.com
```

Run the browser-visible proof endpoints directly:

```bash
curl --fail -X POST https://roboagent-guard.onrender.com/v1/agent-skill-test
curl --fail -X POST https://roboagent-guard.onrender.com/v1/compose/mission-plan
```

Verify the skill file:

```bash
curl --fail https://roboagent-guard.onrender.com/skill.md
```

Verify registry API after submission:

```bash
curl --fail https://nandatown.projectnanda.org/api/skills
```

Find the entry ID, then:

```bash
curl --fail https://nandatown.projectnanda.org/api/skills/ENTRY_ID
```

## Final Manual Checklist

- [x] Public service URL opens in browser.
- [x] `https://roboagent-guard.onrender.com/health` returns `ok`.
- [x] `https://roboagent-guard.onrender.com/skill.md` contains `Base URL` with the public URL.
- [x] Skills registry entry uses GitHub handle, not GitHub URL.
- [x] Skills registry endpoint lines use full live URLs.
- [x] Registry says `link responded`.
- [ ] Required video is uploaded and linked in the Google form.
- [ ] Google form is resubmitted with the new required fields.
- [ ] Service remains available through judging.

## Audit Verification Note

The default local audit file is generated while running demos and tests. If it contains old or mixed local data, verify a fresh audit path before submission:

```bash
AUDIT_PATH=/tmp/roboagent-guard-audit-check.jsonl uv run python scripts/run_demo.py --scenario normal_navigation --seed 42
AUDIT_PATH=/tmp/roboagent-guard-audit-check.jsonl uv run python scripts/verify_audit_chain.py --path /tmp/roboagent-guard-audit-check.jsonl
```
