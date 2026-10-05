import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { VAULT_INVOKE } from './local-vault';
import { CaptureConnection } from './capture-connection';

describe('Capture connection boundary', () => {
  const client = {
    provider: 'codex',
    configured: false,
    enabled: false,
    memory_enabled: false,
    source_root: '',
    memory_roots: [],
    revision: 'a'.repeat(64),
    snippet: '',
  };
  const status = {
    schema_version: 1,
    inbox_root: 'C:/synthetic/inbox',
    health: {
      schema_version: 1,
      kind: 'capture_health',
      derived: true,
      bytes_used: 0,
      quota_bytes: 1073741824,
      failures: 0,
      pending_spool: 0,
      retention_days: 30,
      last_indexed_at: null,
    },
    clients: [{ ...client, provider: 'claude-code' }, client],
  };
  let call: ReturnType<typeof vi.fn>;
  let service: CaptureConnection;
  beforeEach(() => {
    Object.defineProperty(globalThis, '__TAURI_INTERNALS__', { configurable: true, value: {} });
    call = vi.fn().mockResolvedValue(status);
    TestBed.configureTestingModule({ providers: [{ provide: VAULT_INVOKE, useValue: call }] });
    service = TestBed.inject(CaptureConnection);
  });
  afterEach(() => Reflect.deleteProperty(globalThis, '__TAURI_INTERNALS__'));
  it('does not enable or configure on status reads', async () => {
    await service.refresh();
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_status');
    expect(service.status()?.clients.every((item) => !item.enabled)).toBe(true);
  });
  it('rejects malformed, duplicate providers and unconsented memory states', async () => {
    for (const clients of [
      [client, client],
      [
        { ...client, provider: 'claude-code' },
        { ...client, memory_enabled: true },
      ],
    ]) {
      call.mockResolvedValue({ ...status, clients });
      await service.refresh();
      expect(service.status()).toBeNull();
    }
    call.mockResolvedValue({ ...status, endpoint: 'private' });
    await service.refresh();
    expect(service.status()).toBeNull();
  });
  it('passes only explicitly supplied scopes and does not retry uncertain writes', async () => {
    const input = {
      provider: 'codex' as const,
      source_root: 'C:/synthetic/source',
      memory_roots: [],
      enabled: false,
      memory_enabled: false,
      revision: client.revision,
    };
    call.mockRejectedValue({ message: 'private transcript' });
    await service.configure(input);
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_configure', { input });
    expect(service.error()).not.toContain('private transcript');
    expect(service.status()).toBeNull();
  });
  it('rejects index results containing content and does not invoke in the browser', async () => {
    call.mockResolvedValue({
      status: 'indexed',
      sessions: 1,
      memories: 0,
      revisions: 1,
      text: 'private',
    });
    await service.rebuild();
    expect(service.index()).toBeNull();
    Reflect.deleteProperty(globalThis, '__TAURI_INTERNALS__');
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({ providers: [{ provide: VAULT_INVOKE, useValue: call }] });
    const browser = TestBed.inject(CaptureConnection);
    call.mockClear();
    await browser.refresh();
    expect(call).not.toHaveBeenCalled();
  });
  it('validates bounded import receipts and advances only to the returned page', async () => {
    call.mockResolvedValue({
      schema_version: 1,
      created: 1,
      updated: 0,
      unchanged: 0,
      acknowledged: 1,
      skipped: 1,
      memories_pending: 2,
      next_offset: 10,
    });
    await service.importCaptured();
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_import', { offset: 0 });
    expect(service.nextOffset()).toBe(10);
    expect(service.notice()).toContain('1 captured session imported or updated');
    call.mockResolvedValue({
      schema_version: 1,
      created: 0,
      updated: 0,
      unchanged: 0,
      acknowledged: 1,
      skipped: 0,
      memories_pending: 0,
      next_offset: 10,
      private_text: 'reject',
    });
    await service.importCaptured();
    expect(service.nextOffset()).toBe(10);
    expect(service.error()).not.toContain('private_text');
  });
  it('imports history only after explicit preview confirmation and uses its exact token', async () => {
    const preview = { preview_id: '01010101-0101-4101-8101-010101010101', source_root: 'C:/synthetic/source',
      sessions: 2, files: 2, bytes: 128, skipped: 0, earliest: null, latest: null };
    call.mockResolvedValue(preview);
    await service.previewHistory();
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_history_preview');
    expect(service.historyPreview()?.files).toBe(2);
    call.mockClear().mockResolvedValue({ captured: 2, skipped: 0, next_offset: null });
    await service.importHistory();
    expect(call).toHaveBeenCalledExactlyOnceWith('capture_history_import', { previewId: preview.preview_id, offset: 0 });
    expect(service.historyPreview()).toBeNull();
    expect(service.notice()).toContain('2 Codex history files captured');
  });
  it('does not retry an uncertain history write or accept a nonadvancing page', async () => {
    const preview = { preview_id: '01010101-0101-4101-8101-010101010101', source_root: 'C:/synthetic/source',
      sessions: 2, files: 2, bytes: 128, skipped: 0, earliest: null, latest: null };
    call.mockResolvedValue(preview);
    await service.previewHistory();
    call.mockClear().mockResolvedValue({ captured: 0, skipped: 0, next_offset: 0 });
    await service.importHistory();
    expect(call).toHaveBeenCalledTimes(1);
    expect(service.historyPreview()).toBeNull();
    expect(service.error()).toContain('failed');
    await service.importHistory();
    expect(call).toHaveBeenCalledTimes(1);
  });
});
