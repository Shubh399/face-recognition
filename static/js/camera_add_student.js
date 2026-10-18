// camera_add_student.js
const saveInfoBtn = document.getElementById("saveInfoBtn");
const startCaptureBtn = document.getElementById("startCaptureBtn");
const addStudentBtn = document.getElementById("addStudentBtn");
const video = document.getElementById("video");
const captureStatus = document.getElementById("captureStatus");
const progressBar = document.getElementById("progressBar");
const detectCameraBtn = document.getElementById("detectCameraBtn");
const cameraSelect = document.getElementById("cameraSelect");

let student_id = null;
let captured = 0;
const maxImages = 50;
let images = [];
let stream = null;
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

document.getElementById("studentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const res = await fetch("/add_student", { method: "POST", body: fd });
  if (!res.ok) {
    alert("Failed to save student info");
    return;
  }
  const j = await res.json();
  student_id = j.student_id;
  captureStatus.innerText = "Student saved. Detect cameras, choose the laptop webcam, then start capture.";
  detectCameraBtn.disabled = false;
  startCaptureBtn.disabled = false;
});

detectCameraBtn.addEventListener("click", async () => {
  detectCameraBtn.disabled = true;
  try {
    const cameras = await CameraPicker.detect(cameraSelect);
    const selected = cameraSelect.selectedOptions[0]?.textContent || "selected webcam";
    captureStatus.innerText = `Found ${cameras.length} camera(s). Selected: ${selected}. Choose your laptop webcam if needed.`;
  } catch (err) {
    captureStatus.innerText = err.message || "Could not detect webcams.";
  } finally {
    detectCameraBtn.disabled = false;
  }
});

startCaptureBtn.addEventListener("click", async () => {
  startCaptureBtn.disabled = true;
  detectCameraBtn.disabled = true;
  cameraSelect.disabled = true;
  try {
    if (!cameraSelect.value) await CameraPicker.detect(cameraSelect);
    stream = await CameraPicker.open(cameraSelect);
    video.srcObject = stream;
    await video.play();
    captureImagesLoop();
  } catch (err) {
    captureStatus.innerText = err.message || "Could not open the selected webcam.";
    startCaptureBtn.disabled = false;
    detectCameraBtn.disabled = false;
    cameraSelect.disabled = false;
  }
});

async function captureImagesLoop() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");

  while (captured < maxImages) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(res => canvas.toBlob(res, "image/jpeg", 0.9));
    images.push(blob);
    captured++;
    captureStatus.innerText = `Captured ${captured} / ${maxImages}`;
    progressBar.style.width = `${(captured / maxImages) * 100}%`;
    // small visual flash
    await new Promise(r => setTimeout(r, 200));
  }

  // upload all images in one request
  const form = new FormData();
  form.append("student_id", student_id);
  images.forEach((b, i) => form.append("images[]", b, `img_${i}.jpg`));
  try {
    const resp = await fetch("/upload_face", {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: form
    });
    const result = await resp.json();
    if (!resp.ok) throw new Error(result.error || "Upload failed.");
    captureStatus.innerText = `Saved ${result.saved} photos in the database.`;
    addStudentBtn.disabled = result.saved === 0;
    cameraSelect.disabled = false;
    detectCameraBtn.disabled = false;
  } catch (err) {
    alert(err.message || "Could not save captured photos.");
  } finally {
    if (stream) stream.getTracks().forEach(t => t.stop());
  }
}

addStudentBtn.addEventListener("click", () => {
  alert("Student record complete. Returning to dashboard.");
  window.location.href = "/";
});
