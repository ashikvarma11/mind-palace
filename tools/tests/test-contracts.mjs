import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { validateSessionMetadata, validateSessionRead, validateSessionList, validateSessionCreated } from '../../src/app/core/validators.generated.ts';

const metadata = {
  schema_version: 1, id: '11111111-1111-4111-8111-111111111111', kind: 'session',
  title: 'Synthetic', source_id: '22222222-2222-4222-8222-222222222222',
  review_status: 'unreviewed', created_at: '2026-10-02T12:00:00.123456Z',
};
test('valid generated session contracts accept original Unicode text', () => {
  assert.equal(validateSessionMetadata(metadata), true);
  assert.equal(validateSessionRead({ metadata, body: 'Summary', source_text: 'Original\r\nதமிழ்' }), true);
  assert.equal(validateSessionList({ items: [metadata], total: 1, next_offset: null }), true);
  assert.equal(validateSessionCreated({ id: metadata.id }), true);
});
test('unexpected fields, false approvals and invalid identity fail', () => {
  for (const value of [null, [], {}, { ...metadata, id: '../../secret' },
    { ...metadata, review_status: 'confirmed' }, { ...metadata, secret: 'not allowed' }]) {
    assert.equal(validateSessionMetadata(value), false);
  }
  assert.equal(validateSessionCreated({ id: metadata.id, path: 'not allowed' }), false);
});
test('real calendar UTC timestamps are required', () => {
  for (const value of ['2026-02-30T12:00:00Z', '2026-10-02T99:00:00Z',
    '2026-10-02T12:00:00+05:30', '0000-10-02T12:00:00Z', '2026-12-31T23:59:60Z', 'not-a-date']) {
    assert.equal(validateSessionMetadata({ ...metadata, created_at: value }), false);
  }
});
test('response sizes and integer pagination are bounded', () => {
  assert.equal(validateSessionRead({ metadata, body: 'x'.repeat(32769), source_text: '' }), false);
  assert.equal(validateSessionRead({ metadata, body: '', source_text: 'x'.repeat(65537) }), false);
  assert.equal(validateSessionList({ items: Array(51).fill(metadata), total: 51, next_offset: null }), false);
  for (const total of [true, -1, 1001, 1.5]) {
    assert.equal(validateSessionList({ items: [], total, next_offset: null }), false);
  }
});
test('standalone browser validators have static imports and no code evaluation', async () => {
  const source = await readFile(new URL('../../src/app/core/validators.generated.ts', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /\beval\s*\(|\bnew Function\b|\brequire\s*\(/);
  assert.match(source, /import runtime0 from/);
});
