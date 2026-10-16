/* Dreamberry archive studio — Cloudberry gallery → full viewer. */
(function () {
  const INDEX_URL = "./index.json";
  // Absolute archive root (never resolve relative to /studio/).
  const ARCHIVE_ORIGIN = `${window.location.origin}/archive/`;

  const el = {
    page: document.getElementById("page"),
    navMeta: document.getElementById("navMeta"),
    track: document.getElementById("daysTrack"),
    scroll: document.getElementById("daysScroll"),
    gallery: document.getElementById("gallery"),
    viewer: document.getElementById("viewer"),
    viewerImg: document.getElementById("viewerImg"),
    viewerKicker: document.getElementById("viewerKicker"),
    viewerTitle: document.getElementById("viewerTitle"),
    viewerSub: document.getElementById("viewerSub"),
    viewerDl: document.getElementById("viewerDl"),
    viewerPng: document.getElementById("viewerPng"),
    viewerJson: document.getElementById("viewerJson"),
    prevBtn: document.getElementById("prevBtn"),
    nextBtn: document.getElementById("nextBtn"),
    brandLink: document.getElementById("brandLink"),
  };

  /** @type {object[]} */
  let flat = [];
  /** @type {Map<string, number>} */
  let byId = new Map();
  let currentIndex = -1;
  let dragSuppressUntil = 0;

  /** Encode path segments so timestamps with ":" are safe in <img src>. */
  function archiveUrl(key) {
    const rel = String(key || "").replace(/^archive\//, "");
    return (
      ARCHIVE_ORIGIN +
      rel
        .split("/")
        .map((seg) => encodeURIComponent(seg))
        .join("/")
    );
  }

  function thumbUrl(entry) {
    if (entry.thumb) return archiveUrl(entry.thumb);
    return "";
  }

  function groupByDay(entries) {
    const map = new Map();
    for (const e of entries) {
      const day = e.cabin_day || "unknown";
      if (!map.has(day)) map.set(day, []);
      map.get(day).push(e);
    }
    return [...map.entries()];
  }

  function shortDay(isoDay) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDay || "");
    if (!m) return isoDay || "";
    const months = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];
    const d = Number(m[3]);
    const mon = months[Number(m[2]) - 1] || m[2];
    const year = Number(m[1]);
    const nowY = new Date().getFullYear();
    return year === nowY ? `${d} ${mon}` : `${d} ${mon} ${String(year).slice(2)}`;
  }

  function selectedId() {
    return new URLSearchParams(window.location.search).get("id");
  }

  function setSelectedId(id, { replace = false } = {}) {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("id", id);
    else url.searchParams.delete("id");
    const state = { id };
    if (replace) history.replaceState(state, "", url);
    else history.pushState(state, "", url);
  }

  function row(dt, dd) {
    if (dd == null || dd === "") return null;
    const d = document.createElement("dt");
    d.textContent = dt;
    const v = document.createElement("dd");
    v.textContent = String(dd);
    return [d, v];
  }

  function showGallery() {
    el.page.classList.remove("is-viewer");
    el.viewer.hidden = true;
    el.gallery.hidden = false;
    el.navMeta.textContent =
      flat.length > 0 ? `${flat.length} dreams · newest first` : el.navMeta.textContent;
  }

  async function openViewer(entry) {
    const idx = byId.get(entry.dream_id);
    if (idx == null) return;
    currentIndex = idx;
    el.page.classList.add("is-viewer");
    el.gallery.hidden = true;
    el.viewer.hidden = false;

    const png = archiveUrl(entry.png);
    const jsonUrl = archiveUrl(entry.json);
    el.viewerImg.alt = `Dream ${entry.dream_id}`;
    el.viewerImg.src = png;
    el.viewerKicker.textContent = "Generated frame";
    el.viewerTitle.textContent =
      entry.cabin_feed || shortDay(entry.cabin_day) || entry.dream_id;
    el.viewerSub.textContent = [
      entry.cabin_time,
      entry.weather_summary,
      entry.failure_mode ? `failure: ${entry.failure_mode}` : null,
    ]
      .filter(Boolean)
      .join(" · ");

    el.viewerDl.replaceChildren();
    for (const [k, v] of [
      ["Dream id", entry.dream_id],
      ["Dial", entry.dial != null ? String(entry.dial) : null],
      ["Generated", entry.generated_at],
      ["Anchor", entry.anchor_frame],
      ["Weather", entry.weather_summary],
      ["Failure", entry.failure_mode],
    ]) {
      const nodes = row(k, v);
      if (nodes) el.viewerDl.append(...nodes);
    }

    try {
      const sc = await fetch(jsonUrl).then((r) => (r.ok ? r.json() : null));
      if (sc) {
        const promptShort = sc.prompt
          ? String(sc.prompt).replace(
              /^cldbry window view of Pinchard's Island, Newfoundland,?\s*/i,
              ""
            )
          : null;
        el.viewerSub.textContent = [entry.cabin_time, entry.weather_summary, promptShort]
          .filter(Boolean)
          .join(" · ");
        el.viewerDl.replaceChildren();
        for (const [k, v] of [
          ["Dream id", entry.dream_id],
          ["Dial", sc.dial != null ? String(sc.dial) : null],
          ["Generated", sc.generated_at],
          ["Anchor", sc.anchor_frame],
          ["Seed", sc.seed],
          ["Size", sc.width && sc.height ? `${sc.width} × ${sc.height}` : null],
          [
            "Identity",
            sc.validator_scores && sc.validator_scores.dino_distance != null
              ? String(sc.validator_scores.dino_distance)
              : null,
          ],
          ["Failure", sc.failure_mode],
          ["Prompt", sc.prompt],
        ]) {
          const nodes = row(k, v);
          if (nodes) el.viewerDl.append(...nodes);
        }
      }
    } catch (_) {
      /* index-only */
    }

    el.viewerPng.href = png;
    el.viewerJson.href = jsonUrl;
    el.navMeta.textContent = `${currentIndex + 1} / ${flat.length}`;
    el.prevBtn.disabled = currentIndex <= 0;
    el.nextBtn.disabled = currentIndex >= flat.length - 1;
  }

  function go(delta) {
    const next = currentIndex + delta;
    if (next < 0 || next >= flat.length) return;
    const entry = flat[next];
    setSelectedId(entry.dream_id);
    openViewer(entry);
  }

  function lazyThumbs(root) {
    const imgs = root.querySelectorAll("img[data-src]");
    if (!("IntersectionObserver" in window)) {
      imgs.forEach((img) => {
        img.src = img.dataset.src;
        img.removeAttribute("data-src");
      });
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const ent of entries) {
          if (!ent.isIntersecting) continue;
          const img = ent.target;
          const src = img.dataset.src;
          if (src) {
            img.src = src;
            img.removeAttribute("data-src");
          }
          io.unobserve(img);
        }
      },
      { root: el.scroll, rootMargin: "400px 600px", threshold: 0.01 }
    );
    imgs.forEach((img) => io.observe(img));
  }

  function renderGallery(entries) {
    el.track.replaceChildren();
    for (const [day, frames] of groupByDay(entries)) {
      const col = document.createElement("section");
      col.className = "gallery-day-column";
      col.setAttribute("aria-label", frames[0]?.cabin_feed || day);

      const label = document.createElement("div");
      label.className = "gallery-day-label";
      label.textContent = frames[0]?.cabin_feed || shortDay(day);
      label.title = day;

      const stack = document.createElement("div");
      stack.className = "gallery-day-stack";

      const ordered = [...frames].sort((a, b) =>
        String(a.cabin_time || "").localeCompare(String(b.cabin_time || ""))
      );

      for (const e of ordered) {
        const a = document.createElement("a");
        a.className = "gallery-day-photo";
        a.href = `?id=${encodeURIComponent(e.dream_id)}`;
        a.title = e.dream_id;
        a.dataset.dreamId = e.dream_id;

        const img = document.createElement("img");
        img.decoding = "async";
        img.width = 288;
        img.height = 216;
        img.alt = "";
        const src = thumbUrl(e);
        if (src) {
          img.dataset.src = src;
        } else {
          a.classList.add("is-missing-thumb");
        }
        img.addEventListener("error", () => {
          img.removeAttribute("src");
          a.classList.add("is-missing-thumb");
        });

        const t = document.createElement("span");
        t.className = "time";
        t.textContent = e.cabin_time || "";

        a.append(img, t);
        stack.append(a);
      }

      col.append(label, stack);
      el.track.append(col);
    }

    // Event delegation: one listener, survives re-renders.
    el.track.onclick = (ev) => {
      const a = ev.target.closest("a.gallery-day-photo");
      if (!a || !el.track.contains(a)) return;
      if (Date.now() < dragSuppressUntil) {
        ev.preventDefault();
        return;
      }
      const id = a.dataset.dreamId;
      const entry = id != null ? flat[byId.get(id)] : null;
      if (!entry) return;
      ev.preventDefault();
      setSelectedId(entry.dream_id);
      openViewer(entry);
    };

    lazyThumbs(el.track);
  }

  function enableDragScroll(node) {
    let down = false;
    let dragging = false;
    let startX = 0;
    let startScroll = 0;
    const THRESH = 8;

    node.addEventListener("pointerdown", (ev) => {
      if (ev.pointerType === "touch" || ev.button !== 0) return;
      down = true;
      dragging = false;
      startX = ev.clientX;
      startScroll = node.scrollLeft;
    });
    node.addEventListener("pointermove", (ev) => {
      if (!down) return;
      const dx = ev.clientX - startX;
      if (!dragging && Math.abs(dx) > THRESH) {
        dragging = true;
        node.classList.add("is-dragging");
        dragSuppressUntil = Date.now() + 400;
        try {
          node.setPointerCapture(ev.pointerId);
        } catch (_) {
          /* ignore */
        }
      }
      if (dragging) node.scrollLeft = startScroll - dx;
    });
    const end = () => {
      if (!down) return;
      down = false;
      node.classList.remove("is-dragging");
      if (dragging) dragSuppressUntil = Date.now() + 400;
      dragging = false;
    };
    node.addEventListener("pointerup", end);
    node.addEventListener("pointercancel", end);
  }

  function route() {
    const id = selectedId();
    if (id && byId.has(id)) openViewer(flat[byId.get(id)]);
    else showGallery();
  }

  async function main() {
    enableDragScroll(el.scroll);
    el.prevBtn.addEventListener("click", () => go(-1));
    el.nextBtn.addEventListener("click", () => go(1));
    el.brandLink.addEventListener("click", (ev) => {
      if (selectedId()) {
        ev.preventDefault();
        setSelectedId(null);
        showGallery();
      }
    });
    window.addEventListener("popstate", route);
    window.addEventListener("keydown", (ev) => {
      if (!el.page.classList.contains("is-viewer")) return;
      if (ev.key === "ArrowLeft") go(-1);
      if (ev.key === "ArrowRight") go(1);
      if (ev.key === "Escape") {
        setSelectedId(null);
        showGallery();
      }
    });

    try {
      const res = await fetch(INDEX_URL, { cache: "no-store" });
      if (!res.ok) throw new Error(`index ${res.status}`);
      const doc = await res.json();
      flat = doc.entries || [];
      byId = new Map(flat.map((e, i) => [e.dream_id, i]));
      el.navMeta.textContent = `${doc.count ?? flat.length} dreams · newest first`;
      renderGallery(flat);
      route();
    } catch (err) {
      el.navMeta.textContent = `Could not load index (${err.message || err})`;
    }
  }

  main();
})();
