from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

UPLOAD_FOLDER = "uploads/videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4","mkv","webm","jpg","jpeg","png"}

# -------------------------
# Advanced Math Questions
# -------------------------
questions = [

("Solve: 3x + 9 = 0. What is x?", "-3"),
("Solve: 2x = 16. What is x?", "8"),
("Solve: x² = 25. Positive value of x?", "5"),

("Area of circle radius 7 (π=22/7)?", "154"),
("Perimeter of square side 12?", "48"),
("Area of triangle base 10 height 6?", "30"),

("Distance between (0,0) and (3,4)?", "5"),
("Slope between (1,2) and (3,6)?", "2"),

("sin(90)?", "1"),
("cos(0)?", "1"),
("tan(45)?", "1"),

("Derivative of x² at x=3?", "6"),
("Derivative of 3x?", "3"),

("∫ 2x dx at x=3 (ignore C)?", "9"),
("∫ 1 dx from 0 to 5?", "5"),

("log10(100)?", "2"),
("log10(1000)?", "3"),

("Square root of 144?", "12"),
("2^5 ?", "32")
]

# -------------------------
# File Validation
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------
# DATABASE
# -------------------------
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


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET","POST"])
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
            INSERT INTO users (username,login_password,view_password,delete_password)
            VALUES (?,?,?,?)
            """,(username,login_hash,view_hash,delete_hash))

            conn.commit()

        except:
            return "Username already exists"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT login_password FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user[0], password):
            session["user"] = username

            # Reset security locks on login
            cursor.execute("""
            UPDATE users
            SET view_attempts=0,
                delete_attempts=0,
                view_locked=0,
                delete_locked=0
            WHERE username=?
            """,(username,))

            conn.commit()
            conn.close()

            return redirect("/dashboard")
        else:
            # Either username or password is wrong
            conn.close()
            return render_template("login.html", error="Wrong credentials")

    return render_template("login.html")


# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    files = os.listdir(UPLOAD_FOLDER)

    return render_template("dashboard.html", username=session["user"], files=files)


# -------------------------
# UPLOAD MEDIA
# -------------------------
@app.route("/upload", methods=["GET","POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files["media"]

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER,filename))

            return redirect("/dashboard")

    return render_template("upload.html")


# -------------------------
# VERIFY ACCESS
# -------------------------
@app.route("/verify/<filename>", methods=["GET","POST"])
def verify(filename):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT view_attempts, view_locked, view_password FROM users WHERE username=?",
        (session["user"],)
    )

    attempts, locked, stored_password = cursor.fetchone()

    # BLOCK ACCESS COMPLETELY IF LOCKED
    if locked == 1:
        conn.close()
        session.pop("math_question", None)
        session.pop("math_answer", None)
        return redirect("/dashboard")

    if "math_question" not in session:

        q,a = random.choice(questions)

        session["math_question"] = q
        session["math_answer"] = a

    if request.method == "POST":

        user_answer = request.form.get("answer")
        view_password = request.form.get("view_password")

        correct_answer = session.get("math_answer")

        if user_answer == correct_answer or check_password_hash(stored_password, view_password):

            session.pop("math_question",None)
            session.pop("math_answer",None)

            cursor.execute(
                "UPDATE users SET view_attempts=0 WHERE username=?",
                (session["user"],)
            )

            conn.commit()
            conn.close()

            return redirect(f"/view/{filename}")

        else:

            attempts += 1

            if attempts >= 3:

                cursor.execute(
                    "UPDATE users SET view_locked=1 WHERE username=?",
                    (session["user"],)
                )

                conn.commit()
                conn.close()

                return render_template("verify.html",
                                       question=session["math_question"],
                                       error="Too many failed attempts. Access locked.")

            cursor.execute(
                "UPDATE users SET view_attempts=? WHERE username=?",
                (attempts,session["user"])
            )

            conn.commit()
            conn.close()

            return render_template("verify.html",
                                   question=session["math_question"],
                                   error=f"Wrong answer or password. Attempt {attempts}/3")

    conn.close()

    return render_template("verify.html", question=session["math_question"])


# -------------------------
# VIEW MEDIA
# -------------------------
@app.route("/view/<filename>")
def view_media(filename):

    if "user" not in session:
        return redirect("/login")

    return render_template("view_media.html", file=filename)


# -------------------------
# DELETE MEDIA
# -------------------------
@app.route("/delete/<filename>", methods=["GET","POST"])
def delete_media(filename):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT delete_password, delete_attempts, delete_locked FROM users WHERE username=?",
        (session["user"],)
    )

    stored_password, attempts, locked = cursor.fetchone()

    if locked == 1:
        conn.close()
        return render_template("delete_verify.html",
                               filename=filename,
                               error="Delete locked due to multiple failed attempts.")

    if request.method == "POST":

        entered_password = request.form["delete_password"]

        if check_password_hash(stored_password, entered_password):

            filepath = os.path.join(UPLOAD_FOLDER, filename)

            if os.path.exists(filepath):
                os.remove(filepath)

            cursor.execute(
                "UPDATE users SET delete_attempts=0 WHERE username=?",
                (session["user"],)
            )

            conn.commit()
            conn.close()

            return redirect("/dashboard")

        else:

            attempts += 1

            if attempts >= 3:

                cursor.execute(
                    "UPDATE users SET delete_locked=1 WHERE username=?",
                    (session["user"],)
                )

                conn.commit()
                conn.close()

                return render_template("delete_verify.html",
                                       filename=filename,
                                       error="Too many wrong attempts. Delete locked.")

            cursor.execute(
                "UPDATE users SET delete_attempts=? WHERE username=?",
                (attempts, session["user"])
            )

            conn.commit()
            conn.close()

            return render_template("delete_verify.html",
                                   filename=filename,
                                   error=f"Wrong password. Attempt {attempts}/3")

    conn.close()

    return render_template("delete_verify.html", filename=filename)


# -------------------------
# SERVE MEDIA
# -------------------------
@app.route("/media/<filename>")
def media(filename):
    return send_from_directory(UPLOAD_FOLDER,filename)


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():

    session.pop("user",None)
    return redirect("/login")


# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)