/**
 * Book reader: section jump buttons and paginated pages (\\newpage markers).
 */
(function () {
  "use strict";

  var reader = document.querySelector(".xuanxin-paginated-reader");
  var pages = reader
    ? Array.prototype.slice.call(reader.querySelectorAll(".xuanxin-page"))
    : [];
  var total = pages.length;
  var paginated = total > 1;

  var body = document.body;
  var prevChapter = body.dataset.prevChapter || "";
  var prevChapterPages = parseInt(body.dataset.prevChapterPages || "0", 10);
  var nextChapter = body.dataset.nextChapter || "";

  var prevButtons = document.querySelectorAll("[data-page-action='prev']");
  var nextButtons = document.querySelectorAll("[data-page-action='next']");
  var currentEls = document.querySelectorAll("[data-page-current]");
  var totalEls = document.querySelectorAll("[data-page-total]");
  var postHeader = document.querySelector(".post-header");

  var current = 1;

  function setupFloatingSectionNav() {
    var nav = document.querySelector(".xuanxin-section-nav");
    if (!nav) return null;
    nav.classList.add("xuanxin-section-nav--floating");
    document.body.appendChild(nav);
    document.body.classList.add("xuanxin-has-section-nav");
    return nav;
  }

  setupFloatingSectionNav();

  function setupImageDownloadGuard() {
    document.addEventListener(
      "contextmenu",
      function (event) {
        if (event.target && event.target.tagName === "IMG") {
          event.preventDefault();
        }
      },
      true
    );

    document.addEventListener(
      "dragstart",
      function (event) {
        if (event.target && event.target.tagName === "IMG") {
          event.preventDefault();
        }
      },
      true
    );
  }

  setupImageDownloadGuard();

  var fullpageToolbar = null;
  var fullpageLightbox = null;
  var activeFullpageWrapper = null;

  var FULLPAGE_EXPAND_ICON =
    '<svg class="xuanxin-fullpage-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M4 10V7a1 1 0 0 1 1-1h3a1 1 0 1 1 0 2H6v2a1 1 0 1 1-2 0zm9-5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v3a1 1 0 1 1-2 0V6h-2a1 1 0 0 1-1-1zm5 9a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-3a1 1 0 1 1 0-2h2v-2a1 1 0 0 1 1-1zM9 19a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 1 1 2 0v2h2a1 1 0 0 1 1 1z"/>' +
    "</svg>";

  function readInlineRotation(img) {
    var style = img.getAttribute("style") || "";
    var match = style.match(/rotate\(([-\d.]+)deg\)/i);
    if (!match) return 0;
    var deg = Math.round(parseFloat(match[1])) % 360;
    return deg < 0 ? deg + 360 : deg;
  }

  function clearInlineRotation(img) {
    var style = img.getAttribute("style") || "";
    style = style
      .replace(/transform\s*:\s*rotate\([^;)]+\)\s*;?/gi, "")
      .replace(/;\s*;/g, ";")
      .trim();
    if (style.endsWith(";")) style = style.slice(0, -1).trim();
    if (style) img.setAttribute("style", style);
    else img.removeAttribute("style");
  }

  function parseStyleDimension(style, prop) {
    var match = style.match(new RegExp(prop + "\\s*:\\s*([^;]+)", "i"));
    return match ? match[1].trim() : "";
  }

  function paginatedFullpagePageHeight(wrapper) {
    var prose = wrapper.closest(".prose");
    var width = prose ? prose.clientWidth : wrapper.clientWidth;
    return width > 0 ? width * 1.414 : 0;
  }

  function layoutPaginatedFullpage(img, wrapper) {
    var width = img.dataset.fullpageWidth || "";
    var height = img.dataset.fullpageHeight || "";
    var pageHeight = paginatedFullpagePageHeight(wrapper);

    img.style.width = width || "100%";
    img.style.maxWidth = "100%";
    img.style.height = "auto";
    img.style.maxHeight = "";

    if (height && height.charAt(height.length - 1) === "%" && pageHeight > 0) {
      var pct = parseFloat(height) / 100;
      if (!Number.isNaN(pct) && pct > 0) {
        img.style.maxHeight = String(Math.round(pageHeight * pct)) + "px";
      }
    } else if (height && height !== "auto") {
      img.style.maxHeight = height;
    }

    applyFullpageTransform(img, wrapper);

    window.requestAnimationFrame(function () {
      var rect = img.getBoundingClientRect();
      wrapper.style.minHeight = Math.ceil(rect.height) + "px";
    });
  }

  function initFullpageImages() {
    document.querySelectorAll(".fullpage-image img").forEach(function (img) {
      if (img.dataset.fullpageInited === "1") return;
      img.dataset.fullpageInited = "1";
      var style = img.getAttribute("style") || "";
      img.dataset.fullpageWidth = parseStyleDimension(style, "width");
      img.dataset.fullpageHeight = parseStyleDimension(style, "height");
      img.dataset.rotateDeg = String(readInlineRotation(img));
      clearInlineRotation(img);
      img.style.cursor = "default";

      var wrapper = img.closest(".fullpage-image");
      function layout() {
        if (!wrapper) return;
        if (document.body.classList.contains("xuanxin-paginated")) {
          layoutPaginatedFullpage(img, wrapper);
        } else {
          applyFullpageTransform(img, wrapper);
        }
      }

      if (img.complete) layout();
      else img.addEventListener("load", layout);
    });
  }

  function syncLightboxRotation(img) {
    if (!fullpageLightbox || fullpageLightbox.hidden || !img) return;
    var lbImg = fullpageLightbox.querySelector(".xuanxin-fullpage-lightbox-img");
    if (!lbImg) return;
    var deg = parseInt(img.dataset.rotateDeg || "0", 10);
    lbImg.style.transform = "rotate(" + deg + "deg)";
    lbImg.classList.toggle("is-rotated-side", deg === 90 || deg === 270);
  }

  function applyFullpageTransform(img, wrapper) {
    var deg = parseInt(img.dataset.rotateDeg || "0", 10);
    img.style.transform = "rotate(" + deg + "deg)";
    wrapper.classList.toggle("is-rotated-side", deg === 90 || deg === 270);
    syncLightboxRotation(img);
    if (document.body.classList.contains("xuanxin-paginated")) {
      window.requestAnimationFrame(function () {
        var rect = img.getBoundingClientRect();
        wrapper.style.minHeight = Math.ceil(rect.height) + "px";
      });
    }
  }

  function ensureFullpageLightbox() {
    if (fullpageLightbox) return fullpageLightbox;

    fullpageLightbox = document.createElement("div");
    fullpageLightbox.className = "xuanxin-fullpage-lightbox";
    fullpageLightbox.hidden = true;
    fullpageLightbox.innerHTML =
      '<button type="button" class="xuanxin-fullpage-lightbox-backdrop" data-action="close" aria-label="Close"></button>' +
      '<div class="xuanxin-fullpage-lightbox-stage" role="dialog" aria-modal="true" aria-label="Image preview">' +
      '<img class="xuanxin-fullpage-lightbox-img" alt="" />' +
      '<button type="button" class="xuanxin-fullpage-lightbox-close" data-action="close" aria-label="Close">×</button>' +
      "</div>";
    document.body.appendChild(fullpageLightbox);

    fullpageLightbox.addEventListener("click", function (event) {
      if (event.target.closest('[data-action="close"]')) {
        closeFullpageLightbox();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && fullpageLightbox && !fullpageLightbox.hidden) {
        closeFullpageLightbox();
      }
    });

    return fullpageLightbox;
  }

  function openFullpageLightbox(img) {
    var lightbox = ensureFullpageLightbox();
    var lbImg = lightbox.querySelector(".xuanxin-fullpage-lightbox-img");
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt || "";
    syncLightboxRotation(img);
    lightbox.hidden = false;
    document.body.classList.add("xuanxin-lightbox-open");
    lightbox.querySelector(".xuanxin-fullpage-lightbox-close").focus();
  }

  function closeFullpageLightbox() {
    if (!fullpageLightbox || fullpageLightbox.hidden) return;
    fullpageLightbox.hidden = true;
    document.body.classList.remove("xuanxin-lightbox-open");
  }

  function findFullpageWrapperForPage(pageNumber) {
    if (paginated && pages.length) {
      var pageEl = pages[pageNumber - 1];
      return pageEl ? pageEl.querySelector(".fullpage-image") : null;
    }
    return document.querySelector(".fullpage-image");
  }

  function ensureFullpageToolbar() {
    if (fullpageToolbar) return fullpageToolbar;

    fullpageToolbar = document.createElement("div");
    fullpageToolbar.className = "xuanxin-fullpage-controls";
    fullpageToolbar.setAttribute("aria-label", "Image controls");
    fullpageToolbar.hidden = true;
    fullpageToolbar.innerHTML =
      '<button type="button" class="xuanxin-fullpage-btn" data-action="rotate-left" aria-label="Rotate left" title="Rotate left">↺</button>' +
      '<button type="button" class="xuanxin-fullpage-btn" data-action="rotate-right" aria-label="Rotate right" title="Rotate right">↻</button>' +
      '<button type="button" class="xuanxin-fullpage-btn" data-action="popup" aria-label="View larger" title="View larger">' +
      FULLPAGE_EXPAND_ICON +
      "</button>";
    document.body.appendChild(fullpageToolbar);

    fullpageToolbar.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-action]");
      if (!btn || !activeFullpageWrapper) return;
      event.preventDefault();
      event.stopPropagation();

      var img = activeFullpageWrapper.querySelector("img");
      if (!img) return;

      var action = btn.dataset.action;
      if (action === "rotate-left") {
        var leftDeg = parseInt(img.dataset.rotateDeg || "0", 10);
        img.dataset.rotateDeg = String((leftDeg + 270) % 360);
        applyFullpageTransform(img, activeFullpageWrapper);
      } else if (action === "rotate-right") {
        var rightDeg = parseInt(img.dataset.rotateDeg || "0", 10);
        img.dataset.rotateDeg = String((rightDeg + 90) % 360);
        applyFullpageTransform(img, activeFullpageWrapper);
      } else if (action === "popup") {
        openFullpageLightbox(img);
      }
    });

    return fullpageToolbar;
  }

  function updateFullpageToolbar(pageNumber) {
    initFullpageImages();
    closeFullpageLightbox();
    var toolbar = ensureFullpageToolbar();
    var wrapper = findFullpageWrapperForPage(pageNumber);
    activeFullpageWrapper = wrapper;

    if (!wrapper) {
      toolbar.hidden = true;
      closeFullpageLightbox();
      document.body.classList.remove("xuanxin-fullpage-active");
      return;
    }

    wrapper.appendChild(toolbar);
    toolbar.hidden = false;
    document.body.classList.add("xuanxin-fullpage-active");
    var img = wrapper.querySelector("img");
    if (!img) return;
    if (document.body.classList.contains("xuanxin-paginated")) {
      layoutPaginatedFullpage(img, wrapper);
    } else {
      applyFullpageTransform(img, wrapper);
    }
  }

  initFullpageImages();

  function pageForElement(el) {
    if (!el) return 1;
    var pageEl = el.closest(".xuanxin-page");
    if (!pageEl) return 1;
    return parseInt(pageEl.getAttribute("data-page"), 10) || 1;
  }

  function readInitialPage() {
    if (window.location.hash) {
      var hashTarget = document.getElementById(window.location.hash.slice(1));
      if (hashTarget) return pageForElement(hashTarget);
    }
    var params = new URLSearchParams(window.location.search);
    var requested = parseInt(params.get("page") || "1", 10);
    if (Number.isNaN(requested)) return 1;
    return Math.min(Math.max(1, requested), Math.max(total, 1));
  }

  function pageHasCover(pageEl) {
    return !!pageEl.querySelector(".fullpage-image");
  }

  function updateHeader(pageNumber) {
    if (!postHeader) return;
    var pageEl = pages[pageNumber - 1];
    postHeader.hidden = pageNumber > 1 || pageHasCover(pageEl);
  }

  function syncButtons() {
    if (!paginated) return;
    var atFirst = current <= 1;
    var atLast = current >= total;
    var canGoPrev = !atFirst || (prevChapter && prevChapterPages > 0);
    var canGoNext = !atLast || !!nextChapter;

    prevButtons.forEach(function (btn) {
      btn.disabled = !canGoPrev;
    });
    nextButtons.forEach(function (btn) {
      btn.disabled = !canGoNext;
    });
  }

  function updateUrl(pageNumber, hash) {
    var url = new URL(window.location.href);
    if (pageNumber <= 1) url.searchParams.delete("page");
    else url.searchParams.set("page", String(pageNumber));
    if (hash) url.hash = hash;
    window.history.replaceState(null, "", url);
  }

  function showPage(pageNumber, hash) {
    if (!paginated) return;
    current = pageNumber;
    pages.forEach(function (el, index) {
      el.hidden = index + 1 !== pageNumber;
    });
    currentEls.forEach(function (el) {
      el.textContent = String(pageNumber);
    });
    updateHeader(pageNumber);
    syncButtons();
    updateUrl(pageNumber, hash || window.location.hash.slice(1));
    updateFullpageToolbar(pageNumber);
    if (reader) {
      reader.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }

  function goPrev() {
    if (!paginated) return;
    if (current > 1) {
      showPage(current - 1);
      return;
    }
    if (prevChapter && prevChapterPages > 0) {
      window.location.href =
        prevChapter +
        (prevChapterPages > 1 ? "?page=" + prevChapterPages : "");
    }
  }

  function goNext() {
    if (!paginated) return;
    if (current < total) {
      showPage(current + 1);
      return;
    }
    if (nextChapter) {
      window.location.href = nextChapter;
    }
  }

  function highlightSection(target) {
    target.classList.add("xuanxin-section-target");
    window.setTimeout(function () {
      target.classList.remove("xuanxin-section-target");
    }, 1800);
  }

  function navigateToSection(targetId) {
    var target = document.getElementById(targetId);
    if (!target) return;

    var pageNumber = pageForElement(target);
    if (paginated && pageNumber !== current) {
      showPage(pageNumber, targetId);
    }

    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        target.scrollIntoView({ block: "start", behavior: "smooth" });
        highlightSection(target);
        updateUrl(paginated ? current : pageNumber, targetId);
      });
    });
  }

  document.querySelectorAll(".xuanxin-section-nav-btn").forEach(function (btn) {
    btn.addEventListener("click", function (event) {
      event.preventDefault();
      var href = btn.getAttribute("href") || "";
      if (href.charAt(0) === "#") {
        navigateToSection(href.slice(1));
      }
    });
  });

  if (paginated) {
    document.body.classList.add("xuanxin-paginated");

    totalEls.forEach(function (el) {
      el.textContent = String(total);
    });

    current = readInitialPage();

    prevButtons.forEach(function (btn) {
      btn.addEventListener("click", goPrev);
    });
    nextButtons.forEach(function (btn) {
      btn.addEventListener("click", goNext);
    });

    document.addEventListener("keydown", function (event) {
      if (event.defaultPrevented) return;
      var tag = (event.target && event.target.tagName) || "";
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goPrev();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goNext();
      }
    });

    showPage(current, window.location.hash.slice(1));
  } else {
    updateFullpageToolbar(1);
  }

  if (window.location.hash) {
    window.setTimeout(function () {
      navigateToSection(window.location.hash.slice(1));
    }, paginated ? 60 : 0);
  }
})();
