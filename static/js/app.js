/* Project javascript.
 *
 * Everything here runs from an external file on purpose: the production CSP is
 * script-src 'self', so an inline <script> would be blocked. Components hand
 * their data over through data-* attributes.
 */
(function () {
  "use strict";

  /* Leaflet map, tech.md section 7. OpenStreetMap tiles, no google script. */
  function initMaps() {
    var nodes = document.querySelectorAll("[data-map]");
    if (!nodes.length || typeof window.L === "undefined") {
      return;
    }
    nodes.forEach(function (node) {
      var lat = parseFloat(node.dataset.lat);
      var lng = parseFloat(node.dataset.lng);
      if (isNaN(lat) || isNaN(lng)) {
        return;
      }
      var map = window.L.map(node).setView([lat, lng], parseInt(node.dataset.zoom, 10) || 16);
      window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(map);
      var marker = window.L.marker([lat, lng]).addTo(map);
      if (node.dataset.label) {
        marker.bindPopup(node.dataset.label);
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

  document.addEventListener("DOMContentLoaded", function () {
    initMaps();
    initCookieBanner();
    initModals();
    linkFieldErrors();
  });
})();
