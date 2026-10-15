# NextPosition · 下一站

**Discover doctoral opportunities, understand the overlap, and check the gaps before applying.**

[Open the app](https://olivia-wr-research.github.io/apps/application-board/) · [中文说明](README.zh-CN.md) · [Matching and sources](docs/MATCHING.md)

## v0.2: discovery first

The Chinese homepage replaces the earlier planning-only layout with searchable vacancy cards, country/field/deadline filters, local research-interest profiles, explainable keyword scores, separate eligibility-review notes and bookmarks. The original material/progress workspace remains at `tracker.html`. Its existing browser storage key is preserved.

The default dataset is **nine manually curated original-employer snapshots across two countries**, checked on 2026-10-15. It is not a live feed or a comprehensive European job index. Every record links to the employer page. Titles and short summaries are this project's own Chinese paraphrases. No reference-radar dataset, page code, brand, paywalled content or salary estimates were copied.

## Matching is not an admission probability

Enter only broad public/non-confidential interests and methods, optionally degree level, English readiness and preferred countries. No CV or identity is required. A bounded bilingual vocabulary measures interest overlap (70%) and method overlap (30%); missing components are not invented. No profile means no score.

Degree, language, deadline and country-preference checks stay separate. A high keyword score can coexist with a degree gap, unknown language evidence or special restrictions. The app does not determine eligibility, evaluate applicant quality or submit anything. Read the [exact method and limitations](docs/MATCHING.md).

## Local run

Python 3.11+, no installation or runtime Python dependencies:

```sh
python3 server.py
```

Open http://127.0.0.1:8907/. Hosted and local versions use separate browser storage. Search/filter, profile save, vacancy details, matching explanations and bookmarks work locally. Bookmarks join the old application checklist without overwriting existing IDs. Your own vacancy snapshots can be exported/imported using the exported JSON schema; imported facts are labelled unverified.

## Privacy

Profiles and application records stay **unencrypted in this browser profile/origin**. Shared profiles and other same-origin code are in the trust boundary. Clearing browser data can erase records. Export private application backups from the tracker; profile export/sync is not implemented. There are no accounts, cloud applicant database, CV uploads, analytics, model calls, automatic emails or applications. Hosting receives normal static-asset requests.

The personal dashboard that inspired this work remains private and untouched. No private application data, contact list, paper or applicant profile was bundled. This is a new general-purpose public implementation, not the full private system and not an authenticated multi-tenant SaaS.

## Checks

Node 20+ is needed only for tests:

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
```

44 JavaScript tests plus 8 Python launcher tests. Real-browser checks used a fictional profile to verify scoring, degree gaps and bookmark persistence in the local workspace. See [QA boundaries](docs/QA.md) and [security](SECURITY.md).

MIT licensed code, AI-assisted implementation. Employer content and the reference product retain their own rights. No user adoption, calibrated fit accuracy, production security or comprehensive vacancy coverage is claimed.

See [release 0.3](docs/RELEASE_03.md) for the discovery-first pilot, new sources and verification limits.
