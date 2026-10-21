#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# رفع تصليحات مركز السياسات على السيرفر — أمر واحد:
#   curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/group6-web/_deploy/policies_hub/deploy.sh | sudo bash
#
# لو المستودعات خاصة: مفتاح قراءة من GitHub محفوظ في /root/.motionhr_github_token
#
# بيعمل:
#   1) نسخة احتياطية من الكود (الباك إند والويب) ومن قاعدة البيانات
#   2) ينزل الملفات المعدلة بس من GitHub
#   3) يشغل الاختبارات على السيرفر (قاعدة بيانات وهمية في الذاكرة، مابيلمسش بياناتك)
#   4) يبني الويب ويعيد تشغيل الخدمات
#   5) لو أي خطوة فشلت: بيرجع كل حاجة زي ما كانت لوحده
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

BRANCH="${BRANCH:-fix/group6-web}"
BE="${BE:-/var/www/motionhr}"
WEB="${WEB:-/var/www/motionhr_web}"
BE_SERVICE="${BE_SERVICE:-motionhr}"
WEB_SERVICE="${WEB_SERVICE:-motionhr-web}"
TS="$(date +%Y%m%d_%H%M%S)"
START_ISO="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
BK="/var/backups/motionhr_policies_${TS}"
TMP="$(mktemp -d)"

BE_FILES=(
  accounts/access.py
  accounts/company_announcements.py
  accounts/activation.py
  accounts/fcm_service.py
  accounts/jwt_serializers.py
  accounts/login_backend.py
  accounts/test_access_guard.py
  accounts/views.py
  attendance/action_scope.py
  attendance/api_announcements.py
  attendance/api_company_policy.py
  attendance/api_departments.py
  attendance/api_employee_management.py
  attendance/api_employee_profile.py
  attendance/api_offboarding.py
  attendance/test_group4_permissions.py
  attendance/test_group5_bugs.py
  attendance/test_group6_web_server.py
  attendance/reminders.py
  employees/models.py
  employees/management/commands/import_employees_bulk.py
  employees/test_import_bulk.py
  leaves/signals.py
  attendance/api_attachments.py
  attendance/api_manual_entries.py
  attendance/api_missions.py
  attendance/api_mobile.py
  attendance/api_mobile_requests.py
  attendance/api_permissions_balance.py
  attendance/api_work_locations.py
  attendance/test_group3_misc.py
  leaves/leave_dates.py
  leaves/models.py
  leaves/test_leave_balance.py
  leaves/views.py
  attendance/test_action_scope.py
  companies/admin.py
  companies/management/__init__.py
  companies/management/commands/__init__.py
  companies/management/commands/company_access.py
  core/middleware.py
  core/push_helper.py
  motionhr/settings.py
  subscriptions/views.py
  attendance/api_attendance_policy.py
  attendance/api_eos_policy.py
  attendance/api_payroll.py
  attendance/api_reports.py
  attendance/company_policy_models.py
  attendance/payroll_rules.py
  attendance/test_payroll_scenarios.py
  attendance/management/commands/convert_policy_rules.py
  leaves/api_leave_policy.py
  leaves/services_leave_accrual.py
  motionhr/settings_test.py
)
WEB_FILES=(
  src/app/api/employee/announcements/route.ts
  src/app/api/employee/my-missions/route.ts
  src/app/api/employee/my-permissions/route.ts
  src/app/api/employee/my-work-locations/route.ts
  src/app/api/employee/today-sessions/route.ts
  src/app/api/hr/leave-recalls/route.ts
  src/app/api/hr/policies-allowance/route.ts
  src/app/api/hr/policies-attendance/route.ts
  src/app/api/hr/policies-bonus/route.ts
  src/app/api/hr/policies-deduction/route.ts
  src/app/api/hr/policies-leave/route.ts
  src/app/api/hr/policies/allowance-policies/[id]/route.ts
  src/app/api/hr/policies/bonus-policies/[id]/route.ts
  src/app/api/hr/policies/deduction-policies/[id]/route.ts
  src/app/api/hr/work-location-types/route.ts
  src/app/api/manager/mission-requests/route.ts
  src/app/api/manager/shift-changes/route.ts
  src/app/api/manager/withdraw-requests/route.ts
  src/app/employee/dashboard/page.tsx
  src/app/employee/field-visits/page.tsx
  src/app/employee/missions/page.tsx
  src/app/employee/permissions/page.tsx
  src/app/hr/attendance/page.tsx
  src/app/hr/manual-entries/page.tsx
  src/app/hr/policies/page.tsx
  src/app/hr/reports/leaves-basic/page.tsx
  src/app/hr/settings/page.tsx
  src/app/hr/work-locations/page.tsx
  src/app/manager/attendance/page.tsx
  src/app/manager/locations/page.tsx
  src/app/manager/my-field-visits/page.tsx
  src/app/manager/my-missions/page.tsx
  src/app/manager/requests/page.tsx
  src/components/auth/access-guard.tsx
  src/components/auth/login-form.tsx
  src/components/hr/policies/attendance-policy-dialog.tsx
  src/components/hr/policies/bonus-rule-dialog.tsx
  src/components/hr/policies/leave-policy-dialog.tsx
  src/components/hr/policies/penalty-rule-dialog.tsx
  src/lib/providers.tsx
)

