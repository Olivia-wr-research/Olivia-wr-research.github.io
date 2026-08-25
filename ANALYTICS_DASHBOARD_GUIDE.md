# Analytics Dashboard Guide

Do not publicly embed a Google Analytics dashboard on the personal website. Use GA4 privately.

## Acquisition

In GA4, review:

- users
- sessions
- source / medium
- campaign

Use these views to compare outreach batches, application-system visits, GitHub referrals, and organic visits.

## Engagement

Review:

- landing pages
- page views
- Publications page views
- CV page views
- Research page views
- paper detail page views

Use page-level patterns to see whether visitors move from the homepage to research evidence, publications, and CV materials.

## Events

Review custom events:

- `cv_download`
- `research_profile_download`
- `publication_page_view`
- `paper_view`
- `research_page_view`
- `github_click`
- `code_repository_click`
- `contact_email_click`

## Geography

Use GA4's standard geography reports:

- country
- city only if GA4 already provides it

Do not add custom geolocation, IP storage, fingerprinting, or person-level tracking.

## Outreach Campaigns

Compare only batch-level categories:

- domestic versus overseas
- science-of-science versus management versus economics
- PhD versus RA
- research collaboration versus application-oriented outreach

## GitHub Traffic

GitHub repository traffic is available from:

```text
GitHub repository -> Insights -> Traffic
```

GitHub repository traffic is not the same as GitHub Pages website traffic. Do not treat GitHub stars, watchers, or repository views as website visitors.

## Live Verification

After the real GA4 Measurement ID is added and the site is deployed, use GA4 Realtime and browser developer tools to confirm page views and custom events. Until then, the correct status is:

```text
STATIC_INTEGRATION_PASS
LIVE_ANALYTICS_VERIFICATION_PENDING
```
