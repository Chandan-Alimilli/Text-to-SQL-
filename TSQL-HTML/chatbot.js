// document.addEventListener("DOMContentLoaded", () => {
//   const input = document.getElementById("user-input");
//   const chat = document.getElementById("chat-list");
//   const sendBtn = document.getElementById("send-message-button");
//   const micBtn = document.getElementById("mic-button");
//   const themeToggle = document.getElementById("theme-toggle-button");
//   const suggestions = document.querySelectorAll(".suggestion");

//   function sendMessage() {
//     const text = input.value.trim();
//     if (!text) return;
//     appendUserMessage(text);
//     callBackend(text);
//     input.value = "";
//   }

//   function handleSuggestionClick(text) {
//     input.value = text;
//     sendMessage();
//   }

//   sendBtn?.addEventListener("click", sendMessage);
//   input?.addEventListener("keypress", (e) => {
//     if (e.key === "Enter") {
//       e.preventDefault();
//       sendMessage();
//     }
//   });

//   micBtn?.addEventListener("click", () => {
//     const recognition = new webkitSpeechRecognition();
//     recognition.lang = "en-US";
//     recognition.start();
//     recognition.onresult = (e) => {
//       input.value = e.results[0][0].transcript;
//       sendMessage();
//     };
//   });

//   themeToggle?.addEventListener("click", () => {
//     document.body.classList.toggle("light_mode");
//     themeToggle.textContent = document.body.classList.contains("light_mode")
//       ? "dark_mode"
//       : "light_mode";
//   });

//   suggestions.forEach((s) => {
//     s.addEventListener("click", () => {
//       const text = s.querySelector(".text")?.innerText.trim();
//       handleSuggestionClick(text);
//     });
//   });
// });

// function appendUserMessage(text) {
//   const chat = document.getElementById("chat-list");
//   const msg = document.createElement("div");
//   msg.className = "message user";
//   msg.innerHTML = `<div class="message-content">${text}</div>`;
//   chat.appendChild(msg);
//   chat.scrollTop = chat.scrollHeight;
// }

// function appendBotMessage(sqlQuery, summary, dataArray) {
//   const chat = document.getElementById("chat-list");
//   const msg = document.createElement("div");
//   msg.className = "message bot";

//   let html = `<div class="message-content">`;
//   html += `<div class="bot-heading">Data + Query</div>`;
//   html += `<div class="sql-block"><strong>SQL Query:</strong><br>${
//     sqlQuery || "No SQL generated"
//   }</div>`;

//   if (summary && Array.isArray(summary)) {
//     html += `<div class="summary-block"><strong>Summary:</strong><br><pre>${JSON.stringify(
//       summary,
//       null,
//       2
//     )}</pre></div>`;
//   } else if (typeof summary === "string") {
//     html += `<div class="summary-block"><strong>Summary:</strong><br>${summary}</div>`;
//   }

//   if (!dataArray || dataArray.length === 0) {
//     html += `<div>No data found.</div>`;
//   } else {
//     html += `<div class="data-table-label"><strong>Data Table:</strong></div>`;
//     html += `<div class="table-wrapper"><table class="response-table"><thead><tr>`;
//     const headers = Object.keys(dataArray[0]);
//     headers.forEach((h) => {
//       html += `<th>${h}</th>`;
//     });
//     html += `</tr></thead><tbody>`;
//     dataArray.forEach((row) => {
//       html += `<tr>`;
//       headers.forEach((h) => {
//         html += `<td>${row[h] ?? ""}</td>`;
//       });
//       html += `</tr>`;
//     });
//     html += `</tbody></table></div>`;
//   }

//   html += `</div>`;
//   msg.innerHTML = html;
//   chat.appendChild(msg);
//   chat.scrollTop = chat.scrollHeight;
// }

// async function callBackend(prompt) {
//   try {
//     const res = await fetch("http://localhost:8000/data", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ prompt }),
//     });

//     const json = await res.json();

//     const sql = json.sql || "No SQL generated";
//     const summary = json.response || "No summary";
//     const data = json.data || [];

