from flask import Flask, render_template, session
from flask import request, redirect, url_for
from functools import wraps
from flask import g, redirect
import sqlite3
import csv

app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user ID is in session
        if 'user_id' not in session:
            return redirect(url_for('sign_in', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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
    return render_template("index.html")

@app.route("/sign_in", methods = ["POST", "GET"])
def sign_in():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        # check if email and password match
        query = "SELECT * FROM users WHERE email = ?;"
        data = (email,)
        cur.execute(query, data)
        result = cur.fetchone()
        if result:
            if(result['password'] == password):
                session['user_id'] = email
                return redirect(url_for("user_home"))
    return render_template("sign_in.html")

@app.route("/sign_up", methods = ["POST", "GET"])
def sign_up():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        query = "INSERT INTO users (email, password, name) VALUES (?, ?, ?)"
        data = (email, password, name)
        cur.execute(query, data)   
        db.commit()     
    return render_template("sign_up.html")

@app.route("/user_home", methods = ["POST", "GET"])
@login_required
def user_home():
    db = get_db()
    cur = db.cursor()
    # get list of words to display
    cur.execute("SELECT * FROM words;")
    words = cur.fetchall()
    return render_template("user_home.html", words = words)