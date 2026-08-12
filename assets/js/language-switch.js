(function () {
  function counterpartHref(label) {
    var path = window.location.pathname || "/";
    var file = path.split("/").filter(Boolean).pop() || "index.html";
    var isEnglishPaper = path.indexOf("/papers/") === 0;
    var isChinesePaper = path.indexOf("/zh/papers/") === 0;
    var isChineseRoot = path === "/zh" || path === "/zh/";
    if (file === "zh") file = "index.html";
    if (label === "中文") {
      if (isEnglishPaper) return "/zh/papers/" + file;
      return file === "index.html" ? "/zh/" : "/zh/" + file;
    }
    if (label === "English") {
      if (isChinesePaper) return "/papers/" + file;
      if (isChineseRoot) return "/";
      return file === "index.html" ? "/" : "/" + file;
    }
    return null;
  }

  var links = document.querySelectorAll('.navbar a.nav-link, .navbar a.dropdown-item');
  links.forEach(function (link) {
    var label = (link.textContent || '').trim();
    var href = counterpartHref(label);
    if (href) link.setAttribute('href', href);
  });
}());
