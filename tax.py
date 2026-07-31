"""לוגיקת חישוב: סיכומי הכנסה/הוצאה חודשיים ורזרבת מס מומלצת.

כל האחוזים מגיעים מטבלת ה-Settings וניתנים לעריכה במסך ההגדרות.
החישובים כאן הם הערכה לתכנון בלבד ואינם ייעוץ מס מחייב.
"""

from sqlalchemy import extract

from models import ExpenseEntry, IncomeEntry, Settings, db

SAVINGS_TIPS = [
    "אין עדיין הפרשה פנסיונית כעצמאי — לא קרן השתלמות ולא פנסיה. "
    "זהו פוטנציאל החיסכון הגדול ביותר כרגע: הפקדה לקרן השתלמות מוכרת כהוצאה "
    "והרווחים פטורים ממס, והפקדה לפנסיה מזכה בניכוי/זיכוי מס משמעותי.",
    "ניתן להגיש בקשה להחזר מס רטרואקטיבי עד 6 שנים אחורה.",
    "פחת על ציוד יקר (מכשירים/לייזר) ניתן לפרוס על פני מספר שנים.",
    "חובה לבצע תיאום מס בין המקורות ולהגיש דוח שנתי (טופס 1301).",
]


def get_settings():
    settings = Settings.query.first()
    if settings is None:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return settings


def _income_for_month(year, month):
    return IncomeEntry.query.filter(
        extract("year", IncomeEntry.date) == year,
        extract("month", IncomeEntry.date) == month,
    ).all()


def _expenses_for_month(year, month):
    return ExpenseEntry.query.filter(
        extract("year", ExpenseEntry.date) == year,
        extract("month", ExpenseEntry.date) == month,
    ).all()


def month_income_summary(year, month):
    settings = get_settings()
    entries = _income_for_month(year, month)

    hospital = [e for e in entries if e.source == "hospital"]
    boston = [e for e in entries if e.source == "boston"]
    other = [e for e in entries if e.source == "other"]

    hospital_gross = sum(e.gross for e in hospital)
    hospital_net = sum(e.net or 0 for e in hospital)

    boston_gross = sum(e.gross for e in boston) + sum(e.bonus or 0 for e in boston)
    boston_withheld = sum(e.tax_withheld or 0 for e in boston)
    boston_net_of_vat = boston_gross / (1 + settings.vat_rate)
    boston_vat_component = boston_gross - boston_net_of_vat

    other_gross = sum(e.gross for e in other)

    reserve_needed = boston_net_of_vat * settings.reserve_pct
    additional_reserve = max(reserve_needed - boston_withheld, 0)

    return {
        "entries": entries,
        "hospital_gross": hospital_gross,
        "hospital_net": hospital_net,
        "boston_gross": boston_gross,
        "boston_net_of_vat": boston_net_of_vat,
        "boston_vat_component": boston_vat_component,
        "boston_withheld": boston_withheld,
        "other_gross": other_gross,
        "total_gross": hospital_gross + boston_gross + other_gross,
        "reserve_needed": reserve_needed,
        "additional_reserve": additional_reserve,
    }


def month_expense_summary(year, month):
    entries = _expenses_for_month(year, month)
    total = sum(e.amount for e in entries)
    recognized = sum(e.recognized_amount for e in entries)
    by_category = {}
    for e in entries:
        by_category.setdefault(e.category_label, {"total": 0.0, "recognized": 0.0})
        by_category[e.category_label]["total"] += e.amount
        by_category[e.category_label]["recognized"] += e.recognized_amount

    return {
        "entries": entries,
        "total": total,
        "recognized": recognized,
        "by_category": by_category,
    }


def year_to_date_summary(year, up_to_month):
    total_gross = 0.0
    total_reserve_needed = 0.0
    total_expenses_recognized = 0.0
    for m in range(1, up_to_month + 1):
        inc = month_income_summary(year, m)
        exp = month_expense_summary(year, m)
        total_gross += inc["total_gross"]
        total_reserve_needed += inc["reserve_needed"]
        total_expenses_recognized += exp["recognized"]
    return {
        "total_gross": total_gross,
        "total_reserve_needed": total_reserve_needed,
        "total_expenses_recognized": total_expenses_recognized,
    }
