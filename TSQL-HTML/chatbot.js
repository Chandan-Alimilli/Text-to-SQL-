document.addEventListener("DOMContentLoaded", () => {
  if (window.Chart) {
    console.log("✅ Chart.js is available");
    window.chartJsReady = true;
    Chart.register(
      Chart.BarController,
      Chart.PieController,
      Chart.LinearScale,
      Chart.CategoryScale,
      Chart.PointElement,
      Chart.BarElement,
      Chart.ArcElement
    );
  } else {
    console.log("❌ Chart.js not available");
    window.chartJsReady = false;
  }

  const input = document.getElementById("user-input");
  const chat = document.getElementById("chat-list");
  const sendBtn = document.getElementById("send-message-button");
  const micBtn = document.getElementById("mic-button");
  const themeToggle = document.getElementById("theme-toggle-button");

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    appendUserMessage(text);
    callBackend(text);
    input.value = "";
  }

  sendBtn?.addEventListener("click", sendMessage);
  input?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  micBtn?.addEventListener("click", () => {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();
    recognition.onresult = (e) => {
      input.value = e.results[0][0].transcript;
      sendMessage();
    };
  });

  themeToggle?.addEventListener("click", () => {
    document.body.classList.toggle("light_mode");
    themeToggle.textContent = document.body.classList.contains("light_mode")
      ? "dark_mode"
      : "light_mode";
  });
});

