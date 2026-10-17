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

  // Chart initial render & update every 10s
  let chart = null;
  async function updateChart() {
    const res = await fetch("/attendance_stats");
    const data = await res.json();
    const ctx = document.getElementById("attendanceChart").getContext("2d");
    if (!chart) {
      chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: data.dates,
          datasets: [{ label: "Attendance", data: data.counts, backgroundColor: "rgba(59,130,246,0.7)" }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });
    } else {
      chart.data.labels = data.dates;
      chart.data.datasets[0].data = data.counts;
      chart.update();
    }
  }
  updateChart();
  setInterval(updateChart, 10000);
});
