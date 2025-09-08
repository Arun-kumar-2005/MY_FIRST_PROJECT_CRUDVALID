import os
import time
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

# Ensure Flask uses the 'static' folder in the project root
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Simple cache-buster value (changes each restart)
app.jinja_env.globals['static_version'] = str(int(time.time()))

# Debug prints (will appear in the terminal when you start the app)
print("DEBUG: Flask static_folder =", app.static_folder)
print("DEBUG: Flask template_folder =", app.template_folder)
print("DEBUG: Current working dir =", os.getcwd())

# --- MySQL Connection ---
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST", "localhost"),
    user=os.getenv("MYSQLUSER", "root"),
    password=os.getenv("MYSQLPASSWORD", "1234"),
    database=os.getenv("MYSQLDATABASE", "company_app"),
    port=int(os.getenv("MYSQLPORT", 3306))
)

cursor = db.cursor(dictionary=True)

# Debug route to check static file existence
@app.route("/static-debug")
def static_debug():
    css_path = os.path.join(app.static_folder, "style.css")
    return {
        "static_folder": app.static_folder,
        "css_path": css_path,
        "exists": os.path.exists(css_path),
        "url_to_css": url_for('static', filename='style.css'),
    }

# --- Routes ---

# Dashboard (show only names)
@app.route("/")
def dashboard():
    cursor.execute("SELECT id, name FROM companies")
    companies = cursor.fetchall()

    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    return render_template("dashboard.html", companies=companies, users=users)

# Organisations Page
@app.route("/organisations", methods=["GET", "POST"])
def organisations():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        description = request.form["description"]
        cursor.execute(
            "INSERT INTO companies (name, email, description) VALUES (%s, %s, %s)",
            (name, email, description)
        )
        db.commit()
        return redirect(url_for("organisations"))

    cursor.execute("SELECT * FROM companies")
    companies = cursor.fetchall()
    return render_template("organisations.html", companies=companies)

# --- Delete User Route ---
@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    return redirect(url_for("users"))

# --- Delete Organisation Route ---
@app.route("/delete_company/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    cursor.execute("DELETE FROM companies WHERE id = %s", (company_id,))
    db.commit()
    return redirect(url_for("organisations"))

# --- View Employees of a Company ---
@app.route("/view_employees/<int:company_id>")
def view_employees(company_id):
    cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
    company = cursor.fetchone()

    cursor.execute("""
        SELECT users.id, users.name, users.email 
        FROM users 
        WHERE users.company_id = %s
    """, (company_id,))
    employees = cursor.fetchall()

    return render_template("view_employees.html", company=company, employees=employees)

# Users Page
@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        company_id = request.form["company_id"]
        cursor.execute(
            "INSERT INTO users (name, email, password, company_id) VALUES (%s, %s, %s, %s)",
            (name, email, password, company_id)
        )
        db.commit()
        return redirect(url_for("users"))

    company_id = request.args.get("company_id")
    cursor.execute("SELECT * FROM companies")
    companies = cursor.fetchall()

    if company_id:
        cursor.execute("""
            SELECT users.id, users.name, users.email, companies.name AS company
            FROM users 
            JOIN companies ON users.company_id = companies.id
            WHERE users.company_id = %s
        """, (company_id,))
    else:
        cursor.execute("""
            SELECT users.id, users.name, users.email, companies.name AS company
            FROM users 
            JOIN companies ON users.company_id = companies.id
        """)

    users_list = cursor.fetchall()
    return render_template("users.html", companies=companies, users=users_list)

if __name__ == "__main__":
    app.run(debug=True)
