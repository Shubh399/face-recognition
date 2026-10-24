# Digital Facial Recognition Attendance System

## Description

A local, browser-based student attendance application built with Python, Flask, SQLite, OpenCV YuNet, and OpenCV SFace. An administrator enrolls students using a webcam, trains a face-matching model, and records attendance through live camera recognition.

This is an educational/demo application. Face recognition can produce false matches or miss a student; evaluate it carefully before using it for consequential decisions. Obtain consent before collecting biometric data.

## Features

- Admin sign-in with CSRF-protected forms and authenticated application routes.
- Student enrollment with name, roll, registration number, class, and section.
- Laptop webcam selector for enrollment and live attendance; camera selection helps avoid phone cameras linked through Windows.
- Captured enrollment images stored as image BLOBs in the local SQLite database.
- YuNet face detection and SFace embeddings for face matching.
- Background model training with visible progress and terminal success/error status.
- Live attendance with at most one attendance record per student per UTC calendar day, or per class session.
- Admin-created classes with a name, scheduled date, start and end times, faculty, and a live attendance count for the scheduled date. Class times use the server's local time.
- Server-enforced attendance windows: attendance opens at the class start time and closes at the end time. Past classes are read-only and cannot be used to mark attendance.
- Class-specific attendance tracking, so students can be counted independently in each class.
- Dashboard chart for the last 30 days, class-filtered attendance records, and class-wise or all-record CSV exports.
- Dashboard analytics showing recorded attendance totals per student and per class session.
- Deleting a student removes their profile, attendance, photos, and trained embedding.

## How the Project Works

1. **Enroll:** An administrator saves a student's details. The browser requests webcam permission and captures up to 50 JPEG frames from the selected camera. The frames are validated and saved to the `student_faces` SQLite table.
2. **Train:** The training process reads the stored photos, detects and aligns faces with YuNet, computes SFace embeddings, averages the embeddings per student, and writes the searchable model to `face_embeddings.npz`.
3. **Recognize:** The attendance page captures webcam frames and sends them to Flask. The server creates an SFace embedding and compares it with enrolled student embeddings using cosine similarity.
4. **Record attendance:** A match above the configured similarity threshold is recorded only while the selected class is in its scheduled window and only once per student per class session.
5. **Review:** The administrator views dashboard statistics, filters attendance records, or downloads them as CSV.

### Workflow

```text
Admin login
    -> Add student details
    -> Detect/select laptop webcam
    -> Capture and store student photos in SQLite
    -> Train face embeddings
    -> Create a class with its scheduled start/end times and faculty
    -> Select the class and detect/select webcam on the attendance page
    -> Recognize faces and mark attendance during the class window
    -> View or export attendance records
```

## Project Structure

```text
.
|-- app.py                       Flask routes, authentication, SQLite operations
|-- model.py                     YuNet/SFace embedding extraction and training
|-- download_models.py           Downloads the OpenCV Zoo model weights
|-- requirements.txt             Python dependencies
|-- attendance.db                Local student, attendance, and enrollment-photo data
|-- models/                      Downloaded detector and recognizer weights
|-- templates/                   Flask HTML pages
|-- static/css/                  Stylesheets
|-- static/js/                   Dashboard and webcam interaction
`-- tests/                       Automated tests
```

Generated data, secrets, downloaded weights, and virtual environments are local-only and excluded from Git. Student images are sensitive biometric data; protect database backups and set an appropriate retention policy.

## Tests

### Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## How to Run

### First-time setup (Windows PowerShell)

From this project directory, create the virtual environment, install dependencies, and download face-model weights:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_models.py
```

Create a private `.env` file in the project directory. Use an admin password of at least 12 characters and create a fresh secret key:

```powershell
$secret = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
@"
ADMIN_USERNAME=admin
ADMIN_PASSWORD=replace-with-a-private-password-at-least-12-characters
SECRET_KEY=$secret
"@ | Set-Content -Encoding ascii .env
```

Keep `.env` private; it is ignored by Git. Do not use a demo password for any network-accessible deployment.

### Start the app

Whenever you want to run the app, from this project directory execute:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000> in the browser and sign in with the credentials in `.env`. Stop the server with **Ctrl+C**. On the dashboard, add students and train the model before using **Mark Attendance**. At enrollment and attendance, select **Detect cameras**, grant camera permission, then choose the laptop's integrated/built-in webcam rather than a device labeled Phone, Mobile, or Link to Windows.

The app currently has one administrator account; it does not implement separate teacher or student accounts. Keep the development server bound to localhost. A network deployment requires HTTPS, a production server, secure cookies, stronger account management, and a reviewed privacy/security policy.
