"""
Patch 49k-v2 — Professional Sales Kit PDF Generator

يولّد ملف PDF احترافي للمبيعات يحتوي على:
- غلاف احترافي
- نظرة عامة على المنتج
- كل المميزات بالتفصيل
- جدول الباقات والأسعار
- الوحدات الإضافية
- لمين البرنامج مناسب
- لماذا MotionHR
- الفترة التجريبية المجانية
- كيف تبدأ
- بيانات التواصل
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
        Spacer, PageBreak, HRFlowable, KeepTogether
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

from xml.sax.saxutils import escape

# ════════════════════════════════════════
# Config
# ════════════════════════════════════════
COMPANY = "JS Solutions"
PRODUCT = "MotionHR"
TAGLINE = "HR in Motion"
TAGLINE_AR = "إدارة بسلاسة"
PHONE = "(+20)01501551593"
WHATSAPP = "(+20)01501551593"
EMAIL = "info@jssolutions.com"

# Colors
PRIMARY = "#06B6D4"
PRIMARY_DARK = "#0E7490"
DARK = "#0F172A"
GRAY = "#64748B"
LIGHT_GRAY = "#94A3B8"
LIGHT_BG = "#F0FDFF"
WHITE = "#FFFFFF"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
PURPLE = "#8B5CF6"
CYAN = "#06B6D4"

# ════════════════════════════════════════
# Font
# ════════════════════════════════════════
FONT_NAME = "SalesKitFont"
FONT_REGISTERED = False

def register_font():
    global FONT_REGISTERED
    if FONT_REGISTERED:
        return FONT_NAME
    candidates = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "calibri.ttf"),
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

def p(text, style):
    return Paragraph(escape(ar(str(text))), style)

def colored_p(text, style, color):
    s = ParagraphStyle(f'colored_{id(text)}', parent=style, textColor=colors.HexColor(color))
    return Paragraph(escape(ar(str(text))), s)


def generate_sales_kit():
    font_name = register_font()
    output_path = os.path.join(BASE_DIR, "static", "MotionHR_Sales_Kit.pdf")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8*cm,
        leftMargin=1.8*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title=f"{PRODUCT} — Sales Kit",
        author=COMPANY,
    )

    page_width = A4[0] - 3.6*cm

    # ════════════════════════════════════════
    # Styles
    # ════════════════════════════════════════
    cover_title = ParagraphStyle(
        "CoverTitle", fontName=font_name, fontSize=36, leading=44,
        alignment=TA_CENTER, textColor=colors.HexColor(PRIMARY),
        spaceAfter=8,
    )
    cover_tagline = ParagraphStyle(
        "CoverTagline", fontName=font_name, fontSize=16, leading=22,
        alignment=TA_CENTER, textColor=colors.HexColor(DARK),
        spaceAfter=6,
    )
    cover_sub = ParagraphStyle(
        "CoverSub", fontName=font_name, fontSize=12, leading=18,
        alignment=TA_CENTER, textColor=colors.HexColor(GRAY),
        spaceAfter=4,
    )
    section_title = ParagraphStyle(
        "SectionTitle", fontName=font_name, fontSize=20, leading=28,
        alignment=TA_RIGHT, textColor=colors.HexColor(PRIMARY_DARK),
        spaceBefore=16, spaceAfter=10,
    )
    subsection_title = ParagraphStyle(
        "SubsectionTitle", fontName=font_name, fontSize=14, leading=20,
        alignment=TA_RIGHT, textColor=colors.HexColor(DARK),
        spaceBefore=12, spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body", fontName=font_name, fontSize=11, leading=19,
        alignment=TA_RIGHT, textColor=colors.HexColor(DARK),
        spaceAfter=6,
    )
    body_small = ParagraphStyle(
        "BodySmall", fontName=font_name, fontSize=10, leading=16,
        alignment=TA_RIGHT, textColor=colors.HexColor(GRAY),
        spaceAfter=4,
    )
    bullet = ParagraphStyle(
        "Bullet", fontName=font_name, fontSize=10, leading=17,
        alignment=TA_RIGHT, textColor=colors.HexColor(DARK),
        rightIndent=15, spaceAfter=3,
    )
    center_body = ParagraphStyle(
        "CenterBody", fontName=font_name, fontSize=11, leading=19,
        alignment=TA_CENTER, textColor=colors.HexColor(DARK),
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer", fontName=font_name, fontSize=9, leading=13,
        alignment=TA_CENTER, textColor=colors.HexColor(LIGHT_GRAY),
    )
    table_header_style = ParagraphStyle(
        "TableHeader", fontName=font_name, fontSize=9, leading=13,
        alignment=TA_CENTER, textColor=colors.white,
    )
    table_cell_style = ParagraphStyle(
        "TableCell", fontName=font_name, fontSize=9, leading=13,
        alignment=TA_CENTER, textColor=colors.HexColor(DARK),
    )
    highlight_box = ParagraphStyle(
        "HighlightBox", fontName=font_name, fontSize=12, leading=20,
        alignment=TA_CENTER, textColor=colors.HexColor(PRIMARY_DARK),
        spaceBefore=10, spaceAfter=10,
    )
    cta_style = ParagraphStyle(
        "CTA", fontName=font_name, fontSize=14, leading=22,
        alignment=TA_CENTER, textColor=colors.HexColor(SUCCESS),
        spaceBefore=8, spaceAfter=8,
    )

    story = []

    def add_divider(width="90%", color=PRIMARY, thickness=2):
        story.append(Spacer(1, 6))
        story.append(HRFlowable(
            width=width, thickness=thickness,
            color=colors.HexColor(color), spaceAfter=10,
        ))

    def add_section_page(title_text):
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*cm))
        story.append(p(title_text, section_title))
        add_divider()

    def add_feature_table(features_list, icon_color=PRIMARY):
        data = []
        for i, feat in enumerate(features_list):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            data.append([
                Paragraph(escape(ar(feat)), ParagraphStyle(
                    f"feat_{i}", fontName=font_name, fontSize=10,
                    leading=16, alignment=TA_RIGHT,
                    textColor=colors.HexColor(DARK),
                )),
                Paragraph(escape(ar("✅")), ParagraphStyle(
                    f"check_{i}", fontName=font_name, fontSize=12,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor(SUCCESS),
                )),
            ])

        t = Table(data, colWidths=[page_width - 1.5*cm, 1.2*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
        ] + [
            ('BACKGROUND', (0, i), (-1, i),
             colors.HexColor(LIGHT_BG if i % 2 == 0 else WHITE))
            for i in range(len(data))
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ════════════════════════════════════════
    # PAGE 1: COVER
    # ════════════════════════════════════════
    story.append(Spacer(1, 3*cm))
    story.append(p(PRODUCT, cover_title))
    story.append(p(f"{TAGLINE} — {TAGLINE_AR}", cover_tagline))
    story.append(Spacer(1, 1.5*cm))

    add_divider("60%", PRIMARY, 3)

    story.append(Spacer(1, 1*cm))
    story.append(p("نظام إدارة الموارد البشرية الأذكى في مصر", ParagraphStyle(
        "CoverDesc", fontName=font_name, fontSize=14, leading=22,
        alignment=TA_CENTER, textColor=colors.HexColor(DARK),
    )))
    story.append(Spacer(1, 0.5*cm))
    story.append(p("تتبع ميداني · حضور GPS · سياسات مرنة · إشعارات فورية", cover_sub))
    story.append(Spacer(1, 2*cm))

    # Free Trial Box
    trial_data = [[
        Paragraph(escape(ar("جرّب مجاناً 14 يوم — كل المميزات مفتوحة — بدون بطاقة ائتمان")),
                  ParagraphStyle("TrialBox", fontName=font_name, fontSize=12,
                                 leading=20, alignment=TA_CENTER,
                                 textColor=colors.white))
    ]]
    trial_table = Table(trial_data, colWidths=[page_width])
    trial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(SUCCESS)),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    story.append(trial_table)

    story.append(Spacer(1, 2*cm))
    story.append(p(COMPANY, cover_sub))
    story.append(p(f"هاتف/واتساب: {PHONE}", cover_sub))

    # ════════════════════════════════════════
    # PAGE 2: نظرة عامة
    # ════════════════════════════════════════
    add_section_page("نظرة عامة على النظام")

    story.append(p(
        "MotionHR هو نظام إدارة موارد بشرية عصري وذكي مصمم خصيصاً للشركات في مصر والعالم العربي. "
        "يتميز بتتبع الموظفين الميدانيين في الوقت الفعلي على الخريطة، نظام حضور ذكي بالـ GPS، "
        "سياسات مرنة تناسب كل أنواع الشركات، وإشعارات فورية لكل الأحداث المهمة.",
        body
    ))
    story.append(Spacer(1, 6))

    overview_points = [
        "يعمل من أي جهاز (كمبيوتر / موبايل / تابلت) — بدون تنزيل أي برنامج",
        "واجهة عربية RTL بالكامل مع دعم اللغة الإنجليزية",
        "كل شركة معزولة تماماً عن الأخرى (Multi-tenant)",
        "تحديثات مستمرة ومجانية — بدون رسوم إضافية",
        "بياناتك آمنة ومشفرة على سيرفرات محمية",
        "دعم فني بالعربي عبر الواتساب والإيميل",
        "يُثبّت على الموبايل كتطبيق مستقل (PWA)",
    ]
    add_feature_table(overview_points)

    # ════════════════════════════════════════
    # PAGE 3-6: المميزات
    # ════════════════════════════════════════
    features_sections = [
        {
            "title": "إدارة الموظفين",
            "icon": "📋",
            "features": [
                "ملف شامل لكل موظف (بيانات شخصية + عمل + مالية + تأمينات)",
                "نموذج إضافة ذكي من 5 مراحل يمنعك تنسى أي بيانات",
                "هيكل وظيفي واضح (مستويات + مسميات + مدير مباشر تلقائي)",
                "27 تصنيف مستند جاهز لملف الموظف الإلكتروني",
                "ملف شامل يعرض كل بيانات الموظف في صفحة واحدة",
                "تصدير قائمة الموظفين (Excel + PDF) باللغة العربية",
                "بحث فوري حرف بحرف (Live Search) في كل البيانات",
                "إنشاء حساب دخول تلقائي لكل موظف جديد",
            ],
        },
        {
            "title": "الحضور والانصراف الذكي (GPS)",
            "icon": "📍",
            "features": [
                "تسجيل الحضور بالموقع الجغرافي (GPS) من الموبايل",
                "Geofencing — التحقق من وجود الموظف داخل نطاق الفرع",
                "تنبيه فوري لو الموظف سجل حضور من مكان غير معتمد",
                "سجلات مفصلة (وقت الدخول / الخروج / التأخير / الغياب)",
                "تعديل السجلات من HR مع Audit Log كامل",
                "إحصائيات يومية لحظية (حاضر / متأخر / غائب / إجازة)",
                "بدون أجهزة بصمة — الموبايل كافي",
            ],
        },
        {
            "title": "التتبع الميداني الحي (Live Tracking)",
            "icon": "🗺️",
            "features": [
                "خريطة حية تعرض مواقع كل الموظفين الميدانيين لحظة بلحظة",
                "تتبع صامت (Stealth Tracking) بدون علم الموظف",
                "تنبيهات فورية لو الموظف خرج من المنطقة المسموحة",
                "سجل تحركات كامل لكل موظف قابل للمراجعة",
                "تسجيل الزيارات الميدانية مع تحديد الموقع والغرض",
                "مناسب لشركات التوزيع والمقاولات والصيانة",
            ],
        },
        {
            "title": "جداول العمل الذكية (Smart Schedule)",
            "icon": "📅",
            "features": [
                "7 أنواع أيام (عمل / إجازة / مهمة / تدريب / استعداد / ...)",
                "6 أنماط عمل (ثابت / مرن / متقسم / ميداني / عن بُعد / مختلط)",
                "الشاشة تتغير تلقائياً حسب نمط العمل المختار",
                "تكليفات فردية أو جماعية",
                "دعم الورديات المتعددة والمتقسمة",
            ],
        },
        {
            "title": "نظام التأخيرات والإنذارات التلقائي",
            "icon": "⏰",
            "features": [
                "حساب التأخير تلقائياً بالدقيقة من سجلات الحضور",
                "فترة سماح قابلة للتعديل حسب سياسة الشركة",
                "تصعيد تلقائي: تنبيه ← إنذار ← خصم ← إجراء تأديبي",
                "سجل إنذارات كامل لكل موظف",
                "خصومات تلقائية مرتبطة بالتأخير والغياب",
            ],
        },
        {
            "title": "نظام الإجازات المتكامل",
            "icon": "🏖️",
            "features": [
                "أنواع إجازات مخصصة (سنوية / مرضية / عارضة / أمومة / ...)",
                "رصيد إجازات لكل موظف يتحدث تلقائياً",
                "طلب إجازة إلكتروني مع مسار موافقة",
                "الموظف يشوف رصيده المتبقي من حسابه في أي وقت",
            ],
        },
        {
            "title": "نظام الطلبات الإلكتروني (18 نوع طلب)",
            "icon": "📝",
            "features": [
                "سلفة / إذن خروج / إذن تأخير / شهادة خبرة",
                "تغيير وردية / نقل / ترقية / تعديل بيانات",
                "مسار موافقة من 3 خطوات (مدير ← HR ← إدارة عليا)",
                "تفويض الصلاحيات لو المدير في إجازة",
                "متابعة حالة كل طلب لحظة بلحظة",
            ],
        },
        {
            "title": "التقارير والتحليلات",
            "icon": "📊",
            "features": [
                "تقرير الحضور والغياب الشامل",
                "تقرير التأخيرات مع تفاصيل كل تأخير",
                "تقرير الإجازات وأرصدتها",
                "تقرير بيانات الموظفين الكامل",
                "تقرير الموظفين الميدانيين وتحركاتهم",
                "ملف شامل لأي موظف (كل البيانات في صفحة واحدة)",
                "تصدير Excel احترافي (ألوان + لوجو + تنسيق)",
                "تصدير PDF باللغة العربية",
                "لوجو الشركة واسمها في كل تقرير تلقائياً",
            ],
        },
        {
            "title": "ميثاق العمل والتوقيع الرقمي",
            "icon": "📜",
            "features": [
                "إنشاء ميثاق عمل رقمي بأي عدد بنود",
                "توقيع رقمي حقيقي من كل موظف (اسم + رقم قومي + IP + تاريخ)",
                "متابعة حالة التوقيع: مين وقّع ومين لسه",
                "إرسال تذكير تلقائي للموظفين اللي ما وقعوش",
                "طباعة الميثاق بالتوقيع الرقمي كمستند رسمي",
            ],
        },
        {
            "title": "إدارة ملفات ومستندات الموظفين",
            "icon": "📁",
            "features": [
                "27 تصنيف مستند جاهز (بطاقة / عقد / شهادة / تقرير طبي / ...)",
                "ربط المستند بحدث (تعيين / ترقية / إجازة / طبي / ...)",
                "مستندات سرية وعادية",
                "تاريخ إصدار وانتهاء لكل مستند",
                "عرض / تحميل / حذف من صفحة واحدة منظمة",
            ],
        },
    ]

    for feat_section in features_sections:
        add_section_page(f"{feat_section['icon']} {feat_section['title']}")
        add_feature_table(feat_section["features"])

    # ════════════════════════════════════════
    # PRICING PAGE
    # ════════════════════════════════════════
    add_section_page("خطط الاشتراك والأسعار")

    # Free trial banner
    trial_banner = [[
        Paragraph(escape(ar("🎁 جرّب مجاناً لمدة 14 يوم — كل المميزات مفتوحة — بدون التزام — بدون بطاقة ائتمان")),
                  ParagraphStyle("TrialBanner", fontName=font_name, fontSize=11,
                                 leading=18, alignment=TA_CENTER,
                                 textColor=colors.white))
    ]]
    trial_t = Table(trial_banner, colWidths=[page_width])
    trial_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(SUCCESS)),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(trial_t)
    story.append(Spacer(1, 12))

    # Pricing Table
    def tp(text, bold=False, color=DARK, size=9):
        weight = font_name
        return Paragraph(
            escape(ar(str(text))),
            ParagraphStyle(f"tp_{id(text)}", fontName=weight, fontSize=size,
                           leading=14, alignment=TA_CENTER,
                           textColor=colors.HexColor(color))
        )

    pricing_header = [
        tp("", color=WHITE),
        tp("Basic أساسية", color=WHITE, size=10),
        tp("Business أعمال", color=WHITE, size=10),
        tp("Enterprise مؤسسات", color=WHITE, size=10),
    ]

    pricing_rows = [
        [tp("السعر الشهري"), tp("199 ج.م", color=SUCCESS), tp("499 ج.م", color=PRIMARY_DARK), tp("999 ج.م", color=PURPLE)],
        [tp("السعر السنوي"), tp("1,990 ج.م"), tp("4,990 ج.م"), tp("9,990 ج.م")],
        [tp("(وفّر شهرين)"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("عدد الموظفين"), tp("حتى 30"), tp("حتى 150"), tp("غير محدود")],
        [tp("إدارة الموظفين"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("الحضور GPS"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("الإجازات"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("الطلبات (18 نوع)"), tp("—"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("التقارير"), tp("أساسية"), tp("✅ كاملة", color=SUCCESS), tp("✅ كاملة", color=SUCCESS)],
        [tp("الخريطة الحية"), tp("—"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("التتبع الصامت"), tp("—"), tp("—"), tp("✅", color=SUCCESS)],
        [tp("Workflow"), tp("خطوة واحدة"), tp("3 خطوات"), tp("غير محدود")],
        [tp("المستندات"), tp("—"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("ميثاق العمل"), tp("—"), tp("✅", color=SUCCESS), tp("✅", color=SUCCESS)],
        [tp("API"), tp("—"), tp("—"), tp("✅", color=SUCCESS)],
        [tp("الدعم الفني"), tp("إيميل"), tp("واتساب + إيميل"), tp("واتساب + اتصال")],
    ]

    pricing_data = [pricing_header] + pricing_rows
    col_w = page_width / 4
    pricing_table = Table(pricing_data, colWidths=[col_w] * 4)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY_DARK)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]

    for i in range(1, len(pricing_data)):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(bg)))

    pricing_table.setStyle(TableStyle(style_cmds))
    story.append(pricing_table)

    # ════════════════════════════════════════
    # ADD-ONS PAGE
    # ════════════════════════════════════════
    add_section_page("الوحدات الإضافية (Add-ons)")

    story.append(p(
        "وحدات إضافية يمكن تفعيلها حسب احتياج شركتك. "
        "كل وحدة تُضاف لباقتك الحالية بتكلفة شهرية إضافية بسيطة.",
        body
    ))
    story.append(Spacer(1, 8))

    addons = [
        ["💰 الرواتب والأجور", "200 ج.م/شهر", "حساب آلي للرواتب + مسيرات + تصدير بنكي + تأمينات"],
        ["👤 التوظيف (ATS)", "150 ج.م/شهر", "نشر وظائف + استقبال CVs + مقابلات + تحويل لموظف"],
        ["📊 تقييم الأداء", "150 ج.م/شهر", "KPIs + تقييم 360° + ربط بالمكافآت"],
        ["📚 إدارة التدريب", "100 ج.م/شهر", "خطط تدريب + شهادات + متابعة حضور"],
        ["💻 الأصول والعهد", "100 ج.م/شهر", "تسليم/استلام + إخلاء طرف + صيانة"],
        ["🔌 الربط البرمجي (API)", "حسب الطلب", "REST API + Webhooks + ربط ERP"],
    ]

    addon_header = [
        tp("الوحدة", color=WHITE, size=10),
        tp("التكلفة", color=WHITE, size=10),
        tp("أبرز المميزات", color=WHITE, size=10),
    ]

    addon_rows = []
    for addon in addons:
        addon_rows.append([tp(addon[0]), tp(addon[1], color=SUCCESS), tp(addon[2])])

    addon_data = [addon_header] + addon_rows
    addon_table = Table(addon_data, colWidths=[page_width * 0.28, page_width * 0.18, page_width * 0.54])

    addon_style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY_DARK)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]
    for i in range(1, len(addon_data)):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        addon_style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(bg)))

    addon_table.setStyle(TableStyle(addon_style_cmds))
    story.append(addon_table)

    # ════════════════════════════════════════
    # TARGET AUDIENCE
    # ════════════════════════════════════════
    add_section_page("لمين البرنامج مناسب؟")

    targets = [
        ("🏗️", "شركات المقاولات والبناء", "تتبع العمال في المواقع + حضور GPS + جداول مرنة"),
        ("🚚", "شركات التوزيع والنقل", "تتبع السائقين + زيارات ميدانية + خريطة حية"),
        ("🔧", "شركات الصيانة والخدمات", "تتبع فنيين الصيانة + جداول مرنة + تقارير"),
        ("🏢", "الشركات المتوسطة (50-300 موظف)", "إدارة شاملة + تقارير + workflow + إجازات"),
        ("🏬", "سلاسل المحلات والفروع", "Geofencing + حضور متعدد الفروع"),
        ("🏥", "المستشفيات والعيادات", "ورديات متقسمة + حضور دقيق + تقارير"),
        ("📱", "أي شركة عندها موظفين ميدانيين", "Live Map + Stealth Tracking + GPS"),
    ]

    for icon, title, desc in targets:
        target_data = [[
            Paragraph(escape(ar(f"{icon} {title}")), ParagraphStyle(
                f"t_title_{title}", fontName=font_name, fontSize=11,
                leading=16, alignment=TA_RIGHT,
                textColor=colors.HexColor(PRIMARY_DARK),
            )),
            Paragraph(escape(ar(desc)), ParagraphStyle(
                f"t_desc_{title}", fontName=font_name, fontSize=10,
                leading=15, alignment=TA_RIGHT,
                textColor=colors.HexColor(GRAY),
            )),
        ]]
        t = Table(target_data, colWidths=[page_width * 0.4, page_width * 0.6])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)

    # ════════════════════════════════════════
    # WHY MOTIONHR
    # ════════════════════════════════════════
    add_section_page("لماذا MotionHR؟")

    why_points = [
        "عربي 100% — واجهة ولغة وتقارير بالعربي الكامل",
        "مصمم خصيصاً للسوق المصري والعربي",
        "بدون أجهزة بصمة — الموبايل كافي",
        "بدون تنزيل — يعمل من المتصفح مباشرة",
        "تحديثات مستمرة ومجانية — بدون رسوم إضافية",
        "دعم فني بالعربي عبر الواتساب والإيميل",
        "فترة تجريبية 14 يوم مجاناً — كل المميزات مفتوحة",
        "بياناتك آمنة ومشفرة على سيرفرات محمية 24/7",
        "كل شركة معزولة تماماً عن الأخرى (Multi-tenant)",
        "يُثبّت على الموبايل كتطبيق مستقل بدون متجر",
    ]
    add_feature_table(why_points)

    # ════════════════════════════════════════
    # HOW TO START
    # ════════════════════════════════════════
    add_section_page("كيف تبدأ؟")

    steps = [
        ("1️⃣", "تواصل معنا", f"واتساب أو اتصال: {PHONE}"),
        ("2️⃣", "احصل على فترة تجريبية", "14 يوم مجاناً — كل المميزات مفتوحة — بدون التزام"),
        ("3️⃣", "أدخل بيانات شركتك", "بمساعدة فريق الدعم الفني — فروع + إدارات + موظفين"),
        ("4️⃣", "ابدأ العمل فوراً", "الموظفين يسجلون حضورهم من الموبايل في نفس اليوم"),
        ("5️⃣", "اختر باقتك", "قبل انتهاء الفترة التجريبية — وفعّل الاشتراك"),
    ]

    for icon, title, desc in steps:
        step_data = [[
            Paragraph(escape(ar(f"{icon} {title}")), ParagraphStyle(
                f"step_t_{title}", fontName=font_name, fontSize=12,
                leading=18, alignment=TA_RIGHT,
                textColor=colors.HexColor(PRIMARY_DARK),
            )),
            Paragraph(escape(ar(desc)), ParagraphStyle(
                f"step_d_{title}", fontName=font_name, fontSize=10,
                leading=16, alignment=TA_RIGHT,
                textColor=colors.HexColor(GRAY),
            )),
        ]]
        t = Table(step_data, colWidths=[page_width * 0.35, page_width * 0.65])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(LIGHT_BG)),
        ]))
        story.append(t)
        story.append(Spacer(1, 4))

    # ════════════════════════════════════════
    # LAST PAGE: CONTACT + CTA
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(Spacer(1, 3*cm))
    story.append(p(PRODUCT, cover_title))
    story.append(p(f"{TAGLINE} — {TAGLINE_AR}", cover_tagline))
    story.append(Spacer(1, 1.5*cm))

    add_divider("50%", SUCCESS, 3)

    story.append(Spacer(1, 1*cm))
    story.append(p("جاهز تطوّر إدارة شركتك؟", ParagraphStyle(
        "LastCTA", fontName=font_name, fontSize=18, leading=26,
        alignment=TA_CENTER, textColor=colors.HexColor(DARK),
    )))
    story.append(Spacer(1, 0.5*cm))

    # Contact Box
    contact_data = [
        [Paragraph(escape(ar(f"📞 هاتف/واتساب: {PHONE}")),
                   ParagraphStyle("c1", fontName=font_name, fontSize=13,
                                  leading=22, alignment=TA_CENTER,
                                  textColor=colors.HexColor(DARK)))],
        [Paragraph(escape(ar(f"📧 إيميل: {EMAIL}")),
                   ParagraphStyle("c2", fontName=font_name, fontSize=12,
                                  leading=20, alignment=TA_CENTER,
                                  textColor=colors.HexColor(GRAY)))],
        [Paragraph(escape(ar(f"🏢 {COMPANY}")),
                   ParagraphStyle("c3", fontName=font_name, fontSize=12,
                                  leading=20, alignment=TA_CENTER,
                                  textColor=colors.HexColor(GRAY)))],
    ]
    contact_table = Table(contact_data, colWidths=[page_width * 0.7])
    contact_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(contact_table)

    story.append(Spacer(1, 1.5*cm))

    # Final trial CTA
    final_trial = [[
        Paragraph(escape(ar("🎁 ابدأ فترتك التجريبية المجانية الآن — 14 يوم — كل المميزات — بدون التزام")),
                  ParagraphStyle("FinalCTA", fontName=font_name, fontSize=13,
                                 leading=22, alignment=TA_CENTER,
                                 textColor=colors.white))
    ]]
    final_t = Table(final_trial, colWidths=[page_width * 0.85])
    final_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(PRIMARY_DARK)),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(final_t)

    story.append(Spacer(1, 2*cm))
    story.append(p(f"© 2025 {COMPANY}. All rights reserved.", footer_style))
    story.append(p(f"{PRODUCT} — {TAGLINE}", footer_style))

    # ════════════════════════════════════════
    # Build
    # ════════════════════════════════════════
    doc.build(story)

    pdf_data = buffer.getvalue()
    buffer.close()

    with open(output_path, "wb") as f:
        f.write(pdf_data)

    print(f"\n✅ تم إنشاء Sales Kit PDF:")
    print(f"   📄 {os.path.relpath(output_path, BASE_DIR)}")
    print(f"   📦 الحجم: {len(pdf_data) // 1024} KB")
    print(f"\n   افتحه من: http://127.0.0.1:8000/static/MotionHR_Sales_Kit.pdf")

    return output_path


if __name__ == "__main__":
    generate_sales_kit()