from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads/videos"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {"mp4", "mkv", "webm", "jpg", "jpeg", "png"}

# ------------------------------
# CHECK FILE TYPE
# ------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------------
# DATABASE INITIALIZATION
# ------------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        login_password TEXT,
        view_password TEXT,
        delete_password TEXT,
        view_attempts INTEGER DEFAULT 0,
        delete_attempts INTEGER DEFAULT 0,
        view_locked INTEGER DEFAULT 0,
        delete_locked INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ------------------------------
# HOME
# ------------------------------
@app.route("/")
def home():
    return "Secure Video Vault Project Started"


# ------------------------------
# REGISTER
# ------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        login_password = request.form["login_password"]
        view_password = request.form["view_password"]
        delete_password = request.form["delete_password"]

        login_hash = generate_password_hash(login_password)
        view_hash = generate_password_hash(view_password)
        delete_hash = generate_password_hash(delete_password)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO users (username, login_password, view_password, delete_password)
            VALUES (?, ?, ?, ?)
            """, (username, login_hash, view_hash, delete_hash))

            conn.commit()
            message = "User registered successfully!"

        except:
            message = "Username already exists!"

        conn.close()

        return message

    return render_template("register.html")


# ------------------------------
# LOGIN
# ------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT login_password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[0], password):

            session["user"] = username
            return redirect("/dashboard")

        else:
            return "Invalid username or password"

    return render_template("login.html")


# ------------------------------
# DASHBOARD
# ------------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    files = os.listdir(UPLOAD_FOLDER)

    return render_template("dashboard.html", username=session["user"], files=files)


# ------------------------------
# UPLOAD FILE
# ------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files["video"]

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            file.save(filepath)

            return redirect("/dashboard")

        else:
            return "Invalid file type"

    return render_template("upload.html")


# ------------------------------
# SERVE MEDIA FILES
# ------------------------------
@app.route("/media/<filename>")
def media(filename):

    return send_from_directory(UPLOAD_FOLDER, filename)


# ------------------------------
# LOGOUT
# ------------------------------
@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect("/login")


# ------------------------------
# RUN SERVER
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)