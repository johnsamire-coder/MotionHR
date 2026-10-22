"""
أداة صغيرة بتكلم جهاز بصمة ZKTeco على نفس الشبكة (من اللابتوب).

  py zk_tool.py 192.168.1.201 info      → بيانات الجهاز ومين المدير عليه (قراية بس، مابتغيرش حاجة)
  py zk_tool.py 192.168.1.201 unlock    → بتشيل صلاحية المدير من كل اللي عليهم (بعد نسخة احتياطية)
                                          عشان قايمة الإعدادات تفتح من غير باسورد. الموظفين والبصمات زي ما هم.
  py zk_tool.py 192.168.1.201 export    → بتنزل كل البصمات في ملف attlog_<SN>.txt ينفع يترفع من صفحة "أجهزة البصمة"
  py zk_tool.py 192.168.1.201 names     → بتبعت أسامي الموظفين اللي على الجهاز للبرنامج (عشان شاشة الربط)
                                          الجهاز لازم يكون متسجل ومفعّل في صفحة "أجهزة البصمة"

  py zk_tool.py auto sync --sn CJMS213461364
                                        → بتفضل شغالة: كل 3 دقايق بتسحب البصمات الجديدة وتبعتها للبرنامج
                                          (auto = بتدور على الجهاز في الشبكة برقمه التسلسلي، حتى لو عنوانه اتغير)

لو الجهاز عليه "Comm Key": --key 1234
محتاج: py -m pip install pyzk
"""
import argparse
import json
import sys
from datetime import datetime

try:
    from zk import ZK, const
except ImportError:
    print('محتاج تثبت المكتبة الأول: py -m pip install pyzk')
    sys.exit(1)


def connect(ip, key):
    last = None
    for udp in (False, True):
        try:
            return ZK(ip, port=4370, timeout=15, password=key, force_udp=udp, ommit_ping=True).connect()
        except Exception as e:  # بعض الأجهزة UDP بس
            last = e
    print(f'FAILED: معرفتش أكلم الجهاز على {ip} ({last})')
    print('اتأكد إن اللابتوب على نفس الشبكة، ولو الجهاز عليه Comm Key جرب --key')
    sys.exit(2)


def safe(fn):
    try:
        return fn()
    except Exception:
        return ''


def info(conn):
    sn = safe(conn.get_serialnumber)
    print(f'Serial Number : {sn}')
    print(f'Device Name   : {safe(conn.get_device_name)}')
    print(f'Platform      : {safe(conn.get_platform)}')
    print(f'Firmware      : {safe(conn.get_firmware_version)}')
    print(f'Device Time   : {safe(conn.get_time)}')
    users = conn.get_users()
    admins = [u for u in users if u.privilege == const.USER_ADMIN]
    print(f'Users         : {len(users)}')
    print(f'Admins        : {len(admins)}')
    for u in admins:
        print(f'   - ID {u.user_id}  name "{u.name}"  password {"yes" if u.password else "no"}')
    safe(conn.read_sizes)
    print(f'Punches       : {getattr(conn, "records", "?")}')
    return sn, users


def unlock(conn):
    sn, users = info(conn)
    admins = [u for u in users if u.privilege == const.USER_ADMIN]
    if not admins:
        print('OK: مفيش مدير على الجهاز — القايمة المفروض تفتح على طول')
        return
    backup = f'zk_users_backup_{sn or "device"}_{datetime.now():%Y%m%d_%H%M%S}.json'
    with open(backup, 'w', encoding='utf-8') as f:
        json.dump([{'uid': u.uid, 'user_id': u.user_id, 'name': u.name, 'privilege': u.privilege,
                    'group_id': u.group_id, 'card': u.card, 'has_password': bool(u.password)} for u in users],
                  f, ensure_ascii=False, indent=1)
    print(f'Backup        : {backup}')
    conn.disable_device()
    try:
        for u in admins:
            conn.set_user(uid=u.uid, name=u.name, privilege=const.USER_DEFAULT, password=u.password,
                          group_id=u.group_id, user_id=u.user_id, card=u.card)
            print(f'   ✔ ID {u.user_id} بقى موظف عادي (بصمته زي ما هي)')
    finally:
        conn.enable_device()
    left = [u for u in conn.get_users() if u.privilege == const.USER_ADMIN]
    print('OK: الجهاز اتفتح — دوس M/OK على الجهاز' if not left else f'FAILED: لسه فيه {len(left)} مدير')


