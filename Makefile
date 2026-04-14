.PHONY: setup setup-wizard run test lint docker-up docker-down

setup:
	uv sync --group extras --group test

# Interactive: asks for each env var one by one, writes .env
setup-wizard:
	uv run python setup_wizard.py

run:
	uv run python src/bot.py --debug

test:
	uv run pytest tests

lint:
	uv run ruff check src tests

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
