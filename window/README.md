# Dreamberry public window (`window/`)

Self-contained static bundle for `art.adamsimms.xyz/dreamberry`. No build step —
copy verbatim to `dist/dreamberry/` (see [docs/M6-WINDOW.md](../docs/M6-WINDOW.md)).

```
window/
  index.html          → /dreamberry         portfolio landing
  window/index.html   → /dreamberry/window   the live piece (image + drawer)
  info/index.html     → /dreamberry/info     about + attributions
  assets/             → config, styles, weather-code map, window logic
```

The window only **observes** the R2 pointer the Modal cron writes
(`current/status.json`, `current/current.json`, `current/current.webp`); it never
generates or mutates. R2 base URL is in `assets/config.js` (override for dev with
`?base=<url>`).

Local preview:

```bash
cd window && python3 -m http.server 8080
# → http://localhost:8080/window/?base=<r2-or-fixture-base>
```

Mount on art Pages (sibling assemble, issue #20):

```bash
# from art.adamsimms.xyz after `npm run build`
npm run assemble:dreamberry
# or full: npm run build:full
```
