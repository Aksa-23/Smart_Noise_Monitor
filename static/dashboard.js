const ctx = document.getElementById("dbChart");

const dbChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [{
      label: "dB Level",
      data: [],
      borderColor: "#34d399",
      borderWidth: 3,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: { color: "#cbd5e1" },
        grid: { color: "#334155" }
      },
      x: {
        ticks: { color: "#cbd5e1" },
        grid: { color: "#334155" }
      }
    },
    plugins: {
      legend: {
        labels: { color: "#cbd5e1" }
      }
    }
  }
});

async function fetchLiveData() {
  const res = await fetch("/api/live");
  const data = await res.json();
  const db = data.db;

  const angle = Math.min(Math.max(data.db, 0), 100) * 1.8;

  document
    .querySelector(".gauge-arc")
    .style.setProperty("--angle", angle + "deg");

  document.getElementById("dbValue").textContent = data.db;
  document.getElementById("statusBox").textContent = data.status;
  document.getElementById("statusText").textContent =
    data.status === "ALERT" ? "Noise threshold exceeded" : "Environment is under control";

  document.getElementById("timestamp").textContent = data.timestamp;
  document.getElementById("currentMode").textContent = data.mode;
  document.getElementById("threshold").textContent = data.threshold + " dB";
  document.getElementById("thresholdOnly").textContent = data.threshold;
  document.getElementById("lastUpdated").textContent = data.timestamp;

  document.getElementById("location").textContent = data.location;
  document.getElementById("deviceId").textContent = data.device_id;
  document.getElementById("deviceIp").textContent = data.device_ip;

  const statusBox = document.getElementById("statusBox");
  statusBox.className = data.status === "ALERT" ? "status alert" : "status normal";

  updateIndicator("alertCard", data.alert);
  updateIndicator("eventCard", data.event);
  updateIndicator("muteCard", data.mute);
  updateIndicator("buzzerCard", data.buzzer);

  updateModeButtons(data.mode);

  dbChart.data.labels.push(new Date().toLocaleTimeString());
  dbChart.data.datasets[0].data.push(data.db);

  if (dbChart.data.labels.length > 12) {
    dbChart.data.labels.shift();
    dbChart.data.datasets[0].data.shift();
  }

  dbChart.update();
}

function updateIndicator(id, isOn) {
  const card = document.getElementById(id);
  card.classList.toggle("on", isOn);
  card.querySelector("p").textContent = isOn ? "ON" : "OFF";
}

function updateModeButtons(mode) {
  ["Study", "Normal", "Event"].forEach(m => {
    document.getElementById("mode" + m).classList.toggle("active", m === mode);
  });
}

async function setMode(mode) {
  await fetch("/api/mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ mode })
  });

  fetchLiveData();
}

async function fetchEvents() {

  const res = await fetch("/api/events");
  const events = await res.json();

  const tbody = document.getElementById("eventTableBody");

  tbody.innerHTML = "";

  if (events.length === 0) {

    tbody.innerHTML =
      `<tr><td colspan="4">No events yet</td></tr>`;

    return;
  }

  events.forEach(event => {

    tbody.innerHTML += `
      <tr>
        <td>${event.timestamp}</td>
        <td>${event.db}</td>
        <td>${event.status}</td>
        <td>${event.event_type}</td>
      </tr>
    `;
  });
}

fetchLiveData();
setInterval(fetchLiveData, 2000);
fetchEvents();
setInterval(fetchEvents, 3000);