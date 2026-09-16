// Tab switching, plus hash-based navigation so internal cross-references
// (e.g. a playbook entry's "Evidence" link to a ledger entry) land on the
// right tab and entry instead of doing nothing, since this is a single page
// with no separate URL per tab.
function activateTab(name) {
  const btn = document.querySelector(`.tab-btn[data-tab="${name}"]`);
  const panel = document.getElementById("tab-" + name);
  if (!btn || !panel) return false;
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  btn.classList.add("active");
  panel.classList.add("active");
  return true;
}

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

function handleHash() {
  const hash = decodeURIComponent(location.hash.slice(1));
  if (!hash) return;

  if (hash.startsWith("tab-")) {
    activateTab(hash.slice(4));
    return;
  }

  // Otherwise the hash should be a specific card's id (a ledger/playbook
  // entry slug, an exercise id, a proposal filename, ...). Find it, switch
  // to whichever tab contains it, and scroll it into view with a brief flash
  // so it's obvious what was jumped to.
  const el = document.getElementById(hash);
  if (!el) return;
  const panel = el.closest(".tab-panel");
  if (panel) activateTab(panel.id.slice(4));
  el.scrollIntoView({ behavior: "smooth", block: "start" });
  el.classList.add("jump-highlight");
  setTimeout(() => el.classList.remove("jump-highlight"), 2000);
}

window.addEventListener("hashchange", handleHash);
window.addEventListener("DOMContentLoaded", handleHash);

// Status dropdowns: write straight back to the source markdown file.
// A status line can carry a freeform annotation beyond the bare keyword
// (e.g. "in-progress (Claude leg complete; Codex leg blocked)"). Setting a
// new status necessarily replaces that annotation, since it describes the
// OLD status specifically and would be misleading left attached to the new
// one — so confirm before discarding one, rather than dropping it silently.
document.querySelectorAll(".card").forEach((card) => {
  const select = card.querySelector(".status-select");
  const saveState = card.querySelector(".save-state");
  const rawEl = card.querySelector(".card-status-raw");
  if (!select) return;

  const kind = card.dataset.kind; // "exercise" | "proposal"
  const id = card.dataset.id;
  const endpoint = kind === "exercise"
    ? `/api/exercise/${encodeURIComponent(id)}/status`
    : `/api/proposal/${encodeURIComponent(id)}/status`;

  let previousValue = select.value;

  select.addEventListener("change", async () => {
    const newStatus = select.value;
    const currentRaw = (rawEl && rawEl.textContent.trim()) || previousValue;
    const hasAnnotation = currentRaw.toLowerCase() !== previousValue.toLowerCase();

    if (hasAnnotation) {
      const proceed = confirm(
        `The current status line has a note attached:\n\n"${currentRaw}"\n\n` +
        `Setting it to "${newStatus}" here will replace the whole line with just "${newStatus}" ` +
        `(no note). The old text stays recoverable via git history, but won't be in the file anymore.\n\n` +
        `Continue?`
      );
      if (!proceed) {
        select.value = previousValue;
        return;
      }
    }

    saveState.textContent = "Saving…";
    saveState.className = "save-state";
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      const body = await res.json();
      if (!res.ok || !body.ok) throw new Error(body.error || res.statusText);
      const badge = card.querySelector(".badge");
      badge.className = "badge status-" + newStatus;
      badge.textContent = newStatus;
      if (rawEl) rawEl.textContent = newStatus;
      previousValue = newStatus;
      saveState.textContent = "Saved to file";
      saveState.className = "save-state ok";
      setTimeout(() => { saveState.textContent = ""; }, 2500);
    } catch (err) {
      select.value = previousValue;
      saveState.textContent = "Failed: " + err.message;
      saveState.className = "save-state err";
    }
  });
});
