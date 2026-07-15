const statusEl = document.getElementById("connection-status");
const sectorPanelsEl = document.getElementById("sector-panels");
const tabsEl = document.querySelector(".entity-tabs");
const searchTabEl = document.getElementById("tab-search");
const searchTabLabelEl = document.getElementById("search-tab-label");
const searchTabDetailEl = document.getElementById("search-tab-detail");
const searchPopoverEl = document.getElementById("entity-search-popover");
const searchFormEl = document.getElementById("entity-search-form");
const searchInputEl = document.getElementById("entity-search-input");
const searchSubmitEl = document.getElementById("entity-search-submit");
const searchFeedbackEl = document.getElementById("entity-search-feedback");
const searchResultEl = document.getElementById("entity-search-result");
const closeSearchEl = document.getElementById("close-entity-search");

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

function openSearchPopover() {
  if (!searchPopoverEl || !searchTabEl) return;
  searchPopoverEl.hidden = false;
  searchTabEl.setAttribute("aria-expanded", "true");
  window.setTimeout(() => searchInputEl?.focus(), 0);
}

function closeSearchPopover() {
  if (!searchPopoverEl || !searchTabEl) return;
  searchPopoverEl.hidden = true;
  searchTabEl.setAttribute("aria-expanded", "false");
}

function activateTab(theme, moveFocus = false) {
  showTab(theme, moveFocus);
  if (theme === "search") openSearchPopover();
  else closeSearchPopover();
}

function bindTabs() {
  document.querySelectorAll(".entity-tab").forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tabTarget));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const tabs = [...document.querySelectorAll(".entity-tab")];
      const index = tabs.indexOf(tab);
      let nextIndex = event.key === "ArrowLeft" ? index - 1 : index + 1;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = tabs.length - 1;
      nextIndex = (nextIndex + tabs.length) % tabs.length;
      activateTab(tabs[nextIndex].dataset.tabTarget, true);
    });
  });
}

