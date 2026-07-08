.PHONY: sync format lint type test coverage demo judge determinism audit run

sync:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run pyright

test:
	uv run pytest -q

coverage:
	uv run pytest --cov=roboagent_guard --cov-report=term-missing

demo:
	uv run python scripts/run_demo.py --scenario normal_navigation --seed 42

judge:
	uv run python scripts/run_judge_test.py --local

determinism:
	uv run python scripts/verify_determinism.py --scenario combined_safety_privacy_crisis --seed 42

audit:
	uv run python scripts/verify_audit_chain.py

run:
	uv run uvicorn roboagent_guard.app:app --host 127.0.0.1 --port 8000 --reload
