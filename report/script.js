const D = JSON.parse(document.getElementById("payload").textContent);
const YS = D.years, N = YS.length;
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
const path = pts => pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");

function frame(svg, o) {
  const { W, H, ml, mr, mt, mb, yMax, ticks } = o;
  const pw = W - ml - mr, ph = H - mt - mb;
  const X = i => ml + (pw * i) / (N - 1);
  const Y = v => mt + ph - (ph * v) / yMax;
  ticks.forEach(t => {
    svg.appendChild(el("line", { x1: ml, x2: ml + pw, y1: Y(t), y2: Y(t), class: "grid-line" }));
    const lb = el("text", { x: ml - 9, y: Y(t) + 4, class: "axis-txt", "text-anchor": "end" });
    lb.textContent = t + "%"; svg.appendChild(lb);
  });
  YS.forEach((y, i) => {
    if (i % 2) return;
    const lb = el("text", { x: X(i), y: mt + ph + 20, class: "axis-txt", "text-anchor": "middle" });
    lb.textContent = "’" + String(y).slice(2); svg.appendChild(lb);
  });
  return { X, Y, pw, ph };
}

function crosshair(svg, o, X, rowsFor) {
  const { W, ml, mr, mt, mb, H } = o, pw = W - ml - mr, ph = H - mt - mb;
  const rule = el("line", { y1: mt, y2: mt + ph, style: "stroke:var(--rule-2);stroke-width:1", opacity: 0 });
  svg.appendChild(rule);
  const hit = el("rect", { x: ml, y: mt, width: pw, height: ph, style: "fill:transparent" });
  svg.appendChild(hit);
  hit.addEventListener("pointermove", e => {
    const b = svg.getBoundingClientRect();
    const sx = ((e.clientX - b.left) / b.width) * W;
    let i = Math.round(((sx - ml) / pw) * (N - 1));
    i = Math.max(0, Math.min(N - 1, i));
    rule.setAttribute("x1", X(i)); rule.setAttribute("x2", X(i)); rule.setAttribute("opacity", 1);
    showTip(e, `<div class="th">FY${YS[i]} · 11/30</div>` + rowsFor(i));
  });
  hit.addEventListener("pointerleave", () => { rule.setAttribute("opacity", 0); hideTip(); });
}

function endpoint(svg, x, y, v, c) {
  svg.appendChild(el("circle", { cx: x, cy: y, r: 4, style: `fill:var(${c});stroke:var(--surface);stroke-width:2` }));
  const t = el("text", { x: x + 11, y: y + 4, class: "dlabel", style: `fill:var(${c})` });
  t.textContent = v.toFixed(1) + "%"; svg.appendChild(t);
}

