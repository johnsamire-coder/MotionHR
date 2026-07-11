# -*- coding: utf-8 -*-
"""
Patch 49a-safe
Exports only the bug-relevant templates/views into a UTF-8 file
without printing large Unicode content to the Windows console.
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "_patches", "patch_49a_bug_context_output.txt")


def read_text(path):
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return None

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1256",
        "cp1252",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin-1",
    ]

    for enc in encodings:
        try:
            with open(full_path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue

    try:
        with open(full_path, "rb") as f:
            data = f.read()
        return data.decode("latin-1", errors="replace")
    except Exception as e:
        return f"[READ FAILED] {e}"


def write_line(f, text=""):
    f.write(text + "\n")


def write_header(f, title):
    write_line(f, "\n" + "=" * 100)
    write_line(f, title)
    write_line(f, "=" * 100)


def write_subheader(f, title):
    write_line(f, "\n" + "-" * 100)
    write_line(f, title)
    write_line(f, "-" * 100)


def write_file_full(f, rel_path):
    content = read_text(rel_path)
    write_subheader(f, f"FILE: {rel_path}")
    if content is None:
        write_line(f, "[MISSING]")
        return

    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        write_line(f, f"{i:04d}: {line}")


def list_top_level_defs(rel_path):
    content = read_text(rel_path)
    if content is None:
        return []

    results = []
    for i, line in enumerate(content.splitlines(), 1):
        if re.match(r"^def\s+\w+\s*\(", line):
            results.append((i, "def", line.strip()))
        elif re.match(r"^class\s+\w+\s*[\(:]", line):
            results.append((i, "class", line.strip()))
    return results


def extract_block(rel_path, block_name):
    content = read_text(rel_path)
    if content is None:
        return None

    lines = content.splitlines()
    start = None
    start_idx = None

    pattern_def = re.compile(rf"^def\s+{re.escape(block_name)}\s*\(")
    pattern_class = re.compile(rf"^class\s+{re.escape(block_name)}\s*[\(:]")

    for idx, line in enumerate(lines):
        if pattern_def.match(line) or pattern_class.match(line):
            start_idx = idx
            break

    if start_idx is None:
        return None

    # include decorators immediately above the function
    start = start_idx
    while start > 0 and lines[start - 1].lstrip().startswith("@"):
        start -= 1

    end = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        line = lines[idx]
        if re.match(r"^def\s+\w+\s*\(", line) or re.match(r"^class\s+\w+\s*[\(:]", line):
            end = idx
            break

    block_lines = []
    for i in range(start, end):
        block_lines.append(f"{i+1:04d}: {lines[i]}")
    return "\n".join(block_lines)


def write_defs_index(f, rel_path):
    write_subheader(f, f"DEFS INDEX: {rel_path}")
    defs = list_top_level_defs(rel_path)
    if not defs:
        write_line(f, "[NO TOP LEVEL DEFS/CLASSES FOUND OR FILE MISSING]")
        return
    for line_no, kind, decl in defs:
        write_line(f, f"{line_no:04d} | {kind.upper():5s} | {decl}")


def write_named_blocks(f, rel_path, names):
    write_defs_index(f, rel_path)
    for name in names:
        write_subheader(f, f"BLOCK: {rel_path} :: {name}")
        block = extract_block(rel_path, name)
        if block is None:
            write_line(f, f"[NOT FOUND] {name}")
        else:
            write_line(f, block)


def write_keyword_hits(f, rel_path, keywords, context=8):
    content = read_text(rel_path)
    write_subheader(f, f"KEYWORD HITS: {rel_path}")
    if content is None:
        write_line(f, "[MISSING]")
        return

    lines = content.splitlines()
    hits = []
    lowered_keywords = [k.lower() for k in keywords]

    for idx, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in lowered_keywords):
            hits.append(idx)

    if not hits:
        write_line(f, "[NO HITS]")
        return

    seen_ranges = []
    for idx in hits:
        start = max(0, idx - context)
        end = min(len(lines), idx + context + 1)

        merged = False
        for i, (s, e) in enumerate(seen_ranges):
            if not (end < s or start > e):
                seen_ranges[i] = (min(s, start), max(e, end))
                merged = True
                break
        if not merged:
            seen_ranges.append((start, end))

    seen_ranges.sort()

    for start, end in seen_ranges:
        write_line(f, "\n--- snippet lines {start+1}-{end} ---")
        for i in range(start, end):
            write_line(f, f"{i+1:04d}: {lines[i]}")


def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        write_header(f, "PATCH 49A SAFE BUG CONTEXT")

        write_line(f, "Project root: " + BASE_DIR)
        write_line(f, "Output file: " + OUTPUT_FILE)

        # 1) Dashboard/base templates for sidebar scroll
        write_header(f, "1) SIDEBAR / BASE TEMPLATES")
        write_file_full(f, "templates/base/base.html")
        write_file_full(f, "templates/base/dashboard_base.html")

        # 2) Attendance list for NoReverseMatch override
        write_header(f, "2) ATTENDANCE LIST / OVERRIDE BUG")
        write_file_full(f, "templates/attendance/list.html")
        write_named_blocks(
            f,
            "attendance/views.py",
            [
                "attendance_list",
                "attendance_override",
            ],
        )

        # 3) Live map / visit form map CSS & JS
        write_header(f, "3) LIVE MAP / VISIT FORM MAP")
        write_file_full(f, "templates/attendance/live_map.html")
        write_file_full(f, "templates/attendance/visit_form.html")
        write_file_full(f, "templates/attendance/visits.html")
        write_named_blocks(
            f,
            "attendance/views.py",
            [
                "live_map",
                "api_live_locations",
                "visits_list",
                "field_visit_add_page",
            ],
        )

        # 4) Stealth tracking policy issue
        write_header(f, "4) STEALTH TRACKING BUG")
        write_file_full(f, "templates/attendance/stealth_manage.html")
        write_file_full(f, "templates/companies/policies.html")
        write_named_blocks(
            f,
            "attendance/views.py",
            [
                "stealth_tracking_manage",
                "stealth_tracking_alerts",
                "api_stealth_location",
            ],
        )
        write_named_blocks(
            f,
            "companies/views.py",
            [
                "company_policies",
                "policies_view",
                "policies_manage",
                "settings_view",
                "company_settings",
            ],
        )
        write_keyword_hits(
            f,
            "companies/models.py",
            [
                "class CompanyPolicy",
                "stealth_tracking_enabled",
                "stealth_tracking_alert_after_minutes",
                "stealth_tracking_requires_charter_clause",
            ],
            context=10,
        )

        # 5) Excel / PDF export bugs
        write_header(f, "5) EMPLOYEES EXPORT / REPORTS EXPORT")
        write_file_full(f, "employees/forms.py")
        write_file_full(f, "templates/employees/list.html")
        write_named_blocks(
            f,
            "employees/views.py",
            [
                "employee_list",
                "export_employees_excel",
                "export_employees_pdf",
                "employee_create",
                "employee_add",
                "employee_update",
                "employee_form",
            ],
        )
        write_file_full(f, "reports/views.py")
        write_file_full(f, "reports/utils.py")
        write_file_full(f, "templates/reports/attendance_report.html")
        write_file_full(f, "templates/reports/late_report.html")
        write_file_full(f, "templates/reports/leave_report.html")
        write_file_full(f, "templates/reports/employees_report.html")

        # 6) schedule / assignment for next UX step
        write_header(f, "6) SCHEDULE / ASSIGNMENT (NEXT STEP)")
        write_file_full(f, "templates/attendance/schedule_week.html")
        write_file_full(f, "templates/attendance/assignment_form.html")
        write_named_blocks(
            f,
            "attendance/views.py",
            [
                "schedule_week_view",
                "assignment_add",
            ],
        )

        # 7) departments / charter for later
        write_header(f, "7) DEPARTMENTS / CHARTER (LATER)")
        write_file_full(f, "templates/companies/departments_list.html")
        write_file_full(f, "templates/companies/charter_manage.html")
        write_named_blocks(
            f,
            "companies/views.py",
            [
                "departments_list",
                "department_list",
                "charter_manage",
                "charter_view",
            ],
        )

    print("DONE")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()