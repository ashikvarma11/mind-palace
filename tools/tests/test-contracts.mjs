import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { validateSessionMetadata, validateSessionRead, validateSessionList, validateSessionCreated, validateVaultStatus,
  validateAiPreviewRequest, validateAiPreviewResult, validateAiPrompt } from '../../src/app/core/validators.generated.ts';

const metadata = {
  schema_version: 1, id: '11111111-1111-4111-8111-111111111111', kind: 'session',
  title: 'Synthetic', source_id: '22222222-2222-4222-8222-222222222222',
  review_status: 'unreviewed', created_at: '2026-10-02T12:00:00.123456Z',
};
test('vault status never claims AI or accepts unexpected fields', () => {
  assert.equal(validateVaultStatus({ connected: true, ai_enabled: false }), true);
  for (const value of [{ connected: true, ai_enabled: true }, { connected: 1, ai_enabled: false }, { connected: false, ai_enabled: false, path: 'secret' }]) {
    assert.equal(validateVaultStatus(value), false);
  }
});
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
  assert.match(source, /import \* as runtime0 from/);
});
test('preview contracts forbid sending, keys, custom endpoints and provider-shape mixing', () => {
  const input = { provider: 'openai', model: 'synthetic-model', question: 'Why?', max_output_tokens: 512,
    selections: [{ kind: 'session', id: metadata.id, start: 0, end: 1 }] };
  assert.equal(validateAiPreviewRequest(input), true);
  assert.equal(validateAiPreviewRequest({ ...input, api_key: 'fake' }), false);
  assert.equal(validateAiPrompt({ question: 'Why?', sources: [{ source_id: 'S1', text: '😀' }] }), true);
  const value = { preview_id: metadata.id, payload_sha256: 'a'.repeat(64), expires_in_seconds: 300,
    can_send: false, sharing_warning: 'Charges apply.', local_references: [{ ...input.selections[0], source_id: 'S1', snapshot_sha256: 'b'.repeat(64) }],
    request: { provider: 'openai', endpoint: 'https://api.openai.com/v1/responses', headers: { 'Content-Type': 'application/json' },
      body: { model: 'synthetic-model', instructions: 'Synthetic instructions', input: [{ role: 'user', content: '{}' }], max_output_tokens: 512, store: false, stream: false } } };
  assert.equal(validateAiPreviewResult(value), true);
  for (const bad of [ { ...value, can_send: true }, { ...value, api_key: 'fake' },
    { ...value, request: { ...value.request, endpoint: 'https://other.example' } },
    { ...value, request: { ...value.request, provider: 'anthropic' } },
    { ...value, request: { ...value.request, headers: { ...value.request.headers, Authorization: 'fake' } } } ]) {
    assert.equal(validateAiPreviewResult(bad), false);
  }
});
