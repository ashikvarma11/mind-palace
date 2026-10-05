import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { CapturePanel } from './capture-panel.component';
import { CaptureConnection } from '../../core/capture-connection';
import { LocalVault } from '../../core/local-vault';

describe('Codex setup guidance', () => {
  const client = { provider: 'codex', configured: true, enabled: true, memory_enabled: false,
    source_root: 'C:/synthetic/sessions', memory_roots: [], revision: 'a'.repeat(64), snippet: '' };
  function setup(enabled = true) {
    const connection = { native: true, refresh: vi.fn().mockResolvedValue(undefined),
      status: signal({ inbox_root: 'C:/synthetic/inbox', clients: [ { ...client, enabled } ],
        health: { bytes_used: 0, quota_bytes: 1073741824, failures: 0, pending_spool: 0,
          retention_days: 30, last_indexed_at: null } }),
      codexHook: signal({ status: 'installed', config_path: 'C:/synthetic/hooks.json', trust_verified: false }),
      busy: signal(false), error: signal(''), notice: signal(''), index: signal(null),
      nextOffset: signal(null), historyPreview: signal(null) };
    const vault = { connected: signal(false), busy: signal(false), error: signal(''), notice: signal(''),
      reload: vi.fn().mockResolvedValue(undefined), open: vi.fn() };
    TestBed.configureTestingModule({ imports: [CapturePanel], providers: [provideRouter([]),
      { provide: CaptureConnection, useValue: connection }, { provide: LocalVault, useValue: vault }] });
    return { connection, vault, fixture: TestBed.createComponent(CapturePanel) };
  }
  it('restores saved scope but never labels installed hooks as trusted', async () => {
    const { fixture, vault } = setup();
    await fixture.whenStable();
    fixture.detectChanges();
    const element = fixture.nativeElement as HTMLElement;
    expect((element.querySelector('#capture-source') as HTMLInputElement).value).toBe(client.source_root);
    expect(element.textContent).toContain('Runtime approval is not checked here.');
    const sync = [...element.querySelectorAll('button')].find((button) => button.textContent?.trim() === 'Sync Codex to vault');
    expect(sync?.disabled).toBe(true);
    await fixture.componentInstance.syncNow();
    expect(vault.reload).not.toHaveBeenCalled();
  });
  it('keeps paused scope and consent paused when the page opens', async () => {
    const { fixture } = setup(false);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Capture is paused.');
    expect((fixture.nativeElement.querySelector('[name="enabled"]') as HTMLInputElement).checked).toBe(false);
  });
  it('does not use stale installed state after a refresh failure', async () => {
    const { fixture, connection } = setup();
    await fixture.whenStable();
    connection.error.set('Capture status unavailable.');
    fixture.detectChanges();
    const guide = fixture.nativeElement.querySelector('.setup-guide') as HTMLElement;
    expect(guide.textContent).toContain('Status unavailable.');
    expect(guide.textContent).not.toContain('Hook file installed.');
    expect(fixture.nativeElement.querySelector('[role="alert"]')?.textContent).toContain('Capture status unavailable.');
  });
});
