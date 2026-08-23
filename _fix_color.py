import pathlib

p = pathlib.Path('leaves/models.py')
content = p.read_text(encoding='utf-8')

# تصليح سطر color ليكون بـ 4 مسافات
content = content.replace('\ncolor            = models.CharField(', '\n    color            = models.CharField(')
content = content.replace('\ncolor = models.CharField(', '\n    color = models.CharField(')

p.write_text(content, encoding='utf-8')
print("[OK] leaves/models.py indentation fixed.")
