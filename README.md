# Calmmage Sleep Challenge Bot

Telegram bot that runs **sleep challenges**: participants pick bed/wake deadlines, confirm each night and morning with a message or video note (кружочек), and get scored (1 / 0.5 / 0) per day with a win-streak that breaks on two half-fails in a row.

Bot: `@calmmage_sleep_challenge_bot` · built on [botspot](https://github.com/calmmage/botspot).

## Features

- Multi-user, multi-challenge — admins create challenge events, users register via DM with `/join <code>`.
- Per-user timezone setup (geo / current time / manual).
- Three setup flows: guided (usual time → light/medium/hard), manual, defaults.
- Deadlines can only be tightened (`/tighten_bed`, `/tighten_wake`), never relaxed.
- Challenge-day pivots at 14:00 local to keep evening+morning as one day.
- Scheduled reminders, per-user day finalization, daily group stats (08:00), weekly leaderboard (Sun 20:00).
- Service-account Telethon client polls participants' "last seen" as a fallback signal (needs `/service_auth` once).

## Quick start

```bash
make setup
cp example.env .env
# fill TELEGRAM_BOT_TOKEN, BOTSPOT_MONGO_DATABASE_*, optionally SLEEP_BOT_SERVICE_*
make run
```

Then in Telegram:

- **Admin:** `/admin_new_challenge` → wizard. Add the bot to a group chat, `/bind_here <code>`, then `/admin_start <code>`.
- **Participant:** DM the bot `/join <code>` → timezone → setup flow → proof choice (if policy is `user_choice`).
- **Daily:** reply with text or a video note in the evening (bed) and morning (wake).

## Architecture

```
src/
├── _app.py                 # AppConfig (env)
├── bot.py                  # BotManager wiring + startup
├── models.py               # Pydantic: Challenge, ChallengeUser, SleepLog, CheckIn
├── db.py                   # Motor-backed repo
├── scoring.py              # score_day, update_streak (pure)
├── setup_flows.py          # light/medium/hard deadline math (pure)
├── time_utils.py           # challenge-day pivot, tz inference (pure)
├── router.py               # /start, /help
├── routers/
│   ├── admin.py            # /admin_new_challenge, /admin_start, /bind_here, …
│   ├── registration.py     # /join wizard
│   ├── checkins.py         # text/video-note → bed/wake, /tighten_*, /status, /history
│   └── group.py            # write-only group redirect
├── scheduler_jobs.py       # APScheduler jobs
└── service_account/
    ├── client.py           # shared Telethon client singleton
    ├── setup_command.py    # /service_auth
    └── jobs.py             # 15-min online polling
```

## Scoring

- Both bed + wake on-time → **1.0**
- Both present, at least one late → **0.5**
- Anything missing → **0.0**
- Streak resets on `0`, also on a second consecutive `0.5`.

## Bonus: share online status with the service account

Instructions live behind `/how_to_share_online`. TL;DR: add the service account to Telegram contacts and set *Last Seen & Online → My Contacts*.

## Testing

```bash
make test
```

Pure-function tests cover scoring, streak, tightening, guided-flow math, and challenge-day bucketing.

## Docker

```bash
docker compose up --build
```

Requires Mongo; add a `mongo` service to `docker-compose.yaml` or set `BOTSPOT_MONGO_DATABASE_CONN_STR` to an external instance.
