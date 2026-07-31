from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

INCOME_SOURCES = [
    ("hospital", "בית חולים (שכיר)"),
    ("boston", "בוסטון קליניק (עצמאי)"),
    ("other", "אחר"),
]

EXPENSE_CATEGORIES = [
    ("insurance", "ביטוח אחריות מקצועית"),
    ("fuel", "דלק / רכב"),
    ("materials", "מזרקים / חומרים"),
    ("equipment", "ציוד / פחת"),
    ("other", "אחר"),
]


class Settings(db.Model):
    """שורה יחידה עם הפרמטרים של תכנון המס וההוצאות, ניתנת לעריכה מהאפליקציה."""

    id = db.Column(db.Integer, primary_key=True)
    credit_points = db.Column(db.Float, default=4.25)
    # אחוז מומלץ להפריש בצד מכל תשלום מבוסטון (מס + ביטוח לאומי ובריאות)
    reserve_pct = db.Column(db.Float, default=0.42)
    vat_rate = db.Column(db.Float, default=0.18)
    national_insurance_pct = db.Column(db.Float, default=0.1217)
    insurance_annual = db.Column(db.Float, default=7700.0)
    fuel_monthly = db.Column(db.Float, default=2000.0)
    fuel_recognized_pct = db.Column(db.Float, default=0.45)
    boston_withholding_pct = db.Column(db.Float, default=0.05)


class IncomeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    source = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200))
    gross = db.Column(db.Float, nullable=False, default=0.0)
    net = db.Column(db.Float, default=0.0)
    hours = db.Column(db.Float)
    bonus = db.Column(db.Float, default=0.0)
    tax_withheld = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def source_label(self):
        return dict(INCOME_SOURCES).get(self.source, self.source)


class ExpenseEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    recognized_pct = db.Column(db.Float, default=1.0)
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def recognized_amount(self):
        return self.amount * self.recognized_pct

    @property
    def category_label(self):
        return dict(EXPENSE_CATEGORIES).get(self.category, self.category)
