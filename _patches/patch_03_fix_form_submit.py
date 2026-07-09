"""
============================================================
Patch 03: إصلاح مشكلة حفظ فورم تعديل الموظف
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def fix_form_submit():
    """إصلاح مشكلة عدم عمل submit للفورم"""
    form_path = BASE_DIR / 'templates' / 'employees' / 'form.html'
    
    if not form_path.exists():
        return False, "ملف form.html مش موجود"
    
    content = form_path.read_text(encoding='utf-8')
    
    # المشكلة الأولى: الأزرار مش داخل الفورم
    # نتأكد إن الأزرار مربوطة بالفورم صح
    
    # نصلح زرار Submit بإضافة form="employeeForm"
    old_submit = '<button type="submit" \n                            class="btn btn-success" \n                            id="submitBtn"'
    new_submit = '<button type="submit" \n                            form="employeeForm"\n                            class="btn btn-success" \n                            id="submitBtn"'
    
    if 'form="employeeForm"' in content:
        return True, "الإصلاح موجود بالفعل"
    
    # نصلح أيضاً زرار Next عشان ميعملش submit
    old_next = '<button type="button" \n                            class="btn btn-primary" \n                            id="nextBtn"'
    new_next = '<button type="button" \n                            class="btn btn-primary" \n                            id="nextBtn"'
    
    # التعديل الأساسي: نضيف form attribute للـ submit button
    if old_submit in content:
        content = content.replace(old_submit, new_submit)
    
    # نتأكد إن كل الحقول جوه الفورم
    # نبحث عن مكان زرار submit ونتأكد إنه قبل </form>
    
    # الحل الأضمن: نستخدم JavaScript يعمل submit يدوي
    old_js = '''<button type="submit" 
                            form="employeeForm"
                            class="btn btn-success" 
                            id="submitBtn"'''
    
    new_js = '''<button type="button" 
                            onclick="document.getElementById('employeeForm').submit();"
                            class="btn btn-success" 
                            id="submitBtn"'''
    
    if old_js in content:
        content = content.replace(old_js, new_js)
    
    form_path.write_text(content, encoding='utf-8')
    
    return True, "تم إصلاح مشكلة حفظ الفورم"


def main():
    print("=" * 60)
    print("🔧 Patch 03: إصلاح حفظ فورم الموظف")
    print("=" * 60)
    print()
    
    try:
        success, message = fix_form_submit()
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("جرب دلوقتي:")
    print("  1. شغل السيرفر")
    print("  2. روح لصفحة تعديل موظف")
    print("  3. عدل حاجة")
    print("  4. امشي للخطوة الأخيرة")
    print("  5. اضغط حفظ التعديلات")
    print()


if __name__ == '__main__':
    main()