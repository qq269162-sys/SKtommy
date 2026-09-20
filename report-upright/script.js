const D = JSON.parse(document.getElementById("payload").textContent);
const YS = D.years, N = YS.length;          // 1999..2025  (size / return / cum / flow)
const HY = D.hy, M = HY.length;             // 2003..2025  (holdings series)
const tip = document.getElementById("tip");
const NS = "http://www.w3.org/2000/svg";
const el = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };

function showTip(evt, html) {
  tip.innerHTML = html; tip.style.opacity = 1;
  const r = tip.getBoundingClientRect();
  let x = evt.clientX + 14, y = evt.clientY - r.height - 12;
  if (x + r.width > innerWidth - 8) x = evt.clientX - r.width - 14;
  if (x < 8) x = 8;
  if (y < 8) y = evt.clientY + 18;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
const hideTip = () => { tip.style.opacity = 0; };
const path = p => p.map((q, i) => (i ? "L" : "M") + q[0].toFixed(1) + " " + q[1].toFixed(1)).join(" ");

function frame(svg, o, years) {
  const { W, H, ml, mr, mt, mb, yMin, yMax, ticks, fmt, every } = o;
  const n = years.length, pw = W - ml - mr, ph = H - mt - mb;
  const X = i => ml + (pw * i) / (n - 1);
  const Y = v => mt + ph - (ph * (v - yMin)) / (yMax - yMin);
  ticks.forEach(t => {
    svg.appendChild(el("line", { x1: ml, x2: ml + pw, y1: Y(t), y2: Y(t), class: "grid-line" }));
    const lb = el("text", { x: ml - 9, y: Y(t) + 4, class: "axis-txt", "text-anchor": "end" });
    lb.textContent = fmt ? fmt(t) : t; svg.appendChild(lb);
  });
  years.forEach((y, i) => {
    if (i % (every || 2)) return;
    const lb = el("text", { x: X(i), y: mt + ph + 20, class: "axis-txt", "text-anchor": "middle" });
    lb.textContent = "’" + String(y).slice(2); svg.appendChild(lb);
  });
  return { X, Y, pw, ph };
}
function crosshair(svg, o, X, years, rowsFor) {
  const { W, ml, mr, mt, mb, H } = o, n = years.length, pw = W - ml - mr, ph = H - mt - mb;
  const rule = el("line", { y1: mt, y2: mt + ph, style: "stroke:var(--rule-2);stroke-width:1", opacity: 0 });
  svg.appendChild(rule);
  const hit = el("rect", { x: ml, y: mt, width: pw, height: ph, style: "fill:transparent" });
  svg.appendChild(hit);
  hit.addEventListener("pointermove", e => {
    const b = svg.getBoundingClientRect();
    const sx = ((e.clientX - b.left) / b.width) * W;
    let i = Math.round(((sx - ml) / pw) * (n - 1));
    i = Math.max(0, Math.min(n - 1, i));
    rule.setAttribute("x1", X(i)); rule.setAttribute("x2", X(i)); rule.setAttribute("opacity", 1);
    showTip(e, `<div class="th">FY${years[i]} · 09/30</div>` + rowsFor(i));
  });
  hit.addEventListener("pointerleave", () => { rule.setAttribute("opacity", 0); hideTip(); });
}
function endpoint(svg, x, y, txt, c) {
  svg.appendChild(el("circle", { cx: x, cy: y, r: 4, style: `fill:var(${c});stroke:var(--surface);stroke-width:2` }));
  const t = el("text", { x: x + 11, y: y + 4, class: "dlabel", style: `fill:var(${c})` });
  t.textContent = txt; svg.appendChild(t);
}

/* 1 — net assets */
(function () {
  const svg = document.getElementById("c1");
  const o = { W: 900, H: 240, ml: 52, mr: 96, mt: 14, mb: 34, yMin: 0, yMax: 28, ticks: [0, 10, 20, 28], fmt: t => "$" + t + "M" };
  const { X, Y } = frame(svg, o, YS);
  const pts = D.size.map((v, i) => [X(i), Y(v)]);
  svg.appendChild(el("path", { d: path(pts) + ` L${X(N - 1).toFixed(1)} ${Y(0).toFixed(1)} L${X(0).toFixed(1)} ${Y(0).toFixed(1)} Z`, style: "fill:var(--s1);opacity:.13" }));
  svg.appendChild(el("path", { d: path(pts), style: "fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round;stroke-linecap:round" }));
  endpoint(svg, pts[N - 1][0], pts[N - 1][1], "$" + D.size[N - 1].toFixed(1) + "M", "--s1");
  crosshair(svg, o, X, YS, i =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(--s1)"></i>净资产</span><span>$${D.size[i].toFixed(2)}M</span></div>`);
})();

/* 2 — annual returns, diverging bars */
(function () {
  const svg = document.getElementById("c2");
  const o = { W: 900, H: 250, ml: 52, mr: 96, mt: 14, mb: 34, yMin: -60, yMax: 100, ticks: [-50, 0, 50, 100], fmt: t => t + "%" };
  const { X, Y, pw } = frame(svg, o, YS);
  svg.appendChild(el("line", { x1: 52, x2: 900 - 96, y1: Y(0), y2: Y(0), style: "stroke:var(--rule-2);stroke-width:1" }));
  const bw = Math.max(6, (pw / N) * 0.62);
  D.ret.forEach((v, i) => {
    const y0 = Y(0), y1 = Y(v);
    svg.appendChild(el("rect", {
      x: X(i) - bw / 2, y: Math.min(y0, y1), width: bw, height: Math.max(1.5, Math.abs(y1 - y0)), rx: 1.5,
      style: `fill:var(${v >= 0 ? "--s1" : "--neg"})`
    }));
  });
  const best = D.ret.indexOf(Math.max(...D.ret)), worst = D.ret.indexOf(Math.min(...D.ret));
  [[best, "--s1"], [worst, "--neg"]].forEach(([i, c]) => {
    const t = el("text", { x: X(i), y: D.ret[i] >= 0 ? Y(D.ret[i]) - 7 : Y(D.ret[i]) + 15, class: "dlabel", "text-anchor": "middle", style: `fill:var(${c})` });
    t.textContent = (D.ret[i] > 0 ? "+" : "") + D.ret[i].toFixed(1) + "%"; svg.appendChild(t);
  });
  crosshair(svg, o, X, YS, i =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${D.ret[i] >= 0 ? "--s1" : "--neg"})"></i>年度回报</span><span>${D.ret[i] > 0 ? "+" : ""}${D.ret[i].toFixed(2)}%</span></div>`);
})();

/* 3 — implied flows */
(function () {
  const svg = document.getElementById("c3");
  const o = { W: 900, H: 260, ml: 56, mr: 96, mt: 16, mb: 34, yMin: -4, yMax: 8, ticks: [-4, -2, 0, 4, 8], fmt: t => (t > 0 ? "+$" : t < 0 ? "−$" : "$") + Math.abs(t) + "M" };
  const { X, Y, pw } = frame(svg, o, YS);
  svg.appendChild(el("line", { x1: 56, x2: 900 - 96, y1: Y(0), y2: Y(0), style: "stroke:var(--rule-2);stroke-width:1" }));
  const bw = Math.max(6, (pw / N) * 0.62);
  D.flow.forEach((v, i) => {
    if (v === null) return;
    const y0 = Y(0), y1 = Y(v);
    svg.appendChild(el("rect", {
      x: X(i) - bw / 2, y: Math.min(y0, y1), width: bw, height: Math.max(1.5, Math.abs(y1 - y0)), rx: 1.5,
      style: `fill:var(${v >= 0 ? "--s1" : "--neg"})`
    }));
  });
  const i17 = YS.indexOf(2017);
  const lab = el("text", { x: X(i17), y: Y(D.flow[i17]) - 8, class: "dlabel", "text-anchor": "middle", style: "fill:var(--s1)" });
  lab.textContent = "+$7.69M"; svg.appendChild(lab);
  const i25 = YS.indexOf(2025);
  const lab2 = el("text", { x: X(i25), y: Y(D.flow[i25]) + 15, class: "dlabel", "text-anchor": "middle", style: "fill:var(--neg)" });
  lab2.textContent = "−$3.22M"; svg.appendChild(lab2);
  crosshair(svg, o, X, YS, i => D.flow[i] === null ? "<div class=\"tr\"><span>成立年，无上年可比</span></div>" :
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${D.flow[i] >= 0 ? "--s1" : "--neg"})"></i>隐含净申赎</span><span>${D.flow[i] > 0 ? "+" : "−"}$${Math.abs(D.flow[i]).toFixed(2)}M</span></div>` +
    `<div class="tr"><span>当年回报</span><span>${D.ret[i] > 0 ? "+" : ""}${D.ret[i].toFixed(1)}%</span></div>`);
})();

/* 4 — growth of 10k */
(function () {
  const svg = document.getElementById("c4");
  const o = { W: 900, H: 250, ml: 58, mr: 96, mt: 16, mb: 34, yMin: 0, yMax: 22000, ticks: [0, 5000, 10000, 15000, 20000], fmt: t => "$" + (t / 1000) + "k" };
  const { X, Y } = frame(svg, o, YS);
  svg.appendChild(el("line", { x1: 58, x2: 900 - 96, y1: Y(10000), y2: Y(10000), style: "stroke:var(--rule-2);stroke-width:1;stroke-dasharray:none" }));
  const pts = D.cum.map((v, i) => [X(i), Y(v)]);
  svg.appendChild(el("path", { d: path(pts), style: "fill:none;stroke:var(--s2);stroke-width:2;stroke-linejoin:round;stroke-linecap:round" }));
  endpoint(svg, pts[N - 1][0], pts[N - 1][1], "$20,403", "--s2");
  const lb = el("text", { x: 900 - 96 + 11, y: Y(10000) + 4, class: "dlabel", style: "fill:var(--ink-3)" });
  lb.textContent = "起点 $10k"; svg.appendChild(lb);
  crosshair(svg, o, X, YS, i =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(--s2)"></i>累计值</span><span>$${D.cum[i].toLocaleString()}</span></div>` +
    `<div class="tr"><span>当年回报</span><span>${D.ret[i] > 0 ? "+" : ""}${D.ret[i].toFixed(1)}%</span></div>`);
})();

/* 5 — concentration */
(function () {
  const svg = document.getElementById("c5");
  const o = { W: 900, H: 300, ml: 48, mr: 104, mt: 16, mb: 34, yMin: 0, yMax: 100, ticks: [0, 25, 50, 75, 100], fmt: t => t + "%" };
  const { X, Y } = frame(svg, o, HY);
  const S = [{ k: "top10", n: "前十大合计", c: "--s1" }, { k: "top5", n: "前五大合计", c: "--s2" }, { k: "top1", n: "第一大持仓", c: "--s3" }];
  S.forEach(s => {
    const pts = D[s.k].map((v, i) => [X(i), Y(v)]);
    svg.appendChild(el("path", { d: path(pts), style: `fill:none;stroke:var(${s.c});stroke-width:2;stroke-linejoin:round;stroke-linecap:round` }));
    endpoint(svg, pts[M - 1][0], pts[M - 1][1], D[s.k][M - 1].toFixed(1) + "%", s.c);
  });
  crosshair(svg, o, X, HY, i => S.map(s =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${s.c})"></i>${s.n}</span><span>${D[s.k][i].toFixed(1)}%</span></div>`).join("") +
    `<div class="tr"><span>持股只数</span><span>${D.nstock[i]}</span></div>`);
  document.getElementById("l5").innerHTML = S.map(s =>
    `<span class="lg"><i class="sw" style="background:var(${s.c})"></i>${s.n}</span>`).join("");
})();

/* 6 — asset mix */
(function () {
  const svg = document.getElementById("c6");
  const o = { W: 900, H: 280, ml: 48, mr: 104, mt: 16, mb: 34, yMin: 0, yMax: 110, ticks: [0, 25, 50, 75, 100], fmt: t => t + "%" };
  const { X, Y } = frame(svg, o, HY);
  const S = [{ k: "stock", n: "个股", c: "--s1" }, { k: "etf", n: "ETF", c: "--s2" }, { k: "cash", n: "现金与货币基金", c: "--s3" }];
  const base = new Array(M).fill(0);
  S.forEach(s => {
    const lo = base.slice(), hi = base.map((b, i) => b + D[s.k][i]);
    const pts = hi.map((v, i) => [X(i), Y(v)]).concat(lo.map((v, i) => [X(i), Y(v)]).reverse());
    svg.appendChild(el("path", { d: path(pts) + " Z", style: `fill:var(${s.c});stroke:var(--surface);stroke-width:2;stroke-linejoin:round` }));
    hi.forEach((v, i) => base[i] = v);
  });
  crosshair(svg, o, X, HY, i => S.map(s =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${s.c})"></i>${s.n}</span><span>${D[s.k][i].toFixed(1)}%</span></div>`).join(""));
  document.getElementById("l6").innerHTML = S.map(s =>
    `<span class="lg"><i class="sw" style="background:var(${s.c})"></i>${s.n} <span class="mono" style="color:var(--ink-3)">${D[s.k][M - 1].toFixed(1)}%</span></span>`).join("");
})();

/* 7 — heatmap */
(function () {
  const wrap = document.getElementById("hm");
  const bucket = v => v === 0 ? 0 : v < 1 ? 1 : v < 3 ? 2 : v < 6 ? 3 : v < 10 ? 4 : v < 18 ? 5 : v < 30 ? 6 : 7;
  const head = document.createElement("div");
  head.className = "hm-row";
  head.innerHTML = "<div></div>" + HY.map(y => `<div class="hm-head">’${String(y).slice(2)}</div>`).join("");
  wrap.appendChild(head);
  D.heat.forEach(r => {
    const row = document.createElement("div");
    row.className = "hm-row";
    const nm = document.createElement("div");
    nm.className = "hm-name"; nm.textContent = r.name; row.appendChild(nm);
    r.v.forEach((v, i) => {
      const c = document.createElement("div");
      c.className = "cell";
      c.style.background = `var(--r${bucket(v)})`;
      if (v >= 10) { c.textContent = v.toFixed(0); c.style.color = "var(--rt4)"; }
      const html = `<div class="th">FY${HY[i]} · 09/30</div><div class="tr"><span>${r.name}</span><span>${v === 0 ? "未持有" : v.toFixed(2) + "%"}</span></div>`;
      c.addEventListener("pointerenter", e => showTip(e, html));
      c.addEventListener("pointermove", e => showTip(e, html));
      c.addEventListener("pointerleave", hideTip);
      row.appendChild(c);
    });
    wrap.appendChild(row);
  });
  document.getElementById("hmscale").innerHTML =
    '<span>占净资产</span><span class="bar">' +
    [0, 1, 2, 3, 4, 5, 6, 7].map(i => `<i style="background:var(--r${i})"></i>`).join("") +
    '</span><span class="mono" style="font-size:11px">未持有 · &lt;1 · 1–3 · 3–6 · 6–10 · 10–18 · 18–30 · ≥30%</span>';
})();

/* 8 — per-year top ten */
(function () {
  const chips = document.getElementById("chips"), tb = document.getElementById("tbody");
  const render = y => {
    const rows = D.tables[String(y)], max = rows[0][1];
    tb.innerHTML = rows.map((r, i) => `<tr>
      <td class="r">${i + 1}</td>
      <td>${r[0]}</td>
      <td><span style="display:flex;align-items:center;gap:9px">
        <span class="mono" style="width:48px;text-align:right">${r[1].toFixed(2)}%</span>
        <span class="wbar" style="width:${(r[1] / max * 84).toFixed(1)}px"></span></span></td>
      <td class="n">$${r[2].toLocaleString()}k</td></tr>`).join("");
    [...chips.children].forEach(c => c.setAttribute("aria-pressed", String(+c.dataset.y === y)));
  };
  HY.forEach(y => {
    const b = document.createElement("button");
    b.className = "chip"; b.type = "button"; b.dataset.y = y; b.id = "chip-" + y;
    b.textContent = "FY" + y; b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", () => render(y));
    chips.appendChild(b);
  });
  render(HY[M - 1]);

  document.getElementById("printTables").innerHTML =
    '<div class="ptgrid">' + HY.map(y => {
      const rows = D.tables[String(y)];
      return `<div class="pt"><h3>FY${y} · 09/30</h3><table><tbody>` +
        rows.map((r, i) => `<tr><td class="r">${i + 1}</td><td>${r[0]}</td>` +
          `<td class="n">${r[1].toFixed(2)}%</td><td class="n">$${r[2].toLocaleString()}k</td></tr>`).join("") +
        `</tbody></table></div>`;
    }).join("") + '</div>';
})();
