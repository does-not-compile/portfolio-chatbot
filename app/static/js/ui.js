const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input-text");
const inputContainer = document.getElementById("input");

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

export { chatEl, inputEl, inputContainer };
