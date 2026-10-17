import io
import os
import sqlite3
import threading

import cv2
import numpy as np
import pytest

os.environ.setdefault("SECRET_KEY", "test-session-key-that-is-long-enough")
os.environ.setdefault("ADMIN_USERNAME", "test-admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-password-long-enough")

import app as attendance_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(attendance_app, "DB_PATH", str(tmp_path / "attendance.db"))
    monkeypatch.setattr(attendance_app, "DATASET_DIR", str(tmp_path / "dataset"))
    monkeypatch.setattr(attendance_app, "TRAIN_STATUS_FILE", str(tmp_path / "train_status.json"))
    attendance_app.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ADMIN_USERNAME="test-admin",
        ADMIN_PASSWORD="test-password-long-enough",
    )
    attendance_app.training_lock = threading.Lock()
    attendance_app.init_db()
    with attendance_app.app.test_client() as test_client:
        yield test_client


def login(client):
    return client.post(
        "/login",
        data={"username": "test-admin", "password": "test-password-long-enough"},
    )


def test_admin_login_protects_pages_and_apis(client):
    assert client.get("/").status_code == 302
    assert client.get("/students").status_code == 401
    assert login(client).status_code == 302
    assert client.get("/").status_code == 200
    assert client.get("/students").status_code == 200


def test_student_enrollment_and_face_upload(client):
    login(client)
    response = client.post(
        "/add_student",
        data={"name": "Ada Lovelace", "roll": "42", "class": "CS", "sec": "A", "reg_no": "R-42"},
    )
    assert response.status_code == 200
    student_id = response.json["student_id"]

    ok, encoded = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
    assert ok
    image_bytes = encoded.tobytes()
    upload = client.post(
        "/upload_face",
        data={
            "student_id": str(student_id),
            "images[]": [
                (io.BytesIO(image_bytes), "first.jpg"),
                (io.BytesIO(image_bytes), "second.jpg"),
            ],
        },
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    assert upload.json == {"saved": 2, "storage": "database"}
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        rows = conn.execute(
            "SELECT image FROM student_faces WHERE student_id = ? ORDER BY id", (student_id,)
        ).fetchall()
    assert [row[0] for row in rows] == [image_bytes, image_bytes]
    assert not os.path.exists(os.path.join(attendance_app.DATASET_DIR, str(student_id)))
    students = client.get("/students").json["students"]
    assert students[0]["name"] == "Ada Lovelace"
    assert students[0]["roll"] == "42"


def test_face_upload_rejects_unknown_student(client):
    login(client)
    ok, encoded = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
    assert ok
    response = client.post(
        "/upload_face",
        data={"student_id": "999", "images[]": (io.BytesIO(encoded.tobytes()), "face.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 404
    assert response.json["error"] == "Student not found."


def test_face_upload_rejects_invalid_image_bytes(client):
    login(client)
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        student_id = conn.execute("INSERT INTO students (name) VALUES (?)", ("Ada",)).lastrowid
    response = client.post(
        "/upload_face",
        data={"student_id": str(student_id), "images[]": (io.BytesIO(b"not an image"), "face.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM student_faces").fetchone()[0] == 0


def test_legacy_face_files_migrate_to_database(client, tmp_path):
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        student_id = conn.execute("INSERT INTO students (name) VALUES (?)", ("Ada",)).lastrowid
    folder = tmp_path / "dataset" / str(student_id)
    folder.mkdir(parents=True)
    ok, encoded = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
    assert ok
    image_path = folder / "legacy.jpg"
    image_path.write_bytes(encoded.tobytes())

    attendance_app.migrate_dataset_images()

    assert not image_path.exists()
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        image = conn.execute("SELECT image FROM student_faces WHERE student_id = ?", (student_id,)).fetchone()[0]
    assert image == encoded.tobytes()


def test_deleting_student_removes_database_photos(client):
    login(client)
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        student_id = conn.execute("INSERT INTO students (name) VALUES (?)", ("Ada",)).lastrowid
        conn.execute(
            "INSERT INTO student_faces (student_id, image, created_at) VALUES (?, ?, ?)",
            (student_id, b"stored image", "2026-01-01T00:00:00+00:00"),
        )

    response = client.delete(f"/students/{student_id}")

    assert response.status_code == 200
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM student_faces").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0


def test_recognition_records_attendance_once_per_utc_day(client, monkeypatch):
    login(client)
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        cursor = conn.execute("INSERT INTO students (name) VALUES (?)", ("Ada",))
        student_id = cursor.lastrowid

    monkeypatch.setattr(attendance_app, "extract_embedding_for_image", lambda stream: [0.1, 0.2])
    monkeypatch.setattr(attendance_app, "load_model_if_exists", lambda: object())
    monkeypatch.setattr(attendance_app, "predict_with_model", lambda model, embedding: (student_id, 0.9))

    def recognize():
        return client.post(
            "/recognize_face",
            data={"image": (io.BytesIO(b"test image"), "face.jpg")},
            content_type="multipart/form-data",
        )

    first = recognize()
    second = recognize()
    assert first.status_code == 200
    assert first.json["recognized"] is True
    assert first.json["already_marked"] is False
    assert second.status_code == 200
    assert second.json["already_marked"] is True
    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 1


def test_training_reads_face_images_from_database(client, monkeypatch, tmp_path):
    import model as face_model

    with sqlite3.connect(attendance_app.DB_PATH) as conn:
        student_id = conn.execute("INSERT INTO students (name) VALUES (?)", ("Ada",)).lastrowid
        conn.execute(
            "INSERT INTO student_faces (student_id, image, created_at) VALUES (?, ?, ?)",
            (student_id, b"encoded image", "2026-01-01T00:00:00+00:00"),
        )
    monkeypatch.setattr(face_model, "MODEL_PATH", str(tmp_path / "trained.npz"))
    monkeypatch.setattr(face_model, "create_face_models", lambda: (object(), object()))
    monkeypatch.setattr(
        face_model, "decode_image_bytes", lambda image_bytes: np.zeros((32, 32, 3), dtype=np.uint8)
    )
    monkeypatch.setattr(face_model, "embedding_from_image", lambda image, detector, recognizer: np.array([1.0, 0.0]))

    face_model.train_model_background(attendance_app.DB_PATH)

    with np.load(tmp_path / "trained.npz", allow_pickle=False) as trained:
        assert trained["labels"].tolist() == [student_id]
        assert trained["embeddings"].shape == (1, 2)


def test_training_finishes_with_terminal_status(client, monkeypatch):
    def successful_training(dataset_dir, callback):
        callback(100, "Training complete.")

    monkeypatch.setattr(attendance_app, "train_model_background", successful_training)
    attendance_app.training_lock.acquire()
    attendance_app.write_train_status(
        {"running": True, "progress": 0, "status": "running", "message": "Starting training."}
    )

    attendance_app.run_training()

    status = attendance_app.read_train_status()
    assert status["running"] is False
    assert status["status"] == "completed"


def test_training_failure_is_reported_and_lock_released(client, monkeypatch):
    def failed_training(dataset_dir, callback):
        raise ValueError("No usable faces")

    monkeypatch.setattr(attendance_app, "train_model_background", failed_training)
    attendance_app.training_lock.acquire()
    attendance_app.write_train_status(
        {"running": True, "progress": 0, "status": "running", "message": "Starting training."}
    )

    attendance_app.run_training()

    status = attendance_app.read_train_status()
    assert status["running"] is False
    assert status["status"] == "error"
    assert "No usable faces" in status["message"]
    assert attendance_app.training_lock.acquire(blocking=False)
    attendance_app.training_lock.release()
