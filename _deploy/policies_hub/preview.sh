#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# معاينة قبل الرفع — بتوريك صافي مرتب كل موظف قبل وبعد التصليحات، من غير ما تغير أي حاجة:
#   curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/motionhr/<الفرع>/_deploy/policies_hub/preview.sh | sudo BRANCH=<الفرع> bash
#
# بتعمل نسخة مؤقتة من الباك إند فيها الملفات الجديدة، وتحسب المرتبات بالنسختين على نفس البيانات
# (الحساب بيرجع في الآخر ومفيش إشعارات بتتبعت)، وبعدين تمسح النسخة المؤقتة.
# الموقع الشغال مابيتلمسش خالص.
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

BRANCH="${BRANCH:?لازم تحدد الفرع: BRANCH=...}"
BE="${BE:-/var/www/motionhr}"
TS="$(date +%Y%m%d_%H%M%S)"
TMP="$(mktemp -d)"
OUT_CSV="/var/backups/motionhr_preview_${TS}.csv"
trap 'rm -rf "$TMP"' EXIT

say() { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()  { echo -e "\033[1;32m✔ $*\033[0m"; }

GH_TOKEN_FILE="${GH_TOKEN_FILE:-/root/.motionhr_github_token}"
GH_TOKEN=""
[ -r "$GH_TOKEN_FILE" ] && GH_TOKEN="$(tr -d '[:space:]' < "$GH_TOKEN_FILE")"
gh_tarball() {
  if [ -n "$GH_TOKEN" ]; then
    curl -fsSL -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/repos/johnsamire-coder/$1/tarball/$2" -o "$3"
  else
    curl -fsSL "https://codeload.github.com/johnsamire-coder/$1/tar.gz/refs/heads/$2" -o "$3"
  fi
}

[ -f "$BE/manage.py" ] || { echo "مش لاقي الباك إند في $BE"; exit 1; }
BE_OWNER="$(stat -c %U "$BE/manage.py")"
PY="$BE/venv/bin/python"; [ -x "$PY" ] || PY="$BE/.venv/bin/python"
chmod 755 "$TMP"

say "1/4 بنزّل التصليحات من GitHub ($BRANCH)"
gh_tarball motionhr "$BRANCH" "$TMP/be.tgz"
mkdir -p "$TMP/src" && tar -xzf "$TMP/be.tgz" -C "$TMP/src" --strip-components=1
mapfile -t FILES < <(sed -n '/^BE_FILES=(/,/^)/p' "$TMP/src/_deploy/policies_hub/deploy.sh" | sed '1d;$d' | sed 's/^ *//')
ok "${#FILES[@]} ملف"

say "2/4 بعمل نسخة مؤقتة من الباك إند فيها الملفات الجديدة"
mkdir -p "$TMP/new"
( cd "$BE" && tar -cf - --exclude=./media --exclude=./staticfiles --exclude=./venv --exclude=./.venv \
    --exclude=./backups --exclude=./.git --exclude='*.log' --exclude=__pycache__ . ) | tar -xf - -C "$TMP/new"
for f in "${FILES[@]}"; do install -D -m 644 "$TMP/src/$f" "$TMP/new/$f"; done
cp "$TMP/src/_deploy/policies_hub/net_snapshot.py" "$TMP/net_snapshot.py"
chown -R "$BE_OWNER" "$TMP"

MONTHS="$(TZ=Africa/Cairo date +%Y-%m),$(TZ=Africa/Cairo date -d "$(TZ=Africa/Cairo date +%Y-%m-15) -1 month" +%Y-%m)"
say "3/4 بحسب المرتبات بالنسختين (الشهر الحالي واللي قبله: $MONTHS) — ممكن ياخد دقايق"
( cd "$BE" && sudo -H -u "$BE_OWNER" env SNAP_OUT="$TMP/old.json" SNAP_MONTHS="$MONTHS" "$PY" manage.py shell < "$TMP/net_snapshot.py" ) | grep SNAPSHOT_OK
( cd "$TMP/new" && sudo -H -u "$BE_OWNER" env SNAP_OUT="$TMP/new.json" SNAP_MONTHS="$MONTHS" "$PY" manage.py shell < "$TMP/net_snapshot.py" ) | grep SNAPSHOT_OK

say "4/4 الفرق"
"$PY" - "$TMP/old.json" "$TMP/new.json" "$OUT_CSV" <<'PYEOF'
import csv, json, sys
old, new = (json.load(open(p, encoding='utf-8')) for p in sys.argv[1:3])
rows, any_change = [], False
for cid, c in sorted(new.items(), key=lambda x: int(x[0])):
    changed = []
    for eid, e in c['emps'].items():
        o = old.get(cid, {}).get('emps', {}).get(eid, {}).get('net', {})
        for month, n in e['net'].items():
            b = o.get(month)
            rows.append([c['company'], e['code'], e['name'], month, b, n])
            if b != n:
                diff = (n - b) if isinstance(n, float) and isinstance(b, float) else None
                changed.append((month, e, b, n, diff))
    if not changed:
        continue
    any_change = True
    months = sorted({x[0] for x in changed})
    print(f'\n■ {c["company"]} (شركة {cid}): {len({x[1]["code"] for x in changed})} موظف اتغير صافيه')
    for m in months:
        mc = [x for x in changed if x[0] == m]
        tot = sum(x[4] for x in mc if x[4] is not None)
        print(f'   شهر {m}: {len(mc)} موظف، إجمالي الفرق {tot:+,.2f} جنيه')
        for month, e, b, n, d in sorted(mc, key=lambda x: -abs(x[4] or 0))[:8]:
            print(f'      {e["code"]} {e["name"]}: {b} ← {n}' + (f'  ({d:+,.2f})' if d is not None else ''))
with open(sys.argv[3], 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['الشركة', 'الكود', 'الموظف', 'الشهر', 'الصافي قبل', 'الصافي بعد'])
    w.writerows(rows)
if not any_change:
    print('\nمفيش ولا موظف صافي مرتبه هيتغير ✅')
PYEOF
chmod 600 "$OUT_CSV"
echo
ok "المعاينة خلصت — ماتغيرش أي حاجة على السيرفر"
echo "التفاصيل كلها (كل موظف) في: $OUT_CSV"
