"""
Reference secured Flask app for secure coding lab.
This version demonstrates safer implementations for:
- Login
- Assignment submission
- Messaging
- Profile update

Run in a controlled lab environment.
"""

from flask import Flask, request, session, redirect, url_for, render_template_string, abort
import pymysql
import os
import uuid
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-lab")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "yourpassword"),
    "database": os.getenv("DB_NAME", "student_portal_lab_secure"),
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, role, full_name, email, phone FROM users WHERE id = %s", (uid,))
        return cur.fetchone()


@app.route("/")
def index():
    user = current_user()
    return render_template_string("""
    <h2>Student Portal Lab Demo (Secured Reference)</h2>
    {% if user %}
      <p>Logged in as <b>{{ user.username }}</b> ({{ user.role }})</p>
      <p><a href="/logout">Logout</a></p>
    {% else %}
      <p><a href="/login">Login</a></p>
    {% endif %}
    <ul>
      <li><a href="/assignment">Assignment Submission</a></li>
      <li><a href="/message">Messaging</a></li>
      {% if user %}
      <li><a href="/profile">Profile Update</a></li>
      {% endif %}
    </ul>
    """, user=user)


# -------------------------------------------------------------------
# 1) LOGIN
# -------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Safer input validation
        if not username or not password or len(username) > 50:
            return "Invalid username or password."

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

        # Generic error message prevents username enumeration
        if not user or not check_password_hash(user["password_hash"], password):
            return "Invalid username or password."

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return redirect(url_for("index"))

    return render_template_string("""
    <h3>Login</h3>
    <form method="post">
      Username: <input type="text" name="username" maxlength="50"><br><br>
      Password: <input type="password" name="password"><br><br>
      <button type="submit">Login</button>
    </form>
    <p><a href="/">Back</a></p>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# -------------------------------------------------------------------
# 2) ASSIGNMENT SUBMISSION
# -------------------------------------------------------------------
@app.route("/assignment", methods=["GET", "POST"])
def assignment():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        course_code = request.form.get("course_code", "").strip()
        title = request.form.get("title", "").strip()
        upload = request.files.get("assignment_file")

        if not course_code or not title:
            return "Course code and title are required."

        if not upload or not upload.filename:
            return "No file selected."

        if not allowed_file(upload.filename):
            return "Invalid file type. Allowed: pdf, doc, docx, txt."

        upload.stream.seek(0, os.SEEK_END)
        size = upload.stream.tell()
        upload.stream.seek(0)
        if size > MAX_UPLOAD_SIZE:
            return "File too large. Maximum allowed is 5 MB."

        upload_dir = os.path.join(os.getcwd(), "uploads_secure")
        os.makedirs(upload_dir, exist_ok=True)

        original_name = secure_filename(upload.filename)
        ext = original_name.rsplit(".", 1)[1].lower()
        saved_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, saved_name)
        upload.save(filepath)

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assignments (user_id, course_code, title, original_filename, stored_filename)
                VALUES (%s, %s, %s, %s, %s)
            """, (user["id"], course_code, title, original_name, saved_name))

        return f"Assignment uploaded successfully: {escape(original_name)}. <a href='/'>Home</a>"

    return render_template_string("""
    <h3>Assignment Submission</h3>
    <form method="post" enctype="multipart/form-data">
      Course Code: <input type="text" name="course_code" maxlength="20"><br><br>
      Title: <input type="text" name="title" maxlength="200"><br><br>
      File: <input type="file" name="assignment_file"><br><br>
      <button type="submit">Submit Assignment</button>
    </form>
    <p><a href="/">Back</a></p>
    """)


# -------------------------------------------------------------------
# 3) MESSAGING
# -------------------------------------------------------------------
@app.route("/message", methods=["GET", "POST"])
def message():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        recipient = request.form.get("recipient", "").strip()
        message_text = request.form.get("message_text", "").strip()

        if not recipient or not message_text:
            return "Recipient and message are required."

        if len(message_text) > 2000:
            return "Message too long."

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (sender_user_id, recipient_username, message_text)
                VALUES (%s, %s, %s)
            """, (user["id"], recipient, message_text))

        return redirect(url_for("message"))

    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.id, u.username AS sender, m.recipient_username, m.message_text, m.created_at
            FROM messages m
            JOIN users u ON m.sender_user_id = u.id
            WHERE u.username = %s OR m.recipient_username = %s
            ORDER BY m.id DESC
        """, (user["username"], user["username"]))
        messages = cur.fetchall()

    return render_template_string("""
    <h3>Messaging</h3>
    <form method="post">
      Recipient Username: <input type="text" name="recipient" maxlength="50"><br><br>
      Message: <textarea name="message_text" maxlength="2000"></textarea><br><br>
      <button type="submit">Send</button>
    </form>
    <h4>Your Messages</h4>
    <ul>
      {% for m in messages %}
        <li><b>{{ m.sender }}</b> to <b>{{ m.recipient_username }}</b>: {{ m.message_text }}</li>
      {% endfor %}
    </ul>
    <p><a href="/">Back</a></p>
    """, messages=messages)
    # Jinja auto-escapes output here, helping prevent XSS.


# -------------------------------------------------------------------
# 4) PROFILE UPDATE
# -------------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not full_name or not email:
            return "Full name and email are required."
        if len(full_name) > 100 or len(email) > 100 or len(phone) > 30:
            return "Input exceeds allowed length."

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET full_name = %s, email = %s, phone = %s
                WHERE id = %s
            """, (full_name, email, phone, user["id"]))

        return "Profile updated successfully. <a href='/'>Home</a>"

    return render_template_string("""
    <h3>Profile Update</h3>
    <form method="post">
      Full Name: <input type="text" name="full_name" value="{{ user.full_name }}" maxlength="100"><br><br>
      Email: <input type="text" name="email" value="{{ user.email }}" maxlength="100"><br><br>
      Phone: <input type="text" name="phone" value="{{ user.phone or '' }}" maxlength="30"><br><br>
      <button type="submit">Update Profile</button>
    </form>
    <p>Editing your own profile only.</p>
    <p><a href="/">Back</a></p>
    """, user=user)


@app.errorhandler(403)
def forbidden(_):
    return "Access denied.", 403


@app.errorhandler(404)
def not_found(_):
    return "Page not found.", 404


@app.errorhandler(500)
def server_error(_):
    return "An internal error occurred.", 500


if __name__ == "__main__":
    app.run(debug=False)
