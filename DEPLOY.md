# Deployment

Branch: `main`. Commit and push only when a writable remote is configured.

Where: not set. Docker Compose is documented for local use; no production host was identified in the repository or Launchpad.

Check: run `UV_OFFLINE=1 uv run --no-sync pytest -q tests/test_deadline_rules.py` and verify the remote branch matches committed HEAD. No deployed service check is defined.

Do not deploy until a host and its verification are established.
