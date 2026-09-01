# Configuration

## Choose the package deliberately

Use `puppeteer` when the project wants Puppeteer to install and select its
compatible Chrome for Testing binary. Use `puppeteer-core` when the host owns
browser installation and the application always supplies `executablePath` or
`channel` itself.

Puppeteer configuration files and `PUPPETEER_*` environment variables do not
configure `puppeteer-core`. An agent must not assume that moving from
`puppeteer` to `puppeteer-core` preserves installation or launch behavior.

Pin the package through the repository lockfile. For release or visual gates,
also bind the resolved browser version. Chrome for Testing exists specifically
to provide versioned automation binaries without using a user's auto-updating
browser installation.

## Installation-time configuration

A repository-owned `puppeteer.config.cjs` is easier to audit than ambient host
state:

```js
const {join} = require('node:path');

/** @type {import('puppeteer').Configuration} */
module.exports = {
  cacheDirectory: join(__dirname, '.cache', 'puppeteer'),
  temporaryDirectory: join(__dirname, '.tmp', 'puppeteer'),
  chrome: {
    skipDownload: false,
    // Pin this when the project requires a literal browser identity.
    // version: 'MAJOR.MINOR.BUILD.PATCH',
  },
};
```

Relevant upstream settings include:

| Purpose | Configuration | Environment override |
| --- | --- | --- |
| Browser cache | `cacheDirectory` | `PUPPETEER_CACHE_DIR` |
| Temporary files | `temporaryDirectory` | `PUPPETEER_TMP_DIR` |
| Explicit executable | `executablePath` | `PUPPETEER_EXECUTABLE_PATH` |
| Skip all downloads | `skipDownload` | `PUPPETEER_SKIP_DOWNLOAD` |
| Chrome version | `chrome.version` | `PUPPETEER_CHROME_VERSION` |
| Skip Chrome download | `chrome.skipDownload` | `PUPPETEER_CHROME_SKIP_DOWNLOAD` |

After changing a download-related setting, rerun the browser installation step,
for example `npx puppeteer browsers install` or
`bun x puppeteer browsers install`. A configuration edit alone does not
retroactively populate the cache.

Do not commit browser caches, user profiles, cookies, or downloaded artifacts.
Cache reuse is an optimization; the lockfile plus verified runtime identity is
the test contract.

## Safe runtime launch template

```js
import {mkdtemp, mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import puppeteer from 'puppeteer';

const artifacts = resolve(process.env.AGENT_ARTIFACT_DIR ?? 'artifacts/browser');
await mkdir(artifacts, {recursive: true});
const userDataDir = await mkdtemp(join(tmpdir(), 'agent-puppeteer-'));

const launchAbort = new AbortController();
const launchTimer = setTimeout(() => launchAbort.abort(), 30_000);
let browser;

try {
  browser = await puppeteer.launch({
    headless: true,
    // Prefer Puppeteer's compatible Chrome for Testing. If the host owns the
    // browser, require an audited absolute path instead of searching PATH.
    executablePath: process.env.AGENT_CHROME_PATH || undefined,
    userDataDir,
    signal: launchAbort.signal,
    timeout: 30_000,
    args: [
      '--disable-background-networking',
      '--disable-component-update',
      '--disable-domain-reliability',
      '--no-first-run',
    ],
  });
  clearTimeout(launchTimer);

  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  page.setDefaultTimeout(10_000);
  page.setDefaultNavigationTimeout(30_000);
  await page.setViewport({width: 1440, height: 900, deviceScaleFactor: 1});

  await page.goto('http://127.0.0.1:3000', {
    waitUntil: 'domcontentloaded',
    timeout: 30_000,
  });
  await page.screenshot({path: join(artifacts, 'page.png'), fullPage: true});
  await context.close();
} finally {
  clearTimeout(launchTimer);
  await browser?.close().catch(() => undefined);
}
```

Production code should also remove the unique profile after confirming that the
owned browser process has exited. Preserve it only when it is an explicitly
requested diagnostic artifact, because it can contain sensitive site state.

## Identity to record

Before making a browser-backed PASS claim, record at least:

- exact application/repository SHA;
- Node version and resolved executable path;
- Puppeteer package and lockfile-resolved version;
- browser type, resolved executable path, and `await browser.version()` result;
- headless mode, viewport, locale/timezone if material, and sandbox status;
- profile/context isolation method;
- network policy;
- command, exit code, elapsed time, and artifact hashes.

Do not probe a normal Windows user `chrome.exe` by launching it with
`--version`. In our testing that activated a real Chrome for Testing/user-style
session and left multiple visible processes. Resolve a dedicated automation
binary first, launch it headlessly with a unique profile, then obtain browser
identity through Puppeteer.
