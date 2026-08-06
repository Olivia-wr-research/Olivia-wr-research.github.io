(function () {
  function counterpartHref(label) {
    var path = window.location.pathname || "/";
    var file = path.split("/").filter(Boolean).pop() || "index.html";
    if (file === "zh") file = "index.html";
    if (label === "中文") {
      return file === "index.html" ? "/zh/" : "/zh/" + file;
    }
    if (label === "English") {
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
