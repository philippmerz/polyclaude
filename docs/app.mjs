const DAY = 86400000;
const NS = 'http://www.w3.org/2000/svg';
const SOURCE_ROOT = 'https://github.com/philippmerz/polyclaude/blob/main/';
const COLORS = { depth: '#087f72', mark: '#98aaa6', spy: '#bc8841' };
const REQUIRED = ['timestamp_utc', 'trading_capital_usd', 'total_mark_usd', 'gas_usd', 'pm_mark_usd', 'pm_depth_usd', 'settled_pnl_usd', 'source', 'note'];

export function parseCSV(text) {
  const rows = []; let row = [], cell = '', quoted = false, closed = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') { quoted = false; closed = true; }
      else cell += c;
    } else if (c === ',' || c === '\n' || c === '\r') {
      row.push(cell); cell = ''; closed = false;
      if (c !== ',') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        if (row.some(x => x !== '')) rows.push(row);
        row = [];
      }
    } else if (c === '"') {
      if (cell || closed) throw new Error('Unexpected quote in CSV.');
      quoted = true;
    } else {
      if (closed) throw new Error('Unexpected text after CSV quote.');
      cell += c;
    }
  }
  if (quoted) throw new Error('Unclosed quote in CSV.');
  if (cell || row.length || closed) { row.push(cell); if (row.some(x => x !== '')) rows.push(row); }
  return rows;
}

function records(text, required) {
  const [header, ...body] = parseCSV(text.replace(/^\uFEFF/, ''));
  if (!header || new Set(header).size !== header.length || required.some(x => !header.includes(x))) throw new Error('CSV columns are missing or duplicated.');
  return body.map((cells, i) => {
    if (cells.length !== header.length) throw new Error(`CSV record ${i + 2} has the wrong number of fields.`);
    return Object.fromEntries(header.map((h, j) => [h, cells[j]]));
  });
}

function number(value, field, optional = false) {
  if (value === '' && optional) return null;
  if (value.trim() === '' || !/^-?\d+(?:\.\d+)?$/.test(value)) throw new Error(`Invalid ${field} in CSV.`);
  const n = Number(value);
  if (!Number.isFinite(n)) throw new Error(`Invalid ${field} in CSV.`);
  return n;
}

function timestamp(value) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)) throw new Error('Use UTC timestamps ending in Z.');
  const t = Date.parse(value);
  if (!Number.isFinite(t) || new Date(t).toISOString() !== value.replace('Z', '.000Z')) throw new Error('Invalid UTC timestamp.');
  return t;
}

function ordered(rows) {
  if (!rows.length) throw new Error('No recorded observations.');
  rows.forEach((r, i) => { if (i && r.t <= rows[i - 1].t) throw new Error('CSV timestamps must be unique and increasing.'); });
  return rows;
}

export function parsePerformance(text) {
  return ordered(records(text, REQUIRED).map(raw => {
    const capital = number(raw.trading_capital_usd, 'trading capital');
    const total = number(raw.total_mark_usd, 'whole-account mark');
    const gas = number(raw.gas_usd, 'funded gas', true);
    const pm = number(raw.pm_mark_usd, 'PM midpoint', true);
    const bids = number(raw.pm_depth_usd, 'PM depth', true);
    const settled = number(raw.settled_pnl_usd, 'settled P&L', true);
    const timestampKind = raw.timestamp_kind || 'second';
    if (!['second', 'minute', 'check_window', 'day'].includes(timestampKind)) throw new Error('Invalid timestamp precision.');
    if (capital <= 0 || total < 0 || [gas, pm, bids].some(x => x !== null && x < 0)) throw new Error('Invalid negative value or nonpositive capital.');
    if (gas !== null && gas > total) throw new Error('Funded gas exceeds the account value.');
    if (pm !== null && pm > total) throw new Error('PM midpoint exceeds the account value.');
    const mark = gas === null ? null : total - gas;
    const depth = mark === null || pm === null || bids === null ? null : mark - pm + bids;
    if (depth !== null && depth < 0) throw new Error('Invalid negative trading-depth value.');
    if (!raw.source) throw new Error('Every observation needs a source.');
    return { ...raw, timestampKind, t: timestamp(raw.timestamp_utc), capital, total, gas, pm, bids, settled, mark, depth };
  }));
}