function appendUserMessage(text) {
  const chat = document.getElementById("chat-list");
  const msg = document.createElement("div");
  msg.className = "message user";
  msg.innerHTML = `<div class="message-content">${text}</div>`;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

function appendBotMessage(sqlQuery, summary, dataArray) {
  const chat = document.getElementById("chat-list");
  const msg = document.createElement("div");
  msg.className = "message bot";

  const uid = `uid-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

  let html = `<div class="message-content">`;
  html += `<div class="bot-heading">Data + Query</div>`;

  if (summary?.trim()) {
    html += `<div class="summary-block"><strong>Summary:</strong><br>${summary}</div>`;
  }

  if (!Array.isArray(dataArray) || dataArray.length === 0) {
    html += `<div>No data found.</div>`;
  } else {
    html += `<div class="sql-block"><strong>SQL Query:</strong><br>${
      sqlQuery || "No SQL generated"
    }</div>`;
    html += `<div class="data-table-label"><strong>Data Table:</strong></div>`;
    html += `<div class="table-wrapper"><table class="response-table"><thead><tr>`;

    const headers = Object.keys(dataArray[0]);
    headers.forEach((h) => {
      html += `<th>${h}</th>`;
    });

    html += `</tr></thead><tbody>`;
    dataArray.forEach((row) => {
      html += `<tr>`;
      headers.forEach((h) => {
        html += `<td>${row[h] ?? ""}</td>`;
      });
      html += `</tr>`;
    });
    html += `</tbody></table></div>`;

    // Excel download button
    html += `<button class="download-btn" id="${uid}-excel">⬇ Download Excel</button>`;
    html += `<div class="chart-wrapper" style="display:flex;flex-wrap:wrap;gap:1rem;margin-top:1rem;min-height:200px;"></div>`;
  }

  html += `</div>`;
  msg.innerHTML = html;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;

  // Excel export
  const excelBtn = document.getElementById(`${uid}-excel`);
  if (excelBtn)
    excelBtn.addEventListener("click", () => downloadExcel(dataArray));

  // Render charts once Chart.js is ready
  const wrapper = msg.querySelector(".chart-wrapper");
  console.log("📊 DataArray:", JSON.stringify(dataArray, null, 2)); // Debug data

  const waitForChart = () => {
    if (window.chartJsReady) {
      console.log("📊 Rendering charts for:", uid);
      renderCharts(wrapper, dataArray);
    } else {
      console.warn("⚠️ Chart.js not ready, retrying...");
      setTimeout(waitForChart, 100);
    }
  };
  waitForChart();
}

function renderCharts(wrapper, dataArray) {
  if (!wrapper || !Array.isArray(dataArray) || dataArray.length === 0) {
    console.warn("⚠️ Invalid wrapper or dataArray");
    return;
  }

  const sample = dataArray[0];
  const keys = Object.keys(sample);
  console.log("📦 Keys available:", keys);

  const tableRules = {
    accounts: {
      flags: ["appl_aprv_in", "bk_in"],
      categories: [],
      numerics: ["aprv_loan_am", "aprv_loan_pymt_am", "aprv_pymt_am"],
    },
    auto_fnce_orgn_refn_elg: {
      flags: ["refn_el_in", "state_alow_in"],
      categories: ["state_cd"],
    },
    auto_fnce_orgn_refn_clsng_fee: {
      flags: [],
      categories: ["lien_hldr_nm"],
      numerics: ["orgn_loan_pyf_am", "vhcl_fee_am", "addl_fee_am"],
    },
    auto_fnce_orgn_refn_clse: {
      categories: ["clse_task_stg_sts_tx", "clse_task_stg_tx"],
    },
  };

  // Detect table based on case-insensitive key presence
  const detectedTable = keys.some(
    (k) => k.toLowerCase() === "appl_aprv_in".toLowerCase()
  )
    ? "accounts"
    : keys.some((k) => k.toLowerCase() === "refn_el_in".toLowerCase())
    ? "auto_fnce_orgn_refn_elg"
    : keys.some((k) => k.toLowerCase() === "lien_hldr_nm".toLowerCase())
    ? "auto_fnce_orgn_refn_clsng_fee"
    : keys.some((k) => k.toLowerCase() === "clse_task_stg_sts_tx".toLowerCase())
    ? "auto_fnce_orgn_refn_clse"
    : null;

  if (!detectedTable) {
    console.warn("⚠️ No table detected for keys:", keys);
    return;
  }

  const config = tableRules[detectedTable] || {};
  const flags = config.flags || [];
  const categories = config.categories || [];
  const numerics = config.numerics || [];

  const dateKey = keys.find(
    (k) => k.toLowerCase().includes("date") || k.toLowerCase().endsWith("_dt")
  );

  let chartCount = 0;

  // ✅ Special bar chart: Approved vs Booked for "accounts" table
  if (detectedTable === "accounts") {
    const approvedCount = dataArray.filter((d) =>
      [1, true].includes(d.appl_aprv_in || d.APPL_APRV_IN)
    ).length;
    const bookedCount = dataArray.filter((d) =>
      [1, true].includes(d.bk_in || d.BK_IN)
    ).length;

    const approvalCanvas = document.createElement("canvas");
    approvalCanvas.className = "approval-bar-chart";
    approvalCanvas.style.maxWidth = "380px";
    approvalCanvas.style.maxHeight = "300px";
    approvalCanvas.style.marginTop = "12px";
    approvalCanvas.style.borderRadius = "10px";
    wrapper.appendChild(approvalCanvas);

    const ctx = approvalCanvas.getContext("2d");
    const gradientColors = [
      ctx.createLinearGradient(0, 0, approvalCanvas.width, 0),
      ctx.createLinearGradient(0, 0, approvalCanvas.width, 0),
    ];
    gradientColors[0].addColorStop(0, "#0775f3");
    gradientColors[0].addColorStop(1, "#02053b");
    gradientColors[1].addColorStop(0, "#ff7043");
    gradientColors[1].addColorStop(1, "#701d03");

    new Chart(approvalCanvas, {
      type: "bar",
      data: {
        labels: ["Approved", "Booked"],
        datasets: [
          {
            label: "Applications",
            data: [approvedCount, bookedCount],
            backgroundColor: gradientColors,
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: "Approved vs Booked Applications",
            color: "#fff",
          },
          legend: { display: false },
        },
        scales: {
          x: { ticks: { color: "#fff" } },
          y: { beginAtZero: true, ticks: { color: "#fff" } },
        },
      },
    });
    chartCount++;
  }

  // ✅ Flag-based bar charts (1 vs 0 or true vs false)

  for (const key of flags) {
    const trueCount = dataArray.filter((d) =>
      [1, true].includes(d[key] || d[key.toUpperCase()])
    ).length;
    const falseCount = dataArray.filter((d) => {
      const value = d[key] || d[key.toUpperCase()];
      return (
        value === null || value === undefined || [0, false].includes(value)
      );
    }).length;

    const canvas = document.createElement("canvas");
    canvas.className = "flag-bar-chart";
    canvas.style.maxWidth = "380px";
    canvas.style.maxHeight = "300px";
    canvas.style.marginTop = "12px";
    canvas.style.borderRadius = "10px";
    wrapper.appendChild(canvas);

    const ctx = canvas.getContext("2d");
    const gradientColors = [
      ctx.createLinearGradient(0, 0, canvas.width, 0),
      ctx.createLinearGradient(0, 0, canvas.width, 0),
    ];
    gradientColors[0].addColorStop(0, "#4294f1");
    gradientColors[0].addColorStop(1, "#02053b");
    gradientColors[1].addColorStop(0, "#0511fd");
    gradientColors[1].addColorStop(1, "#02053b");

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: ["Yes (1/True)", "No (0/False)"],
        datasets: [
          {
            label: key,
            data: [trueCount, falseCount],
            backgroundColor: gradientColors,
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: `${key} Distribution`, // Added "Distribution" for clarity
            color: "#fff",
          },
          legend: { display: false },
        },
        scales: {
          x: { ticks: { color: "#fff" } },
          y: { beginAtZero: true, ticks: { color: "#fff" } },
        },
      },
    });
    chartCount++;
  }

  // ✅ Pie charts for categories
  for (const key of categories) {
    const canvas = document.createElement("canvas");
    canvas.className = "pie-chart-canva";
    if (!document.body.classList.contains("light_mode")) {
      canvas.classList.add("dark-mode");
    }
    wrapper.appendChild(canvas);

    const values = dataArray
      .map((d) => d[key] || d[key.toUpperCase()])
      .filter((v) => v != null);
    if (values.length === 0) {
      wrapper.removeChild(canvas);
      continue;
    }

    const counts = values.reduce((acc, v) => {
      const val = v?.toString() || "Unknown";
      acc[val] = (acc[val] || 0) + 1;
      return acc;
    }, {});

    const ctx = canvas.getContext("2d");
    const gradientColors = [];
    const data = Object.values(counts);
    const labels = Object.keys(counts);

    // Define a set of base gradient pairs
    const gradientPairs = [
      { start: "#88b8ff", end: "#02053b" },
      { start: "#0775f3", end: "#02053b" },
      { start: "#26a69a", end: "#02053b" },
      { start: "#ff7043", end: "#02053b" },
      { start: "#ab47bc", end: "#02053b" },
      { start: "#ff7043", end: "#701d03" },
      { start: "#b59c52", end: "#f0b505" },
      { start: "#03a9f4", end: "#0288d1" },
      { start: "#ffca28", end: "#ab47bc" },
      { start: "#ab47bc", end: "#8e24aa" },
    ];

    // Create unique gradients for each segment
    for (let i = 0; i < data.length; i++) {
      const pairIndex = i % gradientPairs.length;
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, gradientPairs[pairIndex].start);
      gradient.addColorStop(1, gradientPairs[pairIndex].end);
      gradientColors.push(gradient);
    }

    new Chart(canvas, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            data: data,
            backgroundColor: gradientColors,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          title: {
            display: true,
            text: `${key} Distribution`,
            color: "#fff",
          },
          legend: {
            position: "top",
            labels: { color: "#fff" },
          },
        },
      },
    });
    chartCount++;
  }

  // ✅ Numeric charts (bar + line) over date
  if (numerics.length > 0 && dateKey) {
    const sorted = [...dataArray]
      .filter((d) => d[dateKey] && !isNaN(new Date(d[dateKey]).getTime()))
      .sort((a, b) => new Date(a[dateKey]) - new Date(b[dateKey]));
    if (sorted.length === 0) return;

    // Bar chart
    const barCanvas = document.createElement("canvas");
    barCanvas.className = "bar-chart-canvas";
    barCanvas.style.height = "180px";
    barCanvas.style.borderRadius = "12px";
    barCanvas.style.padding = "12px";
    wrapper.appendChild(barCanvas);

    new Chart(barCanvas, {
      type: "bar",
      data: {
        labels: sorted.map((d) => new Date(d[dateKey]).toLocaleDateString()),
        datasets: numerics.map((num, index) => ({
          label: num,
          data: sorted.map((d) =>
            parseFloat(d[num] || d[num.toUpperCase()] || 0)
          ),
          backgroundColor: ["#0775f3", "#ff7043", "#fff"][index % 3],
          borderColor: ["#0775f3", "#388E3C", "#7B1FA2"][index % 3],
          borderWidth: 1,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: `Trends: ${numerics.join(", ")}`,
            color: "#ffffff",
          },
          legend: {
            labels: { color: "#ffffff" },
          },
        },
        scales: {
          x: {
            title: { display: true, text: dateKey, color: "#ffffff" },
            ticks: { color: "#ffffff" },
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Amount", color: "#ffffff" },
            ticks: { color: "#ffffff" },
          },
        },
      },
    });
    chartCount++;

    // Line chart
    const lineCanvas = document.createElement("canvas");
    lineCanvas.className = "line-chart-canvas";
    lineCanvas.style.height = "180px";
    lineCanvas.style.borderRadius = "12px";
    lineCanvas.style.padding = "12px";
    wrapper.appendChild(lineCanvas);

    new Chart(lineCanvas, {
      type: "line",
      data: {
        labels: sorted.map((d) => new Date(d[dateKey]).toLocaleDateString()),
        datasets: numerics.map((num, index) => ({
          label: num,
          data: sorted.map((d) =>
            parseFloat(d[num] || d[num.toUpperCase()] || 0)
          ),
          borderColor: ["#0775f3", "#ff7043", "#fff"][index % 3],
          borderWidth: 2,
          fill: false,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: `Trends: ${numerics.join(", ")}`,
            color: "#ffffff",
          },
          legend: {
            labels: { color: "#ffffff" },
          },
        },
        scales: {
          x: {
            title: { display: true, text: dateKey, color: "#ffffff" },
            ticks: { color: "#ffffff" },
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Amount", color: "#ffffff" },
            ticks: { color: "#ffffff" },
          },
        },
      },
    });
    chartCount++;
  }

  console.log(`📊 Total charts rendered: ${chartCount}`);
}

function downloadExcel(dataArray) {
  if (!Array.isArray(dataArray) || dataArray.length === 0) return;
  if (typeof XLSX === "undefined") {
    console.error("❌ XLSX library is not loaded.");
    return;
  }

  const worksheet = XLSX.utils.json_to_sheet(dataArray);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Results");
  XLSX.writeFile(workbook, `query-result-${Date.now()}.xlsx`);
}

async function callBackend(prompt) {
  const payload = { prompt };
  console.log("📨 Sending payload:", payload);

  try {
    const res = await fetch("http://localhost:8000/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const json = await res.json();
    const sql = json.sql || "No SQL generated";
    const data = Array.isArray(json.data) ? json.data : [];
    const summary = json.summary || "";
    appendBotMessage(sql, summary, data);
  } catch (err) {
    console.error("❌ Backend Error:", err);
    appendBotMessage("", "", [
      { error: "❌ Could not connect to backend or invalid response." },
    ]);
  }
}
