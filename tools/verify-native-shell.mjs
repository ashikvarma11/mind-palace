import { chromium, expect } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import net from 'node:net';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, '.tools/native/verification');
const executable = path.join(root, 'src-tauri/target/debug/mind-palace.exe');
await access(executable);
await mkdir(out, { recursive: true });
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
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`,
    WEBVIEW2_USER_DATA_FOLDER: profile,
  },
});
let browser;
let graceful = false;
try {
  const endpoint = `http://127.0.0.1:${port}`;
  const deadline = Date.now() + 30000;
  while (true) {
    if (child.exitCode !== null) throw new Error('Native shell exited before WebView initialized');
    try {
      const response = await fetch(`${endpoint}/json/version`, {
        signal: AbortSignal.timeout(1000),
      });
      if (response.ok) break;
    } catch {
      /* bounded startup wait */
    }
    if (Date.now() > deadline) throw new Error('Native WebView startup timed out');
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  browser = await chromium.connectOverCDP(endpoint, { timeout: 10000 });
  const context = browser.contexts()[0];
  let page;
  while (!page && Date.now() < deadline) {
    page = context.pages().find((candidate) => {
      try {
        return new URL(candidate.url()).hostname === 'tauri.localhost';
      } catch {
        return false;
      }
    });
    if (!page) await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!page) throw new Error('Expected packaged local WebView target missing');
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.reload();
  await expect(page.getByRole('heading', { name: 'No workspace is open yet.' })).toBeVisible();
  await expect(page.getByText('Memory service not connected', { exact: true })).toBeVisible();
  const health = await page.evaluate(() => window.__TAURI_INTERNALS__.invoke('native_health'));
  expect(health).toBe('desktop_shell_only: storage_disconnected, ai_disabled');
  const styles = await page.evaluate(() => ({
    nonce: document.querySelector('#native-style-nonce')?.nonce,
    grid: getComputedStyle(document.querySelector('.opening')).display,
  }));
  expect(styles.nonce).toMatch(/^[0-9]+$/);
  expect(styles.grid).toBe('grid');
  const forbidden = await page.evaluate(async () => {
    try {
      await window.__TAURI_INTERNALS__.invoke('read_api_key');
      return false;
    } catch {
      return true;
    }
  });
  expect(forbidden).toBe(true);
  await page.screenshot({ path: path.join(out, 'native-opening.png') });
  await page.getByRole('button', { name: 'Explore sample workspace', exact: true }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'Sessions', exact: true }).click();
  await expect(page).toHaveURL(/\/sessions$/);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'No memory workspace is open.' })).toBeVisible();
  expect(errors).toEqual([]);
  // Close only the exact process spawned by this probe through its native window.
  const closed = execFileSync(
    'powershell.exe',
    ['-NoProfile', '-Command', `(Get-Process -Id ${child.pid}).CloseMainWindow()`],
    { windowsHide: true, encoding: 'utf8' },
  ).trim();
  graceful = closed === 'True';
  if (child.exitCode === null)
    await Promise.race([
      new Promise((resolve) => child.once('exit', resolve)),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Native shutdown timed out')), 10000),
      ),
    ]);
  expect(graceful).toBe(true);
  console.log(
    JSON.stringify({
      rendered: true,
      native_health: health,
      unknown_key_command_denied: forbidden,
      route_reload: true,
      console_errors: errors,
      graceful_exit: graceful,
      screenshot: path.join(out, 'native-opening.png'),
    }),
  );
} finally {
  if (child.exitCode === null) child.kill();
  if (browser) await browser.close().catch(() => {});
}
