import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AiGateway } from './ai-gateway';
import { LocalVault, VAULT_INVOKE } from './local-vault';
import type { AiPreviewRequest, AiPreviewResult, SessionRead } from './contracts.generated';

const original: SessionRead = {
  metadata: {
    schema_version: 1,
    id: '11111111-1111-4111-8111-111111111111',
    kind: 'session',
    title: 'Synthetic',
    source_id: '22222222-2222-4222-8222-222222222222',
    review_status: 'unreviewed',
    created_at: '2026-10-02T12:00:00Z',
  },
  body: 'Manual notes must not be shared.',
  source_text: 'A😀B<script>window.injected=true</script>',
};
function input(): AiPreviewRequest {
  return {
    provider: 'openai',
    model: 'synthetic-model',
    question: 'What is recorded?',
    max_output_tokens: 512,
    selections: [{ kind: 'session', id: original.metadata.id, start: 1, end: 2 }],
  };
}
function result(request = input()): AiPreviewResult {
  const selected = request.selections[0];
  const content = JSON.stringify({
    question: request.question,
    sources: [
      {
        source_id: 'S1',
        text: Array.from(original.source_text).slice(selected.start, selected.end).join(''),
      },
    ],
  });
  return {
    preview_id: '33333333-3333-4333-8333-333333333333',
    payload_sha256: 'a'.repeat(64),
    expires_in_seconds: 300,
    can_send: false,
    sharing_warning: 'Provider retention and API charges apply.',
    request: {
      provider: 'openai',
      endpoint: 'https://api.openai.com/v1/responses',
      headers: { 'Content-Type': 'application/json' },
      body: {
        model: request.model,
        instructions: 'Synthetic instructions',
        input: [{ role: 'user', content }],
        max_output_tokens: 512,
        store: false,
        stream: false,
      },
    },
    local_references: [{ ...selected, source_id: 'S1', snapshot_sha256: 'b'.repeat(64) }],
  };
}

