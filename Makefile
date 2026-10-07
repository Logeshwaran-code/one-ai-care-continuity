.PHONY: up down test lint types eval cov demo seed e2e audit
up:        ; docker compose up --build
down:      ; docker compose down -v
test:      ; cd backend && python -m pytest -q
cov:       ; cd backend && python -m pytest -q --cov --cov-report=term-missing --cov-fail-under=80
lint:      ; cd backend && ruff check . && ruff format --check .
types:     ; cd backend && mypy app
eval:      ; cd backend && python -m eval.run_eval
seed:      ; cd backend && python -m app.seed
demo:      ; python scripts/demo_walkthrough.py http://localhost:8000
e2e:      ; cd e2e && npm ci && npx playwright install --with-deps chromium && npx playwright test
audit:     ; cd backend && pip-audit -r requirements.txt && bandit -q -r app
