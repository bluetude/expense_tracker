import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_db_connection():
    conn = sqlite3.connect('expense_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

user_id = 1
with get_db_connection() as conn:
    data = conn.execute("SELECT expenses.name, expenses.description, expenses.amount, expenses_category.category, expenses.date FROM expenses INNER JOIN expenses_category ON expenses.category = expenses_category.id WHERE user_id = ? AND expenses.date >= ? AND expenses.date < ? ORDER BY date DESC", (user_id, datetime.today().replace(day=1), (datetime.today() + relativedelta(day=31)))).fetchall()

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

print(len(chart))

print(datetime.today().replace(day=1))