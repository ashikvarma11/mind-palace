import { Injectable, InjectionToken, inject, signal } from '@angular/core';
import { invoke } from '@tauri-apps/api/core';
import type {
  MemoryAnswer,
  CaptureImportResult,
  CaptureStatus,
  SessionCreated,
  SessionList,
  SessionRead,
  VaultStatus,
} from './contracts.generated';
import {
  validateMemoryAnswer,
  validateCaptureImportResult,
  validateCaptureIndexResult,
  validateCaptureStatus,
  validateCaptureCleanupResult,
  validateSessionCreated,
  validateSessionList,
  validateSessionRead,
  validateVaultStatus,
} from './validators.generated';

export const VAULT_INVOKE = new InjectionToken<typeof invoke>('Local vault invoke', {
  providedIn: 'root',
  factory: () => invoke,
});
const safeErrors: Record<string, string> = {
  BUSY: 'Another local operation is running. Wait and try again.',
  VAULT_CLOSED: 'Open the local vault first.',
  CONFLICT: 'Existing data was preserved. Close and reopen the vault to inspect it.',
  NOT_FOUND: 'The conversation was not found.',
  VALIDATION_ERROR: 'The request or stored data is invalid. Existing files were preserved.',
  LIMIT_EXCEEDED: 'This operation exceeds the supported size limit.',
  WORKER_DISCONNECTED:
    'The worker stopped. Reopen the vault. A save may already have completed; retry the unchanged draft only.',
  WORKER_SHUTDOWN_FAILED: 'Worker shutdown could not be confirmed. Close the app before reopening.',
  WORKER_RESOURCES_INVALID:
    'The bundled worker is missing or changed. Rebuild the verified development resources.',
  VAULT_PATH_INVALID: 'The local storage folder is unavailable or redirected.',
};

@Injectable({ providedIn: 'root' })
export class LocalVault {
  readonly native = '__TAURI_INTERNALS__' in globalThis;
  private readonly invoke = inject(VAULT_INVOKE);
  readonly connected = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly notice = signal('');
  readonly list = signal<SessionList>({ items: [], total: 0, next_offset: null });
  readonly selected = signal<SessionRead | null>(null);
  readonly answer = signal<MemoryAnswer | null>(null);
  readonly draftLocked = signal(false);
  draft = { title: '', body: '', source_text: '' };
  private pending: { op_id: string; title: string; body: string; source_text: string } | null =
    null;

  constructor() {
    if (this.native) void this.refreshStatus();
  }

