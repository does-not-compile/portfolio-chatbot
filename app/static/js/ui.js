import { localizeTimestamp } from "./utils.js";

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input-text");
const sessionListEl = document.getElementById("sessionList");
const inputContainer = document.getElementById("input");
const currentSessionId = window.location.pathname.split("/").pop();

// Scroll to bottom of Chat element
export function scrollToBottom(force = false) {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      chatEl.scrollTo({
        top: chatEl.scrollHeight,
        behavior: force ? "auto" : "smooth",
      });
    });
  });
}

// Resize the input field
export function resizeInput(inputEl) {
  inputEl.style.height = "auto";
  inputEl.style.height = inputEl.scrollHeight + "px";
}

// Auto-grow input as user types
export function setupAutoGrow(inputEl, inputContainer) {
  inputEl.addEventListener("input", () => {
    resizeInput(inputEl);
    if (inputEl.scrollHeight > 48) {
      inputContainer.classList.add("expanded");
    } else {
      inputContainer.classList.remove("expanded");
    }
  });
}

// fetch sessions and populate ul with class session-list
export async function fillSessionList() {
  const res = await fetch(`/sessions`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Server error: ${res.status} - ${text}`);
  }

  // 1. Parse JSON
  const data = await res.json();

  // 2. Clear existing list
  sessionListEl.innerHTML = "";

  // 3. Populate list
  function shortenId(id) {
    if (!id) return "";
    if (id.length <= 8) return id; // if already short
    return `${id.slice(0, 4)}...${id.slice(-4)}`;
  }

  data.sessions.forEach((session) => {
    const li = document.createElement("li");
    const shortId = shortenId(session.id);

    if (session.id === currentSessionId) {
      li.innerHTML = `<a class="nav-link active" href="/chat/${
        session.id
      }">${localizeTimestamp(session.created_at)} | ${shortId}</a>`;
    } else {
      li.innerHTML = `<a class="nav-link" href="/chat/${
        session.id
      }">${localizeTimestamp(session.created_at)} | ${shortId}</a>`;
    }

    sessionListEl.appendChild(li);
  });
}

export { chatEl, inputEl, inputContainer };
