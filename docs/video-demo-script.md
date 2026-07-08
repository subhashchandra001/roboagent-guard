# RoboAgent Guard Video Demo Script

Goal: record a short required Phase 2 video after the service is deployed publicly. Target length: 60 to 90 seconds.

Replace `PUBLIC_URL` with the deployed service URL.

## Recording Setup

Open these tabs before recording:

- `PUBLIC_URL`
- `PUBLIC_URL/skill.md`
- `PUBLIC_URL/docs`

Optional terminal commands:

```bash
curl --fail PUBLIC_URL/health
curl --fail -X POST 'PUBLIC_URL/v1/scenarios/normal_navigation/run?seed=42'
curl --fail -X POST 'PUBLIC_URL/v1/scenarios/combined_safety_privacy_crisis/run?seed=42'
```

## Suggested Narration

1. "This is RoboAgent Guard, a deterministic safety and privacy gate for mobile-robot actions."
2. "A stock agent can read this SKILL.md and learn the base URL, endpoints, request format, and decision rules."
3. "Before a robot action is executed, the agent calls `/v1/evaluate`."
4. "The service checks authorization, replay, freshness, physical risk, SLAM reliability, and privacy."
5. "Here is a safe navigation scenario returning approve."
6. "Here is a crisis scenario returning block. Notice the digital twin does not apply blocked actions."
7. "If the decision is modify, the agent must execute only the returned recommended action."
8. "The service is self-contained: one FastAPI deployment, no ROS, no database, no external LLM, no paid APIs."

## Demo Flow

1. Show the dashboard at `PUBLIC_URL`.
2. Click `Run safe demo`.
3. Click `Run crisis demo`.
4. Click `Run full demo`.
5. Open `PUBLIC_URL/skill.md` and show that the file contains endpoint examples and agent instructions.
6. Open `PUBLIC_URL/docs` to show OpenAPI is available.
7. Optionally show terminal output from the two curl scenario calls.

## Final Video Checklist

- [ ] Public URL visible.
- [ ] `SKILL.md` visible.
- [ ] Safe case shown.
- [ ] Block/crisis case shown.
- [ ] Agent instruction rule explained: execute recommended action on `modify`, execute nothing on `block`.
- [ ] Video uploaded somewhere shareable.
- [ ] Video link pasted into the final Google form.
