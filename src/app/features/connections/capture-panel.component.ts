import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CaptureConnection } from '../../core/capture-connection';
import type { CaptureClient } from '../../core/contracts.generated';
import { LocalVault } from '../../core/local-vault';

@Component({
  selector: 'app-capture-panel',
  imports: [FormsModule, RouterLink],
  templateUrl: './capture-panel.component.html',
  styleUrl: './capture-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CapturePanel {
  readonly connection = inject(CaptureConnection);
  readonly vault = inject(LocalVault);
  readonly codex = computed(() => this.connection.status()?.clients.find((client) => client.provider === 'codex'));
  provider: 'claude-code' | 'codex' = 'codex';
  sourceRoot = '';
  memoryRoots = '';
  enabled = false;
  memoryEnabled = false;
  private revision = '';
  usage(bytes: number): string {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }
  constructor() {
    if (this.connection.native) void this.loadScope();
  }
  private async loadScope(): Promise<void> {
    await this.connection.refresh();
    this.selectProvider();
  }
  async syncNow(): Promise<void> {
    if (this.connection.busy() || this.vault.busy() || !this.vault.connected()) return;
    await this.vault.reload();
    await this.connection.refresh();
  }
  edit(client: CaptureClient): void {
    this.provider = client.provider;
    this.sourceRoot = client.source_root;
    this.memoryRoots = client.memory_roots.join('\n');
    this.enabled = client.enabled;
    this.memoryEnabled = client.memory_enabled;
    this.revision = client.revision;
  }
  async save(): Promise<void> {
    const client = this.connection
      .status()
      ?.clients.find((item) => item.provider === this.provider);
    if (!client) return;
    await this.connection.configure({
      provider: this.provider,
      source_root: this.sourceRoot.trim(),
      memory_roots: this.memoryRoots
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean),
      enabled: this.enabled,
      memory_enabled: this.memoryEnabled,
      revision: this.revision || client.revision,
    });
    this.revision = '';
  }
  selectProvider(): void {
    const client = this.connection
      .status()
      ?.clients.find((item) => item.provider === this.provider);
    if (client) this.edit(client);
  }
  selectSnippet(element: HTMLTextAreaElement): void {
    element.focus();
    element.select();
  }
  async pause(client: CaptureClient): Promise<void> {
    await this.connection.pause(client);
    const updated = this.connection
      .status()
      ?.clients.find((item) => item.provider === client.provider);
    if (updated && this.provider === updated.provider) this.edit(updated);
  }
  async importCaptured(): Promise<void> {
    await this.connection.importCaptured();
    if (!this.connection.error()) await this.vault.reload();
  }
  async recover(): Promise<void> {
    await this.connection.recover();
    if (this.vault.connected()) await this.vault.reload();
  }
  async importHistory(): Promise<void> {
    await this.connection.importHistory();
    if (this.vault.connected()) await this.vault.reload();
  }
}
