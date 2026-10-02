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
});
