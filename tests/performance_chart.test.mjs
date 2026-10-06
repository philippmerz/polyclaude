import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseCSV, parsePerformance, parseBenchmarks, parseContributions, capitalAt, performanceChange, pathFor, chartValue } from '../docs/app.mjs';

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

test('an account total with missing gas is visible only in dollars, never as a trading return', () => {
  const [row] = parsePerformance(HEADER + '\n2026-07-01T02:00:00Z,170,180,,,,,notes/journal.md:1,account total only');
  assert.equal(chartValue(row, 'total', 'usd'), 180);
  assert.equal(chartValue(row, 'total', 'return'), null);
  assert.equal(chartValue(row, 'mark', 'usd'), null);
  assert.equal(chartValue(row, 'depth', 'return'), null);
  const complete = { ...row, depth: 175 };
  assert.ok(Math.abs(chartValue(complete, 'depth', 'return') - 2.941176470588225) < 1e-9);
});

test('a complete recorded trading subtotal does not invent a gas-inclusive account total', () => {
  const text = HEADER + ',reported_trading_mark_usd\n2026-04-25T16:46:00Z,70,,,64.94,,,notes/journal_archive_2026-04.md:138,positions plus 5.05 cash,69.99';
  const [row] = parsePerformance(text);
  assert.equal(row.total, null); assert.equal(row.gas, null); assert.equal(row.depth, null);
  assert.equal(row.mark, 69.99); assert.equal(row.reconstructed, true);
  assert.equal(chartValue(row, 'total'), null);
  assert.throws(() => parsePerformance(text.replace(',69.99', ',')), /account total/);
});

test('gas derived from a rounded snapshot identity carries its provenance and uncertainty', () => {
  const text = HEADER + ',gas_kind,gas_rounding_bound_usd\n2026-09-04T02:19:23Z,170,186.94,6.17,153.54,146.89,14.43,notes/pnl_weekly.md:998,rounded snapshot identity,rounded_identity,0.015';
  const [row] = parsePerformance(text);
  assert.equal(row.reconstructed, true); assert.equal(row.roundingBound, .015);
  assert.ok(Math.abs(row.depth - 174.12) < 1e-9);
  assert.throws(() => parsePerformance(text.replace(',0.015', ',')), /rounding bound/);
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

test('inception deposits are dated flows rather than invented account valuations', async () => {
  const flows = parseContributions(await readFile(new URL('../docs/contributions.csv', import.meta.url), 'utf8'));
  assert.equal(capitalAt(flows, Date.parse('2026-04-24T23:59:59Z')), 0);
  assert.equal(capitalAt(flows, Date.parse('2026-04-28T12:00:00Z')), 70);
  assert.equal(capitalAt(flows, Date.parse('2026-04-29T12:00:00Z')), 70);
  assert.equal(capitalAt(flows, Date.parse('2026-04-29T20:00:00Z')), 170);
  assert.equal(flows[0].timestampKind, 'day');
  assert.equal(flows[1].timestampKind, 'check_window');
  assert.ok(flows.every(r => r.source));
  assert.equal(pathFor(flows, r => r.capital, t => t / 86400000, v => v, true).includes('H'), true);
  const text = await readFile(new URL('../docs/contributions.csv', import.meta.url), 'utf8');
  assert.throws(() => parseContributions(text.replace(',170,100,', ',171,100,')), /cumulative/);
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
  const flows = parseContributions(await readFile(new URL('../docs/contributions.csv', import.meta.url), 'utf8'));
  assert.ok(rows.length >= 15);
  assert.ok(rows.every(r => r.source && r.note && r.capital > 0));
  assert.ok([...rows, ...bench].every(r => r.capital === capitalAt(flows, r.t)));
  const oct4 = rows.find(r => r.timestamp_utc === '2026-10-04T18:07:00Z');
  assert.ok(Math.abs(oct4.depth - 177.80) < 1e-9);
  const oct1 = bench.find(r => r.timestamp_utc === '2026-10-01T20:00:00Z');
  assert.equal(oct1.spy, 182);
});
