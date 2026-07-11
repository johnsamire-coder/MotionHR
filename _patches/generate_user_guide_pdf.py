"""
MotionHR User Guide PDF Generator
يولّد دليل استخدام احترافي بصيغة PDF
"""

import os
import sys
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, HRFlowable
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("❌ reportlab غير مثبت. شغّل: pip install reportlab")
    sys.exit(1)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

# ── Font Setup ──
FONT_NAME = "GuideArabic"
FONT_REGISTERED = False

def register_font():
    global FONT_REGISTERED
    if FONT_REGISTERED:
        return FONT_NAME
    candidates = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, path))
                FONT_REGISTERED = True
                return FONT_NAME
            except Exception:
                pass
    return "Helvetica"

def ar(text):
    if not text:
        return ''
    text = str(text)
    if HAS_ARABIC:
        try:
            text = arabic_reshaper.reshape(text)
            text = get_display(text)
        except Exception:
            pass
    return text

from xml.sax.saxutils import escape

def p(text, style):
    return Paragraph(escape(ar(text)), style)


# ── Guide Content ──
COMPANY_NAME = "JS Solutions"
PRODUCT_NAME = "MotionHR"
PHONE = "(+20)01501551593"

GUIDE_SECTIONS = [
    {
        "title": "نظرة عامة على النظام",
        "content": "MotionHR هو نظام إدارة موارد بشرية عصري وذكي مصمم للشركات في مصر والعالم العربي. يتميز بتتبع الموظفين الميدانيين في الوقت الفعلي، سياسات مرنة، وإشعارات فورية.",
        "steps": [],
    },
    {
        "title": "الخطوة 1: تسجيل الدخول",
        "content": "بعد استلام بيانات الدخول من فريق الدعم، ادخل على رابط النظام وسجّل دخولك.",
        "steps": [
            "افتح المتصفح (Chrome أو Edge) على الكمبيوتر أو الموبايل.",
            "اكتب رابط النظام في شريط العنوان.",
            "أدخل اسم المستخدم وكلمة المرور.",
            "اضغط 'تسجيل الدخول'.",
            "ستظهر لك لوحة التحكم الرئيسية (Dashboard).",
        ],
    },
    {
        "title": "الخطوة 2: إعداد بيانات الشركة",
        "content": "قبل إضافة الموظفين، يجب إعداد بيانات الشركة الأساسية.",
        "steps": [
            "من القائمة الجانبية، اختر 'الإعدادات'.",
            "أدخل اسم الشركة بالعربي والإنجليزي.",
            "ارفع لوجو الشركة.",
            "حدد العنوان ورقم الهاتف.",
            "اضغط 'حفظ'.",
        ],
    },
    {
        "title": "الخطوة 3: إضافة الفروع",
        "content": "لو شركتك عندها أكثر من فرع، أضف كل فرع مع عنوانه وإحداثيات GPS.",
        "steps": [
            "من القائمة، اختر 'الشركة' ← 'الفروع'.",
            "اضغط 'إضافة فرع'.",
            "أدخل اسم الفرع بالعربي والإنجليزي.",
            "أدخل العنوان.",
            "حدد الموقع على الخريطة (GPS) — ده مهم للـ Geofencing.",
            "حدد نطاق الـ Geofencing بالأمتار.",
            "اضغط 'حفظ'.",
        ],
    },
    {
        "title": "الخطوة 4: إضافة الإدارات والأقسام",
        "content": "أنشئ الهيكل الإداري للشركة بربط الإدارات والأقسام ببعضها.",
        "steps": [
            "من القائمة، اختر 'الشركة' ← 'الإدارات'.",
            "اضغط 'إضافة إدارة'.",
            "أدخل اسم الإدارة.",
            "لو هي إدارة فرعية، اربطها بالإدارة الأم.",
            "اضغط 'حفظ'.",
            "كرر لكل الإدارات والأقسام.",
        ],
    },
    {
        "title": "الخطوة 5: إعداد الهيكل الوظيفي",
        "content": "حدد المستويات الوظيفية والمسميات وربطها ببعضها لضمان تحديد المدير المباشر بشكل صحيح.",
        "steps": [
            "من القائمة، اختر 'الموظفون' ← 'الهيكل الوظيفي'.",
            "أضف المستويات الوظيفية (مثال: 1-صاحب الشركة، 2-مدير عام، 3-مدير، ...).",
            "اربط كل إدارة بالمسمى الوظيفي والمستوى المناسب.",
            "حدد المسمى الأعلى المباشر لكل مسمى.",
            "اضغط 'حفظ'.",
        ],
    },
    {
        "title": "الخطوة 6: إضافة الموظفين",
        "content": "أضف بيانات كل موظف خطوة بخطوة عبر نموذج ذكي من 5 مراحل.",
        "steps": [
            "من القائمة، اختر 'الموظفون' ← 'إضافة موظف'.",
            "المرحلة 1: أدخل البيانات الأساسية (الاسم، الرقم القومي، تاريخ الميلاد).",
            "المرحلة 2: أدخل بيانات التواصل (الهاتف، الإيميل، العنوان).",
            "المرحلة 3: أدخل بيانات التعيين (الفرع، الإدارة، المسمى الوظيفي، المدير المباشر).",
            "المرحلة 4: أدخل البيانات المالية (الراتب، البنك، التأمينات).",
            "المرحلة 5: حدد إعدادات الحضور (ثابت/مرن/ميداني).",
            "اضغط 'حفظ الموظف'.",
            "النظام سينشئ حساب دخول تلقائي للموظف.",
        ],
    },
    {
        "title": "الخطوة 7: رفع مستندات الموظف",
        "content": "ارفع كل مستندات الموظف (بطاقة، عقد، شهادات) في ملفه الإلكتروني.",
        "steps": [
            "من صفحة الموظف، اضغط 'ملف المستندات'.",
            "اضغط 'رفع مستند جديد'.",
            "اختر تصنيف المستند (بطاقة هوية / عقد تعيين / شهادة / ...).",
            "ارفع الملف (PDF أو صورة).",
            "حدد الحدث المرتبط (تعيين / ترقية / إجازة / ...).",
            "اضغط 'رفع المستند'.",
        ],
    },
    {
        "title": "الخطوة 8: إعداد سياسات الشركة",
        "content": "ضبط سياسات الحضور والتأخير والتتبع الصامت.",
        "steps": [
            "من القائمة، اختر 'الإعدادات' ← 'سياسات الشركة'.",
            "حدد فترة السماح للتأخير بالدقائق.",
            "حدد سياسة الخصم على الغياب.",
            "فعّل/عطّل التتبع الصامت.",
            "اختر من يستلم إشعارات التتبع (HR / صاحب الشركة / المدير).",
            "اضغط 'حفظ'.",
        ],
    },
    {
        "title": "الخطوة 9: إعداد ميثاق العمل",
        "content": "أنشئ ميثاق عمل إلكتروني يوقعه كل موظف رقمياً.",
        "steps": [
            "من القائمة، اختر 'الإعدادات' ← 'ميثاق العمل'.",
            "اكتب بنود الميثاق.",
            "اضغط 'حفظ'.",
            "النظام سيطلب من كل موظف قراءة الميثاق وتوقيعه رقمياً.",
            "يمكنك متابعة حالة التوقيع من 'حالة التوقيع'.",
            "يمكنك إرسال تذكير للموظفين الذين لم يوقعوا.",
        ],
    },
    {
        "title": "الخطوة 10: إعداد الورديات وجداول العمل",
        "content": "حدد مواعيد العمل لكل موظف أو مجموعة.",
        "steps": [
            "من القائمة، اختر 'الحضور' ← 'جدول العمل'.",
            "أنشئ تكليف جديد.",
            "حدد الموظف وتاريخ اليوم.",
            "اختر نوع اليوم (عمل / إجازة / مهمة / ...).",
            "اختر طريقة التنفيذ (ثابت / مرن / متقسم / ...).",
            "النظام سيظهر لك الحقول المناسبة فقط حسب اختيارك.",
            "اضغط 'حفظ'.",
        ],
    },
    {
        "title": "كيف يسجّل الموظف حضوره؟",
        "content": "الموظف يفتح النظام من الموبايل ويسجل حضوره بالـ GPS.",
        "steps": [
            "الموظف يفتح رابط النظام من الموبايل.",
            "يسجل دخول ببياناته.",
            "يضغط 'تسجيل حضور'.",
            "النظام يأخذ موقعه GPS تلقائياً.",
            "لو الموظف داخل نطاق الفرع (Geofencing) يتسجل حضور.",
            "لو برة النطاق يظهر تحذير.",
            "عند الانصراف يضغط 'تسجيل انصراف'.",
        ],
    },
    {
        "title": "الخريطة الحية (Live Map)",
        "content": "تابع مواقع الموظفين الميدانيين لحظة بلحظة.",
        "steps": [
            "من القائمة، اختر 'الحضور' ← 'الخريطة الحية'.",
            "ستظهر خريطة بمواقع كل الموظفين الميدانيين النشطين.",
            "اضغط على أي موظف لعرض تفاصيله وموقعه.",
            "الخريطة تتحدث تلقائياً كل 30 ثانية.",
        ],
    },
    {
        "title": "نظام الإجازات",
        "content": "إدارة أنواع الإجازات وأرصدتها وطلباتها.",
        "steps": [
            "من القائمة، اختر 'الإجازات' ← 'أنواع الإجازات'.",
            "أضف أنواع الإجازات (سنوية / مرضية / عارضة / ...).",
            "حدد الرصيد السنوي لكل نوع.",
            "الموظف يقدم طلب إجازة من حسابه.",
            "المدير المباشر يوافق أو يرفض.",
            "الرصيد يتحدث تلقائياً.",
        ],
    },
    {
        "title": "نظام الطلبات",
        "content": "18 نوع طلب جاهز (سلف / إذن / شهادة خبرة / ...).",
        "steps": [
            "من القائمة، اختر 'الطلبات' ← 'طلب جديد'.",
            "اختر نوع الطلب.",
            "املأ البيانات المطلوبة.",
            "اضغط 'إرسال'.",
            "الطلب يمر على مسار الموافقة (3 خطوات).",
            "يمكن متابعة حالة الطلب من 'طلباتي'.",
        ],
    },
    {
        "title": "التقارير",
        "content": "5 تقارير جاهزة + ملف شامل لكل موظف.",
        "steps": [
            "من القائمة، اختر 'التقارير'.",
            "اختر نوع التقرير (حضور / تأخيرات / إجازات / موظفين / ميدانيين).",
            "حدد الفترة الزمنية.",
            "اعرض التقرير.",
            "اضغط 'تصدير Excel' للحصول على ملف منظم.",
            "اضغط 'تصدير PDF' للحصول على ملف PDF.",
            "اضغط أيقونة الملف الشامل بجانب أي موظف لعرض كل بياناته.",
        ],
    },
    {
        "title": "التتبع الصامت (Stealth Tracking)",
        "content": "تتبع الموظفين الميدانيين بشكل صامت بدون علمهم.",
        "steps": [
            "فعّل التتبع الصامت من 'سياسات الشركة'.",
            "من القائمة، اختر 'الحضور' ← 'إدارة التتبع الصامت'.",
            "فعّل التتبع لكل موظف ميداني تريد تتبعه.",
            "النظام سيرسل تنبيهات لو الموظف خرج من نطاق معين.",
        ],
    },
    {
        "title": "إدارة ملفات الموظفين",
        "content": "كل مستندات الموظف في مكان واحد.",
        "steps": [
            "من صفحة الموظف، اختر 'ملف المستندات'.",
            "ارفع أي مستند (بطاقة / عقد / شهادة / تقرير طبي / ...).",
            "المستندات تُصنّف تلقائياً حسب النوع.",
            "يمكن عرض / تحميل / حذف أي مستند.",
        ],
    },
    {
        "title": "تثبيت التطبيق على الموبايل",
        "content": "البرنامج يعمل كتطبيق على الموبايل بدون تنزيل من أي متجر.",
        "steps": [
            "افتح رابط النظام من متصفح الموبايل (Chrome).",
            "سيظهر إشعار 'إضافة إلى الشاشة الرئيسية'.",
            "اضغط 'إضافة'.",
            "ستجد أيقونة MotionHR على شاشة الموبايل.",
            "افتح منها مباشرة — ستعمل كتطبيق مستقل.",
        ],
    },
]

