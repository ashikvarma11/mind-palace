import { Injectable, effect, inject, signal } from '@angular/core';
import { LocalVault, VAULT_INVOKE } from './local-vault';
import type {
  AiPreviewRequest,
  AiPreviewResult,
  AiPrompt,
  SessionRead,
} from './contracts.generated';
import {
  validateAiDiscardResult,
  validateAiPreviewRequest,
  validateAiPreviewResult,
  validateAiPrompt,
} from './validators.generated';

const errors: Record<string, string> = {
  AI_CANCELLED: 'Preview cancelled. Reopen the local vault to continue.',
  AI_TIMEOUT: 'Preview timed out. Reopen the local vault to continue.',
  BUSY: 'Another local operation is running. Wait and try again.',
  CONFLICT: 'The preview or source changed. Discard it and create a new preview.',
  LIMIT_EXCEEDED: 'The request exceeds a local limit. Shorten the excerpt or restart the app.',
  VALIDATION_ERROR: 'Choose a valid question, model and source range within the displayed limits.',
  VAULT_CLOSED: 'Open the local vault first.',
  WORKER_DISCONNECTED: 'The worker stopped. Close and reopen the local vault.',
  WORKER_SHUTDOWN_FAILED: 'Worker shutdown could not be confirmed. Close the app before retrying.',
};

@Injectable({ providedIn: 'root' })
export class AiGateway {
  readonly vault = inject(LocalVault);
  private readonly invoke = inject(VAULT_INVOKE);
  readonly busy = signal(false);
  readonly cancelling = signal(false);
  readonly error = signal('');
  readonly preview = signal<AiPreviewResult | null>(null);
  readonly clock = signal(performance.now());
  readonly expiresAt = signal(0);
  private active: string | null = null;

  constructor() {
    effect(() => {
      if (!this.vault.connected()) this.forget();
    });
  }

  expired(): boolean {
    return this.clock() >= this.expiresAt();
  }
  forget(): void {
    this.preview.set(null);
    this.expiresAt.set(0);
  }

  private async run(operation: (requestId: string) => Promise<void>): Promise<void> {
    if (this.busy() || this.vault.busy()) return;
    this.error.set('');
    if (!this.vault.native || !this.vault.connected()) {
      this.error.set(
        'Open a local vault in the desktop app. This browser cannot preview real memory.',
      );
      return;
    }
    this.busy.set(true);
    this.vault.busy.set(true);
    this.active = crypto.randomUUID();
    let refresh = false;
    try {
      await operation(this.active);
    } catch (error: unknown) {
      this.forget();
      const code =
        typeof error === 'object' && error !== null && 'code' in error ? String(error.code) : '';
      this.error.set(
        errors[code] ??
          'Preview failed or returned invalid data. Nothing was sent; no automatic retry was made.',
      );
      refresh = ['AI_CANCELLED', 'AI_TIMEOUT', 'WORKER_DISCONNECTED', 'VAULT_CLOSED'].includes(
        code,
      );
    } finally {
      this.active = null;
      this.busy.set(false);
      this.cancelling.set(false);
      this.vault.busy.set(false);
      if (refresh) await this.vault.refreshStatus();
    }
  }

  async create(input: AiPreviewRequest, original: SessionRead): Promise<void> {
    if (this.preview()) {
      this.error.set('Discard the current preview before editing or creating another.');
      return;
    }
    if (!validateAiPreviewRequest(input)) {
      this.error.set(errors['VALIDATION_ERROR']);
      return;
    }
    const selection = input.selections[0];
    const points = Array.from(original.source_text);
    if (
      !selection ||
      selection.id !== original.metadata.id ||
      selection.end <= selection.start ||
      selection.end > points.length ||
      selection.end - selection.start > 8000
    ) {
      this.error.set(errors['VALIDATION_ERROR']);
      return;
    }
    // Capture immutable expected input before any await; a caller's draft
    // changes cannot silently change the request or its validation basis.
    const request: AiPreviewRequest = structuredClone(input);
    const captured = request.selections[0];
    const expectedText = points.slice(selection.start, selection.end).join('');
    const started = performance.now();
    await this.run(async (requestId) => {
      this.forget();
      const result: unknown = await this.invoke('ai_preview', { requestId, input: request });
      if (!validateAiPreviewResult(result)) throw { code: 'INVALID_RESPONSE' };
      const preview = result as AiPreviewResult;
      const provider = preview.request;
      const content =
        provider.provider === 'openai'
          ? provider.body.input[0].content
          : provider.body.messages[0].content;
      const prompt: unknown = JSON.parse(content);
      const cap =
        provider.provider === 'openai' ? provider.body.max_output_tokens : provider.body.max_tokens;
      const reference = preview.local_references[0];
      if (
        !validateAiPrompt(prompt) ||
        provider.provider !== request.provider ||
        provider.body.model !== request.model ||
        cap !== request.max_output_tokens ||
        (prompt as AiPrompt).question !== request.question ||
        (prompt as AiPrompt).sources.length !== 1 ||
        (prompt as AiPrompt).sources[0].source_id !== 'S1' ||
        (prompt as AiPrompt).sources[0].text !== expectedText ||
        reference.id !== captured.id ||
        reference.start !== captured.start ||
        reference.end !== captured.end
      )
        throw { code: 'INVALID_RESPONSE' };
      this.expiresAt.set(started + preview.expires_in_seconds * 1000);
      this.clock.set(performance.now());
      this.preview.set(preview);
    });
  }

  private async checkedDiscard(previewId: string, requestId: string): Promise<void> {
    const result: unknown = await this.invoke('ai_discard', { requestId, previewId });
    if (!validateAiDiscardResult(result)) throw { code: 'INVALID_RESPONSE' };
  }
  async discard(): Promise<void> {
    const preview = this.preview();
    if (!preview) return;
    await this.run(async (requestId) => {
      await this.checkedDiscard(preview.preview_id, requestId);
      this.forget();
    });
  }
  async cancel(): Promise<void> {
    if (!this.active || this.cancelling()) return;
    this.cancelling.set(true);
    try {
      const accepted: unknown = await this.invoke('ai_cancel', { requestId: this.active });
      if (typeof accepted !== 'boolean') throw { code: 'INVALID_RESPONSE' };
      // A true acknowledgement is not completion: keep BUSY until the
      // original request confirms cleanup and refreshes vault status.
    } catch {
      this.error.set(
        'Cancellation could not be confirmed. Wait for the original request to finish.',
      );
      this.cancelling.set(false);
    }
  }
}