export function parseBenchmarks(text) {
  return ordered(records(text, ['timestamp_utc', 'trading_capital_usd', 'spy_usd', 'source', 'note']).map(raw => {
    const capital = number(raw.trading_capital_usd, 'benchmark capital');
    const spy = number(raw.spy_usd, 'SPY value');
    if (capital <= 0 || spy <= 0 || !raw.source) throw new Error('Invalid benchmark observation.');
    return { ...raw, t: timestamp(raw.timestamp_utc), capital, spy };
  }));
}

export function performanceChange(rows, days = 14) {
  const latest = rows.at(-1);
  if (!latest || latest.depth === null) return null;
  const candidates = rows.filter(r => r.depth !== null && r.t < latest.t);
  const start = candidates.filter(r => r.t <= latest.t - days * DAY).at(-1) ?? candidates[0];
  if (!start || start.depth <= 0) return null;
  return { start, latest, dollars: latest.depth - start.depth, percent: (latest.depth / start.depth - 1) * 100, sameCapital: latest.capital === start.capital };
}

export function pathFor(rows, value, x, y) {
  let connected = false;
  return rows.map(r => {
    const v = value(r);
    if (v === null || !Number.isFinite(v)) { connected = false; return ''; }
    const part = `${connected ? 'L' : 'M'}${x(r.t).toFixed(2)},${y(v).toFixed(2)}`;
    connected = true; return part;
  }).join(' ');
}

const money = n => n === null || n === undefined ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
const pct = n => n === null || n === undefined ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
const date = t => new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }).format(t);
const dateTime = t => new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone: 'UTC' }).format(t) + ' UTC';
const returnOf = (v, capital) => v === null ? null : (v / capital - 1) * 100;

function sourceLink(ref, commit = '') {
  const match = /^((?:notes|research)\/[a-zA-Z0-9_.-]+|README\.md)(?::(\d+))?$/.exec(ref);
  const base = /^[0-9a-f]{40}$/.test(commit) ? SOURCE_ROOT.replace('/main/', '/' + commit + '/') : SOURCE_ROOT;
  return match ? base + match[1] + (match[2] ? '#L' + match[2] : '') : null;
}

const recordTime = r => r.timestampKind === 'day' ? date(r.t) + ' (date only)' : (r.timestampKind === 'check_window' ? '~' : '') + dateTime(r.t);

function node(tag, attrs = {}, text = '') {
  const n = document.createElementNS(NS, tag);
  Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
  if (text) n.textContent = text;
  return n;
}

