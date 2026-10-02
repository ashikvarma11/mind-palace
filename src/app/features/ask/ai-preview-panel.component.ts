import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AiGateway } from '../../core/ai-gateway';
import { LocalVault } from '../../core/local-vault';

@Component({
  selector: 'app-ai-preview-panel',
  imports: [FormsModule, RouterLink],
  templateUrl: './ai-preview-panel.component.html',
  styleUrl: './ai-preview-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AiPreviewPanel {
  readonly ai = inject(AiGateway);
  readonly vault = inject(LocalVault);
  readonly sourceLength = computed(
    () => Array.from(this.vault.selected()?.source_text ?? '').length,
  );
  readonly payload = computed(() => JSON.stringify(this.ai.preview()?.request ?? {}, null, 2));
  provider: 'openai' | 'anthropic' = 'openai';
  model = '';
  question = '';
  start = 0;
  end = 0;
  session = '';

  constructor() {
    this.ai.clock.set(performance.now());
    const timer = setInterval(() => this.ai.clock.set(performance.now()), 1000);
    inject(DestroyRef).onDestroy(() => clearInterval(timer));
    effect(() => {
      const selected = this.vault.selected();
      if (selected) {
        this.session = selected.metadata.id;
        this.start = 0;
        // Require an explicit end offset; never automatically select a full conversation.
        this.end = 0;
      }
    });
  }
  async load(): Promise<void> {
    if (this.ai.preview() || this.ai.busy() || this.vault.busy()) return;
    // A failed read must not leave a previously loaded conversation selectable
    // as if it belonged to the newly chosen title.
    this.vault.selected.set(null);
    this.end = 0;
    this.ai.error.set('');
    await this.vault.read(this.session);
  }
  async create(): Promise<void> {
    const original = this.vault.selected();
    if (!original) return;
    await this.ai.create(
      {
        provider: this.provider,
        model: this.model,
        question: this.question,
        max_output_tokens: 512,
        selections: [
          { kind: 'session', id: original.metadata.id, start: this.start, end: this.end },
        ],
      },
      original,
    );
  }
}
