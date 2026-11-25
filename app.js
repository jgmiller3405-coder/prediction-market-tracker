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

  window.esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  window.changeCell = (d) =>
    d == null ? '<span class="muted">–</span>' : `<span class="${d > 0 ? "up" : d < 0 ? "down" : "muted"}">${RC.signed(d)}</span>`;

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
