/* Pure functions shared by all pages (also loadable in Node for checking). */
(function (root) {
  "use strict";

  const NUMERIC = [
    { key: "yes_pct", label: "Yes probability", unit: "%", digits: 2 },
    { key: "best_bid_pct", label: "Best bid", unit: "%", digits: 2 },
    { key: "best_ask_pct", label: "Best ask", unit: "%", digits: 2 },
    { key: "day_change_pts", label: "24h change (source)", unit: "pts", digits: 2 },
    { key: "volume_24h_usd", label: "24h volume", unit: "$", digits: 0 },
    { key: "volume_total_usd", label: "Total volume", unit: "$", digits: 0 },
    { key: "liquidity_usd", label: "Liquidity", unit: "$", digits: 0 },
  ];
  const TOP_N = 5;

  /* ---------- CSV ---------- */
  function parseCSV(text) {
    const rows = [];
    let row = [], field = "", quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (quoted) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; } else quoted = false;
        } else field += c;
      } else if (c === '"') quoted = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field); field = "";
        if (row.length > 1 || row[0] !== "") rows.push(row);
        row = [];
      } else field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    if (!rows.length) return [];
    const header = rows.shift();
    const numeric = new Set(NUMERIC.map((n) => n.key));
    return rows.map((r) => {
      const o = {};
      header.forEach((h, i) => {
        const v = r[i] === undefined ? "" : r[i];
        o[h] = numeric.has(h) ? (v === "" ? null : Number(v)) : v;
      });
      return o;
    });
  }

  /* ---------- history helpers ---------- */
  const dates = (rows) => [...new Set(rows.map((r) => r.date))].sort();
  const onDate = (rows, d) => rows.filter((r) => r.date === d);
  const indexById = (rows) => new Map(rows.map((r) => [r.item_id, r]));
  const round2 = (x) => Math.round(x * 100) / 100;

  /* The move rule (same as tracker/moves.py): change in yes_pct since the previous day in the
     history, ranked by size (ties: larger 24h volume, then smaller item_id), top 5, non-zero. */
  function compareLatest(rows) {
    const ds = dates(rows);
    const date = ds[ds.length - 1] || null;
    const prevDate = ds.length > 1 ? ds[ds.length - 2] : null;
    const cur = indexById(date ? onDate(rows, date) : []);
    const prev = indexById(prevDate ? onDate(rows, prevDate) : []);
    const changes = new Map(); // item_id -> change in points (only items on both days)
    const all = [];
    for (const [id, r] of cur) {
      const p = prev.get(id);
      if (!p || r.yes_pct == null || p.yes_pct == null) continue;
      const delta = round2(r.yes_pct - p.yes_pct);
      changes.set(id, delta);
      if (delta !== 0) all.push({ item_id: id, item: r.item, old: p.yes_pct, new: r.yes_pct, delta, vol: r.volume_24h_usd || 0 });
    }
    all.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta) || b.vol - a.vol || (a.item_id < b.item_id ? -1 : 1));
    return {
      date, prevDate, cur, prev, changes,
      moves: all.slice(0, TOP_N),
      appeared: prevDate ? [...cur.keys()].filter((i) => !prev.has(i)).sort() : [],
      disappeared: [...prev.keys()].filter((i) => !cur.has(i)).sort(),
    };
  }

  // item_id -> list of yes_pct values in date order (for sparklines)
  function seriesById(rows) {
    const m = new Map();
    for (const r of [...rows].sort((a, b) => (a.date < b.date ? -1 : 1))) {
      if (r.yes_pct == null) continue;
      if (!m.has(r.item_id)) m.set(r.item_id, []);
      m.get(r.item_id).push(r.yes_pct);
    }
    return m;
  }

  /* ---------- statistics for the Trends page ---------- */
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
  const stdev = (a) => (a.length < 2 ? 0 : Math.sqrt(a.reduce((s, x) => s + (x - mean(a)) ** 2, 0) / (a.length - 1)));

  // per item: first and latest yes_pct and the difference
  function sinceFirst(rows) {
    const by = new Map();
    for (const r of rows) {
      if (r.yes_pct == null) continue;
      if (!by.has(r.item_id)) by.set(r.item_id, []);
      by.get(r.item_id).push(r);
    }
    const out = [];
    for (const [id, list] of by) {
      list.sort((a, b) => (a.date < b.date ? -1 : 1));
      const first = list[0], last = list[list.length - 1];
      out.push({ item_id: id, item: last.item, firstDate: first.date, lastDate: last.date,
        first: first.yes_pct, last: last.yes_pct, delta: round2(last.yes_pct - first.yes_pct), days: list.length });
    }
    return out;
  }

  // per consecutive pair of dates: mean absolute change in yes_pct over items present on both days
  function dailyMoves(rows) {
    const ds = dates(rows), out = [];
    for (let i = 1; i < ds.length; i++) {
      const a = indexById(onDate(rows, ds[i - 1])), b = onDate(rows, ds[i]);
      const diffs = [];
      for (const r of b) {
        const p = a.get(r.item_id);
        if (p && p.yes_pct != null && r.yes_pct != null) diffs.push(Math.abs(r.yes_pct - p.yes_pct));
      }
      if (diffs.length) out.push({ date: ds[i], prev: ds[i - 1], value: mean(diffs), n: diffs.length });
    }
    return out;
  }

  // yes_pct on one date: min, max, spread, standard deviation and a 10-point-wide histogram
  function spreadOn(rows, date) {
    const v = onDate(rows, date).filter((r) => r.yes_pct != null);
    const bins = Array(10).fill(0);
    v.forEach((r) => { bins[Math.min(9, Math.floor(r.yes_pct / 10))]++; });
    const sorted = [...v].sort((a, b) => a.yes_pct - b.yes_pct);
    return { n: v.length, min: sorted[0], max: sorted[sorted.length - 1],
      spread: v.length ? sorted[sorted.length - 1].yes_pct - sorted[0].yes_pct : 0,
      sd: stdev(v.map((r) => r.yes_pct)), bins };
  }

  // 24h volume per event on one date
  function volumeByEvent(rows, date) {
    const m = new Map();
    for (const r of onDate(rows, date)) m.set(r.event, (m.get(r.event) || 0) + (r.volume_24h_usd || 0));
    const total = [...m.values()].reduce((s, x) => s + x, 0);
    return { total, list: [...m].map(([event, volume]) => ({ event, volume, share: total ? volume / total : 0 })).sort((a, b) => b.volume - a.volume) };
  }

  // per item: standard deviation of the day-to-day changes in yes_pct
  function volatility(rows) {
    const by = new Map();
    for (const r of rows) {
      if (r.yes_pct == null) continue;
      if (!by.has(r.item_id)) by.set(r.item_id, []);
      by.get(r.item_id).push(r);
    }
    const out = [];
    for (const [id, list] of by) {
      list.sort((a, b) => (a.date < b.date ? -1 : 1));
      const diffs = [];
      for (let i = 1; i < list.length; i++) diffs.push(list[i].yes_pct - list[i - 1].yes_pct);
      out.push({ item_id: id, item: list[list.length - 1].item, sd: stdev(diffs), changes: diffs.length });
    }
    return out;
  }

  /* ---------- formatting ---------- */
  const num = (x, d = 2) => (x == null ? "–" : Number(x).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }));
  const usd = (x) => (x == null ? "–" : "$" + Number(x).toLocaleString("en-US", { maximumFractionDigits: 0 }));
  const signed = (x, d = 2) => (x == null ? "–" : (x > 0 ? "+" : "") + Number(x).toFixed(d));

  const api = { NUMERIC, TOP_N, parseCSV, dates, onDate, indexById, compareLatest, seriesById, sinceFirst, dailyMoves,
    spreadOn, volumeByEvent, volatility, mean, stdev, num, usd, signed };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RC = api;
})(typeof window !== "undefined" ? window : this);
