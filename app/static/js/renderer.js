// renderer.js
// Handles Markdown + Prism rendering

const md = window.markdownit({
  html: true,
  linkify: true,
  typographer: true,
});

// ─── Strip <p> everywhere to prevent extra spacing ────────────────
md.renderer.rules.paragraph_open = () => "";
md.renderer.rules.paragraph_close = () => "";

// ─── Prevent Markdown-it from inserting extra newlines after list markers ──
md.renderer.rules.list_item_open = (tokens, idx, options, env, self) => {
  let result = self.renderToken(tokens, idx, options);
  return result.replace(/\n$/, ""); // remove newline after <li>
};
md.renderer.rules.list_item_close = (tokens, idx, options, env, self) => {
  let result = self.renderToken(tokens, idx, options);
  return result.replace(/\n$/, ""); // remove newline before </li>
};

// ─── Render Markdown into element ───────────────────────────────
window.ChatRenderer = {
  renderMarkdown(el, text) {
    let html = md.render(text || "");

    // Remove trailing whitespace / empty lines everywhere
    html = html.replace(/(\s|<br>)+$/gm, "");

    el.innerHTML = html;

    // Prism highlighting
    el.querySelectorAll("pre code").forEach((block) => {
      Prism.highlightElement(block);

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
  },

  rerenderAllMessages() {
    document.querySelectorAll(".message.assistant").forEach((msg) => {
      window.ChatRenderer.renderMarkdown(
        msg,
        msg.dataset.raw || msg.textContent
      );
    });
  },
};
