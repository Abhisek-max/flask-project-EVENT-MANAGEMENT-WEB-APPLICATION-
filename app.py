from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "smart_college_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            event_date TEXT,
            event_time TEXT,
            venue TEXT,
            guest_speaker TEXT,
            event_goal TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             registration_no TEXT NOT NULL,
             contact TEXT NOT NULL,
             branch TEXT NOT NULL,
             email TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT,
             registration_no TEXT,
             contact TEXT,
             branch TEXT,
             email TEXT UNIQUE,
             password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             student_id INTEGER,
             event_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             email TEXT UNIQUE,
             password TEXT
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO admin (email, password)
        VALUES ('admin@gmail.com', 'admin123')
   """)

    conn.commit()
    conn.close()


init_db()


# ---------- HOME (DYNAMIC CARDS) ----------
@app.route("/")
def home():
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    # ✅ IMPORTANT FIX: include ID
    cursor.execute("SELECT id, event_name, event_date, venue FROM events")
    events = cursor.fetchall()

    conn.close()

    return render_template("index.html", events=events)


# ---------- ADMIN ----------
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html", events=events, students=students)


@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/login")


# ---------- EVENT DETAILS PAGE ----------
@app.route("/event/<int:id>")
def event_details(id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id=?", (id,))
    event = cursor.fetchone()

    conn.close()

    return render_template("event_details.html", event=event)


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        registration_no = request.form.get("registration_no")
        contact = request.form.get("contact")
        branch = request.form.get("branch")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template("register.html", message="Passwords do not match!")

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO students
                (name, registration_no, contact, branch, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (name, registration_no, contact, branch, email, password),
            )

            conn.commit()

            return render_template("register.html", message="Registration Successful!")

        except sqlite3.IntegrityError:
            return render_template("register.html", message="Email Already Exists!")

        finally:
            conn.close()

    return render_template("register.html")


# ---------- EDIT STUDENT ----------
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect("events.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        registration_no = request.form["registration_no"]
        contact = request.form["contact"]
        branch = request.form["branch"]

        c.execute(
            """
            UPDATE students
            SET name=?, email=?, registration_no=?, contact=?, branch=?
            WHERE id=?
        """,
            (name, email, registration_no, contact, branch, id),
        )

        conn.commit()
        conn.close()
        return redirect("/admin")

    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()
    conn.close()

    return render_template("edit_student.html", student=student)


# ---------- DELETE STUDENT ----------
@app.route("/delete_student/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("events.db")
    c = conn.cursor()

    c.execute("DELETE FROM students WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------- LOGIN EVENT ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE email=? AND password=?", (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_email"] = user[5]
            return redirect("/")

        else:
            return render_template("login.html", message="Invalid Email or Password!")

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- ADD EVENT ----------
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":

        event_name = request.form.get("event_name")
        event_date = request.form.get("event_date")
        event_time = request.form.get("event_time")
        venue = request.form.get("venue")
        guest_speaker = request.form.get("guest_speaker")
        event_goal = request.form.get("event_goal")
        description = request.form.get("description")
        capacity = request.form.get("capacity")

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (
                event_name, event_date, event_time,
                venue, guest_speaker, event_goal, description, capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event_name,
                event_date,
                event_time,
                venue,
                guest_speaker,
                event_goal,
                description,
                capacity,
            ),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin"))

    return render_template("add_event.html")


# ---------- DELETE EVENT ----------
@app.route("/delete_event/<int:id>")
def delete_event(id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM events WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------- EDIT EVENT ----------
@app.route("/edit_event/<int:id>", methods=["GET", "POST"])
def edit_event(id):
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    if request.method == "POST":

        event_name = request.form.get("event_name")
        event_date = request.form.get("event_date")
        event_time = request.form.get("event_time")
        venue = request.form.get("venue")
        guest_speaker = request.form.get("guest_speaker")
        event_goal = request.form.get("event_goal")
        description = request.form.get("description")

        cursor.execute(
            """
            UPDATE events SET
            event_name=?, event_date=?, event_time=?,
            venue=?, guest_speaker=?, event_goal=?, description=?
            WHERE id=?
        """,
            (
                event_name,
                event_date,
                event_time,
                venue,
                guest_speaker,
                event_goal,
                description,
                id,
            ),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin"))

    cursor.execute("SELECT * FROM events WHERE id=?", (id,))
    event = cursor.fetchone()
    conn.close()

    return render_template("edit_event.html", event=event)


# ---------- UPDATE DATABASE ----------
@app.route("/update_db")
def update_db():
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN profile_image TEXT
        """)
        conn.commit()
        return "Database Updated Successfully!"
    except:
        return "Column Already Exists!"
    finally:
        conn.close()


# ---------- PROFILE EVENT ----------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (session["user_id"],))
    user = cursor.fetchone()

    conn.close()

    return render_template("profile.html", user=user)


# ----------  EDIT PROFILE EVENT ----------
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        registration_no = request.form["registration_no"]
        contact = request.form["contact"]
        branch = request.form["branch"]
        email = request.form["email"]

        cursor.execute(
            """
            UPDATE students
            SET
                name=?,
                registration_no=?,
                contact=?,
                branch=?,
                email=?
            WHERE id=?
        """,
            (name, registration_no, contact, branch, email, session["user_id"]),
        )

        conn.commit()

        session["user_name"] = name

        conn.close()

        return redirect("/profile")

    cursor.execute("SELECT * FROM students WHERE id=?", (session["user_id"],))

    user = cursor.fetchone()

    conn.close()

    return render_template("edit_profile.html", user=user)


