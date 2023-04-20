import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from dateutil.relativedelta import relativedelta

from helpers import login_required, usd


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Function for connecting to SQLite DB
def get_db_connection():
    conn = sqlite3.connect('expense_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")
        user_id = session.get("user_id")
        with get_db_connection() as conn:
            data = conn.execute("SELECT expenses.name, expenses.description, expenses.amount, expenses_category.category, expenses.date FROM expenses INNER JOIN expenses_category ON expenses.category = expenses_category.id WHERE user_id = ? AND expenses.date >= ? AND expenses.date <= ? ORDER BY date DESC", (user_id, date_from, date_to)).fetchall()
        
        dict = {}
        for record in data:
            if record["category"] not in dict:
                dict[record["category"]] = float(record["amount"])
            else:
                dict[record["category"]] += float(record["amount"])

        chart = []
        chart.append(["Category", "Amount"])
        for key, value in dict.items():
            chart.append([key, value])

        display = True
        if len(chart) == 1:
            display = False

        return render_template("index.html", data=data, chart=chart, display=display)
    else:
        user_id = session.get("user_id")
        with get_db_connection() as conn:
            data = conn.execute("SELECT expenses.name, expenses.description, expenses.amount, expenses_category.category, expenses.date FROM expenses INNER JOIN expenses_category ON expenses.category = expenses_category.id WHERE user_id = ? AND expenses.date >= ? AND expenses.date <= ? ORDER BY date DESC", (user_id, date.today().replace(day=1), (date.today() + relativedelta(day=31)))).fetchall()
        
        dict = {}
        for record in data:
            if record["category"] not in dict:
                dict[record["category"]] = float(record["amount"])
            else:
                dict[record["category"]] += float(record["amount"])

        chart = []
        chart.append(["Category", "Amount"])
        for key, value in dict.items():
            chart.append([key, value])     

        display = True
        if len(chart) == 1:
            display = False   
        
        return render_template("index.html", data=data, chart=chart, display=display)


@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        amount = request.form.get("amount")
        date = request.form.get("date")
        category = request.form.get("category")
        user_id = session.get("user_id")

        if not name or not amount or not date or not category:
            flash("Please fill out all fields")
            return redirect("/add_expense")
        
        with get_db_connection() as conn:
            data = (name, description, amount, date, category, user_id)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expenses (name, description, amount, date, category, user_id) VALUES (?, ?, ?, ?, ?, ?)", data)
            conn.commit()

        flash(f"Expense ({name}) added!")
        return redirect("/add_expense")

    else:
        with get_db_connection() as conn:
            categories = conn.execute("SELECT * FROM expenses_category").fetchall()
        return render_template("add_expense.html", categories=categories)


@app.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        amount = request.form.get("amount")
        date = request.form.get("date")
        user_id = session.get("user_id")

        if not name or not amount or not date:
                flash("Please fill out all fields")
                return redirect("/add_income")
        
        with get_db_connection() as conn:
            data = (name, description, amount, date, user_id)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO income (name, description, amount, date, user_id) VALUES (?, ?, ?, ?, ?)", data)
            conn.commit()

        flash(f"Income ({name}) added!")
        return redirect("/add_income")

    else:
        return render_template("add_income.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # Requesting username and passwords from HTML form
        username = request.form.get("username")
        password = request.form.get("password")

        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
        
        # Check if username exists in db and check password
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        # Remember user id in session
        session["user_id"] = rows[0]["id"]

        flash("Succesfully logged in")
        return redirect("/")
    
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    # Forget user ID
    session.clear()

    #R edirect to login form
    return redirect("/login")    

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Requesting username and passwords from HTML form
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Fetching all usernames from db to check if available
        with get_db_connection() as conn:
            users = conn.execute("SELECT username FROM users").fetchall()
        for user in users:
            if user["username"] == username:
                flash("This username is not available")
                return redirect("/register")
            
        # Checking if user typed all data
        if not username:
            flash("Please type in your username.")
            return redirect("/register")
        if not password:
            flash("Please type in your password.")
            return redirect("/register")
        if not confirm_password:
            flash("Please confirm your password")
            return redirect("/register")
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/register")
        
        # Adding new user to db
        with get_db_connection() as conn:
            user_data = (username, generate_password_hash(password))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, hash) VALUES(?, ?)", user_data)
            conn.commit()

        with get_db_connection() as conn:
            user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchall()
            session["user_id"] = user_id[0]["id"]

        flash("Registered succesfully!")
        return redirect("/")
    else:
        return render_template("register.html")
    

