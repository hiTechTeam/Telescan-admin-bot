# Telescan Admin Bot

Private Telegram bot for reviewing Telescan reports. Access is limited by
`ADMIN_TELEGRAM_IDS`; the bot has no public port or database access and talks
only to the private moderation API.

## Run locally

```sh
cp .env.example .env
uv sync
make check
make run
```

Set `BOT_TOKEN`, `ADMIN_TELEGRAM_IDS`, `API_BASE_URL` and
`MODERATION_SERVICE_SECRET`. Keep tokens and `.env` out of Git. Production must
use `http://telescan-api:8000` and a moderation secret different from the user
bot secret.

## Moderation

Moderators open pending reports, move a case to `reviewing`, then explicitly
`resolve` or `dismiss` it. Closed cases are final. Each update includes the
current revision; stale cards are rejected and must be refreshed.

Commands: `/start`, `/menu`, `/reports`, `/cancel`.

## Deployment

Pull requests run lint, type checks, tests and a Docker build. A successful
push to protected `main` deploys an immutable release and rolls back on failed
health checks. Runtime secrets remain in the server `.env`.

Cross-service behavior is documented in
[`Telescan-internal-docs`](https://github.com/hiTechTeam/Telescan-internal-docs).

## License

Proprietary and confidential. See [LICENSE](LICENSE).
