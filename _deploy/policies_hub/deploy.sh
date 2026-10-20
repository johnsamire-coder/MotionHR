#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# رفع تصليحات مركز السياسات على السيرفر — أمر واحد:
#   curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/policies-hub/_deploy/policies_hub/deploy.sh | sudo bash
#
# بيعمل:
#   1) نسخة احتياطية من الكود (الباك إند والويب) ومن قاعدة البيانات
#   2) ينزل الملفات المعدلة بس من GitHub
#   3) يشغل الاختبارات على السيرفر (قاعدة بيانات وهمية في الذاكرة، مابيلمسش بياناتك)
#   4) يبني الويب ويعيد تشغيل الخدمات
#   5) لو أي خطوة فشلت: بيرجع كل حاجة زي ما كانت لوحده
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

BRANCH="${BRANCH:-fix/policies-hub}"
BE="${BE:-/var/www/motionhr}"
WEB="${WEB:-/var/www/motionhr_web}"
BE_SERVICE="${BE_SERVICE:-motionhr}"
WEB_SERVICE="${WEB_SERVICE:-motionhr-web}"
TS="$(date +%Y%m%d_%H%M%S)"
BK="/var/backups/motionhr_policies_${TS}"
TMP="$(mktemp -d)"

BE_FILES=(
  attendance/api_attendance_policy.py
  attendance/api_eos_policy.py
  attendance/api_payroll.py
  attendance/api_reports.py
  attendance/company_policy_models.py
  attendance/payroll_rules.py
  attendance/test_payroll_scenarios.py
  leaves/api_leave_policy.py
  leaves/services_leave_accrual.py
  motionhr/settings_test.py
)
WEB_FILES=(
  src/app/hr/policies/page.tsx
  src/components/hr/policies/attendance-policy-dialog.tsx
  src/components/hr/policies/bonus-rule-dialog.tsx
  src/components/hr/policies/leave-policy-dialog.tsx
  src/components/hr/policies/penalty-rule-dialog.tsx
)

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
curl -fsSL "https://codeload.github.com/johnsamire-coder/motionhr/tar.gz/refs/heads/live-server-snapshot" -o "$TMP/be_snap.tgz"
curl -fsSL "https://codeload.github.com/johnsamire-coder/motionhr_web/tar.gz/refs/heads/live-server-snapshot" -o "$TMP/web_snap.tgz"
mkdir -p "$TMP/be_snap" "$TMP/web_snap"
tar -xzf "$TMP/be_snap.tgz" -C "$TMP/be_snap" --strip-components=1
tar -xzf "$TMP/web_snap.tgz" -C "$TMP/web_snap" --strip-components=1
CHANGED=""
for f in "${BE_FILES[@]}"; do
  if [ -e "$TMP/be_snap/$f" ] && ! cmp -s "$TMP/be_snap/$f" "$BE/$f"; then CHANGED="$CHANGED\n  backend: $f"; fi
done
for f in "${WEB_FILES[@]}"; do
  if [ -e "$TMP/web_snap/$f" ] && ! cmp -s "$TMP/web_snap/$f" "$WEB/$f"; then CHANGED="$CHANGED\n  web: $f"; fi
done
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
( cd "$WEB" && tar -czf "$BK/web_files.tar.gz" "${WEB_FILES[@]}" )
if [ -d "$WEB/.next" ]; then ( cd "$WEB" && tar -czf "$BK/web_next_build.tar.gz" .next ); fi

cat > "$BK/rollback.sh" <<ROLLBACK
#!/usr/bin/env bash
# الرجوع للنسخة اللي كانت قبل رفع $TS
set -u
echo "▶ برجّع ملفات الباك إند..."
cd "$BE" && tar -xzf "$BK/backend_files.tar.gz"
while read -r f; do [ -n "\$f" ] && rm -f "$BE/\$f"; done < "$BK/backend_new_files.txt"
chown $BE_OWNER: \$(tar -tzf "$BK/backend_files.tar.gz") 2>/dev/null || true
echo "▶ برجّع ملفات الويب..."
cd "$WEB" && tar -xzf "$BK/web_files.tar.gz"
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
curl -fsSL "https://codeload.github.com/johnsamire-coder/motionhr/tar.gz/refs/heads/$BRANCH" -o "$TMP/be.tgz"
curl -fsSL "https://codeload.github.com/johnsamire-coder/motionhr_web/tar.gz/refs/heads/$BRANCH" -o "$TMP/web.tgz"
mkdir -p "$TMP/be" "$TMP/web"
tar -xzf "$TMP/be.tgz" -C "$TMP/be" --strip-components=1
tar -xzf "$TMP/web.tgz" -C "$TMP/web" --strip-components=1
for f in "${BE_FILES[@]}"; do install -D -o "$BE_OWNER" -g "$(stat -c %G "$BE/manage.py")" -m 644 "$TMP/be/$f" "$BE/$f"; done
for f in "${WEB_FILES[@]}"; do install -D -o "$WEB_OWNER" -g "$(stat -c %G "$WEB/package.json")" -m 644 "$TMP/web/$f" "$WEB/$f"; done
ok "الملفات اتحدثت (${#BE_FILES[@]} باك إند + ${#WEB_FILES[@]} ويب)"

# ── 3) اختبارات الباك إند على السيرفر نفسه ──
say "3/5 بشغّل اختبارات المرتبات (182 اختبار على قاعدة بيانات وهمية) — بياخد دقيقتين تقريباً"
( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py check >/dev/null )
if ! ( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py test attendance.test_payroll_scenarios --settings=motionhr.settings_test --noinput >"$BK/tests.log" 2>&1 ); then
  grep -E "^(FAIL|ERROR):|Error" "$BK/tests.log" | head -20; tail -5 "$BK/tests.log"; false
fi
grep -E "^Ran |^OK" "$BK/tests.log" || true
ok "كل الاختبارات نجحت"

# ── 4) بناء الويب ──
say "4/5 ببني الويب (ممكن ياخد كام دقيقة)"
( cd "$WEB" && sudo -H -u "$WEB_OWNER" env PATH="$(dirname "$NPM"):$NODE_DIR:/usr/local/bin:/usr/bin:/bin" "$NPM" run build >"$BK/web_build.log" 2>&1 ) || { tail -30 "$BK/web_build.log"; false; }
ok "الويب اتبنى"

# ── 5) إعادة التشغيل والتأكد ──
say "5/5 بعيد تشغيل الخدمات"
systemctl restart "$BE_SERVICE"
systemctl restart "$WEB_SERVICE"
sleep 5
systemctl is-active --quiet "$BE_SERVICE" || { journalctl -u "$BE_SERVICE" -n 30 --no-pager; false; }
systemctl is-active --quiet "$WEB_SERVICE" || { journalctl -u "$WEB_SERVICE" -n 30 --no-pager; false; }
ok "الخدمتين شغالين"

trap - ERR
rm -rf "$TMP"
echo
echo "════════════════════════════════════════════"
ok "تم الرفع بنجاح ✅"
echo "النسخة الاحتياطية: $BK"
echo "لو عايز ترجع للنسخة القديمة في أي وقت، الصق الأمر ده:"
echo "   sudo bash /var/backups/motionhr_policies_latest/rollback.sh"
echo "════════════════════════════════════════════"
