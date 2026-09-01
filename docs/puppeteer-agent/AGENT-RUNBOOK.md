# Agent runbook

## 1. Preflight

1. Read repository instructions and identify the authorized URL/origin.
2. Resolve the exact source SHA and dirty state.
3. Install dependencies using the repository's frozen lockfile command.
4. Resolve one dedicated automation browser. Prefer Puppeteer's compatible
   Chrome for Testing; otherwise require an explicit absolute path.
5. Allocate a unique writable profile, temporary directory, and artifact root
   outside protected source paths.
6. Verify sandbox availability before starting the expensive test.
7. Record runtime identity without invoking the user's normal browser.

Fail closed when a required executable, browser version, sandbox, profile path,
or artifact directory cannot be verified. Do not convert an unavailable browser
path into a skipped PASS.

## 2. Bound each phase

Use distinct limits so diagnostics identify the stalled boundary:

| Boundary | Typical starting limit | Failure label |
| --- | ---: | --- |
| Browser launch/connect | 30 s | `BROWSER_LAUNCH_TIMEOUT` |
| Navigation | 30 s | `NAVIGATION_TIMEOUT` |
| One locator/action | 10 s | `ACTION_TIMEOUT` |
| Stable application readiness | application-specific | `READINESS_TIMEOUT` |
| Whole scenario | 60–120 s | `SCENARIO_TIMEOUT` |
| Graceful browser close | 5–10 s | `CLEANUP_TIMEOUT` |

These values are initial engineering defaults, not universal acceptance
criteria. Increase a bound only with evidence that the operation makes useful
progress. A larger timeout is not a repair for an unowned browser, dead request
interceptor, missing sandbox, modal dialog, or incorrect readiness condition.

Use observable state instead of fixed sleeps:

- a locator becomes visible/enabled;
- a response with the expected URL/status arrives;
- a page function observes an application state transition;
- a stable rendered artifact is produced;
- a bounded log/trace reports progress.

## 3. Run safely

- keep `headless: true` explicit for unattended work;
- use `devtools: false` and do not pass headful flags unless the user requests
  visible interactive debugging;
- retain Puppeteer's default arguments unless a documented contract requires a
  narrow change;
- never add `--no-sandbox` as a CI convenience fix;
- do not reuse a human profile or cookie store;
- do not send repository secrets to pages outside the authorized origin;
- bind downloads and artifacts to a known directory;
- log page errors and failed requests, but redact credentials and sensitive
  response bodies;
- cap concurrency and artifact sizes.

When the browser content is untrusted, run the agent and browser with minimal
host credentials. Chrome's sandbox protects the host from web content; it does
not make an over-privileged automation controller safe.

## 4. Capture useful failure evidence

On failure, capture bounded evidence before cleanup:

```js
await page.screenshot({path: failurePng, fullPage: true}).catch(() => undefined);
const html = await page.content().catch(() => '<unavailable>');
const url = page.url();
```

Prefer a small manifest containing runtime identity, current URL, failed phase,
error class/message, console/page errors, failed request summaries, elapsed
times, and artifact hashes. Store a DevTools trace only when it is necessary;
the default Chromium trace buffer can be large and traces may contain sensitive
page data.

## 5. Clean up by ownership

The controller owns only the browser process it launched and the unique profile
it allocated:

1. stop tracing and finish bounded artifact writes;
2. close the scenario context;
3. call `browser.close()` in `finally`;
4. wait briefly for the owned process to exit;
5. if it remains alive, terminate only that recorded PID/process group and its
   children;
6. verify no owned processes remain;
7. remove only the resolved unique temporary profile after the browser exits.

Never use a broad `taskkill /IM chrome.exe`, `pkill chrome`, or equivalent. It
can destroy user sessions and unrelated agents.

## Windows notes

- Prefer Puppeteer's Chrome for Testing cache or another dedicated automation
  binary, not the user's installed Stable Chrome.
- An apparently harmless `chrome.exe --version` probe can activate a GUI
  session instead of behaving like a console command. We observed it opening
  visible windows and leaving a Chrome process tree. Obtain the version through
  an isolated Puppeteer launch (`browser.version()`) or trusted package metadata.
- Resolve the executable as an absolute path and retain its root PID before
  doing any work. If cleanup is needed, target that exact process tree.
- Chrome sandbox errors can be Windows ACL problems on the downloaded binary;
  fix permissions or reinstall the pinned browser rather than disabling the
  sandbox.

## Linux and CI notes

- Install Chrome's shared-library and font dependencies explicitly.
- Use the regular modern headless mode unless the project deliberately tests
  `chrome-headless-shell`.
- Ubuntu AppArmor can prevent downloaded Chrome for Testing builds from using
  user namespaces and produce `No usable sandbox!`. Repair runner sandbox
  configuration or choose a policy-compatible installed Chrome. Do not conceal
  the failure with `--no-sandbox`.
- In containers, provide writable profile/config/cache/temp locations even when
  the application checkout is read-only.
- Use an init process in containers when necessary to reap orphaned Chrome
  children.

## Common failure patterns

| Symptom | Likely cause | Correct response |
| --- | --- | --- |
| Visible windows appear | Headful launch or ordinary user Chrome selected | Stop only owned processes; switch to dedicated Chrome for Testing and explicit headless mode |
| `Could not find expected browser locally` | Cache path or install step mismatch | Verify `PUPPETEER_CACHE_DIR`; rerun frozen browser install |
| `No usable sandbox!` | Host sandbox/AppArmor configuration | Repair runner policy; keep sandbox enabled |
| Navigation never completes | Wrong `waitUntil`, long polling, modal, or blocked request | Use application readiness evidence and inspect request/page errors |
| All requests freeze | Interception handler did not continue/respond/abort every request | Make handler branches total and attach before navigation |
| CI has zombie Chrome processes | Controller died before `browser.close()` or container lacks reaper | Add outer process ownership/watchdog and init/reaping |
| Screenshot differs only in CI | Browser/font/viewport/device-scale/locale drift | Pin and record all rendering inputs |

## Completion report

Report browser-backed checks as `PASS`, `FAIL`, or `NOT RUN`. Include the exact
runtime identity and artifact locations. A launch failure, missing sandbox, or
unavailable executable is `NOT RUN`/infrastructure failure, never product PASS.
