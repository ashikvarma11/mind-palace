import { computed, Injectable, signal } from '@angular/core';

export type DecisionState = 'proposed' | 'confirmed' | 'rejected';
export type PageKey =
  | 'welcome'
  | 'today'
  | 'sessions'
  | 'decisions'
  | 'ask'
  | 'resume'
  | 'connections'
  | 'settings';
export interface SampleTask {
  readonly id: string;
  readonly title: string;
  readonly reason: string;
  readonly done: boolean;
}
export interface ReviewEvent {
  readonly sequence: number;
  readonly from: DecisionState;
  readonly to: DecisionState;
  readonly basis: 'preview_user_action';
}
export interface SampleAnswer {
  readonly status: 'sample_answer' | 'insufficient_evidence';
  readonly text: string;
  readonly evidence: readonly string[];
}

const initialTasks: readonly SampleTask[] = [
  {
    id: 'errors',
    title: 'Review the checkout error states',
    reason: 'Recorded next step · Checkout architecture',
    done: false,
  },
  {
    id: 'form-state',
    title: 'Review delivery-form state',
    reason: 'An open proposal needs your decision',
    done: false,
  },
  {
    id: 'design',
    title: 'Prepare the design review',
    reason: 'Recorded task · Product review notes',
    done: false,
  },
];

/** Explicit synthetic browser gateway. No durable writes, extraction, or inference. */
@Injectable({ providedIn: 'root' })
export class WorkspaceStore {
  private readonly active = signal(false);
  private readonly proposal = signal<DecisionState>('proposed');
  private readonly taskState = signal<readonly SampleTask[]>([]);
  private readonly events = signal<readonly ReviewEvent[]>([]);
  private readonly summary = signal(false);
  readonly sampleActive = this.active.asReadonly();
  readonly decisionState = this.proposal.asReadonly();
  readonly tasks = this.taskState.asReadonly();
  readonly history = this.events.asReadonly();
  readonly summaryReviewed = this.summary.asReadonly();
  readonly priorities = computed(() =>
    this.taskState()
      .filter((task) => !task.done)
      .slice(0, 3),
  );
  readonly proposalDescription = computed(() => {
    switch (this.proposal()) {
      case 'confirmed':
        return 'Signals for isolated delivery-form state were confirmed in this sample review.';
      case 'rejected':
        return 'The delivery-form signals proposal was rejected in this sample review.';
      default:
        return 'The delivery-form signals proposal is still unresolved.';
    }
  });
  readonly handoff = computed(() => {
    if (!this.active()) return '';
    const state = this.proposal();
    const next =
      this.priorities()[0]?.title ?? 'No unfinished sample task remains. Choose a new next step.';
    const reviewed =
      state === 'confirmed'
        ? 'CONFIRMED DURING SAMPLE REVIEW\nUse signals for isolated delivery-form state.\nBasis: explicit review action, not the original assistant suggestion.'
        : state === 'rejected'
          ? 'REJECTED DURING SAMPLE REVIEW\nDo not apply the delivery-form signals proposal.\nBasis: explicit review action.'
          : 'NOT YET APPROVED\nUse signals for isolated delivery-form state.\nSource: sample assistant message 15.\nThis is a suggestion, not a requirement.';
    const done =
      this.taskState()
        .filter((t) => t.done)
        .map((t) => '- ' + t.title)
        .join('\n') || 'No sample task has been marked done.';
    return `SYNTHETIC SAMPLE — NOT YOUR ACTUAL MEMORY\n\nTASK\nContinue Storefront checkout work.\n\nCONFIRMED CHOICE\nKeep NgRx for shared checkout state.\nReason: event history helps debug payment issues.\nSource: sample Checkout architecture, user message 14.\n\n${reviewed}\n\nCOMPLETED SAMPLE TASKS\n${done}\n\nOPEN QUESTIONS\n${state === 'proposed' ? 'Should delivery-form state use signals?\n' : ''}Which payment errors need dedicated UI states?\n\nNEXT ACTION\n${next}\n\nNo code implementation or failed attempt is asserted by this sample. Verify original evidence before using a real handoff.`;
  });

  activateSample(): void {
    this.proposal.set('proposed');
    this.taskState.set(initialTasks.map((task) => ({ ...task })));
    this.events.set([]);
    this.summary.set(false);
    this.active.set(true);
  }
  closeSample(): void {
    this.active.set(false);
    this.proposal.set('proposed');
    this.taskState.set([]);
    this.events.set([]);
    this.summary.set(false);
  }
  reviewSummary(): void {
    if (this.active()) this.summary.set(true);
  }
  reviewDecision(to: DecisionState): void {
    if (!this.active() || this.proposal() === to) return;
    const from = this.proposal();
    this.events.update((events) => [
      ...events,
      { sequence: events.length + 1, from, to, basis: 'preview_user_action' },
    ]);
    this.proposal.set(to);
    this.taskState.update((tasks) =>
      tasks.map((task) => (task.id === 'form-state' ? { ...task, done: to !== 'proposed' } : task)),
    );
  }
  setTaskDone(id: string, done: boolean): void {
    if (this.active())
      this.taskState.update((tasks) =>
        tasks.map((task) => (task.id === id ? { ...task, done } : task)),
      );
  }
  answer(question: string): SampleAnswer {
    if (!this.active())
      return {
        status: 'insufficient_evidence',
        text: 'No memory service is connected. Explore the fictional sample to preview this screen.',
        evidence: [],
      };
    const q = question
      .trim()
      .toLowerCase()
      .replace(/[?!.]+$/, '');
    if (q === 'why did we keep ngrx')
      return {
        status: 'sample_answer',
        text:
          'In this fictional conversation, NgRx was kept for shared checkout state because event history helps debug payment issues. ' +
          this.proposalDescription() +
          ' The shared-state choice is unchanged.',
        evidence: ['Sample user message 14', 'Sample assistant message 15'],
      };
    if (q === 'what should i do next')
      return {
        status: 'sample_answer',
        text:
          'The first unfinished recorded sample task is: ' +
          (this.priorities()[0]?.title ?? 'none — all sample tasks are complete.'),
        evidence: ['Synthetic task fixture'],
      };
    return {
      status: 'insufficient_evidence',
      text: 'I don’t have enough evidence. This prototype only answers its listed sample questions; no AI model is running.',
      evidence: [],
    };
  }
}
