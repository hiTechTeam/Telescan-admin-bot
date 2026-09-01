# Telescan Admin Bot

Private Telegram interface for reviewing reports submitted by Telescan users.
Only explicitly configured Telegram accounts can interact with the bot. The bot
never connects to MongoDB and reaches moderation data only through the private
Telescan API Docker network.

## Features

- queues for pending, reviewing, resolved, and dismissed reports;
- report cards with reporter and target Telescan IDs, optional comment, captured
  name, username, BIO, photo, timestamps, and moderation history;
- explicit confirmation before resolving or dismissing a report;
- moderator notes and a separate reviewing state;
- automatic notifications about new reports;
- persistent notification deduplication in a local SQLite volume;
- Telegram ID allow-list enforced for messages and callback queries;
- no public ports and no direct database access.

Administrators are configured through the `ADMIN_TELEGRAM_IDS` allow-list.

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

Production validation rejects missing, malformed, placeholder, or reused bot
and moderation credentials and requires the exact private API origin
`http://telescan-api:8000` without credentials, path, query, or fragment. The
bot token and moderation secret must never be committed.

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
4. Move it to reviewing, optionally attaching a moderator note as part of that
   transition, then resolve or dismiss it with explicit confirmation.

Every mutation reloads the current report and sends its `revision`; a stale
card receives `409` and must be refreshed. The API permits only
`pending -> reviewing|resolved|dismissed` and
`reviewing -> resolved|dismissed`; resolved/dismissed reports are terminal.
The card distinguishes durable moderation photo evidence as available, absent,
or pending retry after a copy failure.

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
checks out the private repository inside GitHub Actions and finalizes the upload
as a root-owned, read-only immutable release without copying `.env`. A versioned
host controller runs under the shared `/tmp/telescan-production-deploy.lock`,
snapshots the complete active configuration except `.env`, and protects the
previous image under a unique rollback tag. Release files, the snapshot, and
their directory ancestry are fsynced before the controller publishes and
fsyncs a durable `prepared` intent.

The candidate is promoted only after that intent exists. Any failure before the
fsynced `committed` transition restores both the snapshot and protected image,
then requires exactly one restored container to be `healthy`. The intent is
cleared only after a healthy rollback or committed candidate is verified. The
deploy runs as a transient systemd service so an SSH disconnect cannot strand
the shell, while an enabled persistent systemd timer dispatches recovery after
a process crash or host reboot using the controller recorded by the immutable
release. The installed launcher, systemd units, enable symlink, and their
directories are fsynced and attested before a transaction may start. A corrupt
or unrecoverable intent remains in place and fails closed for operator review.
Only protected `main` can deploy, and workflow concurrency does not cancel an
active production transaction.

Deploy this bot during the API's explicitly bounded revision-compatibility
window, then enable mandatory revisions in the API. Do not leave the API
compatibility deadline extended after this client is live.

Cross-service architecture, moderation boundaries, and production risks are
maintained in the private
[`Telescan-internal-docs`](https://github.com/hiTechTeam/Telescan-internal-docs)
repository.

## License

Proprietary and confidential. See [LICENSE](LICENSE).
