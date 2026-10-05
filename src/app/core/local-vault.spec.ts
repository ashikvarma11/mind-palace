import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { LocalVault, VAULT_INVOKE } from './local-vault';

describe('Local vault boundary', () => {
  const metadata = {
    schema_version: 1,
    id: '11111111-1111-4111-8111-111111111111',
    kind: 'session',
    title: 'Synthetic',
    source_id: '22222222-2222-4222-8222-222222222222',
    review_status: 'unreviewed',
    created_at: '2026-10-02T12:00:00Z',
  };
  let call: ReturnType<typeof vi.fn>;
  let vault: LocalVault;
  beforeEach(async () => {
    Object.defineProperty(globalThis, '__TAURI_INTERNALS__', { configurable: true, value: {} });
    call = vi.fn().mockResolvedValue({ connected: false, ai_enabled: false });
    TestBed.configureTestingModule({ providers: [{ provide: VAULT_INVOKE, useValue: call }] });
    vault = TestBed.inject(LocalVault);
    await vi.waitFor(() => expect(vault.busy()).toBe(false));
    call.mockClear();
  });
  afterEach(() => {
    Reflect.deleteProperty(globalThis, '__TAURI_INTERNALS__');
  });
  it('rejects malformed native responses and hides arbitrary error details', async () => {
    call.mockResolvedValue({ connected: true, ai_enabled: true, secret: 'private' });
    await vault.refreshStatus();
    expect(vault.connected()).toBe(false);
    expect(vault.error()).toContain('invalid data');
    call.mockRejectedValue({ code: 'CONFLICT', message: 'private content' });
    await vault.open(false);
    expect(vault.error()).not.toContain('private content');
  });
  it('explicit retry reuses the same operation ID and unchanged draft', async () => {
    vault.draft = { title: 'Synthetic', body: 'Notes', source_text: 'Original\r\nதமிழ்' };
    call.mockRejectedValue({ code: 'WORKER_DISCONNECTED' });
    await vault.save();
    const first = call.mock.calls[0][1].input;
    expect(vault.draftLocked()).toBe(true);
    expect(call).toHaveBeenCalledTimes(1);
    vault.draft.title = 'Changed after failure';
    call.mockImplementation(async (command: string) => {
      if (command === 'sessions_create') return { id: metadata.id };
      if (command === 'sessions_list') return { items: [metadata], total: 1, next_offset: null };
      return { metadata, body: 'Notes', source_text: first.source_text };
    });
    await vault.save();
    expect(call.mock.calls[1][1].input).toEqual(first);
    expect(vault.draftLocked()).toBe(false);
    expect(vault.error()).toBe('');
    expect(vault.selected()?.source_text).toBe('Original\r\nதமிழ்');
  });
  it('rejects empty drafts without invoking native saving', async () => {
    await vault.save();
    expect(call).not.toHaveBeenCalled();
    expect(vault.error()).toContain('Enter a title');
  });
  it('does not queue a second operation while one is pending', async () => {
    let finish!: (value: unknown) => void;
    call.mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const first = vault.refreshStatus();
    await vault.open(true);
    expect(call).toHaveBeenCalledTimes(1);
    finish({ connected: false, ai_enabled: false });
    await first;
  });
  it('asks the open vault and keeps exact local evidence', async () => {
    const answer = {
      schema_version: 1,
      status: 'answered',
      answer: 'The closest stored evidence is from Synthetic:\n\nSQLite was selected.',
      sources: [
        {
          session_id: metadata.id,
          title: 'Synthetic',
          quote: 'SQLite was selected.',
          start: 10,
          end: 30,
          snapshot_sha256: 'a'.repeat(64),
          provider: 'codex',
        },
      ],
    };
    call.mockResolvedValue(answer);
    await vault.ask('Which database was selected?');
    expect(call).toHaveBeenCalledExactlyOnceWith('sessions_ask', {
      question: 'Which database was selected?',
    });
    expect(vault.answer()).toEqual(answer);
  });
  it('does not send an empty question to native code', async () => {
    await vault.ask('   ');
    expect(call).not.toHaveBeenCalled();
    expect(vault.error()).toContain('Enter a question');
  });
  it('answers from stored sessions after a capture timeout and reports the missing sync', async () => {
    vault.connected.set(true);
    const answer = { schema_version: 1, status: 'insufficient_evidence', answer: 'No matching evidence.', sources: [] };
    call.mockImplementation(async (command: string) => {
      if (command === 'capture_status') throw { code: 'CAPTURE_TIMEOUT', message: 'private details' };
      return answer;
    });
    await vault.ask('Which database?');
    expect(call.mock.calls.map((args) => args[0])).toEqual(['capture_status', 'sessions_ask']);
    expect(vault.connected()).toBe(true);
    expect(vault.answer()).toEqual(answer);
    expect(vault.notice()).toContain('sessions already in the vault');
    expect(vault.notice()).not.toContain('private details');
  });
  it('does not query an unusable vault after a worker disconnect during sync', async () => {
    vault.connected.set(true);
    call.mockRejectedValue({ code: 'WORKER_DISCONNECTED' });
    await vault.ask('Which database?');
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_status', {});
    expect(vault.connected()).toBe(false);
    expect(vault.answer()).toBeNull();
  });
  it('checks new Codex captures before answering from an open vault', async () => {
    vault.connected.set(true);
    const client = (provider: string) => ({ provider, configured: provider === 'codex', enabled: true,
      memory_enabled: false, source_root: 'C:/synthetic/source', memory_roots: [], revision: 'a'.repeat(64), snippet: '' });
    call.mockImplementation(async (command: string) => {
      if (command === 'capture_status') return { schema_version: 1, inbox_root: 'C:/synthetic/inbox',
        health: { schema_version: 1, kind: 'capture_health', derived: true, bytes_used: 0, quota_bytes: 1073741824,
          failures: 0, pending_spool: 0, retention_days: 30, last_indexed_at: null },
        clients: [client('claude-code'), client('codex')] };
      if (command === 'capture_index') return { status: 'indexed', sessions: 1, memories: 0, revisions: 1 };
      if (command === 'capture_import') return { schema_version: 1, created: 1, updated: 0, unchanged: 0,
        acknowledged: 1, skipped: 0, memories_pending: 0, next_offset: null };
      if (command === 'capture_cleanup') return { removed_revisions: 0, removed_chunks: 0, bytes_freed: 0, deferred: false };
      if (command === 'sessions_list') return { items: [metadata], total: 1, next_offset: null };
      return { schema_version: 1, status: 'insufficient_evidence', answer: 'No matching evidence.', sources: [] };
    });
    await vault.ask('Which database?');
    expect(call.mock.calls.map((args) => args[0])).toEqual([
      'capture_status', 'capture_index', 'capture_import', 'capture_cleanup', 'sessions_list', 'sessions_ask',
    ]);
    expect(vault.error()).toBe('');
    expect(vault.list().total).toBe(1);
  });
});
