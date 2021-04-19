#!/bin/sh
set -e

if [ "$1" = 'dns-internal-check' ]; then
    exec python main.py
fi

exec "$@"
