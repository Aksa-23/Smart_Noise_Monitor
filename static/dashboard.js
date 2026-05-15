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

let lastLoggedStatus = "NORMAL";
let alertHistory = [];

async function fetchLiveData() {
  try {
    const res = await fetch("/api/live");
    const data = await res.json();

    const db = Number(data.db || 0);
    const angle = Math.min(Math.max(db, 0), 100) * 1.8;

    document
      .querySelector(".gauge-arc")
      .style.setProperty("--angle", angle + "deg");

    document.getElementById("dbValue").textContent = db.toFixed(2);
    document.getElementById("statusBox").textContent = data.status;
    document.getElementById("timestamp").textContent = data.timestamp;
    document.getElementById("currentMode").textContent = data.mode;
    document.getElementById("threshold").textContent = data.threshold + " dB";
    document.getElementById("thresholdOnly").textContent = data.threshold;
    document.getElementById("lastUpdated").textContent = data.timestamp;
    document.getElementById("location").textContent = data.location;
    document.getElementById("deviceId").textContent = data.device_id;
    document.getElementById("deviceIp").textContent = data.device_ip;

    updateStatusText(data);
    updateStatusStyle(data.status);

    updateIndicator("alertCard", data.alert);
    updateIndicator("eventCard", data.event);
    updateIndicator("muteCard", data.mute);
    updateIndicator("buzzerCard", data.buzzer);

    updateModeButtons(data.mode);
    updateChart(db);

    maybeAddAlertHistory(data);

  } catch (error) {
    console.error("Failed to fetch live data:", error);
  }
}

function updateStatusText(data) {
  const statusText = document.getElementById("statusText");

  if (data.status === "MANUAL_ALERT") {
    statusText.textContent = "Manual alert triggered";
  } else if (data.status === "ALERT") {
    statusText.textContent = "Noise threshold exceeded";
  } else if (data.status === "MUTED") {
    statusText.textContent = "Alert muted";
  } else {
    statusText.textContent = "Environment is under control";
  }
}

function updateStatusStyle(status) {
  const statusBox = document.getElementById("statusBox");

  if (status === "ALERT" || status === "MANUAL_ALERT") {
    statusBox.className = "status alert";
  } else {
    statusBox.className = "status normal";
  }
}

function updateIndicator(id, isOn) {
  const card = document.getElementById(id);

  if (!card) {
    return;
  }

  card.classList.toggle("on", Boolean(isOn));

  const label = card.querySelector("p");
  if (label) {
    label.textContent = isOn ? "ON" : "OFF";
  }

  const smallText = card.querySelector("small");
  if (smallText) {
    if (id === "alertCard") {
      smallText.textContent = isOn ? "Alert Active" : "No Alert";
    } else if (id === "eventCard") {
      smallText.textContent = isOn ? "Event Active" : "No Event";
    } else if (id === "muteCard") {
      smallText.textContent = isOn ? "Sound Muted" : "Sound Enabled";
    } else if (id === "buzzerCard") {
      smallText.textContent = isOn ? "Buzzer On" : "Buzzer Off";
    }
  }
}

function updateModeButtons(mode) {
  ["Study", "Normal", "Event"].forEach(m => {
    const button = document.getElementById("mode" + m);

    if (button) {
      button.classList.toggle("active", m === mode);
    }
  });
}

function updateChart(db) {
  dbChart.data.labels.push(new Date().toLocaleTimeString());
  dbChart.data.datasets[0].data.push(db);

  if (dbChart.data.labels.length > 12) {
    dbChart.data.labels.shift();
    dbChart.data.datasets[0].data.shift();
  }

  dbChart.update();
}

function maybeAddAlertHistory(data) {
  const isAlertEvent =
    data.status === "ALERT" ||
    data.status === "MANUAL_ALERT" ||
    data.event === true;

  if (isAlertEvent && lastLoggedStatus !== data.status) {
    addAlertHistory(data);
    lastLoggedStatus = data.status;
  }

  if (!isAlertEvent) {
    lastLoggedStatus = "NORMAL";
  }
}

function addAlertHistory(data) {
  const tbody = document.getElementById("eventTableBody");

  if (!tbody) {
    return;
  }

  const existingEmptyRow = tbody.querySelector("td[colspan='4']");
  if (existingEmptyRow) {
    tbody.innerHTML = "";
  }

  const db = Number(data.db || 0).toFixed(2);
  const time = data.timestamp || new Date().toLocaleTimeString();

  let eventType = "Noise Alert";

  if (data.status === "MANUAL_ALERT" || data.event === true) {
    eventType = "Manual Alert";
  } else if (data.status === "MUTED") {
    eventType = "Muted Alert";
  }

  const row = document.createElement("tr");

  row.innerHTML = `
        <td>${time}</td>
        <td>${db}</td>
        <td>${data.status}</td>
        <td>${eventType}</td>
    `;

  tbody.prepend(row);

  alertHistory.unshift({
    time: time,
    db: db,
    status: data.status,
    eventType: eventType
  });

  while (tbody.children.length > 10) {
    tbody.removeChild(tbody.lastChild);
  }
}

async function setMode(mode) {
  try {
    await fetch("/api/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode })
    });

    fetchLiveData();

  } catch (error) {
    console.error("Failed to set mode:", error);
  }
}

fetchLiveData();
setInterval(fetchLiveData, 2000);