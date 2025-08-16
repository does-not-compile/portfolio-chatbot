(() => {
  const inputs = Array.from(document.querySelectorAll("#uuidInputs input"));
  const hiddenField = document.getElementById("userId");
  // ensure only uuid characters
  const sanitize = (s) =>
    s
      .replace(/[{}]/g, "")
      .replace(/[^0-9a-fA-F]/g, "")
      .toLowerCase();

  function combine() {
    hiddenField.value = inputs.map((i) => i.value).join("-");
  }

  function distributeFrom(text) {
    const cleaned = sanitize(text);
    let parts;

    if (cleaned.includes("-")) {
      parts = cleaned.split("-");
    } else {
      const hex = cleaned.replace(/-/g, ""); // just for my own sanity
      parts = [
        hex.slice(0, 8),
        hex.slice(8, 12),
        hex.slice(12, 16),
        hex.slice(16, 20),
        hex.slice(20, 32),
      ];
    }

    if (parts.length !== inputs.length) return false; // if there are more or less text fields than uuid parts

    inputs.forEach((inp, i) => {
      inp.value = (parts[i] || "").slice(0, inp.maxLength); // just making sure the part exists and it does not exceed the input's max length
    });

    // Focus next empty (or last) after distributing
    const next =
      inputs.find((inp) => inp.value.length < inp.maxLength) ||
      inputs[inputs.length - 1];
    next.focus();
    next.select?.();
    combine();
    return true;
  }

  inputs.forEach((inp, idx) => {
    // Correct paste handling — this fixes the "only first batch" issue
    inp.addEventListener("paste", (e) => {
      const text = (e.clipboardData || window.clipboardData).getData("text");
      if (distributeFrom(text)) {
        e.preventDefault(); // stop default paste into the single field
      }
    });

    // Typing: sanitize + auto-advance
    inp.addEventListener("input", () => {
      inp.value = inp.value.replace(/[^0-9a-fA-F]/g, "").toLowerCase();
      if (inp.value.length >= inp.maxLength && idx < inputs.length - 1) {
        inputs[idx + 1].focus();
        inputs[idx + 1].select?.();
      }
      combine();
    });

    // Hyphen to jump forward (optional UX nicety)
    inp.addEventListener("keydown", (e) => {
      if (e.key === "-" && idx < inputs.length - 1) {
        e.preventDefault();
        inputs[idx + 1].focus();
        inputs[idx + 1].select?.();
      }
    });

    // Backspace to previous when caret at start
    inp.addEventListener("keydown", (e) => {
      if (
        e.key === "Backspace" &&
        inp.selectionStart === 0 &&
        inp.selectionEnd === 0 &&
        idx > 0
      ) {
        e.preventDefault();
        const prev = inputs[idx - 1];
        prev.focus();
        prev.setSelectionRange(prev.value.length, prev.value.length);
      }
    });
  });

  // Ensure combined UUID is set before submit
  document.getElementById("loginForm").addEventListener("submit", (e) => {
    combine();
    console.log("Submitting userId:", hiddenField.value); // debug
    if (!hiddenField.value) {
      e.preventDefault();
      alert("Please enter your User ID");
    }
  });
})();
