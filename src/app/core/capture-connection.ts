import { Injectable, inject, signal } from '@angular/core';
import { VAULT_INVOKE } from './local-vault';
import type {
  CaptureClient,
  CaptureImportResult,
  CaptureIndexResult,
  CaptureHookStatus,
  CaptureRecoveryResult,
  CaptureHistoryPreview,
  CaptureHistoryImportResult,
  CaptureCleanupResult,
  CaptureStatus,
} from './contracts.generated';
import {
  validateCaptureImportResult,
  validateCaptureIndexResult,
  validateCaptureHookStatus,
  validateCaptureRecoveryResult,
  validateCaptureHistoryPreview,
  validateCaptureHistoryImportResult,
  validateCaptureCleanupResult,
  validateCaptureStatus,
} from './validators.generated';

export interface CaptureScope {
  provider: 'claude-code' | 'codex';
  source_root: string;
  memory_roots: string[];
  enabled: boolean;
  memory_enabled: boolean;
  revision: string;
}

@Injectable({ providedIn: 'root' })
export class CaptureConnection {
  readonly native = '__TAURI_INTERNALS__' in globalThis;
  private readonly invoke = inject(VAULT_INVOKE);
  readonly status = signal<CaptureStatus | null>(null);
  readonly index = signal<CaptureIndexResult | null>(null);
  readonly codexHook = signal<CaptureHookStatus | null>(null);
  readonly historyPreview = signal<CaptureHistoryPreview | null>(null);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly notice = signal('');
  readonly nextOffset = signal<number | null>(0);

