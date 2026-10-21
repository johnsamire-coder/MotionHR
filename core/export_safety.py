"""
تأمين الملفات اللي بتتصدّر (Excel و PDF) من النصوص اللي الموظفين بيكتبوها.
"""
from xml.sax.saxutils import escape

_FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def safe_cell_value(value):
    """نص بيبدأ بـ = أو + أو - أو @ ممكن Excel يشغّله كمعادلة، فبنخليه نص عادي.
    الأرقام (حتى لو مكتوبة كنص زي "-5") بتفضل زي ما هي."""
    if isinstance(value, str) and value.startswith(_FORMULA_START):
        try:
            float(value)
            return value
        except ValueError:
            return "'" + value
    return value


def pdf_text(value):
    """علامات زي & و < بتبوّظ فقرات الـ PDF، فبتتحول لنص عادي"""
    return escape('' if value is None else str(value))
