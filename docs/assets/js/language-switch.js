(function () {
  var mapToZh = {
    '/': '/zh/',
    '/index.html': '/zh/',
    '/research.html': '/zh/research.html',
    '/publications.html': '/zh/publications.html',
    '/projects.html': '/zh/projects.html',
    '/cv.html': '/zh/cv.html',
    '/contact.html': '/zh/contact.html'
  };
  var mapToEn = {
    '/zh/': '/',
    '/zh/index.html': '/',
    '/zh/research.html': '/research.html',
    '/zh/publications.html': '/publications.html',
    '/zh/projects.html': '/projects.html',
    '/zh/cv.html': '/cv.html',
    '/zh/contact.html': '/contact.html'
  };
  var path = window.location.pathname;
  var links = document.querySelectorAll('.navbar a.nav-link, .navbar a.dropdown-item');
  links.forEach(function (link) {
    var label = (link.textContent || '').trim();
    if (label === '中文' && mapToZh[path]) link.setAttribute('href', mapToZh[path]);
    if (label === 'EN' && mapToEn[path]) link.setAttribute('href', mapToEn[path]);
  });
}());
