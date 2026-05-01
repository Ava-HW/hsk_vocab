from flask import Flask, render_template
from flask import request, redirect, url_for

app = Flask(__name__)

# to activate venv: .\.venv\Scripts\Activate.ps1
 
@app.route("/")
def hello_world():
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
    return render_template("sign_up.html")

@app.route("/user_home", methods = ["POST", "GET"])
def user_home():
    return render_template("user_home.html")