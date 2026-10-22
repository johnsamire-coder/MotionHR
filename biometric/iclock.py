"""
استقبال البصمات من أجهزة ZKTeco مباشرة (بروتوكول ADMS / Push).
في إعدادات الجهاز: Cloud Server / ADMS → عنوان السيرفر وبورته.

الجهاز بيكلم:
  GET  /iclock/cdata?SN=...&options=all   → بناخد منه الإعدادات
  POST /iclock/cdata?SN=...&table=ATTLOG  → البصمات (سطر لكل بصمة)
  GET  /iclock/getrequest?SN=...          → بيسأل لو فيه أوامر له (بنقول مفيش)
  POST /iclock/devicecmd?SN=...           → نتيجة الأوامر

الأمان: مابنقبلش بصمات غير من جهاز رقمه التسلسلي متسجل ومفعّل في شركة.
الجهاز اللي مش متسجل بيترد عليه برفض، فبيحتفظ ببصماته ويعيد المحاولة لحد ما يتسجل (مافيش بصمة بتضيع).
"""
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from biometric.models import BiometricDevice, BiometricUserMap
from biometric.services import parse_attlog, parse_userinfo, store_punches


def _text(body, status=200):
    return HttpResponse(body, status=status, content_type='text/plain')


def _ip(request):
    return (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', ''))[:64]


def _device(request):
    """الجهاز المتسجل (أو بنسجله كجهاز جديد مستني الموافقة لو أول مرة يتصل)"""
    sn = (request.GET.get('SN') or request.GET.get('sn') or '').strip()[:64]
    if not sn:
        return None, ''
    dev = BiometricDevice.objects.filter(serial_number=sn).first()
    if dev is None:
        dev = BiometricDevice.objects.create(serial_number=sn, is_active=False,
                                             notes='اتصل لوحده ولسه ماتسجلش في شركة')
    BiometricDevice.objects.filter(pk=dev.pk).update(last_seen=timezone.now(), last_ip=_ip(request))
    return dev, sn


def _accepted(dev):
    return dev is not None and dev.is_active and dev.company_id


@csrf_exempt
def cdata(request):
    dev, sn = _device(request)
    if dev is None:
        return _text('ERROR: no SN', status=400)

    if request.method == 'GET':
        # إعدادات بنبعتها للجهاز: يبعت البصمات أول بأول (Realtime) وكمان بيانات المستخدمين عشان أساميهم
        info = request.GET.get('pushver') or ''
        if info and not dev.firmware:
            BiometricDevice.objects.filter(pk=dev.pk).update(firmware=info[:100])
        return _text('\n'.join([
            f'GET OPTION FROM: {sn}',
            'ATTLOGStamp=None',
            'OPERLOGStamp=9999',
            'ATTPHOTOStamp=None',
            'ErrorDelay=60',
            'Delay=30',
            'TransTimes=00:00;14:05',
            'TransInterval=1',
            'TransFlag=TransData AttLog\tOpLog\tEnrollUser',
            'TimeZone=2',
            'Realtime=1',
            'Encrypt=None',
            '',
        ]))

    if not _accepted(dev):
        # مش متسجل: نرفض عشان الجهاز يحتفظ بالبصمات ويبعتها تاني بعد التسجيل
        return _text('ERROR: device not registered', status=403)

    table = (request.GET.get('table') or '').upper()
    body = request.body.decode('utf-8', errors='replace')

    if table == 'ATTLOG':
        rows = parse_attlog(body)
        new, dup, _ = store_punches(dev.company_id, sn, rows, source='device')
        BiometricDevice.objects.filter(pk=dev.pk).update(last_upload=timezone.now())
        return _text(f'OK: {len(rows)}')

    if table in ('OPERLOG', 'USERINFO'):
        # أسامي الموظفين المتسجلة على الجهاز (بتساعد في شاشة الربط)
        names = parse_userinfo('\n'.join(l for l in body.splitlines() if l.startswith('USER ')))
        for pin, name in names.items():
            m, _ = BiometricUserMap.objects.get_or_create(company_id=dev.company_id, pin=pin)
            if name and m.device_user_name != name:
                m.device_user_name = name
                m.save(update_fields=['device_user_name', 'updated_at'])
        return _text(f'OK: {len(body.splitlines())}')

    return _text('OK')


@csrf_exempt
def getrequest(request):
    _device(request)
    return _text('OK')


@csrf_exempt
def devicecmd(request):
    _device(request)
    return _text('OK')