function renderSectorDecisions(decisions) {
  if (!sectorPanelsEl || !Array.isArray(decisions)) return;
  sectorPanelsEl.innerHTML = decisions.map(renderDecision).join("");
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

function setSearchFeedback(message, state = "") {
  if (!searchFeedbackEl) return;
  searchFeedbackEl.textContent = message;
  searchFeedbackEl.className = `search-feedback${state ? ` ${state}` : ""}`;
}

function renderSearchLoading(query) {
  if (!searchResultEl) return;
  searchResultEl.className = "search-empty-state search-loading";
  searchResultEl.innerHTML = `
    <span class="search-empty-icon" aria-hidden="true">⌕</span>
    <p class="section-label">Searching Yahoo Finance</p>
    <h2>Looking for “${escapeHtml(query)}”</h2>
    <p>Finding the listed company, latest available price, daily change, and matching finance news.</p>`;
}

function renderSearchError(message) {
  if (!searchResultEl) return;
  searchResultEl.className = "search-empty-state";
  searchResultEl.innerHTML = `
    <span class="search-empty-icon" aria-hidden="true">!</span>
    <p class="section-label">Search unsuccessful</p>
    <h2>We could not load that entity</h2>
    <p>${escapeHtml(message)}</p>
    <button class="secondary-action" type="button" data-open-entity-search>Try another search</button>`;
}

function renderSearchResult(entity) {
  if (!searchResultEl) return;
  const news = entity.news?.length
    ? entity.news.map(renderSearchNews).join("")
    : `<div class="empty-news"><strong>No matching finance news</strong><p>The company was found, but Yahoo Finance returned no recent matching headlines.</p></div>`;

  searchResultEl.className = "search-result-view";
  searchResultEl.innerHTML = `
    <div class="hero-grid">
      <section class="data-card wind-card">
        <p class="section-label">Entity found</p>
        <div class="search-result-summary">
          <span class="entity-found-badge">${escapeHtml(entity.exchange)}</span>
          <h2 class="search-company-name">${escapeHtml(entity.company_name)}</h2>
          <span class="search-company-meta">${escapeHtml(entity.symbol)} · ${escapeHtml(entity.quote_type)}</span>
          <button class="secondary-action" type="button" data-open-entity-search>Search another entity</button>
        </div>
      </section>
      <section class="data-card market-card">
        <p class="section-label">Latest Market Snapshot <span>(${escapeHtml(entity.currency || "Yahoo Finance")})</span></p>
        <div class="market-content">
          <div>
            <strong class="market-price">${escapeHtml(entity.market_price)}</strong>
            <span class="day-change ${escapeHtml(entity.change_direction)}">${escapeHtml(entity.day_change)} Today</span>
          </div>
          <dl class="ticker-details">
            <div><dt>Ticker</dt><dd>${escapeHtml(entity.symbol)}</dd></div>
            <div><dt>Exchange</dt><dd>${escapeHtml(entity.exchange)}</dd></div>
          </dl>
        </div>
      </section>
    </div>
    <div class="search-source-row">
      <span>Retrieved from ${escapeHtml(entity.source)}. Values may be delayed.</span>
      <a href="${escapeHtml(entity.source_url)}" target="_blank" rel="noreferrer">View source ↗</a>
    </div>
    <div class="context-grid">
      <section class="data-card explanation-card">
        <p class="section-label">How to read this result</p>
        <p class="explanation-copy">This is a market-data lookup, not a completed geopolitical forecast. The company has not been assigned a tailwind, headwind, or AI logic score because it has not passed through the project’s company-specific analysis workflow.</p>
      </section>
      <section class="data-card news-card">
        <div class="news-heading"><p class="section-label">Matching Finance News</p><span>${entity.news?.length || 0} stories</span></div>
        <div class="news-list">${news}</div>
      </section>
    </div>`;
}

function renderSearchNews(item) {
  const date = item.published_at ? String(item.published_at).slice(0, 10) : "";
  return `
    <a class="news-item" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
      <div class="news-meta">
        <span class="news-source">${escapeHtml(item.source)}</span>
        ${date ? `<time datetime="${escapeHtml(item.published_at)}">${escapeHtml(date)}</time>` : ""}
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <span class="topic-tag">Finance</span>
    </a>`;
}

async function submitEntitySearch(event) {
  event.preventDefault();
  const query = searchInputEl?.value.trim() || "";
  if (query.length < 2) {
    setSearchFeedback("Enter at least two characters.", "error");
    searchInputEl?.focus();
    return;
  }

  activateTab("search");
  renderSearchLoading(query);
  setSearchFeedback(`Searching for “${query}”…`);
  if (searchSubmitEl) {
    searchSubmitEl.disabled = true;
    searchSubmitEl.textContent = "Searching…";
  }

  try {
    const response = await fetch(`/api/entities/search?q=${encodeURIComponent(query)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The entity search failed.");

    renderSearchResult(payload);
    if (searchTabLabelEl) searchTabLabelEl.textContent = `${payload.company_name} (${payload.symbol})`;
    if (searchTabDetailEl) searchTabDetailEl.textContent = "Search result · click to change";
    setSearchFeedback(`${payload.company_name} was found.`, "success");
    closeSearchPopover();
  } catch (error) {
    const message = error instanceof Error ? error.message : "The entity search failed.";
    renderSearchError(message);
    setSearchFeedback(message, "error");
  } finally {
    if (searchSubmitEl) {
      searchSubmitEl.disabled = false;
      searchSubmitEl.textContent = "Search";
    }
  }
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
searchFormEl?.addEventListener("submit", submitEntitySearch);
closeSearchEl?.addEventListener("click", closeSearchPopover);
searchResultEl?.addEventListener("click", (event) => {
  if (event.target.closest("[data-open-entity-search]")) openSearchPopover();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !searchPopoverEl?.hidden) {
    closeSearchPopover();
    searchTabEl?.focus();
  }
});
loadSnapshot();
connectWebSocket();
