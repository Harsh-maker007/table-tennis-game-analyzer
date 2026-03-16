const analyzeBtn = document.getElementById("analyzeBtn");
const videoFile = document.getElementById("videoFile");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const tableViz = document.getElementById("tableViz");
const playerFilter = document.getElementById("playerFilter");
const resultFilter = document.getElementById("resultFilter");
const totalShotsEl = document.getElementById("totalShots");
const successRateEl = document.getElementById("successRate");
const bestZoneEl = document.getElementById("bestZone");
const weakZoneEl = document.getElementById("weakZone");
const leftPctEl = document.getElementById("leftPct");
const rightPctEl = document.getElementById("rightPct");
const zonesGrid = document.getElementById("zonesGrid");
const eventsBody = document.getElementById("eventsBody");
const handsViz = document.getElementById("handsViz");
const feetViz = document.getElementById("feetViz");
const handLeftSpeed = document.getElementById("handLeftSpeed");
const handRightSpeed = document.getElementById("handRightSpeed");
const handLeftAngle = document.getElementById("handLeftAngle");
const handRightAngle = document.getElementById("handRightAngle");
const footLeftSpeed = document.getElementById("footLeftSpeed");
const footRightSpeed = document.getElementById("footRightSpeed");
const footLeftAngle = document.getElementById("footLeftAngle");
const footRightAngle = document.getElementById("footRightAngle");
const shotBody = document.getElementById("shotBody");
const strokeServe = document.getElementById("strokeServe");
const strokeReceive = document.getElementById("strokeReceive");
const strokeAttack = document.getElementById("strokeAttack");
const strokeDefence = document.getElementById("strokeDefence");
const strokeTransition = document.getElementById("strokeTransition");
const strokeTitle = document.getElementById("strokeTitle");
const strokeChain = document.getElementById("strokeChain");
const metricPlane = document.getElementById("metricPlane");
const metricWrist = document.getElementById("metricWrist");
const metricArm = document.getElementById("metricArm");
const metricSpin = document.getElementById("metricSpin");
const strokeCue = document.getElementById("strokeCue");

const API_BASE = window.API_BASE || "http://127.0.0.1:8000";
const API_URL = `${API_BASE}/analyze`;
let lastData = null;

analyzeBtn.addEventListener("click", async () => {
  if (!videoFile.files.length) {
    statusEl.textContent = "Select a video first.";
    return;
  }

  statusEl.textContent = "Uploading and analyzing...";
  const formData = new FormData();
  formData.append("video", videoFile.files[0]);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    lastData = data;
    resultsEl.textContent = JSON.stringify(data, null, 2);
    statusEl.textContent = "Analysis complete.";
    renderSummary(data);
    renderZones(data);
    renderTable(data);
    renderEvents(data);
    renderMovement(data);
    renderShotStats(data);
  } catch (err) {
    statusEl.textContent = "Failed to analyze video.";
  }
});

playerFilter.addEventListener("change", () => {
  if (lastData) {
    renderTable(lastData);
    renderEvents(lastData);
  }
});

resultFilter.addEventListener("change", () => {
  if (lastData) {
    renderTable(lastData);
    renderEvents(lastData);
  }
});

function renderSummary(data) {
  totalShotsEl.textContent = data.total_shots ?? 0;
  const sr = typeof data.success_rate === "number" ? data.success_rate : 0;
  successRateEl.textContent = `${sr.toFixed(1)}%`;
  bestZoneEl.textContent = data.best_zone ?? "-";
  weakZoneEl.textContent = data.weak_zone ?? "-";
  leftPctEl.textContent = `${(data.movement?.left_pct ?? 0).toFixed(1)}%`;
  rightPctEl.textContent = `${(data.movement?.right_pct ?? 0).toFixed(1)}%`;
}

function renderZones(data) {
  const zones = data.zones || {};
  const keys = Object.keys(zones);
  if (!keys.length) {
    zonesGrid.innerHTML = "<div class=\"zone-cell\">No zones yet.</div>";
    return;
  }
  zonesGrid.innerHTML = keys
    .sort()
    .map(
      (key) =>
        `<div class="zone-cell"><span class="zone-label">${key}</span><span class="zone-value">${zones[key]}</span></div>`
    )
    .join("");
}

