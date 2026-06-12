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

  function typesetMath(nodes) {
    if (!window.MathJax || !window.MathJax.typesetPromise) return;
    var targets = nodes ? (Array.isArray(nodes) ? nodes : [nodes]) : undefined;
    window.MathJax.typesetPromise(targets).catch(function () {});
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
    if (pages[pageNumber - 1]) {
      typesetMath([pages[pageNumber - 1]]);
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

  function setupPasswordLock(lock, config) {
    var hash = lock.getAttribute(config.hashAttr) || "";
    var form = lock.querySelector(config.formSelector);
    var content = lock.querySelector(config.contentSelector);
    var storageKey = config.storageKey(hash);
    var pwdStorageKey = storageKey + ":pwd";

    function unlock(password) {
      lock.classList.add("is-unlocked");
      if (content) content.hidden = false;
      hydrateEncryptedMedia(lock, password).catch(function () {});
      if (config.afterUnlock) config.afterUnlock(content);
      try {
        sessionStorage.setItem(storageKey, "1");
        if (password) sessionStorage.setItem(pwdStorageKey, password);
      } catch (err) {}
    }

    try {
      if (sessionStorage.getItem(storageKey) === "1") {
        unlock(sessionStorage.getItem(pwdStorageKey) || "");
        return;
      }
    } catch (err) {}

    if (content) content.hidden = true;

    if (!form) return;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var input = form.querySelector(".xuanxin-gallery-unlock-input");
      var error = form.querySelector(".xuanxin-gallery-unlock-error");
      var value = input ? input.value : "";
      sha256(value).then(function (enteredHash) {
        if (enteredHash && enteredHash === hash) {
          if (error) error.hidden = true;
          unlock(value);
          return;
        }
        if (error) error.hidden = false;
      });
    });
  }

  function sha256(text) {
    if (!window.crypto || !window.crypto.subtle) {
      return Promise.resolve("");
    }
    return window.crypto.subtle
      .digest("SHA-256", new TextEncoder().encode(text))
      .then(function (buf) {
        return Array.from(new Uint8Array(buf))
          .map(function (b) {
            return b.toString(16).padStart(2, "0");
          })
          .join("");
      });
  }

  function deriveKey(password, salt) {
    return window.crypto.subtle
      .importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"])
      .then(function (keyMaterial) {
        return window.crypto.subtle.deriveBits(
          {
            name: "PBKDF2",
            salt: salt,
            iterations: 120000,
            hash: "SHA-256",
          },
          keyMaterial,
          256
        );
      })
      .then(function (bits) {
        return window.crypto.subtle.importKey("raw", bits, { name: "AES-GCM" }, false, ["decrypt"]);
      });
  }

  function decryptAsset(data, password) {
    var bytes = new Uint8Array(data);
    if (new TextDecoder().decode(bytes.slice(0, 8)) !== "xuanxin1") {
      return Promise.reject(new Error("bad format"));
    }
    var salt = bytes.slice(8, 24);
    var nonce = bytes.slice(24, 36);
    var ciphertext = bytes.slice(36);
    return deriveKey(password, salt).then(function (key) {
      return window.crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce }, key, ciphertext);
    });
  }

  function guessMime(path, kind) {
    if (kind === "video") {
      var ext = (path.split(".").pop() || "").toLowerCase();
      if (ext === "webm") return "video/webm";
      if (ext === "mov") return "video/quicktime";
      if (ext === "ogv") return "video/ogg";
      return "video/mp4";
    }
    var ext = (path.split(".").pop() || "").toLowerCase();
    if (ext === "png") return "image/png";
    if (ext === "gif") return "image/gif";
    if (ext === "webp") return "image/webp";
    return "image/jpeg";
  }

  function hydrateEncryptedMedia(container, password) {
    var nodes = container.querySelectorAll("[data-encrypted-src]");
    if (!nodes.length || !password || !window.crypto || !window.crypto.subtle) {
      return Promise.resolve();
    }
    return Promise.all(
      Array.prototype.map.call(nodes, function (node) {
        var encSrc = node.getAttribute("data-encrypted-src");
        if (!encSrc) return Promise.resolve();
        return fetch(encSrc)
          .then(function (resp) {
            if (!resp.ok) throw new Error("fetch failed");
            return resp.arrayBuffer();
          })
          .then(function (buf) {
            return decryptAsset(buf, password);
          })
          .then(function (plain) {
            var kind = node.getAttribute("data-media-kind") || "image";
            var logicalSrc = encSrc.replace(/\.enc$/, "");
            var blob = new Blob([plain], { type: guessMime(logicalSrc, kind) });
            var url = URL.createObjectURL(blob);
            node.removeAttribute("hidden");
            node.src = url;
          });
      })
    );
  }

  document.querySelectorAll("[data-gallery-lock]").forEach(function (lock) {
    setupPasswordLock(lock, {
      hashAttr: "data-gallery-password-hash",
      formSelector: "[data-gallery-unlock]",
      contentSelector: "[data-gallery]",
      storageKey: function (hash) {
        return "xuanxin-gallery:" + hash;
      },
    });
  });

  document.querySelectorAll("[data-entry-lock]").forEach(function (lock) {
    setupPasswordLock(lock, {
      hashAttr: "data-entry-password-hash",
      formSelector: "[data-entry-unlock]",
      contentSelector: "[data-entry-body]",
      storageKey: function (hash) {
        return "xuanxin-entry:" + window.location.pathname + ":" + hash;
      },
      afterUnlock: function (body) {
        typesetMath(body);
      },
    });
  });

  document.querySelectorAll("[data-gallery]").forEach(function (gallery) {
    var track = gallery.querySelector(".xuanxin-gallery-track");
    var slides = gallery.querySelectorAll(".xuanxin-gallery-slide");
    var prevBtn = gallery.querySelector("[data-gallery-prev]");
    var nextBtn = gallery.querySelector("[data-gallery-next]");
    var indicator = gallery.querySelector("[data-gallery-indicator]");
    var captionBar = gallery.querySelector("[data-gallery-caption-bar]");
    if (!track || !slides.length) return;

    var current = 0;
    var total = slides.length;

    function collapseCaption() {
      if (captionBar) captionBar.setAttribute("aria-expanded", "false");
    }

    function syncCaption() {
      if (!captionBar) return;
      var caption = slides[current].getAttribute("data-caption") || "";
      if (!caption) {
        captionBar.hidden = true;
        captionBar.textContent = "";
        collapseCaption();
        return;
      }
      captionBar.hidden = false;
      captionBar.textContent = caption;
      captionBar.setAttribute("aria-label", caption);
      collapseCaption();
    }

    if (captionBar) {
      captionBar.addEventListener("click", function () {
        var expanded = captionBar.getAttribute("aria-expanded") === "true";
        captionBar.setAttribute("aria-expanded", expanded ? "false" : "true");
      });
    }

    function update() {
      collapseCaption();
      track.style.transform = "translateX(-" + (current * 100) + "%)";
      if (indicator) indicator.textContent = (current + 1) + " / " + total;
      if (prevBtn) prevBtn.disabled = current === 0;
      if (nextBtn) nextBtn.disabled = current === total - 1;
      syncCaption();
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        if (current > 0) {
          current -= 1;
          update();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        if (current < total - 1) {
          current += 1;
          update();
        }
      });
    }

    update();
  });
})();
