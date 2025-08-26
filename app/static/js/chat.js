import {
  chatEl,
  inputEl,
  inputContainer,
  scrollToBottom,
  setupAutoGrow,
  resizeInput,
} from "./ui.js";
import { appendMessage } from "./messages.js";
import { renderMarkdown, rerenderAllMessages } from "./renderer.js";
import { localizeTimestamps } from "./utils.js";

const sendBtn = document.getElementById("send-btn");
const sessionId = window.location.pathname.split("/").pop();
const timestamps = document.querySelectorAll(".timestamp");

if (!sessionId) {
  alert("No session ID found in URL. Please log in or use a valid link.");
}

// setup
setupAutoGrow(inputEl, inputContainer);
scrollToBottom();

// Render existing messages
window.addEventListener("load", () => {
  rerenderAllMessages();
  localizeTimestamps();
  scrollToBottom(true);
});

async function sendMessage() {
  const prompt = inputEl.value.trim();
  if (!prompt) return;

  appendMessage(prompt, "user");
  inputEl.value = "";
  resizeInput(inputEl); // ✅ now defined

  sendBtn.disabled = true;

  const assistantEl = appendMessage("", "assistant");
  assistantEl.innerHTML = `<div class="dot-typing"><span></span><span></span><span></span></div>`;
  scrollToBottom();

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

      assistantEl.dataset.raw = assistantText;
      renderMarkdown(assistantEl, assistantText);

      if (isAtBottom) scrollToBottom();
      await new Promise(requestAnimationFrame);
    }

    assistantEl.dataset.raw = "";
  } catch (err) {
    console.error(err);
    assistantEl.textContent = "I'm sorry. Something went wrong!";
  } finally {
    sendBtn.disabled = false;
  }
}

// Auto-send on Enter (Shift+Enter for newline)
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
