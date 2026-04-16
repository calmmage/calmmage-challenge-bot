.PHONY: check docker-down docker-up fix fix-unsafe help lint run setup setup-wizard test

setup:
	uv sync --group extras --group test

# Interactive: asks for each env var one by one, writes .env
setup-wizard:
	uv run python setup_wizard.py

run:
	uv run python src/bot.py --debug

test:
	uv run pytest tests/ --cov=src --cov-report=term --cov-fail-under=50

lint:
	uv run ruff check src tests

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

help:
	@echo "Available targets:"
	@echo "  check        - Run all linters and type checks (continues past failures)"
	@echo "  fix          - Auto-fix lint issues and format code"
	@echo "  fix-unsafe   - Auto-fix with unsafe fixes enabled"
	@echo "  test         - Run tests with coverage"
	@echo "  help         - Show this help message"

check:
	-uv run ruff check src
	-uv run ruff format --check src
	-uv run vulture --min-confidence 80 src
	-uv run pyright src

fix:
	-uv run ruff check --fix .
	uv run ruff format .

fix-unsafe:
	-uv run ruff check --fix --unsafe-fixes .
	uv run ruff format .
