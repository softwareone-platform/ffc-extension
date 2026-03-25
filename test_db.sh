#!/usr/bin/env sh
set -eu

NAME=ffc-test-db

case "${1:-}" in
  start)
    docker run \
      -d \
      --name "$NAME" \
      -p 65432:5432 \
      -e POSTGRES_PASSWORD='mysecurepass#' \
      --tmpfs /var/lib/postgresql/data:size=1g \
      postgres:17
    ;;

  stop)
    docker rm -f "$NAME" 2>/dev/null || true
    ;;

  restart)
    "$0" stop
    "$0" start
    ;;

  *)
    echo "usage: $0 {start|stop|restart}" >&2
    exit 1
    ;;
esac
