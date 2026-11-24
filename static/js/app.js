/* =============================================================
   ASSURED CONTRACT FARMING — UI behaviours
   Theme, navigation, command palette, motion & form UX.
   ============================================================= */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- Theme toggle ---------- */
  var themeBtn = $("#themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("acf-theme", next); } catch (e) {}
      toast(next === "dark" ? "Dark mode enabled" : "Light mode enabled");
    });
  }

  /* ---------- Mobile navigation ---------- */
  var menuBtn = $("#menuToggle");
  if (menuBtn) menuBtn.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  document.addEventListener("click", function (e) {
    if (document.body.classList.contains("nav-open") && !e.target.closest(".rail") && !e.target.closest("#menuToggle")) {
      document.body.classList.remove("nav-open");
    }
  });

  /* ---------- Toasts ---------- */
  window.toast = function (msg) {
    var host = $("#toastHost");
    if (!host) return;
    var t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    host.appendChild(t);
    setTimeout(function () { t.classList.add("out"); setTimeout(function () { t.remove(); }, 300); }, 2600);
  };
  var toast = window.toast;

  /* ---------- Command palette (Ctrl/Cmd + K, or "/") ---------- */
  var backdrop = $("#cmdBackdrop"), cmdInput = $("#cmdInput"), cmdList = $("#cmdList");
  if (backdrop && cmdInput && cmdList) {
    var items = $$(".rail nav a").filter(function (a) { return !a.classList.contains("logout"); }).map(function (a) {
      return { label: a.textContent.trim(), href: a.getAttribute("href"), icon: a.querySelector("svg") ? a.querySelector("svg").outerHTML : "" };
    });
    var sel = 0, shown = items;
    var render = function () {
      cmdList.innerHTML = shown.map(function (it, i) {
        return '<li class="' + (i === sel ? "sel" : "") + '"><a href="' + it.href + '">' + it.icon + it.label + "<small>Go to page</small></a></li>";
      }).join("") || '<li style="padding:18px;color:var(--ink-mute);font-size:14px">No matching pages</li>';
    };
    var open = function () { backdrop.classList.add("open"); cmdInput.value = ""; shown = items; sel = 0; render(); setTimeout(function () { cmdInput.focus(); }, 30); };
    var close = function () { backdrop.classList.remove("open"); };
    var trigger = $("#cmdOpen");
    if (trigger) trigger.addEventListener("click", open);
    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) close(); });
    cmdInput.addEventListener("input", function () {
      var q = cmdInput.value.toLowerCase();
      shown = items.filter(function (it) { return it.label.toLowerCase().indexOf(q) > -1; });
      sel = 0; render();
    });
    cmdInput.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, shown.length - 1); render(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); render(); }
      else if (e.key === "Enter" && shown[sel]) { window.location.href = shown[sel].href; }
    });
    document.addEventListener("keydown", function (e) {
      var typing = /INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || "");
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); open(); }
      else if (e.key === "/" && !typing) { e.preventDefault(); open(); }
      else if (e.key === "Escape") close();
    });
  }

  /* ---------- Scroll reveal ---------- */
  var reveals = $$(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: .12 });
    reveals.forEach(function (el, i) { el.style.transitionDelay = Math.min(i % 6, 5) * 60 + "ms"; io.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add("in"); }); }

  /* ---------- Count-up numbers: <span data-count="1234" data-decimals="1"> ---------- */
  $$("[data-count]").forEach(function (el) {
    var end = parseFloat(el.getAttribute("data-count")), dec = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var suffix = el.getAttribute("data-suffix") || "";
    if (isNaN(end)) return;
    var start = null, dur = 1200;
    var fmt = function (v) { return v.toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix; };
    var step = function (ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(end * eased);
      if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(end);
    };
    requestAnimationFrame(step);
  });

  /* ---------- Animated bars/rings: set --v (0-100) then animate ---------- */
  requestAnimationFrame(function () {
    $$("[data-fill]").forEach(function (el) { el.style.setProperty("--v", el.getAttribute("data-fill")); el.classList.add("filled"); });
  });

  /* ---------- Form UX: loading state + live validation ---------- */
  $$("form").forEach(function (form) {
    $$("input, select", form).forEach(function (f) {
      f.addEventListener("blur", function () { f.classList.add("touched"); });
    });
    form.addEventListener("submit", function () {
      if (!form.checkValidity()) { $$("input, select", form).forEach(function (f) { f.classList.add("touched"); }); return; }
      var btn = form.querySelector("button[type=submit], button:not([type])");
      if (btn && !btn.dataset.noLoading) { setTimeout(function () { btn.classList.add("is-loading"); }, 0); }
      var bar = $("#pageProgress"); if (bar) { bar.style.opacity = 1; bar.style.width = "70%"; }
    });
  });

  /* ---------- Page progress on navigation ---------- */
  var bar = $("#pageProgress");
  if (bar) {
    bar.style.width = "35%";
    window.addEventListener("load", function () { bar.style.width = "100%"; setTimeout(function () { bar.style.opacity = 0; }, 300); });
    $$("a[href]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        var h = a.getAttribute("href");
        if (h && h.charAt(0) !== "#" && !a.target && !e.ctrlKey && !e.metaKey) { bar.style.opacity = 1; bar.style.width = "65%"; }
      });
    });
  }



  /* ---------- Range tag beside each field label ---------- */
  function addRangeTag(inp, text) {
    var label = (inp.id && document.querySelector('label[for="' + inp.id + '"]')) ||
      (inp.closest(".yield-form-group, .form-group, .search-group") || document).querySelector("label");
    if (!label || label.querySelector(".range-chip")) return;
    label.classList.add("has-range");
    var chip = document.createElement("span");
    chip.className = "range-chip";
    chip.textContent = text;
    label.appendChild(chip);
  }

  /* ---------- Range-aware number inputs (sliders, typical band, live status) ---------- */
  $$("input[data-range]").forEach(function (inp) {
    var min = parseFloat(inp.min), max = parseFloat(inp.max), step = parseFloat(inp.step) || 1;
    var unit = inp.getAttribute("data-unit") || "", u = unit ? " " + unit : "";
    var tl = parseFloat(inp.getAttribute("data-typ-low")), th = parseFloat(inp.getAttribute("data-typ-high"));
    if (isNaN(min) || isNaN(max)) return;
    var fmt = function (v) { v = Number(v); if (inp.name === "crop_year") return String(v); return v.toLocaleString("en-IN", { maximumFractionDigits: 2 }); };
    addRangeTag(inp, "Range: " + fmt(min) + " – " + fmt(max) + u);
    var wrap = document.createElement("div");
    wrap.className = "range-wrap";
    var slider = null;
    if (!inp.hasAttribute("data-no-slider")) {
      slider = document.createElement("input");
      slider.type = "range"; slider.className = "range-slider"; slider.min = min; slider.max = max; slider.step = step;
      slider.setAttribute("aria-label", "Adjust value");
      if (!isNaN(tl) && !isNaN(th)) {
        slider.style.setProperty("--tl", ((tl - min) / (max - min) * 100) + "%");
        slider.style.setProperty("--th", ((th - min) / (max - min) * 100) + "%");
      }
      wrap.appendChild(slider);
    }
    var meta = document.createElement("div");
    meta.className = "range-meta";
    meta.innerHTML = '<span>' + fmt(min) + '</span>' +
      (isNaN(tl) ? "" : '<span class="typ">Typical: ' + fmt(tl) + ' – ' + fmt(th) + u + '</span>') +
      '<span>' + fmt(max) + '</span>';
    wrap.appendChild(meta);
    var status = document.createElement("div");
    status.className = "range-status";
    wrap.appendChild(status);
    inp.parentNode.insertBefore(wrap, inp.nextSibling);

    function refresh() {
      var v = parseFloat(inp.value);
      status.className = "range-status"; status.textContent = "";
      if (slider && !isNaN(v)) slider.value = Math.min(Math.max(v, min), max);
      if (isNaN(v)) return;
      if (v < min || v > max) { status.className += " bad"; status.textContent = "Allowed range: " + fmt(min) + " – " + fmt(max) + u; }
      else if (!isNaN(tl) && (v < tl || v > th)) { status.className += " warn"; status.textContent = "Outside the typical range — prediction may be less reliable"; }
      else { status.className += " ok"; status.textContent = "Within the typical range"; }
    }
    if (slider) slider.addEventListener("input", function () { inp.value = slider.value; refresh(); inp.dispatchEvent(new Event("input", { bubbles: true })); });
    inp.addEventListener("input", refresh);
    refresh();
  });

  /* ---------- Fertilizer / pesticide: total kg with per-hectare guidance ---------- */
  var areaField = $("input[name=farm_area][data-range]");
  $$("input[data-perha]").forEach(function (inp) {
    var perMax = parseFloat(inp.getAttribute("data-perha-max")), tl = parseFloat(inp.getAttribute("data-typ-low")), th = parseFloat(inp.getAttribute("data-typ-high"));
    var mid = (tl + th) / 2;
    addRangeTag(inp, "Max " + perMax + " kg/ha");
    var box = document.createElement("div");
    box.className = "range-wrap";
    box.innerHTML = '<div class="range-meta perha"><span class="typ perha-typ"></span><button type="button" class="use-typical">Use typical for my farm</button></div><div class="range-status perha-status"></div>';
    inp.parentNode.insertBefore(box, inp.nextSibling);
    var typ = box.querySelector(".perha-typ"), st = box.querySelector(".perha-status"), btn = box.querySelector(".use-typical");
    function area() { var a = areaField ? parseFloat(areaField.value) : NaN; return isNaN(a) || a <= 0 ? NaN : a; }
    function refresh() {
      var a = area(), v = parseFloat(inp.value);
      st.className = "range-status perha-status"; st.textContent = "";
      if (isNaN(a)) { typ.textContent = "Enter farm area to see guidance"; inp.removeAttribute("max"); return; }
      inp.max = (perMax * a).toFixed(2);
      typ.textContent = "Typical for " + a + " ha: " + (tl * a).toLocaleString("en-IN", { maximumFractionDigits: 2 }) + " – " + (th * a).toLocaleString("en-IN", { maximumFractionDigits: 2 }) + " kg";
      if (isNaN(v)) return;
      var per = v / a, shown = per.toLocaleString("en-IN", { maximumFractionDigits: 2 });
      if (per > perMax) { st.className += " bad"; st.textContent = "That is " + shown + " kg/ha — the maximum allowed is " + perMax + " kg/ha (" + (perMax * a).toLocaleString("en-IN") + " kg total)"; }
      else if (per < tl || per > th) { st.className += " warn"; st.textContent = "≈ " + shown + " kg/ha — outside the typical " + tl + "–" + th + " kg/ha; prediction may be less reliable"; }
      else { st.className += " ok"; st.textContent = "≈ " + shown + " kg/ha — within the typical range"; }
    }
    btn.addEventListener("click", function () { var a = area(); if (isNaN(a)) { if (areaField) areaField.focus(); return; } inp.value = (mid * a).toFixed(2); refresh(); inp.dispatchEvent(new Event("input", { bubbles: true })); });
    inp.addEventListener("input", refresh);
    if (areaField) areaField.addEventListener("input", refresh);
    refresh();
  });

  /* ---------- Print button helper ---------- */
  $$("[data-print]").forEach(function (b) { b.addEventListener("click", function () { window.print(); }); });
})();
