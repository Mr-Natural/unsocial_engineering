const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/app/api/pipeline/status/route.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function loadRoute(token) {
  let databaseCalls = 0;
  const context = {
    exports: {}, process: { env: { PIPELINE_STATUS_TOKEN: token } },
    require(name) {
      if (name === 'next/server') return { NextResponse: { json: (data, init) => Response.json(data, init) } };
      if (name === '@/lib/supabase/admin') return { createAdminClient() {
        databaseCalls++;
        const query = {
          select() { return this; }, gte() { return this; }, eq() { return this; },
          order() { return this; }, limit() { return this; },
          then(resolve) { return Promise.resolve({ data: [], count: 0 }).then(resolve); },
        };
        return { from() { return query; } };
      } };
      throw new Error(`Unexpected import: ${name}`);
    },
  };
  vm.runInNewContext(compiled, context);
  return { get: context.exports.GET, calls: () => databaseCalls };
}

for (const [label, token, authorization] of [
  ['missing configured token', undefined, undefined],
  ['empty configured token', '', 'Bearer '],
  ['missing request credential', 'synthetic-test-token', undefined],
  ['incorrect request credential', 'synthetic-test-token', 'Bearer wrong'],
]) {
  test(`rejects ${label} before database access`, async () => {
    const route = loadRoute(token);
    const response = await route.get(new Request('https://example.org/api/pipeline/status', {
      headers: authorization ? { authorization } : {},
    }));
    assert.equal(response.status, 401);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.deepEqual(await response.json(), { error: 'unauthorized' });
    assert.equal(route.calls(), 0);
  });
}

test('allows the configured credential and forbids response caching', async () => {
  const route = loadRoute('synthetic-test-token');
  const response = await route.get(new Request('https://example.org/api/pipeline/status', {
    headers: { authorization: 'Bearer synthetic-test-token' },
  }));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(route.calls(), 1);
  assert.deepEqual((await response.json()).flagged, []);
});
