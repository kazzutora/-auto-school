/* Project javascript.
 *
 * Everything here runs from an external file on purpose: the production CSP is
 * script-src 'self', so an inline <script> would be blocked. Components hand
 * their data over through data-* attributes.
 */
(function () {
  "use strict";

  /* Leaflet map, tech.md section 7. OpenStreetMap tiles, no google script.
   *
   * Built when the map comes into view rather than on load. The tiles are the
   * only third party request the site makes at all, and on the home page the
   * map sits in the last section: fetching a dozen of them before the visitor
   * has scrolled past the hero spends the first screen budget in A.11 on
   * something nobody is looking at yet. rootMargin starts the work a screen
   * early, so it is ready by the time it is on screen.
   */
  /* Fetch leaflet the first time a map is about to be seen, and only then.
   *
   * defer delays execution, not the download: the tags in the page head cost
   * 157 KB on load for a map that sits below the fold on both pages that have
   * one, and that is what took the home page past the 400 KB first screen
   * budget in A.11.
   */
  var leafletPromise = null;

  function loadLeaflet(node) {
    if (window.L) {
      return Promise.resolve();
    }
    if (leafletPromise) {
      return leafletPromise;
    }
    leafletPromise = new Promise(function (resolve, reject) {
      var styles = document.createElement("link");
      styles.rel = "stylesheet";
      styles.href = node.dataset.leafletCss;
      document.head.appendChild(styles);

      var script = document.createElement("script");
      script.src = node.dataset.leafletJs;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
    return leafletPromise;
  }

  function buildMap(node) {
    var lat = parseFloat(node.dataset.lat);
    var lng = parseFloat(node.dataset.lng);
    if (isNaN(lat) || isNaN(lng) || node.dataset.mapReady) {
      return;
    }
    node.dataset.mapReady = "1";
    var map = window.L.map(node).setView([lat, lng], parseInt(node.dataset.zoom, 10) || 16);
    window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    var marker = window.L.marker([lat, lng]).addTo(map);
    if (node.dataset.label) {
      marker.bindPopup(node.dataset.label);
    }
  }

  function reveal(node) {
    loadLeaflet(node).then(function () {
      buildMap(node);
    });
  }

  function initMaps() {
    var nodes = document.querySelectorAll("[data-map]");
    if (!nodes.length) {
      return;
    }
    if (typeof window.IntersectionObserver === "undefined") {
      Array.prototype.forEach.call(nodes, reveal);
      return;
    }
    var observer = new window.IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            observer.unobserve(entry.target);
            reveal(entry.target);
          }
        });
      },
      { rootMargin: "100% 0px" }
    );
    Array.prototype.forEach.call(nodes, function (node) {
      observer.observe(node);
    });
  }

  /* Cookie choice. Analytics stay off until the visitor accepts. */
  var CONSENT_KEY = "osk-cookie-consent";

  function readConsent() {
    try {
      return window.localStorage.getItem(CONSENT_KEY);
    } catch (err) {
      return null;
    }
  }

  function writeConsent(value) {
    try {
      window.localStorage.setItem(CONSENT_KEY, value);
    } catch (err) {
      /* Private mode: the banner simply shows again next visit. */
    }
  }

  function initCookieBanner() {
    var banner = document.querySelector("[data-cookie-banner]");
    if (!banner) {
      return;
    }
    if (readConsent()) {
      return;
    }
    banner.hidden = false;

    banner.addEventListener("click", function (event) {
      var accept = event.target.closest("[data-cookie-accept]");
      var reject = event.target.closest("[data-cookie-reject]");
      if (!accept && !reject) {
        return;
      }
      writeConsent(accept ? "accepted" : "rejected");
      banner.hidden = true;
      if (accept) {
        document.dispatchEvent(new CustomEvent("cookie-consent-accepted"));
      }
    });
  }

  /* Modals, tech.md section 7 and FRONTEND.md A.5.
   *
   * <dialog>.showModal() is what gives the focus trap, the Esc key and the
   * focus restore, all three of them correctly and for free. The only thing it
   * has no opinion about is closing on a click outside, which is the block
   * below: a click that lands on the dialog element itself rather than on
   * anything inside it landed on the backdrop.
   */
  function initModals() {
    document.addEventListener("click", function (event) {
      var opener = event.target.closest("[data-modal-open]");
      if (opener) {
        var dialog = document.getElementById(opener.dataset.modalOpen);
        if (dialog && typeof dialog.showModal === "function") {
          event.preventDefault();
          dialog.showModal();
          syncExpanded(opener, dialog);
        }
        return;
      }

      var closer = event.target.closest("[data-modal-close]");
      if (closer) {
        var owner = closer.closest("dialog");
        if (owner) {
          owner.close();
        }
        return;
      }

      if (event.target.matches("dialog[open]")) {
        event.target.close();
      }
    });
  }

  /* Field errors, FRONTEND.md A.5.
   *
   * A.5 wants the error text tied to the control it belongs to, so a screen
   * reader reads the reason rather than just announcing "invalid". c-input
   * writes that itself, but c-field hands rendering to django, which points
   * aria-describedby at the help text and never at the errors. This walks the
   * gap: every error c-field rendered carries an id, and the control that
   * failed is the one already marked aria-invalid inside the same field.
   *
   * See the CONTRACT GAP in templates/cotton/field.html. The real fix is the
   * form setting the attribute server side.
   */
  function linkFieldErrors() {
    var invalid = document.querySelectorAll('[aria-invalid="true"]');
    Array.prototype.forEach.call(invalid, function (control) {
      var field = control.closest("div");
      if (!field) {
        return;
      }
      var errors = field.querySelectorAll('[id$="_error_0"], [id*="_error_"]');
      if (!errors.length) {
        return;
      }
      var ids = [];
      Array.prototype.forEach.call(errors, function (node) {
        ids.push(node.id);
      });
      var existing = control.getAttribute("aria-describedby");
      if (existing) {
        ids = existing.split(/\s+/).concat(ids);
      }
      control.setAttribute("aria-describedby", ids.join(" "));
    });
  }

  /* The burger says whether the panel it controls is open. <dialog> fires close
   * for every way out — Esc, the button, a click on the backdrop — so one
   * listener per opener covers all of them. */
  function syncExpanded(opener, dialog) {
    if (!opener.hasAttribute("aria-expanded")) {
      return;
    }
    opener.setAttribute("aria-expanded", "true");
    dialog.addEventListener(
      "close",
      function () {
        opener.setAttribute("aria-expanded", "false");
      },
      { once: true }
    );
  }

  /* Table of contents on a long legal page, FRONTEND.md F10.
   *
   * Built here rather than by the renderer because the renderer is python and
   * this is a frontend change, but also because it is genuinely an
   * enhancement: the policy is complete without it, and a reader with no
   * javascript loses a shortcut rather than any of the text.
   *
   * Only past the threshold F10 sets. A contents list over three headings is
   * longer than the thing it indexes.
   */
  var TOC_THRESHOLD = 5;

  function slugify(text, taken) {
    var base =
      text
        .toLowerCase()
        .replace(/[ąćęłńóśźż]/g, function (letter) {
          return { ą: "a", ć: "c", ę: "e", ł: "l", ń: "n", ó: "o", ś: "s", ź: "z", ż: "z" }[letter];
        })
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "sekcja";
    var slug = base;
    var suffix = 2;
    while (taken[slug]) {
      slug = base + "-" + suffix++;
    }
    taken[slug] = true;
    return slug;
  }

  function initTableOfContents() {
    var holder = document.querySelector("[data-toc]");
    if (!holder) {
      return;
    }
    var scope = document.querySelector(holder.dataset.toc);
    var headings = scope ? scope.querySelectorAll("h2") : [];
    if (headings.length <= TOC_THRESHOLD) {
      return;
    }

    var taken = {};
    var list = document.createElement("ol");
    list.className = "flex flex-col gap-2";

    Array.prototype.forEach.call(headings, function (heading) {
      if (!heading.id) {
        heading.id = slugify(heading.textContent || "", taken);
      }
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = "#" + heading.id;
      link.textContent = heading.textContent;
      link.className = "underline underline-offset-4 hover:text-ink";
      item.appendChild(link);
      list.appendChild(item);
    });

    holder.appendChild(list);
    holder.hidden = false;
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMaps();
    initCookieBanner();
    initModals();
    linkFieldErrors();
    initTableOfContents();
  });

  /* htmx replaces the enrolment form with a version carrying its errors, and
   * that markup never went through DOMContentLoaded. Without this the fields
   * come back marked aria-invalid while pointing at their help text, so a
   * screen reader announces "invalid" and never says why — which is exactly
   * the criterion in DEV.md S3.1. */
  document.body.addEventListener("htmx:afterSwap", function () {
    linkFieldErrors();
  });

  /* The rate limit answers 429 and htmx swaps 2xx only, so the message the
   * server took the trouble to render was being dropped on the floor and the
   * visitor saw a button that did nothing. 429 carries a body meant to be
   * read: let it through. */
  var SWAPPABLE_ERRORS = [429];

  document.body.addEventListener("htmx:beforeSwap", function (event) {
    if (SWAPPABLE_ERRORS.indexOf(event.detail.xhr.status) !== -1) {
      event.detail.shouldSwap = true;
      event.detail.isError = false;
    }
  });

  /* F7 point 6: the server did not answer.
   *
   * htmx swaps nothing on a failed response, which is the behaviour we want —
   * everything the visitor typed is still in the form. All that is missing is
   * telling them, and giving them a number, so the submission is not simply
   * lost in silence.
   */
  function formErrorRegion(source) {
    var form = source && source.closest ? source.closest("form") : null;
    return form ? form.querySelector("[data-form-error]") : null;
  }

  document.body.addEventListener("htmx:responseError", function (event) {
    var region = formErrorRegion(event.detail.elt);
    if (region) {
      region.hidden = false;
      region.scrollIntoView({ block: "nearest" });
    }
  });

  document.body.addEventListener("htmx:sendError", function (event) {
    var region = formErrorRegion(event.detail.elt);
    if (region) {
      region.hidden = false;
    }
  });

  /* A fresh attempt starts without the last one's failure on screen. */
  document.body.addEventListener("htmx:beforeRequest", function (event) {
    var region = formErrorRegion(event.detail.elt);
    if (region) {
      region.hidden = true;
    }
  });
})();
