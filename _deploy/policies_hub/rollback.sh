#!/usr/bin/env bash
# الرجوع لآخر نسخة قبل رفع تصليحات مركز السياسات:
#   curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/policies-hub/_deploy/policies_hub/rollback.sh | sudo bash
set -u
LATEST=/var/backups/motionhr_policies_latest
if [ ! -x "$LATEST/rollback.sh" ]; then
  echo "✘ مفيش نسخة احتياطية من رفع مركز السياسات على السيرفر ده"
  exit 1
fi
bash "$LATEST/rollback.sh"
