// camera_mark.js
const startMarkBtn = document.getElementById("startMarkBtn");
const stopMarkBtn = document.getElementById("stopMarkBtn");
const markVideo = document.getElementById("markVideo");
const markStatus = document.getElementById("markStatus");
const recognizedList = document.getElementById("recognizedList");
const detectMarkCameraBtn = document.getElementById("detectMarkCameraBtn");
const markCameraSelect = document.getElementById("markCameraSelect");

let markStream = null;
let scanning = false;
let recognizedIds = new Set();
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

detectMarkCameraBtn.addEventListener("click", async () => {
  detectMarkCameraBtn.disabled = true;
  try {
    const cameras = await CameraPicker.detect(markCameraSelect);
    const selected = markCameraSelect.selectedOptions[0]?.textContent || "selected webcam";
    markStatus.innerText = `Found ${cameras.length} camera(s). Selected: ${selected}. Choose your laptop webcam if needed.`;
  } catch (err) {
    markStatus.innerText = err.message || "Could not detect webcams.";
  } finally {
    detectMarkCameraBtn.disabled = false;
  }
});

markCameraSelect.addEventListener("change", async () => {
  if (!scanning) return;
  try {
    const nextStream = await CameraPicker.open(markCameraSelect);
    const previousStream = markStream;
    markStream = nextStream;
    markVideo.srcObject = nextStream;
    await markVideo.play();
    if (previousStream) previousStream.getTracks().forEach(track => track.stop());
    markStatus.innerText = "Switched webcam. Scanning...";
  } catch (err) {
    markStatus.innerText = err.message || "Could not switch webcams.";
  }
});

startMarkBtn.addEventListener("click", async () => {
  startMarkBtn.disabled = true;
  stopMarkBtn.disabled = false;
  try {
    if (!markCameraSelect.value) await CameraPicker.detect(markCameraSelect);
    markStream = await CameraPicker.open(markCameraSelect);
    markVideo.srcObject = markStream;
    await markVideo.play();
    scanning = true;
    markStatus.innerText = "Scanning...";
    captureAndRecognize();
  } catch (err) {
    alert("Camera error: " + err.message);
    startMarkBtn.disabled = false;
    stopMarkBtn.disabled = true;
  }
});

stopMarkBtn.addEventListener("click", () => {
  scanning = false;
  if (markStream) markStream.getTracks().forEach(t => t.stop());
  startMarkBtn.disabled = false;
  stopMarkBtn.disabled = true;
  markStatus.innerText = "Stopped";
});

async function captureAndRecognize() {
  if (!scanning) return;
  const canvas = document.createElement("canvas");
  canvas.width = markVideo.videoWidth || 640;
  canvas.height = markVideo.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(markVideo, 0, 0, canvas.width, canvas.height);
  try {
    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.85));
    if (!blob) throw new Error("Could not capture a camera frame.");
    const fd = new FormData();
    fd.append("image", blob, "snap.jpg");
    const res = await fetch("/recognize_face", {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: fd
    });
    const j = await res.json();
    if (j.recognized) {
      markStatus.innerText = j.already_marked
        ? `${j.name} is already marked present today`
        : `Attendance marked: ${j.name} (similarity ${j.similarity.toFixed(2)})`;
      if (!recognizedIds.has(j.student_id)) {
        recognizedIds.add(j.student_id);
        const li = document.createElement("li");
        li.className = "list-group-item";
        li.innerText = `${j.name} — ${new Date().toLocaleTimeString()}`;
        recognizedList.prepend(li);
      }
    } else {
      if (j.error) markStatus.innerText = `Not recognized: ${j.error}`;
      else markStatus.innerText = `Not recognized`;
    }
  } catch (err) {
    markStatus.innerText = err.message || "Recognition request failed.";
  } finally {
    if (scanning) setTimeout(captureAndRecognize, 1200);
  }
}
