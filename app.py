from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"


# ---------------- DATABASE INIT ----------------

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT,
        question TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT,
        question TEXT,
        status TEXT,
        remarks TEXT,
        date TEXT,
        record_id TEXT,
        user TEXT
    )
    """)

    # create master user if not exists
    c.execute("SELECT * FROM users WHERE username=?", ("master",))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                  ("master",
                   generate_password_hash("master123"),
                   "MASTER"))

    conn.commit()
    conn.close()

init_db()


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):

            session["user"] = user[1]
            session["role"] = user[3]

            return redirect("/dashboard")

        flash("Invalid login")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html",
                           role=session["role"],
                           user=session["user"])


# ---------------- USER MANAGEMENT ----------------

@app.route("/users", methods=["GET", "POST"])
def users():

    if session.get("role") != "MASTER":
        return redirect("/dashboard")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        c.execute("INSERT INTO users VALUES(NULL,?,?,?)",
                  (username, password, role))
        conn.commit()

    c.execute("SELECT username, role FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("user_management.html", users=users)


# ---------------- ADD MACHINE ----------------

@app.route("/add_machine", methods=["POST"])
def add_machine():

    if session.get("role") not in ["MASTER", "Admin", "Manager"]:
        return redirect("/dashboard")

    name = request.form["machine"]

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO machines VALUES(NULL,?)", (name,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- ADD CHECKLIST ----------------

@app.route("/add_checklist", methods=["GET", "POST"])
def add_checklist():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == "POST":

        machine = request.form["machine"]
        question = request.form["question"]

        c.execute("INSERT INTO checklists VALUES(NULL,?,?)",
                  (machine, question))
        conn.commit()

    c.execute("SELECT name FROM machines")
    machines = c.fetchall()

    conn.close()

    return render_template("add_checklist.html", machines=machines)


# ---------------- FILL CHECKLIST ----------------

@app.route("/fill", methods=["GET", "POST"])
def fill():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == "POST":

        machine = request.form["machine"]
        question = request.form["question"]
        status = request.form["status"]
        remarks = request.form["remarks"]

        date = datetime.now().strftime("%d%b%Y").upper()

        record_id = machine + "_" + date

        c.execute("""
        INSERT INTO records VALUES(NULL,?,?,?,?,?,?,?)
        """, (machine, question, status, remarks, date,
              record_id, session["user"]))

        conn.commit()

    c.execute("SELECT name FROM machines")
    machines = c.fetchall()

    conn.close()

    return render_template("fill_checklist.html",
                           machines=machines)


# ---------------- SHOW DATA ----------------

@app.route("/data")
def data():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM records ORDER BY id DESC")

    records = c.fetchall()

    conn.close()

    return render_template("show_data.html",
                           records=records)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run()
