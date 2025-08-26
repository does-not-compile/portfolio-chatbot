// renderer.js

// markdown-it instance
const md = window.markdownit({
  html: true,
  linkify: true,
  typographer: true,
});

// --- Core plugin: tighten paragraphs inside list items only when appropriate ---
function tightenNestedListParagraphs(md) {
  md.core.ruler.after(
    "block",
    "tighten_nested_list_paragraphs",
    function (state) {
      const tokens = state.tokens;

      for (let i = 0; i < tokens.length; i++) {
        if (tokens[i].type !== "paragraph_open") continue;

        const inline = tokens[i + 1];
        const close = tokens[i + 2];
        if (
          !inline ||
          inline.type !== "inline" ||
          !close ||
          close.type !== "paragraph_close"
        ) {
          continue;
        }

        // Look ahead: is the very next *non-hidden* token a nested list?
        let k = i + 3;
        while (k < tokens.length && tokens[k].hidden) k++;
        if (
          k < tokens.length &&
          (tokens[k].type === "bullet_list_open" ||
            tokens[k].type === "ordered_list_open")
        ) {
          tokens[i].hidden = true;
          tokens[i + 2].hidden = true;
        }
      }
    }
  );
}

md.use(tightenNestedListParagraphs);

md.renderer.rules.paragraph_open = function (tokens, idx, options, env, self) {
  if (tokens[idx].hidden) return "";
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.paragraph_close = function (tokens, idx, options, env, self) {
  if (tokens[idx].hidden) return "";
  return self.renderToken(tokens, idx, options);
};

// ─── Render Markdown into element ───────────────────────────────
function renderMarkdown(el, text) {
  let html = md.render(text || "");

  // remove newlines that precede tags
  html = html.replace(/\n+(?=<)/g, "");
  // remove trailing whitespace/newline
  html = html.replace(/\s+$/g, "");

  el.innerHTML = html;

  // Prism highlighting
  el.querySelectorAll("pre code").forEach((block) => {
    window.Prism.highlightElement(block); // ⬅️ use window.Prism

    // Wrap with .code-block if not already wrapped
    if (!block.closest(".code-block")) {
      const pre = block.parentElement;
      const wrapper = document.createElement("div");
      wrapper.className = "code-block";

      // detect language
      const lang =
        [...block.classList]
          .find((cls) => cls.startsWith("language-"))
          ?.replace("language-", "") || "text";

      // label
      const label = document.createElement("div");
      label.className = "code-lang-label";
      label.innerHTML = `<span>${lang}</span>`;

      // wrap
      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(label);
      wrapper.appendChild(pre);
    }
  });
}

function rerenderAllMessages() {
  document.querySelectorAll(".message.assistant").forEach((msg) => {
    renderMarkdown(msg, msg.dataset.raw || msg.textContent);
  });
}

// ─── Exports ───────────────────────────────────────────────────
export { renderMarkdown, rerenderAllMessages };
