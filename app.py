from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "student_task_manager_secret_key"

DATABASE = "task_manager.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            priority TEXT DEFAULT 'Medium',
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggested_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            priority TEXT DEFAULT 'Medium'
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM suggested_tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        suggested_tasks = [
            (
                "Complete DBMS Assignment",
                "Complete the assigned DBMS questions and submit the assignment.",
                "DBMS",
                "High"
            ),
            (
                "Practice SQL Queries",
                "Practice SELECT, JOIN, GROUP BY and nested SQL queries.",
                "DBMS",
                "Medium"
            ),
            (
                "Prepare Java Practical",
                "Revise important Java programs for the upcoming practical.",
                "Java",
                "High"
            ),
            (
                "Complete Python Lab",
                "Complete the pending Python laboratory programs.",
                "Python",
                "Medium"
            ),
            (
                "Prepare Unit 1 Notes",
                "Read and revise all important topics from Unit 1.",
                "Study",
                "High"
            ),
            (
                "Practice Aptitude Questions",
                "Solve at least 20 basic aptitude questions.",
                "Aptitude",
                "Medium"
            ),
            (
                "Complete Project Documentation",
                "Prepare documentation for the college project.",
                "Project",
                "High"
            ),
            (
                "Prepare Project Presentation",
                "Create slides and prepare important project points.",
                "Project",
                "Medium"
            ),
            (
                "Practice HTML and CSS",
                "Create a simple webpage using HTML and CSS.",
                "Web Development",
                "Low"
            ),
            (
                "Prepare Viva Questions",
                "Prepare important questions and answers for upcoming viva.",
                "Viva",
                "High"
            ),
            (
                "Revise Operating System",
                "Revise important Operating System concepts.",
                "Operating System",
                "Medium"
            ),
            (
                "Practice Data Structures",
                "Solve basic questions on arrays, stacks, queues and linked lists.",
                "Data Structures",
                "High"
            )
        ]

        cursor.executemany("""
            INSERT INTO suggested_tasks
            (title, description, subject, priority)
            VALUES (?, ?, ?, ?)
        """, suggested_tasks)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))

        conn = get_db()

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    total = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()[0]

    pending = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE user_id = ? AND status = 'Pending'
    """, (session["user_id"],)).fetchone()[0]

    completed = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE user_id = ? AND status = 'Completed'
    """, (session["user_id"],)).fetchone()[0]

    tasks = conn.execute("""
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY
            CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
            due_date ASC
    """, (session["user_id"],)).fetchall()

    conn.close()

    if total > 0:
        progress = round((completed / total) * 100)
    else:
        progress = 0

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        pending=pending,
        completed=completed,
        progress=progress
    )


@app.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        subject = request.form["subject"].strip()
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        if not title:
            flash("Task title is required.", "danger")
            return redirect(url_for("add_task"))

        conn = get_db()

        conn.execute("""
            INSERT INTO tasks
            (user_id, title, description, subject, priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
        """, (
            session["user_id"],
            title,
            description,
            subject,
            priority,
            due_date,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        flash("Task added successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_task.html")


@app.route("/edit-task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):

    conn = get_db()

    task = conn.execute("""
        SELECT * FROM tasks
        WHERE id = ? AND user_id = ?
    """, (task_id, session["user_id"])).fetchone()

    if not task:
        conn.close()
        flash("Task not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        subject = request.form["subject"].strip()
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        conn.execute("""
            UPDATE tasks
            SET title = ?,
                description = ?,
                subject = ?,
                priority = ?,
                due_date = ?
            WHERE id = ? AND user_id = ?
        """, (
            title,
            description,
            subject,
            priority,
            due_date,
            task_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash("Task updated successfully.", "success")

        return redirect(url_for("dashboard"))

    conn.close()

    return render_template("edit_task.html", task=task)


@app.route("/complete-task/<int:task_id>")
@login_required
def complete_task(task_id):

    conn = get_db()

    conn.execute("""
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = ? AND user_id = ?
    """, (task_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Task marked as completed.", "success")

    return redirect(url_for("dashboard"))


@app.route("/pending-task/<int:task_id>")
@login_required
def pending_task(task_id):

    conn = get_db()

    conn.execute("""
        UPDATE tasks
        SET status = 'Pending'
        WHERE id = ? AND user_id = ?
    """, (task_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Task moved to pending.", "info")

    return redirect(url_for("dashboard"))


@app.route("/delete-task/<int:task_id>")
@login_required
def delete_task(task_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM tasks
        WHERE id = ? AND user_id = ?
    """, (task_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Task deleted successfully.", "success")

    return redirect(url_for("dashboard"))


@app.route("/suggested-tasks")
@login_required
def suggested_tasks():

    conn = get_db()

    tasks = conn.execute("""
        SELECT * FROM suggested_tasks
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "suggested_tasks.html",
        tasks=tasks
    )


@app.route("/add-suggested/<int:suggested_id>")
@login_required
def add_suggested(suggested_id):

    conn = get_db()

    suggested = conn.execute("""
        SELECT * FROM suggested_tasks
        WHERE id = ?
    """, (suggested_id,)).fetchone()

    if not suggested:
        conn.close()
        flash("Suggested task not found.", "danger")
        return redirect(url_for("suggested_tasks"))

    conn.execute("""
        INSERT INTO tasks
        (user_id, title, description, subject, priority, due_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, '', 'Pending', ?)
    """, (
        session["user_id"],
        suggested["title"],
        suggested["description"],
        suggested["subject"],
        suggested["priority"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    flash("Suggested task added to your tasks.", "success")

    return redirect(url_for("suggested_tasks"))


@app.route("/my-tasks")
@login_required
def my_tasks():

    filter_type = request.args.get("filter", "all")

    conn = get_db()

    if filter_type == "pending":

        tasks = conn.execute("""
            SELECT * FROM tasks
            WHERE user_id = ? AND status = 'Pending'
            ORDER BY due_date ASC
        """, (session["user_id"],)).fetchall()

    elif filter_type == "completed":

        tasks = conn.execute("""
            SELECT * FROM tasks
            WHERE user_id = ? AND status = 'Completed'
            ORDER BY due_date ASC
        """, (session["user_id"],)).fetchall()

    else:

        tasks = conn.execute("""
            SELECT * FROM tasks
            WHERE user_id = ?
            ORDER BY
                CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
                due_date ASC
        """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "my_tasks.html",
        tasks=tasks,
        filter_type=filter_type
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)