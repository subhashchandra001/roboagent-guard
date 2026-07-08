from __future__ import annotations

import json
from pathlib import Path

from roboagent_guard.audit.hashing import sha256_digest


def verify_audit_chain(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    previous = "genesis"
    if not path.exists():
        return True, []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        record = json.loads(line)
        expected_previous = record.get("previous_hash")
        if expected_previous != previous:
            errors.append(f"line {line_no}: previous_hash mismatch")
        supplied_hash = record.get("record_hash")
        payload = {key: value for key, value in record.items() if key != "record_hash"}
        expected_hash = sha256_digest(payload)
        if supplied_hash != expected_hash:
            errors.append(f"line {line_no}: record_hash mismatch")
        previous = str(supplied_hash)
    return not errors, errors
