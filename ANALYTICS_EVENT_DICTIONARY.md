# Analytics Event Dictionary

The custom event layer is implemented in `assets/js/analytics-events.js`. It sends events only when GA4's `gtag` function is present. Without a real GA4 Measurement ID, the script is a no-op.

## Shared Parameters

- `page_path`: current path only, without query string or hash
- `content_type`: broad page or asset type
- `link_type`: link category when relevant
- `campaign_category`: whitelisted `utm_campaign` when present, otherwise whitelisted `utm_source`, otherwise `none`
- `outbound_path`: origin plus path for non-sensitive external links; query strings and hashes are removed

No event stores professor names, professor emails, visitor identifiers, IP-derived custom identifiers, fingerprints, raw email addresses, or personal tracking tokens.

## Events

| Event | Trigger | Page | Parameters | Interpretation | Limitations |
| --- | --- | --- | --- | --- | --- |
| `cv_page_view` | Page load | `/cv.html`, `/zh/cv.html` | `page_path`, `content_type`, `campaign_category` | Visitor reached the CV page. | Does not prove CV was read. |
| `cv_download` | Click on `Ran_Wang_CV_Public.pdf` | Any page | `page_path`, `content_type`, `link_type`, `campaign_category` | Visitor clicked the public CV PDF. | Browser or network settings may prevent GA delivery. |
| `research_profile_download` | Click on `Ran_Wang_Research_Collaboration_Profile.pdf` | Any page | `page_path`, `content_type`, `link_type`, `campaign_category` | Visitor clicked the research profile PDF. | Does not prove the PDF was fully read. |
| `publication_page_view` | Page load | `/publications.html`, `/zh/publications.html` | `page_path`, `content_type`, `campaign_category` | Visitor reached the publications index. | Not equivalent to paper-level engagement. |
| `paper_view` | Page load | `/papers/*.html`, `/zh/papers/*.html` | `page_path`, `content_type`, `campaign_category` | Visitor reached a paper or project detail page. | Does not identify which person visited. |
| `research_page_view` | Page load | `/research.html`, `/zh/research.html` | `page_path`, `content_type`, `campaign_category` | Visitor reached the research overview page. | Page visibility duration is not measured here. |
| `project_page_view` | Page load | `/projects.html`, `/zh/projects.html` | `page_path`, `content_type`, `campaign_category` | Visitor reached the project redirect/overview page. | Current project content may live mainly under Research. |
| `github_click` | Click on `github.com/Olivia-wr-research` | Any page | `page_path`, `content_type`, `link_type`, `campaign_category` | Visitor clicked the GitHub profile link. | GitHub traffic must be checked separately in GitHub Insights. |
| `code_repository_click` | Click on `github.com/Olivia-wr-research/author-institution-city-linkage` | Any page | `page_path`, `content_type`, `link_type`, `campaign_category` | Visitor clicked the public code repository link. | Does not prove the repository was browsed after click. |
| `contact_email_click` | Click on `mailto:` | Any page | `page_path`, `content_type`, `link_type`, `campaign_category` | Visitor opened an email link. | Email address is not sent as an event parameter. |
| `outbound_link_click` | Click on other external links | Any page | `page_path`, `content_type`, `link_type`, `outbound_path`, `campaign_category` | Visitor clicked a non-site external destination. | Query strings and hashes are stripped; no PII attribution. |

## Academic Outreach Funnel

```text
EMAIL SENT
-> WEBSITE VISIT
-> RESEARCH/PUBLICATIONS VIEW
-> CV VIEW
-> CV DOWNLOAD
-> REPLY
-> MEETING
-> FORMAL APPLICATION
-> INTERVIEW
-> OFFER
```

The website analytics layer can only support the first five layers. Replies, meetings, formal applications, interviews, and offers must be tracked outside the website, preferably at batch level.

## Core Limitation

Website analytics cannot prove that a specific professor viewed the site.
