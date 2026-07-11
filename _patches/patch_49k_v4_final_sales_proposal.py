"""
Patch 49k-v4 — Final Sales Proposal PDF
عرض سعر احترافي نهائي بالتسعير المعتمد
"""

import os
import sys
from io import BytesIO
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, HRFlowable
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("❌ شغّل: pip install reportlab")
    sys.exit(1)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

from xml.sax.saxutils import escape

COMPANY = "JS Solutions"
PRODUCT = "MotionHR"
TAGLINE = "HR in Motion — إدارة بسلاسة"
PHONE = "(+20)01501551593"
EMAIL = "info@jssolutions.com"
WHATSAPP = "2001501551593"

PROPOSAL_DATE = datetime.now().strftime("%Y/%m/%d")
PROPOSAL_EXPIRY = (datetime.now() + timedelta(days=14)).strftime("%Y/%m/%d")
REF = f"MHR-{datetime.now().strftime('%Y%m%d')}-001"

PRIMARY = "#06B6D4"
PRIMARY_DARK = "#0E7490"
DARK = "#0F172A"
GRAY = "#64748B"
LIGHT_GRAY = "#94A3B8"
LIGHT_BG = "#F0FDFF"
WHITE = "#FFFFFF"
SUCCESS = "#10B981"
PURPLE = "#8B5CF6"
GOLD = "#F59E0B"

FONT_NAME = "SalesFont"
_FONT_REG = False

def reg_font():
    global _FONT_REG
    if _FONT_REG: return FONT_NAME
    for p in [
        os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts","tahoma.ttf"),
        os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts","arial.ttf"),
    ]:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, p))
                _FONT_REG = True
                return FONT_NAME
            except: pass
    return "Helvetica"

def ar(t):
    if not t: return ''
    t = str(t)
    if HAS_ARABIC:
        try:
            t = arabic_reshaper.reshape(t)
            t = get_display(t)
        except: pass
    return t

def P(t, s):
    return Paragraph(escape(ar(str(t))), s)

