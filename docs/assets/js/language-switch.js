(function () {
  var links = document.querySelectorAll('.navbar a.nav-link, .navbar a.dropdown-item');
  links.forEach(function (link) {
    var label = (link.textContent || '').trim();
    if (label === '中文') link.setAttribute('href', '/zh/');
    if (label === 'English') link.setAttribute('href', '/index.html');
  });
}());
