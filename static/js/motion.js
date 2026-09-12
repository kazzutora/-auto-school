/* Motion, REDESIGN.md C.2 point 2. Under 3 KB unminified, and checked.
 *
 * Three jobs, and only the three the platform cannot do on its own:
 *   1. counting a number up when its block arrives;
 *   2. stepping a carousel from its arrows;
 *   3. telling the header it has been scrolled past.
 *
 * Everything else that moves is CSS — static/src/css/motion.css. There is no
 * animation library here and there is not going to be one: C.2 does the
 * arithmetic on why.
 *
 * Nothing in this file is load bearing. With javascript off the numbers show
 * their final value, the carousel scrolls by touch and keyboard, and the header
 * stays at its full height. That is the whole degradation.
 */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------- *
   * 1. Count-up, C.3 row 9.
   *
   * The element carries its final value as text so that it reads correctly
   * before this runs and if this never runs. data-count-to is the number to
   * animate towards, and the text is only ever replaced once the animation is
   * about to start.
   *
   * Under prefers-reduced-motion the final value is set immediately rather
   * than left at zero — C.5 says so outright, and the e2e suite checks it.
   * ---------------------------------------------------------------- */
  function countUp(el) {
    // The comma is the polish decimal separator and the mean-attempts figure
    // uses one. parseFloat stops at it — "1,3" comes back as 1 — so it is
    // normalised here rather than in the template, where the value would then
    // have to be formatted twice: once for the reader and once for this.
    var target = parseFloat(String(el.getAttribute("data-count-to")).replace(",", "."));
    if (isNaN(target)) return;

    // How many decimals to paint, which separator to paint them with, and what
    // trails the number — a percent sign, usually — all read off the markup, so
    // the animation lands on exactly the string that was there to begin with.
    var raw = el.textContent.trim();
    var decimals = (raw.split(/[.,]/)[1] || "").replace(/\D+$/, "").length;
    var separator = raw.indexOf(",") > -1 ? "," : ".";
    var suffix = raw.replace(/^[\d\s., ]+/, "");

    function paint(value) {
      var text = value.toFixed(decimals);
      if (separator === ",") text = text.replace(".", ",");
      el.textContent = text + suffix;
    }

    if (reduced) return; // the markup already says the right thing

    var duration = 900;
    var started = null;

    function frame(now) {
      if (started === null) started = now;
      var t = Math.min((now - started) / duration, 1);
      // The same curve the rest of the site uses, as a cubic ease-out.
      paint(target * (1 - Math.pow(1 - t, 3)));
      if (t < 1) requestAnimationFrame(frame);
      else paint(target);
    }

    paint(0);
    requestAnimationFrame(frame);
  }

  /* ---------------------------------------------------------------- *
   * 2. The carousel arrows, C.3 row 10.
   *
   * scrollBy on the track, one card at a time. The scrolling itself, the
   * snapping and the swipe are all the browser's; this only answers the two
   * buttons and keeps their disabled state honest at either end.
   * ---------------------------------------------------------------- */
  function carousel(root) {
    var track = root.querySelector("[data-carousel-track]");
    if (!track) return;
    var prev = root.querySelector("[data-carousel-prev]");
    var next = root.querySelector("[data-carousel-next]");

    function step() {
      var first = track.firstElementChild;
      if (!first) return track.clientWidth;
      var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return first.getBoundingClientRect().width + gap;
    }

    function sync() {
      // 2px of slack: a fractional scrollWidth would otherwise leave the last
      // arrow enabled on a track that cannot move.
      var max = track.scrollWidth - track.clientWidth - 2;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    }

    if (prev) prev.addEventListener("click", function () {
      track.scrollBy({ left: -step(), behavior: reduced ? "auto" : "smooth" });
    });
    if (next) next.addEventListener("click", function () {
      track.scrollBy({ left: step(), behavior: reduced ? "auto" : "smooth" });
    });

    track.addEventListener("scroll", function () {
      clearTimeout(track._t);
      track._t = setTimeout(sync, 80);
    }, { passive: true });

    window.addEventListener("resize", sync, { passive: true });
    sync();
  }

  /* ---------------------------------------------------------------- *
   * 3. The header, C.3 row 6.
   *
   * An IntersectionObserver on a one pixel sentinel above the header, not a
   * scroll listener: R4 point 1 asks for it that way, and the reason is that a
   * scroll handler runs on every frame of every scroll to answer a question
   * whose value changes twice.
   * ---------------------------------------------------------------- */
  function header() {
    var bar = document.querySelector("[data-header]");
    var sentinel = document.querySelector("[data-header-sentinel]");
    if (!bar || !sentinel || !("IntersectionObserver" in window)) return;

    new IntersectionObserver(function (entries) {
      bar.classList.toggle("is-stuck", !entries[0].isIntersecting);
    }).observe(sentinel);
  }

  function init() {
    header();

    var counters = document.querySelectorAll("[data-count-to]");
    if (counters.length && "IntersectionObserver" in window) {
      var seen = new IntersectionObserver(function (entries, self) {
        for (var i = 0; i < entries.length; i++) {
          if (!entries[i].isIntersecting) continue;
          self.unobserve(entries[i].target); // C.4: once, never again
          countUp(entries[i].target);
        }
      }, { rootMargin: "0px 0px -15% 0px" });
      for (var i = 0; i < counters.length; i++) seen.observe(counters[i]);
    } else {
      // No observer: the markup already carries the final number, so there is
      // nothing to do and nothing to fix.
      for (var j = 0; j < counters.length; j++) void counters[j];
    }

    var rails = document.querySelectorAll("[data-carousel]");
    for (var k = 0; k < rails.length; k++) carousel(rails[k]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
