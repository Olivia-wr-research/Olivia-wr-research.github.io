# NextPosition · 下一站

Research opportunities, local CV-assisted exploration, research-unit evidence and application planning.

[Open the app](https://olivia-wr-research.github.io/apps/application-board/) · [中文说明](README.zh-CN.md) · [0.6 release and limits](docs/RELEASE_06.md) · [Matching method](docs/MATCHING.md)

## Explore without knowing your interests first

- Browse 75 employer advertisements across 5 countries, compiled 2026-10-16. These are source-based records, not a live or comprehensive European index. An advertisement with two places is counted once.
- Start from guided topic/method checkboxes, or locally read a text-layer PDF/DOCX/TXT/Markdown CV and review candidate tags. No raw CV transmission or storage; no model calls. PDF parsing is local using bundled PDF.js; scans/OCR remain unsupported. Files are capped at 5 MB, PDFs at 20 pages.
- Inspect 6 research-unit evidence entries (institutes, project and group explicitly distinguished) and related snapshot links. Graduate outcomes, funding continuity and publication metrics are unknown, not fabricated rankings.
- Compare up to 3 jobs, inspect requirements and restrictions, save to the preserved browser-local application tracker at `tracker.html`.
- Use 5 official external source portals when the small snapshot does not cover your needs. External jobs are not added to this product's counts.

## Matching is not admission prediction

Results are ordered by the number of shared topic/method tags, not an admission score. Cards show intersections and separate unknowns/attention items, not an admission score. No input means no invented fit. CV mentions do not prove experience or interest; users confirm candidate labels. Degree, language, mobility, funding and professional requirements still require employer verification. No identity, degree or language proficiency is inferred from the CV.

## Run and test

Python 3.11+ (no runtime Python dependencies), Node 22+ for tests:

```sh
python3 server.py
# open http://127.0.0.1:8907/
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
```

JavaScript and Python regression tests cover matching, file bounds, stored/deflated synthetic DOCX, rejection cases, source associations, storage and the loopback launcher. Browser checks use synthetic files only. PDF evidence is shown as controlled trigger phrases, with no automatic selection of interests. Engineering tests are not a real-user study, eligibility assessment, security certification or CV accuracy benchmark.

## Privacy and release boundary

Confirmed tags and application records remain **unencrypted in the current browser origin/profile**. Same-origin code and shared browser profiles are trusted. Back up private application records from the tracker. Clearing browser data can erase them. CV raw text is held in form memory only, cleared after extraction/close and never included in backups. No accounts, cloud applicant database, analytics, automatic email/application or payments. Static hosting receives ordinary asset requests; opening external employer links visits those sites under their policies.

Original private application systems and unpublished research remain untouched. No private CV, contact list, manuscript or personal application records are bundled. No reference-site database, paywalled reports, artwork or code is mirrored. Code is MIT licensed and AI-assisted; employer materials retain their rights. See [security](SECURITY.md) and [role-based release review](docs/RELEASE_05.md).
