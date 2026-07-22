// Dreamberry live window — observes R2 pointer; drawer for provenance.
// Hold / signal_lost: DREAMBERRY.md §7. No toast — transition only.

(function () {
  "use strict";

  const CFG = window.DREAMBERRY;
  const url = (key) => `${CFG.base}/${key}`;
  const bust = (u, v) => u + (u.includes("?") ? "&" : "?") + "v=" + encodeURIComponent(v);

  const el = {
    frame: document.getElementById("frame"),
    layers: [document.getElementById("layerA"), document.getElementById("layerB")],
    waiting: document.getElementById("waiting"),
    toggle: document.getElementById("toggle"),
    toggleLabel: document.getElementById("toggleLabel"),
    drawer: document.getElementById("drawer"),
    drawerBody: document.getElementById("drawerBody"),
  };

  const ALT_DREAM =
    "A generated view of Pinchard's Island under the current weather. Labeled generated — not a photograph.";
  const ALT_NOISE =
    "Signal lost — white noise. No dream was generated this hour.";

  let front = 0; // index of the currently-visible layer
  let shownKey = null; // "<current-name>@<version>" of the frame on screen
  let firstPaint = true;

  // -- fetch helpers ---------------------------------------------------------

  async function getJSON(key) {
    const resp = await fetch(bust(url(key), Date.now()), { cache: "no-store" });
    if (!resp.ok) throw new Error(`${key} → ${resp.status}`);
    return resp.json();
  }

  function imageUrlFor(status) {
    const name = status && status.current;
    if (!name) return null;
    // Dreams version by dream_id; noise has dream_id null — always use updated_at
    // so a regenerated signal_lost.webp still busts hourly.
    const version =
      status.failure_mode === "signal_lost"
        ? status.updated_at || Date.now()
        : status.dream_id || status.last_success_dream_id || status.updated_at || "0";
    return bust(url(`current/${name}`), version);
  }

  function frameKey(status) {
    if (!status.current) return null;
    if (status.failure_mode === "signal_lost") {
      return `${status.current}@${status.updated_at || "0"}`;
    }
    return `${status.current}@${status.dream_id || status.updated_at || "0"}`;
  }

  // -- crossfade -------------------------------------------------------------

  function setVisibleAlt(status) {
    const visible = el.layers[front];
    const hidden = el.layers[1 - front];
    const alt =
      status && status.failure_mode === "signal_lost" ? ALT_NOISE : ALT_DREAM;
    visible.alt = alt;
    visible.removeAttribute("aria-hidden");
    hidden.alt = "";
    hidden.setAttribute("aria-hidden", "true");
  }

  function paint(src, { instant } = {}) {
    return new Promise((resolve) => {
      const back = 1 - front;
      const incoming = el.layers[back];
      const outgoing = el.layers[front];
      const img = new Image();
      img.onload = () => {
        incoming.src = src;
        if (instant) el.frame.classList.add("no-transition");
        // next frame so the browser registers the src before the opacity flip
        requestAnimationFrame(() => {
          incoming.classList.add("visible");
          outgoing.classList.remove("visible");
          front = back;
          if (instant) {
            requestAnimationFrame(() => el.frame.classList.remove("no-transition"));
          }
          resolve(true);
        });
      };
      img.onerror = () => resolve(false);
      img.src = src;
    });
  }

  function showWaiting(on) {
    el.waiting.classList.toggle("show", !!on);
  }

  // -- drawer render ---------------------------------------------------------

  const fmt = {
    num: (v, unit, digits = 0) =>
      v === null || v === undefined || Number.isNaN(Number(v))
        ? null
        : `${Number(v).toFixed(digits)}${unit || ""}`,
    when: (iso) => {
      if (!iso) return null;
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return String(iso);
      // Cabin local time — not the viewer's browser zone (EDT ≠ NDT).
      return d.toLocaleString("en-CA", {
        year: "numeric", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit", timeZoneName: "short",
        timeZone: "America/St_Johns",
      });
    },
    wind: (deg) => {
      if (deg === null || deg === undefined) return null;
      const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
      return dirs[Math.round(Number(deg) / 22.5) % 16];
    },
  };

  function row(dt, dd, mono) {
    if (dd === null || dd === undefined || dd === "") return "";
    return `<dt>${dt}</dt><dd${mono ? ' class="mono"' : ""}>${dd}</dd>`;
  }

  function stateLine(status) {
    const fm = status.failure_mode;
    if (fm === "signal_lost") {
      return `The channel is dead — no frame was generated this hour. The window shows static until the next successful dream. <span class="badge">signal lost</span>`;
    }
    if (status.hold) {
      const reason = status.hold_reason === "season_lock"
        ? "the season could not be honoured"
        : status.hold_reason === "identity_collapse"
        ? "the view would not hold"
        : "the weather sensors went quiet";
      const since = fmt.when(status.last_success_at);
      return `Holding the last dream — ${reason}. Nothing new was generated; the frame stays until the feed returns.${since ? ` Last moved <strong>${since}</strong>.` : ""} <span class="badge">hold</span>`;
    }
    return `Dreamed from the island's weather and the remembered window — not a photograph. <span class="badge generated">generated</span>`;
  }

  function generationGroup(status, sc) {
    if (!sc) return "";
    const m = sc.models || {};
    const rows = [
      row("Labeled", '<span class="badge generated">generated</span>'),
      row("Dial", `${fmt.num(sc.dial, "", 1)} · artist`),
      row("Base model", m.base, true),
      row("LoRA", m.has_lora ? m.lora : "none (dial-0 anchor lock)", !!m.has_lora),
      row("Generated at", fmt.when(sc.generated_at)),
      row("Frame id", sc.dream_id, true),
    ].join("");
    return `<section class="group"><h2>Generation</h2><dl>${rows}</dl></section>`;
  }

  function weatherGroup(sc) {
    if (!sc || !sc.weather_packet) return "";
    const w = sc.weather_packet;
    const visKm = w.visibility != null ? Number(w.visibility) / 1000 : null;
    const rows = [
      row("Condition", window.wmoText(w.weather_code)),
      row("Temperature", fmt.num(w.temperature_2m, " °C", 1)),
      row("Wind", w.wind_speed_10m != null
        ? `${fmt.num(w.wind_speed_10m, " km/h", 0)}${fmt.wind(w.wind_direction_10m) ? " " + fmt.wind(w.wind_direction_10m) : ""}`
        : null),
      row("Cloud cover", fmt.num(w.cloud_cover, " %", 0)),
      row("Visibility", visKm != null ? fmt.num(visKm, " km", 1) : null),
      row("Precipitation", fmt.num(w.precipitation, " mm", 1)),
      row("Humidity", fmt.num(w.relative_humidity_2m, " %", 0)),
      row("Wave height", w.wave_ht_sig != null ? fmt.num(w.wave_ht_sig, " m", 2) : null),
      row("Sun elevation", fmt.num(w.solar_elevation, "°", 1)),
      row("Observed", fmt.when(w.open_meteo_hour_utc)),
    ].join("");
    return `<section class="group"><h2>Weather — the only live signal</h2><dl>${rows}</dl>
      <p class="attrib">Open-Meteo (CC-BY 4.0) at the cabin · ECCC Wesleyville (open data) · SmartAtlantic / CIOOS buoy (CC-BY 4.0).</p></section>`;
  }

  function imageGroup(status, sc) {
    if (!sc) return "";
    const vs = sc.validator_scores || {};
    const season = vs.season || {};
    const collapse = vs.collapse || {};
    const rows = [
      row("Dimensions", sc.width && sc.height ? `${sc.width} × ${sc.height}` : null),
      row("Seed", sc.seed, true),
      row("Anchor frame", sc.anchor_frame, true),
      row("Anchor", sc.anchor_source
        ? `${sc.anchor_source}${sc.anchor_distance != null ? ` · d=${fmt.num(sc.anchor_distance, "", 3)}` : ""}`
        : null),
      row("Identity (DINOv2)", vs.dino_distance != null ? fmt.num(vs.dino_distance, "", 3) : null),
      row("Horizon shift", vs.horizon_displacement != null ? fmt.num(vs.horizon_displacement, "", 3) : null),
      row("Season check", season.action ? `${season.action}` : null),
      row("Identity check", collapse.action ? `${collapse.action}` : null),
      row("Failure mode", sc.failure_mode || status.failure_mode || null),
    ].join("");
    return `<section class="group"><h2>Image</h2><dl>${rows}</dl></section>`;
  }

  function renderDrawer(status, sc) {
    const isLost = status.failure_mode === "signal_lost";
    const parts = [`<p class="state-line">${stateLine(status)}</p>`];
    // On signal_lost there is no dream on screen — show only the state + weather
    // reasons; the last dream's provenance would be misleading here.
    if (!isLost) {
      parts.push(generationGroup(status, sc), weatherGroup(sc), imageGroup(status, sc));
    } else if (status.reasons && status.reasons.length) {
      parts.push(`<section class="group"><h2>Why</h2><p class="attrib">${status.reasons.join(" · ")}</p></section>`);
    }
    parts.push(
      `<div class="drawer-foot"><span>Dreamberry · a generated window</span>` +
        `<span><a href="../info/">About &amp; attributions →</a></span></div>`
    );
    el.drawerBody.innerHTML = parts.join("");
  }

  function setStatePill(status) {
    let cls = "state-live";
    let label = "generated";
    if (status.failure_mode === "signal_lost") {
      cls = "state-lost";
      label = "signal lost";
    } else if (status.hold) {
      cls = "state-hold";
      label = "holding";
    }
    el.toggle.classList.remove("state-live", "state-hold", "state-lost");
    el.toggle.classList.add(cls);
    el.toggleLabel.textContent = label;
  }

  // -- tick ------------------------------------------------------------------

  async function tick() {
    let status;
    try {
      status = await getJSON(CFG.statusKey);
    } catch (e) {
      // Pointer unreachable — leave whatever is on screen; try again next poll.
      return;
    }

    setStatePill(status);

    const imgSrc = imageUrlFor(status);
    const key = frameKey(status);

    if (!imgSrc) {
      // Nothing has ever published (or first-ever hold): honest emptiness.
      showWaiting(true);
    } else if (status.hold) {
      // Hold: show last dream. Must also recover from a prior signal_lost noise
      // frame (shownKey is non-null but points at signal_lost.webp).
      const onDream = shownKey && shownKey.startsWith("current.webp@");
      if (!onDream || key !== shownKey) {
        const ok = await paint(imgSrc, { instant: firstPaint || !onDream });
        if (ok) {
          shownKey = key;
          firstPaint = false;
          setVisibleAlt(status);
        }
      }
      showWaiting(false);
    } else if (key !== shownKey) {
      // Published or signal_lost: move the pointer with a crossfade.
      showWaiting(false);
      const ok = await paint(imgSrc, { instant: firstPaint });
      if (ok) {
        shownKey = key;
        firstPaint = false;
        setVisibleAlt(status);
      }
    }

    // Refresh drawer provenance (sidecar is untouched on hold/lost, so this is
    // the last successful dream's record; render guards the signal_lost case).
    let sc = null;
    if (status.failure_mode !== "signal_lost") {
      try {
        sc = await getJSON(CFG.sidecarKey);
      } catch (e) {
        sc = null;
      }
    }
    renderDrawer(status, sc);
  }

  // -- drawer open/close -----------------------------------------------------

  let focusBeforeDrawer = null;

  function toggleDrawer(force) {
    const open = force === undefined ? !el.drawer.classList.contains("open") : force;
    el.drawer.classList.toggle("open", open);
    el.toggle.setAttribute("aria-expanded", String(open));
    if (open) {
      focusBeforeDrawer = document.activeElement;
      el.drawer.setAttribute("tabindex", "-1");
      el.drawer.focus({ preventScroll: true });
    } else {
      el.drawer.removeAttribute("tabindex");
      if (focusBeforeDrawer && typeof focusBeforeDrawer.focus === "function") {
        focusBeforeDrawer.focus({ preventScroll: true });
      } else {
        el.toggle.focus({ preventScroll: true });
      }
      focusBeforeDrawer = null;
    }
  }

  el.toggle.addEventListener("click", () => toggleDrawer());
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp") { toggleDrawer(true); e.preventDefault(); }
    else if (e.key === "ArrowDown" || e.key === "Escape") { toggleDrawer(false); e.preventDefault(); }
  });

  // -- boot ------------------------------------------------------------------

  el.frame.style.setProperty("--crossfade", CFG.crossfadeMs + "ms");
  tick();
  setInterval(tick, CFG.pollMs);
  // Catch up immediately when the tab is refocused near the top of the hour.
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) tick();
  });
})();
