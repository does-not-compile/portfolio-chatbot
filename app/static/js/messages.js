import { renderMarkdown } from "./renderer.js";
import { scrollToBottom, chatEl } from "./ui.js";
import { getCurrentDateTime } from "./utils.js";

// Handles appendign messages to #chat
export function appendMessage(text, type) {
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

  scrollToBottom();
  return msg;
}
