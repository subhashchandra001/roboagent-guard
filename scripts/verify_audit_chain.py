from __future__ import annotations

import argparse
from pathlib import Path

from roboagent_guard.audit.verification import verify_audit_chain
from roboagent_guard.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=get_settings().audit_path)
    args = parser.parse_args()
    ok, errors = verify_audit_chain(args.path)
    if not ok:
        print("audit chain failed")
        for error in errors:
            print(error)
        return 1
    print(f"audit chain ok: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
