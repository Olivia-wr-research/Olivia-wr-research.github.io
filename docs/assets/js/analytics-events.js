(function () {
  "use strict";

  const allowedCampaignValues = {
    utm_source: new Set(["outreach", "application", "organic", "github", "other"]),
    utm_medium: new Set(["email", "cv", "application_system", "referral"]),
    utm_campaign: new Set(["phd_2027", "ra_2026", "research_collaboration"]),
  };

  const siteHost = "olivia-wr-research.github.io";
  const codeRepositoryPath = "/Olivia-wr-research/author-institution-city-linkage";
  const githubProfilePath = "/Olivia-wr-research";

  function cleanPath(url) {
    try {
      const parsed = new URL(url, window.location.href);
      return parsed.pathname || "/";
    } catch (_error) {
      return window.location.pathname || "/";
    }
  }

  function normalizePath(path) {
    if (!path || path === "/") return "/";
    return path.replace(/\/index\.html$/, "/");
  }

  function campaignCategory() {
    const params = new URLSearchParams(window.location.search || "");
    const campaign = params.get("utm_campaign");
    if (campaign && allowedCampaignValues.utm_campaign.has(campaign)) return campaign;
    const source = params.get("utm_source");
    if (source && allowedCampaignValues.utm_source.has(source)) return source;
    return "none";
  }

  function safeEventParams(extra) {
    return Object.assign({
      page_path: normalizePath(window.location.pathname || "/"),
      campaign_category: campaignCategory(),
    }, extra || {});
  }

  function track(eventName, params) {
    if (!eventName || typeof window.gtag !== "function") return false;
    window.gtag("event", eventName, safeEventParams(params));
    return true;
  }

  function classifyCurrentPage() {
    const path = normalizePath(window.location.pathname || "/");
    if (/^\/zh\/papers\//.test(path) || /^\/papers\//.test(path)) {
      return { event: "paper_view", content_type: "paper" };
    }
    if (path === "/cv.html" || path === "/zh/cv.html") {
      return { event: "cv_page_view", content_type: "cv" };
    }
    if (path === "/publications.html" || path === "/zh/publications.html") {
      return { event: "publication_page_view", content_type: "publications" };
    }
    if (path === "/research.html" || path === "/zh/research.html") {
      return { event: "research_page_view", content_type: "research" };
    }
    if (path === "/projects.html" || path === "/zh/projects.html") {
      return { event: "project_page_view", content_type: "project" };
    }
    return null;
  }

  function safeOutboundPath(anchor) {
    try {
      const parsed = new URL(anchor.href, window.location.href);
      return parsed.hostname === siteHost ? parsed.pathname : parsed.origin + parsed.pathname;
    } catch (_error) {
      return "external";
    }
  }

  function trackPageViewEvents() {
    const pageEvent = classifyCurrentPage();
    if (!pageEvent) return;
    track(pageEvent.event, { content_type: pageEvent.content_type });
  }

  function trackLinkClick(anchor) {
    const href = anchor.getAttribute("href") || "";
    const absoluteHref = anchor.href || href;
    if (!href) return;

    if (href.indexOf("mailto:") === 0) {
      track("contact_email_click", { content_type: "contact", link_type: "mailto" });
      return;
    }

    if (/Ran_Wang_CV_Public\.pdf$/i.test(cleanPath(absoluteHref))) {
      track("cv_download", { content_type: "cv", link_type: "pdf" });
      return;
    }

    if (/Ran_Wang_Research_Collaboration_Profile\.pdf$/i.test(cleanPath(absoluteHref))) {
      track("research_profile_download", { content_type: "research_profile", link_type: "pdf" });
      return;
    }

    let parsed;
    try {
      parsed = new URL(absoluteHref, window.location.href);
    } catch (_error) {
      return;
    }

    if (parsed.hostname === "github.com") {
      const githubPath = parsed.pathname.replace(/\/$/, "");
      if (githubPath === codeRepositoryPath) {
        track("code_repository_click", { content_type: "code_repository", link_type: "github" });
      } else if (githubPath === githubProfilePath) {
        track("github_click", { content_type: "github_profile", link_type: "github" });
      } else {
        track("outbound_link_click", { content_type: "external", link_type: "github", outbound_path: safeOutboundPath(anchor) });
      }
      return;
    }

    if (parsed.hostname && parsed.hostname !== window.location.hostname) {
      track("outbound_link_click", { content_type: "external", link_type: "external", outbound_path: safeOutboundPath(anchor) });
    }
  }

  function setupClickTracking() {
    document.addEventListener("click", function (event) {
      const anchor = event.target && event.target.closest ? event.target.closest("a[href]") : null;
      if (!anchor) return;
      trackLinkClick(anchor);
    }, { capture: true, passive: true });
  }

  document.addEventListener("DOMContentLoaded", function () {
    trackPageViewEvents();
    setupClickTracking();
  });

  window.rwAnalyticsTrack = track;
  window.rwAnalyticsClassifyCurrentPage = classifyCurrentPage;
}());
