from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os
from datetime import datetime
import openpyxl

app = Flask(__name__)
app.secret_key = "pm_secret_key"

DB_PATH = "pm.db"

# ---------------- DATABASE INIT ----------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS machines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS checklists(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT,
        question TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT,
        date TEXT,
        question TEXT,
        status TEXT,
        remarks TEXT
    )
    """)

    # default master user
    c.execute("SELECT * FROM users WHERE username='master'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES(NULL,'master','master123','MASTER')")

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()

        c.execute("SELECT role FROM users WHERE username=? AND password=?",(username,password))
        user=c.fetchone()

        conn.close()

        if user:
            session["user"]=username
            session["role"]=user[0]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html",
                           user=session["user"],
                           role=session["role"])

# ---------------- ADD CHECKLIST ----------------

@app.route("/add_checklist",methods=["GET","POST"])
def add_checklist():

    if request.method=="POST":

        machine=request.form["machine"]
        question=request.form["question"]

        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()

        c.execute("INSERT OR IGNORE INTO machines(name) VALUES(?)",(machine,))
        c.execute("INSERT INTO checklists(machine,question) VALUES(?,?)",(machine,question))

        conn.commit()
        conn.close()

    return render_template("add_checklist.html")

# ---------------- FILL CHECKLIST ----------------

@app.route("/fill_checklist",methods=["GET","POST"])
def fill_checklist():

    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    if request.method=="POST":

        machine=request.form["machine"]

        c.execute("SELECT question FROM checklists WHERE machine=?",(machine,))
        questions=c.fetchall()

        today=datetime.now().strftime("%d%b%Y")

        for q in questions:

            status=request.form.get(q[0]+"_status")
            remarks=request.form.get(q[0]+"_remarks")

            c.execute("INSERT INTO records(machine,date,question,status,remarks) VALUES(?,?,?,?,?)",
                      (machine,today,q[0],status,remarks))

        conn.commit()

    c.execute("SELECT name FROM machines")
    machines=c.fetchall()

    conn.close()

    return render_template("fill_checklist.html",machines=machines)

# ---------------- SHOW DATA ----------------

@app.route("/show_data")
def show_data():

    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    c.execute("SELECT * FROM records")
    data=c.fetchall()

    conn.close()

    return render_template("show_data.html",data=data)

# ---------------- USER MANAGEMENT ----------------

@app.route("/user_management",methods=["GET","POST"])
def user_management():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()

        c.execute("INSERT INTO users VALUES(NULL,?,?,?)",(username,password,"USER"))

        conn.commit()
        conn.close()

    return render_template("user_management.html")

# ---------------- EXPORT EXCEL ----------------

@app.route("/export_excel")
def export_excel():

    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    c.execute("SELECT * FROM records")
    data=c.fetchall()

    conn.close()

    wb=openpyxl.Workbook()
    ws=wb.active

    ws.append(["Machine","Date","Question","Status","Remarks"])

    for row in data:
        ws.append(row[1:])

    filename="pm_export.xlsx"
    wb.save(filename)

    return send_file(filename,as_attachment=True)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__=="__main__":
    app.run()
