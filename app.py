from flask import Flask, render_template

app = Flask(__name__)

# to activate venv: .\.venv\Scripts\Activate.ps1
 
@app.route("/")
def hello_world():
    return render_template("index.html")