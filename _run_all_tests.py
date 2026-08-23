import subprocess

tests = [
    ('_test_step1.py', 'Step 1: Excused Absence & Mandatory Reason'),
    ('_test_step2.py', 'Step 2: HR Attendance Adjustment'),
    ('_test_step3.py', 'Step 3: Absence Rules & Multiplier Deduction'),
    ('_test_step4.py', 'Step 4: Shift Checkout Flexibility & Grace'),
    ('_test_step5.py', 'Step 5: Pro-Rated Tenure Leave Policy'),
]

print("="*60)
print("RUNNING FULL CONSOLIDATED TEST SUITE (5/5 FEATURES)")
print("="*60)

all_passed = True
for test_file, label in tests:
    res = subprocess.run(['.\\venv\\Scripts\\python.exe', test_file], capture_output=True, text=True)
    passed = '>>> STEP' in res.stdout and res.returncode == 0
    status = '[PASS]' if passed else '[FAIL]'
    print(f"{status} {label}")
    if not passed:
        all_passed = False
        print(f"--- Output for {test_file} ---\n{res.stdout}\n{res.stderr}\n")

print("\n" + "="*60)
if all_passed:
    print("🎉 ALL 5 FEATURES ARE FULLY VERIFIED & WORKING 100%!")
else:
    print("⚠️ SOME TESTS FAILED. PLEASE REVIEW.")
print("="*60)
