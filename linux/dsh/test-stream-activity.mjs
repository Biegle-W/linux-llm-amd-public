import assert from 'node:assert/strict';
import http from 'node:http';
import { activityFetch } from './stream-activity-fetch.mjs';
import { idleWatchdog } from '@deepseek-ai/dsh-timeout';

const results = [];
const server = http.createServer((req, res) => {
  if (req.url === '/error') {
    res.writeHead(429, { 'Content-Type': 'application/json', 'Retry-After': '7' });
    res.end('{"error":{"message":"synthetic limit"}}');
    return;
  }
  if (req.url === '/empty') { res.writeHead(204); res.end(); return; }
  res.writeHead(200, { 'Content-Type': 'text/event-stream' });
  res.flushHeaders();
  if (req.url === '/idle') return;
  const interval = setInterval(() => res.write(': loading\n\n'), 35);
  const final = setTimeout(() => res.end('data: complete\n\n'), 450);
  res.on('close', () => { clearInterval(interval); clearTimeout(final); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;
async function readWithWatchdog(path, signal) {
  using watchdog = idleWatchdog(signal, 160, 'SYNTHETIC_IDLE');
  const response = await activityFetch(() => watchdog.pulse())(base + path, { signal: watchdog.signal });
  const reader = response.body.getReader();
  const iterator = { next: () => reader.read() };
  let value = '';
  try {
    while (true) {
      const item = await watchdog.next(iterator);
      if (item.done) return value;
      value += new TextDecoder().decode(item.value);
    }
  } finally { await reader.cancel().catch(() => {}); }
}
try {
  const active = readWithWatchdog('/active');
  const idle = readWithWatchdog('/idle');
  await assert.rejects(idle, /SYNTHETIC_IDLE|aborted/);
  assert.match(await active, /data: complete/);
  results.push('keepalive activity survives; concurrent silent stream still times out');
  const controller = new AbortController();
  const cancelled = readWithWatchdog('/active', controller.signal);
  setTimeout(() => controller.abort(new Error('explicit caller stop')), 70);
  await assert.rejects(cancelled, /explicit caller stop/);
  results.push('caller cancellation propagates through the observed body');
  const error = await activityFetch(() => {})(base + '/error');
  assert.equal(error.status, 429);
  assert.equal(error.headers.get('Retry-After'), '7');
  assert.equal(error.url, base + '/error');
  assert.equal(error.redirected, false);
  assert.deepEqual(await error.json(), { error: { message: 'synthetic limit' } });
  results.push('HTTP error status, URL, headers and JSON body are preserved');
  const empty = await activityFetch(() => {})(base + '/empty');
  assert.equal(empty.status, 204);
  assert.equal(empty.body, null);
  results.push('null-body responses pass through');
  console.log(JSON.stringify({ passed: results.length, checks: results }));
} finally {
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