# تنزيل نسخة من GitHub — بمفتاح القراءة لو موجود (المستودعات الخاصة)، ومن غيره لو عامة
GH_TOKEN_FILE="${GH_TOKEN_FILE:-/root/.motionhr_github_token}"
GH_TOKEN=""
[ -r "$GH_TOKEN_FILE" ] && GH_TOKEN="$(tr -d '[:space:]' < "$GH_TOKEN_FILE")"
gh_tarball() {  # $1 = اسم المستودع ، $2 = الفرع ، $3 = الملف
  if [ -n "$GH_TOKEN" ]; then
    curl -fsSL -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/johnsamire-coder/$1/tarball/$2" -o "$3"
  else
    curl -fsSL "https://codeload.github.com/johnsamire-coder/$1/tar.gz/refs/heads/$2" -o "$3"
  fi
}

say()  { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()   { echo -e "\033[1;32m✔ $*\033[0m"; }
fail() { echo -e "\n\033[1;31m✘ $*\033[0m"; }

ROLLED_BACK=0
rollback() {
  [ "$ROLLED_BACK" = 1 ] && return
  ROLLED_BACK=1
  fail "حصلت مشكلة — برجّع كل حاجة زي ما كانت..."
  bash "$BK/rollback.sh" || true
  fail "تم الرجوع للنسخة القديمة. البرنامج شغال زي ما كان. ابعت الرسالة اللي فوق للمطور."
}
trap 'fail "حصلت مشكلة قبل أي تغيير — السيرفر ماتغيرش خالص"' ERR

[ "$(id -u)" = 0 ] || { fail "لازم يتشغل بـ sudo"; exit 1; }
[ -f "$BE/manage.py" ] || { fail "مش لاقي الباك إند في $BE"; exit 1; }
[ -d "$WEB/src" ] || { fail "مش لاقي الويب في $WEB"; exit 1; }
BE_OWNER="$(stat -c %U "$BE/manage.py")"
WEB_OWNER="$(stat -c %U "$WEB/package.json")"
PY="$BE/venv/bin/python"
[ -x "$PY" ] || PY="$BE/.venv/bin/python"
# npm ممكن يكون متسطب عام أو جوه nvm بتاع صاحب الويب
NPM="${NPM_BIN:-$(command -v npm || true)}"
if [ -z "$NPM" ]; then
  WEB_HOME="$(getent passwd "$WEB_OWNER" | cut -d: -f6)"
  NPM="$(ls -1 "$WEB_HOME"/.nvm/versions/node/*/bin/npm 2>/dev/null | tail -1 || true)"
fi
[ -n "$NPM" ] || { fail "مش لاقي npm على السيرفر"; exit 1; }
NODE_DIR="$(dirname "$(readlink -f "$NPM")")"

# ── 0) التأكد إن ملفات السيرفر هي نفس النسخة اللي اتعمل عليها التصليح ──
say "0/5 بتأكد إن الكود اللي على السيرفر ماتغيرش من ساعة ما اتبعت"
# النسخ المعروفة: كود السيرفر الأصلي + كل رفعة سابقة من التصليحات دي
# + الفرع اللي بنرفعه نفسه: لو السيرفر عليه النسخة دي خلاص، إعادة الرفع آمنة
KNOWN_REFS="live-server-snapshot policies-hub-deployed-1 policies-hub-deployed-2 policies-hub-deployed-3 policies-hub-deployed-4 policies-hub-deployed-5 policies-hub-deployed-6 policies-hub-deployed-7 policies-hub-deployed-8 policies-hub-deployed-9 policies-hub-deployed-10 $BRANCH"
for ref in $KNOWN_REFS; do
  mkdir -p "$TMP/known_be/$ref" "$TMP/known_web/$ref"
  # النسخة اللي لسه ماترفعتش مش هتبقى موجودة — عادي
  gh_tarball motionhr "$ref" "$TMP/k.tgz" 2>/dev/null && tar -xzf "$TMP/k.tgz" -C "$TMP/known_be/$ref" --strip-components=1
  gh_tarball motionhr_web "$ref" "$TMP/k.tgz" 2>/dev/null && tar -xzf "$TMP/k.tgz" -C "$TMP/known_web/$ref" --strip-components=1
done
rm -f "$TMP/k.tgz"
# لازم على الأقل النسخة اللي على السيرفر دلوقتي تكون نزلت، وإلا الفحص مالوش لازمة
[ -f "$TMP/known_be/policies-hub-deployed-3/manage.py" ] && [ -f "$TMP/known_web/policies-hub-deployed-3/package.json" ] || {
  trap - ERR; fail "معرفتش أنزّل النسخ المعروفة من GitHub (النت أو مفتاح GitHub). ماحصلش أي تغيير على السيرفر."; exit 1; }
_known() {  # $1 = be|web ، $2 = الملف ، $3 = المسار على السيرفر
  [ -e "$3" ] || return 0
  local found_any=0
  for ref in $KNOWN_REFS; do
    local k="$TMP/known_$1/$ref/$2"
    [ -e "$k" ] && found_any=1 && cmp -s "$k" "$3" && return 0
  done
  [ "$found_any" = 0 ]
}
CHANGED=""
for f in "${BE_FILES[@]}"; do _known be "$f" "$BE/$f" || CHANGED="$CHANGED\n  backend: $f"; done
for f in "${WEB_FILES[@]}"; do _known web "$f" "$WEB/$f" || CHANGED="$CHANGED\n  web: $f"; done
if [ -n "$CHANGED" ]; then
  trap - ERR
  fail "الملفات دي اتعدلت على السيرفر بعد ما بعتها، فمش هكمل عشان مانمسحش تعديلاتك:$CHANGED"
  fail "ماحصلش أي تغيير على السيرفر. ابعت الرسالة دي للمطور."
  exit 1
fi
ok "الكود مطابق — نقدر نكمل"

# ── 1) نسخة احتياطية ──
say "1/5 باخد نسخة احتياطية في $BK"
mkdir -p "$BK"
( cd "$BE" && for f in "${BE_FILES[@]}"; do [ -e "$f" ] && echo "$f"; done > "$BK/backend_existing_files.txt"; true )
( cd "$BE" && for f in "${BE_FILES[@]}"; do [ -e "$f" ] || echo "$f"; done > "$BK/backend_new_files.txt"; true )
( cd "$BE" && tar -czf "$BK/backend_files.tar.gz" -T "$BK/backend_existing_files.txt" )
( cd "$WEB" && for f in "${WEB_FILES[@]}"; do [ -e "$f" ] && echo "$f"; done > "$BK/web_existing_files.txt"; true )
( cd "$WEB" && for f in "${WEB_FILES[@]}"; do [ -e "$f" ] || echo "$f"; done > "$BK/web_new_files.txt"; true )
( cd "$WEB" && tar -czf "$BK/web_files.tar.gz" -T "$BK/web_existing_files.txt" )
if [ -d "$WEB/.next" ]; then ( cd "$WEB" && tar -czf "$BK/web_next_build.tar.gz" .next ); fi

cat > "$BK/rollback.sh" <<ROLLBACK
#!/usr/bin/env bash
# الرجوع للنسخة اللي كانت قبل رفع $TS
set -u
echo "▶ بشيل القواعد اللي اتنقلت من سياسات الحضور (السياسات الأصلية لسه موجودة)..."
# بس القواعد اللي اتنقلت في الرفعة دي (مش اللي اتنقلت في رفعات قبلها)
cd "$BE" && sudo -H -u $BE_OWNER "$PY" manage.py shell -c "from django.utils.dateparse import parse_datetime; from attendance.company_policy_models import PenaltyRule, BonusRule; t = parse_datetime('$START_ISO'); print(PenaltyRule._base_manager.filter(change_reason__startswith='converted_from_policy:', created_at__gte=t).delete()[0] + BonusRule._base_manager.filter(change_reason__startswith='converted_from_policy:', created_at__gte=t).delete()[0], 'قاعدة')" 2>/dev/null | tail -1 || true
echo "▶ برجّع ملفات الباك إند..."
cd "$BE" && tar -xzf "$BK/backend_files.tar.gz"
while read -r f; do [ -n "\$f" ] && rm -f "$BE/\$f" && rmdir -p --ignore-fail-on-non-empty "\$(dirname "$BE/\$f")" 2>/dev/null; done < "$BK/backend_new_files.txt"
chown $BE_OWNER: \$(tar -tzf "$BK/backend_files.tar.gz") 2>/dev/null || true
echo "▶ برجّع ملفات الويب..."
cd "$WEB" && tar -xzf "$BK/web_files.tar.gz"
while read -r f; do [ -n "\$f" ] && rm -f "$WEB/\$f"; done < "$BK/web_new_files.txt"
if [ -f "$BK/web_next_build.tar.gz" ]; then rm -rf "$WEB/.next" && tar -xzf "$BK/web_next_build.tar.gz" && chown -R $WEB_OWNER: "$WEB/.next"; fi
systemctl restart $BE_SERVICE
systemctl restart $WEB_SERVICE
sleep 3
systemctl is-active $BE_SERVICE $WEB_SERVICE
echo "✔ رجعنا للنسخة القديمة"
ROLLBACK
chmod +x "$BK/rollback.sh"
ln -sfn "$BK" /var/backups/motionhr_policies_latest

# نسخة من قاعدة البيانات (احتياطي بس — التصليحات مابتغيرش شكل قاعدة البيانات)
( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py shell -c "
from django.conf import settings
d = settings.DATABASES['default']
for v in (d['ENGINE'], d.get('NAME'), d.get('USER'), d.get('HOST'), d.get('PORT'), d.get('PASSWORD')):
    print('DBV|' + str(v or ''))
" 2>/dev/null | sed -n 's/^DBV|//p' ) > "$TMP/db.txt" || true
DB_ENGINE="$(sed -n 1p "$TMP/db.txt")"
if echo "$DB_ENGINE" | grep -q postgresql; then
  if PGPASSWORD="$(sed -n 6p "$TMP/db.txt")" pg_dump -Fc -h "$(sed -n 4p "$TMP/db.txt" | sed 's/^$/localhost/')" \
    -p "$(sed -n 5p "$TMP/db.txt" | sed 's/^$/5432/')" -U "$(sed -n 3p "$TMP/db.txt")" \
    "$(sed -n 2p "$TMP/db.txt")" > "$BK/database.dump" 2>"$BK/pg_dump.log"; then
    ok "قاعدة البيانات اتنسخت ($(du -h "$BK/database.dump" | cut -f1))"
  else
    echo "⚠ نسخة قاعدة البيانات ماتعملتش (التصليحات مابتغيرش شكل قاعدة البيانات، فهنكمل). السبب: $(tail -1 "$BK/pg_dump.log")"
  fi
elif echo "$DB_ENGINE" | grep -q sqlite; then
  cp "$(sed -n 2p "$TMP/db.txt")" "$BK/database.sqlite3" && ok "قاعدة البيانات اتنسخت" || echo "⚠ نسخة قاعدة البيانات ماتعملتش"
else
  echo "⚠ معرفتش نوع قاعدة البيانات، هنكمل من غير نسخة منها (التصليحات مابتغيرش شكلها)"
fi
rm -f "$TMP/db.txt"
chmod 700 "$BK"
ok "النسخة الاحتياطية جاهزة"
# من هنا ورايح أي مشكلة = رجوع تلقائي للنسخة القديمة
trap 'rollback' ERR

# ── 2) تنزيل التصليحات ──
say "2/5 بنزّل التصليحات من GitHub"
gh_tarball motionhr "$BRANCH" "$TMP/be.tgz"
gh_tarball motionhr_web "$BRANCH" "$TMP/web.tgz"
mkdir -p "$TMP/be" "$TMP/web"
tar -xzf "$TMP/be.tgz" -C "$TMP/be" --strip-components=1
tar -xzf "$TMP/web.tgz" -C "$TMP/web" --strip-components=1
for f in "${BE_FILES[@]}"; do install -D -o "$BE_OWNER" -g "$(stat -c %G "$BE/manage.py")" -m 644 "$TMP/be/$f" "$BE/$f"; done
WEB_CHANGED=0
for f in "${WEB_FILES[@]}"; do cmp -s "$TMP/web/$f" "$WEB/$f" || WEB_CHANGED=1; done
for f in "${WEB_FILES[@]}"; do install -D -o "$WEB_OWNER" -g "$(stat -c %G "$WEB/package.json")" -m 644 "$TMP/web/$f" "$WEB/$f"; done
ok "الملفات اتحدثت (${#BE_FILES[@]} باك إند + ${#WEB_FILES[@]} ويب)"

# ── 3) اختبارات الباك إند على السيرفر نفسه ──
say "3/5 بشغّل الاختبارات (المرتبات والدخول، على قاعدة بيانات وهمية) — بياخد دقيقتين تقريباً"
( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py check >/dev/null )
if ! ( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py test attendance.test_payroll_scenarios accounts.test_access_guard attendance.test_action_scope attendance.test_group3_misc leaves.test_leave_balance attendance.test_group4_permissions attendance.test_group5_bugs employees.test_import_bulk attendance.test_group6_web_server --settings=motionhr.settings_test --noinput >"$BK/tests.log" 2>&1 ); then
  grep -E "^(FAIL|ERROR):|Error" "$BK/tests.log" | head -20; tail -5 "$BK/tests.log"; false
fi
grep -E "^Ran |^OK" "$BK/tests.log" || true
ok "كل الاختبارات نجحت"

# ── 3ب) نقل قواعد سياسات الحضور لكروتها المنفصلة (بيتأكد إن ولا مرتب اتغير قبل ما يحفظ) ──
say "3ب نقل قواعد التأخير والغياب والأوفر تايم لكروتها المنفصلة"
CONVERT_OK=1
( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py convert_policy_rules --apply >"$BK/convert.log" 2>&1 ) || CONVERT_OK=0
grep -v "objects imported" "$BK/convert.log" || true
[ "$CONVERT_OK" = 1 ] && grep -q "ولا صافي مرتب اتغير\|مفيش قواعد محتاجة تتنقل" "$BK/convert.log" || { fail "النقل ماتمش"; false; }
ok "النقل تم من غير ما أي رقم يتغير"

# ── 4) بناء الويب ──
if [ "$WEB_CHANGED" = 1 ]; then
  say "4/5 ببني الويب (ممكن ياخد كام دقيقة)"
  ( cd "$WEB" && sudo -H -u "$WEB_OWNER" env PATH="$(dirname "$NPM"):$NODE_DIR:/usr/local/bin:/usr/bin:/bin" "$NPM" run build >"$BK/web_build.log" 2>&1 ) || { tail -30 "$BK/web_build.log"; false; }
  ok "الويب اتبنى"
else
  say "4/5 الويب ماتغيرش — مش محتاج يتبني"
fi

# ── 5) إعادة التشغيل والتأكد ──
say "5/5 بعيد تشغيل الخدمات"
systemctl restart "$BE_SERVICE"
[ "$WEB_CHANGED" = 1 ] && systemctl restart "$WEB_SERVICE"
sleep 5
systemctl is-active --quiet "$BE_SERVICE" || { journalctl -u "$BE_SERVICE" -n 30 --no-pager; false; }
systemctl is-active --quiet "$WEB_SERVICE" || { journalctl -u "$WEB_SERVICE" -n 30 --no-pager; false; }
ok "الخدمتين شغالين"

trap - ERR
rm -rf "$TMP"
if ! grep -q '^EMAIL_HOST_PASSWORD=.' "$BE/.env" 2>/dev/null; then
  echo -e "\n\033[1;33m⚠ باسورد إيميل البرنامج لسه مش متحط في ملف .env — الإيميلات (زي استعادة الباسورد) واقفة لحد ما تحطه.\033[0m"
fi
echo
echo "════════════════════════════════════════════"
ok "تم الرفع بنجاح ✅"
echo "النسخة الاحتياطية: $BK"
echo "لو عايز ترجع للنسخة القديمة في أي وقت، الصق الأمر ده:"
echo "   sudo bash /var/backups/motionhr_policies_latest/rollback.sh"
echo "════════════════════════════════════════════"
