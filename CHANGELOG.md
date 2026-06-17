# Changelog

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
