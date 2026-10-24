#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# رفع نوع خصم "ساعات" في جزاءات السياسات (تأخير/غياب/خروج مبكر)
# أمر واحد يُلصق في تيرمنال السيرفر:
#   curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/MotionHR/main/_deploy/hours_penalty/deploy.sh | sudo bash
#
# بيعمل:
#   1) نسخة احتياطية من الملفين اللي هيتغيرا (وبنّاء الويب)
#   2) ينزل الملفات من GitHub (main)
#   3) يشغّل اختبارات المرتبات على السيرفر (قاعدة بيانات وهمية، مابيلمسش بياناتك)
#   4) يبني الويب ويعيد تشغيل الخدمات
#   5) لو أي خطوة فشلت: بيرجع كل حاجة زي ما كانت لوحده
# ملاحظة: مافيش أي تغيير في شكل قاعدة البيانات — مفيش migrate
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

BRANCH="${BRANCH:-main}"
BE="${BE:-/var/www/motionhr}"
WEB="${WEB:-/var/www/motionhr_web}"
BE_SERVICE="${BE_SERVICE:-motionhr}"
WEB_SERVICE="${WEB_SERVICE:-motionhr-web}"
TS="$(date +%Y%m%d_%H%M%S)"
BK="/var/backups/motionhr_hourspen_${TS}"
TMP="$(mktemp -d)"

BE_FILES=(
  attendance/payroll_rules.py
  attendance/test_hours_penalty_scratch.py
)
WEB_FILES=(
  src/components/hr/policies/penalty-rule-dialog.tsx
)

GH_TOKEN_FILE="${GH_TOKEN_FILE:-/root/.motionhr_github_token}"
GH_TOKEN=""
[ -r "$GH_TOKEN_FILE" ] && GH_TOKEN="$(tr -d '[:space:]' < "$GH_TOKEN_FILE")"
gh_tarball() {  # $1 = repo ، $2 = branch ، $3 = ملف الخرج
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
NPM="${NPM_BIN:-$(command -v npm || true)}"
if [ -z "$NPM" ]; then
  WEB_HOME="$(getent passwd "$WEB_OWNER" | cut -d: -f6)"
  NPM="$(ls -1 "$WEB_HOME"/.nvm/versions/node/*/bin/npm 2>/dev/null | tail -1 || true)"
fi
[ -x "$PY" ] || { fail "مش لاقي بايثون الباك إند"; exit 1; }
[ -n "$NPM" ] || { fail "مش لاقي npm على السيرفر"; exit 1; }
NODE_DIR="$(dirname "$(readlink -f "$NPM")")"

# ── 1) تنزيل الملفات من GitHub ──
say "1/4 بنزّل الملفات من GitHub ($BRANCH)"
gh_tarball motionhr "$BRANCH" "$TMP/be.tgz"
gh_tarball motionhr_web "$BRANCH" "$TMP/web.tgz"
mkdir -p "$TMP/be" "$TMP/web"
tar -xzf "$TMP/be.tgz" -C "$TMP/be" --strip-components=1
tar -xzf "$TMP/web.tgz" -C "$TMP/web" --strip-components=1
for f in "${BE_FILES[@]}"; do [ -f "$TMP/be/$f" ] || { fail "مش لاقي $f في نسخة GitHub"; exit 1; }; done
for f in "${WEB_FILES[@]}"; do [ -f "$TMP/web/$f" ] || { fail "مش لاقي $f في نسخة GitHub"; exit 1; }; done
ok "الملفات نزلت"

# ── 2) نسخة احتياطية ──
say "2/4 نسخة احتياطية في $BK"
mkdir -p "$BK"
( cd "$BE" && for f in "${BE_FILES[@]}"; do [ -e "$f" ] && echo "$f"; done > "$BK/be_existing.txt"; true )
( cd "$BE" && for f in "${BE_FILES[@]}"; do [ -e "$f" ] || echo "$f"; done > "$BK/be_new.txt"; true )
( cd "$BE" && tar -czf "$BK/be_files.tar.gz" -T "$BK/be_existing.txt" )
( cd "$WEB" && for f in "${WEB_FILES[@]}"; do [ -e "$f" ] && echo "$f"; done > "$BK/web_existing.txt"; true )
( cd "$WEB" && tar -czf "$BK/web_files.tar.gz" -T "$BK/web_existing.txt" )
( cd "$WEB" && tar -czf "$BK/web_next_build.tar.gz" .next )
cat > "$BK/rollback.sh" <<ROLLBACK
#!/usr/bin/env bash
set -u
echo "▶ برجّع ملفات الباك إند..."
cd "$BE" && tar -xzf "$BK/be_files.tar.gz"
while read -r f; do [ -n "\$f" ] && rm -f "$BE/\$f"; done < "$BK/be_new.txt"
echo "▶ برجّع ملفات الويب وبنّاؤه القديم..."
cd "$WEB" && tar -xzf "$BK/web_files.tar.gz"
rm -rf "$WEB/.next" && tar -xzf "$BK/web_next_build.tar.gz" && chown -R $WEB_OWNER: "$WEB/.next"
systemctl restart $BE_SERVICE
systemctl restart $WEB_SERVICE
echo "✔ رجعنا للنسخة القديمة"
ROLLBACK
chmod +x "$BK/rollback.sh"
ln -sfn "$BK" /var/backups/motionhr_hourspen_latest
ok "النسخة الاحتياطية جاهزة"
trap 'rollback' ERR

# ── 3) تركيب الباك إند + اختبارات المرتبات على السيرفر ──
say "3/4 بتركيب الباك إند وبشغّل اختبارات المرتبات (دقيقتين تقريبًا)"
for f in "${BE_FILES[@]}"; do install -D -o "$BE_OWNER" -g "$(stat -c %G "$BE/manage.py")" -m 644 "$TMP/be/$f" "$BE/$f"; done
( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py check >/dev/null )
if ! ( cd "$BE" && sudo -H -u "$BE_OWNER" "$PY" manage.py test attendance.test_hours_penalty_scratch attendance.test_payroll_scenarios --settings=motionhr.settings_test --noinput >"$BK/tests.log" 2>&1 ); then
  grep -E "^(FAIL|ERROR):|Error" "$BK/tests.log" | head -20; tail -5 "$BK/tests.log"; false
fi
grep -E "^Ran |^OK" "$BK/tests.log" || true
ok "كل اختبارات المرتبات نجحت على السيرفر"

# ── 4) الويب ──
say "4/4 ببني الويب (ممكن ياخد كام دقيقة)"
for f in "${WEB_FILES[@]}"; do install -D -o "$WEB_OWNER" -g "$(stat -c %G "$WEB/package.json")" -m 644 "$TMP/web/$f" "$WEB/$f"; done
( cd "$WEB" && sudo -H -u "$WEB_OWNER" env PATH="$(dirname "$NPM"):$NODE_DIR:/usr/local/bin:/usr/bin:/bin" "$NPM" run build >"$BK/web_build.log" 2>&1 ) || { tail -30 "$BK/web_build.log"; false; }
ok "الويب اتبنى"

say "بعيد تشغيل الخدمات"
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
ok "تم الرفع بنجاح ✅ — نوع الخصم الجديد \"خصم عدد ساعات\" متاح في كروت الجزاءات بالسياسات"
echo "النسخة الاحتياطية: $BK"
echo "لو عايز ترجع للنسخة القديمة في أي وقت، الصق الأمر ده:"
echo "   sudo bash /var/backups/motionhr_hourspen_latest/rollback.sh"
echo "════════════════════════════════════════════"