async function init() {
  const read = async file => {
    const r = await fetch(file, { cache: 'no-cache' });
    if (!r.ok) throw new Error(`Could not load ${file} (HTTP ${r.status}).`);
    return r.text();
  };
  const [data, benchmarkData] = await Promise.all([read('performance.csv'), read('benchmarks.csv')]);
  const rows = parsePerformance(data), benchmarks = parseBenchmarks(benchmarkData);
  const latest = rows.at(-1), change = performanceChange(rows);
  document.querySelector('#updated').textContent = `Recorded ${dateTime(latest.t)}`;
  document.querySelector('#value').textContent = money(latest.depth);
  const roi = returnOf(latest.depth, latest.capital);
  const roiNode = document.querySelector('#return'); roiNode.textContent = pct(roi);
  if (roi !== null) roiNode.className = roi >= 0 ? 'positive' : 'negative';
  document.querySelector('#capital').textContent = `Against ${money(latest.capital)} in trading contributions`;
  if (change) {
    document.querySelector('#change-label').textContent = `Since ${date(change.start.t)}`;
    const el = document.querySelector('#change');
    el.textContent = `${change.dollars >= 0 ? '+' : '−'}${money(Math.abs(change.dollars))}`;
    el.className = change.dollars >= 0 ? 'positive' : 'negative';
    document.querySelector('#change-detail').textContent = `${pct(change.percent)} in value${change.sameCapital ? ' · no change in contributions' : ' · contributions changed'}`;
  }
  document.querySelector('#record-count').textContent = `(${rows.length})`;
  const tbody = document.querySelector('#observations');
  rows.slice().reverse().forEach(r => {
    const tr = document.createElement('tr');
    [recordTime(r).replace(' UTC', ''), money(r.depth), money(r.mark), pct(returnOf(r.depth, r.capital))].forEach(text => { const td = document.createElement('td'); td.textContent = text; tr.append(td); });
    const td = document.createElement('td'), href = sourceLink(r.source, r.source_commit);
    if (href) { const a = document.createElement('a'); a.href = href; a.textContent = 'Record ↗'; a.title = r.note || r.source; td.append(a); }
    else td.textContent = r.source;
    tr.append(td); tbody.append(tr);
  });

  const svg = document.querySelector('#chart'), tooltip = document.querySelector('#tooltip'), wrap = document.querySelector('#chart-wrap');
  const state = { days: 0, unit: 'usd', enabled: { depth: true, mark: true, spy: true }, selected: -1 };
  let W = 960, H = 390;
  const left = 64, right = 20, top = 30, bottom = 46;
  let points = [], x, y, lo, hi, guide, valueAt;

  function hideTooltip() { tooltip.hidden = true; if (guide) guide.setAttribute('visibility', 'hidden'); }
  function select(index) {
    if (!points.length) return;
    state.selected = Math.max(0, Math.min(points.length - 1, index));
    const point = points[state.selected]; tooltip.replaceChildren();
    const title = document.createElement('b'); title.textContent = point.pilot ? recordTime(point.pilot) : dateTime(point.t); tooltip.append(title);
    const lines = [];
    if (point.pilot) {
      const r = point.pilot;
      if (state.enabled.depth) lines.push(['Depth', state.unit === 'usd' ? money(r.depth) : pct(returnOf(r.depth, r.capital))]);
      if (state.enabled.mark) lines.push(['Midpoint', state.unit === 'usd' ? money(r.mark) : pct(returnOf(r.mark, r.capital))]);
    }
    if (point.benchmark && state.enabled.spy) {
      const r = point.benchmark;
      lines.push(['SPY benchmark', state.unit === 'usd' ? money(r.spy) : pct(returnOf(r.spy, r.capital))]);
    }
    lines.forEach(([label, value]) => {
      const span = document.createElement('span'), a = document.createElement('span'), b = document.createElement('span');
      a.textContent = label; b.textContent = value; span.append(a, b); tooltip.append(span);
    });
    tooltip.hidden = false;
    const px = x(point.t) / W * wrap.clientWidth;
    const width = tooltip.offsetWidth;
    tooltip.style.left = `${Math.max(4, Math.min(wrap.clientWidth - width - 4, px - width / 2))}px`;
    tooltip.style.top = '4px';
    guide.setAttribute('x1', x(point.t)); guide.setAttribute('x2', x(point.t)); guide.setAttribute('visibility', 'visible');
    svg.setAttribute('aria-label', `${dateTime(point.t)}. ${lines.map(([k, v]) => k + ' ' + v).join('. ')}. Use arrow keys for another observation.`);
  }

  function render() {
    hideTooltip(); svg.replaceChildren(); state.selected = -1;
    const narrow = wrap.clientWidth < 600;
    W = narrow ? 520 : 960; H = narrow ? 360 : 390;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.style.setProperty('--axis-font-size', narrow ? '17px' : '12px');
    lo = state.days ? Math.max(rows[0].t, latest.t - state.days * DAY) : rows[0].t; hi = latest.t;
    const visible = rows.filter(r => r.t >= lo && r.t <= hi);
    const bench = benchmarks.filter(r => r.t >= lo && r.t <= hi);
    valueAt = (r, key) => state.unit === 'usd' ? r[key] : returnOf(r[key], r.capital);
    const values = visible.map(r => state.unit === 'usd' ? r.capital : 0);
    if (state.enabled.depth) visible.forEach(r => { if (r.depth !== null) values.push(valueAt(r, 'depth')); });
    if (state.enabled.mark) visible.forEach(r => { if (r.mark !== null) values.push(valueAt(r, 'mark')); });
    if (state.enabled.spy) bench.forEach(r => values.push(valueAt(r, 'spy')));
    const min = Math.min(...values), max = Math.max(...values), span = Math.max(max - min, state.unit === 'usd' ? 8 : 4);
    const y0 = min - span * .15, y1 = max + span * .15;
    x = t => left + (t - lo) / Math.max(hi - lo, 1) * (W - left - right);
    y = v => top + (y1 - v) / (y1 - y0) * (H - top - bottom);
    for (let i = 0; i <= 4; i++) {
      const v = y0 + (y1 - y0) * i / 4;
      svg.append(node('line', { x1: left, x2: W - right, y1: y(v), y2: y(v), stroke: '#edf0eb' }));
      svg.append(node('text', { x: left - 10, y: y(v) + 4, 'text-anchor': 'end' }, state.unit === 'usd' ? '$' + Math.round(v) : v.toFixed(1) + '%'));
    }
    for (let i = 0; i <= 4; i++) {
      const t = lo + (hi - lo) * i / 4;
      svg.append(node('text', { x: x(t), y: H - 14, 'text-anchor': i === 0 ? 'start' : i === 4 ? 'end' : 'middle' }, date(t)));
    }
    svg.append(node('path', { d: pathFor(visible, r => state.unit === 'usd' ? r.capital : 0, x, y), fill: 'none', stroke: '#a8b4ab', 'stroke-dasharray': '3 5', 'stroke-width': 1.3 }));
    for (const [key, seriesRows] of [['mark', visible], ['spy', bench], ['depth', visible]]) {
      if (!state.enabled[key] || !seriesRows.length) continue;
      const attrs = { d: pathFor(seriesRows, r => valueAt(r, key), x, y), class: 'series', stroke: COLORS[key], 'stroke-width': key === 'depth' ? 2.8 : 1.8 };
      if (key === 'spy') attrs['stroke-dasharray'] = '6 6';
      svg.append(node('path', attrs));
      seriesRows.forEach(r => {
        const v = valueAt(r, key); if (v === null) return;
        svg.append(node('circle', { cx: x(r.t), cy: y(v), r: key === 'spy' ? 4 : 2.5, fill: key === 'spy' ? 'white' : COLORS[key], stroke: COLORS[key], 'stroke-width': 1.5 }));
      });
    }
    guide = node('line', { x1: 0, x2: 0, y1: top, y2: H - bottom, stroke: '#788d82', 'stroke-dasharray': '3 4', visibility: 'hidden' }); svg.append(guide);
    const merged = new Map();
    visible.forEach(r => merged.set(r.t, { t: r.t, pilot: r }));
    if (state.enabled.spy) bench.forEach(r => merged.set(r.t, { ...merged.get(r.t), t: r.t, benchmark: r }));
    points = [...merged.values()].sort((a, b) => a.t - b.t);
    const complete = visible.filter(r => r.depth !== null).length;
    document.querySelector('#range-detail').textContent = `${date(lo)} – ${date(hi)}, ${new Date(hi).getUTCFullYear()} · ${complete} valued snapshots${complete < visible.length ? ` · ${visible.length - complete} gas gaps` : ''}`;
  }

  document.querySelectorAll('[data-days]').forEach(button => button.addEventListener('click', () => {
    state.days = Number(button.dataset.days);
    document.querySelectorAll('[data-days]').forEach(b => { b.classList.toggle('active', b === button); b.setAttribute('aria-pressed', String(b === button)); }); render();
  }));
  document.querySelectorAll('[data-unit]').forEach(button => button.addEventListener('click', () => {
    state.unit = button.dataset.unit;
    document.querySelectorAll('[data-unit]').forEach(b => { b.classList.toggle('active', b === button); b.setAttribute('aria-pressed', String(b === button)); }); render();
  }));
  document.querySelectorAll('[data-series]').forEach(input => input.addEventListener('change', () => { state.enabled[input.dataset.series] = input.checked; render(); }));
  svg.addEventListener('pointermove', e => {
    const rect = svg.getBoundingClientRect(), px = (e.clientX - rect.left) / rect.width * W;
    if (px < left || px > W - right || !points.length) { hideTooltip(); return; }
    select(points.reduce((best, r, i) => Math.abs(x(r.t) - px) < Math.abs(x(points[best].t) - px) ? i : best, 0));
  });
  svg.addEventListener('pointerleave', hideTooltip);
  window.addEventListener('resize', () => { if ((wrap.clientWidth < 600) !== (W === 520)) render(); });
  svg.addEventListener('keydown', e => {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Escape'].includes(e.key)) e.preventDefault();
    if (e.key === 'Escape') hideTooltip();
    else if (e.key === 'Home') select(0);
    else if (e.key === 'End') select(points.length - 1);
    else if (e.key === 'ArrowLeft') select(state.selected < 0 ? points.length - 1 : state.selected - 1);
    else if (e.key === 'ArrowRight') select(state.selected < 0 ? 0 : state.selected + 1);
  });
  render();
}

if (typeof document !== 'undefined') init().catch(error => {
  const el = document.querySelector('#error'); el.textContent = `The chart could not load: ${error.message}`; el.hidden = false;
  document.querySelector('#updated').textContent = 'Data unavailable';
});
