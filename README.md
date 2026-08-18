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
| `API_TIMEOUT_SECONDS` | Timeout for moderation API calls, 15 seconds by default |
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

The container runs as the unprivileged `telescan` user with a read-only root
filesystem, all Linux capabilities dropped, and `no-new-privileges`. Only the
named `/data` volume is writable for SQLite notification deduplication; `/tmp`
is a bounded tmpfs.

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

Pull requests run linting, formatting, Pyright, tests, and a Docker build without
accessing production deployment steps. Pushes to `main` repeat those checks and
deploy to production only after they pass. Manual workflow dispatch is also
available. The repository requires these Actions secrets:

- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_KNOWN_HOSTS`

Runtime secrets live only in
`/home/ubuntu/telescan/Telescan-admin-bot/.env` on the server. The deploy job
checks out the private repository inside GitHub Actions, uploads the release
over SSH without replacing `.env`, and waits for the container health check.

This implementation repository is private. Changes are reviewed through pull
requests by project convention, while the current GitHub plan does not enforce
branch protection/rulesets or provide secret scanning and push protection for
private repositories. Dependabot vulnerability alerts and security updates are
enabled. Do not force-push or delete `main`; these safeguards remain procedural
until repository protection is available for the private plan.

Cross-service architecture, moderation boundaries, and production risks are
maintained in the private
[`Telescan-internal-docs`](https://github.com/hiTechTeam/Telescan-internal-docs)
repository.

## License

Proprietary and confidential. See [LICENSE](LICENSE).
