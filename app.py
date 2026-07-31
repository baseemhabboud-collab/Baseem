import os
from datetime import date, datetime

from flask import Flask, redirect, render_template, request, url_for

import tax
from models import EXPENSE_CATEGORIES, INCOME_SOURCES, ExpenseEntry, IncomeEntry, Settings, db


def create_app():
    app = Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "finance.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        tax.get_settings()

    register_routes(app)
    return app


def _selected_period():
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month
    return year, month


def register_routes(app):
    @app.route("/")
    def dashboard():
        year, month = _selected_period()
        income = tax.month_income_summary(year, month)
        expenses = tax.month_expense_summary(year, month)
        ytd = tax.year_to_date_summary(year, month)

        prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
        next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

        return render_template(
            "dashboard.html",
            year=year,
            month=month,
            income=income,
            expenses=expenses,
            ytd=ytd,
            prev_month=prev_month,
            prev_year=prev_year,
            next_month=next_month,
            next_year=next_year,
            tips=tax.SAVINGS_TIPS,
        )

    @app.route("/income")
    def income_list():
        entries = IncomeEntry.query.order_by(IncomeEntry.date.desc()).all()
        return render_template("income_list.html", entries=entries)

    @app.route("/income/new", methods=["GET", "POST"])
    def income_new():
        if request.method == "POST":
            entry = IncomeEntry(
                date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
                source=request.form["source"],
                description=request.form.get("description", ""),
                gross=float(request.form.get("gross") or 0),
                net=float(request.form.get("net") or 0),
                hours=float(request.form["hours"]) if request.form.get("hours") else None,
                bonus=float(request.form.get("bonus") or 0),
                tax_withheld=float(request.form.get("tax_withheld") or 0),
            )
            db.session.add(entry)
            db.session.commit()
            return redirect(url_for("income_list"))
        return render_template("income_form.html", sources=INCOME_SOURCES, today=date.today())

    @app.route("/income/<int:entry_id>/delete", methods=["POST"])
    def income_delete(entry_id):
        entry = IncomeEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("income_list"))

    @app.route("/expenses")
    def expense_list():
        entries = ExpenseEntry.query.order_by(ExpenseEntry.date.desc()).all()
        return render_template("expense_list.html", entries=entries)

    @app.route("/expenses/new", methods=["GET", "POST"])
    def expense_new():
        if request.method == "POST":
            entry = ExpenseEntry(
                date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
                category=request.form["category"],
                amount=float(request.form.get("amount") or 0),
                recognized_pct=float(request.form.get("recognized_pct") or 100) / 100.0,
                note=request.form.get("note", ""),
            )
            db.session.add(entry)
            db.session.commit()
            return redirect(url_for("expense_list"))
        return render_template(
            "expense_form.html", categories=EXPENSE_CATEGORIES, today=date.today()
        )

    @app.route("/expenses/<int:entry_id>/delete", methods=["POST"])
    def expense_delete(entry_id):
        entry = ExpenseEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("expense_list"))

    @app.route("/settings", methods=["GET", "POST"])
    def settings_page():
        settings = tax.get_settings()
        if request.method == "POST":
            settings.credit_points = float(request.form["credit_points"])
            settings.reserve_pct = float(request.form["reserve_pct"]) / 100.0
            settings.vat_rate = float(request.form["vat_rate"]) / 100.0
            settings.national_insurance_pct = float(request.form["national_insurance_pct"]) / 100.0
            settings.insurance_annual = float(request.form["insurance_annual"])
            settings.fuel_monthly = float(request.form["fuel_monthly"])
            settings.fuel_recognized_pct = float(request.form["fuel_recognized_pct"]) / 100.0
            settings.boston_withholding_pct = float(request.form["boston_withholding_pct"]) / 100.0
            db.session.commit()
            return redirect(url_for("settings_page"))
        return render_template("settings.html", settings=settings)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
