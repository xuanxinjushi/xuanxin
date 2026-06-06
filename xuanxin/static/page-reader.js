/**
 * Paginated book reader: one viewport "page" per \\newpage marker.
 * Arrow keys, on-screen buttons, and ?page=N in the URL.
 */
(function () {
  "use strict";

  var reader = document.querySelector(".xuanxin-paginated-reader");
  if (!reader) return;

  var pages = Array.prototype.slice.call(
    reader.querySelectorAll(".xuanxin-page")
  );
  var total = pages.length;
  if (total <= 1) return;

  document.body.classList.add("xuanxin-paginated");

  var body = document.body;
  var prevChapter = body.dataset.prevChapter || "";
  var prevChapterPages = parseInt(body.dataset.prevChapterPages || "0", 10);
  var nextChapter = body.dataset.nextChapter || "";

  var prevButtons = document.querySelectorAll("[data-page-action='prev']");
  var nextButtons = document.querySelectorAll("[data-page-action='next']");
  var currentEls = document.querySelectorAll("[data-page-current]");
  var totalEls = document.querySelectorAll("[data-page-total]");
  var postHeader = document.querySelector(".post-header");

  totalEls.forEach(function (el) {
    el.textContent = String(total);
  });

  function readInitialPage() {
    var params = new URLSearchParams(window.location.search);
    var requested = parseInt(params.get("page") || "1", 10);
    if (Number.isNaN(requested)) return 1;
    return Math.min(Math.max(1, requested), total);
  }

  var current = readInitialPage();

  function pageHasCover(pageEl) {
    return !!pageEl.querySelector(".fullpage-image");
  }

  function updateHeader(pageNumber) {
    if (!postHeader) return;
    var pageEl = pages[pageNumber - 1];
    postHeader.hidden = pageNumber > 1 || pageHasCover(pageEl);
  }

  function syncButtons() {
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

  function updateUrl(pageNumber) {
    var url = new URL(window.location.href);
    if (pageNumber <= 1) url.searchParams.delete("page");
    else url.searchParams.set("page", String(pageNumber));
    window.history.replaceState(null, "", url);
  }

  function showPage(pageNumber) {
    current = pageNumber;
    pages.forEach(function (el, index) {
      el.hidden = index + 1 !== pageNumber;
    });
    currentEls.forEach(function (el) {
      el.textContent = String(pageNumber);
    });
    updateHeader(pageNumber);
    syncButtons();
    updateUrl(pageNumber);
    reader.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  function goPrev() {
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
    if (current < total) {
      showPage(current + 1);
      return;
    }
    if (nextChapter) {
      window.location.href = nextChapter;
    }
  }

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

  showPage(current);
})();
