"""
MotionHR - Username Generator
────────────────────────────────
Owner:    admin_{first_name}   →   admin_ahmed  →  admin_ahmed1  → admin_ahmed2 ...
Employee: {first}{last2}{nid4} →   ahmedmo2345  →  ahmedmo12345  (5) → ahmedmo012345 (6) ...
"""

from slugify import slugify

# ══════════════════════════════════════════════════════════
# Dictionary للأسماء العربية الشائعة (الأدق)
# ══════════════════════════════════════════════════════════
ARABIC_NAMES_MAP = {
    # ذكور
    'أحمد': 'ahmed', 'احمد': 'ahmed',
    'محمد': 'mohamed', 'محمّد': 'mohamed',
    'علي': 'ali', 'علىّ': 'ali',
    'حسن': 'hassan', 'حسين': 'hussein',
    'إبراهيم': 'ibrahim', 'ابراهيم': 'ibrahim',
    'يوسف': 'youssef', 'يوسُف': 'youssef',
    'عمر': 'omar', 'عُمر': 'omar',
    'خالد': 'khaled', 'كريم': 'karim',
    'طارق': 'tarek', 'سامي': 'sami',
    'سامر': 'samer', 'أسامة': 'osama', 'اسامة': 'osama',
    'مصطفى': 'mostafa', 'مُصطفى': 'mostafa',
    'محمود': 'mahmoud', 'مروان': 'marwan',
    'عبدالله': 'abdullah', 'عبد الله': 'abdullah',
    'عبدالرحمن': 'abdelrahman', 'عبد الرحمن': 'abdelrahman',
    'عبدالعزيز': 'abdelaziz', 'عبد العزيز': 'abdelaziz',
    'عبدالرحيم': 'abdelrahim', 'عبد الرحيم': 'abdelrahim',
    'عبدالكريم': 'abdelkarim', 'عبد الكريم': 'abdelkarim',
    'عبدالحميد': 'abdelhamid', 'عبد الحميد': 'abdelhamid',
    'عبدالمنعم': 'abdelmenem', 'عبد المنعم': 'abdelmenem',
    'عبدالسلام': 'abdelsalam', 'عبد السلام': 'abdelsalam',
    'عبدالفتاح': 'abdelfattah', 'عبد الفتاح': 'abdelfattah',
    'عبدالغني': 'abdelghany', 'عبد الغني': 'abdelghany',
    'عبدالمجيد': 'abdelmagid', 'عبد المجيد': 'abdelmagid',
    'عبدالوهاب': 'abdelwahab', 'عبد الوهاب': 'abdelwahab',
    'زياد': 'ziad', 'رامي': 'ramy',
    'شريف': 'sherif', 'وائل': 'wael',
    'هاني': 'hany', 'هشام': 'hisham',
    'ياسر': 'yasser', 'يحيى': 'yahya',
    'إسلام': 'islam', 'اسلام': 'islam',
    'باسم': 'bassem', 'بلال': 'belal',
    'حازم': 'hazem', 'حاتم': 'hatem',
    'صلاح': 'salah', 'صالح': 'saleh',
    'ضياء': 'diaa', 'طه': 'taha',
    'عادل': 'adel', 'عاطف': 'atef',
    'عصام': 'essam', 'فادي': 'fady',
    'فارس': 'fares', 'فاروق': 'farouk',
    'فرج': 'farag', 'مازن': 'mazen',
    'ماجد': 'maged', 'مالك': 'malek',
    'ميلاد': 'milad', 'نبيل': 'nabil',
    'نادر': 'nader', 'نصر': 'nasr',
    'وليد': 'walid', 'يعقوب': 'yaacoub',
    'جون': 'john', 'سمير': 'samir',
    'جمال': 'gamal', 'رفعت': 'refaat',
    'حسنى': 'hosny', 'صابر': 'saber',
    'صبري': 'sabry', 'عبده': 'abdo',
    'كامل': 'kamel', 'مأمون': 'maamoun',
    'منير': 'moneer', 'مختار': 'mokhtar',

    # إناث
    'فاطمة': 'fatma', 'عائشة': 'aisha',
    'خديجة': 'khadija', 'زينب': 'zeinab',
    'مريم': 'mariam', 'سارة': 'sara',
    'ريم': 'reem', 'ليلى': 'laila',
    'ندى': 'nada', 'نور': 'nour',
    'هدى': 'hoda', 'ياسمين': 'yasmin',
    'دينا': 'dina', 'رنا': 'rana',
    'سلمى': 'salma', 'شيماء': 'shaimaa',
    'صفاء': 'safaa', 'عبير': 'abeer',
    'غادة': 'ghada', 'فرح': 'farah',
    'كريمة': 'karima', 'لبنى': 'lubna',
    'منى': 'mona', 'ميرنا': 'mirna',
    'نجلاء': 'naglaa', 'هاجر': 'hagar',
    'هبة': 'heba', 'هند': 'hend',
    'وفاء': 'wafaa', 'ولاء': 'walaa',
    'أميرة': 'amira', 'اميرة': 'amira',
    'إيمان': 'iman', 'ايمان': 'iman',
    'إسراء': 'israa', 'اسراء': 'israa',
    'إيناس': 'inas', 'اناس': 'inas',
    'أروى': 'arwa', 'اروى': 'arwa',
    'رانيا': 'rania', 'ريهام': 'reham',
    'داليا': 'dalia', 'دنيا': 'donya',
    'سميرة': 'samira', 'سعاد': 'souad',
    'صفية': 'safia', 'ضحى': 'doha',
    'عزيزة': 'aziza', 'فوزية': 'fawzia',
    'جيهان': 'gehan', 'كوثر': 'kawthar',
    'ماجدة': 'magda', 'ملك': 'malak',
    'نادية': 'nadia', 'ناهد': 'nahed',
    'نعمة': 'nema', 'وسام': 'wesam',

    # أسماء الشركات الشائعة
    'شركة': 'co', 'مؤسسة': 'est',
    'الأمل': 'alamal', 'الامل': 'alamal',
    'النور': 'alnour', 'المستقبل': 'almostakbal',
    'التقدم': 'altaqadom', 'النجاح': 'alnajah',
    'الرائد': 'alraed', 'الفارس': 'alfares',
}


