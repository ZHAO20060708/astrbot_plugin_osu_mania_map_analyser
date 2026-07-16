# Changelog

## 0.1.9

- Detect missing Chromium shared libraries on Linux with `ldd`.
- Automatically run Playwright's official `install-deps chromium` workflow when
  a root-based AstrBot container does not include the required system packages.
- Allow the plugin to run on the official AstrBot image without a locally
  derived Playwright image.

## 0.1.8

- Synced the embedded analyser with the latest upstream Roxy and rendering fixes.
- Moved browser runtime, caches, outputs, and schema snapshots to AstrBot's
  `data/plugin_data/astrbot_plugin_osu_mania_map_analyser/` directory.
- Fixed Playwright Chromium detection for the `chrome-headless-shell` executable.
- Reused AstrBot-managed Python dependencies instead of reinstalling them into a
  private directory on every requirements change.
- Added plugin shutdown cleanup for the persistent Chromium worker and local
  static server.
- Updated plugin metadata and documentation.

## 0.1.7

- Added plugin-local dependency bootstrap so startup now installs Python
  packages into `data/runtime/site-packages` and Playwright Chromium into
  `data/runtime/ms-playwright`, avoiding repeated manual installation after
  AstrBot restarts.
- Updated startup error messages to report automatic dependency/browser install
  failures more accurately.
- Updated plugin version metadata to `0.1.7`.

## 0.1.6

- Unified the full-card body background into a single shared shell during
  bridge rendering, so Pattern / Etterna / Graph no longer repeat the same
  beatmap cover background three times.
- Updated plugin version metadata to `0.1.6`.

## 0.1.4

- Fixed Python 3.14 compatibility in the render service by removing thread-local
  `asyncio.get_event_loop()` usage during cover theme generation.
- Fixed render bridge startup failures caused by an invalid settings import
  (`applyCardBlurSetting` -> `applyCardBgBlurSetting`).
- Added cross-origin isolation headers to the local static render server to
  improve Playwright/wasm rendering stability.
- Improved render error diagnostics by forwarding page errors, console errors,
  and frontend stack information back to the Python layer.
- Synced `_conf_schema.json` with upstream `config.js` for several options and
  defaults, including `content_bar`, `sr_text`, `estimator_algorithm`,
  `enable_etterna_rainbow_bars`, and `card_blur`.
- Updated plugin version metadata to `0.1.4`.
- Adjusted the left-top SR capsule typography so the main numeric value is
  visually centered more accurately in rendered output.
