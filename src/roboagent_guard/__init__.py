"""RoboAgent Guard package."""

__version__ = "1.0.0"


def main() -> None:
    """Print how to start the service."""
    print("Run: uvicorn roboagent_guard.app:app --host 0.0.0.0 --port ${PORT:-8000}")
