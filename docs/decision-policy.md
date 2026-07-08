# Decision Policy

Decision precedence:

1. Invalid request: HTTP `422`.
2. Replay: `block`.
3. Stale critical evidence: `request_human_approval` or `block`.
4. Unauthorized action: `block`.
5. Emergency physical hazard: `block`.
6. Critical privacy violation: `block`.
7. Lost localization: `modify` to stop/relocalize.
8. High recoverable physical or SLAM risk: `modify`.
9. Moderate risk: `approve_with_constraints`.
10. Low risk: `approve`.

Risk scores are deterministic, finite, clamped to `[0, 1]`, and never accepted from the client as authority.