//     appendBotMessage(sql, summary, data);
//   } catch (err) {
//     console.error("Backend Error:", err);
//     appendBotMessage("", "", [
//       { error: "❌ Could not connect to backend or invalid response." },
//     ]);
//   }
// }

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("user-input");
  const chat = document.getElementById("chat-list");
  const sendBtn = document.getElementById("send-message-button");
  const micBtn = document.getElementById("mic-button");
  const themeToggle = document.getElementById("theme-toggle-button");
  const suggestions = document.querySelectorAll(".suggestion");

  function sendMessage() {
    const text = input.value.trim();
    const fromDate = document.getElementById("from-date").value;
    const toDate = document.getElementById("to-date").value;

    if (!text) return;
    if (!fromDate || !toDate) {
      alert("⚠️ Please select both From Date and To Date before submitting.");
      return;
    }

    appendUserMessage(text);
    callBackend(text);
    input.value = "";
  }

  function handleSuggestionClick(text) {
    const fromDate = document.getElementById("from-date").value;
    const toDate = document.getElementById("to-date").value;

    if (!fromDate || !toDate) {
      alert(
        "⚠️ Please select both From Date and To Date before selecting a suggestion."
      );
      return;
    }

    input.value = text;
    sendMessage();
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

  suggestions.forEach((s) => {
    s.addEventListener("click", () => {
      const text = s.querySelector(".text")?.innerText.trim();
      handleSuggestionClick(text);
    });
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

  let html = `<div class="message-content">`;
  html += `<div class="bot-heading">Data + Query</div>`;
  html += `<div class="sql-block"><strong>SQL Query:</strong><br>${
    sqlQuery || "No SQL generated"
  }</div>`;

  if (summary && typeof summary === "string" && summary.trim() !== "") {
    html += `<div class="summary-block"><strong>Summary:</strong><br>${summary}</div>`;
  }

  if (!Array.isArray(dataArray) || dataArray.length === 0) {
    html += `<div>No data found.</div>`;
  } else {
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
    // html += `</tbody></table></div>`;
    html += `</tbody></table></div>`;
    html += `<button class="download-btn" onclick='downloadCSV(${JSON.stringify(
      dataArray
    )})'>⬇ Download CSV</button>`;
    html += `<button class="download-btn" onclick='downloadExcel(${JSON.stringify(
      dataArray
    )})'>⬇ Download Excel</button>`;
  }

  html += `</div>`;
  msg.innerHTML = html;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

function downloadCSV(dataArray) {
  if (!Array.isArray(dataArray) || dataArray.length === 0) return;

  const headers = Object.keys(dataArray[0]);
  const csvRows = [
    headers.join(","), // header row
    ...dataArray.map((row) =>
      headers
        .map((h) => `"${(row[h] ?? "").toString().replace(/"/g, '""')}"`)
        .join(",")
    ), // data rows
  ];

  const csvBlob = new Blob([csvRows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(csvBlob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `query-result-${Date.now()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function appendBotMessage(sqlQuery, summary, dataArray) {
  const chat = document.getElementById("chat-list");
  const msg = document.createElement("div");
  msg.className = "message bot";

  const uid = `uid-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

  let html = `<div class="message-content">`;
  html += `<div class="bot-heading">Data + Query</div>`;
  html += `<div class="sql-block"><strong>SQL Query:</strong><br>${
    sqlQuery || "No SQL generated"
  }</div>`;

  if (summary && typeof summary === "string" && summary.trim() !== "") {
    html += `<div class="summary-block"><strong>Summary:</strong><br>${summary}</div>`;
  }

  if (!Array.isArray(dataArray) || dataArray.length === 0) {
    html += `<div>No data found.</div>`;
  } else {
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

    // Add download buttons with unique IDs
    html += `
      <button class="download-btn" id="${uid}-csv">⬇ Download CSV</button>
      <button class="download-btn" id="${uid}-excel">⬇ Download Excel</button>
    `;
  }

  html += `</div>`;
  msg.innerHTML = html;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;

  // ✅ Attach handlers after rendering
  const csvBtn = document.getElementById(`${uid}-csv`);
  const excelBtn = document.getElementById(`${uid}-excel`);

  if (csvBtn) {
    csvBtn.addEventListener("click", () => downloadCSV(dataArray));
  }
  if (excelBtn) {
    excelBtn.addEventListener("click", () => downloadExcel(dataArray));
  }
}

function downloadCSV(dataArray) {
  if (!Array.isArray(dataArray) || dataArray.length === 0) return;

  const headers = Object.keys(dataArray[0]);
  const csvRows = [
    headers.join(","), // header row
    ...dataArray.map((row) =>
      headers
        .map((h) => `"${(row[h] ?? "").toString().replace(/"/g, '""')}"`)
        .join(",")
    ),
  ];

  const csvBlob = new Blob([csvRows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(csvBlob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `query-result-${Date.now()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function downloadExcel(dataArray) {
  if (!Array.isArray(dataArray) || dataArray.length === 0) return;

  const worksheet = XLSX.utils.json_to_sheet(dataArray);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Results");

  XLSX.writeFile(workbook, `query-result-${Date.now()}.xlsx`);
}

async function callBackend(prompt) {
  const fromDate = document.getElementById("from-date").value;
  const toDate = document.getElementById("to-date").value;
  const recordLimit = document.getElementById("record-limit").value;

  const payload = {
    prompt,
    from_date: fromDate,
    to_date: toDate,
    record_limit: recordLimit ? parseInt(recordLimit) : null,
  };

  console.log("📦 Sending payload:", payload);

  try {
    const res = await fetch("http://localhost:8000/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const json = await res.json();

    const sql = json.sql || "No SQL generated";
    const data = Array.isArray(json.data) ? json.data : []; // ✅ correct field
    const summary = json.response || ""; // ✅ optional message

    appendBotMessage(sql, summary, data);
  } catch (err) {
    console.error("Backend Error:", err);
    appendBotMessage("", "", [
      { error: "❌ Could not connect to backend or invalid response." },
    ]);
  }
}