  private async checked<T>(
    command: string,
    args: Record<string, unknown>,
    valid: (value: unknown) => boolean,
  ): Promise<T> {
    const value: unknown = await this.invoke(command, args);
    if (!valid(value)) throw { code: 'INVALID_RESPONSE' };
    return value as T;
  }
  private async run(operation: () => Promise<void>): Promise<void> {
    if (this.busy()) return;
    this.error.set('');
    if (!this.native) {
      this.error.set('Local storage is available only in the desktop app.');
      return;
    }
    this.busy.set(true);
    try {
      await operation();
    } catch (error: unknown) {
      const code =
        typeof error === 'object' && error !== null && 'code' in error ? String(error.code) : '';
      this.error.set(
        safeErrors[code] ??
          'The local operation failed or returned invalid data. No automatic retry was made.',
      );
      if (['WORKER_DISCONNECTED', 'INVALID_RESPONSE', 'VAULT_CLOSED'].includes(code)) {
        this.connected.set(false);
        this.list.set({ items: [], total: 0, next_offset: null });
        this.selected.set(null);
        this.answer.set(null);
      }
    } finally {
      this.busy.set(false);
    }
  }
  private async syncCapturedSessions(): Promise<number> {
    const status = await this.checked<CaptureStatus>('capture_status', {}, validateCaptureStatus);
    if (!status.clients.some((client) => client.provider === 'codex' && client.configured)) return 0;
    const indexed: unknown = await this.invoke('capture_index');
    if (!validateCaptureIndexResult(indexed)) throw { code: 'INVALID_RESPONSE' };
    let offset = 0;
    let changed = 0;
    for (let page = 0; page < 500; page += 1) {
      const result = await this.checked<CaptureImportResult>(
        'capture_import',
        { offset },
        validateCaptureImportResult,
      );
      changed += result.created + result.updated;
      if (result.next_offset === null) {
        const cleanup: unknown = await this.invoke('capture_cleanup');
        if (!validateCaptureCleanupResult(cleanup)) throw { code: 'INVALID_RESPONSE' };
        return changed;
      }
      if (result.next_offset <= offset) throw { code: 'INVALID_RESPONSE' };
      offset = result.next_offset;
    }
    throw { code: 'INVALID_RESPONSE' };
  }
  async refreshStatus(): Promise<void> {
    await this.run(async () => {
      const status = await this.checked<VaultStatus>('vault_status', {}, validateVaultStatus);
      if (status.connected) {
        await this.loadList(0);
        try {
          const imported = await this.syncCapturedSessions();
          await this.loadList(0);
          if (imported) this.notice.set(`${imported} Codex session${imported === 1 ? '' : 's'} synced to the local vault.`);
        } finally {
          this.connected.set(true);
        }
      }
      else {
        this.connected.set(false);
        this.list.set({ items: [], total: 0, next_offset: null });
        this.selected.set(null);
      }
    });
  }
  async open(create: boolean): Promise<void> {
    await this.run(async () => {
      const status = await this.checked<VaultStatus>('vault_open', { create }, validateVaultStatus);
      try {
        await this.loadList(0);
        const imported = await this.syncCapturedSessions();
        await this.loadList(0);
        this.notice.set(
          imported
            ? `${imported} Codex session${imported === 1 ? '' : 's'} synced to the local vault.`
            : 'Local vault open. No new captured revisions were imported.',
        );
      } finally {
        this.connected.set(status.connected);
      }
    });
  }
  async close(): Promise<void> {
    await this.run(async () => {
      const status = await this.checked<VaultStatus>('vault_close', {}, validateVaultStatus);
      this.connected.set(status.connected);
      this.list.set({ items: [], total: 0, next_offset: null });
      this.selected.set(null);
      this.answer.set(null);
      this.notice.set('Vault closed. Saved files remain on this device.');
    });
  }
  private async loadList(offset: number): Promise<void> {
    const list = await this.checked<SessionList>(
      'sessions_list',
      { limit: 50, offset },
      validateSessionList,
    );
    this.list.set(offset ? { ...list, items: [...this.list().items, ...list.items] } : list);
  }
  async reload(): Promise<void> {
    await this.run(async () => {
      const imported = await this.syncCapturedSessions();
      await this.loadList(0);
      this.notice.set(
        imported
          ? `${imported} Codex session${imported === 1 ? '' : 's'} synced to the local vault.`
          : 'No new captured revisions were imported. This does not verify hook delivery.',
      );
    });
  }
  async more(): Promise<void> {
    const offset = this.list().next_offset;
    if (offset !== null) await this.run(() => this.loadList(offset));
  }
  async read(id: string): Promise<void> {
    await this.run(async () => {
      this.selected.set(
        await this.checked<SessionRead>('sessions_read', { id }, validateSessionRead),
      );
    });
  }
  async ask(question: string): Promise<void> {
    if (!question.trim() || Array.from(question).length > 2000) {
      this.error.set('Enter a question of up to 2,000 characters.');
      return;
    }
    await this.run(async () => {
      this.answer.set(null);
      this.notice.set('');
      if (this.connected()) {
        try {
          const imported = await this.syncCapturedSessions();
          if (imported) await this.loadList(0);
        } catch (error: unknown) {
          const code = typeof error === 'object' && error !== null && 'code' in error
            ? String(error.code) : '';
          if (!['BUSY', 'CAPTURE_UNAVAILABLE', 'CAPTURE_TIMEOUT', 'CAPTURE_PROCESS_FAILED',
            'CAPTURE_RESOURCES_INVALID', 'CAPTURE_RESPONSE_INVALID'].includes(code)) throw error;
          this.notice.set('New captures could not be synced. This answer uses sessions already in the vault. Check Connections before retrying sync.');
        }
      }
      this.answer.set(
        await this.checked<MemoryAnswer>('sessions_ask', { question }, validateMemoryAnswer),
      );
    });
  }
  async save(): Promise<void> {
    if (
      !this.pending &&
      (!this.draft.title.trim() ||
        !this.draft.source_text ||
        Array.from(this.draft.title).length > 200 ||
        Array.from(this.draft.body).length > 32768 ||
        Array.from(this.draft.source_text).length > 65536)
    ) {
      this.error.set('Enter a title and original conversation within the displayed limits.');
      return;
    }
    await this.run(async () => {
      this.pending ??= { op_id: crypto.randomUUID(), ...this.draft };
      this.draftLocked.set(true);
      const receipt = await this.checked<SessionCreated>(
        'sessions_create',
        { input: this.pending },
        validateSessionCreated,
      );
      this.pending = null;
      this.draftLocked.set(false);
      this.draft = { title: '', body: '', source_text: '' };
      this.notice.set(
        'Conversation saved locally. It remains unreviewed; no decisions were inferred.',
      );
      await this.loadList(0);
      this.selected.set(
        await this.checked<SessionRead>('sessions_read', { id: receipt.id }, validateSessionRead),
      );
    });
  }
}
