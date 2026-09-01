#!/usr/bin/env bash
set -Eeuo pipefail

readonly INTENT_FILE="/home/ubuntu/telescan/.transactions/Telescan-admin-bot/active.json"
readonly RELEASES_DIR="/home/ubuntu/telescan/.releases/Telescan-admin-bot"

exec 9>/tmp/telescan-production-deploy.lock
if ! flock -w 1800 9; then
  echo "CRITICAL: timed out waiting for the production deployment lock" >&2
  exit 21
fi

if [[ ! -e "$INTENT_FILE" ]]; then
  exit 0
fi
if [[ ! -f "$INTENT_FILE" || -L "$INTENT_FILE" ]]; then
  echo "CRITICAL: admin-bot deployment intent is not a regular file" >&2
  exit 21
fi

release_dir="$(
  /usr/bin/python3 -c \
    'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); print(value["release_dir"])' \
    "$INTENT_FILE"
)"
case "$release_dir" in
  "$RELEASES_DIR"/*) ;;
  *)
    echo "CRITICAL: admin-bot deployment intent has an unsafe release path" >&2
    exit 21
    ;;
esac
if [[ ! -d "$release_dir" || -L "$release_dir" ]]; then
  echo "CRITICAL: immutable admin-bot release is unavailable" >&2
  exit 21
fi
if [[ ! -x "$release_dir/ops/deploy-production.sh" ]]; then
  echo "CRITICAL: versioned admin-bot deployment controller is unavailable" >&2
  exit 21
fi

export TELESCAN_DEPLOY_LOCK_HELD=1
exec "$release_dir/ops/deploy-production.sh" recover-locked
