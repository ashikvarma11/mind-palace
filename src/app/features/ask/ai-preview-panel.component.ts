import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LocalVault } from '../../core/local-vault';

@Component({
  selector: 'app-ai-preview-panel',
  imports: [FormsModule, RouterLink],
  templateUrl: './ai-preview-panel.component.html',
  styleUrl: './ai-preview-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AiPreviewPanel {
  readonly vault = inject(LocalVault);
  private readonly router = inject(Router);
  question = '';
  async ask(): Promise<void> {
    await this.vault.ask(this.question);
  }
  async openSource(id: string): Promise<void> {
    await this.vault.read(id);
    if (this.vault.selected()?.metadata.id === id) await this.router.navigate(['/sessions']);
  }
}
