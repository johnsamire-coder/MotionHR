import pathlib

p = pathlib.Path('leaves/models.py')
lines = p.read_text(encoding='utf-8').splitlines()

start = max(0, 280)
end = min(len(lines), 340)

print(f"=== leaves/models.py (Lines {start} to {end}) ===")
for i in range(start, end):
    # طباعة رقم السطر مع تمثيل المسافات بنقاط عشان نشوف أي tab أو space غير منضبط
    line_repr = lines[i].replace(' ', '·').replace('\t', '→→→→')
    print(f"{i+1:4d}: {line_repr}")
