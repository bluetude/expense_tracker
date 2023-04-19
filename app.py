import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, usd

# Configure application
app = Flask(__name__)

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


@app.route('/')
@login_required
def index():
    return redirect('/register')

@app.route('/login')
def login():
    return redirect('/register')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Requesting username and passwords from HTML form
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Fetching all usernames from db to check if available
        with get_db_connection() as conn:
            users = conn.execute('SELECT username FROM users').fetchall()
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

        return 'Register succesfull'
    else:
        return render_template("register.html")