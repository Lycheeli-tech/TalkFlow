import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const compiled = ts.transpileModule(readFileSync(join(dirname(fileURLToPath(import.meta.url)), '../lib/auth-session.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const jwt = (owner, version) => `e30.${Buffer.from(JSON.stringify({ sub: owner, version })).toString('base64url')}.signature`;
const storage = () => {
  const values = new Map();
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
};
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
class AuthRequestError extends Error { constructor(status) { super('Auth rejected'); this.status = status; } }

function harness({ local = storage(), refresh, fetch } = {}) {
  let now = Date.now();
  const exports = {};
  const events = new Map();
  const intervals = new Set();
  const window = {
    dispatchEvent() {}, addEventListener: (name, callback) => events.set(name, callback),
    removeEventListener: name => events.delete(name), setInterval: callback => { intervals.add(callback); return callback; },
    clearInterval: callback => intervals.delete(callback),
  };
  const document = { visibilityState: 'visible', addEventListener: window.addEventListener, removeEventListener: window.removeEventListener };
  const session = storage();
  vm.runInNewContext(compiled, {
    exports, require: () => ({ AuthRequestError, refreshAuthSession: refresh ?? (async () => { throw new Error('unexpected refresh'); }) }),
    localStorage: local, sessionStorage: session, window, document, Event, Headers, Response, atob,
    fetch: fetch ?? (() => { throw new Error('unexpected API call'); }),
    Date: class extends Date { static now() { return now; } },
  });
  const save = (owner = 'owner-a', version = 1, expires = 3600) => exports.storeAuthSession({
    access_token: jwt(owner, version), refresh_token: `${owner}-refresh-${version}`, expires_at: now / 1000 + expires,
  });
  return { api: exports, save, local, session, advance: ms => { now += ms; }, events, intervals };
}

test('same account restores after browser-session storage is gone, including after three days away', async () => {
  const first = harness(); first.save();
  const next = harness({ local: first.local, refresh: async () => ({ access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }) });
  next.advance(3 * 24 * 3600000);
  assert.equal(await next.api.getValidAccessToken(), jwt('owner-a', 2));
  assert.equal(next.session.getItem(next.api.ACCESS_TOKEN_STORAGE_KEY), jwt('owner-a', 2));
});

test('valid token does not call Auth; concurrent expired requests refresh only once', async () => {
  let calls = 0; const gate = deferred();
  const h = harness({ refresh: async () => { calls++; await gate.promise; return { access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }; } });
  h.save(); assert.equal(await h.api.getValidAccessToken(), jwt('owner-a', 1)); assert.equal(calls, 0);
  h.advance(3600000);
  const requests = Array.from({ length: 10 }, () => h.api.getValidAccessToken());
  assert.equal(calls, 1); gate.resolve();
  assert.ok((await Promise.all(requests)).every(token => token === jwt('owner-a', 2)));
});

test('temporary Auth network outage preserves session and later retry succeeds', async () => {
  let failing = true;
  const h = harness({ refresh: async () => { if (failing) throw new Error('network'); return { access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }; } });
  h.save('owner-a', 1, 0);
  await assert.rejects(h.api.getValidAccessToken(), /network/);
  assert.equal(h.api.getStoredAccessToken(), jwt('owner-a', 1));
  failing = false; assert.equal(await h.api.getValidAccessToken(), jwt('owner-a', 2));
});

test('confirmed invalid refresh session clears both stores', async () => {
  const h = harness({ refresh: async () => { throw new AuthRequestError(400); } });
  h.save('owner-a', 1, 0);
  await assert.rejects(h.api.getValidAccessToken());
  assert.equal(h.api.getStoredAccessToken(), '');
  assert.equal(h.local.getItem(h.api.AUTH_SESSION_STORAGE_KEY), null);
});

for (const action of ['logout', 'different account', 'another tab refresh']) {
  test(`late refresh cannot undo ${action}`, async () => {
    const gate = deferred();
    const h = harness({ refresh: async () => { await gate.promise; return { access_token: jwt('owner-a', 2), refresh_token: 'old-response', expires_in: 3600 }; } });
    h.save('owner-a', 1, 0); const pending = h.api.getValidAccessToken();
    if (action === 'logout') h.api.clearAccessToken();
    else h.save(action === 'different account' ? 'owner-b' : 'owner-a', 3);
    gate.resolve(); await pending;
    assert.equal(h.api.getStoredAccessToken(), action === 'logout' ? '' : jwt(action === 'different account' ? 'owner-b' : 'owner-a', 3));
  });
}

test('401 renews same owner once and preserves request body', async () => {
  const calls = [];
  const h = harness({ refresh: async () => ({ access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }),
    fetch: async (url, init) => { calls.push(init); return new Response('{}', { status: calls.length === 1 ? 401 : 200 }); } });
  h.save();
  const body = new FormData(); body.append('recording', new Blob(['synthetic']), 'audio.webm');
  assert.equal((await h.api.sessionFetch('/test', { method: 'POST', body })).status, 200);
  assert.equal(calls.length, 2); assert.equal(calls[0].body, body); assert.equal(calls[1].body, body);
  assert.equal(calls[1].headers.get('Authorization'), 'Bearer ' + jwt('owner-a', 2));
});

test('a second 401 terminates retry and signs out', async () => {
  let calls = 0;
  const h = harness({ refresh: async () => ({ access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }),
    fetch: async () => { calls++; return new Response('{}', { status: 401 }); } });
  h.save(); assert.equal((await h.api.sessionFetch('/test')).status, 401);
  assert.equal(calls, 2); assert.equal(h.api.getStoredAccessToken(), '');
});

test('old-account request is not replayed under a new login', async () => {
  let calls = 0; let h;
  h = harness({ fetch: async () => { calls++; h.save('owner-b', 3); return new Response('{}', { status: 401 }); } });
  h.save(); assert.equal((await h.api.sessionFetch('/test', { method: 'POST', body: '{}' })).status, 401);
  assert.equal(calls, 1); assert.equal(h.api.getStoredAccessToken(), jwt('owner-b', 3));
});

test('legacy token replacement cannot leave a persistent different-account session active', () => {
  const h = harness(); h.save(); h.api.storeAccessToken(jwt('owner-b', 1));
  assert.equal(h.api.getStoredAccessToken(), jwt('owner-b', 1));
  assert.equal(h.local.getItem(h.api.AUTH_SESSION_STORAGE_KEY), null);
});

test('an API request waiting for refresh cannot start under a different newly logged-in owner', async () => {
  const gate = deferred(); let calls = 0;
  const h = harness({ refresh: async () => { await gate.promise; return { access_token: jwt('owner-a', 2), refresh_token: 'old-response', expires_in: 3600 }; },
    fetch: async () => { calls++; return new Response('{}'); } });
  h.save('owner-a', 1, 0);
  const request = h.api.sessionFetch('/test', { method: 'POST', body: '{}' });
  h.save('owner-b', 3); gate.resolve();
  await assert.rejects(request, /Account changed/); assert.equal(calls, 0);
  assert.equal(h.api.getStoredAccessToken(), jwt('owner-b', 3));
});

test('focus/visibility maintenance uses the refresh path and cleans listeners on unmount', async () => {
  let calls = 0;
  const h = harness({ refresh: async () => { calls++; return { access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_in: 3600 }; } });
  h.save(); const stop = h.api.maintainAuthSession(); h.advance(3600000);
  h.events.get('visibilitychange')(); await h.api.getValidAccessToken();
  assert.equal(calls, 1); stop(); assert.equal(h.intervals.size, 0); assert.equal(h.events.size, 0);
});

test('another tab logout clears the legacy fallback and another tab renewal synchronizes it', () => {
  const h = harness(); h.save(); const stop = h.api.maintainAuthSession();
  h.local.removeItem(h.api.AUTH_SESSION_STORAGE_KEY);
  h.events.get('storage')({ key: h.api.AUTH_SESSION_STORAGE_KEY });
  assert.equal(h.api.getStoredAccessToken(), '');
  h.local.setItem(h.api.AUTH_SESSION_STORAGE_KEY, JSON.stringify({ access_token: jwt('owner-a', 2), refresh_token: 'rotated', expires_at: Date.now() / 1000 + 3600 }));
  h.events.get('storage')({ key: h.api.AUTH_SESSION_STORAGE_KEY });
  assert.equal(h.session.getItem(h.api.ACCESS_TOKEN_STORAGE_KEY), jwt('owner-a', 2)); stop();
});
