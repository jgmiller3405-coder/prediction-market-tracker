/* Shared page code: navigation bar, data loading, shortlist, service worker, chart colors. */
(function () {
  "use strict";
  const PAGES = [["index.html", "Today"], ["browse.html", "Browse"], ["trends.html", "Trends"]];
  const here = location.pathname.split("/").pop() || "index.html";

  // one navigation bar for every page
  const nav = document.getElementById("nav");
  if (nav) {
    nav.innerHTML =
      '<div class="nav-inner"><a class="brand" href="index.html">Odds Tracker</a><nav>' +
      PAGES.map(([h, t]) => `<a href="${h}"${h === here ? ' aria-current="page"' : ""}>${t}</a>`).join("") +
      '</nav><span id="net" class="net" hidden>offline: showing saved data</span></div>';
  }
  function showNet() {
    const el = document.getElementById("net");
    if (el) el.hidden = navigator.onLine;
  }
  addEventListener("online", showNet);
  addEventListener("offline", showNet);
  showNet();

  async function getText(url) {
    const r = await fetch(url, { cache: "no-cache" });
    if (!r.ok) throw new Error(url + " " + r.status);
    return r.text();
  }
  // Online: the network answers (and the service worker saves a copy). Offline: the saved copy answers.
  window.loadData = async function () {
    const [csv, status] = await Promise.all([getText("data/history.csv"), getText("data/status.json")]);
    return { rows: RC.parseCSV(csv), status: JSON.parse(status) };
  };

  // shortlist, kept in the browser
  const KEY = "odds-tracker-shortlist";
  window.Shortlist = {
    get() {
      try { return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) { return new Set(); }
    },
    toggle(id) {
      const s = this.get();
      s.has(id) ? s.delete(id) : s.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...s])); } catch (e) { /* storage blocked */ }
      return s.has(id);
    },
  };

  // chart colors come from the CSS variables so charts follow the theme
  window.palette = function () {
    const css = getComputedStyle(document.documentElement);
    const v = (n) => css.getPropertyValue(n).trim();
    return { series: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => v("--s" + i)), text: v("--muted"), grid: v("--line"), up: v("--up"), down: v("--down"), accent: v("--accent") };
  };
  window.styleChart = function () {
    const p = palette();
    Chart.defaults.color = p.text;
    Chart.defaults.borderColor = p.grid;
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    return p;
  };

  // ---- small visual helpers ----
  const CAT = { Financial: "fin", "Pop culture": "pop", Political: "pol", Sports: "spt" };
  window.catChip = (c) => `<span class="chip ${CAT[c] || ""}">${esc(c)}</span>`;
  window.probBar = (pct) =>
    pct == null ? '<span class="muted">–</span>'
      : `<span class="prob"><span class="track"><span class="fill" style="width:${Math.max(0, Math.min(100, pct))}%"></span></span><b>${RC.num(pct, 1)}%</b></span>`;
  // sparkline of Yes % over the days in the history (a flat dash when there is only one day)
  window.spark = function (vals) {
    if (!vals || !vals.length) return "";
    const w = 84, h = 24, pad = 3;
    const lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
    const x = (i) => (vals.length === 1 ? w / 2 : pad + (i * (w - 2 * pad)) / (vals.length - 1));
    const y = (v) => (hi === lo ? h / 2 : h - pad - ((v - lo) * (h - 2 * pad)) / span);
    const dir = vals[vals.length - 1] - vals[0];
    const cls = dir > 0 ? "up" : dir < 0 ? "down" : "flat";
    const pts = vals.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    return `<svg class="spark ${cls}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">` +
      (vals.length > 1 ? `<polyline points="${pts}" fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>` : `<line x1="${pad}" x2="${w - pad}" y1="${h / 2}" y2="${h / 2}" stroke-width="2" stroke-dasharray="3 3"/>`) +
      `<circle cx="${x(vals.length - 1).toFixed(1)}" cy="${y(vals[vals.length - 1]).toFixed(1)}" r="2.6"/></svg>`;
  };
  window.esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  window.changeCell = (d) =>
    d == null ? '<span class="muted">–</span>'
      : `<span class="${d > 0 ? "up" : d < 0 ? "down" : "muted"}">${d > 0 ? "▲" : d < 0 ? "▼" : "•"} ${RC.signed(d)}</span>`;

  // footer on every page
  const main = document.querySelector("main");
  if (main) main.insertAdjacentHTML("afterend",
    '<footer class="foot">Odds data from <a href="https://polymarket.com" target="_blank" rel="noopener">Polymarket</a>\'s public API. Updated daily by GitHub Actions. Not financial advice.</footer>');

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