def transliterate_arabic(text):
    """
    تحويل النص العربي لإنجليزي
    الأولوية:
      1. من الـ Dictionary (الأدق)
      2. python-slugify (fallback)
    """
    if not text:
        return ""

    text = text.strip()

    # 1) شوف لو الاسم كامل موجود في الـ dictionary
    if text in ARABIC_NAMES_MAP:
        return ARABIC_NAMES_MAP[text]

    # 2) شوف لو الاسم بيبدأ بأي مفتاح
    for arabic, english in ARABIC_NAMES_MAP.items():
        if text == arabic:
            return english

    # 3) fallback: python-slugify
    result = slugify(text, separator='', lowercase=True)

    # لو النتيجة فاضية (أحياناً بيحصل مع بعض الحروف)، جرب unidecode
    if not result:
        from text_unidecode import unidecode
        result = ''.join(c for c in unidecode(text) if c.isalnum()).lower()

    return result or 'user'


def _clean_username(username):
    """تنظيف الـ username: lowercase + alphanumeric فقط"""
    return ''.join(c for c in username.lower() if c.isalnum() or c == '_')


def generate_owner_username(first_name, User=None):
    """
    Owner: admin_{first_name}
    - admin_ahmed
    - admin_ahmed1
    - admin_ahmed2
    """
    if User is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()

    # نظّف الاسم الأول
    first_clean = transliterate_arabic(first_name.split()[0] if first_name else 'owner')
    first_clean = _clean_username(first_clean)[:15]

    base = f"admin_{first_clean}"
    username = base

    # لو موجود، زوّد رقم
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
        if counter > 999:
            # سيناريو مستحيل، بس نحتاط
            import random
            username = f"{base}_{random.randint(1000, 9999)}"
            break

    return username


def generate_employee_username(full_name, national_id, User=None):
    """
    Employee: {first}{last2}{last_4_of_nid}
    - ahmedmo2345
    - لو موجود: ahmedmo12345 (آخر 5)
    - لو موجود: ahmedmo012345 (آخر 6)
    """
    if User is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()

    # قسّم الاسم
    parts = full_name.strip().split()
    first_name = parts[0] if parts else 'user'
    last_name = parts[1] if len(parts) > 1 else ''

    # transliterate
    first_en = _clean_username(transliterate_arabic(first_name))
    last_en = _clean_username(transliterate_arabic(last_name)) if last_name else ''

    # لو مفيش اسم ثاني، خد أول حرفين من الأول أو ضيف "emp"
    if not last_en:
        last_2 = 'emp'
    else:
        last_2 = last_en[:2]

    # نظّف الرقم القومي
    nid_str = ''.join(c for c in str(national_id or '') if c.isdigit())

    if not nid_str:
        # لو مفيش رقم قومي، استخدم random 4 digits
        import random
        nid_str = str(random.randint(1000, 9999))

    # ابدأ بآخر 4
    for digits_count in range(4, min(len(nid_str), 15) + 1):
        suffix = nid_str[-digits_count:]
        username = f"{first_en}{last_2}{suffix}"
        username = _clean_username(username)[:30]

        if not User.objects.filter(username=username).exists():
            return username

    # fallback نهائي: زوّد counter
    counter = 1
    base = f"{first_en}{last_2}{nid_str}"[:25]
    while User.objects.filter(username=f"{base}{counter}").exists():
        counter += 1
        if counter > 999:
            import random
            return f"{base}_{random.randint(10000, 99999)}"

    return f"{base}{counter}"