/* 1 — concentration */
(function () {
  const svg = document.getElementById("c1");
  const o = { W: 900, H: 330, ml: 48, mr: 104, mt: 16, mb: 38, yMax: 80, ticks: [0, 20, 40, 60, 80] };
  const { X, Y } = frame(svg, o);
  const S = [
    { k: "top10", n: "前十大合计", c: "--s1" },
    { k: "top5", n: "前五大合计", c: "--s2" },
    { k: "top1", n: "第一大持仓", c: "--s3" }
  ];
  S.forEach(s => {
    const pts = D[s.k].map((v, i) => [X(i), Y(v)]);
    svg.appendChild(el("path", { d: path(pts), style: `fill:none;stroke:var(${s.c});stroke-width:2;stroke-linejoin:round;stroke-linecap:round` }));
    endpoint(svg, pts[N - 1][0], pts[N - 1][1], D[s.k][N - 1], s.c);
  });
  crosshair(svg, o, X, i => S.map(s =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${s.c})"></i>${s.n}</span><span>${D[s.k][i].toFixed(1)}%</span></div>`).join(""));
  document.getElementById("l1").innerHTML = S.map(s =>
    `<span class="lg"><i class="sw" style="background:var(${s.c})"></i>${s.n}</span>`).join("");
})();

/* 2 — regions, stacked */
(function () {
  const svg = document.getElementById("c2");
  const o = { W: 900, H: 330, ml: 48, mr: 104, mt: 16, mb: 38, yMax: 110, ticks: [0, 25, 50, 75, 100] };
  const { X, Y } = frame(svg, o);
  const NM = { KR: "韩国", TW: "台湾", CN: "中国／香港", IN: "印度", BR: "巴西", RU: "俄罗斯", OT: "其他市场" };
  const C = { KR: "--s1", TW: "--s2", CN: "--s3", IN: "--s4", BR: "--s5", RU: "--s6", OT: "--s7" };
  const order = D.regions, base = new Array(N).fill(0);
  order.forEach(g => {
    const lo = base.slice(), hi = base.map((b, i) => b + D.cser[g][i]);
    const pts = hi.map((v, i) => [X(i), Y(v)]).concat(lo.map((v, i) => [X(i), Y(v)]).reverse());
    svg.appendChild(el("path", { d: path(pts) + " Z", style: `fill:var(${C[g]});stroke:var(--surface);stroke-width:2;stroke-linejoin:round` }));
    hi.forEach((v, i) => base[i] = v);
  });
  crosshair(svg, o, X, i => order.map(g =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(${C[g]})"></i>${NM[g]}</span><span>${D.cser[g][i].toFixed(1)}%</span></div>`).join(""));
  document.getElementById("l2").innerHTML = order.map(g =>
    `<span class="lg"><i class="sw" style="background:var(${C[g]})"></i>${NM[g]} <span class="mono" style="color:var(--ink-3)">${D.cser[g][N - 1].toFixed(1)}%</span></span>`).join("");
})();

/* 3 — semiconductor complex */
(function () {
  const svg = document.getElementById("c3");
  const o = { W: 900, H: 220, ml: 48, mr: 104, mt: 14, mb: 32, yMax: 60, ticks: [0, 20, 40, 60] };
  const { X, Y } = frame(svg, o);
  const v = D.semis, line = v.map((d, i) => [X(i), Y(d)]);
  const area = line.concat([[X(N - 1), Y(0)], [X(0), Y(0)]]);
  svg.appendChild(el("path", { d: path(area) + " Z", style: "fill:var(--s1);opacity:.14" }));
  svg.appendChild(el("path", { d: path(line), style: "fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round;stroke-linecap:round" }));
  endpoint(svg, line[N - 1][0], line[N - 1][1], v[N - 1], "--s1");
  crosshair(svg, o, X, i =>
    `<div class="tr"><span class="tk"><i class="sw" style="background:var(--s1)"></i>半导体／存储合计</span><span>${v[i].toFixed(1)}%</span></div>`);
})();

/* 4 — heatmap */
(function () {
  const wrap = document.getElementById("hm");
  const bucket = v => v === 0 ? 0 : v < 1 ? 1 : v < 2 ? 2 : v < 4 ? 3 : v < 6 ? 4 : v < 9 ? 5 : v < 14 ? 6 : 7;
  const head = document.createElement("div");
  head.className = "hm-row";
  head.innerHTML = "<div></div>" + YS.map(y => `<div class="hm-head">’${String(y).slice(2)}</div>`).join("");
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
      if (v >= 6) { c.textContent = v.toFixed(1); c.style.color = "var(--rt4)"; }
      const html = `<div class="th">FY${YS[i]} · 11/30</div><div class="tr"><span>${r.name}</span><span>${v === 0 ? "未持有" : v.toFixed(2) + "%"}</span></div>`;
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
    '</span><span class="mono" style="font-size:11px">未持有 · &lt;1 · 1–2 · 2–4 · 4–6 · 6–9 · 9–14 · ≥14%</span>';
})();

/* 5 — per-year top ten */
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
      <td class="n">$${r[2].toLocaleString()}M</td></tr>`).join("");
    [...chips.children].forEach(c => c.setAttribute("aria-pressed", String(+c.dataset.y === y)));
  };
  YS.forEach(y => {
    const b = document.createElement("button");
    b.className = "chip"; b.type = "button"; b.dataset.y = y; b.id = "chip-" + y;
    b.textContent = "FY" + y; b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", () => render(y));
    chips.appendChild(b);
  });
  render(YS[N - 1]);
})();
