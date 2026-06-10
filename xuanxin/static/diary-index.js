/** Diary index language toggle (works on file:// without sessionStorage). */
(function () {
  "use strict";

  var langToggle = document.querySelector("[data-diary-lang-toggle]");
  if (!langToggle) return;

  var items = document.querySelectorAll("[data-lang-entries]");
  var labels = { en: "English", zh: "中文" };

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

  function updateToggle(lang) {
    var target = otherLang(lang);
    langToggle.textContent = labels[target] || target.toUpperCase();
    langToggle.setAttribute("data-current-lang", lang);
    langToggle.setAttribute(
      "aria-label",
      lang === "zh" ? "Switch to English" : "切换到中文"
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