def generate_guide():
    font_name = register_font()
    output_path = os.path.join(BASE_DIR, "static", "MotionHR_User_Guide.pdf")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="MotionHR User Guide",
        author="JS Solutions",
    )

    # Styles
    title_style = ParagraphStyle(
        name="GuideTitle",
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#06B6D4"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        name="GuideSubtitle",
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=20,
    )

    section_title_style = ParagraphStyle(
        name="SectionTitle",
        fontName=font_name,
        fontSize=16,
        leading=22,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0E7490"),
        spaceBefore=20,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        name="GuideBody",
        fontName=font_name,
        fontSize=11,
        leading=18,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10,
    )

    step_style = ParagraphStyle(
        name="GuideStep",
        fontName=font_name,
        fontSize=10,
        leading=16,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=20,
        spaceAfter=4,
    )

    footer_style = ParagraphStyle(
        name="GuideFooter",
        fontName=font_name,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#94A3B8"),
    )

    story = []

    # ── Cover Page ──
    story.append(Spacer(1, 4*cm))
    story.append(p(PRODUCT_NAME, title_style))
    story.append(p("HR in Motion — إدارة بسلاسة", subtitle_style))
    story.append(Spacer(1, 1*cm))
    story.append(p("دليل الاستخدام الشامل", ParagraphStyle(
        name="CoverGuide",
        fontName=font_name,
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),
    )))
    story.append(Spacer(1, 2*cm))
    story.append(p(f"إعداد: {COMPANY_NAME}", subtitle_style))
    story.append(p(f"هاتف: {PHONE}", subtitle_style))
    story.append(Spacer(1, 3*cm))

    story.append(HRFlowable(
        width="80%",
        thickness=2,
        color=colors.HexColor("#06B6D4"),
        spaceAfter=20,
    ))

    story.append(p("هذا الدليل يشرح كل شاشات النظام خطوة بخطوة", footer_style))
    story.append(PageBreak())

    # ── Table of Contents ──
    story.append(p("فهرس المحتويات", section_title_style))
    story.append(Spacer(1, 10))

    for i, section in enumerate(GUIDE_SECTIONS):
        toc_style = ParagraphStyle(
            name=f"TOC_{i}",
            fontName=font_name,
            fontSize=11,
            leading=20,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#0E7490"),
        )
        story.append(p(f"{i+1}. {section['title']}", toc_style))

    story.append(PageBreak())

    # ── Sections ──
    for i, section in enumerate(GUIDE_SECTIONS):
        # Section number + title
        story.append(p(f"— {i+1} —", ParagraphStyle(
            name=f"SecNum_{i}",
            fontName=font_name,
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#06B6D4"),
            spaceBefore=10,
        )))
        story.append(p(section["title"], section_title_style))

        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#E2E8F0"),
            spaceAfter=10,
        ))

        # Content
        story.append(p(section["content"], body_style))

        # Steps
        if section["steps"]:
            story.append(Spacer(1, 6))

            step_data = []
            for j, step in enumerate(section["steps"]):
                step_data.append([
                    Paragraph(escape(ar(step)), step_style),
                    Paragraph(escape(ar(f"الخطوة {j+1}")), ParagraphStyle(
                        name=f"StepNum_{i}_{j}",
                        fontName=font_name,
                        fontSize=9,
                        alignment=TA_CENTER,
                        textColor=colors.white,
                    )),
                ])

            table = Table(step_data, colWidths=[doc.width - 2.5*cm, 2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#06B6D4")),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('ROWBACKGROUNDS', (0, 0), (0, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)

        story.append(Spacer(1, 15))

        # لو مش آخر قسم، نضيف page break كل 2 sections
        if (i + 1) % 2 == 0 and i < len(GUIDE_SECTIONS) - 1:
            story.append(PageBreak())

    # ── Last Page ──
    story.append(PageBreak())
    story.append(Spacer(1, 4*cm))
    story.append(p(PRODUCT_NAME, title_style))
    story.append(p("HR in Motion — إدارة بسلاسة", subtitle_style))
    story.append(Spacer(1, 2*cm))
    story.append(p(f"للدعم الفني والمبيعات:", body_style))
    story.append(p(f"هاتف / واتساب: {PHONE}", body_style))
    story.append(p(f"{COMPANY_NAME}", body_style))
    story.append(Spacer(1, 3*cm))
    story.append(p("شكراً لاختياركم MotionHR", footer_style))

    doc.build(story)

    pdf_data = buffer.getvalue()
    buffer.close()

    with open(output_path, "wb") as f:
        f.write(pdf_data)

    print(f"\n✅ تم إنشاء الدليل: {os.path.relpath(output_path, BASE_DIR)}")
    print(f"   الحجم: {len(pdf_data) // 1024} KB")

    return output_path


if __name__ == "__main__":
    generate_guide()
