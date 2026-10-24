// dashboard.js
document.addEventListener("DOMContentLoaded", () => {
  const trainBtn = document.getElementById("trainBtn");
  const trainProgress = document.getElementById("trainProgress");
  const trainMsg = document.getElementById("trainMsg");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

  async function pollStatus() {
    try {
      const res = await fetch("/train_status");
      const data = await res.json();
      trainProgress.style.width = data.progress + "%";
      trainProgress.innerText = data.progress + "%";
      trainMsg.innerText = data.message || "";
      trainBtn.disabled = Boolean(data.running);
      return data;
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  trainBtn.addEventListener("click", async () => {
    trainBtn.disabled = true;
    let start;
    try {
      start = await fetch("/train_model", {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken }
      });
    } catch (error) {
      trainMsg.innerText = "Could not contact the server.";
      trainBtn.disabled = false;
      return;
    }
    if (!start.ok && start.status !== 202) {
      trainMsg.innerText = "Failed to start training.";
      trainBtn.disabled = false;
      return;
    }
    trainMsg.innerText = "Training started...";
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      const s = await pollStatus();
      if (!s || !s.running) {
        if (s && s.status === "completed") alert("Training completed");
        break;
      }
    }
  });

  pollStatus();

  // Switch between attendance views in the dashboard's single chart.
  let chart = null;
  const analysisSelect = document.getElementById("attendanceAnalysisSelect");
  const chartTitle = document.getElementById("attendanceChartTitle");
  const chartLabels = {
    daily: "Attendance (Last 30 days)",
    students: "Student-wise Attendance",
    classes: "Class-wise Attendance"
  };

  async function updateChart() {
    const view = analysisSelect.value;
    const endpoint = view === "daily" ? "/attendance_stats" : "/attendance_analysis";
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error("Could not load attendance analysis.");
    const data = await res.json();
    let labels;
    let values;
    let datasetLabel;
    let horizontal = false;
    if (view === "daily") {
      labels = data.dates;
      values = data.counts;
      datasetLabel = "Attendance";
    } else if (view === "students") {
      labels = data.students.map(student => student.name);
      values = data.students.map(student => student.attendance_count);
      datasetLabel = "Recorded attendances";
      horizontal = true;
    } else {
      labels = data.classes.map(item => `${item.name} (${item.class_date})`);
      values = data.classes.map(item => item.attendance_count);
      datasetLabel = "Students present";
    }
    chartTitle.innerText = chartLabels[view];
    if (!chart) {
      const ctx = document.getElementById("attendanceChart").getContext("2d");
      chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [{ label: datasetLabel, data: values, backgroundColor: "rgba(59,130,246,0.7)" }]
        },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: horizontal ? "y" : "x" }
      });
    } else {
      chart.data.labels = labels;
      chart.data.datasets[0].label = datasetLabel;
      chart.data.datasets[0].data = values;
      chart.options.indexAxis = horizontal ? "y" : "x";
      chart.update();
    }
  }

  analysisSelect.addEventListener("change", () => updateChart().catch(error => console.error(error)));
  updateChart().catch(error => console.error(error));
  setInterval(() => updateChart().catch(error => console.error(error)), 10000);
});
