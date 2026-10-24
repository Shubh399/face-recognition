import csv
import datetime
import hmac
import io
import json
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from model import (
    MODEL_PATH,
    decode_image_bytes,
    extract_embedding_for_image,
    load_model_if_exists,
    predict_with_model,
    train_model_background,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, ".env"))
DB_PATH = os.path.join(APP_DIR, "attendance.db")
DATASET_DIR = os.path.join(APP_DIR, "dataset")
TRAIN_STATUS_FILE = os.path.join(APP_DIR, "train_status.json")
os.makedirs(DATASET_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME"),
    ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD"),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(minutes=30),
)
if not app.config["SECRET_KEY"] or not app.config["ADMIN_USERNAME"] or not app.config["ADMIN_PASSWORD"]:
    raise RuntimeError("Set SECRET_KEY, ADMIN_USERNAME, and ADMIN_PASSWORD environment variables before starting.")
if len(app.config["ADMIN_PASSWORD"]) < 6:
    raise RuntimeError("ADMIN_PASSWORD must be at least 6 characters long.")

CSRFProtect(app)
training_lock = threading.Lock()


@contextmanager
def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with connect_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_date TEXT NOT NULL,
                class_time TEXT NOT NULL,
                faculty TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        class_columns = {row["name"] for row in conn.execute("PRAGMA table_info(classes)").fetchall()}
        if "class_date" not in class_columns:
            conn.execute("ALTER TABLE classes ADD COLUMN class_date TEXT NOT NULL DEFAULT ''")
            conn.execute(
                """UPDATE classes
                   SET class_date = COALESCE(NULLIF(date(created_at), ''), date('now'))
                   WHERE class_date = ''"""
            )
        if "end_time" not in class_columns:
            conn.execute("ALTER TABLE classes ADD COLUMN end_time TEXT NOT NULL DEFAULT ''")
            conn.execute(
                """UPDATE classes
                   SET end_time = CASE
                       WHEN time(class_time, '+1 hour') IS NULL THEN '23:59'
                       WHEN class_time >= '23:00' THEN '23:59'
                       ELSE time(class_time, '+1 hour')
                   END
                   WHERE end_time = ''"""
            )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll TEXT,
                class TEXT,
                section TEXT,
                reg_no TEXT,
                created_at TEXT
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                name TEXT,
                timestamp TEXT,
                class_id INTEGER
            )"""
        )
        attendance_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()
        }
        if "class_id" not in attendance_columns:
            conn.execute("ALTER TABLE attendance ADD COLUMN class_id INTEGER")

        conn.execute(
            """CREATE TABLE IF NOT EXISTS attendance_daily (
                student_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                class_id INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (student_id, attendance_date, class_id)
            )"""
        )
        daily_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(attendance_daily)").fetchall()
        }
        if "class_id" not in daily_columns:
            conn.execute("ALTER TABLE attendance_daily RENAME TO attendance_daily_legacy")
            conn.execute(
                """CREATE TABLE attendance_daily (
                    student_id INTEGER NOT NULL,
                    attendance_date TEXT NOT NULL,
                    class_id INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (student_id, attendance_date, class_id)
                )"""
            )
            conn.execute(
                """INSERT OR IGNORE INTO attendance_daily (student_id, attendance_date, class_id)
                   SELECT student_id, attendance_date, 0 FROM attendance_daily_legacy"""
            )
            conn.execute("DROP TABLE attendance_daily_legacy")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS student_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                image BLOB NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """INSERT OR IGNORE INTO attendance_daily (student_id, attendance_date, class_id)
               SELECT student_id, date(timestamp), COALESCE(class_id, 0) FROM attendance
               WHERE student_id IS NOT NULL AND date(timestamp) IS NOT NULL"""
        )


def migrate_dataset_images():
    if not os.path.isdir(DATASET_DIR):
        return
    for student_folder in os.listdir(DATASET_DIR):
        if not student_folder.isdigit():
            continue
        folder = os.path.join(DATASET_DIR, student_folder)
        if not os.path.isdir(folder):
            continue
        files = [
            os.path.join(folder, filename)
            for filename in os.listdir(folder)
            if filename.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not files:
            continue
        migrated_files = []
        with connect_db() as conn:
            student = conn.execute("SELECT 1 FROM students WHERE id = ?", (int(student_folder),)).fetchone()
            existing = conn.execute(
                "SELECT 1 FROM student_faces WHERE student_id = ? LIMIT 1", (int(student_folder),)
            ).fetchone()
            if student and not existing:
                created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for path in files:
                    with open(path, "rb") as image_file:
                        image = image_file.read()
                    if decode_image_bytes(image) is None:
                        app.logger.warning("Skipping invalid legacy face image: %s", path)
                        continue
                    conn.execute(
                        "INSERT INTO student_faces (student_id, image, created_at) VALUES (?, ?, ?)",
                        (int(student_folder), image, created_at),
                    )
                    migrated_files.append(path)
        for path in migrated_files:
            if os.path.isfile(path):
                os.remove(path)
        if migrated_files and not os.listdir(folder):
            os.rmdir(folder)


def write_train_status(status):
    temp_path = TRAIN_STATUS_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as status_file:
        json.dump(status, status_file)
    os.replace(temp_path, TRAIN_STATUS_FILE)


def read_train_status():
    if not os.path.exists(TRAIN_STATUS_FILE):
        return {"running": False, "progress": 0, "status": "idle", "message": "No training yet."}
    try:
        with open(TRAIN_STATUS_FILE, "r", encoding="utf-8") as status_file:
            status = json.load(status_file)
        if not isinstance(status, dict):
            raise ValueError("Training status must be a JSON object.")
        return status
    except (OSError, ValueError, json.JSONDecodeError):
        app.logger.exception("Could not read training status")
        return {"running": False, "progress": 0, "status": "error", "message": "Training status file is invalid."}


def run_training():
    try:
        train_model_background(
            DB_PATH,
            lambda progress, message: write_train_status(
                {"running": True, "progress": progress, "status": "running", "message": message}
            ),
        )
        status = read_train_status()
        if status.get("running"):
            write_train_status(
                {
                    "running": False,
                    "progress": 100,
                    "status": "completed",
                    "message": status.get("message", "Training complete."),
                }
            )
    except Exception as exc:
        app.logger.exception("Model training failed")
        write_train_status(
            {"running": False, "progress": 0, "status": "error", "message": f"Training failed: {exc}"}
        )
    finally:
        training_lock.release()


init_db()
migrate_dataset_images()
initial_status = read_train_status()
if initial_status.get("running"):
    write_train_status(
        {
            "running": False,
            "progress": initial_status.get("progress", 0),
            "status": "error",
            "message": "The previous server stopped during training. Start training again.",
        }
    )


@app.before_request
def require_admin_login():
    if request.endpoint in {"login", "static"} or session.get("admin_authenticated"):
        return None
    if request.path.startswith(("/students", "/recognize_face", "/train_", "/attendance_", "/upload_face")):
        return jsonify({"error": "Authentication required."}), 401
    return redirect(url_for("login", next=request.path))


def valid_next_url(target):
    if not target or "\\" in target:
        return False
    parsed = urlsplit(target)
    return parsed.scheme == "" and parsed.netloc == "" and parsed.path.startswith("/") and not parsed.path.startswith("//")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_authenticated"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username_ok = hmac.compare_digest(
            request.form.get("username", "").encode("utf-8"),
            app.config["ADMIN_USERNAME"].encode("utf-8"),
        )
        password_ok = hmac.compare_digest(
            request.form.get("password", "").encode("utf-8"),
            app.config["ADMIN_PASSWORD"].encode("utf-8"),
        )
        if username_ok and password_ok:
            session.clear()
            session["admin_authenticated"] = True
            session.permanent = True
            next_url = request.args.get("next")
            return redirect(next_url if valid_next_url(next_url) else url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classes", methods=["GET", "POST"])
def classes_page():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        class_date = request.form.get("class_date", "").strip()
        class_time = request.form.get("class_time", "").strip()
        end_time = request.form.get("end_time", "").strip()
        faculty = request.form.get("faculty", "").strip()
        try:
            valid_date = datetime.date.fromisoformat(class_date).isoformat() == class_date
        except ValueError:
            valid_date = False
        try:
            datetime.datetime.strptime(class_time, "%H:%M")
            valid_time = True
        except ValueError:
            valid_time = False
        try:
            datetime.datetime.strptime(end_time, "%H:%M")
            valid_end_time = end_time > class_time
        except ValueError:
            valid_end_time = False
        if not name or not valid_date or not valid_time or not valid_end_time or not faculty:
            error = "Provide a class name, valid date and start/end times (end after start), and faculty."
        else:
            created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            with connect_db() as conn:
                conn.execute(
                    """INSERT INTO classes (name, class_date, class_time, end_time, faculty, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (name, class_date, class_time, end_time, faculty, created_at),
                )
            return redirect(url_for("classes_page", created=1))

    now = datetime.datetime.now()
    today = now.date().isoformat()
    with connect_db() as conn:
        classes = conn.execute(
            """SELECT c.id, c.name, c.class_date, c.class_time, c.end_time, c.faculty,
                      COUNT(DISTINCT a.student_id) AS attended_count
               FROM classes c
               LEFT JOIN attendance a
                 ON a.class_id = c.id AND date(a.timestamp) = c.class_date
               GROUP BY c.id
               ORDER BY c.id DESC""",
        ).fetchall()
    classes = [
        {
            **dict(class_item),
            "schedule_status": (
                "Past - read-only"
                if datetime.datetime.combine(
                    datetime.date.fromisoformat(class_item["class_date"]),
                    datetime.time.fromisoformat(class_item["end_time"]),
                ) <= now
                else "Attendance open"
                if datetime.datetime.combine(
                    datetime.date.fromisoformat(class_item["class_date"]),
                    datetime.time.fromisoformat(class_item["class_time"]),
                ) <= now
                else "Upcoming"
            ),
        }
        for class_item in classes
    ]
    return render_template(
        "classes.html",
        classes=classes,
        error=error,
        created=request.args.get("created") == "1",
        today=today,
    )


