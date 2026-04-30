from flask import Flask, render_template
from flask import request

app = Flask(__name__)

# to activate venv: .\.venv\Scripts\Activate.ps1
 
@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/sign_in", methods = ["POST", "GET"])
def sign_in():
    if request.method == "POST":
        return hello_world()
    return render_template("sign_in.html")

@app.route("/sign_up", methods = ["POST", "GET"])
def sign_up():
    return render_template("sign_up.html")