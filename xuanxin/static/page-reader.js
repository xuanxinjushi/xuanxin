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
  }

  if (window.location.hash) {
    window.setTimeout(function () {
      navigateToSection(window.location.hash.slice(1));
    }, paginated ? 60 : 0);
  }
})();
