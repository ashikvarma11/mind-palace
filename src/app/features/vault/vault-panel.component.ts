import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LocalVault } from '../../core/local-vault';

@Component({
  selector: 'app-vault-panel',
  imports: [FormsModule, RouterLink],
  templateUrl: './vault-panel.component.html',
  styleUrl: './vault-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VaultPanel {
  readonly vault = inject(LocalVault);
  readonly showPaste = input(false);
  readonly query = signal('');
  readonly filtered = computed(() => {
    const term = this.query().trim().toLocaleLowerCase();
    return this.vault.list().items.filter((item) => !term || item.title.toLocaleLowerCase().includes(term));
  });
  readonly showOriginal = signal(false);
  readonly conversation = computed(() => {
    const session = this.vault.selected();
    const messages: { role: 'user' | 'assistant'; text: string }[] = [];
    let total = 0;
    if (session?.metadata.provider !== 'codex') return { messages, total };
    const object = (value: unknown): value is Record<string, unknown> =>
      typeof value === 'object' && value !== null && !Array.isArray(value);
    for (const line of session.source_text.split('\n')) {
      let value: unknown;
      try { value = JSON.parse(line); } catch { continue; }
      if (!object(value) || value['type'] !== 'response_item' || !object(value['payload'])) continue;
      const payload = value['payload'];
      const role = payload['role'];
      if (payload['type'] !== 'message' || (role !== 'user' && role !== 'assistant') || !Array.isArray(payload['content'])) continue;
      const text = payload['content']
        .filter((part): part is Record<string, unknown> => object(part) && (part['type'] === 'input_text' || part['type'] === 'output_text') && typeof part['text'] === 'string')
        .map((part) => String(part['text'])).join('\n');
      if (!text.trim()) continue;
      total += 1;
      messages.push({ role, text });
      if (messages.length > 200) messages.shift();
    }
    return { messages, total };
  });
}
