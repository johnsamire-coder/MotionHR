import pathlib
p = pathlib.Path('requirements.txt')
raw = p.read_bytes()
# شيل BOM لو موجود
if raw[:2] == b'\xff\xfe':
    raw = raw[2:]
elif raw[:3] == b'\xef\xbb\xbf':
    raw = raw[3:]
# جرب decode
for enc in ['utf-16-le', 'utf-8', 'cp1252', 'latin-1']:
    try:
        text = raw.decode(enc)
        # نظف
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '\x00' not in line:
                lines.append(line)
        if lines:
            clean = '\n'.join(lines) + '\n'
            p.write_text(clean, encoding='utf-8')
            print(f"Fixed! Encoding: {enc}, Lines: {len(lines)}")
            print("First 5 lines:")
            for l in lines[:5]:
                print(f"  {l}")
            break
    except:
        continue
else:
    print("FAILED to decode. Creating minimal requirements.txt")
    p.write_text("django>=5.0\ndjangorestframework>=3.15\ndjangorestframework-simplejwt>=5.3\ndjango-cors-headers>=4.3\npsycopg2-binary>=2.9\npillow>=10.0\npython-dateutil>=2.8\nrequests>=2.31\n", encoding='utf-8')
    print("Created minimal requirements.txt")