function renderTable(data) {
  const events = Array.isArray(data.events) ? data.events : [];
  const filtered = events.filter((e) => {
    const playerOk =
      playerFilter.value === "all" || e.player === playerFilter.value;
    const resultOk =
      resultFilter.value === "all" || e.result === resultFilter.value;
    return playerOk && resultOk;
  });

  const svgWidth = 640;
  const svgHeight = 360;
  const cols = 3;
  const rows = 3;
  const cellW = svgWidth / cols;
  const cellH = svgHeight / rows;

  const dots = filtered
    .map((e) => {
      const x = Math.max(0, Math.min(1, e.x)) * svgWidth;
      const y = Math.max(0, Math.min(1, e.y)) * svgHeight;
      const color =
        e.result === "win"
          ? "#22c55e"
          : e.result === "loss"
          ? "#ef4444"
          : "#38bdf8";
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(
        1
      )}" r="6" fill="${color}" opacity="0.9" />`;
    })
    .join("");

  let labels = "";
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const label = `${String.fromCharCode(65 + r)}${c + 1}`;
      const lx = c * cellW + 10;
      const ly = r * cellH + 20;
      labels += `<text x="${lx}" y="${ly}" font-size="12" fill="#d1d5db">${label}</text>`;
    }
  }

  const svg = `
    <svg viewBox="0 0 ${svgWidth} ${svgHeight}" width="100%" height="100%">
      <rect x="0" y="0" width="${svgWidth}" height="${svgHeight}" fill="#0c2026"/>
      <line x1="0" y1="${cellH}" x2="${svgWidth}" y2="${cellH}" stroke="#2b5d66" />
      <line x1="0" y1="${cellH * 2}" x2="${svgWidth}" y2="${cellH * 2}" stroke="#2b5d66" />
      <line x1="${cellW}" y1="0" x2="${cellW}" y2="${svgHeight}" stroke="#2b5d66" />
      <line x1="${cellW * 2}" y1="0" x2="${cellW * 2}" y2="${svgHeight}" stroke="#2b5d66" />
      <line x1="0" y1="${svgHeight / 2}" x2="${svgWidth}" y2="${svgHeight / 2}" stroke="#97b4b8" stroke-dasharray="6 6" />
      <text x="${svgWidth / 2 - 12}" y="${svgHeight / 2 - 8}" font-size="12" fill="#9ca3af">Net</text>
      ${labels}
      ${dots}
    </svg>
  `;
  tableViz.innerHTML = svg;
}

function renderEvents(data) {
  const events = Array.isArray(data.events) ? data.events : [];
  const filtered = events.filter((e) => {
    const playerOk =
      playerFilter.value === "all" || e.player === playerFilter.value;
    const resultOk =
      resultFilter.value === "all" || e.result === resultFilter.value;
    return playerOk && resultOk;
  });

  if (!filtered.length) {
    eventsBody.innerHTML =
      "<div class=\"events-row\"><span>-</span><span>-</span><span>-</span><span>-</span></div>";
    return;
  }

  eventsBody.innerHTML = filtered
    .slice(0, 200)
    .map((e) => {
      const badge = `<span class="badge ${e.result}">${e.result}</span>`;
      return `<div class="events-row">
        <span>${e.frame ?? "-"}</span>
        <span>${e.player ?? "-"}</span>
        <span>${badge}</span>
        <span>${e.zone ?? "-"}</span>
      </div>`;
    })
    .join("");
}

function renderMovement(data) {
  const hands = data.movement?.hands || {};
  const feet = data.movement?.feet || {};

  handLeftSpeed.textContent = `${(hands.left_speed ?? 0).toFixed(2)} km/h`;
  handRightSpeed.textContent = `${(hands.right_speed ?? 0).toFixed(2)} km/h`;
  handLeftAngle.textContent = `${(hands.left_angle ?? 0).toFixed(0)} deg`;
  handRightAngle.textContent = `${(hands.right_angle ?? 0).toFixed(0)} deg`;

  footLeftSpeed.textContent = `${(feet.left_speed ?? 0).toFixed(2)} km/h`;
  footRightSpeed.textContent = `${(feet.right_speed ?? 0).toFixed(2)} km/h`;
  footLeftAngle.textContent = `${(feet.left_angle ?? 0).toFixed(0)} deg`;
  footRightAngle.textContent = `${(feet.right_angle ?? 0).toFixed(0)} deg`;

  handsViz.innerHTML = renderMovementWave(hands.left || [], hands.right || []);
  feetViz.innerHTML = renderMovementDots(feet.left || [], feet.right || []);
}

