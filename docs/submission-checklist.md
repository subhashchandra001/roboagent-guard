# NandaHack Phase 2 Submission Checklist

Use this file to track the final hosted submission. Replace `PUBLIC_URL` with the deployed HTTPS URL, for example `https://roboagent-guard.onrender.com`.

## Current Local Status

- [x] One FastAPI service.
- [x] `GET /SKILL.md` served by the app.
- [x] `GET /skill.md` lowercase alias served by the app.
- [x] Required local endpoints implemented.
- [x] Deterministic safety, SLAM, privacy, replay, freshness, and digital-twin logic implemented.
- [x] Local tests, Ruff, Pyright, audit verification, and scenario checks pass.
- [x] Render deployment file exists.
- [x] Agent-facing `SKILL.md` includes endpoint descriptions, curl examples, and example responses.

## Pending Hosted Submission Work

- [ ] Deploy the service to a public HTTPS host.
- [ ] Set `PUBLIC_BASE_URL` on the host to the final deployed URL.
- [ ] Run `uv run python scripts/smoke_test_live.py --base-url PUBLIC_URL`.
- [ ] Run `uv run python scripts/run_judge_test.py --base-url PUBLIC_URL`.
- [ ] Confirm `PUBLIC_URL/SKILL.md` returns Markdown with the public base URL, not localhost.
- [ ] Confirm `PUBLIC_URL/skill.md` also works.
- [ ] Submit or resubmit the NANDA Skills Registry entry.
- [ ] Confirm the registry card appears.
- [ ] Confirm the registry card badge says `link responded`.
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
Subhash
```

Email:

```text
YOUR_EMAIL
```

GitHub username:

```text
YOUR_GITHUB_HANDLE
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
PUBLIC_URL/skill.md
```

Tags:

```text
robotics, safety, privacy, digital-twin, slam, replay, agents
```

## Endpoint Lines To Paste In Registry

```text
GET PUBLIC_URL/health
GET PUBLIC_URL/SKILL.md
GET PUBLIC_URL/skill.md
GET PUBLIC_URL/capabilities
GET PUBLIC_URL/.well-known/agent.json
POST PUBLIC_URL/v1/evaluate
POST PUBLIC_URL/v1/evaluate/batch
GET PUBLIC_URL/v1/scenarios
POST PUBLIC_URL/v1/scenarios/normal_navigation/run?seed=42
GET PUBLIC_URL/v1/demo
POST PUBLIC_URL/v1/judge-test
```

## Live Verification Commands

Warm the service:

```bash
curl --fail PUBLIC_URL/health
```

Run complete live smoke test:

```bash
uv run python scripts/smoke_test_live.py --base-url PUBLIC_URL
```

Run live judge-style test:

```bash
uv run python scripts/run_judge_test.py --base-url PUBLIC_URL
```

Verify the skill file:

```bash
curl --fail PUBLIC_URL/skill.md
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

- [ ] Public service URL opens in browser.
- [ ] `PUBLIC_URL/health` returns `ok`.
- [ ] `PUBLIC_URL/skill.md` contains `Base URL` with the public URL.
- [ ] Skills registry entry uses GitHub handle, not GitHub URL.
- [ ] Skills registry endpoint lines use full live URLs.
- [ ] Registry says `link responded`.
- [ ] Required video is uploaded and linked in the Google form.
- [ ] Google form is resubmitted with the new required fields.
- [ ] Service remains available through judging.
