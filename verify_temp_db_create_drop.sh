#!/bin/bash
set -e

export PGPASSFILE=/root/.pgpass
TMP_DB="motionhr_restore_test_tmp"

echo "Creating temp DB: $TMP_DB"
createdb -U motionhr_user -h localhost "$TMP_DB"

echo "Listing temp DB:"
psql -U motionhr_user -h localhost -d postgres -tAc "SELECT datname FROM pg_database WHERE datname='${TMP_DB}';"

echo "Dropping temp DB: $TMP_DB"
dropdb -U motionhr_user -h localhost "$TMP_DB"

echo "Verifying drop:"
psql -U motionhr_user -h localhost -d postgres -tAc "SELECT datname FROM pg_database WHERE datname='${TMP_DB}';"

echo "TEMP_DB_CREATE_DROP_OK"
