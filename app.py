from flask import Flask, render_template
from flask import request, redirect, url_for
from functools import wraps
from flask import g, redirect
import sqlite3

app = Flask(__name__)

# to activate venv: .\.venv\Scripts\Activate.ps1

# code to connect database to flask app
DATABASE = 'hsk.db'
app.secret_key = 'the random string'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# code to start database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
 
@app.route("/")
def hello_world():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM words;")
    thing = cur.fetchall()
    print(thing)
    return render_template("index.html")

@app.route("/sign_in", methods = ["POST", "GET"])
def sign_in():
    if request.method == "POST":
        username = request.form.get('username')
        print(username)
        return redirect(url_for("user_home"))
    return render_template("sign_in.html")

@app.route("/sign_up", methods = ["POST", "GET"])
def sign_up():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        print(email, password, name)
    return render_template("sign_up.html")

@app.route("/user_home", methods = ["POST", "GET"])
def user_home():
    return render_template("user_home.html")