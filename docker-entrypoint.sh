#!/bin/sh
set -e

if [ "$1" = 'dns-internal-check' ]; then
    exec python dns-internal-check.py
fi

exec "$@"
