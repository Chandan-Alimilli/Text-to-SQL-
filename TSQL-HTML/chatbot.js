// Load Chart.js safely
const chartScript = document.createElement("script");
chartScript.src =
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js";
chartScript.onload = () => {
  console.log("✅ Chart.js loaded");
  if (window.Chart) {
    // Register components for Chart.js v4
    Chart.register(
      Chart.BarController,
      Chart.PieController,
      Chart.LinearScale,
      Chart.CategoryScale,
      Chart.PointElement,
      Chart.BarElement,
      Chart.ArcElement
    );
    window.chartJsReady = true;
    // Test chart to verify Chart.js
    const testCanvas = document.createElement("canvas");
    testCanvas.style.position = "absolute";
    testCanvas.style.top = "-9999px"; // Offscreen for testing
    document.body.appendChild(testCanvas);
    try {
      new Chart(testCanvas, {
        type: "pie",
        data: {
          labels: ["Test1", "Test2"],
          datasets: [
            { data: [10, 20], backgroundColor: ["#90caf9", "#1565c0"] },
          ],
        },
      });
      console.log("✅ Test chart rendered");
    } catch (err) {
      console.error("❌ Test chart failed:", err);
    }
  } else {
    console.error("❌ Chart.js not available");
    window.chartJsReady = false;
  }
};
chartScript.onerror = () => {
  console.error("❌ Failed to load Chart.js");
  window.chartJsReady = false;
};
document.head.appendChild(chartScript);