function renderShotStats(data) {
  const stats = data.shot_type_stats || {};
  const keys = Object.keys(stats);
  if (!keys.length) {
    shotBody.innerHTML =
      "<div class=\"shot-row\"><span>-</span><span>-</span></div>";
    return;
  }
  shotBody.innerHTML = keys
    .sort()
    .map((k) => {
      const s = stats[k];
      const overall = s.overall || { total: 0 };
      const total = overall.total || 0;
      return `<div class="shot-row">
        <span>${k}</span>
        <span>${total}</span>
      </div>`;
    })
    .join("");
}

function renderMovementWave(leftPoints, rightPoints) {
  const width = 520;
  const height = 240;

  const left = [...(leftPoints || [])].sort((a, b) => a.frame - b.frame);
  const right = [...(rightPoints || [])].sort((a, b) => a.frame - b.frame);

  const leftPath = left
    .map((p, i) => {
      const x = (i / Math.max(1, left.length - 1)) * width;
      const y = p.y * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const rightPath = right
    .map((p, i) => {
      const x = (i / Math.max(1, right.length - 1)) * width;
      const y = p.y * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="100%">
      <rect x="0" y="0" width="${width}" height="${height}" fill="#0f131a" />
      <polyline points="${leftPath}" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8"/>
      <polyline points="${rightPath}" fill="none" stroke="#22c55e" stroke-width="2" opacity="0.8"/>
    </svg>
  `;
}

function renderMovementDots(leftPoints, rightPoints) {
  const width = 520;
  const height = 240;
  const leftDots = (leftPoints || [])
    .map(
      (p) =>
        `<circle cx="${(p.x * width).toFixed(1)}" cy="${(p.y * height).toFixed(
          1
        )}" r="3" fill="#38bdf8" opacity="0.6" />`
    )
    .join("");
  const rightDots = (rightPoints || [])
    .map(
      (p) =>
        `<circle cx="${(p.x * width).toFixed(1)}" cy="${(p.y * height).toFixed(
          1
        )}" r="3" fill="#22c55e" opacity="0.6" />`
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="100%">
      <rect x="0" y="0" width="${width}" height="${height}" fill="#0f131a" />
      ${leftDots}
      ${rightDots}
    </svg>
  `;
}

const strokeLibrary = {
  Serve: [
    {
      name: "Pendulum",
      plane: "Diagonal",
      wrist: "35 deg",
      arm: "Forearm + wrist",
      spin: "Side-topspin",
      cue: "Load low, brush across the back-right of the ball.",
    },
    {
      name: "Reverse pendulum",
      plane: "Diagonal",
      wrist: "40 deg",
      arm: "Forearm + wrist",
      spin: "Reverse sidespin",
      cue: "Lead with the wrist and finish across your body.",
    },
    {
      name: "Fast topspin",
      plane: "Forward",
      wrist: "22 deg",
      arm: "Shoulder + forearm",
      spin: "Topspin",
      cue: "Compact toss, accelerate through contact.",
    },
    {
      name: "No-spin ghost",
      plane: "Flat",
      wrist: "5 deg",
      arm: "Forearm",
      spin: "No-spin",
      cue: "Match the toss to a heavy-spin serve, then deaden.",
    },
    {
      name: "Backspin short",
      plane: "Downward",
      wrist: "28 deg",
      arm: "Forearm + wrist",
      spin: "Backspin",
      cue: "Brush under the ball, keep the bounce short.",
    },
  ],
  Receive: [
    {
      name: "Push",
      plane: "Downward",
      wrist: "10 deg",
      arm: "Forearm",
      spin: "Backspin",
      cue: "Soft hands, keep it low and short.",
    },
    {
      name: "Flick",
      plane: "Upward",
      wrist: "35 deg",
      arm: "Wrist + forearm",
      spin: "Topspin",
      cue: "Contact early over the table, snap up.",
    },
    {
      name: "Loop receive",
      plane: "Forward",
      wrist: "18 deg",
      arm: "Shoulder + forearm",
      spin: "Topspin",
      cue: "Open the racket and lift through the ball.",
    },
    {
      name: "Chop receive",
      plane: "Downward",
      wrist: "20 deg",
      arm: "Forearm",
      spin: "Heavy backspin",
      cue: "Long stroke, finish low.",
    },
  ],
  Attack: [
    {
      name: "FH topspin loop",
      plane: "Forward",
      wrist: "18 deg",
      arm: "Shoulder + forearm",
      spin: "Topspin",
      cue: "Load legs, brush up and forward.",
    },
    {
      name: "BH topspin loop",
      plane: "Forward",
      wrist: "22 deg",
      arm: "Forearm + wrist",
      spin: "Topspin",
      cue: "Compact swing, accelerate through contact.",
    },
    {
      name: "FH smash",
      plane: "Flat",
      wrist: "8 deg",
      arm: "Shoulder",
      spin: "No-spin",
      cue: "Hit through the ball, keep it down.",
    },
    {
      name: "BH smash",
      plane: "Flat",
      wrist: "10 deg",
      arm: "Forearm",
      spin: "No-spin",
      cue: "Short punch, square contact.",
    },
    {
      name: "FH flick",
      plane: "Upward",
      wrist: "30 deg",
      arm: "Wrist",
      spin: "Topspin",
      cue: "Explode from the wrist, quick recovery.",
    },
    {
      name: "BH flick",
      plane: "Upward",
      wrist: "32 deg",
      arm: "Wrist",
      spin: "Topspin",
      cue: "Take it off the bounce, snap up.",
    },
  ],
  Defence: [
    {
      name: "FH chop",
      plane: "Downward",
      wrist: "22 deg",
      arm: "Forearm",
      spin: "Backspin",
      cue: "Long, relaxed stroke to generate spin.",
    },
    {
      name: "BH chop",
      plane: "Downward",
      wrist: "18 deg",
      arm: "Forearm",
      spin: "Backspin",
      cue: "Angle the bat, absorb and brush.",
    },
    {
      name: "FH block",
      plane: "Flat",
      wrist: "6 deg",
      arm: "Forearm",
      spin: "Neutral",
      cue: "Stable racket, use the opponent's pace.",
    },
    {
      name: "BH block",
      plane: "Flat",
      wrist: "6 deg",
      arm: "Forearm",
      spin: "Neutral",
      cue: "Short stroke, close the angle.",
    },
    {
      name: "Lob",
      plane: "Upward",
      wrist: "16 deg",
      arm: "Shoulder",
      spin: "Topspin",
      cue: "Lift high with heavy spin for depth.",
    },
  ],
  Transition: [
    {
      name: "FH counter-loop",
      plane: "Forward",
      wrist: "20 deg",
      arm: "Shoulder + forearm",
      spin: "Topspin",
      cue: "Meet the ball early, forward acceleration.",
    },
    {
      name: "BH counter-loop",
      plane: "Forward",
      wrist: "24 deg",
      arm: "Forearm + wrist",
      spin: "Topspin",
      cue: "Compact swing, quick snap through contact.",
    },
    {
      name: "FH drive",
      plane: "Flat",
      wrist: "12 deg",
      arm: "Shoulder + forearm",
      spin: "Light topspin",
      cue: "Drive forward, keep it low.",
    },
    {
      name: "BH drive",
      plane: "Flat",
      wrist: "12 deg",
      arm: "Forearm",
      spin: "Light topspin",
      cue: "Short stroke, controlled pace.",
    },
  ],
};

function renderStrokeLibrary() {
  const groups = [
    ["Serve", strokeServe],
    ["Receive", strokeReceive],
    ["Attack", strokeAttack],
    ["Defence", strokeDefence],
    ["Transition", strokeTransition],
  ];

  groups.forEach(([key, container]) => {
    container.innerHTML = strokeLibrary[key]
      .map((s, idx) => {
        return `<div class="stroke-item" data-group="${key}" data-idx="${idx}">${s.name}</div>`;
      })
      .join("");
  });

  document.querySelectorAll(".stroke-item").forEach((el) => {
    el.addEventListener("click", () => {
      document
        .querySelectorAll(".stroke-item")
        .forEach((x) => x.classList.remove("active"));
      el.classList.add("active");
      const group = el.getAttribute("data-group");
      const idx = parseInt(el.getAttribute("data-idx"), 10);
      const stroke = strokeLibrary[group][idx];
      strokeTitle.textContent = stroke.name;
      strokeChain.textContent =
        "Backswing load -> Drive arc -> Wrist snap -> Follow-through";
      metricPlane.textContent = stroke.plane;
      metricWrist.textContent = stroke.wrist;
      metricArm.textContent = stroke.arm;
      metricSpin.textContent = stroke.spin;
      strokeCue.textContent = stroke.cue;
    });
  });
}

renderStrokeLibrary();
