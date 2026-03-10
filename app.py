from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
import random
import time
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
    # Algebra
    ("Solve: 3x + 9 = 0. What is x?", "-3"),
    ("Solve: 2x = 16. What is x?", "8"),
    ("Solve: x² = 25. Positive value of x?", "5"),
    ("Solve: 5x - 15 = 0. What is x?", "3"),
    ("Solve: 4x = 36. What is x?", "9"),
    ("Solve: x + 7 = 20. What is x?", "13"),
    ("Solve: 6x = 42. What is x?", "7"),
    ("Solve: x/3 = 5. What is x?", "15"),
    ("Solve: 2x + 10 = 30. What is x?", "10"),
    ("Solve: x² = 64. Positive value of x?", "8"),
    ("Solve: 7x - 21 = 0. What is x?", "3"),
    ("Solve: x/4 = 3. What is x?", "12"),
    
    # Geometry - Area & Perimeter
    ("Area of circle radius 7 (π=22/7)?", "154"),
    ("Perimeter of square side 12?", "48"),
    ("Area of triangle base 10 height 6?", "30"),
    ("Area of rectangle length 8 width 5?", "40"),
    ("Perimeter of rectangle length 10 width 6?", "32"),
    ("Area of square side 9?", "81"),
    ("Perimeter of square side 15?", "60"),
    ("Area of triangle base 12 height 5?", "30"),
    ("Area of circle radius 14 (π=22/7)?", "616"),
    ("Area of square side 11?", "121"),
    ("Perimeter of rectangle length 7 width 3?", "20"),
    ("Area of triangle base 8 height 9?", "36"),
    
    # Coordinate Geometry
    ("Distance between (0,0) and (3,4)?", "5"),
    ("Slope between (1,2) and (3,6)?", "2"),
    ("Distance between (0,0) and (5,12)?", "13"),
    ("Midpoint of (2,4) and (6,8)? X-coordinate only", "4"),
    ("Slope between (0,0) and (4,8)?", "2"),
    
    # Trigonometry
    ("sin(90°)?", "1"),
    ("cos(0°)?", "1"),
    ("tan(45°)?", "1"),
    ("sin(0°)?", "0"),
    ("cos(90°)?", "0"),
    ("sin(30°)?", "0.5"),
    
    # Calculus
    ("Derivative of x² at x=3?", "6"),
    ("Derivative of 3x?", "3"),
    ("Derivative of 5x at x=2?", "5"),
    ("∫ 2x dx at x=3 (ignore C)?", "9"),
    ("∫ 1 dx from 0 to 5?", "5"),
    ("Derivative of x³ at x=2?", "12"),
    
    # Logarithms
    ("log10(100)?", "2"),
    ("log10(1000)?", "3"),
    ("log10(10)?", "1"),
    ("log2(8)?", "3"),
    ("log2(16)?", "4"),
    ("log10(10000)?", "4"),
    
    # Powers & Roots
    ("Square root of 144?", "12"),
    ("2^5?", "32"),
    ("Square root of 81?", "9"),
    ("3^3?", "27"),
    ("2^6?", "64"),
    ("Square root of 196?", "14"),
    ("4^3?", "64"),
    ("2^7?", "128"),
    ("Square root of 169?", "13"),
    ("5^2?", "25"),
    ("Square root of 225?", "15"),
    ("3^4?", "81"),
    ("2^8?", "256"),
    ("10^3?", "1000"),
    
    # Arithmetic
    ("15 × 8 = ?", "120"),
    ("144 ÷ 12 = ?", "12"),
    ("25 × 4 = ?", "100"),
    ("200 ÷ 5 = ?", "40"),
    ("18 × 5 = ?", "90"),
    ("121 ÷ 11 = ?", "11"),
    ("16 × 7 = ?", "112"),
    ("169 ÷ 13 = ?", "13"),
    ("13 × 9 = ?", "117"),
    ("225 ÷ 15 = ?", "15"),
    ("19 × 6 = ?", "114"),
    ("288 ÷ 12 = ?", "24"),
    ("23 + 47 = ?", "70"),
    ("100 - 37 = ?", "63"),
    ("56 + 89 = ?", "145"),
    
    # Number Theory
    ("First prime after 10?", "11"),
    ("First prime after 20?", "23"),
    ("LCM of 4 and 6?", "12"),
    ("GCD of 12 and 18?", "6"),
    ("Next perfect square after 100?", "121"),
    ("Sum of first 5 natural numbers?", "15"),
    ("Sum of first 10 natural numbers?", "55"),
    ("Factorial of 4?", "24"),
    ("Factorial of 5?", "120"),
    
    # Percentages
    ("20% of 200?", "40"),
    ("50% of 80?", "40"),
    ("25% of 100?", "25"),
    ("10% of 500?", "50"),
    ("75% of 80?", "60"),
    
    # Mixed Operations
    ("(12 + 8) × 2 = ?", "40"),
    ("50 - (3 × 6) = ?", "32"),
    ("(20 ÷ 4) + 15 = ?", "20"),
    ("100 - (25 + 30) = ?", "45"),
    ("(15 × 2) - 10 = ?", "20"),
    ("(36 ÷ 6) + 8 = ?", "14"),
    ("7 × (4 + 3) = ?", "49"),
    ("(50 - 20) ÷ 3 = ?", "10"),
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
        session.pop("question_timestamp", None)
        session.pop("used_questions", None)
        return redirect("/dashboard")

    # Check if question exists and if it's expired (30 seconds)
    current_time = time.time()
    question_timestamp = session.get("question_timestamp", 0)
    time_elapsed = current_time - question_timestamp
    
    # Generate new question if it doesn't exist or if 30 seconds have passed
    if "math_question" not in session or time_elapsed > 30:
        # Track used questions to avoid repeats
        if "used_questions" not in session:
            session["used_questions"] = []
        
        # Reset used questions list if all questions have been used
        if len(session["used_questions"]) >= len(questions) - 5:
            session["used_questions"] = []
        
        # Find available questions (not recently used)
        available_questions = [
            (i, q, a) for i, (q, a) in enumerate(questions)
            if i not in session["used_questions"]
        ]
        
        # Select random question from available ones
        if available_questions:
            idx, q, a = random.choice(available_questions)
            session["used_questions"].append(idx)
        else:
            # Fallback: use any random question
            idx = random.randint(0, len(questions) - 1)
            q, a = questions[idx]
            session["used_questions"] = [idx]
        
        session["math_question"] = q
        session["math_answer"] = a
        session["question_timestamp"] = current_time
        time_remaining = 30
    else:
        # Question still valid, calculate remaining time
        time_remaining = max(0, int(30 - time_elapsed))

    if request.method == "POST":

        user_answer = request.form.get("answer")
        view_password = request.form.get("view_password")

        correct_answer = session.get("math_answer")

        if user_answer == correct_answer or check_password_hash(stored_password, view_password):

            session.pop("math_question",None)
            session.pop("math_answer",None)
            session.pop("question_timestamp",None)

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
                                       time_remaining=0,
                                       error="Too many failed attempts. Access locked.")
            
            cursor.execute(
                "UPDATE users SET view_attempts=? WHERE username=?",
                (attempts, session["user"])
            )

            conn.commit()
            conn.close()

            # Calculate new time remaining after failed attempt
            new_time_remaining = max(0, int(30 - (time.time() - session.get("question_timestamp", time.time()))))
            return render_template("verify.html",
                                   question=session["math_question"],
                                   time_remaining=new_time_remaining,
                                   error=f"Wrong answer or password. Attempt {attempts}/3")

    conn.close()

    return render_template("verify.html", question=session["math_question"], time_remaining=time_remaining)


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