// Chat app logic
document.addEventListener("DOMContentLoaded", () => {
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

// function renderCharts(wrapper, dataArray) {
//   if (!wrapper || !Array.isArray(dataArray) || dataArray.length === 0) {
//     console.warn("⚠️ Invalid wrapper or dataArray");
//     return;
//   }

//   const sample = dataArray[0];
//   const keys = Object.keys(sample);
//   console.log("📦 Keys available:", keys);

//   const tableRules = {
//     accounts: {
//       flags: ["appl_aprv_in", "bk_in"],
//       categories: [],
//       numerics: ["aprv_loan_am", "aprv_loan_pymt_am", "aprv_pymt_am"], // Fixed typo
//     },
//     auto_fnce_orgn_refn_elg: {
//       flags: ["refn_el_in", "state_alow_in"],
//       categories: ["state_cd"],
//       // numerics: ["refn_ln_amt", "refn_pd_amt"],
//     },
//     auto_fnce_orgn_refn_clsng_fee: {
//       flags: [],
//       categories: ["lien_hldr_nm"],
//       numerics: ["orgn_loan_pyf_am", "vhcl_fee_am", "addl_fee_am"],
//     },
//     auto_fnce_orgn_refn_clse: {
//       flags: ["sts_cd"],
//       categories: ["clse_task_stg_sts_tx"],
//       // numerics: ["clsng_ln_amt", "clsng_pd_amt"],
//     },
//   };

//   const detectedTable = keys.includes("appl_aprv_in")
//     ? "accounts"
//     : keys.includes("refn_el_in")
//     ? "auto_fnce_orgn_refn_elg"
//     : keys.includes("lien_hldr_nm")
//     ? "auto_fnce_orgn_refn_clsng_fee"
//     : keys.includes("clse_task_stg_sts_tx")
//     ? "auto_fnce_orgn_refn_clse"
//     : null;

//   if (!detectedTable) {
//     console.warn("⚠️ No table detected for keys:", keys);
//     return;
//   }

//   const config = tableRules[detectedTable] || {};
//   const flags = config.flags || [];
//   const categories = config.categories || [];
//   const numerics = config.numerics || [];

//   const dateKey = keys.find(
//     (k) => k.toLowerCase().includes("date") || k.toLowerCase().endsWith("_dt")
//   );

//   let chartCount = 0;

//   // ✅ Small bar chart for approved vs booked applications
//   if (detectedTable === "accounts") {
//     const approvedCount = dataArray.filter((d) => d.appl_aprv_in === 1).length;
//     const bookedCount = dataArray.filter((d) => d.bk_in === 1).length;

//     const approvalCanvas = document.createElement("canvas");
//     approvalCanvas.className = "approval-bar-chart";
//     approvalCanvas.style.maxWidth = "280px";
//     approvalCanvas.style.maxHeight = "200px";
//     approvalCanvas.style.marginTop = "12px";
//     approvalCanvas.style.borderRadius = "10px";
//     approvalCanvas.style.background = "#fff";
//     wrapper.appendChild(approvalCanvas);

//     new Chart(approvalCanvas, {
//       type: "bar",
//       data: {
//         labels: ["Approved", "Booked"],
//         datasets: [
//           {
//             label: "Applications",
//             data: [approvedCount, bookedCount],
//             backgroundColor: ["#1976d2", "#26a69a"],
//             borderRadius: 6,
//           },
//         ],
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//         plugins: {
//           title: {
//             display: true,
//             text: "Approved vs Booked Applications",
//             color: "#333",
//           },
//           legend: { display: false },
//         },
//         scales: {
//           x: {
//             ticks: { color: "#333" },
//           },
//           y: {
//             beginAtZero: true,
//             ticks: { color: "#333" },
//           },
//         },
//       },
//     });
//   }

//   // Handle pie charts for flags and categories
//   const pieContainer = document.createElement("div");
//   pieContainer.className = "pie-chart-container";
//   wrapper.appendChild(pieContainer);

//   for (const key of [...flags, ...categories]) {
//     const canvas = document.createElement("canvas");
//     canvas.className = "pie-chart-canvas";
//     if (!document.body.classList.contains("light_mode")) {
//       canvas.classList.add("dark-mode");
//     }
//     pieContainer.appendChild(canvas);

//     if (!canvas.isConnected) {
//       console.error(`❌ Canvas for ${key} not added to DOM`);
//       continue;
//     }

//     const values = dataArray.map((d) => d[key]).filter((v) => v != null);
//     if (values.length === 0) {
//       console.warn(`⚠️ No valid data for ${key}, skipping chart`);
//       pieContainer.removeChild(canvas);
//       continue;
//     }

//     try {
//       const counts = values.reduce((acc, v) => {
//         const val = v?.toString() || "Unknown";
//         acc[val] = (acc[val] || 0) + 1;
//         return acc;
//       }, {});
//       if (Object.keys(counts).length === 0) {
//         console.warn(`⚠️ No data to plot for ${key}`);
//         pieContainer.removeChild(canvas);
//         continue;
//       }
//       console.log(`📊 Creating pie chart for ${key}:`, counts);
//       new Chart(canvas, {
//         type: "pie",
//         data: {
//           labels: Object.keys(counts).map((v) => `${key}: ${v}`),
//           datasets: [
//             {
//               data: Object.values(counts),
//               backgroundColor: [
//                 "#1548a0", // Dark Purple
//                 "#0775f3", // Dark Green
//                 "#080425",
//                 "#09c1fe", // Medium Green
//                 "#092afe", // Purple
//               ].slice(0, Object.keys(counts).length),
//             },
//           ],
//         },
//         options: {
//           responsive: true,
//           maintainAspectRatio: true,
//           plugins: {
//             legend: {
//               position: "top",
//               labels: {
//                 generateLabels: (chart) => {
//                   const data = chart.data;
//                   return data.labels.map((label, i) => ({
//                     text: label,
//                     fillStyle: data.datasets[0].backgroundColor[i],
//                     datasetIndex: 0,
//                     index: i,
//                     color: "#ffffff", // White text for legend
//                   }));
//                 },
//                 color: "#ffffff", // White text for legend
//               },
//               className: "pie-chart-legend",
//             },
//             title: {
//               display: true,
//               text: `${key} Distribution`,
//               color: "#000", // White text for title
//             },
//             datalabels: {
//               color: "#ffffff", // White text for data labels (requires chartjs-plugin-datalabels)
//               font: {
//                 weight: "bold",
//               },
//               formatter: (value, ctx) => {
//                 return value; // Display the value as the label
//               },
//               anchor: "center", // Position label inside the segment
//               align: "center",
//             },
//           },
//           scales: {
//             // Pie charts don't use scales, but included for consistency
//           },
//         },
//       });
//       chartCount++;
//     } catch (err) {
//       console.error(`❌ Error rendering pie chart for ${key}:`, err);
//       pieContainer.removeChild(canvas);
//     }
//   }

//   // Handle bar and line charts for numerics
//   if (numerics.length > 0 && dateKey) {
//     const sorted = [...dataArray]
//       .filter((d) => d[dateKey] && !isNaN(new Date(d[dateKey]).getTime()))
//       .sort((a, b) => new Date(a[dateKey]) - new Date(b[dateKey]));
//     if (sorted.length === 0) {
//       console.warn(
//         `⚠️ No valid data for numerics with date ${dateKey}. Raw data:`,
//         dataArray.map((d) => ({
//           [dateKey]: d[dateKey],
//           ...numerics.reduce((acc, num) => ({ ...acc, [num]: d[num] }), {}),
//         }))
//       );
//       return;
//     }
//     console.log(`📊 Sorted data for numerics:`, sorted);

//     // Bar chart for all numerics
//     const barCanvas = document.createElement("canvas");
//     barCanvas.className = "bar-chart-canvas";
//     if (!document.body.classList.contains("light_mode")) {
//       barCanvas.classList.add("dark-mode");
//     }
//     barCanvas.style.height = "180px";
//     barCanvas.style.borderRadius = "12px";
//     barCanvas.style.padding = "12px";
//     wrapper.appendChild(barCanvas);
//     console.log(
//       `📊 Creating bar chart for ${numerics.join(", ")} with date ${dateKey}`
//     );
//     new Chart(barCanvas, {
//       type: "bar",
//       data: {
//         labels: sorted.map((d) => new Date(d[dateKey]).toLocaleDateString()),
//         datasets: numerics.map((num, index) => ({
//           label: num,
//           data: sorted.map((d) => parseFloat(d[num] || 0)),
//           backgroundColor: [
//             "#0775f3", // Deep Orange
//             "#4CAF50", // Green
//             "#fff", // Purple
//           ][index % 3],
//           borderColor: [
//             "#0775f3", // Dark Red
//             "#388E3C", // Dark Green
//             "#7B1FA2", // Dark Purple
//           ][index % 3],
//           borderWidth: 1,
//         })),
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//         scales: {
//           x: {
//             title: {
//               display: true,
//               text: dateKey,
//               color: "#ffffff", // White text for x-axis title
//             },
//             ticks: {
//               color: "#ffffff", // White text for x-axis labels
//             },
//           },
//           y: {
//             beginAtZero: true,
//             title: {
//               display: true,
//               text: "Amount",
//               color: "#ffffff", // White text for y-axis title
//             },
//             ticks: {
//               color: "#ffffff", // White text for y-axis labels
//             },
//           },
//         },
//         plugins: {
//           legend: {
//             display: true,
//             labels: {
//               color: "#ffffff", // White text for legend
//             },
//             className: "bar-chart-legend",
//           },
//           title: {
//             display: true,
//             text: `Trends: ${numerics.join(", ")}`,
//             color: "#ffffff", // White text for title
//           },
//         },
//       },
//     });
//     chartCount++;

//     // Line chart for all numerics
//     const lineCanvas = document.createElement("canvas");
//     lineCanvas.className = "line-chart-canvas";
//     if (!document.body.classList.contains("light_mode")) {
//       lineCanvas.classList.add("dark-mode");
//     }
//     lineCanvas.style.height = "180px";
//     lineCanvas.style.borderRadius = "12px";
//     lineCanvas.style.padding = "12px";
//     wrapper.appendChild(lineCanvas);
//     console.log(
//       `📊 Creating line chart for ${numerics.join(", ")} with date ${dateKey}`
//     );
//     new Chart(lineCanvas, {
//       type: "line",
//       data: {
//         labels: sorted.map((d) => new Date(d[dateKey]).toLocaleDateString()),
//         datasets: numerics.map((num, index) => ({
//           label: num,
//           data: sorted.map((d) => parseFloat(d[num] || 0)),
//           borderColor: [
//             "#0775f3", // Light Blue
//             "#388E3C", // Dark Blue
//             "#fff", // Blue
//           ][index % 3],
//           borderWidth: 2,
//           fill: false,
//         })),
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//         scales: {
//           x: {
//             title: {
//               display: true,
//               text: dateKey,
//               color: "#ffffff", // White text for x-axis title
//             },
//             ticks: {
//               color: "#ffffff", // White text for x-axis labels
//             },
//           },
//           y: {
//             beginAtZero: true,
//             title: {
//               display: true,
//               text: "Amount",
//               color: "#ffffff", // White text for y-axis title
//             },
//             ticks: {
//               color: "#ffffff", // White text for y-axis labels
//             },
//           },
//         },
//         plugins: {
//           legend: {
//             display: true,
//             labels: {
//               color: "#ffffff", // White text for legend
//             },
//             className: "line-chart-legend",
//           },
//           title: {
//             display: true,
//             text: `Trends: ${numerics.join(", ")}`,
//             color: "#ffffff", // White text for title
//           },
//         },
//       },
//     });
//     chartCount++;
//   }

//   console.log(`📊 Total charts rendered: ${chartCount}`);
// }

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
      flags: ["sts_cd"],
      categories: ["clse_task_stg_sts_tx"],
    },
  };

  const detectedTable = keys.includes("appl_aprv_in")
    ? "accounts"
    : keys.includes("refn_el_in")
    ? "auto_fnce_orgn_refn_elg"
    : keys.includes("lien_hldr_nm")
    ? "auto_fnce_orgn_refn_clsng_fee"
    : keys.includes("clse_task_stg_sts_tx")
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
    const approvedCount = dataArray.filter((d) => d.appl_aprv_in === 1).length;
    const bookedCount = dataArray.filter((d) => d.bk_in === 1).length;

    const approvalCanvas = document.createElement("canvas");
    approvalCanvas.className = "approval-bar-chart";
    approvalCanvas.style.maxWidth = "380px";
    approvalCanvas.style.maxHeight = "300px";
    approvalCanvas.style.marginTop = "12px";
    approvalCanvas.style.borderRadius = "10px";
    // approvalCanvas.style.background = "#fff";
    wrapper.appendChild(approvalCanvas);

    new Chart(approvalCanvas, {
      type: "bar",
      data: {
        labels: ["Approved", "Booked"],
        datasets: [
          {
            label: "Applications",
            data: [approvedCount, bookedCount],
            backgroundColor: ["#1976d2", "#26a69a"],
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

  // ✅ Flag-based bar charts (1 vs 0)
  for (const key of flags) {
    const trueCount = dataArray.filter((d) => d[key] === 1).length;
    const falseCount = dataArray.filter((d) => d[key] === 0).length;

    const canvas = document.createElement("canvas");
    canvas.className = "flag-bar-chart";
    canvas.style.maxWidth = "380px";
    canvas.style.maxHeight = "300px";
    canvas.style.marginTop = "12px";
    canvas.style.borderRadius = "10px";
    // canvas.style.background = "#fff";
    wrapper.appendChild(canvas);

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: ["Yes (1)", "No (0)"],
        datasets: [
          {
            label: key,
            data: [trueCount, falseCount],
            backgroundColor: ["#1976d2", "#ff7043"],
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
            text: `${key} Distribution`,
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

    const values = dataArray.map((d) => d[key]).filter((v) => v != null);
    if (values.length === 0) {
      wrapper.removeChild(canvas);
      continue;
    }

    const counts = values.reduce((acc, v) => {
      const val = v?.toString() || "Unknown";
      acc[val] = (acc[val] || 0) + 1;
      return acc;
    }, {});

    new Chart(canvas, {
      type: "pie",
      data: {
        labels: Object.keys(counts),
        datasets: [
          {
            data: Object.values(counts),
            backgroundColor: [
              "#1976d2",
              "#03a393",
              "#0775f3",
              "#05ead3",
              "#5983ad",
            ].slice(0, Object.keys(counts).length),
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
          data: sorted.map((d) => parseFloat(d[num] || 0)),
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
          data: sorted.map((d) => parseFloat(d[num] || 0)),
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
