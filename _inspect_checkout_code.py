import pathlib

p = pathlib.Path('attendance/api_mobile.py')
lines = p.read_text(encoding='utf-8').splitlines()

start = 1300
end = 1345

print(f"=== attendance/api_mobile.py (Lines {start} to {end}) ===")
for i in range(start-1, min(len(lines), end)):
    print(f"{i+1:4d}: {lines[i]}")