@app.route("/attendance_stats")
def attendance_stats():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    days = [today - datetime.timedelta(days=i) for i in range(29, -1, -1)]
    with connect_db() as conn:
        rows = conn.execute(
            """SELECT date(timestamp) AS attendance_date, COUNT(*) AS count
               FROM attendance
               WHERE date(timestamp) >= ?
               GROUP BY date(timestamp)""",
            ((today - datetime.timedelta(days=29)).isoformat(),),
        ).fetchall()
    counts_by_date = {row["attendance_date"]: row["count"] for row in rows}
    return jsonify(
        {
            "dates": [day.strftime("%d-%b") for day in days],
            "counts": [counts_by_date.get(day.isoformat(), 0) for day in days],
        }
    )


@app.route("/attendance_analysis")
def attendance_analysis():
    with connect_db() as conn:
        students = conn.execute(
            """SELECT s.id, s.name, COUNT(DISTINCT a.id) AS attendance_count
               FROM students s
               LEFT JOIN attendance a ON a.student_id = s.id
               GROUP BY s.id, s.name
               ORDER BY attendance_count DESC, s.name"""
        ).fetchall()
        classes = conn.execute(
            """SELECT c.id, c.name, c.class_date,
                      COUNT(DISTINCT a.student_id) AS attendance_count
               FROM classes c
               LEFT JOIN attendance a ON a.class_id = c.id
               GROUP BY c.id, c.name, c.class_date
               ORDER BY c.class_date, c.name, c.id"""
        ).fetchall()
    return jsonify(
        {
            "students": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "attendance_count": row["attendance_count"],
                }
                for row in students
            ],
            "classes": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "class_date": row["class_date"],
                    "attendance_count": row["attendance_count"],
                }
                for row in classes
            ],
        }
    )


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "GET":
        return render_template("add_student.html")
    data = request.form
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required."}), 400
    with connect_db() as conn:
        cursor = conn.execute(
            """INSERT INTO students (name, roll, class, section, reg_no, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                name,
                data.get("roll", "").strip(),
                data.get("class", "").strip(),
                data.get("sec", "").strip(),
                data.get("reg_no", "").strip(),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        student_id = cursor.lastrowid
    return jsonify({"student_id": student_id})


@app.route("/upload_face", methods=["POST"])
def upload_face():
    student_id = request.form.get("student_id", "")
    if not student_id.isdigit():
        return jsonify({"error": "A valid student_id is required."}), 400
    files = request.files.getlist("images[]")
    if not files or len(files) > 50:
        return jsonify({"error": "Upload between 1 and 50 face images."}), 400
    images = [uploaded_file.read() for uploaded_file in files if uploaded_file.filename]
    if not images or any(decode_image_bytes(image) is None for image in images):
        return jsonify({"error": "Upload valid webcam photos in JPEG or PNG format."}), 400
    with connect_db() as conn:
        exists = conn.execute("SELECT 1 FROM students WHERE id = ?", (int(student_id),)).fetchone()
        if not exists:
            return jsonify({"error": "Student not found."}), 404
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.executemany(
            "INSERT INTO student_faces (student_id, image, created_at) VALUES (?, ?, ?)",
            [(int(student_id), image, created_at) for image in images],
        )
    return jsonify({"saved": len(images), "storage": "database"})


@app.route("/train_model", methods=["POST"])
def train_model_route():
    if not training_lock.acquire(blocking=False):
        return jsonify({"status": "already_running"}), 202
    write_train_status({"running": True, "progress": 0, "status": "running", "message": "Starting training."})
    thread = threading.Thread(target=run_training, name="attendance-model-training", daemon=True)
    try:
        thread.start()
    except Exception:
        training_lock.release()
        write_train_status(
            {"running": False, "progress": 0, "status": "error", "message": "Could not start training."}
        )
        app.logger.exception("Could not start model training thread")
        return jsonify({"error": "Could not start training."}), 500
    return jsonify({"status": "started"}), 202


@app.route("/train_status")
def train_status():
    return jsonify(read_train_status())


@app.route("/mark_attendance")
def mark_attendance_page():
    now = datetime.datetime.now()
    with connect_db() as conn:
        classes = conn.execute(
            """SELECT c.id, c.name, c.class_date, c.class_time, c.end_time, c.faculty,
                      COUNT(DISTINCT a.student_id) AS attended_count
               FROM classes c
               LEFT JOIN attendance a
                 ON a.class_id = c.id AND date(a.timestamp) = c.class_date
               GROUP BY c.id
               ORDER BY c.name"""
        ).fetchall()
    classes = [
        {
            **dict(class_item),
            "attendance_open": (
                datetime.datetime.combine(
                    datetime.date.fromisoformat(class_item["class_date"]),
                    datetime.time.fromisoformat(class_item["class_time"]),
                )
                <= now
                < datetime.datetime.combine(
                    datetime.date.fromisoformat(class_item["class_date"]),
                    datetime.time.fromisoformat(class_item["end_time"]),
                )
            ),
        }
        for class_item in classes
    ]
    return render_template(
        "mark_attendance.html",
        classes=classes,
        has_open_class=any(class_item["attendance_open"] for class_item in classes),
    )


@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    if "image" not in request.files:
        return jsonify({"recognized": False, "error": "No image provided."}), 400
    class_id_value = request.form.get("class_id")
    if class_id_value:
        if not class_id_value.isdigit() or int(class_id_value) < 1:
            return jsonify({"recognized": False, "error": "A valid class_id is required."}), 400
        class_id = int(class_id_value)
    else:
        class_id = 0
    class_date = None
    class_end = None
    if class_id:
        with connect_db() as conn:
            class_row = conn.execute(
                "SELECT class_date, class_time, end_time FROM classes WHERE id = ?", (class_id,)
            ).fetchone()
        if class_row is None:
            return jsonify({"recognized": False, "error": "Class not found."}), 404
        now = datetime.datetime.now()
        class_date = class_row["class_date"]
        class_start = datetime.datetime.combine(
            datetime.date.fromisoformat(class_date),
            datetime.time.fromisoformat(class_row["class_time"]),
        )
        class_end = datetime.datetime.combine(
            datetime.date.fromisoformat(class_date),
            datetime.time.fromisoformat(class_row["end_time"]),
        )
        if now < class_start:
            return jsonify(
                {"recognized": False, "error": "Attendance for this class has not opened yet."}
            ), 403
        if now >= class_end:
            return jsonify(
                {
                    "recognized": False,
                    "error": "The attendance window for this class has closed.",
                    "attendance_window_closed": True,
                }
            ), 403
    try:
        embedding = extract_embedding_for_image(request.files["image"].stream)
        if embedding is None:
            return jsonify({"recognized": False, "error": "No face detected."})
        model = load_model_if_exists()
        if model is None:
            return jsonify({"recognized": False, "error": "Model not trained."}), 503
        student_id, similarity = predict_with_model(model, embedding)
        if similarity < 0.363:
            return jsonify({"recognized": False, "similarity": float(similarity)})
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        today = timestamp.date().isoformat()
        with connect_db() as conn:
            student = conn.execute("SELECT name FROM students WHERE id = ?", (int(student_id),)).fetchone()
            if student is None:
                return jsonify({"recognized": False, "error": "Recognized student no longer exists."}), 404
            if class_end is not None and datetime.datetime.now() >= class_end:
                return jsonify(
                    {
                        "recognized": False,
                        "error": "The attendance window for this class has closed.",
                        "attendance_window_closed": True,
                    }
                ), 403
            guard = conn.execute(
                """INSERT OR IGNORE INTO attendance_daily (student_id, attendance_date, class_id)
                   VALUES (?, ?, ?)""",
                (int(student_id), class_date or today, class_id),
            )
            already_marked = guard.rowcount == 0
            if not already_marked:
                conn.execute(
                    "INSERT INTO attendance (student_id, name, timestamp, class_id) VALUES (?, ?, ?, ?)",
                    (int(student_id), student["name"], timestamp.isoformat(), class_id or None),
                )
            present_count = None
            if class_id:
                present_count = conn.execute(
                    """SELECT COUNT(DISTINCT student_id) FROM attendance
                       WHERE class_id = ? AND date(timestamp) = ?""",
                    (class_id, class_date),
                ).fetchone()[0]
        return jsonify(
            {
                "recognized": True,
                "student_id": int(student_id),
                "name": student["name"],
                "similarity": float(similarity),
                "already_marked": already_marked,
                "class_id": class_id or None,
                "present_count": present_count,
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"recognized": False, "error": str(exc)}), 503
    except Exception:
        app.logger.exception("Face recognition failed")
        return jsonify({"recognized": False, "error": "Face recognition failed."}), 500


@app.route("/attendance_record")
def attendance_record():
    period = request.args.get("period", "all")
    class_id_value = request.args.get("class_id", "")
    class_id = None
    if class_id_value:
        if not class_id_value.isdigit() or int(class_id_value) < 1:
            abort(400, description="class_id must be a positive integer")
        class_id = int(class_id_value)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    query = """SELECT a.id, a.student_id, a.name, a.timestamp, c.name AS class_name
               FROM attendance a LEFT JOIN classes c ON c.id = a.class_id"""
    conditions = []
    params = []
    if period == "daily":
        conditions.append("date(a.timestamp) = ?")
        params.append(today.isoformat())
    elif period == "weekly":
        conditions.append("date(a.timestamp) >= ?")
        params.append((today - datetime.timedelta(days=7)).isoformat())
    elif period == "monthly":
        conditions.append("date(a.timestamp) >= ?")
        params.append((today - datetime.timedelta(days=30)).isoformat())
    elif period != "all":
        abort(400, description="period must be all, daily, weekly, or monthly")
    if class_id is not None:
        conditions.append("a.class_id = ?")
        params.append(class_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.timestamp DESC LIMIT 5000"
    with connect_db() as conn:
        classes = conn.execute("SELECT id, name FROM classes ORDER BY name").fetchall()
        if class_id is not None and not any(class_item["id"] == class_id for class_item in classes):
            abort(404, description="Class not found.")
        rows = conn.execute(query, params).fetchall()
    return render_template(
        "attendance_record.html",
        records=rows,
        period=period,
        classes=classes,
        selected_class_id=class_id,
    )


@app.route("/download_csv")
def download_csv():
    class_id_value = request.args.get("class_id", "")
    class_id = None
    if class_id_value:
        if not class_id_value.isdigit() or int(class_id_value) < 1:
            abort(400, description="class_id must be a positive integer")
        class_id = int(class_id_value)
    with connect_db() as conn:
        class_name = None
        if class_id is not None:
            class_row = conn.execute("SELECT name FROM classes WHERE id = ?", (class_id,)).fetchone()
            if class_row is None:
                abort(404, description="Class not found.")
            class_name = class_row["name"]
        rows = conn.execute(
            """SELECT a.id, a.student_id, a.name, a.timestamp, COALESCE(c.name, '')
               FROM attendance a LEFT JOIN classes c ON c.id = a.class_id
               WHERE (? IS NULL OR a.class_id = ?)
               ORDER BY a.timestamp DESC""",
            (class_id, class_id),
        ).fetchall()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("id", "student_id", "name", "timestamp", "class"))
    writer.writerows(tuple(row) for row in rows)
    memory = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    memory.seek(0)
    filename = f"attendance_class_{class_id}.csv" if class_name else "attendance.csv"
    return send_file(memory, as_attachment=True, download_name=filename, mimetype="text/csv")


@app.route("/students")
def students_list():
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id, name, roll, class, section, reg_no, created_at FROM students ORDER BY id DESC"
        ).fetchall()
    return jsonify(
        {
            "students": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "roll": row["roll"],
                    "class": row["class"],
                    "section": row["section"],
                    "reg_no": row["reg_no"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        }
    )


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM student_faces WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM attendance_daily WHERE student_id = ?", (student_id,))
    folder = os.path.join(DATASET_DIR, str(student_id))
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    model = load_model_if_exists()
    if model is not None:
        remaining = [(label, vector) for label, vector in zip(model["labels"], model["embeddings"]) if label != student_id]
        if remaining:
            labels, embeddings = zip(*remaining)
            temp_path = MODEL_PATH + ".tmp.npz"
            import numpy as np

            np.savez_compressed(temp_path, labels=np.asarray(labels), embeddings=np.asarray(embeddings))
            os.replace(temp_path, MODEL_PATH)
        else:
            os.remove(MODEL_PATH)
    return jsonify({"deleted": True})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1")
