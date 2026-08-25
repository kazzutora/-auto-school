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

  document.addEventListener("DOMContentLoaded", function () {
    initMaps();
    initCookieBanner();
  });
})();
