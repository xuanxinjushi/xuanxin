/** Diary index language toggle (works on file:// without sessionStorage). */
(function () {
  "use strict";

  var langToggle = document.querySelector("[data-diary-lang-toggle]");
  if (!langToggle) return;

  var items = document.querySelectorAll("[data-lang-entries]");
  var labels = { en: "English", zh: "中文" };
  var uiByLang = window.XUANXIN_DIARY_UI || {};

  function pickEntry(entries, lang) {
    if (entries[lang]) return entries[lang];
    if (entries.en) return entries.en;
    var keys = Object.keys(entries);
    return keys.length ? entries[keys[0]] : null;
  }

  function otherLang(lang) {
    return lang === "zh" ? "en" : "zh";
  }

  function readLang() {
    return langToggle.getAttribute("data-current-lang") || "en";
  }

  function uiText(lang, key) {
    var pack = uiByLang[lang];
    return pack && pack[key] ? pack[key] : "";
  }

  function formatIndexCount(lang) {
    var el = document.querySelector("[data-diary-index-count]");
    if (!el) return;
    var total = Number(el.getAttribute("data-total") || "0");
    var page = Number(el.getAttribute("data-page") || "1");
    var totalPages = Number(el.getAttribute("data-total-pages") || "1");
    var unit = total === 1 ? uiText(lang, "entries_one") : uiText(lang, "entries_many");
    var text = total + " " + unit;
    if (totalPages > 1) {
      text += uiText(lang, "page_of")
        .replace("{page}", String(page))
        .replace("{total}", String(totalPages));
    }
    el.textContent = text;
  }

  function applyChrome(lang) {
    document.querySelectorAll("[data-diary-ui]").forEach(function (el) {
      var key = el.getAttribute("data-diary-ui");
      var text = uiText(lang, key);
      if (text) el.textContent = text;
    });
    formatIndexCount(lang);
  }

  function updateToggle(lang) {
    var target = otherLang(lang);
    langToggle.textContent = labels[target] || target.toUpperCase();
    langToggle.setAttribute("data-current-lang", lang);
    langToggle.setAttribute(
      "aria-label",
      uiText(lang, "switch_to").replace("{label}", labels[target] || target.toUpperCase())
    );
    document.documentElement.lang = lang === "zh" ? "zh-Hans" : "en";
    document.body.classList.toggle("diary-index-lang-zh", lang === "zh");
  }

  function applyLang(lang) {
    items.forEach(function (item) {
      var link = item.querySelector("[data-diary-entry-link]");
      var titleEl = item.querySelector("[data-diary-entry-title]");
      if (!link) return;
      var entries;
      try {
        entries = JSON.parse(item.getAttribute("data-lang-entries") || "{}");
      } catch (err) {
        return;
      }
      var row = pickEntry(entries, lang);
      if (!row) return;
      link.setAttribute("href", row.href);
      if (titleEl && row.title) titleEl.textContent = row.title;
    });
    applyChrome(lang);
    updateToggle(lang);
    try {
      sessionStorage.setItem("xuanxin-diary-index-lang", lang);
    } catch (err) {}
  }

  var initial = "en";
  try {
    initial = sessionStorage.getItem("xuanxin-diary-index-lang") || "en";
  } catch (err) {}
  applyLang(initial);

  langToggle.addEventListener("click", function () {
    applyLang(otherLang(readLang()));
  });
})();
