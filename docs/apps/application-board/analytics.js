/* Anonymous, minimal telemetry for 远境 TERRAFAR.
   Shares the existing Umami Cloud Website ID with 后会友期; the project is
   distinguished by its URL prefix, script tag and terrafar_* event names.
   No CV text, search query, profile values, application records, or IDs are sent.
   Analytics is optional: blocked trackers must never affect site functionality.
*/
(() => {
  'use strict';
  const HOST = 'olivia-wr-research.github.io';
  const PATH = '/apps/application-board/';
  const WEBSITE_ID = 'eb5fafdb-5785-44d4-a4c0-00cfc6072304';
  const enabled = location.hostname === HOST && location.pathname.startsWith(PATH);
  if (!enabled) return;

  const events = new Set([
    'terrafar_guide_start',
    'terrafar_cv_start',
    'terrafar_groups_start',
    'terrafar_search_used',
    'terrafar_compare_clicked',
    'terrafar_tracker_open',
    'terrafar_job_detail_open',
    'terrafar_job_saved',
    'terrafar_job_unsaved',
    'terrafar_profile_saved',
    'terrafar_tracker_record_added'
  ]);
  let queued = [];
  function track(name) {
    if (!events.has(name)) return;
    if (window.umami && typeof window.umami.track === 'function') {
      try {
        const result = window.umami.track(name);
        if (result && typeof result.catch === 'function') result.catch(() => {});
      } catch (_) { /* Never affect the product. */ }
    } else if (queued.length < 24) {
      queued.push(name);
    }
  }
  window.terrafarAnalytics = Object.freeze({ track });

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://cloud.umami.is/script.js';
  script.setAttribute('data-website-id', WEBSITE_ID);
  script.setAttribute('data-domains', HOST);
  script.setAttribute('data-tag', 'terrafar');
  script.setAttribute('data-exclude-search', 'true');
  script.setAttribute('data-exclude-hash', 'true');
  script.setAttribute('data-do-not-track', 'true');
  script.onload = () => {
    const pending = queued;
    queued = [];
    for (const name of pending) track(name);
  };
  script.onerror = () => { queued = []; };
  document.head.appendChild(script);

  const buttonEvents = new Map([
    ['guide-start', 'terrafar_guide_start'],
    ['cv-start', 'terrafar_cv_start'],
    ['groups-start', 'terrafar_groups_start'],
    ['compare-open', 'terrafar_compare_clicked']
  ]);
  document.addEventListener('click', event => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const button = target.closest('button');
    if (button && !button.disabled) {
      const name = buttonEvents.get(button.id);
      if (name) track(name);
    }
    const link = target.closest('a[href]');
    if (link) {
      try {
        const href = new URL(link.getAttribute('href'), location.href);
        if (href.origin === location.origin && href.pathname === PATH + 'tracker.html') {
          track('terrafar_tracker_open');
        }
      } catch (_) { /* Ignore malformed unrelated URLs. */ }
    }
  }, true);

  let searchRecorded = false;
  document.addEventListener('input', event => {
    const el = event.target;
    if (!searchRecorded && el && el.id === 'search' && el.value && el.value.trim()) {
      searchRecorded = true;
      track('terrafar_search_used'); // Never send the search text.
    }
  });
})();
