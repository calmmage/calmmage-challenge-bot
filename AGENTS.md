# Claude instructions for this repo

## Python must always go through `uv`

This project uses `uv` to manage its Python environment and dependencies. Never invoke `python` or `pip` directly.

- Run scripts with `uv run python path/to/script.py` (not `python ...`).
- Install / add deps with `uv add <pkg>` (not `pip install`).
- Sync the env with `uv sync` (optionally `--group extras`).
- Run tests with `uv run pytest` (not bare `pytest`).
- Run one-off Python snippets with `uv run python -c '...'`.

Reason: bare `python` on this machine resolves to a system interpreter with no project deps, which produces misleading `ModuleNotFoundError`s. `uv run` always uses the project's `.venv`.
