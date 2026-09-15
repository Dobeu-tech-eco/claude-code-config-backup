---
name: playwright-cache-pins-chromium-1228
description: This machine's playwright browser cache holds chromium build 1228, which only playwright 1.61.0 pins - installing a newer playwright fails to launch
metadata:
  type: reference
---

The local playwright browser cache (`ms-playwright/`) holds **chromium-1228**. The npm package
version must match the cached build or `browserType.launch` fails with
`Executable doesn't exist`:

| playwright | chromium |
|---|---|
| 1.60.0 | 1223 |
| **1.61.0** | **1228** ← matches the cache |
| 1.62.0 | 1234 |
| 1.63.0 | 1243 |

So install `playwright@1.61.0` for any tooling that needs a headless browser here, and do **not**
assume a repo's own pin is right — RouteReady's `e2e/package.json` pins `@playwright/test` 1.63.0,
which does not match the cache.

Verify a candidate by reading `node_modules/playwright-core/browsers.json` as a FILE (the package's
exports map blocks `require()` of that subpath), or fetch
`https://raw.githubusercontent.com/microsoft/playwright/v<X.Y.Z>/packages/playwright-core/browsers.json`.
