/**
 * Diary share bar: LinkedIn / X links, copy link, WeChat QR code, native share sheet.
 */
(function () {
  "use strict";

  var bar = document.querySelector("[data-share]");
  if (!bar) return;

  var url = bar.dataset.shareUrl || location.href.split("#")[0];
  var title = bar.dataset.shareTitle || document.title;
  var enc = encodeURIComponent;

  var linkedin = bar.querySelector("[data-share-linkedin]");
  if (linkedin) linkedin.href = "https://www.linkedin.com/sharing/share-offsite/?url=" + enc(url);
  var x = bar.querySelector("[data-share-x]");
  if (x) x.href = "https://twitter.com/intent/tweet?url=" + enc(url) + "&text=" + enc(title);

  var copyBtn = bar.querySelector("[data-share-copy]");
  if (copyBtn) {
    var copyLabel = copyBtn.textContent;
    copyBtn.addEventListener("click", function () {
      var done = function () {
        copyBtn.textContent = bar.dataset.copiedLabel || "Copied";
        setTimeout(function () { copyBtn.textContent = copyLabel; }, 1500);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(url).then(done, function () { window.prompt("", url); });
      } else {
        window.prompt("", url);
      }
    });
  }

  var nativeBtn = bar.querySelector("[data-share-native]");
  if (nativeBtn && navigator.share) {
    nativeBtn.hidden = false;
    nativeBtn.addEventListener("click", function () {
      navigator.share({ title: title, url: url }).catch(function () {});
    });
  }

  var wechatBtn = bar.querySelector("[data-share-wechat]");
  var panel = bar.querySelector("[data-share-qr]");
  if (!wechatBtn || !panel) return;

  function renderQr() {
    var holder = panel.querySelector("[data-share-qr-code]");
    if (holder.firstChild) return;
    qrcode.stringToBytes = qrcode.stringToBytesFuncs["UTF-8"];
    var qr = qrcode(0, "M");
    qr.addData(url);
    qr.make();
    holder.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 2, scalable: true });
  }

  function loadQrLib(callback) {
    if (window.qrcode) return callback();
    var script = document.createElement("script");
    script.src = bar.dataset.qrSrc;
    script.onload = callback;
    document.head.appendChild(script);
  }

  wechatBtn.addEventListener("click", function () {
    var open = panel.hidden;
    panel.hidden = !open;
    wechatBtn.setAttribute("aria-expanded", String(open));
    if (open) loadQrLib(renderQr);
  });

  document.addEventListener("click", function (event) {
    if (!panel.hidden && !bar.contains(event.target)) {
      panel.hidden = true;
      wechatBtn.setAttribute("aria-expanded", "false");
    }
  });
})();