def generate():
    fn = reg_font()
    out = os.path.join(BASE_DIR, "static", "MotionHR_Sales_Proposal.pdf")
    buf = BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title=f"{PRODUCT} Sales Proposal", author=COMPANY)

    pw = A4[0] - 3.6*cm

    # Styles
    s_cover = ParagraphStyle("cover", fontName=fn, fontSize=34, leading=42, alignment=TA_CENTER, textColor=colors.HexColor(PRIMARY))
    s_cover_sub = ParagraphStyle("csub", fontName=fn, fontSize=15, leading=22, alignment=TA_CENTER, textColor=colors.HexColor(DARK))
    s_meta = ParagraphStyle("meta", fontName=fn, fontSize=11, leading=16, alignment=TA_CENTER, textColor=colors.HexColor(GRAY))
    s_section = ParagraphStyle("sec", fontName=fn, fontSize=18, leading=26, alignment=TA_RIGHT, textColor=colors.HexColor(PRIMARY_DARK), spaceBefore=14, spaceAfter=8)
    s_subsec = ParagraphStyle("subsec", fontName=fn, fontSize=13, leading=19, alignment=TA_RIGHT, textColor=colors.HexColor(DARK), spaceBefore=10, spaceAfter=4)
    s_body = ParagraphStyle("body", fontName=fn, fontSize=11, leading=19, alignment=TA_RIGHT, textColor=colors.HexColor(DARK), spaceAfter=6)
    s_small = ParagraphStyle("small", fontName=fn, fontSize=10, leading=16, alignment=TA_RIGHT, textColor=colors.HexColor(GRAY), spaceAfter=4)
    s_footer = ParagraphStyle("foot", fontName=fn, fontSize=9, leading=13, alignment=TA_CENTER, textColor=colors.HexColor(LIGHT_GRAY))

    def tp(t, color=DARK, size=9):
        return Paragraph(escape(ar(str(t))), ParagraphStyle(f"t{id(t)}", fontName=fn, fontSize=size, leading=14, alignment=TA_CENTER, textColor=colors.HexColor(color)))

    def divider(w="90%", c=PRIMARY, th=2):
        story.append(Spacer(1,6))
        story.append(HRFlowable(width=w, thickness=th, color=colors.HexColor(c), spaceAfter=10))

    def banner(text, bg=SUCCESS, size=12):
        d = [[Paragraph(escape(ar(text)), ParagraphStyle(f"ban{id(text)}", fontName=fn, fontSize=size, leading=20, alignment=TA_CENTER, textColor=colors.white))]]
        t = Table(d, colWidths=[pw])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(bg)),('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),('ALIGN',(0,0),(-1,-1),'CENTER')]))
        story.append(t)

    def feature_table(features):
        data = []
        for i, f in enumerate(features):
            data.append([
                Paragraph(escape(ar(f)), ParagraphStyle(f"f{i}{id(f)}", fontName=fn, fontSize=10, leading=16, alignment=TA_RIGHT, textColor=colors.HexColor(DARK))),
                tp("✅", color=SUCCESS, size=11)
            ])
        t = Table(data, colWidths=[pw-1.2*cm, 1*cm])
        cmds = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#E2E8F0"))]
        for i in range(len(data)):
            cmds.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor(LIGHT_BG if i%2==0 else WHITE)))
        t.setStyle(TableStyle(cmds))
        story.append(t)
        story.append(Spacer(1,6))

    story = []

    # ════════════════════════════════════════
    # COVER
    # ════════════════════════════════════════
    story.append(Spacer(1, 2.5*cm))
    story.append(P(PRODUCT, s_cover))
    story.append(P(TAGLINE, s_cover_sub))
    story.append(Spacer(1, 1.5*cm))
    divider("50%", PRIMARY, 3)
    story.append(Spacer(1, 0.8*cm))
    story.append(P("عرض أسعار — سعر إطلاق خاص", ParagraphStyle("pt", fontName=fn, fontSize=20, leading=28, alignment=TA_CENTER, textColor=colors.HexColor(DARK))))
    story.append(Spacer(1, 0.8*cm))

    # Meta
    md = [
        [tp("القيمة", color=WHITE, size=10), tp("البند", color=WHITE, size=10)],
        [tp(REF), tp("رقم العرض")],
        [tp(PROPOSAL_DATE), tp("تاريخ العرض")],
        [tp(PROPOSAL_EXPIRY), tp("صالح حتى")],
        [tp("14 يوم"), tp("مدة الصلاحية")],
    ]
    mt = Table(md, colWidths=[pw*0.5]*2)
    mt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor("#DEE2E6")),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('BACKGROUND',(0,1),(-1,1),colors.HexColor(LIGHT_BG)),('BACKGROUND',(0,3),(-1,3),colors.HexColor(LIGHT_BG)),
    ]))
    story.append(mt)
    story.append(Spacer(1, 1.5*cm))

    # Launch banner
    banner("🚀 عرض إطلاق خاص — أسعار تنافسية + بدون رسوم تنفيذ + بدون رسوم تدريب + 14 يوم مجاناً", GOLD, 12)
    story.append(Spacer(1, 0.5*cm))
    banner("🎁 فترة تجريبية مجانية 14 يوم — كل المميزات مفتوحة — بدون بطاقة ائتمان — بدون التزام", SUCCESS, 12)

    story.append(Spacer(1, 1.5*cm))
    story.append(P(COMPANY, s_meta))
    story.append(P(f"هاتف/واتساب: {PHONE}", s_meta))
    story.append(P(f"إيميل: {EMAIL}", s_meta))

    # ════════════════════════════════════════
    # WHY DIFFERENT
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("لماذا MotionHR مختلف؟", s_section))
    divider()

    story.append(P("4 مميزات حصرية تجعلنا الخيار الأذكى:", s_subsec))
    story.append(Spacer(1, 8))

    diff_data = [
        [tp("الميزة", color=WHITE, size=10), tp("التفاصيل", color=WHITE, size=10), tp("الوفر", color=WHITE, size=10)],
        [tp("🚫 بدون رسوم تنفيذ", color=SUCCESS, size=10), tp("التنفيذ والإعداد مجاناً بالكامل", size=9), tp("وفّر 5% من قيمة الاشتراك السنوي", color=SUCCESS, size=9)],
        [tp("🎓 تدريب مجاني", color=SUCCESS, size=10), tp("جلسات تدريب حية ومسجلة — بدون رسوم إضافية", size=9), tp("وفّر 1,000 — 3,000 ج.م", color=SUCCESS, size=9)],
        [tp("🎁 14 يوم مجاناً", color=SUCCESS, size=10), tp("جرّب النظام بكل مميزاته قبل أي التزام مالي", size=9), tp("بدون مخاطرة", color=SUCCESS, size=9)],
        [tp("📍 تتبع ميداني أقوى", color=SUCCESS, size=10), tp("خريطة حية + تتبع صامت + Geofencing + زيارات", size=9), tp("ميزة حصرية", color=PRIMARY_DARK, size=9)],
    ]
    dt = Table(diff_data, colWidths=[pw*0.28, pw*0.45, pw*0.27])
    dt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#DEE2E6")),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('BACKGROUND',(0,1),(-1,1),colors.HexColor(LIGHT_BG)),('BACKGROUND',(0,3),(-1,3),colors.HexColor(LIGHT_BG)),
    ]))
    story.append(dt)

    # ════════════════════════════════════════
    # FEATURES
    # ════════════════════════════════════════
    feat_groups = [
        ("📋 إدارة الموظفين", [
            "ملف شامل لكل موظف (بيانات شخصية + تعيين + مالية + تأمينات)",
            "نموذج إضافة ذكي من 5 مراحل يمنعك تنسى أي بيانات",
            "هيكل وظيفي واضح (مستويات + مسميات + مدير مباشر تلقائي)",
            "27 تصنيف مستند لملف الموظف الإلكتروني",
            "بحث فوري Live Search في كل البيانات",
            "إنشاء حساب دخول تلقائي لكل موظف",
            "تصدير Excel + PDF احترافي باللغة العربية",
        ]),
        ("📍 الحضور الذكي (GPS)", [
            "تسجيل حضور بالموقع الجغرافي من الموبايل — بدون أجهزة بصمة",
            "Geofencing — التحقق من وجود الموظف داخل نطاق الفرع",
            "تنبيه فوري لو الموظف سجل من مكان غير معتمد",
            "سجلات مفصلة + تعديل من HR مع Audit Log كامل",
            "إحصائيات يومية لحظية (حاضر / متأخر / غائب / إجازة)",
        ]),
        ("🗺️ التتبع الميداني الحي", [
            "خريطة حية لمواقع الموظفين الميدانيين لحظة بلحظة",
            "تتبع صامت (Stealth Tracking) بدون علم الموظف",
            "تنبيهات خروج من المنطقة المسموحة",
            "سجل تحركات كامل + زيارات ميدانية",
        ]),
        ("📅 جداول العمل الذكية", [
            "7 أنواع أيام + 6 أنماط عمل (ثابت / مرن / متقسم / ميداني / عن بُعد / مختلط)",
            "الشاشة تتغير تلقائياً حسب النمط المختار",
        ]),
        ("⏰ التأخيرات والإنذارات", [
            "حساب تلقائي بالدقيقة + تصعيد: تنبيه ← إنذار ← خصم ← إجراء تأديبي",
            "خصومات تلقائية مرتبطة بالتأخير والغياب",
        ]),
        ("🏖️ الإجازات + 📝 الطلبات", [
            "إجازات مخصصة + رصيد تلقائي + طلب إلكتروني",
            "18 نوع طلب + مسار موافقة 3 خطوات + تفويض صلاحيات",
        ]),
        ("📊 التقارير + 📜 الميثاق", [
            "5 تقارير + ملف شامل + Excel/PDF بلوجو الشركة",
            "ميثاق عمل رقمي + توقيع رقمي حقيقي + متابعة + طباعة رسمية",
        ]),
        ("📱 يعمل على كل الأجهزة", [
            "بدون تنزيل — من المتصفح مباشرة (كمبيوتر / موبايل / تابلت)",
            "يُثبّت كتطبيق على الموبايل (PWA) + إشعارات فورية",
            "واجهة عربية RTL + Multi-tenant + تحديثات مجانية مستمرة",
        ]),
    ]

    story.append(PageBreak())
    story.append(P("المميزات والخدمات المتضمنة", s_section))
    divider()

    for gtitle, feats in feat_groups:
        story.append(P(f"▸ {gtitle}", s_subsec))
        feature_table(feats)

    # ════════════════════════════════════════
    # PRICING
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("خطط الاشتراك — سعر الإطلاق", s_section))
    divider()

    banner("🚀 سعر إطلاق خاص — بدون رسوم تنفيذ — بدون رسوم تدريب — 14 يوم مجاناً", GOLD, 11)
    story.append(Spacer(1, 10))

    story.append(P("جميع الأسعار بالجنيه المصري — لكل موظف في الشهر — شاملة كل الخدمات بدون رسوم مخفية.", s_small))
    story.append(Spacer(1, 8))

    ph = [tp("", color=WHITE), tp("Starter أساسية", color=WHITE, size=10), tp("Professional أعمال", color=WHITE, size=10), tp("Enterprise مؤسسات", color=WHITE, size=10)]

    pr = [
        [tp("السعر/موظف/شهر", size=10), tp("59 ج.م", color=SUCCESS, size=12), tp("75 ج.م", color=PRIMARY_DARK, size=12), tp("95 ج.م", color=PURPLE, size=12)],
        [tp("الحد الأدنى"), tp("10 موظفين"), tp("10 موظفين"), tp("10 موظفين")],
        [tp("الحد الأقصى"), tp("50 موظف"), tp("200 موظف"), tp("غير محدود")],
        [tp(""), tp(""), tp(""), tp("")],
        [tp("مثال: 15 موظف/شهر", size=10), tp("885 ج.م", color=SUCCESS), tp("1,125 ج.م", color=PRIMARY_DARK), tp("1,425 ج.م", color=PURPLE)],
        [tp("مثال: 15 موظف/سنة", size=10), tp("10,620 ج.م", color=SUCCESS, size=10), tp("13,500 ج.م", color=PRIMARY_DARK, size=10), tp("17,100 ج.م", color=PURPLE, size=10)],
        [tp(""), tp(""), tp(""), tp("")],
        [tp("مثال: 50 موظف/شهر", size=10), tp("2,950 ج.م"), tp("3,750 ج.م"), tp("4,750 ج.م")],
        [tp("مثال: 50 موظف/سنة", size=10), tp("35,400 ج.م"), tp("45,000 ج.م"), tp("57,000 ج.م")],
        [tp(""), tp(""), tp(""), tp("")],
        [tp("رسوم التنفيذ"), tp("مجاناً ✅", color=SUCCESS), tp("مجاناً ✅", color=SUCCESS), tp("مجاناً ✅", color=SUCCESS)],
        [tp("رسوم التدريب"), tp("مجاناً ✅", color=SUCCESS), tp("مجاناً ✅", color=SUCCESS), tp("مجاناً ✅", color=SUCCESS)],
        [tp("فترة تجريبية"), tp("14 يوم مجاناً", color=SUCCESS), tp("14 يوم مجاناً", color=SUCCESS), tp("14 يوم مجاناً", color=SUCCESS)],
        [tp(""), tp(""), tp(""), tp("")],
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
        [tp("الدعم"), tp("إيميل"), tp("واتساب + إيميل"), tp("واتساب + اتصال")],
    ]

    pdata = [ph] + pr
    cw = pw/4
    ptable = Table(pdata, colWidths=[cw]*4)
    pcmds = [
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,-1),fn),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#DEE2E6")),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]
    for i in range(1, len(pdata)):
        pcmds.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor(LIGHT_BG if i%2==0 else WHITE)))
    ptable.setStyle(TableStyle(pcmds))
    story.append(ptable)

    # ════════════════════════════════════════
    # ADD-ONS
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("الوحدات الإضافية (Add-ons)", s_section))
    divider()
    story.append(P("تُضاف لأي باقة بتكلفة شهرية لكل موظف:", s_small))
    story.append(Spacer(1, 8))

    ah = [tp("الوحدة", color=WHITE, size=10), tp("السعر/موظف/شهر", color=WHITE, size=10), tp("أبرز المميزات", color=WHITE, size=10)]
    ar_data = [
        [tp("💰 الرواتب"), tp("+15 ج.م", color=SUCCESS), tp("حساب آلي + مسيرات + تصدير بنكي + تأمينات + ضرائب")],
        [tp("👤 التوظيف"), tp("+12 ج.م", color=SUCCESS), tp("نشر وظائف + CVs + مقابلات + تحويل لموظف")],
        [tp("📊 تقييم الأداء"), tp("+12 ج.م", color=SUCCESS), tp("KPIs + تقييم 360° + مكافآت + خطط تطوير")],
        [tp("📚 التدريب"), tp("+8 ج.م", color=SUCCESS), tp("خطط + شهادات + حضور + تقييم أثر")],
        [tp("💻 الأصول والعهد"), tp("+8 ج.م", color=SUCCESS), tp("تسليم/استلام + إخلاء طرف + صيانة")],
        [tp("🔌 الربط البرمجي"), tp("حسب الطلب"), tp("REST API + Webhooks + ERP + أجهزة بصمة")],
    ]
    adata = [ah] + ar_data
    atable = Table(adata, colWidths=[pw*0.25, pw*0.2, pw*0.55])
    acmds = [
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#DEE2E6")),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]
    for i in range(1, len(adata)):
        acmds.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor(LIGHT_BG if i%2==0 else WHITE)))
    atable.setStyle(TableStyle(acmds))
    story.append(atable)

    story.append(Spacer(1, 12))
    story.append(P("مثال: شركة 15 موظف + باقة Professional + الرواتب:", s_subsec))
    story.append(Spacer(1, 6))

    ex_data = [
        [tp("البند", color=WHITE), tp("الحساب", color=WHITE), tp("المبلغ/شهر", color=WHITE), tp("المبلغ/سنة", color=WHITE)],
        [tp("الباقة"), tp("15 × 75"), tp("1,125 ج.م"), tp("13,500 ج.م")],
        [tp("+ الرواتب"), tp("15 × 15"), tp("225 ج.م"), tp("2,700 ج.م")],
        [tp("الإجمالي", size=11), tp(""), tp("1,350 ج.م", color=PRIMARY_DARK, size=11), tp("16,200 ج.م", color=PRIMARY_DARK, size=11)],
        [tp("رسوم التنفيذ"), tp(""), tp(""), tp("مجاناً ✅", color=SUCCESS, size=11)],
        [tp("رسوم التدريب"), tp(""), tp(""), tp("مجاناً ✅", color=SUCCESS, size=11)],
    ]
    et = Table(ex_data, colWidths=[pw*0.25]*4)
    et.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#DEE2E6")),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('BACKGROUND',(0,3),(-1,3),colors.HexColor(LIGHT_BG)),('BACKGROUND',(0,4),(-1,5),colors.HexColor(LIGHT_BG)),
    ]))
    story.append(et)

    # ════════════════════════════════════════
    # ONBOARDING + SLA
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("الإعداد والتشغيل + الدعم الفني", s_section))
    divider()

    onb = [
        ("الاستكشاف والإعداد", "تحليل سياسات الشركة وتهيئة النظام بالكامل"),
        ("ترحيل البيانات", "قوالب Excel جاهزة لإدخال بيانات الموظفين"),
        ("التدريب (مجاناً)", "جلسات حية ومسجلة للمسؤولين والمديرين — بدون رسوم"),
        ("الإطلاق", "تشغيل النظام ومتابعة أول أسبوع عمل"),
        ("المتابعة", "جلسات متابعة خلال أول 3 أشهر"),
    ]

    for title, desc in onb:
        od = [[
            Paragraph(escape(ar(title)), ParagraphStyle(f"o{title}", fontName=fn, fontSize=11, leading=16, alignment=TA_RIGHT, textColor=colors.HexColor(PRIMARY_DARK))),
            Paragraph(escape(ar(desc)), ParagraphStyle(f"od{title}", fontName=fn, fontSize=10, leading=15, alignment=TA_RIGHT, textColor=colors.HexColor(GRAY))),
        ]]
        ot = Table(od, colWidths=[pw*0.35, pw*0.65])
        ot.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor("#E2E8F0")),('BACKGROUND',(0,0),(0,-1),colors.HexColor(LIGHT_BG))]))
        story.append(ot)

    story.append(Spacer(1, 6))
    story.append(P("الجدول الزمني: أسبوع إلى أسبوعين حسب حجم الشركة.", s_small))

    story.append(Spacer(1, 12))
    story.append(P("اتفاقية مستوى الخدمة (SLA)", s_subsec))
    story.append(Spacer(1, 6))

    slah = [tp("المستوى", color=WHITE), tp("الوصف", color=WHITE), tp("الاستجابة", color=WHITE), tp("الحل", color=WHITE)]
    slar = [
        [tp("عاجل 🔴"), tp("فشل كامل"), tp("ساعة"), tp("4 ساعات")],
        [tp("مرتفع 🟠"), tp("تأثير كبير"), tp("4 ساعات"), tp("يوم عمل")],
        [tp("عادي 🟡"), tp("تأثير متوسط"), tp("يوم عمل"), tp("3 أيام")],
        [tp("منخفض 🟢"), tp("استفسار"), tp("يوم عمل"), tp("5 أيام")],
    ]
    slad = [slah] + slar
    slat = Table(slad, colWidths=[pw*0.18, pw*0.32, pw*0.25, pw*0.25])
    slat.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(PRIMARY_DARK)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#DEE2E6")),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('BACKGROUND',(0,1),(-1,1),colors.HexColor(LIGHT_BG)),('BACKGROUND',(0,3),(-1,3),colors.HexColor(LIGHT_BG)),
    ]))
    story.append(slat)
    story.append(Spacer(1,6))
    story.append(P("ساعات الدعم: الأحد — الخميس، 9 ص — 6 م (توقيت القاهرة)", s_small))

    # ════════════════════════════════════════
    # TERMS
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("الشروط والأحكام", s_section))
    divider()

    terms = [
        "صلاحية العرض: 14 يوماً من تاريخ الإرسال.",
        "الأسعار بالجنيه المصري شاملة كل الخدمات المذكورة.",
        "لا توجد رسوم تنفيذ أو تدريب إضافية (عرض إطلاق).",
        "يسري الاشتراك لمدة سنة ميلادية من تاريخ التفعيل.",
        "زيادة عدد الموظفين تُحسب تناسبياً للمدة المتبقية.",
        "لا يمكن تخفيض عدد الموظفين خلال فترة الاشتراك.",
        "التجديد بنفس السعر ما لم يُخطر الطرف الآخر قبل 30 يوم.",
        "البيانات ملك العميل ويمكن تصديرها في أي وقت.",
        "التحديثات والتطويرات مجانية طوال فترة الاشتراك.",
        "الدعم الفني متاح حسب مستوى الباقة.",
        "يحق للعميل تجربة النظام 14 يوم مجاناً قبل أي التزام مالي.",
    ]
    for i, t in enumerate(terms):
        story.append(P(f"  {i+1}. {t}", s_body))

    story.append(Spacer(1, 12))
    story.append(P("طرق الدفع المتاحة", s_subsec))
    for pm in ["التحويل البنكي (التفاصيل عند الطلب)", "فودافون كاش", "إنستا باي", "الدفع النقدي"]:
        story.append(P(f"  • {pm}", s_body))

    # ════════════════════════════════════════
    # TARGET
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(P("لمين النظام مناسب؟", s_section))
    divider()

    targets = [
        ("🏗️ شركات المقاولات", "تتبع العمال في المواقع + حضور GPS + جداول مرنة"),
        ("🚚 شركات التوزيع والنقل", "تتبع السائقين + زيارات ميدانية + خريطة حية"),
        ("🔧 شركات الصيانة", "تتبع الفنيين + جداول مرنة + تقارير ميدانية"),
        ("🏢 الشركات المتوسطة", "إدارة شاملة + تقارير + workflow + إجازات"),
        ("🏬 سلاسل المحلات", "Geofencing + حضور متعدد الفروع"),
        ("🏥 المستشفيات", "ورديات متقسمة + حضور دقيق"),
        ("📱 أي شركة بموظفين ميدانيين", "Live Map + Stealth Tracking + GPS"),
    ]
    for icon_title, desc in targets:
        td = [[
            Paragraph(escape(ar(icon_title)), ParagraphStyle(f"tg{icon_title}", fontName=fn, fontSize=11, leading=16, alignment=TA_RIGHT, textColor=colors.HexColor(PRIMARY_DARK))),
            Paragraph(escape(ar(desc)), ParagraphStyle(f"td{icon_title}", fontName=fn, fontSize=10, leading=15, alignment=TA_RIGHT, textColor=colors.HexColor(GRAY))),
        ]]
        tt = Table(td, colWidths=[pw*0.35, pw*0.65])
        tt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor("#E2E8F0"))]))
        story.append(tt)

    # ════════════════════════════════════════
    # LAST PAGE
    # ════════════════════════════════════════
    story.append(PageBreak())
    story.append(Spacer(1, 3*cm))
    story.append(P(PRODUCT, s_cover))
    story.append(P(TAGLINE, s_cover_sub))
    story.append(Spacer(1, 1.5*cm))
    divider("40%", SUCCESS, 3)
    story.append(Spacer(1, 1*cm))
    story.append(P("نتطلع للعمل معكم", ParagraphStyle("last", fontName=fn, fontSize=16, leading=24, alignment=TA_CENTER, textColor=colors.HexColor(DARK))))
    story.append(Spacer(1, 1*cm))
    story.append(P(f"📞 هاتف/واتساب: {PHONE}", s_meta))
    story.append(P(f"📧 إيميل: {EMAIL}", s_meta))
    story.append(P(f"🏢 {COMPANY}", s_meta))
    story.append(Spacer(1, 1.5*cm))
    banner("🎁 ابدأ فترتك التجريبية المجانية — 14 يوم — كل المميزات — بدون التزام — تواصل معنا الآن", PRIMARY_DARK, 13)
    story.append(Spacer(1, 1.5*cm))
    story.append(P(f"© 2025 {COMPANY}. All rights reserved.", s_footer))
    story.append(P(f"{PRODUCT} — HR in Motion", s_footer))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    with open(out, "wb") as f:
        f.write(pdf)

    print(f"\n✅ تم إنشاء عرض السعر النهائي:")
    print(f"   📄 {os.path.relpath(out, BASE_DIR)}")
    print(f"   📦 {len(pdf)//1024} KB")
    print(f"\n   افتحه: http://127.0.0.1:8000/static/MotionHR_Sales_Proposal.pdf")

if __name__ == "__main__":
    generate()