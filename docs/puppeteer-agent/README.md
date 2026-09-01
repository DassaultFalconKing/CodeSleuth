# Puppeteer for coding agents

This directory is a practical operating guide for agents that use Puppeteer as
a browser automation dependency. It combines the upstream Puppeteer contract
with failures observed while running browser-backed CodeSleuth gates on Windows
and Ubuntu.

The default agent posture is:

1. use a version-pinned `puppeteer` package and its compatible Chrome for
   Testing binary;
2. resolve and record the exact Node, Puppeteer, and browser identities;
3. launch a new headless browser with a unique writable profile;
4. bound launch, navigation, action, and whole-task time independently;
5. keep the Chrome sandbox enabled;
6. write screenshots, PDFs, traces, and temporary profiles only to an explicit
   task artifact directory;
7. close the browser in `finally` and terminate only the process tree owned by
   the task if graceful cleanup fails;
8. never attach to or launch the user's everyday browser/profile unless the
   user explicitly requests interactive browser control.

## Contents

- [Configuration](CONFIGURATION.md) — package choice, browser pinning,
  configuration files, environment variables, and a safe launch template.
- [Capabilities](CAPABILITIES.md) — what Puppeteer can automate and where its
  authority stops.
- [Agent runbook](AGENT-RUNBOOK.md) — preflight, execution, evidence, cleanup,
  and troubleshooting on Windows, Linux, and CI.
- [CodeSleuth integration](CODESLEUTH-INTEGRATION.md) — the repository's
  isolated Mermaid QA path and the lessons it demonstrates.

## Upstream references

- [Puppeteer configuration](https://pptr.dev/guides/configuration)
- [Launch options](https://pptr.dev/api/puppeteer.launchoptions)
- [Browser management and contexts](https://pptr.dev/guides/browser-management)
- [Page interactions and locators](https://pptr.dev/guides/page-interactions)
- [Puppeteer troubleshooting](https://pptr.dev/troubleshooting)
- [Chrome for Testing](https://developer.chrome.com/docs/automation-and-testing)

These references are versioned external contracts. Recheck them when upgrading
Puppeteer or Chrome rather than assuming an old launch recipe is still valid.