describe('Offline AI preview boundary', () => {
  let call: ReturnType<typeof vi.fn>;
  let vault: LocalVault;
  let ai: AiGateway;
  beforeEach(async () => {
    Object.defineProperty(globalThis, '__TAURI_INTERNALS__', { configurable: true, value: {} });
    call = vi.fn().mockResolvedValue({ connected: false, ai_enabled: false });
    TestBed.configureTestingModule({ providers: [{ provide: VAULT_INVOKE, useValue: call }] });
    vault = TestBed.inject(LocalVault);
    await vi.waitFor(() => expect(vault.busy()).toBe(false));
    vault.connected.set(true);
    vault.selected.set(original);
    call.mockClear();
    ai = TestBed.inject(AiGateway);
  });
  afterEach(() => Reflect.deleteProperty(globalThis, '__TAURI_INTERNALS__'));

  it('uses Unicode code-point ranges, not UTF-16 offsets, and never invokes a sender', async () => {
    call.mockResolvedValue(result());
    await ai.create(input(), original);
    expect(ai.error()).toBe('');
    expect(ai.preview()?.can_send).toBe(false);
    expect(call).toHaveBeenCalledTimes(1);
    expect(call.mock.calls[0][0]).toBe('ai_preview');
    expect(JSON.stringify(ai.preview())).toContain('😀');
    expect(JSON.stringify(ai.preview())).not.toContain(original.body);
    ai.clock.set(ai.expiresAt() + 1);
    expect(ai.expired()).toBe(true);
    call.mockResolvedValue({ discarded: true });
    await ai.discard();
    expect(call.mock.calls[1][0]).toBe('ai_discard');
    expect(ai.preview()).toBeNull();
  });
  it('rejects invalid ranges/questions and does not create another receipt without discard', async () => {
    for (const [start, end] of [
      [0, 0],
      [0, 8001],
      [-1, 2],
      [1.5, 2],
      [0, 999],
    ]) {
      const request = input();
      request.selections[0].start = start;
      request.selections[0].end = end;
      await ai.create(request, original);
    }
    expect(call).not.toHaveBeenCalled();
    const longQuestion = input();
    longQuestion.question = '😀'.repeat(2001);
    await ai.create(longQuestion, original);
    expect(call).not.toHaveBeenCalled();
    call.mockResolvedValue(result());
    await ai.create(input(), original);
    await ai.create(input(), original);
    expect(call).toHaveBeenCalledTimes(1);
    expect(ai.error()).toContain('Discard');
  });
  it('validates the Anthropic message shape without changing providers', async () => {
    const request = input();
    request.provider = 'anthropic';
    const value = result(request);
    value.request = {
      provider: 'anthropic',
      endpoint: 'https://api.anthropic.com/v1/messages',
      headers: { 'Content-Type': 'application/json', 'anthropic-version': '2023-06-01' },
      body: {
        model: request.model,
        system: 'Synthetic instructions',
        messages: [
          {
            role: 'user',
            content: JSON.stringify({
              question: request.question,
              sources: [{ source_id: 'S1', text: '😀' }],
            }),
          },
        ],
        max_tokens: 512,
        stream: false,
      },
    };
    call.mockResolvedValue(value);
    await ai.create(request, original);
    expect(ai.error()).toBe('');
    expect(ai.preview()?.request.provider).toBe('anthropic');
  });
  it('fails closed on unexpected fields, endpoint/key injection and mismatched source content', async () => {
    for (const change of [
      (value: Record<string, unknown>) => {
        value['can_send'] = true;
      },
      (value: Record<string, unknown>) => {
        value['api_key'] = 'fake';
      },
      (value: Record<string, unknown>) => {
        (value['request'] as Record<string, unknown>)['endpoint'] = 'https://other.example';
      },
      (value: Record<string, unknown>) => {
        (value['request'] as { headers: Record<string, unknown> }).headers['Authorization'] =
          'fake';
      },
      (value: Record<string, unknown>) => {
        (value['request'] as { body: { input: { content: string }[] } }).body.input[0].content =
          JSON.stringify({ question: 'Changed', sources: [{ source_id: 'S1', text: 'invented' }] });
      },
    ]) {
      const value = structuredClone(result()) as unknown as Record<string, unknown>;
      change(value);
      call.mockResolvedValue(value);
      await ai.create(input(), original);
      expect(ai.preview()).toBeNull();
      expect(ai.error()).toContain('invalid data');
    }
  });
  it('freezes caller input and redacts arbitrary native error details', async () => {
    let finish!: (value: unknown) => void;
    call.mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const request = input();
    const expected = result(request);
    const pending = ai.create(request, original);
    request.question = 'Changed after click';
    request.selections[0].end = 4;
    finish(expected);
    await pending;
    expect(ai.error()).toBe('');
    ai.forget();
    call.mockRejectedValue({ code: 'UNKNOWN', message: 'private content fake key' });
    await ai.create(input(), original);
    expect(ai.error()).not.toContain('private');
    expect(ai.error()).not.toContain('fake key');
  });
  it('targets cancellation and stays busy until native cleanup completes, then refreshes storage', async () => {
    let reject!: (error: unknown) => void;
    call.mockImplementation((command: string) => {
      if (command === 'ai_preview')
        return new Promise((_, failure) => {
          reject = failure;
        });
      if (command === 'ai_cancel') return Promise.resolve(true);
      return Promise.resolve({ connected: false, ai_enabled: false });
    });
    const pending = ai.create(input(), original);
    await ai.create(input(), original);
    expect(call).toHaveBeenCalledTimes(1);
    await ai.cancel();
    expect(ai.busy()).toBe(true);
    expect(ai.cancelling()).toBe(true);
    expect(call.mock.calls[1][1].requestId).toBe(call.mock.calls[0][1].requestId);
    reject({ code: 'AI_CANCELLED' });
    await pending;
    expect(ai.busy()).toBe(false);
    expect(vault.connected()).toBe(false);
    expect(vault.selected()).toBeNull();
    expect(ai.error()).toContain('cancelled');
  });
  it('makes no native request in browser-only mode', async () => {
    Reflect.deleteProperty(globalThis, '__TAURI_INTERNALS__');
    TestBed.resetTestingModule();
    call.mockClear();
    TestBed.configureTestingModule({ providers: [{ provide: VAULT_INVOKE, useValue: call }] });
    ai = TestBed.inject(AiGateway);
    await ai.create(input(), original);
    expect(call).not.toHaveBeenCalled();
    expect(ai.error()).toContain('desktop');
  });
});
