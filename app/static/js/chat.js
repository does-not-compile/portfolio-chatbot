// chat.js
const chatEl = document.getElementById("chat");
const inputWrapper = document.getElementById("input");
const inputEl = document.getElementById("input-text");
const sendBtn = document.getElementById("send-btn");
const urlParams = new URLSearchParams(window.location.search);
const SESSION_ID = urlParams.get("sessionId");
const USER_ID = urlParams.get("userId");

const { renderMarkdown, rerenderAllMessages } = window.ChatRenderer;

if (!USER_ID) {
  alert("No user ID found in URL. Please log in or use a valid link.");
}
if (!SESSION_ID) {
  alert("No session ID found in URL. Please log in or use a valid link.");
}

// Scroll to bottom if there's already history
chatEl.scrollTop = chatEl.scrollHeight;

// Auto-grow input inputEl
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = inputEl.scrollHeight + "px";

  if (inputEl.scrollHeight > 48) {
    // ≈ 3rem min-height
    inputWrapper.classList.add("expanded");
  } else {
    inputWrapper.classList.remove("expanded");
  }

  // trigger chat to shrink
  chatEl.style.flex = "1 1 auto";
});

// Auto-send on Enter (Shift+Enter for newline)
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Render existing history on page load
window.addEventListener("load", () => {
  rerenderAllMessages();
});

async function sendMessage() {
  const prompt = inputEl.value.trim();
  if (!prompt || !USER_ID || !SESSION_ID) return;

  appendMessage(prompt, "user");
  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;

  const assistantEl = appendMessage("", "assistant");
  assistantEl.innerHTML = `<div class="dot-typing">
    <span></span><span></span><span></span>
  </div>`;

  try {
    const res = await fetch("/chat-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, sessionId: SESSION_ID, userId: USER_ID }),
    });

    if (!res.ok || !res.body) {
      throw new Error(`Server error: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let gotFirstChunk = false;
    let assistantText = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      assistantText += chunk;

      if (!gotFirstChunk) {
        gotFirstChunk = true;
        assistantEl.innerHTML = "";
      }

      // Live rendering while streaming
      renderMarkdown(assistantEl, assistantText);
      assistantEl.dataset.raw = assistantText;

      chatEl.scrollTop = chatEl.scrollHeight;
      await new Promise(requestAnimationFrame);
    }
  } catch (err) {
    console.error("Error during chat stream:", err);
    assistantEl.textContent = "[Error: Could not fetch response]";
  } finally {
    sendBtn.disabled = false;
  }
}

function getCurrentDateTime() {
  const now = new Date();
  return `${String(now.getDate()).padStart(2, "0")}.${String(
    now.getMonth() + 1
  ).padStart(2, "0")}.${now.getFullYear()}, ${String(now.getHours()).padStart(
    2,
    "0"
  )}:${String(now.getMinutes()).padStart(2, "0")}:${String(
    now.getSeconds()
  ).padStart(2, "0")}`;
}

function appendMessage(text, type) {
  const signature = document.createElement("div");
  const msg = document.createElement("div");
  signature.classList.add(`${type}-signature`);
  msg.classList.add("message", type);
  signature.textContent = type == "assistant" ? "Assistant" : "You";
  signature.textContent += ` | ${getCurrentDateTime()}`;

  if (type === "assistant") {
    msg.dataset.raw = text;
    renderMarkdown(msg, text);
  } else {
    msg.textContent = text;
  }

  chatEl.appendChild(signature);
  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
  return msg;
}
