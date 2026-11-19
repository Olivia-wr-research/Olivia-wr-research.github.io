/* Anonymous usage telemetry for 后会友期 V6 (Umami Cloud).
   To activate, set WEBSITE_ID to the UUID shown under Umami > Websites > Tracking code.
   The user's Umami account currently has no configured website; leave this blank until verified.
   No cookies, account IDs, uploaded photos, quiz answers or free text are sent by our event hooks.
*/
(() => {
  'use strict';
  const WEBSITE_ID = '';
  const HOST = 'olivia-wr-research.github.io';
  const APP_PREFIX = '/apps/houhuiyouqi-quiz/';
  const VALID_ID = /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;
  const allowed = new Set([
    'quiz_start', 'quiz_complete', 'poster_view_requested',
    'poster_generated', 'share_clicked', 'share_copy_requested', 'share_native_completed'
  ]);
  const enabled = location.hostname === HOST &&
    location.pathname.startsWith(APP_PREFIX) &&
    !location.pathname.includes('/v6-test/') &&
    VALID_ID.test(WEBSITE_ID);
  let queue = [];
  let loaded = false;
  function send(name) {
    if (!enabled || !allowed.has(name)) return;
    if (loaded && window.umami && typeof window.umami.track === 'function') {
      try {
        const sent = window.umami.track(name);
        if (sent && typeof sent.catch === 'function') sent.catch(() => {});
      } catch (_) { /* Analytics never interrupts the quiz. */ }
    } else if (queue.length < 16) queue.push(name);
  }
  window.hhyqAnalytics = Object.freeze({ track: send, enabled: () => enabled });
  if (!enabled) return;
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://cloud.umami.is/script.js';
  script.setAttribute('data-website-id', WEBSITE_ID);
  script.setAttribute('data-domains', HOST);
  script.setAttribute('data-exclude-search', 'true');
  script.setAttribute('data-exclude-hash', 'true');
  script.setAttribute('data-do-not-track', 'true');
  script.onload = () => {
    loaded = true;
    const pending = queue; queue = [];
    for (const event of pending) send(event);
  };
  script.onerror = () => { queue = []; };
  document.head.appendChild(script);
})();
