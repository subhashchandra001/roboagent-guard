# Architecture

RoboAgent Guard is a single FastAPI process with logically separate internal agents:

External agent -> schema validation -> replay/freshness guard -> authorization -> physical risk -> SLAM reliability -> privacy -> supervisor -> deterministic digital twin -> audit/trace output.

The supervisor applies hard-constraint precedence before weighted scores. Blocked actions are never simulated. Modified actions simulate only the replacement action.
