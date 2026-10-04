import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseCSV, parsePerformance, parseBenchmarks, performanceChange, pathFor } from '../docs/app.mjs';

const HEADER = 'timestamp_utc,trading_capital_usd,total_mark_usd,gas_usd,pm_mark_usd,pm_depth_usd,settled_pnl_usd,source,note';

test('whole-account comparison includes reserves, removes gas and charges the exit spread', () => {
  const [row] = parsePerformance(HEADER + '\n2026-10-04T18:07:00Z,170,187.73,6.83,36.03,32.93,22.52,notes/journal.md:23522,latest\n');
  assert.ok(Math.abs(row.mark - 180.90) < 1e-9);
  assert.ok(Math.abs(row.depth - 177.80) < 1e-9);
  assert.ok(Math.abs((row.depth / row.capital - 1) * 100 - 4.58823529411765) < 1e-9);
  assert.notEqual(row.depth, row.settled + row.capital);
});

test('missing gas or bid-depth cannot become zero or an invented exit valuation', () => {
  const rows = parsePerformance(HEADER + '\n2026-09-24T02:00:00Z,170,162.59,,124.24,114.65,-2.11,notes/journal.md:19524,gas missing\n2026-09-25T02:00:00Z,170,163.40,6.94,124.54,,-2.11,notes/journal.md:19766,depth missing');
  assert.equal(rows[0].mark, null); assert.equal(rows[0].depth, null);
  assert.ok(Math.abs(rows[1].mark - 156.46) < 1e-9); assert.equal(rows[1].depth, null);
  assert.equal(pathFor([{ t: 1, v: 1 }, { t: 2, v: null }, { t: 3, v: 2 }], r => r.v, t => t, v => v), 'M1.00,1.00  M3.00,2.00');
});

test('invalid dates, duplicate times and malformed monetary values fail visibly', () => {
  const line = '2026-10-04T18:07:00Z,170,187.73,6.83,36.03,32.93,22.52,notes/journal.md:23522,latest';
  assert.throws(() => parsePerformance(HEADER + '\n' + line + '\n' + line), /unique/);
  assert.throws(() => parsePerformance(HEADER + '\n' + line.replace('2026-10-04', '2026-02-30')), /timestamp/);
  assert.throws(() => parsePerformance(HEADER + '\n' + line.replace(',170,', ',0,')), /capital/);
  assert.throws(() => parsePerformance(HEADER + '\n' + line.replace(',6.83,', ',NaN,')), /funded gas/);
  assert.throws(() => parsePerformance(HEADER + '\n' + line.replace(',6.83,', ',999,')), /gas exceeds/);
});

test('CSV supports quoted notes, commas, newlines and doubled quotes', () => {
  assert.deepEqual(parseCSV('a,b\r\n1,"Two, \"\"quoted\"\"\nlines"\r\n'), [['a', 'b'], ['1', 'Two, "quoted"\nlines']]);
  assert.throws(() => parseCSV('a,b\n1,"incomplete'), /Unclosed/);
});

test('recent change uses observed value rather than contributions or settled P&L', () => {
  const rows = [{ t: Date.parse('2026-09-25T02:00:00Z'), depth: 146.04, capital: 170 }, { t: Date.parse('2026-10-04T18:07:00Z'), depth: 177.80, capital: 170 }];
  const change = performanceChange(rows, 7);
  assert.ok(Math.abs(change.dollars - 31.76) < 1e-9);
  assert.ok(Math.abs(change.percent - 21.74746644754862) < 1e-9);
  assert.equal(change.sameCapital, true);
});

test('published CSVs are valid, sourced, increasing and reproduce the latest snapshot', async () => {
  const rows = parsePerformance(await readFile(new URL('../docs/performance.csv', import.meta.url), 'utf8'));
  const bench = parseBenchmarks(await readFile(new URL('../docs/benchmarks.csv', import.meta.url), 'utf8'));
  assert.ok(rows.length >= 15);
  assert.ok(rows.every(r => r.source && r.note && r.capital > 0));
  const oct4 = rows.find(r => r.timestamp_utc === '2026-10-04T18:07:00Z');
  assert.ok(Math.abs(oct4.depth - 177.80) < 1e-9);
  const oct1 = bench.find(r => r.timestamp_utc === '2026-10-01T20:00:00Z');
  assert.equal(oct1.spy, 182);
});