# ---------- UPLOAD PROFILE PHOTO EVENT ----------
@app.route("/upload_profile_photo", methods=["POST"])
def upload_profile_photo():

    if "user_id" not in session:
        return redirect("/login")

    file = request.files["profile_photo"]

    if file and file.filename != "":

        filename = secure_filename(file.filename)

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE students
            SET profile_image=?
            WHERE id=?
        """,
            (filename, session["user_id"]),
        )

        conn.commit()
        conn.close()

    return redirect("/profile")


# ---------- REMOVE PROFILE PHOTO EVENT ----------
@app.route("/remove_profile_photo", methods=["POST"])
def remove_profile_photo():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT profile_image FROM students WHERE id=?", (session["user_id"],)
    )

    photo = cursor.fetchone()

    if photo and photo[0]:

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], photo[0])

        if os.path.exists(filepath):
            os.remove(filepath)

        cursor.execute(
            """
            UPDATE students
            SET profile_image=NULL
            WHERE id=?
        """,
            (session["user_id"],),
        )

        conn.commit()

    conn.close()

    return redirect("/profile")


# ---------- CHANGE PASSWORD EVENT ----------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM students WHERE id=?", (session["user_id"],)
        )

        user = cursor.fetchone()

        if user[0] != current_password:
            conn.close()
            return render_template(
                "change_password.html", message="Current Password Incorrect!"
            )

        if new_password != confirm_password:
            conn.close()
            return render_template(
                "change_password.html", message="Passwords Do Not Match!"
            )

        cursor.execute(
            "UPDATE students SET password=? WHERE id=?",
            (new_password, session["user_id"]),
        )

        conn.commit()
        conn.close()

        return render_template(
            "change_password.html", message="Password Updated Successfully!"
        )

    return render_template("change_password.html")


# ---------- FORGOT PASSWORD EVENT ----------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return render_template(
                "forgot_password.html", message="Passwords do not match!"
            )

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE email=?", (email,))

        user = cursor.fetchone()

        if not user:
            conn.close()
            return render_template("forgot_password.html", message="Email not found!")

        cursor.execute(
            "UPDATE students SET password=? WHERE email=?", (new_password, email)
        )

        conn.commit()
        conn.close()

        return render_template(
            "forgot_password.html", message="Password Reset Successful!"
        )

    return render_template("forgot_password.html")


# ---------- JOIN EVENT ----------
@app.route("/join_event/<int:event_id>")
def join_event(event_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM registrations
        WHERE student_id=? AND event_id=?
    """,
        (session["user_id"], event_id),
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return "You have already joined this event!"

    # Event Capacity Check
    cursor.execute("SELECT capacity FROM events WHERE id=?", (event_id,))

    capacity = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registrations WHERE event_id=?", (event_id,))

    current = cursor.fetchone()[0]

    if current >= capacity:
        conn.close()
        return "Event Full! Registration Closed."

    cursor.execute(
        """
        INSERT INTO registrations
        (student_id, event_id)
        VALUES (?, ?)
    """,
        (session["user_id"], event_id),
    )

    conn.commit()
    conn.close()

    return redirect("/my_events")


# ---------- MY EVENTS ----------
@app.route("/my_events")
def my_events():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT events.*
        FROM events
        JOIN registrations
        ON events.id = registrations.event_id
        WHERE registrations.student_id = ?
    """,
        (session["user_id"],),
    )

    events = cursor.fetchall()

    conn.close()

    return render_template("my_events.html", events=events)


# ---------- CLEAR REGISTRATIONS ----------
@app.route("/clear_registrations")
def clear_registrations():

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registrations")

    conn.commit()
    conn.close()

    return "Registrations Cleared!"


# ---------- PARTICIPANTS LIST ----------
@app.route("/participants/<int:event_id>")
def participants(event_id):

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    # Event Name
    cursor.execute("SELECT event_name FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    # Registered Students
    cursor.execute(
        """
        SELECT students.name,
               students.registration_no,
               students.branch,
               students.email
        FROM registrations
        JOIN students
        ON registrations.student_id = students.id
        WHERE registrations.event_id = ?
    """,
        (event_id,),
    )

    participants = cursor.fetchall()

    conn.close()

    return render_template("participants.html", participants=participants, event=event)


# ---------- API: EVENT COUNTS ----------
@app.route("/api/event_counts")
def event_counts():
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id, COUNT(*) 
        FROM registrations
        GROUP BY event_id
    """)

    rows = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in rows}


# ---------- ADMIN LOGIN ----------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM admin
            WHERE email=? AND password=?
        """,
            (email, password),
        )

        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", message="Invalid credentials")

    return render_template("admin_login.html")


# ---------- LEAVE EVENT ----------
@app.route("/leave_event/<int:event_id>")
def leave_event(event_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM registrations
        WHERE student_id=? AND event_id=?
    """,
        (session["user_id"], event_id),
    )

    conn.commit()
    conn.close()

    return redirect("/my_events")


# ---------- ADD CAPACITY COLUMN ----------
@app.route("/add_capacity_column")
def add_capacity_column():

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN capacity INTEGER DEFAULT 50
        """)

        conn.commit()
        return "Capacity Column Added!"

    except Exception as e:
        return str(e)

    finally:
        conn.close()


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
