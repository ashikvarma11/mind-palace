// Real owned WebView -> Rust -> frozen worker; synthetic isolated data only.
import { chromium, expect } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, access } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import net from 'node:net';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, '.tools/native/verification');
const executable = path.join(root, 'src-tauri/target/debug/mind-palace.exe');
const id = randomUUID();
const errors = [];
await access(executable);
await mkdir(out, { recursive: true });
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
    stdio: 'ignore',
    env: {
      ...process.env,
      MP_NATIVE_PROBE_ID: id,
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`,
      WEBVIEW2_USER_DATA_FOLDER: profile,
    },
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
  await expect(app.page.getByRole('region', { name: 'Saved original conversation' })).toContainText(
    'Original Tamil தமிழ்',
  );

  // Hold only the synthetic vault lock to prove exit during an active request.
  const lockPath = path.join(out, `vault-${id}`, 'vault/.memory/locks/write.lock');
  lock = spawn(
    path.join(root, '.tools/probe-venv/Scripts/python.exe'),
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
    }),
  );
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
