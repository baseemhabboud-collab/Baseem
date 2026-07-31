"""מילוי נתונים לדוגמה מהפרופיל הפיננסי הראשוני, כדי שהדשבורד לא יהיה ריק בהרצה הראשונה.
ניתן למחוק את הרשומות האלה בכל עת דרך מסכי ההכנסות/ההוצאות.
"""

from datetime import date

from app import create_app
from models import ExpenseEntry, IncomeEntry, db


def run():
    app = create_app()
    with app.app_context():
        if IncomeEntry.query.first() or ExpenseEntry.query.first():
            print("כבר קיימים נתונים — לא נוספו נתוני דוגמה.")
            return

        db.session.add(
            IncomeEntry(
                date=date(2026, 6, 30),
                source="hospital",
                description="משכורת בית חולים כרמל 6/2026",
                gross=15011,
                net=13225,
                tax_withheld=0,
            )
        )
        db.session.add(
            IncomeEntry(
                date=date(2026, 7, 31),
                source="boston",
                description="19 משמרות, 127 שעות ו-14 דק' — בוסטון קליניק 7/2026",
                gross=42369,
                hours=127.23,
                bonus=2500,
                tax_withheld=(42369 + 2500) * 0.05,
            )
        )
        db.session.add(
            ExpenseEntry(
                date=date(2026, 7, 31),
                category="insurance",
                amount=7700 / 12,
                recognized_pct=1.0,
                note="ביטוח אחריות מקצועית — פריסה חודשית מתוך 7,700 ₪ לשנה",
            )
        )
        db.session.add(
            ExpenseEntry(
                date=date(2026, 7, 31),
                category="fuel",
                amount=2000,
                recognized_pct=0.45,
                note="דלק/רכב — ללא יומן נסיעות",
            )
        )
        db.session.commit()
        print("נתוני דוגמה נוספו בהצלחה.")


if __name__ == "__main__":
    run()
