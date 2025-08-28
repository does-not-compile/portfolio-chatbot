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
    const a = document.createElement("a");
    const span = document.createElement("span");
    const shortId = shortenId(session.id);

    a.classList.add("nav-link");
    a.href = `/chat/${session.id}`;
    a.innerHTML = `${localizeTimestamp(session.created_at)} | ${shortId}`;

    span.classList.add("delete");

    span.addEventListener("click", async (e) => {
      e.preventDefault();

      try {
        const res = await fetch(`/sessions/delete/${session.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Server error: ${res.status} - ${text}`);
        }

        // Optionally remove the li from DOM after successful delete
        span.closest("li")?.remove();
      } catch (err) {
        console.error("Failed to delete session:", err);
      }
    });

    if (session.id === currentSessionId) {
      a.classList.add("active");
    }

    li.appendChild(a);
    li.appendChild(span);
    sessionListEl.appendChild(li);
  });
}

export { chatEl, inputEl, inputContainer };
