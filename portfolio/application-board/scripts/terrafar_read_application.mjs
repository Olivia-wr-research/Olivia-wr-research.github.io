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
let browser;
let stage = "launch";
const network = new Set();
const note = (value) => { if (network.size < 24) network.add(value); };
const escapeHtml = (value) => value.replace(/[&<>"]/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
}[c]));

try {
  const { chromium } = await import(pathToFileURL(process.env.TERRAFAR_PLAYWRIGHT_MODULE));
  browser = await chromium.launch({ executablePath: process.env.TERRAFAR_CHROME, headless: true });
  const context = await browser.newContext({ serviceWorkers: 'block', acceptDownloads: false });
  const root = {
    'www.wur.nl': 'wur.nl',
    'karriere.uni-frankfurt.de': 'uni-frankfurt.de',
    'emea2.softfactors.com': 'softfactors.com',
  }[address.hostname];
  // These vendors are referenced by the official vacancy pages' published assets.
  const vendor = {
    'www.wur.nl': 'applicant.ats-platform.com',
    'karriere.uni-frankfurt.de': 'api.career.hidden-professionals.de',
  }[address.hostname];
  await context.route('**/*', async (route) => {
    const request = route.request();
    const target = new URL(request.url());
    const vendorRead = target.hostname === vendor &&
      ['xhr', 'fetch', 'script', 'stylesheet'].includes(request.resourceType());
    const officialHost = target.hostname === root || target.hostname.endsWith('.' + root) || vendorRead;
    if (target.protocol !== 'https:' || !officialHost ||
        !['GET', 'HEAD', 'OPTIONS'].includes(request.method()) ||
        (request.isNavigationRequest() && (target.hostname !== address.hostname || target.pathname !== address.pathname))) {
      if (['xhr', 'fetch', 'script'].includes(request.resourceType()))
        note('blocked-' + request.method() + '-' + request.resourceType() + ':' + target.hostname);
      await route.abort();
      return;
    }
    await route.continue();
  });
  const page = await context.newPage();
  page.on('response', (response) => {
    if (response.status() >= 400 && ['xhr', 'fetch', 'script'].includes(response.request().resourceType()))
      note('http-' + response.status() + ':' + new URL(response.url()).hostname);
  });
  page.on('pageerror', (error) => note('page-' + error.name));
  page.setDefaultTimeout(24000);
  stage = "navigation";
  const response = await page.goto(address.href, { waitUntil: 'domcontentloaded', timeout: 18000 });
  if (!response?.ok() || page.url() !== address.href) throw Error('Unexpected official page response');

  stage = "official_content";
  let scope = page.locator('body');
  let labels = [];
  if (address.hostname === 'www.wur.nl') {
    stage = 'wur_apply_button';
    await page.getByRole('button', { name: 'Apply now', exact: true }).click();
    stage = 'wur_dialog';
    scope = page.getByRole('dialog');
    await scope.getByRole('heading', { name: /^Apply for / }).waitFor();
    labels = [['first_name', /^First name/], ['last_name', /^Last name/], ['email', /^E-mail address/]];
  } else if (address.hostname === 'karriere.uni-frankfurt.de') {
    stage = 'frankfurt_job_heading';
    scope = page.locator('main');
    await scope.getByRole('heading', { level: 1 }).first().waitFor();
    if (address.pathname.includes('/apply/')) {
      stage = 'frankfurt_submit_visible';
      await scope.getByRole('button', { name: 'Bewerbung senden', exact: true }).waitFor();
      labels = [['first_name', /^Vorname/], ['last_name', /^Nachname/], ['email', /^E-Mail Adresse\*/]];
    } else {
      stage = 'frankfurt_deadline';
      await scope.getByText('Bewerbungsfrist', { exact: true }).first().waitFor();
    }
  } else {
    stage = 'eth_form_heading';
    await scope.getByText(/^Application for /).first().waitFor();
    labels = [['field_firstName', /^First Name/], ['field_lastName', /^Last Name/], ['email', /^Email/]];
  }

  stage = "application_fields";
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
} catch (error) {
  console.error(`browser-check:${stage}:${error.name}`);
  if (network.size) console.error("browser-network:" + [...network].join(","));
  process.exitCode = 1;
} finally {
  await browser?.close();
}
