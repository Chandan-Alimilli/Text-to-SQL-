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
//     s.addEventListener("click", () =>
//       handleSuggestionClick(s.innerText.trim())
//     );
//   });
// });

// function handleSendMessage(e) {
//   e.preventDefault();
//   sendMessage();
// }

// function sendMessage() {
//   const input = document.getElementById("user-input");
//   const text = input.value.trim();
//   if (!text) return;

//   appendUserMessage(text);
//   callBackend(text);
//   input.value = "";
// }

// function appendUserMessage(text) {
//   const chat = document.getElementById("chat-list");
//   const msg = document.createElement("div");
//   msg.className = "message user";
//   msg.innerHTML = `<div class="message-content">${text}</div>`;
//   chat.appendChild(msg);
//   chat.scrollTop = chat.scrollHeight;
// }

// function appendBotMessage(sqlQuery, dataArray) {
//   const chat = document.getElementById("chat-list");
//   const msg = document.createElement("div");
//   msg.className = "message bot";

//   let html = `<div class="message-content">`;
//   html += `<div class="sql-block">SQL: ${sqlQuery || "No SQL generated"}</div>`;

//   if (!dataArray || dataArray.length === 0) {
//     html += `<div>No data found.</div>`;
//   } else {
//     const headers = Object.keys(dataArray[0]);
//     html += `<table class="response-table"><thead><tr>`;
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
//     html += `</tbody></table>`;
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
//     appendBotMessage(json.sql, json.response || []);
//   } catch (err) {
//     appendBotMessage("", [
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
    if (!text) return;
    appendUserMessage(text);
    callBackend(text);
    input.value = "";
  }

  function handleSuggestionClick(text) {
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
    s.addEventListener("click", () =>
      handleSuggestionClick(s.innerText.trim())
    );
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

function appendBotMessage(sqlQuery, dataArray) {
  const chat = document.getElementById("chat-list");
  const msg = document.createElement("div");
  msg.className = "message bot";

  let html = `<div class="message-content">`;
  html += `<div class="bot-heading">Data + Query</div>`;
  html += `<div class="sql-block"><strong>SQL Query:</strong><br>${
    sqlQuery || "No SQL generated"
  }</div>`;

  if (!dataArray || dataArray.length === 0) {
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
  }

  html += `</div>`;
  msg.innerHTML = html;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

async function callBackend(prompt) {
  try {
    const res = await fetch("http://localhost:8000/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const json = await res.json();
    appendBotMessage(json.sql, json.response || []);
  } catch (err) {
    appendBotMessage("", [
      { error: "❌ Could not connect to backend or invalid response." },
    ]);
  }
}
