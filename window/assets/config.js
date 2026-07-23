// Dreamberry public window configuration.
//
// The window is a static bundle mounted at art.adamsimms.xyz/dreamberry.
// It reads the live pointer that the Modal hourly cron writes to R2 —
// nothing here generates or mutates; it only observes the current frame.
//
// `base` is the R2 public custom domain (config/platform.yaml → r2.public_base_url).
// For local dev against a fixture, append ?base=<url> to the page URL, e.g.
//   .../window/?base=http://localhost:8000/current-fixture

(function () {
  const params = new URLSearchParams(window.location.search);
  const override = params.get("base");

  window.DREAMBERRY = {
    // Public R2 custom domain. Cross-origin from art.adamsimms.xyz — needs CORS
    // (GET) on the bucket for the JSON fetches; images use <img> and don't.
    base: (override || "https://dreamberry.adamsimms.xyz").replace(/\/+$/, ""),

    // Keys under the bucket (flat `current/` prefix — see storage.py).
    statusKey: "current/status.json",
    sidecarKey: "current/current.json",

    // Catch signal_lost's ~10s in/out; status.json is tiny.
    pollMs: 5000,

    // Fallbacks when status omits fade_ms (old pointer). Prefer status.fade_ms.
    // Dream→dream: hour-scale morph. Signal lost in/out: quick wake/sleep.
    crossfadeMs: 60 * 60 * 1000,
    signalFadeMs: 10 * 1000,
  };
})();
