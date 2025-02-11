from flask import Blueprint, render_template, redirect, url_for, request, flash
from .models import User, Expense
from . import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")  # Fetch the email from the form
        password = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')

        # Ensure email is provided
        if not email:
            flash("Email is required.")
            return redirect(url_for("main.register"))

        # Ensure username and email are unique
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or Email already exists.")
            return redirect(url_for("main.register"))

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully!")
        return redirect(url_for("main.login"))
    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Login failed. Check username and password.")
    return render_template("login.html")


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


from datetime import datetime

@main.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        date = request.form.get("date")

        # Convert the date to a Python date object
        date = datetime.strptime(date, "%Y-%m-%d").date()

        expense = Expense(category=category, amount=float(amount), date=date, user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!")

    # Fetch all expenses for listing
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template("add_expense.html", expenses=expenses)

@main.route("/expense_summary")
@login_required
def expense_summary():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount

    category_labels = list(categories.keys())
    category_values = list(categories.values())

    return render_template("expense_summary.html", category_labels=category_labels, category_values=category_values)



@main.route('/dashboard')
@login_required
def dashboard():
    # Fetch user expenses
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Prepare data for charts
    category_data = {}
    date_data = {}

    for expense in expenses:
        # Category-wise aggregation
        category_data[expense.category] = category_data.get(expense.category, 0) + expense.amount

        # Date-wise aggregation
        date_str = expense.date.strftime("%Y-%m-%d")
        date_data[date_str] = date_data.get(date_str, 0) + expense.amount

    category_labels = list(category_data.keys())
    category_values = list(category_data.values())
    date_labels = list(date_data.keys())
    date_values = list(date_data.values())

    return render_template(
        'dashboard.html',
        category_labels=category_labels,
        category_values=category_values,
        date_labels=date_labels,
        date_values=date_values
    )
