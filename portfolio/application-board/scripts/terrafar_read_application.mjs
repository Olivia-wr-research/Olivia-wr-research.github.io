// Read rendered official evidence in an ephemeral CI browser.
import { pathToFileURL } from 'node:url';

const address = new URL(process.argv[2]);
const allowed = {
  'www.wur.nl': /^\/en\/vacancy\/[a-z0-9-]+$/,
  'karriere.uni-frankfurt.de': /^\/gu-frankfurt\/(?:job|apply)\/\d+$/,
  'emea2.softfactors.com': /^\/job-opening\/rgum-[A-Za-z0-9]+$/,
};
const path = allowed[address.hostname];
if (address.protocol !== 'https:' || address.username || address.password || address.port ||
    address.search || !path?.test(address.pathname)) {
  throw Error('Unrecognized official application URL');
}
const { chromium } = await import(pathToFileURL(process.env.TERRAFAR_PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  executablePath: process.env.TERRAFAR_CHROME,
  headless: true,
});
const escapeHtml = (value) => value.replace(/[&<>"]/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
}[c]));

try {
  const context = await browser.newContext({ serviceWorkers: 'block', acceptDownloads: false });
  const root = {
    'www.wur.nl': 'wur.nl',
    'karriere.uni-frankfurt.de': 'uni-frankfurt.de',
    'emea2.softfactors.com': 'softfactors.com',
  }[address.hostname];
  await context.route('**/*', async (route) => {
    const request = route.request();
    const target = new URL(request.url());
    const officialHost = target.hostname === root || target.hostname.endsWith('.' + root);
    if (target.protocol !== 'https:' || !officialHost ||
        !['GET', 'HEAD', 'OPTIONS'].includes(request.method()) ||
        (request.isNavigationRequest() && (target.hostname !== address.hostname || target.pathname !== address.pathname))) {
      await route.abort();
      return;
    }
    await route.continue();
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const response = await page.goto(address.href, { waitUntil: 'domcontentloaded', timeout: 18000 });
  if (!response?.ok() || page.url() !== address.href) throw Error('Unexpected official page response');

  let scope = page.locator('body');
  let labels = [];
  if (address.hostname === 'www.wur.nl') {
    await page.getByRole('button', { name: 'Apply now', exact: true }).click();
    scope = page.getByRole('dialog');
    await scope.getByRole('heading', { name: /^Apply for / }).waitFor();
    labels = [['first_name', /^First name/], ['last_name', /^Last name/], ['email', /^E-mail address/]];
  } else if (address.hostname === 'karriere.uni-frankfurt.de') {
    scope = page.locator('main');
    await scope.getByRole('heading', { level: 1 }).first().waitFor();
    if (address.pathname.includes('/apply/')) {
      await scope.getByRole('button', { name: 'Bewerbung senden', exact: true }).waitFor();
      labels = [['first_name', /^Vorname/], ['last_name', /^Nachname/], ['email', /^E-Mail Adresse\*/]];
    } else {
      await scope.getByText('Bewerbungsfrist', { exact: true }).first().waitFor();
    }
  } else {
    await scope.getByText(/^Application for /).first().waitFor();
    labels = [['field_firstName', /^First Name/], ['field_lastName', /^Last Name/], ['email', /^Email/]];
  }

  const fields = [];
  for (const [key, name] of labels) {
    const input = scope.getByRole('textbox', { name }).first();
    await input.waitFor();
    if (await input.isEnabled() && await input.isEditable()) fields.push(key);
  }
  const text = await page.locator('body').innerText();
  if (text.length > 250000) throw Error('Rendered evidence exceeds limit');
  const links = await scope.locator('a[href]').evaluateAll((nodes) => nodes
    .filter((node) => node.getClientRects().length && node.protocol === 'https:')
    .map((node) => node.href));
  const anchors = links.map((url) => '<a href="' + escapeHtml(url) + '"></a>');
  const inputs = fields.map((field) => '<input name="' + field + '">');
  process.stdout.write('<p>' + escapeHtml(text) + '</p>' + anchors.join('') + inputs.join(''));
} finally {
  await browser.close();
}
