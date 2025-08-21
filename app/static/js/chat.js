const chatEl = document.getElementById("chat");
const inputContainer = document.getElementById("input"); // inner div
const inputWrapper = document.getElementById("input-wrapper"); // outer div
const inputEl = document.getElementById("input-text");
const sendBtn = document.getElementById("send-btn");
const sessionId = window.location.pathname.split("/").pop();
const { renderMarkdown, rerenderAllMessages } = window.ChatRenderer;

if (!sessionId) {
  alert("No session ID found in URL. Please log in or use a valid link.");
}

// Scroll to bottom if there's already history
chatEl.scrollTop = chatEl.scrollHeight;

// Auto-grow input
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = inputEl.scrollHeight + "px";

  if (inputEl.scrollHeight > 48) {
    inputContainer.classList.add("expanded");
  } else {
    inputContainer.classList.remove("expanded");
  }
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
  if (!prompt) return;

  appendMessage(prompt, "user");
  inputEl.value = "";
  sendBtn.disabled = true;

  const assistantEl = appendMessage("", "assistant");
  assistantEl.innerHTML = `<div class="dot-typing"><span></span><span></span><span></span></div>`;

  try {
    const res = await fetch(`/chat/${sessionId}/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!res.ok || !res.body) {
      const text = await res.text();
      throw new Error(`Server error: ${res.status} - ${text}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let assistantText = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      assistantText += decoder.decode(value, { stream: true });

      const isAtBottom =
        chatEl.scrollTop + chatEl.clientHeight >= chatEl.scrollHeight - 50;

      renderMarkdown(assistantEl, assistantText);
      assistantEl.dataset.raw = assistantText;

      if (isAtBottom) {
        chatEl.scrollTop = chatEl.scrollHeight;
      }

      await new Promise(requestAnimationFrame);
    }
  } catch (err) {
    console.error(err);
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
  signature.textContent = type === "assistant" ? "Assistant" : "You";
  signature.textContent += ` | ${getCurrentDateTime()}`;

  if (type === "assistant") {
    msg.dataset.raw = text;
    renderMarkdown(msg, text);
  } else {
    msg.textContent = text;
  }

  chatEl.appendChild(signature);
  chatEl.appendChild(msg);

  // Always scroll to bottom on new user message
  chatEl.scrollTop = chatEl.scrollHeight;
  return msg;
}
