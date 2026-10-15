# Application Board

**An application workspace you own: opportunities, material checklists and progress, without handing over your CV or inbox.**

A new public-facing implementation inspired by a private PhD/RA application dashboard. It does **not** import, wrap or run that private system. No personal application data or original applicant profile is included.

## Browser-local hosted edition

The same four static files can be hosted without a data server. The portfolio's GitHub Pages copy is at [Application Board](https://olivia-wr-research.github.io/apps/application-board/). Each visitor gets their own browser-local workspace, not a shared application database. Loading the hosted page contacts the hosting provider for static assets; application records are not uploaded by the app. Browser extensions, other same-origin code and people sharing your browser profile remain part of your trust boundary. The local launcher below is available if you prefer not to use hosted assets.

## Run

Python 3.11+; no installation or Python dependencies:

```sh
python3 server.py
```

Open **http://127.0.0.1:8907/**. The workspace starts empty. “Try fictional examples” works only in an empty workspace and contains no real vacancies, applicants or funding claims.

## What works

- Add and edit PhD, doctoral researcher, RA, Predoc or other opportunities.
- Search and filter by stage/country; view date-only deadlines and a 14-day queue.
- Maintain a material-name checklist with missing/draft/ready states.
- Manually update application stages and inspect local activity history.
- Persist in browser local storage; export/import JSON backups and export spreadsheet-safe CSV.
- Import validation rejects malformed records, duplicate IDs and conflicts with existing records instead of overwriting them.

## “Many people can use it” — the precise boundary

Different people can download the same code and run independent workspaces on their own machines/browser profiles. This first release is **not a hosted multi-tenant service**: no accounts, server database, sync, sharing, authentication or authorization boundary exists. People sharing the same browser profile and origin share its workspace.

Storage is tied to the exact scheme/hostname/port. Use the same URL each time. Changing `127.0.0.1` to `localhost` or changing ports creates a different browser storage area; export a backup before moving. Browser data clearing can erase records.

Data is **not encrypted**. Backups and CSVs can contain private notes. Store them privately. The server serves four allowlisted static files and has no data API; the app has no telemetry, external scripts, model calls, email integration, scraping or automatic submission. Opening a source link navigates to that external website.

## What this release intentionally does not do

No CV/document uploads, recommender/contact database, private-paper processing, account credentials, official deadline verification, eligibility judgments, opportunity recommendations or automatic applications. A checkbox records only that **you** checked a source. A “submitted” stage is a manual note, not proof of an external submission. Activity history is editable local backup data, not a signed audit trail.

Capacity is bounded to 500 opportunities, 30 checklist items and 500 activity entries per record, and a 1.5 MB serialized workspace. Save/import failures do not replace the prior stored data. Do not treat this early release as your only copy of important application records. No claim of broad browser compatibility, security certification or real-user validation is made.

## Checks

Node.js 20+ is needed only for tests:

```sh
node --test tests/core.test.mjs
python3 -m unittest discover -s tests -v
```

See [中文说明](README.zh-CN.md) and [privacy/security boundaries](SECURITY.md). MIT licensed. This public implementation and documentation were prepared with AI assistance. The original private application system remains untouched.