  private async run(operation: () => Promise<void>): Promise<void> {
    if (this.busy()) return;
    this.error.set('');
    this.notice.set('');
    if (!this.native) {
      this.error.set('Hook setup is available in the desktop app.');
      return;
    }
    this.busy.set(true);
    try {
      await operation();
    } catch (error: unknown) {
      this.historyPreview.set(null);
      this.status.set(null);
      this.index.set(null);
      const code = typeof error === 'object' && error !== null && 'code' in error
        ? String(error.code)
        : error instanceof Error && error.message === 'Invalid response' ? 'INVALID_RESPONSE' : 'UNAVAILABLE';
      this.error.set(
        `Capture setup failed (${code}). Refresh before retrying; a configuration change may have completed. Existing snapshots remain on disk.`,
      );
    } finally {
      this.busy.set(false);
    }
  }
  private accept(value: unknown): void {
    if (!validateCaptureStatus(value)) throw new Error('Invalid response');
    const status = value as CaptureStatus;
    if (
      new Set(status.clients.map((item) => item.provider)).size !== 2 ||
      status.clients.some(
        (item) =>
          (!item.configured && (item.enabled || item.memory_enabled || item.snippet !== '')) ||
          (item.memory_enabled && item.memory_roots.length === 0),
      )
    )
      throw new Error('Invalid client state');
    this.status.set(status);
  }
  private async hook(action: 'status' | 'install' | 'remove'): Promise<CaptureHookStatus> {
    const value: unknown = await this.invoke('capture_codex_hook', { action });
    if (!validateCaptureHookStatus(value)) throw new Error('Invalid hook response');
    const result = value as CaptureHookStatus;
    this.codexHook.set(result);
    return result;
  }
  async refresh(): Promise<void> {
    await this.run(async () => {
      this.accept(await this.invoke('capture_status'));
      if (this.status()?.clients.some((client) => client.provider === 'codex' && client.configured)) {
        await this.hook('status');
      } else this.codexHook.set(null);
    });
  }
  async configure(input: CaptureScope): Promise<void> {
    await this.run(async () => {
      this.historyPreview.set(null);
      this.accept(await this.invoke('capture_configure', { input }));
      if (input.provider === 'codex') await this.hook('status');
      this.notice.set(
        input.enabled
          ? 'Capture allowed for this scope. Install the hook snippet to start collecting.'
          : 'Capture paused for this client. Existing snapshots are retained.',
      );
    });
  }
  async installCodexHook(): Promise<void> {
    await this.run(async () => {
      const result = await this.hook('install');
      this.notice.set(
        `Mind Palace handlers were merged into ${result.config_path}. Codex may ask you to trust this hook when a new session starts.`,
      );
    });
  }
  async removeCodexHook(): Promise<void> {
    await this.run(async () => {
      const result = await this.hook('remove');
      this.notice.set(`Mind Palace handlers were removed from ${result.config_path}. Other hooks were preserved.`);
    });
  }
  async recover(): Promise<void> {
    await this.run(async () => {
      const value: unknown = await this.invoke('capture_recover');
      if (!validateCaptureRecoveryResult(value)) throw new Error('Invalid response');
      const result = value as CaptureRecoveryResult;
      this.notice.set(`${result.restored} known session revisions recovered; ${result.unchanged} current; ${result.skipped} unavailable or invalid files skipped.`);
    });
  }
  async cleanup(): Promise<void> {
    await this.run(async () => {
      const value: unknown = await this.invoke('capture_cleanup');
      if (!validateCaptureCleanupResult(value)) throw new Error('Invalid response');
      const result = value as CaptureCleanupResult;
      this.accept(await this.invoke('capture_status'));
      this.notice.set(result.deferred
        ? 'Cleanup exceeded its validation limit. All files were kept. Stored sessions remain available.'
        : `${result.removed_revisions} old imported prefixes removed. The complete acknowledged source remains in the inbox and vault.`);
    });
  }
  async previewHistory(): Promise<void> {
    await this.run(async () => {
      const value: unknown = await this.invoke('capture_history_preview');
      if (!validateCaptureHistoryPreview(value)) throw new Error('Invalid response');
      this.historyPreview.set(value as CaptureHistoryPreview);
    });
  }
  dismissHistory(): void {
    this.historyPreview.set(null);
  }
  async importHistory(): Promise<void> {
    const preview = this.historyPreview();
    if (!preview) return;
    await this.run(async () => {
      this.historyPreview.set(null);
      let offset = 0;
      let captured = 0;
      let skipped = 0;
      for (let page = 0; page < 100; page += 1) {
        const value: unknown = await this.invoke('capture_history_import', { previewId: preview.preview_id, offset });
        if (!validateCaptureHistoryImportResult(value)) throw new Error('Invalid response');
        const result = value as CaptureHistoryImportResult;
        captured += result.captured;
        skipped += result.skipped;
        if (result.next_offset === null) {
          this.notice.set(`${captured} Codex history files captured; ${skipped} changed or invalid files skipped. Originals stay in their source folder.`);
          return;
        }
        if (result.next_offset <= offset) throw new Error('Invalid response');
        offset = result.next_offset;
      }
      throw new Error('Invalid response');
    });
  }
  async pause(client: CaptureClient): Promise<void> {
    await this.configure({
      provider: client.provider,
      source_root: client.source_root,
      memory_roots: client.memory_roots,
      enabled: false,
      memory_enabled: client.memory_enabled,
      revision: client.revision,
    });
  }
  async rebuild(): Promise<void> {
    await this.run(async () => {
      const value: unknown = await this.invoke('capture_index');
      if (!validateCaptureIndexResult(value)) throw new Error('Invalid index response');
      this.index.set(value as CaptureIndexResult);
      this.accept(await this.invoke('capture_status'));
      this.nextOffset.set(0);
      this.notice.set(
        'Inbox validated and index rebuilt. You can import captured sessions into the open vault.',
      );
    });
  }
  async importCaptured(): Promise<void> {
    const offset = this.nextOffset() ?? 0;
    await this.run(async () => {
      const value: unknown = await this.invoke('capture_import', { offset });
      if (!validateCaptureImportResult(value)) throw new Error('Invalid import response');
      const result = value as CaptureImportResult;
      this.nextOffset.set(result.next_offset);
      const changed = result.created + result.updated;
      this.notice.set(
        `${changed} captured session${changed === 1 ? '' : 's'} imported or updated; ${result.unchanged} already current. ` +
          `${result.skipped} ambiguous or oversized; ${result.memories_pending} memory snapshot${result.memories_pending === 1 ? '' : 's'} remain unreviewed in the inbox.` +
          (result.next_offset === null ? '' : ' Another bounded page is ready to import.'),
      );
    });
  }
}
