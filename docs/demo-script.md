# Three-Minute Demo

0:00-0:25: Explain invisible robot risk: localization failures, collision risk, and private data collection.

0:25-0:50: Show architecture: planner -> RoboAgent Guard -> component agents -> supervisor -> digital twin.

0:50-1:15: Explain autonomous-by-default operation: the agent executes approve/modify/block outcomes without routine human intervention.

1:15-1:40: Run `normal_navigation`; show `approve`.

1:40-2:05: Run `low_light_high_speed`; show `modify` and `relocalize`.

2:05-2:30: Run `unauthorized_camera_request`; show `block`.

2:30-2:45: Show that human review is exception-only for stale or uncertain evidence.

2:45-3:00: Show `SKILL.md`, `/health`, and `scripts/run_judge_test.py --local`.
