import os, re

backend_dir = r'C:\MotionHR\Backend'
for root, dirs, files in os.walk(backend_dir):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if 'national_id' in content and ('phone' in content or 'activate' in content):
                        print(f'📄 ملف كود: {os.path.relpath(path, backend_dir)}')
                        for line in content.split('\n'):
                            if 'def ' in line and ('activate' in line.lower() or 'employee' in line.lower()):
                                print(f'   - {line.strip()}')
            except Exception:
                pass
