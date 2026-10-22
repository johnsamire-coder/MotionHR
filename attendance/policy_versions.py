"""
مساعدات النسخ (versions) لقواعد وسياسات المرتب:
- الحذف: القاعدة اللي اتطبقت في شهور فاتت مابتتمسحش (كانت بتختفي من حساب الشهور القديمة)، بتتقفل بس.
- التعديل: بنعرف إذا القيم الأساسية اتغيرت فعلاً، مش إذا الحقل اتبعت (التطبيق بيبعت كل الحقول دايماً).
"""
import json
from calendar import monthrange
from datetime import date

from django.utils import timezone


def month_edges(today=None):
    today = today or timezone.localdate()
    first = date(today.year, today.month, 1)
    last = date(today.year, today.month, monthrange(today.year, today.month)[1])
    prev_last = date.fromordinal(first.toordinal() - 1)
    return first, last, prev_last


def was_used(obj):
    """القاعدة دي اتطبقت قبل الشهر الحالي (أو ليها نسخ تانية)؟"""
    first, _, _ = month_edges()
    start = getattr(obj, 'start_date', None)
    return bool(
        (start and start < first)
        or getattr(obj, 'is_superseded', False)
        or getattr(obj, 'previous_version_id', None)
    )


def soft_delete(obj):
    """
    بترجع رسالة. القاعدة المستخدمة قبل كده بتتقفل من آخر الشهر اللي فات (الشهر الحالي ومابعده مايتأثروش بيها،
    والشهور القديمة بتفضل محسوبة زي ما هي). اللي لسه ماتطبقتش بتتمسح عادي.
    """
    if not was_used(obj):
        obj.delete()
        return 'تم الحذف'
    _, _, prev_last = month_edges()
    end = getattr(obj, 'end_date', None)
    if end is None or end > prev_last:
        obj.end_date = max(prev_last, getattr(obj, 'start_date', prev_last) or prev_last)
        obj.save(update_fields=['end_date'])
    return 'القاعدة اتطبقت في شهور فاتت، فاتقفلت بدل ما تتمسح (الشهور القديمة محسوبة زي ما هي)'


def _num(v):
    """أرقام الشرائح بتيجي مرة 1 ومرة 1.0 ومرة "1" — نوحدها عشان المقارنة"""
    if isinstance(v, dict):
        return {k: _num(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_num(x) for x in v]
    if isinstance(v, bool) or v is None:
        return v
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return v


def _norm(v):
    if hasattr(v, 'pk'):
        v = v.pk
    if isinstance(v, (list, dict)):
        return json.dumps(_num(v), sort_keys=True, default=str, ensure_ascii=False)
    if v in (None, ''):
        return ''
    try:
        return repr(round(float(v), 4))
    except (TypeError, ValueError):
        return str(v).strip()


def changed_fields(obj, data, fields, current_ids=None):
    """الحقول الأساسية اللي قيمتها اتغيرت فعلاً"""
    out = []
    for f in fields:
        if f not in data:
            continue
        if f == 'specific_employees':
            new = sorted(int(x) for x in (data.get(f) or []) if str(x).isdigit())
            if new != sorted(current_ids or []):
                out.append(f)
            continue
        if _norm(getattr(obj, f, None)) != _norm(data.get(f)):
            out.append(f)
    return out
