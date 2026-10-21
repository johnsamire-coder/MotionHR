"""
أداة صغيرة بتكلم جهاز بصمة ZKTeco على نفس الشبكة (من اللابتوب).

  py zk_tool.py 192.168.1.201 info      → بيانات الجهاز ومين المدير عليه (قراية بس، مابتغيرش حاجة)
  py zk_tool.py 192.168.1.201 unlock    → بتشيل صلاحية المدير من كل اللي عليهم (بعد نسخة احتياطية)
                                          عشان قايمة الإعدادات تفتح من غير باسورد. الموظفين والبصمات زي ما هم.
  py zk_tool.py 192.168.1.201 export    → بتنزل كل البصمات في ملف attlog_<SN>.txt ينفع يترفع من صفحة "أجهزة البصمة"

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


def main():
    p = argparse.ArgumentParser()
    p.add_argument('ip')
    p.add_argument('action', choices=['info', 'unlock', 'export'])
    p.add_argument('--key', type=int, default=0)
    a = p.parse_args()
    conn = connect(a.ip, a.key)
    try:
        {'info': info, 'unlock': unlock, 'export': export}[a.action](conn)
    finally:
        safe(conn.disconnect)


if __name__ == '__main__':
    main()
