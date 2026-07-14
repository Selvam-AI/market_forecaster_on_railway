const statusEl = document.getElementById("connection-status");
const decisionBoardEl = document.getElementById("decision-board");
const tabsEl = document.querySelector(".entity-tabs");

let activeTheme = document.querySelector(".entity-tab.active")?.dataset.tabTarget || "offshore";

function setStatus(text, className) {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.className = className;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showTab(theme, moveFocus = false) {
  const tabs = [...document.querySelectorAll(".entity-tab")];
  const panels = [...document.querySelectorAll(".entity-panel")];
  if (!tabs.some((tab) => tab.dataset.tabTarget === theme)) return;

  activeTheme = theme;
  tabs.forEach((tab) => {
    const selected = tab.dataset.tabTarget === theme;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && moveFocus) tab.focus();
  });
  panels.forEach((panel) => {
    const selected = panel.dataset.panel === theme;
    panel.classList.toggle("active", selected);
    panel.hidden = !selected;
  });
}

function bindTabs() {
  document.querySelectorAll(".entity-tab").forEach((tab) => {
    tab.addEventListener("click", () => showTab(tab.dataset.tabTarget));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const tabs = [...document.querySelectorAll(".entity-tab")];
      const index = tabs.indexOf(tab);
      let nextIndex = event.key === "ArrowLeft" ? index - 1 : index + 1;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = tabs.length - 1;
      nextIndex = (nextIndex + tabs.length) % tabs.length;
      showTab(tabs[nextIndex].dataset.tabTarget, true);
    });
  });
}

function renderSectorDecisions(decisions) {
  if (!decisionBoardEl || !Array.isArray(decisions)) return;
  decisionBoardEl.innerHTML = decisions.map(renderDecision).join("");
  showTab(activeTheme);
}

function renderDecision(decision) {
  const theme = escapeHtml(decision.theme);
  const evidence = (decision.evidence || []).length
    ? decision.evidence.map(renderEvidence).join("")
    : `<div class="empty-news"><strong>No matching stories yet</strong><p>Run a news refresh to populate this company’s evidence feed.</p></div>`;

  return `
    <article class="entity-panel" id="panel-${theme}" role="tabpanel" aria-labelledby="tab-${theme}" data-panel="${theme}" hidden>
      <div class="hero-grid">
        <section class="data-card wind-card">
          <p class="section-label">Market Wind Direction</p>
          <div class="wind-content">
            <strong class="wind-badge wind-${escapeHtml(String(decision.wind_direction).toLowerCase())}">${escapeHtml(decision.wind_direction)}</strong>
            <p>${escapeHtml(decision.wind_summary)}</p>
          </div>
        </section>
        <section class="data-card market-card">
          <p class="section-label">Real Market Data <span>(SGX)</span></p>
          <div class="market-content">
            <div>
              <strong class="market-price">${escapeHtml(decision.market_price)}</strong>
              <span class="day-change ${escapeHtml(decision.change_direction)}">${escapeHtml(decision.day_change)} Today</span>
            </div>
            <dl class="ticker-details">
              <div><dt>Ticker</dt><dd>${escapeHtml(decision.ticker)}</dd></div>
              <div><dt>Company</dt><dd>${escapeHtml(decision.company_name)}</dd></div>
            </dl>
          </div>
        </section>
      </div>
      <section class="data-card score-card">
        <div class="score-heading">
          <div><p class="section-label">AI Logic Score</p><strong>${escapeHtml(decision.logic_score)}%</strong></div>
          <span>${escapeHtml(decision.logic_label)}</span>
        </div>
        <div class="score-track" role="progressbar" aria-label="AI logic score" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${escapeHtml(decision.logic_score)}">
          <div class="score-fill score-${theme}" style="--score: ${escapeHtml(decision.logic_score)}%"></div>
        </div>
      </section>
      <div class="context-grid">
        <section class="data-card explanation-card">
          <p class="section-label">Simple Explanation</p>
          <p class="explanation-copy">${escapeHtml(decision.simple_explanation)}</p>
        </section>
        <section class="data-card news-card">
          <div class="news-heading"><p class="section-label">Live Global News Feed</p><span>${decision.evidence?.length || 0} matching stories</span></div>
          <div class="news-list">${evidence}</div>
        </section>
      </div>
      <p class="panel-disclaimer">${escapeHtml(decision.disclaimer)} Educational signal only—not financial advice.</p>
    </article>`;
}

function renderEvidence(item) {
  const date = item.published_at ? String(item.published_at).slice(0, 10) : "";
  return `
    <a class="news-item" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
      <div class="news-meta">
        <span class="news-source">${escapeHtml(item.source)}</span>
        ${date ? `<time datetime="${escapeHtml(item.published_at)}">${escapeHtml(date)}</time>` : ""}
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <span class="topic-tag">${escapeHtml(item.topic)}</span>
    </a>`;
}

function applyPayload(payload) {
  if (payload.sector_decisions) renderSectorDecisions(payload.sector_decisions);
}

async function loadSnapshot() {
  try {
    const response = await fetch("/api/dashboard");
    if (response.ok) applyPayload(await response.json());
  } catch (_error) {
    setStatus("Connection issue", "disconnected");
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/alerts`);

  socket.addEventListener("open", () => setStatus("Live · Connected", "connected"));
  socket.addEventListener("message", (event) => applyPayload(JSON.parse(event.data)));
  socket.addEventListener("close", () => {
    setStatus("Reconnecting", "disconnected");
    window.setTimeout(connectWebSocket, 3000);
  });
  socket.addEventListener("error", () => {
    setStatus("Connection issue", "disconnected");
    socket.close();
  });
}

bindTabs();
loadSnapshot();
connectWebSocket();
