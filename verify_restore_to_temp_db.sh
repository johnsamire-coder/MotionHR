#!/bin/bash
set -e

export PGPASSFILE=/root/.pgpass

TMP_DB="motionhr_restore_test_tmp"
BACKUP_FILE=$(ls -1t /var/www/motionhr_backups/*.sql.gz | head -1)

echo "LATEST_BACKUP=$BACKUP_FILE"

echo "Drop temp DB if exists..."
sudo -u postgres dropdb --if-exists "$TMP_DB"

echo "Create temp DB owned by motionhr_user..."
sudo -u postgres createdb -O motionhr_user "$TMP_DB"

echo "Restore backup into temp DB..."
zcat "$BACKUP_FILE" | psql -U motionhr_user -h localhost -d "$TMP_DB" -v ON_ERROR_STOP=1

echo "Count tables in temp DB..."
psql -U motionhr_user -h localhost -d "$TMP_DB" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

echo "Sample company count..."
psql -U motionhr_user -h localhost -d "$TMP_DB" -tAc "SELECT count(*) FROM companies_company;"

echo "Cleanup temp DB..."
sudo -u postgres dropdb "$TMP_DB"

echo "RESTORE_TEMP_VERIFY_OK"
