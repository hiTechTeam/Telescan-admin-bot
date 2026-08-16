# Telescan Admin Bot

Private Telegram interface for reviewing reports submitted by Telescan users.
Only explicitly configured Telegram accounts can interact with the bot. The bot
never connects to MongoDB and reaches moderation data only through the private
Telescan API Docker network.

## Features

- queues for pending, reviewing, resolved, and dismissed reports;
- report cards with reporter and target Telescan IDs, reason, comment, profile
  snapshot, timestamps, and moderation history;
- explicit confirmation before resolving or dismissing a report;
- moderator notes and a separate reviewing state;
- automatic notifications about new reports;
- persistent notification deduplication in a local SQLite volume;
- Telegram ID allow-list enforced for messages and callback queries;
- no public ports and no direct database access.

The initial production administrator is Telegram ID `2045659349`. Add more IDs
through `ADMIN_TELEGRAM_IDS` as a comma-separated allow-list.

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Purpose |
| --- | --- |
| `BOT_TOKEN` | Token issued by BotFather |
| `ADMIN_TELEGRAM_IDS` | Comma-separated Telegram user ID allow-list |
| `TELEGRAM_PROXY_URL` | Optional proxy supported by aiogram |
| `API_BASE_URL` | Private Docker URL of Telescan API |
| `MODERATION_SERVICE_SECRET` | Same separate moderation secret as Telescan API |
| `REPORT_POLL_INTERVAL_SECONDS` | New-report polling interval, 10–300 seconds |
| `DATABASE_PATH` | SQLite file used only for notification deduplication |

Production validation rejects the built-in development secret and requires the
API URL to stay on the private `telescan_network`. The bot token and moderation
secret must never be committed.

## Local development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/):

```sh
uv sync
make check
make run
```

Build and run the production container:

```sh
docker compose up -d --build
```

The health endpoint is available only inside Docker at `/health/live`. The
service does not publish a host port.

## Moderator workflow

1. Open the bot and send `/start`.
2. Open pending reports or wait for a new-report notification.
3. Inspect the report and captured profile snapshot.
4. Move it to reviewing, optionally attach a moderator note, then resolve or
   dismiss it with explicit confirmation.

Telegram commands:

- `/start` or `/menu` — main menu;
- `/reports` — pending reports;
- `/cancel` — cancel moderator-note entry.

## Deployment

Pushes to `main` run linting, formatting, Pyright, tests, a Docker build, and a
production deployment through GitHub Actions. The repository requires these
Actions secrets:

- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_KNOWN_HOSTS`

Runtime secrets live only in
`/home/ubuntu/telescan/Telescan-admin-bot/.env` on the server. The deploy job
clones the repository on the first run, performs only fast-forward updates, and
waits for the container health check.
