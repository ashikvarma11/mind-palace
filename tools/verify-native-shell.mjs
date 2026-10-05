// Real owned WebView -> Rust -> frozen worker; synthetic isolated data only.
import { chromium, expect } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, access, writeFile, readFile, readdir } from 'node:fs/promises';
import { randomUUID, createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import net from 'node:net';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const probePython =
  process.env.MP_PROBE_PYTHON ?? path.join(root, '.tools/probe-venv/Scripts/python.exe');
const out = path.join(root, '.tools/native/verification');
const executable = path.join(root, 'src-tauri/target/debug/mind-palace.exe');
const id = randomUUID();
const errors = [];
const codexWorkflow = process.argv.includes('--codex-workflow');
const codexHome = path.join(out, `codex-home-${id}`);
await access(executable);
await mkdir(out, { recursive: true });
if (codexWorkflow) {
  await mkdir(codexHome);
  await writeFile(
    path.join(codexHome, 'hooks.json'),
    JSON.stringify({ description: 'Existing user hook', hooks: { Stop: [{ hooks: [{ type: 'command', command: 'echo existing', timeout: 4 }] }] } }),
  );
  process.env.CODEX_HOME = codexHome;
}
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const ps = (code) =>
  execFileSync('powershell.exe', ['-NoProfile', '-Command', code], {
    windowsHide: true,
    encoding: 'utf8',
  }).trim();
const children = (pid) =>
  JSON.parse(
    ps(
      `ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter "ParentProcessId = ${pid}" | Where-Object Name -eq 'mind-palace-memory-worker.exe' | Select-Object -ExpandProperty ProcessId)`,
    ),
  );

async function runHook(executable, args, cwd, event) {
  const child = spawn(executable, args, {
    cwd,
    windowsHide: true,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  let output = '';
  child.stdout.on('data', (chunk) => {
    output += chunk.toString();
  });
  // Receiver emits only bounded redacted status. Drain stderr, don't log content.
  child.stderr.resume();
  child.stdin.end(JSON.stringify(event));
  let timer;
  try {
    const status = await Promise.race([
      new Promise((resolve, reject) => {
        child.once('error', reject);
        child.once('exit', resolve);
      }),
      new Promise((_, reject) => {
        timer = setTimeout(
          () => reject(new Error('Synthetic hook timed out at 30 seconds')),
          30000,
        );
      }),
    ]);
    expect(status).toBe(0);
    expect(output).toBe('');
  } finally {
    clearTimeout(timer);
    if (child.exitCode === null) child.kill();
  }
}

async function docsScreenshot(page, name) {
  if (!process.argv.includes('--docs-screenshots')) return;
  // Show the app's real missing-artwork fallback. Do not publish the temporary
  // supplied logo, whose redistribution provenance is unresolved.
  if (await page.locator('.brand img').count()) {
    await page.locator('.brand img').evaluate((image) => image.dispatchEvent(new Event('error')));
  }
  await expect(page.locator('.brand-fallback')).toHaveText('MP');
  const target = path.join(out, `docs-${name}.png`);
  if (name === 'setup') {
    // The checklist contains no local source paths or user names.
    await page.getByRole('region', { name: 'Codex setup checklist' }).screenshot({ path: target });
  } else {
    await page.screenshot({ path: target, fullPage: true });
  }
}

async function launch() {
  const profile = await mkdtemp(path.join(out, 'webview-'));
  const probe = net.createServer();
  await new Promise((resolve, reject) => {
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', resolve);
  });
  const port = probe.address().port;
  await new Promise((resolve) => probe.close(resolve));
  const child = spawn(executable, [], {
    cwd: root,
    windowsHide: true,
    stdio: ['ignore', 'ignore', 'pipe'],
    env: {
      ...process.env,
      MP_NATIVE_PROBE_ID: id,
      MP_CAPTURE_TIMING: process.argv.includes('--trace-commands') ? '1' : '0',
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`,
      WEBVIEW2_USER_DATA_FOLDER: profile,
    },
  });
  child.stderr.on('data', (chunk) => {
    if (!process.argv.includes('--trace-commands')) return;
    for (const line of chunk.toString().split(/\r?\n/)) {
      if (/^MP_CAPTURE_STAGE [a-z_]+ [0-9]+$/.test(line)) console.log(line);
    }
  });
  let browser;
  try {
    const endpoint = `http://127.0.0.1:${port}`;
    const deadline = Date.now() + 30000;
    while (true) {
      if (child.exitCode !== null) throw new Error('Native app exited before WebView initialized');
      try {
        if ((await fetch(`${endpoint}/json/version`, { signal: AbortSignal.timeout(1000) })).ok)
          break;
      } catch {
        /* bounded polling */
      }
      if (Date.now() > deadline) throw new Error('Native startup timed out');
      await delay(200);
    }
    browser = await chromium.connectOverCDP(endpoint, { timeout: 10000 });
    let page;
    while (!page && Date.now() < deadline) {
      page = browser
        .contexts()[0]
        .pages()
        .find((candidate) => {
          try {
            return new URL(candidate.url()).hostname === 'tauri.localhost';
          } catch {
            return false;
          }
        });
      if (!page) await delay(100);
    }
    if (!page) throw new Error('Owned local WebView target missing');
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    await page.reload();
    try {
      await expect(page.getByRole('heading', { name: 'No workspace is open yet.' })).toBeVisible();
    } catch (error) {
      await page.screenshot({ path: path.join(out, 'native-failure.png') });
      console.log(JSON.stringify({ errors, body: await page.locator('body').innerText() }));
      throw error;
    }
    return { child, browser, page };
  } catch (error) {
    child.kill();
    if (browser) await browser.close().catch(() => {});
    throw error;
  }
}

async function close(app) {
  const workers = children(app.child.pid);
  expect(ps(`(Get-Process -Id ${app.child.pid}).CloseMainWindow()`)).toBe('True');
  if (app.child.exitCode === null)
    await Promise.race([
      new Promise((resolve) => app.child.once('exit', resolve)),
      delay(10000).then(() => {
        throw new Error('Native shutdown timed out');
      }),
    ]);
  for (const worker of workers) {
    expect(
      ps(
        `if (Get-Process -Id ${worker} -ErrorAction SilentlyContinue) { 'alive' } else { 'stopped' }`,
      ),
    ).toBe('stopped');
  }
  await app.browser.close().catch(() => {});
  return workers.length;
}

let app;
let lock;
try {
  app = await launch();
  const { page } = app;
  if (process.argv.includes('--codex-client-probe')) {
    const argument = process.argv[process.argv.indexOf('--codex-client-probe') + 1];
    if (!argument) throw new Error('An isolated installed-client probe folder is required');
    const clientRoot = path.resolve(argument);
    const relative = path.relative(path.join(root, '.tools/codex-hook-probe'), clientRoot);
    if (!relative || relative.startsWith('..') || path.isAbsolute(relative))
      throw new Error('Only this worktree synthetic client probes are allowed');
    const report = JSON.parse(await readFile(path.join(clientRoot, 'report.json'), 'utf8'));
    expect(report.fixture_not_ai).toBe(true);
    expect(report.exact_rollout).toBe(true);
    if (report.normal_persisted_trust_verified !== true)
      expect(report.first_client_seconds).toBeGreaterThanOrEqual(120);
    const originalRoot = path.join(clientRoot, 'codex-home/sessions');
    const rollouts = (await readdir(originalRoot, { recursive: true })).filter((name) =>
      name.endsWith(report.session_id ? `${report.session_id}.jsonl` : '.jsonl'));
    expect(rollouts).toHaveLength(1);
    const raw = await readFile(path.join(originalRoot, rollouts[0]), 'utf8');
    const sessionId = JSON.parse(raw.split('\n')[0]).payload.id;
    const source = path.join(out, `codex-source-${id}`);
    await mkdir(source);
    const transcript = path.join(source, 'synthetic.jsonl');
    await writeFile(transcript, raw);
    await page.getByRole('button', { name: 'Create local vault', exact: true }).click();
    await expect(page.getByText('Local vault connected · AI off', { exact: true })).toBeVisible({ timeout: 35000 });
    const configured = await page.evaluate(async (sourceRoot) => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      const status = await invoke('capture_status');
      const client = status.clients.find((entry) => entry.provider === 'codex');
      return invoke('capture_configure', { input: { provider: 'codex', source_root: sourceRoot,
        memory_roots: [], enabled: true, memory_enabled: false, revision: client.revision } });
    }, source);
    const snippet = JSON.parse(configured.clients.find((entry) => entry.provider === 'codex').snippet);
    const handler = snippet.hooks.Stop[0].hooks[0].command.split(' ');
    await close(app);
    app = null;
    await runHook(handler[0], handler.slice(1), source, { session_id: sessionId, hook_event_name: 'Stop', transcript_path: transcript });
    app = await launch();
    await app.page.getByRole('button', { name: 'Open existing vault', exact: true }).click();
    await expect(app.page.getByRole('button', { name: `Codex session ${sessionId}`, exact: true })).toBeEnabled({ timeout: 35000 });
    const stored = await app.page.evaluate(async () => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      const list = await invoke('sessions_list', { limit: 50, offset: 0 });
      const record = await invoke('sessions_read', { id: list.items[0].id });
      return { total: list.total, source: record.source_text };
    });
    expect(stored.total).toBe(1);
    expect(stored.source).toBe(raw);
    await app.page.getByRole('navigation').getByRole('link', { name: 'Ask memory', exact: true }).click();
    await app.page.getByLabel('Question', { exact: true }).fill(report.normal_persisted_trust_verified === true
      ? 'SQLite local vault' : 'Which database stores the local vault?');
    await app.page.getByRole('button', { name: 'Ask Mind Palace', exact: true }).click();
    await expect(app.page.getByText('Answer from stored evidence')).toBeVisible({ timeout: 35000 });
    await expect(app.page.locator('.answer')).toContainText('SQLite');
    await expect(app.page.locator('blockquote')).toContainText('SQLite');
    expect(errors).toEqual([]);
    await close(app);
    app = null;
    console.log(JSON.stringify({ installed_client_native: true, live_seconds: report.first_client_seconds,
      normal_persisted_trust: report.normal_persisted_trust_verified === true,
      app_closed_capture: true, restart_auto_import: true, exact_source: true, one_session: true,
      source_bytes: Buffer.byteLength(raw), ask_ui_evidence: true, console_errors: errors, isolated_vault: id }));
  } else if (process.argv.includes('--full-size-only')) {
    const source = path.join(out, `codex-source-${id}`);
    await mkdir(source);
    const invoke = (command, args = {}) => app.page.evaluate(async ({ command, args }) => {
      try { return { ok: true, value: await window.__TAURI_INTERNALS__.invoke(command, args) }; }
      catch (error) { return { ok: false, command, safe_error_code: error?.code ?? 'UNKNOWN' }; }
    }, { command, args }).then((response) => {
      if (!response.ok) throw new Error(JSON.stringify(response));
      return response.value;
    });
    await invoke('vault_open', { create: true });
    const status = await invoke('capture_status');
    const client = status.clients.find((entry) => entry.provider === 'codex');
    const configured = await invoke('capture_configure', { input: { provider: 'codex', source_root: source,
      memory_roots: [], enabled: true, memory_enabled: false, revision: client.revision } });
    const handler = JSON.parse(configured.clients.find((entry) => entry.provider === 'codex').snippet).hooks.Stop[0].hooks[0].command.split(' ');
    const sessionId = 'codex-full-size-synthetic';
    const header = JSON.stringify({ type: 'session_meta', payload: { id: sessionId } }) + '\n';
    const prefix = '{"type":"synthetic","text":"';
    const suffix = '"}\n';
    const lineSize = 65536;
    const targetSize = 20 * 1024 * 1024;
    const count = Math.floor((targetSize - header.length) / lineSize);
    const remaining = targetSize - header.length - count * lineSize;
    const raw = header + (prefix + 'x'.repeat(lineSize - prefix.length - suffix.length) + suffix).repeat(count)
      + prefix + 'y'.repeat(remaining - prefix.length - suffix.length) + suffix;
    expect(Buffer.byteLength(raw)).toBe(targetSize);
    const transcript = path.join(source, 'full-size.jsonl');
    await writeFile(transcript, raw);
    await runHook(handler[0], handler.slice(1), source, { session_id: sessionId, hook_event_name: 'Stop', transcript_path: transcript });
    await invoke('capture_index');
    const imported = await invoke('capture_import', { offset: 0 });
    expect(imported.created).toBe(1);
    const list = await invoke('sessions_list', { limit: 50, offset: 0 });
    expect(list.total).toBe(1);
    const stored = await invoke('sessions_read', { id: list.items[0].id });
    expect(Buffer.byteLength(stored.source_text)).toBe(targetSize);
    expect(createHash('sha256').update(stored.source_text).digest('hex')).toBe(createHash('sha256').update(raw).digest('hex'));
    expect(errors).toEqual([]);
    await close(app);
    app = null;
    console.log(JSON.stringify({ full_size_only: true, exact_20_mib_native: true, isolated_vault: id }));
  } else if (process.argv.includes('--diagnose-vault')) {
    const source = path.join(out, `codex-source-${id}`);
    await mkdir(source);
    const measured = async (command, args = {}) => {
      const started = performance.now();
      try {
        const response = await app.page.evaluate(async ({ command, args }) => {
          try { return { ok: true, value: await window.__TAURI_INTERNALS__.invoke(command, args) }; }
          catch (error) { return { ok: false, code: error?.code ?? 'UNKNOWN' }; }
        }, { command, args });
        if (!response.ok) {
          console.log(JSON.stringify({ command, safe_error_code: response.code }));
          throw new Error('Native diagnostic failed: ' + response.code);
        }
        const result = response.value;
        console.log(JSON.stringify({ command, milliseconds: Math.round(performance.now() - started), passed: true }));
        return result;
      } catch (error) {
        console.log(JSON.stringify({ command, milliseconds: Math.round(performance.now() - started), passed: false }));
        throw error;
      }
    };
    await measured('vault_open', { create: true });
    const concurrentStatus = await app.page.evaluate(async () => Promise.allSettled([
      window.__TAURI_INTERNALS__.invoke('capture_status'),
      window.__TAURI_INTERNALS__.invoke('capture_status'),
    ]));
    console.log(JSON.stringify({ concurrent_capture_status: concurrentStatus.map((entry) =>
      entry.status === 'fulfilled' ? { passed: true } : { passed: false, error: entry.reason }) }));
    expect(concurrentStatus.every((entry) => entry.status === 'fulfilled')).toBe(true);
    const status = await measured('capture_status');
    const scope = status.clients.find((item) => item.provider === 'codex');
    const configured = await measured('capture_configure', { input: { provider: 'codex', source_root: source,
      memory_roots: [], enabled: true, memory_enabled: false, revision: scope.revision } });
    const raw = JSON.stringify({ type: 'session_meta', payload: { id: 'diagnostic-synthetic', timestamp: '2026-10-04T00:00:00Z' } }) + '\n';
    const transcript = path.join(source, 'diagnostic.jsonl');
    await writeFile(transcript, raw);
    const snippet = JSON.parse(configured.clients.find((item) => item.provider === 'codex').snippet);
    const handler = snippet.hooks.Stop[0].hooks[0].command.split(' ');
    await runHook(handler[0], handler.slice(1), source, { session_id: 'diagnostic-synthetic', hook_event_name: 'Stop', transcript_path: transcript });
    await measured('capture_index');
    await measured('capture_import', { offset: 0 });
    await measured('capture_cleanup');
    await measured('sessions_list', { limit: 50, offset: 0 });
    const history = await measured('capture_history_preview');
    expect(history.sessions).toBe(1);
    await measured('capture_history_import', { previewId: history.preview_id, offset: 0 });
    await close(app);
    app = await launch();
    await measured('vault_open', { create: false });
    await measured('sessions_list', { limit: 50, offset: 0 });
    await measured('capture_status');
    await measured('capture_index');
    await measured('capture_import', { offset: 0 });
    await measured('capture_cleanup');
    await measured('sessions_list', { limit: 50, offset: 0 });
    await close(app);
    app = null;
  } else if (codexWorkflow) {
    const source = path.join(out, `codex-source-${id}`);
    await mkdir(source);
    const captureProbe = await page.evaluate(async () => {
      try { return { ok: await window.__TAURI_INTERNALS__.invoke('capture_status') }; }
      catch (error) { return { error }; }
    });
    console.log(JSON.stringify({ capture_probe: captureProbe }));
    if (captureProbe.error) throw new Error('Native capture status failed');
    await page.getByRole('navigation').getByRole('link', { name: 'Connections', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Codex setup checklist' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sync Codex to vault', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Create local vault', exact: true }).click();
    await expect(page.getByText('Local vault connected · AI off', { exact: true })).toBeVisible({ timeout: 35000 });
    await page.getByRole('navigation').getByRole('link', { name: 'Connections', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Bring your coding sessions home.' })).toBeVisible();
    await expect(page.getByLabel('Coding client', { exact: true })).toBeVisible({ timeout: 35000 }).catch(async (error) => {
      await page.screenshot({ path: path.join(out, 'codex-workflow-failure.png'), fullPage: true });
      console.log(JSON.stringify({ errors, body: await page.locator('body').innerText() }));
      throw error;
    });
    await page.getByLabel('Coding client', { exact: true }).selectOption('codex');
    await page.getByLabel('Absolute transcript folder', { exact: true }).fill(source);
    await page.getByRole('checkbox', { name: /^Allow hooks/ }).check();
    await page.getByRole('button', { name: 'Save capture scope', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Install Codex hook', exact: true })).toBeEnabled({ timeout: 35000 });
    await page.getByRole('button', { name: 'Install Codex hook', exact: true }).click();
    await expect(page.getByText(/Codex hook file: Installed/)).toBeVisible({ timeout: 35000 });
    await expect(page.getByRole('region', { name: 'Codex setup checklist' })).toContainText('Runtime approval is not checked here.');
    await docsScreenshot(page, 'setup');
    await page.screenshot({ path: path.join(out, 'codex-setup.png'), fullPage: true });
    const initialViewport = page.viewportSize();
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(out, 'codex-setup-narrow.png'), fullPage: true });
    await page.setViewportSize(initialViewport ?? { width: 1280, height: 1000 });
    const hooks = JSON.parse(await readFile(path.join(codexHome, 'hooks.json'), 'utf8'));
    expect(hooks.description).toBe('Existing user hook');
    expect(hooks.hooks.Stop).toHaveLength(2);
    const handler = hooks.hooks.Stop[1].hooks[0].command.split(' ');
    const transcript = path.join(source, 'synthetic.jsonl');
    let raw = JSON.stringify({ type: 'session_meta', payload: { id: 'codex-workflow-synthetic', timestamp: '2026-10-04T00:00:00Z' } }) + '\n' +
      JSON.stringify({ type: 'response_item', payload: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'The local database choice was SQLite for the vault.' }] } }) + '\n';
    await writeFile(transcript, raw);
    await close(app);
    app = null;
    await runHook(handler[0], handler.slice(1), source, {
      session_id: 'codex-workflow-synthetic', hook_event_name: 'Stop', transcript_path: transcript,
    });
    raw += JSON.stringify({ type: 'response_item', payload: { type: 'message', role: 'assistant', content: [{ type: 'output_text', text: 'Final record after the last delivered hook.' }] } }) + '\n';
    await writeFile(transcript, raw);
    await writeFile(path.join(source, 'history.jsonl'), JSON.stringify({ type: 'session_meta', payload: { id: 'codex-history-synthetic', timestamp: '2026-10-03T00:00:00Z' } }) + '\n' +
      JSON.stringify({ type: 'response_item', payload: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'Synthetic historical session for explicit import.' }] } }) + '\n');
    app = await launch();
    await app.page.getByRole('button', { name: 'Open existing vault', exact: true }).click();
    await expect(app.page.getByRole('button', { name: 'Codex session codex-workflow-synthetic', exact: true })).toBeEnabled({ timeout: 35000 });
    const result = await app.page.evaluate(async () => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      const list = await invoke('sessions_list', { limit: 50, offset: 0 });
      const record = await invoke('sessions_read', { id: list.items[0].id });
      return { total: list.total, source: record.source_text, provider: record.metadata.provider };
    });
    expect(result).toEqual({ total: 1, source: raw, provider: 'codex' });
    raw += JSON.stringify({ type: 'response_item', payload: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'The local vault database is SQLite and its codename is CopperKite.' }] } }) + '\n';
    await writeFile(transcript, raw);
    await runHook(handler[0], handler.slice(1), source, { session_id: 'codex-workflow-synthetic', hook_event_name: 'Stop', transcript_path: transcript });
    await app.page.getByRole('navigation').getByRole('link', { name: 'Ask memory', exact: true }).click();
    await app.page.getByLabel('Question', { exact: true }).fill('Which codename did we choose for the local vault?');
    await app.page.getByRole('button', { name: 'Ask Mind Palace', exact: true }).click();
    await expect(app.page.getByText('Answer from stored evidence')).toBeVisible({ timeout: 35000 });
    await expect(app.page.locator('.answer')).toContainText('SQLite');
    await expect(app.page.locator('.answer')).toContainText('CopperKite');
    await expect(app.page.locator('blockquote')).toContainText('SQLite');
    await docsScreenshot(app.page, 'ask');
    await app.page.screenshot({ path: path.join(out, 'codex-ask.png'), fullPage: true });
    await app.page.screenshot({ path: path.join(out, 'codex-ask.png'), fullPage: true });
    // Damage only this test's consent file, then restore its exact bytes.
    // The real frozen controller must reject it; the open vault stays usable.
    const testConsent = path.join(out, `capture-${id}`, 'settings/codex.json');
    const consentBytes = await readFile(testConsent);
    try {
      const invalidConsent = { ...JSON.parse(consentBytes.toString('utf8')), unexpected_field: true };
      await writeFile(testConsent, JSON.stringify(invalidConsent));
      await app.page.getByRole('button', { name: 'Ask Mind Palace', exact: true }).click();
      await expect(app.page.getByText(/New captures could not be synced/)).toBeVisible({ timeout: 35000 });
      await expect(app.page.getByText('Answer from stored evidence')).toBeVisible({ timeout: 35000 });
      await expect(app.page.locator('.answer')).toContainText('CopperKite');
    } finally {
      await writeFile(testConsent, consentBytes);
    }
    await app.page.getByRole('button', { name: 'Open stored session', exact: true }).click();
    await expect(app.page.getByRole('region', { name: 'Saved original conversation', exact: true })).toContainText('Final record after the last delivered hook.');
    await app.page.getByLabel('Find a stored session', { exact: true }).fill('no-matching-title');
    await expect(app.page.getByText('No loaded titles match. Clear the filter or load more sessions.')).toBeVisible();
    await app.page.getByLabel('Find a stored session', { exact: true }).fill('');
    if (process.argv.includes('--docs-screenshots')) {
      await app.page.getByRole('button', { name: 'Refresh conversations', exact: true }).click();
      await expect(app.page.getByText('No new captured revisions were imported. This does not verify hook delivery.', { exact: true })).toBeVisible({ timeout: 35000 });
      await expect(app.page.getByText('Working locally…', { exact: true })).toBeHidden();
    }
    await docsScreenshot(app.page, 'library');
    await app.page.screenshot({ path: path.join(out, 'codex-library.png'), fullPage: true });
    await app.page.getByRole('navigation').getByRole('link', { name: 'Connections', exact: true }).click();
    await expect(app.page.getByRole('button', { name: 'Review Codex history import', exact: true })).toBeEnabled({ timeout: 35000 });
    await app.page.getByRole('button', { name: 'Sync Codex to vault', exact: true }).click();
    await expect(app.page.getByRole('button', { name: 'Review Codex history import', exact: true })).toBeEnabled({ timeout: 35000 });
    await app.page.getByRole('button', { name: 'Review Codex history import', exact: true }).click();
    await expect(app.page.getByRole('region', { name: 'Codex history import review' })).toContainText('2 sessions in 2 files', { timeout: 35000 });
    await app.page.getByRole('button', { name: 'Confirm and import Codex history', exact: true }).click();
    await expect(app.page.getByText(/2 Codex history files captured/)).toBeVisible({ timeout: 35000 });
    await expect(app.page.getByRole('button', { name: 'Clean old imported prefixes', exact: true })).toBeEnabled({ timeout: 35000 });
    expect(await app.page.evaluate(() => window.__TAURI_INTERNALS__.invoke('sessions_list', { limit: 50, offset: 0 }).then((list) => list.total))).toBe(2);
    // Exercise the advertised source bound through both frozen processes and
    // Rust, without rendering a 20 MiB source into the DOM.
    const largeId = 'codex-full-size-synthetic';
    const header = JSON.stringify({ type: 'session_meta', payload: { id: largeId } }) + '\n';
    const fillerPrefix = '{"type":"synthetic","text":"';
    const fillerSuffix = '"}\n';
    const lineSize = 65536;
    const filler = fillerPrefix + 'x'.repeat(lineSize - fillerPrefix.length - fillerSuffix.length) + fillerSuffix;
    const targetSize = 20 * 1024 * 1024;
    const lineCount = Math.floor((targetSize - header.length) / lineSize);
    const remaining = targetSize - header.length - lineCount * lineSize;
    const large = header + filler.repeat(lineCount) + fillerPrefix + 'y'.repeat(remaining - fillerPrefix.length - fillerSuffix.length) + fillerSuffix;
    expect(Buffer.byteLength(large)).toBe(targetSize);
    const largePath = path.join(source, 'full-size.jsonl');
    await writeFile(largePath, large);
    await runHook(handler[0], handler.slice(1), source, { session_id: largeId, hook_event_name: 'Stop', transcript_path: largePath });
    const fullSize = await app.page.evaluate(async (sessionId) => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      let command = 'capture_index';
      try {
        await invoke(command);
        command = 'capture_import';
        await invoke(command, { offset: 0 });
        command = 'sessions_list';
        const list = await invoke(command, { limit: 50, offset: 0 });
        const record = list.items.find((item) => item.title === 'Codex session ' + sessionId);
        if (!record) throw { code: 'FULL_SIZE_SESSION_MISSING' };
        command = 'sessions_read';
        return await invoke(command, { id: record.id });
      } catch (error) { return { failure: { command, code: error?.code ?? 'UNKNOWN' } }; }
    }, largeId);
    if (fullSize.failure) throw new Error('Full-size native check failed: ' + JSON.stringify(fullSize.failure));
    expect(Buffer.byteLength(fullSize.source_text)).toBe(targetSize);
    expect(createHash('sha256').update(fullSize.source_text).digest('hex')).toBe(createHash('sha256').update(large).digest('hex'));
    await app.page.getByRole('button', { name: 'Remove Mind Palace hook', exact: true }).click();
    await expect(app.page.getByText(/Codex hook file: Not installed/)).toBeVisible({ timeout: 35000 });
    const after = JSON.parse(await readFile(path.join(codexHome, 'hooks.json'), 'utf8'));
    expect(after.description).toBe('Existing user hook');
    expect(after.hooks.Stop).toHaveLength(1);
    await app.page.screenshot({ path: path.join(out, 'codex-workflow.png'), fullPage: true });
    await close(app);
    app = null;
    expect(errors).toEqual([]);
    console.log(JSON.stringify({ codex_workflow: true, app_closed_capture: true, automatic_import: true,
      exact_source: true, missing_tail_repaired: true, confirmed_history: true, evidence_opens_source: true, full_20_mib_native_import: true,
      ask_with_evidence: true, ask_refreshes_capture: true, ask_preserves_stored_access: true, hook_merge_and_remove: true, isolated_capture: id }));
  } else if (process.argv.includes('--capture-only')) {
    const source = path.join(out, `source-${id}`);
    const memory = path.join(out, `memory-${id}`);
    await mkdir(source);
    await mkdir(memory);
    await writeFile(path.join(memory, 'MEMORY.md'), '# Synthetic unreviewed memory\r\n');
    await page.getByRole('button', { name: 'Create local vault', exact: true }).click();
    await expect(page.getByText('Local vault connected · AI off', { exact: true })).toBeVisible({
      timeout: 35000,
    });
    await page
      .getByRole('navigation')
      .getByRole('link', { name: 'Connections', exact: true })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Bring your coding sessions home.' }),
    ).toBeVisible();
    try {
      await expect(page.getByText('Not configured · capture off')).toHaveCount(2, {
        timeout: 35000,
      });
    } catch (error) {
      await page.screenshot({ path: path.join(out, 'native-capture-failure.png'), fullPage: true });
      console.log(
        JSON.stringify({
          capture_setup_failure: true,
          errors,
          body: await page.locator('body').innerText(),
        }),
      );
      throw error;
    }
    await page.getByLabel('Coding client', { exact: true }).selectOption('codex');
    await page.getByLabel('Absolute transcript folder', { exact: true }).fill(source);
    await page
      .getByLabel('Optional memory folders, one absolute path per line', { exact: true })
      .fill(memory);
    await page.getByRole('checkbox', { name: /^Allow hooks/ }).check();
    await page.getByRole('checkbox', { name: /^Also copy Markdown/ }).check();
    await page.getByRole('button', { name: 'Save capture scope', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Pause codex', exact: true })).toBeEnabled({
      timeout: 35000,
    });
    const snippet = JSON.parse(
      await page.getByLabel('Hook JSON for codex', { exact: true }).inputValue(),
    );
    const transcript = path.join(source, 'synthetic.jsonl');
    let raw = '';
    const timings = [];
    for (const event of ['SessionStart', 'Stop', 'SessionEnd']) {
      raw += JSON.stringify({ type: 'synthetic', text: event + ' <script>inert</script>' }) + '\n';
      await writeFile(transcript, raw);
      const command = snippet.hooks[event][0].hooks[0].command.split(' ');
      const start = performance.now();
      await runHook(command[0], command.slice(1), source, {
        session_id: 'native-synthetic',
        hook_event_name: event,
        transcript_path: transcript,
      });
      timings.push({ event, milliseconds: Math.round(performance.now() - start) });
    }
    await page
      .getByRole('button', { name: 'Validate inbox and rebuild index', exact: true })
      .click();
    await expect(
      page.getByText('1 sessions · 1 memory files · 4 revisions.', { exact: true }),
    ).toBeVisible({ timeout: 35000 });
    const inbox = path.join(out, `capture-${id}`, 'inbox');
    const index = JSON.parse(await readFile(path.join(inbox, 'index.json'), 'utf8'));
    const originals = await Promise.all(
      index.entries
        .filter((item) => item.kind === 'session')
        .map((item) => readFile(path.join(inbox, item.path), 'utf8').then(JSON.parse)),
    );
    expect(originals.some((item) => item.transcript === raw)).toBe(true);
    await page.getByRole('button', { name: 'Pause codex', exact: true }).click();
    await expect(page.getByText('Capture paused', { exact: true })).toBeVisible({ timeout: 35000 });
    await expect(page.getByRole('checkbox', { name: /^Allow hooks/ })).not.toBeChecked();
    // Exercise Claude Code's distinct executable-plus-args representation through
    // the same real UI/native boundary, with memory left separately disabled.
    await page.getByLabel('Coding client', { exact: true }).selectOption('claude-code');
    await page.getByLabel('Absolute transcript folder', { exact: true }).fill(source);
    await page.getByRole('checkbox', { name: /^Allow hooks/ }).check();
    await expect(page.getByRole('checkbox', { name: /^Also copy Markdown/ })).not.toBeChecked();
    await page.getByRole('button', { name: 'Save capture scope', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Pause claude-code', exact: true })).toBeEnabled({
      timeout: 35000,
    });
    const claudeHook = JSON.parse(
      await page.getByLabel('Hook JSON for claude-code', { exact: true }).inputValue(),
    ).hooks.Stop[0].hooks[0];
    const claudeStart = performance.now();
    await runHook(claudeHook.command, claudeHook.args, source, {
      session_id: 'native-synthetic',
      hook_event_name: 'Stop',
      transcript_path: transcript,
    });
    timings.push({
      event: 'ClaudeCode Stop',
      milliseconds: Math.round(performance.now() - claudeStart),
    });
    await page
      .getByRole('button', { name: 'Validate inbox and rebuild index', exact: true })
      .click();
    await expect(
      page.getByText('2 sessions · 1 memory files · 5 revisions.', { exact: true }),
    ).toBeVisible({ timeout: 35000 });
    await page.getByRole('button', { name: 'Import captured sessions', exact: true }).click();
    await expect(
      page.getByText(/2 captured sessions imported or updated; 0 already current/),
    ).toBeVisible({ timeout: 35000 });
    await page.getByRole('navigation').getByRole('link', { name: 'Sessions', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Codex session native-synthetic', exact: true }),
    ).toBeEnabled({ timeout: 35000 });
    await expect(
      page.getByRole('button', { name: 'Claude Code session native-synthetic', exact: true }),
    ).toBeEnabled();
    await page.getByRole('button', { name: 'Codex session native-synthetic', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Saved original conversation' })).toContainText(
      'SessionEnd <script>inert</script>',
    );
    await expect(page.getByRole('region', { name: 'Saved original conversation' })).toContainText(
      'codex hook capture',
    );
    await page
      .getByRole('navigation')
      .getByRole('link', { name: 'Connections', exact: true })
      .click();
    await page.getByRole('button', { name: 'Pause claude-code', exact: true }).click();
    await expect(page.getByText('Capture paused', { exact: true })).toHaveCount(2, {
      timeout: 35000,
    });
    await page.screenshot({ path: path.join(out, 'native-capture.png'), fullPage: true });
    await close(app);
    app = await launch();
    await app.page
      .getByRole('navigation')
      .getByRole('link', { name: 'Connections', exact: true })
      .click();
    await expect(app.page.getByText('Capture paused', { exact: true })).toHaveCount(2, {
      timeout: 35000,
    });
    expect(errors).toEqual([]);
    await close(app);
    app = null;
    console.log(
      JSON.stringify({
        native_capture_setup_consent_hook_index_pause_restart: true,
        canonical_session_ingestion: true,
        hook_registration: false,
        private_content_read: false,
        timings,
        console_errors: errors,
        isolated_capture: id,
        screenshot: path.join(out, 'native-capture.png'),
      }),
    );
  } else {
    expect(await page.evaluate(() => window.__TAURI_INTERNALS__.invoke('native_health'))).toBe(
      'desktop_local_storage_available: ai_disabled',
    );
    const styles = await page.evaluate(() => ({
      nonce: document.querySelector('#native-style-nonce')?.nonce,
      grid: getComputedStyle(document.querySelector('.opening')).display,
    }));
    expect(styles.nonce).toMatch(/^[0-9]+$/);
    expect(styles.grid).toBe('grid');
    await page.getByRole('button', { name: 'Create local vault', exact: true }).click();
    await expect(page.getByText('Local vault connected · AI off', { exact: true })).toBeVisible({
      timeout: 35000,
    });
    await expect(
      page.getByRole('button', { name: 'Save conversation locally', exact: true }),
    ).toBeEnabled();
    await page.getByLabel('Conversation title').fill('Synthetic desktop conversation');
    await page
      .getByLabel('Original conversation')
      .fill('Original Tamil தமிழ்\n<script>window.injected=true</script>');
    await page.getByLabel('Your notes').fill('Manual notes, not an approved decision.');
    await page.getByRole('button', { name: 'Save conversation locally', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Saved original conversation' })).toContainText(
      'Original Tamil தமிழ்',
    );
    expect(await page.evaluate(() => window.injected)).toBeUndefined();
    await page.getByRole('button', { name: 'Close local vault', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Open existing vault', exact: true }),
    ).toBeEnabled();
    await page.getByRole('button', { name: 'Open existing vault', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Synthetic desktop conversation', exact: true }),
    ).toBeEnabled({ timeout: 35000 });
    await page.getByRole('navigation').getByRole('link', { name: 'Sessions', exact: true }).click();
    await page.reload();
    await expect(
      page.getByRole('button', { name: 'Synthetic desktop conversation', exact: true }),
    ).toBeEnabled();
    await page.getByRole('button', { name: 'Synthetic desktop conversation', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Saved original conversation' })).toContainText(
      'Manual notes',
    );
    const rejected = await page.evaluate(async () => {
      const commands = [
        ['read_api_key', {}],
        ['sessions_read', { id: '../secret' }],
        ['sessions_list', { limit: 51, offset: 0 }],
        [
          'sessions_create',
          { input: { op_id: 'bad', title: 'x', body: '', source_text: '', path: 'secret' } },
        ],
      ];
      return Promise.all(
        commands.map(async ([command, args]) => {
          try {
            await window.__TAURI_INTERNALS__.invoke(command, args);
            return false;
          } catch {
            return true;
          }
        }),
      );
    });
    expect(rejected).toEqual([true, true, true, true]);
    await page
      .getByRole('navigation')
      .getByRole('link', { name: 'Ask memory', exact: true })
      .click();
    await expect(page.getByRole('heading', { name: 'Choose what an AI would see.' })).toBeVisible();
    await page
      .getByLabel('Saved conversation', { exact: true })
      .selectOption({ label: 'Synthetic desktop conversation' });
    await page.getByRole('button', { name: 'Load original conversation', exact: true }).click();
    await expect(page.getByLabel('Original source for preview')).toContainText('Original Tamil');
    await page.getByLabel('Start character', { exact: true }).fill('0');
    await page.getByLabel('End character', { exact: true }).fill('8');
    await page.getByLabel('Model identifier', { exact: true }).fill('synthetic-model');
    await page.getByLabel('Your question', { exact: true }).fill('What is recorded here?');
    await page.getByRole('button', { name: 'Create local request preview', exact: true }).click();
    await expect(page.getByLabel('Exact provider request')).toContainText('What is recorded here?');
    await expect(
      page.getByRole('button', { name: 'Send to AI · not available yet', exact: true }),
    ).toBeDisabled();
    await page.screenshot({ path: path.join(out, 'native-ai-preview.png'), fullPage: true });
    await page.getByRole('button', { name: 'Discard preview and edit', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'No request preview yet' })).toBeVisible();
    await expect(page.getByLabel('Your question', { exact: true })).toBeEnabled();
    await page.getByRole('navigation').getByRole('link', { name: 'Sessions', exact: true }).click();
    const previewCheck = await page.evaluate(async () => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      const sessions = await invoke('sessions_list', { limit: 50, offset: 0 });
      const source = sessions.items[0].id;
      const preview = await invoke('ai_preview', {
        requestId: crypto.randomUUID(),
        input: {
          provider: 'openai',
          model: 'synthetic-model',
          question: 'What did I record?',
          max_output_tokens: 128,
          selections: [{ kind: 'session', id: source, start: 0, end: 8 }],
        },
      });
      const discarded = await invoke('ai_discard', {
        requestId: crypto.randomUUID(),
        previewId: preview.preview_id,
      });
      let sendDenied = false;
      try {
        await invoke('ai_send', {});
      } catch {
        sendDenied = true;
      }
      return {
        noSend: preview.can_send === false,
        endpoint: preview.request.endpoint,
        discarded: discarded.discarded,
        sendDenied,
      };
    });
    expect(previewCheck).toEqual({
      noSend: true,
      endpoint: 'https://api.openai.com/v1/responses',
      discarded: true,
      sendDenied: true,
    });
    await page.screenshot({ path: path.join(out, 'native-vault.png'), fullPage: true });
    expect(errors).toEqual([]);
    const idleWorkers = await close(app);
    expect(idleWorkers).toBe(1);
    app = null;

    app = await launch();
    await app.page.getByRole('button', { name: 'Open existing vault', exact: true }).click();
    await expect(
      app.page.getByRole('button', { name: 'Synthetic desktop conversation', exact: true }),
    ).toBeEnabled({ timeout: 35000 });
    await app.page
      .getByRole('button', { name: 'Synthetic desktop conversation', exact: true })
      .click();
    await expect(
      app.page.getByRole('region', { name: 'Saved original conversation' }),
    ).toContainText('Original Tamil தமிழ்');

    // Select the source through the real UI before holding the synthetic lock.
    await app.page
      .getByRole('navigation')
      .getByRole('link', { name: 'Ask memory', exact: true })
      .click();
    await app.page.getByRole('button', { name: 'Load original conversation', exact: true }).click();
    await expect(app.page.getByLabel('Original source for preview')).toContainText(
      'Original Tamil',
    );
    await app.page.getByLabel('End character', { exact: true }).fill('8');
    await app.page.getByLabel('Model identifier', { exact: true }).fill('synthetic-model');
    await app.page.getByLabel('Your question', { exact: true }).fill('Cancellation test');
    const lockPath = path.join(out, `vault-${id}`, 'vault/.memory/locks/write.lock');
    lock = spawn(
      probePython,
      [
        '-c',
        'import portalocker,sys; f=open(sys.argv[1],"a"); portalocker.lock(f,portalocker.LOCK_EX); print("ready",flush=True); sys.stdin.read()',
        lockPath,
      ],
      { windowsHide: true, stdio: ['pipe', 'pipe', 'ignore'] },
    );
    await Promise.race([
      new Promise((resolve) => lock.stdout.once('data', resolve)),
      delay(5000).then(() => {
        throw new Error('Synthetic lock setup timed out');
      }),
    ]);
    // The load effect resets the range to zero. Select the exact range only
    // after the original load and synthetic lock setup have both settled.
    await app.page.getByLabel('End character', { exact: true }).fill('8');
    await expect(app.page.getByLabel('End character', { exact: true })).toHaveValue('8');
    await app.page
      .getByRole('button', { name: 'Create local request preview', exact: true })
      .click();
    await expect(
      app.page.getByRole('button', { name: 'Cancel preview request', exact: true }),
    ).toBeVisible();
    const targeting = await app.page.evaluate(async () => {
      const invoke = window.__TAURI_INTERNALS__.invoke;
      let busy = false;
      try {
        await invoke('vault_status');
      } catch (error) {
        busy = error.code === 'BUSY';
      }
      const wrong = await invoke('ai_cancel', { requestId: crypto.randomUUID() });
      return { busy, wrong };
    });
    expect(targeting).toEqual({ busy: true, wrong: false });
    await app.page.getByRole('button', { name: 'Cancel preview request', exact: true }).click();
    await expect(app.page.getByRole('alert')).toContainText(
      'Preview cancelled. Reopen the local vault to continue.',
    );
    const cancelledStatus = await app.page.evaluate(() =>
      window.__TAURI_INTERNALS__.invoke('vault_status'),
    );
    expect(cancelledStatus.connected).toBe(false);
    const cancelCheck = {
      ...targeting,
      connected: cancelledStatus.connected,
      ui_cleanup_message: true,
    };
    lock.stdin.end();
    await new Promise((resolve) => lock.once('exit', resolve));
    lock = null;
    // The gateway refreshes connection state only after confirmed cleanup.
    await app.page
      .getByRole('navigation')
      .getByRole('link', { name: 'Welcome', exact: true })
      .click();
    await app.page.getByRole('button', { name: 'Open existing vault', exact: true }).click();
    await expect(
      app.page.getByRole('button', { name: 'Synthetic desktop conversation', exact: true }),
    ).toBeEnabled({ timeout: 35000 });
    lock = spawn(
      probePython,
      [
        '-c',
        'import portalocker,sys; f=open(sys.argv[1],"a"); portalocker.lock(f,portalocker.LOCK_EX); print("ready",flush=True); sys.stdin.read()',
        lockPath,
      ],
      { windowsHide: true, stdio: ['pipe', 'pipe', 'ignore'] },
    );
    await Promise.race([
      new Promise((resolve) => lock.stdout.once('data', resolve)),
      delay(5000).then(() => {
        throw new Error('Synthetic lock setup timed out');
      }),
    ]);
    await app.page.evaluate(() => {
      window.pendingVaultRequest = window.__TAURI_INTERNALS__
        .invoke('sessions_list', { limit: 50, offset: 0 })
        .catch(() => null);
    });
    const busy = await app.page.evaluate(async () => {
      try {
        await window.__TAURI_INTERNALS__.invoke('vault_status');
        return false;
      } catch (e) {
        return e.code === 'BUSY';
      }
    });
    expect(busy).toBe(true);
    const activeWorkers = await close(app);
    expect(activeWorkers).toBe(1);
    app = null;
    expect(errors).toEqual([]);
    console.log(
      JSON.stringify({
        create_save_read_reopen: true,
        native_restart: true,
        original_text_inert: true,
        bad_commands_denied: rejected,
        csp_nonce: true,
        console_errors: errors,
        idle_and_active_exit: true,
        owned_workers_stopped: idleWorkers + activeWorkers,
        screenshot: path.join(out, 'native-vault.png'),
        isolated_vault: id,
        offline_ai_preview: previewCheck,
        targeted_ai_cancellation: cancelCheck,
        ai_preview_ui_review_discard: true,
      }),
    );
  }
} finally {
  if (lock) {
    lock.stdin.end();
    if (lock.exitCode === null) lock.kill();
  }
  if (app) {
    if (app.child.exitCode === null) app.child.kill();
    await app.browser.close().catch(() => {});
  }
}
