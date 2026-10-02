import { WorkspaceStore } from './workspace-store';

describe('Synthetic workspace integrity', () => {
  let store: WorkspaceStore;
  beforeEach(() => {
    store = new WorkspaceStore();
  });
  it('starts empty and never invents three priorities', () => {
    expect(store.sampleActive()).toBe(false);
    expect(store.priorities()).toEqual([]);
    expect(store.handoff()).toBe('');
  });
  it('reviewing a session summary does not confirm a suggestion', () => {
    store.activateSample();
    store.reviewSummary();
    expect(store.summaryReviewed()).toBe(true);
    expect(store.decisionState()).toBe('proposed');
    expect(store.history()).toEqual([]);
    expect(store.handoff()).toContain('NOT YET APPROVED');
  });
  it('explicit confirmation is audited and updates handoff without rewriting its source', () => {
    store.activateSample();
    store.reviewDecision('confirmed');
    store.reviewDecision('confirmed');
    expect(store.history()).toHaveLength(1);
    expect(store.history()[0]).toMatchObject({
      from: 'proposed',
      to: 'confirmed',
      basis: 'preview_user_action',
    });
    expect(store.handoff()).toContain('CONFIRMED DURING SAMPLE REVIEW');
    expect(store.handoff()).not.toContain('NOT YET APPROVED');
    expect(store.handoff()).toContain('Keep NgRx');
  });
  it('rejection and reopening preserve their history and current uncertainty', () => {
    store.activateSample();
    store.reviewDecision('rejected');
    expect(store.handoff()).toContain('REJECTED DURING SAMPLE REVIEW');
    store.reviewDecision('proposed');
    expect(store.history()).toHaveLength(2);
    expect(store.handoff()).toContain('Should delivery-form state use signals?');
  });
  it('does not infer completed work from the end of a conversation', () => {
    store.activateSample();
    expect(store.handoff()).toContain('No sample task has been marked done.');
    store.setTaskDone('errors', true);
    expect(store.priorities()).toHaveLength(2);
    expect(store.handoff()).toContain('- Review the checkout error states');
    expect(store.handoff()).not.toContain('NEXT ACTION\nReview the checkout error states');
  });
  it('abstains for unknown questions and resets all fictional state', () => {
    store.activateSample();
    expect(store.answer('What about the pricing plan?').status).toBe('insufficient_evidence');
    expect(store.answer('Why did we keep NgRx?').evidence.length).toBe(2);
    store.reviewDecision('confirmed');
    store.activateSample();
    expect(store.decisionState()).toBe('proposed');
    expect(store.history()).toEqual([]);
    store.closeSample();
    store.reviewDecision('confirmed');
    expect(store.decisionState()).toBe('proposed');
    expect(store.tasks()).toEqual([]);
  });
});
