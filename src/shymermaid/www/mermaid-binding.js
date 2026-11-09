(function () {
  "use strict";

  var state = {}; // canvas id -> { pz, raw }
  var seq = 0;

  function fit(s) {
    if (!s) return;
    s.pz.resize();
    s.pz.fit();
    s.pz.center();
  }

  async function render(msg) {
    var el = document.getElementById(msg.id);
    if (!el) return;
    var stage = el.querySelector(".sm-stage");
    var err = el.querySelector(".sm-error");
    try {
      window.mermaid.initialize(msg.config);
      await window.mermaid.parse(msg.code);
      var out = await window.mermaid.render("sm-svg-" + ++seq, msg.code);
      if (state[msg.id]) state[msg.id].pz.destroy();
      stage.innerHTML = out.svg;
      var svg = stage.querySelector("svg");
      svg.removeAttribute("style");
      svg.setAttribute("width", "100%");
      svg.setAttribute("height", "100%");
      state[msg.id] = {
        raw: out.svg,
        pz: window.svgPanZoom(svg, {
          fit: true,
          center: true,
          minZoom: 0.1,
          maxZoom: 20,
          zoomScaleSensitivity: 0.3,
        }),
      };
      err.hidden = true;
      err.textContent = "";
    } catch (e) {
      err.textContent = (e && e.message) || String(e);
      err.hidden = false;
    }
  }

  function download(s) {
    var blob = new Blob([s.raw], { type: "image/svg+xml" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "diagram.svg";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-sm-action]");
    if (!btn) return;
    var id = btn.dataset.smTarget;
    var s = state[id];
    switch (btn.dataset.smAction) {
      case "zoom-in":
        if (s) s.pz.zoomIn();
        break;
      case "zoom-out":
        if (s) s.pz.zoomOut();
        break;
      case "actual-size":
        if (s) {
          s.pz.zoom(s.pz.getZoom() / s.pz.getSizes().realZoom);
          s.pz.center();
        }
        break;
      case "fit":
        fit(s);
        break;
      case "fullscreen":
        var viewer = document.getElementById(id).closest(".sm-viewer");
        if (document.fullscreenElement) document.exitFullscreen();
        else viewer.requestFullscreen();
        break;
      case "download-svg":
        if (s) download(s);
        break;
    }
  });

  // Tab inserts spaces in the editor instead of moving focus.
  document.addEventListener("keydown", function (e) {
    var ta = e.target;
    if (e.key !== "Tab" || !ta.closest || !ta.closest(".sm-editor")) return;
    if (ta.tagName !== "TEXTAREA") return;
    e.preventDefault();
    ta.setRangeText("    ", ta.selectionStart, ta.selectionEnd, "end");
    ta.dispatchEvent(new Event("input", { bubbles: true }));
  });

  // Refit when the canvas changes size (sidebar toggle, window resize).
  var ro = new ResizeObserver(function (entries) {
    entries.forEach(function (en) {
      fit(state[en.target.id]);
    });
  });

  $(function () {
    document.querySelectorAll(".sm-canvas").forEach(function (c) {
      ro.observe(c);
    });
    Shiny.addCustomMessageHandler("shymermaid-render", render);
  });
})();
