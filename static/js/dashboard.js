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

  let chart = null;
  const analysisSelect = document.getElementById("attendanceAnalysisSelect");
  const chartTitle = document.getElementById("attendanceChartTitle");
  const periodSelect = document.getElementById("analysisPeriod");
  const classSelect = document.getElementById("analysisClass");
  const cohortSelect = document.getElementById("analysisCohort");
  const sectionSelect = document.getElementById("analysisSection");
  const studentSearch = document.getElementById("studentSearch");
  const studentRows = document.getElementById("studentAnalysisRows");
  let currentStudents = [];
  let chartRequest = 0;
  const chartLabels = {
    daily: "Attendance (Last 30 days)",
    students: "Student Attendance Totals",
    trends: "Student Attendance: Recent 7 Days vs Previous 7 Days",
    classes: "Attendance by Class Session"
  };

  function dashboardFilters() {
    const params = new URLSearchParams({ period: periodSelect.value });
    if (classSelect.value) params.set("class_id", classSelect.value);
    if (cohortSelect.value) params.set("cohort", cohortSelect.value);
    if (sectionSelect.value) params.set("section", sectionSelect.value);
    return params.toString();
  }

  function renderStudentRows() {
    const query = studentSearch.value.trim().toLocaleLowerCase();
    const students = currentStudents.filter(student =>
      `${student.name} ${student.roll || ""}`.toLocaleLowerCase().includes(query)
    );
    studentRows.replaceChildren();
    if (!students.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 8;
      cell.className = "text-muted";
      cell.textContent = currentStudents.length ? "No students match this search." : "No students match these filters.";
      row.appendChild(cell);
      studentRows.appendChild(row);
      return;
    }
    students.forEach(student => {
      const row = document.createElement("tr");
      const values = [
        student.roll ? `${student.name} (${student.roll})` : student.name,
        [student.cohort, student.section].filter(Boolean).join(" / ") || "—",
        student.attendance_count,
        student.sessions_attended,
        student.active_days,
        student.last_7_days,
        student.previous_7_days,
        student.last_attended || "Never"
      ];
      values.forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = String(value);
        row.appendChild(cell);
      });
      studentRows.appendChild(row);
    });
  }

  async function updateChart() {
    const requestId = ++chartRequest;
    const view = analysisSelect.value;
    const filters = dashboardFilters();
    const requests = [
      fetch(`/attendance_analysis?${filters}`).then(res => {
        if (!res.ok) throw new Error("Could not load student attendance analysis.");
        return res.json();
      })
    ];
    if (view === "daily") {
      requests.push(fetch(`/attendance_stats?${filters}`).then(res => {
        if (!res.ok) throw new Error("Could not load daily attendance.");
        return res.json();
      }));
    }
    const [data, dailyData] = await Promise.all(requests);
    if (requestId !== chartRequest) return;
    let labels;
    let datasets;
    let horizontal = false;
    if (view === "daily") {
      labels = dailyData.dates;
      datasets = [{ label: "Attendance records", data: dailyData.counts, backgroundColor: "rgba(59,130,246,0.7)" }];
    } else if (view === "students") {
      labels = data.students.slice(0, 25).map(student => student.name);
      datasets = [{
        label: "Attendance records",
        data: data.students.slice(0, 25).map(student => student.attendance_count),
        backgroundColor: "rgba(59,130,246,0.7)"
      }];
      horizontal = true;
    } else if (view === "trends") {
      const trendStudents = data.students.slice().sort((a, b) =>
        (b.last_7_days + b.previous_7_days) - (a.last_7_days + a.previous_7_days)
      ).slice(0, 25);
      labels = trendStudents.map(student => student.name);
      datasets = [
        { label: "Active days: last 7", data: trendStudents.map(student => student.last_7_days), backgroundColor: "rgba(16,185,129,0.75)" },
        { label: "Active days: prior 7", data: trendStudents.map(student => student.previous_7_days), backgroundColor: "rgba(148,163,184,0.75)" }
      ];
      horizontal = true;
    } else {
      labels = data.classes.map(item => `${item.name} (${item.class_date})`);
      datasets = [{
        label: "Students present",
        data: data.classes.map(item => item.attendance_count),
        backgroundColor: "rgba(59,130,246,0.7)"
      }];
    }
    chartTitle.textContent = view === "daily"
      ? `Attendance (${periodSelect.value === "all" ? "All time" : `Last ${periodSelect.value} days`})`
      : chartLabels[view];
    if (!chart) {
      const ctx = document.getElementById("attendanceChart").getContext("2d");
      chart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: horizontal ? "y" : "x",
          scales: { x: { beginAtZero: true, ticks: { precision: 0 } }, y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });
    } else {
      chart.data.labels = labels;
      chart.data.datasets = datasets;
      chart.options.indexAxis = horizontal ? "y" : "x";
      chart.update();
    }
    currentStudents = data.students;
    document.getElementById("studentCountMetric").textContent = data.summary.student_count;
    document.getElementById("attendanceCountMetric").textContent = data.summary.attendance_count;
    document.getElementById("sessionCountMetric").textContent = data.summary.session_count;
    renderStudentRows();
  }

  analysisSelect.addEventListener("change", () => updateChart().catch(error => console.error(error)));
  [periodSelect, classSelect, cohortSelect, sectionSelect].forEach(filter =>
    filter.addEventListener("change", () => updateChart().catch(error => console.error(error)))
  );
  studentSearch.addEventListener("input", renderStudentRows);
  updateChart().catch(error => console.error(error));
  setInterval(() => updateChart().catch(error => console.error(error)), 10000);
});
