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

  // ELK layouts are an ES module plugin, loaded the first time one is used.
  // layout-elk 0.1.7 matches mermaid 11.4.1; newer releases need mermaid 11.x+.
  var ELK_URL =
    "https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0.1.7/dist/mermaid-layout-elk.esm.min.mjs";
  var elkReady = null;

  function loadLayout(layout) {
    if (!layout || layout.indexOf("elk") !== 0) return Promise.resolve();
    if (!elkReady) {
      elkReady = import(ELK_URL).then(
        function (m) {
          window.mermaid.registerLayoutLoaders(m.default);
        },
        function (e) {
          elkReady = null; // let a later render retry
          throw new Error("Could not load the ELK layout: " + e.message);
        }
      );
    }
    return elkReady;
  }

  async function render(msg) {
    var el = document.getElementById(msg.id);
    if (!el) return;
    var stage = el.querySelector(".sm-stage");
    var err = el.querySelector(".sm-error");
    try {
      await loadLayout(msg.config.layout);
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
        svg: svg,
        theme: msg.config.theme,
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

  function save(blob, name) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(function () {
      URL.revokeObjectURL(a.href);
    }, 0);
  }

  function download(s) {
    save(new Blob([s.raw], { type: "image/svg+xml" }), "diagram.svg");
  }

  // PNG: draw the SVG on a canvas. The image must load from a data: URL;
  // a blob: URL with HTML labels (foreignObject) taints the canvas in Chrome.
  var PNG_SCALE = 2;
  var LABEL_STYLES = [
    "font-family", "font-size", "font-weight", "font-style", "color",
    "line-height", "white-space",
  ];

  // An image can't see the page CSS, so copy the label fonts Mermaid
  // measured on screen (e.g. Bootstrap's <code> font) onto the copy.
  function inlineLabelStyles(from, to) {
    var a = from.querySelectorAll("foreignObject *");
    var b = to.querySelectorAll("foreignObject *");
    for (var i = 0; i < a.length && i < b.length; i++) {
      var cs = getComputedStyle(a[i]);
      LABEL_STYLES.forEach(function (k) {
        b[i].style.setProperty(k, cs.getPropertyValue(k));
      });
    }
  }

  function downloadPng(s) {
    var box = document.createElement("div");
    box.innerHTML = s.raw; // HTML parser, then XMLSerializer gives valid XML
    var svg = box.querySelector("svg");
    inlineLabelStyles(s.svg, svg);
    var vb = svg.viewBox.baseVal;
    svg.setAttribute("width", vb.width);
    svg.setAttribute("height", vb.height);
    svg.style.maxWidth = "none";
    var xml = new XMLSerializer().serializeToString(svg);
    var img = new Image();
    img.onload = function () {
      var c = document.createElement("canvas");
      c.width = Math.ceil(vb.width * PNG_SCALE);
      c.height = Math.ceil(vb.height * PNG_SCALE);
      var ctx = c.getContext("2d");
      ctx.fillStyle = s.theme === "dark" ? "#333" : "#fff";
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.scale(PNG_SCALE, PNG_SCALE);
      ctx.drawImage(img, 0, 0, vb.width, vb.height);
      c.toBlob(function (blob) {
        save(blob, "diagram.png");
      }, "image/png");
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(xml);
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
      case "download-png":
        if (s) downloadPng(s);
        break;
    }
  });

  // Syntax highlighting: color a <pre> that sits behind the textarea.
  var KEYWORDS = [
    "flowchart", "graph", "subgraph", "end", "direction", "style", "classDef",
    "class", "click", "linkStyle", "sequenceDiagram", "participant", "actor",
    "loop", "alt", "else", "opt", "par", "and", "rect", "note", "over", "as",
    "activate", "deactivate", "autonumber", "classDiagram", "stateDiagram",
    "erDiagram", "gantt", "section", "title", "dateFormat", "pie", "journey",
    "gitGraph", "commit", "branch", "checkout", "merge", "mindmap", "timeline",
    "quadrantChart", "xychart", "sankey", "block", "packet", "kanban",
    "architecture", "requirementDiagram", "C4Context", "C4Container",
  ];
  var TOKEN = new RegExp(
    [
      "(%%.*$|^---$)", // 1 comment, directive, or frontmatter fence
      '("[^"\\n]*"?)', // 2 string
      "(\\|[^|\\n]*\\|)", // 3 edge label
      "(<?(?:-{2,}|={2,}|-\\.+-)[>xo]?|-+>>?|--?[x)](?!\\w))", // 4 arrow
      "\\b(" + KEYWORDS.join("|") + ")\\b", // 5 keyword
      "\\b(TB|TD|BT|RL|LR)\\b", // 6 direction
    ].join("|"),
    "gm"
  );
  var CLASSES = [null, "comment", "string", "label", "arrow", "keyword", "dir"];

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function highlight(code) {
    var out = "";
    var last = 0;
    code.replace(TOKEN, function () {
      var m = arguments[0];
      var at = arguments[arguments.length - 2];
      var g = 1;
      while (arguments[g] === undefined) g++;
      out += escapeHtml(code.slice(last, at));
      out += '<span class="sm-tok-' + CLASSES[g] + '">' + escapeHtml(m) + "</span>";
      last = at + m.length;
      return m;
    });
    // A trailing newline needs a character so the <pre> keeps the last line.
    return out + escapeHtml(code.slice(last)) + "\n ";
  }

  function paint(ta) {
    var pre = ta.closest(".sm-code").querySelector(".sm-highlight");
    pre.firstChild.innerHTML = highlight(ta.value);
    pre.scrollTop = ta.scrollTop;
    pre.scrollLeft = ta.scrollLeft;
  }

  function codeArea(el) {
    return el && el.tagName === "TEXTAREA" && el.closest(".sm-code") ? el : null;
  }

  document.addEventListener("input", function (e) {
    var ta = codeArea(e.target);
    if (ta) paint(ta);
  });

  document.addEventListener(
    "scroll",
    function (e) {
      var ta = codeArea(e.target);
      if (!ta) return;
      var pre = ta.closest(".sm-code").querySelector(".sm-highlight");
      pre.scrollTop = ta.scrollTop;
      pre.scrollLeft = ta.scrollLeft;
    },
    true
  );

  // Tab inserts spaces in the editor instead of moving focus. Escape
  // releases the editor: the next Tab (or Shift+Tab) moves focus as usual.
  var released = null;

  document.addEventListener("focusin", function () {
    released = null;
  });

  document.addEventListener("keydown", function (e) {
    var ta = codeArea(e.target);
    if (!ta) return;
    if (e.key === "Escape") {
      released = ta;
      return;
    }
    if (e.key === "Shift") return; // keep the release for Shift+Tab
    if (e.key !== "Tab" || released === ta) {
      released = null;
      return;
    }
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
    document.querySelectorAll(".sm-code textarea").forEach(function (ta) {
      paint(ta);
      var hint = ta.closest(".sm-editor").querySelector(".sm-key-hint");
      if (hint) ta.setAttribute("aria-describedby", hint.id);
    });
    Shiny.addCustomMessageHandler("shymermaid-render", render);
  });
})();
