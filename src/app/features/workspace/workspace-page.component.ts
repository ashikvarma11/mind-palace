import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  LucideDynamicIcon,
  LucideArrowUpRight,
  LucideShieldCheck,
  LucideListChecks,
  LucideQuote,
  LucideFolder,
  LucideMessagesSquare,
  LucideGitBranch,
  LucideFileText,
  LucideFileCode,
  LucidePlus,
  LucideCheck,
  LucideSparkles,
} from '@lucide/angular';
import { PageKey, SampleAnswer, WorkspaceStore } from '../../core/workspace-store';
import { VaultPanel } from '../vault/vault-panel.component';
import { LocalVault } from '../../core/local-vault';
import { AiPreviewPanel } from '../ask/ai-preview-panel.component';

@Component({
  selector: 'app-workspace-page',
  imports: [RouterLink, FormsModule, LucideDynamicIcon, VaultPanel, AiPreviewPanel],
  templateUrl: './workspace-page.component.html',
  styleUrl: './workspace-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkspacePage {
  readonly page = input.required<PageKey>();
  readonly store = inject(WorkspaceStore);
  readonly vault = inject(LocalVault);
  readonly evidenceOpen = signal(false);
  readonly selectedNode = signal('project');
  readonly answer = signal<SampleAnswer | null>(null);
  readonly submittedQuestion = signal('');
  readonly notice = signal('');
  readonly logoMissing = signal(false);
  readonly editedHandoff = signal<string | null>(null);
  readonly draft = computed(() => this.editedHandoff() ?? this.store.handoff());
  readonly icons = {
    arrow: LucideArrowUpRight,
    shield: LucideShieldCheck,
    list: LucideListChecks,
    quote: LucideQuote,
    plus: LucidePlus,
    check: LucideCheck,
    sparkle: LucideSparkles,
  };
  readonly nodes = [
    {
      id: 'project',
      title: 'Storefront checkout',
      type: 'Project',
      icon: LucideFolder,
      detail: 'A sample project connecting checkout conversations, decisions, and work notes.',
    },
    {
      id: 'session',
      title: 'Checkout architecture',
      type: 'Session',
      icon: LucideMessagesSquare,
      detail:
        'A fictional conversation with original messages, a confirmed shared-state choice, and a separate proposal.',
    },
    {
      id: 'decision',
      title: 'Keep NgRx',
      type: 'Decision',
      icon: LucideGitBranch,
      detail: 'The sample user confirms NgRx for shared checkout state in message 14.',
    },
    {
      id: 'note',
      title: 'Error-state notes',
      type: 'Note',
      icon: LucideFileText,
      detail: 'A synthetic note related to the recorded checkout error review.',
    },
    {
      id: 'code',
      title: 'checkout.store.ts',
      type: 'Code · future capability',
      icon: LucideFileCode,
      detail:
        'Illustrative code relationship only. No repository is connected and Graphify is not running.',
    },
  ];
  readonly node = computed(
    () => this.nodes.find((node) => node.id === this.selectedNode()) ?? this.nodes[0],
  );
  readonly day = new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date());
  question = '';
  theme = document.documentElement.dataset['theme'] ?? 'system';

  activateSample(): void {
    this.store.activateSample();
    this.answer.set(null);
    this.notice.set('Fictional sample loaded. All changes are in memory and reset on reload.');
  }
  ask(question = this.question): void {
    this.question = question;
    this.submittedQuestion.set(question);
    this.answer.set(this.store.answer(question));
  }
  updateDraft(value: string): void {
    this.editedHandoff.set(value);
  }
  restoreDraft(): void {
    this.editedHandoff.set(null);
    this.notice.set('Draft refreshed from the current sample decisions and tasks.');
  }
  selectDraft(textarea: HTMLTextAreaElement): void {
    textarea.focus();
    textarea.select();
    this.notice.set(
      'Text selected. Copy using your normal keyboard shortcut. Pasting into a cloud assistant shares it with that provider.',
    );
  }
  setTheme(value: string): void {
    this.theme = value;
    if (value === 'light' || value === 'dark') document.documentElement.dataset['theme'] = value;
    else delete document.documentElement.dataset['theme'];
  }
}
