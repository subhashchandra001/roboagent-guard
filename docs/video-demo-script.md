# RoboAgent Guard Video Demo Script

Goal: record a short required Phase 2 video after the service is deployed publicly. Target length: 60 to 90 seconds.

Public service URL: `https://roboagent-guard.onrender.com`.

## Recording Setup

Open these tabs before recording:

- `https://roboagent-guard.onrender.com`
- `https://roboagent-guard.onrender.com/skill.md`
- `https://roboagent-guard.onrender.com/docs`

Optional terminal commands:

```bash
curl --fail https://roboagent-guard.onrender.com/health
curl --fail -X POST 'https://roboagent-guard.onrender.com/v1/scenarios/normal_navigation/run?seed=42'
curl --fail -X POST 'https://roboagent-guard.onrender.com/v1/scenarios/combined_safety_privacy_crisis/run?seed=42'
curl --fail -X POST 'https://roboagent-guard.onrender.com/v1/agent-skill-test'
curl --fail -X POST 'https://roboagent-guard.onrender.com/v1/compose/mission-plan'
```

## Suggested Narration

1. "This is RoboAgent Guard, a deterministic safety and privacy gate for mobile-robot actions."
2. "A stock agent can read this SKILL.md and learn the base URL, endpoints, request format, and decision rules."
3. "Before a robot action is executed, the agent calls `/v1/evaluate`."
4. "The service checks authorization, replay, freshness, physical risk, SLAM reliability, and privacy."
5. "Here is a safe navigation scenario returning approve."
6. "Here is a crisis scenario returning block. Notice the digital twin does not apply blocked actions."
7. "This judge-test card proves an agent can use the service from SKILL.md alone."
8. "This composition card shows a downstream mission planner using RoboAgent Guard before each robot step."
9. "If the decision is modify, the agent must execute only the returned recommended action."
10. "The service is self-contained: one FastAPI deployment, no ROS, no database, no external LLM, no paid APIs."

## Demo Flow

1. Show the dashboard at `https://roboagent-guard.onrender.com`.
2. Click `Run safe demo`.
3. Click `Run crisis demo`.
4. Click `Run full demo`.
5. Click `Run judge pass test` and show `PASS`.
6. Click `Run composed planner` and show `PASS`.
7. Open `https://roboagent-guard.onrender.com/skill.md` and show that the file contains endpoint examples and agent instructions.
8. Open `https://roboagent-guard.onrender.com/docs` to show OpenAPI is available.
9. Optionally show terminal output from the curl calls.

## Final Video Checklist

- [ ] Public URL visible.
- [ ] `SKILL.md` visible.
- [ ] Safe case shown.
- [ ] Block/crisis case shown.
- [ ] SkillMD judge `PASS` shown.
- [ ] Composed mission planner `PASS` shown.
- [ ] Agent instruction rule explained: execute recommended action on `modify`, execute nothing on `block`.
- [ ] Video uploaded somewhere shareable.
- [ ] Video link pasted into the final Google form.
