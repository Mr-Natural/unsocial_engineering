import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

function load(file, imports) {
  const source = fs.readFileSync(new URL('../src/' + file, import.meta.url), 'utf8');
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  }}).outputText;
  const context = { exports: {}, Date, Map, URLSearchParams, require(name) {
    if (Object.hasOwn(imports, name)) return imports[name];
    throw new Error('Unexpected module: ' + name);
  }};
  vm.runInNewContext(js, context);
  return context.exports;
}

function reader(rows, failure = null) {
  return load('lib/queries.ts', { '@/lib/supabase/public': { supabasePublic: {
    from(table) {
      assert.equal(table, 'articles');
      let result = [...rows];
      return {
        select() { return this; },
        eq(key, value) { result = result.filter(row => row[key] === value); return this; },
        like(key, pattern) {
          assert.match(pattern, /^20\d{2}-%$/);
          result = result.filter(row => row[key].startsWith(pattern.slice(0, -1))); return this;
        },
        order(key, { ascending }) { result.sort((a, b) => ascending ? a[key].localeCompare(b[key]) : b[key].localeCompare(a[key])); return this; },
        range(from, to) { return Promise.resolve({ data: result.slice(from, to + 1), count: result.length, error: failure }); },
      };
    },
  }}});
}

const fixtures = [
  { id: 'visible', slug: '2026-synthetic-reviewed', status: 'published', published_at: '2026-11-08' },
  { id: 'private', slug: '2026-synthetic-private', status: 'draft', published_at: '2026-11-09' },
  { id: 'withdrawn', slug: '2026-synthetic-withdrawn', status: 'flagged', published_at: '2026-11-10' },
  { id: 'other-year', slug: '2025-synthetic-reviewed', status: 'published', published_at: '2026-11-07' },
  { id: 'general', slug: 'synthetic-general', status: 'published', published_at: '2026-11-08' },
];

test('Casebook only includes published members of the selected year', async () => {
  const result = await reader(fixtures).browseArticles({ casebookYear: 2026 });
  assert.equal(result.total, 1);
  assert.deepEqual(Array.from(result.articles, row => row.id), ['visible']);
});

test('a withdrawn article disappears from a fresh Casebook read', async () => {
  const rows = fixtures.map(row => row.id === 'visible' ? { ...row, status: 'draft' } : row);
  const result = await reader(rows).browseArticles({ casebookYear: 2026 });
  assert.equal(result.total, 0);
});

test('an unavailable database does not masquerade as an empty collection', async () => {
  await assert.rejects(reader(fixtures, { message: 'synthetic failure' }).browseArticles({ casebookYear: 2026 }), /temporarily unavailable/);
});

test('pagination preserves the collection route', () => {
  const { Pagination } = load('components/pagination.tsx', {
    'react/jsx-runtime': ReactJsx,
    'next/link': { default: ({ children, ...props }) => React.createElement('a', props, children) },
  });
  const markup = renderToStaticMarkup(React.createElement(Pagination, { page: 2, total: 30, pageSize: 9, params: {}, basePath: '/casebook/2026' }));
  assert.ok(markup.includes('href="/casebook/2026?page=1"'));
  assert.ok(markup.includes('href="/casebook/2026?page=3"'));
  assert.ok(!markup.includes('/scams?'));
});

import * as ReactJsx from 'react/jsx-runtime';
