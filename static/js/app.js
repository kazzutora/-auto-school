/* Project javascript.
 *
 * Everything here runs from an external file on purpose: the production CSP is
 * script-src 'self', so an inline <script> would be blocked. Components hand
 * their data over through data-* attributes.
 */
(function () {
  "use strict";

  /* Google map, tech.md sections 2 and 7, core v26.
   *
   * Nothing goes to google until the visitor presses the button c-map renders.
   * The iframe is built here, on that click, so no page carries a google url a
   * browser would fetch on its own — which is what still lets the site run
   * without a cookie gate. An embedded google map hands the visitor's address
   * to google and sets cookies; behind a button, that is their choice.
   *
   * The keyless embed rather than the Maps JavaScript API: no key to guard, no
   * google script running on our page, nothing downloaded before the click.
   */
  function loadMap(node) {
    var lat = parseFloat(node.dataset.lat);
    var lng = parseFloat(node.dataset.lng);
    if (isNaN(lat) || isNaN(lng) || node.dataset.mapReady) {
      return;
    }
    node.dataset.mapReady = "1";
    var zoom = parseInt(node.dataset.zoom, 10) || 16;
    var lang = document.documentElement.lang || "pl";

    var frame = document.createElement("iframe");
    frame.src =
      "https://www.google.com/maps?q=" + lat + "," + lng +
      "&z=" + zoom + "&hl=" + encodeURIComponent(lang) + "&output=embed";
    frame.title = node.dataset.label || "Mapa dojazdu";
    frame.allowFullscreen = true;

    /* Removed rather than hidden: the placeholder is a flex box, and a display
     * utility beats the hidden attribute. The button that had focus goes with
     * it, so focus moves to the map instead of dropping to the document. */
    var placeholder = node.querySelector("[data-map-placeholder]");
    if (placeholder) {
      node.removeChild(placeholder);
    }
    node.appendChild(frame);
    frame.focus();
  }

  function initMaps() {
    document.addEventListener("click", function (event) {
      var button = event.target.closest("[data-map-load]");
      var node = button ? button.closest("[data-map]") : null;
      if (node) {
        loadMap(node);
      }
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

  /* The accordion and the section reveal both moved into css at core v25.
   *
   * The accordion was ~55 lines here that opened <details>, measured the
   * panel, then walked its height from zero — the only way to animate to a
   * height nobody knows in advance, before grid-template-rows could go from
   * 0fr to 1fr. static/src/css/motion.css does it in four declarations now.
   *
   * The reveal was ~60 lines of IntersectionObserver plus a passive scroll
   * listener to catch the sections an anchor jump skipped over. CSS
   * scroll-driven animations have no such gap: animation-timeline: view()
   * is evaluated per element against the scroll position, so a jump to the
   * bottom of the page leaves nothing behind it hidden.
   *
   * REDESIGN.md C.2 point 1 is what asked for both, and the budget in C.6
   * is what it bought: those two were most of this file's weight.
   */

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

  /* The old site's anchors, tech.md section 4.8.
   *
   * oskostrycharz.pl was one page with anchor navigation, so every link anybody
   * ever shared looks like /#pliki or /#kontakt. A browser does not send the
   * fragment, which is why django.contrib.redirects cannot answer these: the
   * server sees a bare "/" and has no idea what was asked for. The table is
   * printed into the page as json by templates/pages/home.html, read from the
   * same csv the server side redirects come from.
   *
   * replace(), not assign(): the old url must not sit in the history, or Back
   * lands on the home page and bounces straight out again.
   */
  (function () {
    var hash = window.location.hash.replace(/^#/, "");
    if (!hash) {
      return;
    }
    var source = document.getElementById("legacy-fragments");
    if (!source) {
      return;
    }
    var table;
    try {
      table = JSON.parse(source.textContent);
    } catch (error) {
      return;
    }
    var target = table[hash];
    /* An anchor that also exists on this page is a jump, not a redirect. */
    if (target && !document.getElementById(hash)) {
      window.location.replace(target);
    }
  })();
})();
