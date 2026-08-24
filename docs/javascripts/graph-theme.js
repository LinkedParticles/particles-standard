// SPDX-FileCopyrightText: 2026 The Particles authors
//
// SPDX-License-Identifier: Apache-2.0

/* Hand the embedded demo pages this site's palette.
 *
 * The demos (the graph export under docs/demo/, the operations explorer) are
 * self-contained pages in <iframe>s, marked with a `data-themed` attribute.
 * They cannot read the palette: Material stores the choice in localStorage
 * and stamps `data-md-color-scheme` on *this* document's <body>, which is on
 * the other side of the frame boundary. So a reader who toggles the site to
 * dark on a light OS would get a light frame in a dark page.
 *
 * Each embed accepts the theme two ways — a `?theme=dark|light|auto` query
 * parameter at load, and a `particles-graph-theme` postMessage afterwards.
 * Use the parameter for the initial paint (no flash) and the message for
 * every later toggle (no reload).
 */
(function () {
  "use strict";

  function currentTheme() {
    return document.body.getAttribute("data-md-color-scheme") === "slate" ? "dark" : "light";
  }

  function graphFrames() {
    return Array.prototype.slice.call(document.querySelectorAll("iframe[data-themed]"));
  }

  function pin(frame, theme) {
    var base = frame.getAttribute("src").split("#")[0].split("?")[0];
    // The export's own default is light, so only dark needs the parameter.
    // Leaving src untouched in the light case matters: rewriting it re-fetches
    // the frame, and these artifacts inline their whole renderer.
    var next = theme === "dark" ? base + "?theme=dark" : base;
    if (frame.getAttribute("src") !== next) frame.setAttribute("src", next);
  }

  function push(frame, theme) {
    if (frame.contentWindow) {
      frame.contentWindow.postMessage({ type: "particles-graph-theme", theme: theme }, "*");
    }
  }

  graphFrames().forEach(function (frame) {
    pin(frame, currentTheme());
    // loading="lazy": a frame that arrives later missed every toggle so far.
    frame.addEventListener("load", function () {
      push(frame, currentTheme());
    });
  });

  new MutationObserver(function () {
    var theme = currentTheme();
    graphFrames().forEach(function (frame) {
      push(frame, theme);
    });
  }).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
})();
