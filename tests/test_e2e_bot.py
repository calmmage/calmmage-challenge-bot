"""
E2E integration tests for calmmage_sleep_challenge_bot.

Tests the mechanical changes from the UX cleanup pass:
  - visibility=hidden commands are still callable but don't pollute the menu
  - visibility=admin_only commands are blocked for regular users
  - /admin_new_challenge auto-generates a code (no longer asks)
  - Core commands (/start, /status, /join) still respond

Requires the bot to be running and the service Telethon session to be authorised.
Run with:
    uv run python -m pytest tests/test_e2e_bot.py -v -s
Or directly:
    uv run python tests/test_e2e_bot.py
"""

import asyncio
import os
import sys

import pytest

BOT_USERNAME = os.environ.get("TEST_BOT_USERNAME", "@calmmage_sleep_challenge_bot")
TIMEOUT = float(os.environ.get("TEST_TIMEOUT", "12"))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def tester():
    from calmlib.telegram.bot_tester import BotTester

    async with BotTester(BOT_USERNAME, timeout=TIMEOUT) as t:
        yield t


# ---------------------------------------------------------------------------
# Core commands (PUBLIC — should always respond)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_start_responds(tester):
    resp = await tester.send_and_wait("/start")
    assert resp.text, "/start returned empty"
    # Non-admin service account sees user greeting
    assert any(
        kw in resp.text.lower()
        for kw in ("join", "hi", "hello", "привет", "how to")
    ), f"/start text unexpected: {resp.text[:200]}"


@pytest.mark.asyncio(loop_scope="session")
async def test_status_responds(tester):
    resp = await tester.send_and_wait("/status")
    assert resp.text, "/status returned empty"
    # Service account isn't enrolled, so we expect a polite refusal
    assert "active challenge" in resp.text.lower() or "not" in resp.text.lower(), (
        f"/status text unexpected: {resp.text[:200]}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_join_shows_picker_or_responds(tester):
    resp = await tester.send_and_wait("/join")
    assert resp.text or resp.reply_markup, "/join returned neither text nor buttons"


# ---------------------------------------------------------------------------
# Hidden commands — still callable, just not listed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_hidden_help_still_responds(tester):
    resp = await tester.send_and_wait("/help")
    assert resp.text, "/help (hidden) returned empty — handler is broken"


@pytest.mark.asyncio(loop_scope="session")
async def test_hidden_history_still_responds(tester):
    resp = await tester.send_and_wait("/history")
    assert resp.text, "/history (hidden) returned empty"
    # Either 'no logs' or actual history — both are valid
    assert any(kw in resp.text.lower() for kw in ("log", "challenge", "day", "no")), (
        f"/history text unexpected: {resp.text[:200]}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_hidden_tighten_bed_still_responds(tester):
    # Without args it should print usage, not silently swallow the message
    resp = await tester.send_and_wait("/tighten_bed")
    assert resp.text, "/tighten_bed (hidden) returned empty"


@pytest.mark.asyncio(loop_scope="session")
async def test_hidden_tighten_wake_still_responds(tester):
    resp = await tester.send_and_wait("/tighten_wake")
    assert resp.text, "/tighten_wake (hidden) returned empty"


@pytest.mark.asyncio(loop_scope="session")
async def test_hidden_how_to_share_online_still_responds(tester):
    resp = await tester.send_and_wait("/how_to_share_online")
    assert resp.text, "/how_to_share_online (hidden) returned empty"
    assert "online" in resp.text.lower() or "last seen" in resp.text.lower(), (
        f"/how_to_share_online text unexpected: {resp.text[:200]}"
    )


# ---------------------------------------------------------------------------
# Admin-only commands — service account should be silently ignored or blocked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_admin_new_challenge_blocked_for_non_admin(tester):
    # AdminFilter rejects non-admins. Botspot's error handler sends a polite
    # "You are not an admin" message — that's the expected surface, not silence.
    # The wizard MUST NOT start (no "Challenge code" prompt, no step-through).
    resp = await tester.send_and_wait("/admin_new_challenge")
    assert resp.text
    text = resp.text.lower()
    # Accept any rejection phrasing; reject any wizard continuation
    wizard_started = any(kw in text for kw in ("challenge code", "human-readable", "start date", "challenge id"))
    assert not wizard_started, (
        f"/admin_new_challenge started the wizard for a non-admin: {resp.text[:200]}"
    )
    # Confirm it's a refusal
    assert any(kw in text for kw in ("admin", "not", "permission", "access", "allowed")), (
        f"/admin_new_challenge response to non-admin is unexpected: {resp.text[:200]}"
    )


# ---------------------------------------------------------------------------
# List-commands check — verify menu shape via /list_commands
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_list_commands_hides_private_commands(tester):
    resp = await tester.send_and_wait("/list_commands")
    assert resp.text, "/list_commands returned empty"
    text = resp.text.lower()

    # Hidden commands must NOT appear in the menu listing
    hidden = ["help", "history", "tighten_bed", "tighten_wake", "how_to_share_online"]
    for cmd in hidden:
        assert cmd not in text, (
            f"Hidden command /{cmd} is still visible in /list_commands output"
        )

    # Public commands must be present
    for cmd in ["start", "join", "status"]:
        assert cmd in text, (
            f"Public command /{cmd} is missing from /list_commands output"
        )


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