def export(conn):
    sn = safe(conn.get_serialnumber) or 'device'
    rows = conn.get_attendance()
    name = f'attlog_{sn}.txt'
    with open(name, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(f'{r.user_id}\t{r.timestamp:%Y-%m-%d %H:%M:%S}\t{r.status}\t{r.punch}\n')
    print(f'OK: {len(rows)} بصمة اتحفظت في {name} — ارفعه من صفحة "أجهزة البصمة" ← رفع ملف')


SERVER = 'https://jssolutions-eg.com'


def push(sn, table, body):
    """نفس اللي الجهاز كان هيبعته لو فيه Cloud Server"""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f'{SERVER}/iclock/cdata?SN={sn}&table={table}', data=body.encode('utf-8'),
                                 headers={'Content-Type': 'text/plain'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def names(conn):
    sn = safe(conn.get_serialnumber)
    users = conn.get_users()
    body = ''.join(f'USER PIN={u.user_id}\tName={(u.name or "").strip()}\n' for u in users)
    code, text = push(sn, 'OPERLOG', body)
    if code == 200:
        print(f'OK: {len(users)} اسم اتبعت — افتح "ربط الأرقام بالموظفين" في صفحة أجهزة البصمة')
    elif code == 403:
        print(f'FAILED: الجهاز {sn} لسه مش متسجل أو مش مفعّل في صفحة "أجهزة البصمة"')
    else:
        print(f'FAILED: السيرفر رد {code}: {text[:200]}')


# ─────────────────────────── المزامنة التلقائية ───────────────────────────

def log(msg):
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zk_sync.log')
    try:
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            os.replace(path, path + '.old')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n')
    except OSError:
        pass
    print(msg, flush=True)


def find_device(sn, key):
    """بندور في الشبكة على جهاز بالرقم التسلسلي ده"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        base = s.getsockname()[0].rsplit('.', 1)[0]
        s.close()
    except OSError:
        return None
    for i in range(1, 255):
        ip = f'{base}.{i}'
        try:
            with socket.create_connection((ip, 4370), timeout=0.2):
                pass
        except OSError:
            continue
        try:
            c = ZK(ip, port=4370, timeout=10, password=key, ommit_ping=True).connect()
            found = safe(c.get_serialnumber)
            safe(c.disconnect)
            if found == sn:
                return ip
        except Exception:
            continue
    return None


def state_path(sn):
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f'zk_sync_{sn}.state')


def sync(ip, sn, key, every, since=''):
    """كل شوية: بنسحب البصمات اللي بعد آخر بصمة اتبعتت ونبعتها للبرنامج. لو حاجة وقعت بنحاول تاني."""
    import time as _time
    last = ''
    try:
        last = open(state_path(sn), encoding='utf-8').read().strip()
    except OSError:
        pass
    last = last or since   # أول مرة: من التاريخ ده بس (لو اتحدد)
    names_at = 0
    log(f'بدأت المزامنة للجهاز {sn} (آخر بصمة اتبعتت: {last or "مفيش"})')
    while True:
        try:
            if ip == 'auto' or not ip:
                ip = find_device(sn, key) or 'auto'
                if ip == 'auto':
                    raise RuntimeError('مش لاقي الجهاز في الشبكة')
                log(f'لقيت الجهاز على {ip}')
            conn = ZK(ip, port=4370, timeout=20, password=key, ommit_ping=True).connect()
            try:
                if not sn:
                    sn = safe(conn.get_serialnumber)
                if _time.time() - names_at > 3600:
                    users = conn.get_users()
                    body = ''.join(f'USER PIN={u.user_id}\tName={(u.name or "").strip()}\n' for u in users)
                    code, _ = push(sn, 'OPERLOG', body)
                    if code == 200:
                        names_at = _time.time()
                rows = [r for r in conn.get_attendance() if f'{r.timestamp:%Y-%m-%d %H:%M:%S}' >= last]
            finally:
                safe(conn.disconnect)
            rows.sort(key=lambda r: r.timestamp)
            for i in range(0, len(rows), 500):
                chunk = rows[i:i + 500]
                body = ''.join(f'{r.user_id}\t{r.timestamp:%Y-%m-%d %H:%M:%S}\t{r.status}\t{r.punch}\n' for r in chunk)
                code, text = push(sn, 'ATTLOG', body)
                if code != 200:
                    raise RuntimeError(f'السيرفر رد {code}: {text[:120]}'
                                       + (' — الجهاز لازم يتسجل ويتفعّل في صفحة "أجهزة البصمة"' if code == 403 else ''))
                last = f'{chunk[-1].timestamp:%Y-%m-%d %H:%M:%S}'
                with open(state_path(sn), 'w', encoding='utf-8') as f:
                    f.write(last)
            if rows:
                log(f'اتبعت {len(rows)} بصمة (آخرها {last})')
        except Exception as e:
            log(f'مشكلة: {e} — هحاول تاني بعد شوية')
            if 'auto' == ip or 'timed out' in str(e).lower() or 'connect' in str(e).lower():
                ip = 'auto' if sn else ip
        _time.sleep(every)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('ip')
    p.add_argument('action', choices=['info', 'unlock', 'export', 'names', 'sync'])
    p.add_argument('--key', type=int, default=0)
    p.add_argument('--sn', default='')
    p.add_argument('--every', type=int, default=180)
    p.add_argument('--since', default='', help='YYYY-MM-DD: أول مرة يبعت البصمات من التاريخ ده بس')
    a = p.parse_args()
    if a.action == 'sync':
        if a.ip == 'auto' and not a.sn:
            print('مع auto لازم --sn')
            sys.exit(1)
        sync(a.ip, a.sn, a.key, max(30, a.every), a.since)
        return
    if a.ip == 'auto':
        a.ip = find_device(a.sn, a.key) if a.sn else None
        if not a.ip:
            print('FAILED: مش لاقي الجهاز في الشبكة')
            sys.exit(2)
    conn = connect(a.ip, a.key)
    try:
        {'info': info, 'unlock': unlock, 'export': export, 'names': names}[a.action](conn)
    finally:
        safe(conn.disconnect)


if __name__ == '__main__':
    main()
