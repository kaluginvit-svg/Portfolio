#!/bin/sh
set -e
python /app/scripts/init_db.py
exec "$@"
