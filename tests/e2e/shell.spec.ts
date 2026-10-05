import { expect, test } from '@playwright/test';

test('sample opt-in, source inspection, review and handoff preserve approval boundaries', async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/welcome');
  await expect(page.getByText('Desktop vault unavailable in browser', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'No workspace is open yet.' })).toBeVisible();
  await page.screenshot({ path: info.outputPath('opening.png'), fullPage: true });
  await page.getByRole('button', { name: 'Explore sample workspace', exact: true }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'Sessions', exact: true }).click();
  await page.getByRole('button', { name: 'Mark summary reviewed', exact: true }).click();
  await page
    .getByRole('navigation')
    .getByRole('link', { name: /Decisions/ })
    .click();
  await expect(page.getByText('Proposed · needs review', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'See original confirmation' }).click();
  await expect(
    page.getByRole('region', { name: 'Original fictional sample messages' }),
  ).toContainText('We need its event history');
  await page.getByRole('button', { name: 'Reject', exact: true }).click();
  await page
    .getByRole('navigation')
    .getByRole('link', { name: 'Resume work', exact: true })
    .click();
  await expect(page.getByLabel('Context package', { exact: true })).toHaveValue(
    /REJECTED DURING SAMPLE REVIEW/,
  );
  await page.getByRole('navigation').getByRole('link', { name: 'Decisions', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm decision', exact: true }).click();
  await page
    .getByRole('navigation')
    .getByRole('link', { name: 'Resume work', exact: true })
    .click();
  const handoff = page.getByLabel('Context package', { exact: true });
  await expect(handoff).toHaveValue(/CONFIRMED DURING SAMPLE REVIEW/);
  await expect(handoff).not.toHaveValue(/NOT YET APPROVED/);
  await expect(handoff).toHaveValue(/Keep NgRx/);
  await page.screenshot({ path: info.outputPath('handoff.png'), fullPage: true });
  await page.getByRole('button', { name: 'Select text to copy' }).click();
  expect(
    await handoff.evaluate((node: HTMLTextAreaElement) => node.selectionEnd - node.selectionStart),
  ).toBeGreaterThan(100);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'No memory workspace is open.' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('sample answers abstain, input stays inert, and no external network is used', async ({
  page,
}, info) => {
  const external: string[] = [];
  page.on('request', (request) => {
    const url = request.url();
    if (/^https?:/.test(url) && new URL(url).hostname !== '127.0.0.1') external.push(url);
  });
  await page.goto('/welcome');
  await page.getByRole('button', { name: 'Explore sample workspace', exact: true }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'Ask memory', exact: true }).click();
  await page.getByRole('button', { name: 'Why did we keep NgRx?', exact: true }).click();
  await expect(page.getByText('Preset sample answer', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Sample user message 14', exact: true }).click();
  await expect(
    page.getByRole('region', { name: 'Original fictional sample messages' }),
  ).toBeVisible();
  await page.screenshot({ path: info.outputPath('sample-answer.png'), fullPage: true });
  await page
    .getByLabel('Question for your memory')
    .fill('<script>window.sampleInjected=true</script>');
  await page.getByRole('button', { name: 'Ask', exact: true }).click();
  await expect(page.getByText('Insufficient evidence', { exact: true })).toBeVisible();
  expect(
    await page.evaluate(() => Object.prototype.hasOwnProperty.call(window, 'sampleInjected')),
  ).toBe(false);
  await page.getByRole('button', { name: 'Exit sample', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'No memory workspace is open.' })).toBeVisible();
  expect(external).toEqual([]);
});

for (const width of [1024, 768, 390, 320]) {
  test('all routes fit a ' + width + 'px window', async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1100 });
    await page.goto('/welcome');
    await page.getByRole('button', { name: 'Explore sample workspace', exact: true }).click();
    const routes = [
      'Today',
      'Sessions',
      'Decisions',
      'Ask memory',
      'Resume work',
      'Connections',
      'Settings',
      'Welcome',
    ];
    for (const name of routes) {
      await page
        .getByRole('navigation')
        .getByRole('link', {
          name: name === 'Decisions' ? /Decisions/ : name,
          exact: name !== 'Decisions',
        })
        .click();
      const route =
        name === 'Ask memory' ? 'ask' : name === 'Resume work' ? 'resume' : name.toLowerCase();
      await page.waitForURL('**/' + route);
      await expect(page.locator('main h1')).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      );
      expect(overflow, name + ' at ' + width + 'px').toBe(false);
    }
    if (width === 320)
      await page.screenshot({ path: info.outputPath('mobile-opening.png'), fullPage: true });
  });
}

test('keyboard entry and appearance remain accessible across navigation', async ({
  page,
}, info) => {
  await page.goto('/welcome');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.getByRole('button', { name: 'Explore sample workspace', exact: true }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'Settings', exact: true }).click();
  await page.waitForURL('**/settings');
  const appearance = page.getByRole('combobox', { name: 'Appearance', exact: true });
  await expect(appearance).toBeVisible();
  await appearance.selectOption('dark');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('navigation').getByRole('link', { name: 'Today', exact: true }).click();
  await page.waitForURL('**/today');
  await page.screenshot({ path: info.outputPath('dark-today.png'), fullPage: true });
  await page.getByRole('navigation').getByRole('link', { name: 'Settings', exact: true }).click();
  await page.waitForURL('**/settings');
  await expect(page.getByRole('combobox', { name: 'Appearance', exact: true })).toHaveValue('dark');
});
