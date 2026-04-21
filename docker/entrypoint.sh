#!/usr/bin/env sh
set -eu

mode="${1:-web}"
repo="${REPOBRAIN_REPO:-/workspace}"
host="${REPOBRAIN_WEB_HOST:-127.0.0.1}"
port="${REPOBRAIN_WEB_PORT:-8765}"

case "$mode" in
  web)
    shift || true
    exec repobrain serve-web --repo "$repo" --host "$host" --port "$port" "$@"
    ;;
  cli|chat)
    shift || true
    exec repobrain chat --repo "$repo" "$@"
    ;;
  shell|sh)
    shift || true
    exec /bin/sh "$@"
    ;;
  repobrain)
    shift || true
    exec repobrain "$@"
    ;;
  *)
    exec repobrain "$@"
    ;;
esac
