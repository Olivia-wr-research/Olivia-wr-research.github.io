# TERRAFAR launch-readiness content review

Observed on 2026-10-23 UTC by the `opportunity_verifier` subagent using the installed `terrafar-source-audit` Skill. This is a content review and pending-data preview, not a statement that the employer portal currently accepts applications. No form was submitted and no official website data was written or published.

## Official-page observations

The ETH AI Center's official fellowship page was fetched again on 2026-10-24. Its SHA-256 remains `0378110aac5eb00c15261c0072c690f45dd9f31f6501923c9a5d9a4dd1e8fbf2`; the posted rate-5 salary figures and 2026-10-27 16:00 CET deadline are unchanged. The job detail page was also fetched again; the body hash changed to `bfa5bf2bb8a4ad3374f7e6dcbcb11a03cd0a8623a1471dcd1c288ead4552427d` because its per-response CSRF token changed. The deadline and eligibility text remained consistent in the current page read. Neither page establishes current acceptance by the linked application portal.

| Record | Official detail observation | Verified details | Application route and current status |
|---|---|---|---|
| ETH AI Center Doctoral Fellowship 2027 (`eth-ai-12136`) | [ETH job detail](https://jobs.ethz.ch/job/view/12136), 2026-10-23 12:21:32–12:21:35 UTC; SHA-256 `b4fd5fe3dad28008c74381449794afeb1e6fc2754f6e720b83fa81dbcff95fb1` | Deadline 2026-10-27 at 16:00 CET. Master's-level entry in listed quantitative/technical fields, ETH doctoral admission requirements and research-level English. The job detail supports eligibility and deadline. Exact 100% rate 5 salary amounts (CHF 73,100 / 78,300 / 83,500 in years 1–3) are supported by the separate [ETH AI Center Doctoral Fellowships page](https://ai.ethz.ch/research/phd-and-postdoc-programs/phd-fellowships.html), fetched 2026-10-23 18:21:38 UTC; SHA-256 `0378110aac5eb00c15261c0072c690f45dd9f31f6501923c9a5d9a4dd1e8fbf2`. | [Recruitee form](https://switzerland.recruitee.com/o/eth-ai-center-doctoral-fellowship-2027) fetched 2026-10-23 18:21:31 UTC (HTTP 200); body SHA-256 `8aaf1356bb6bf016ca00fd572f0d962b319a8b0ee18e76e71fd55e67514eb77b`. Form fields were present, but the captured page did not explicitly confirm current acceptance. No submission. Current portal acceptance remains **unknown**; the announcement deadline and the portal's acceptance state are tracked separately. |
| Vienna University VINAR (`vienna-6233`) | [University of Vienna job detail](https://jobs.univie.ac.at/job/University-assistant-predoctoral-Vienna-Network-for-Atmospheric-Research-(VINAR)/1447669433/), 2026-10-23 12:21:20–12:21:32 UTC; SHA-256 `4dc7c088d7b929655c83402c6b65627f1184037f67c3aec7c2b247586483a25c` | Official deadline 2026-10-31 (the formal snapshot said 2026-10-24). 30 hours/week. €3,776.10 gross/month is the full-time reference, paid 14 times/year; the actual prorated 30-hour amount is not stated. Physics or related aerosol/atmospheric master's background, C1 English and programming skills. | Apply-now linked to the job-specific route but redirected to the general careers home page. The job form and current acceptance remain **unknown**. |
| ETH PhD Position in Atmospheric Chemistry (`eth-86a50882f2d1`) | [ETH job detail](https://jobs.ethz.ch/job/view/JOPG_ethz_UtuGzrXTpseTskgjY9), 2026-10-23 12:21:45–12:21:46 UTC; SHA-256 `79e65ae6f27f04bc5291c6a3b287cdbc1156fba4bf17f6e7b72caf9966c3e158` | No fixed deadline stated. Evaluation starts 2026-11-15 and continues until filled. Funding secured for four years; projected start March–September 2027. MSc in atmospheric/earth/environmental science, chemistry, physics or related field, atmospheric chemistry experience, programming and English. | [Softfactors route](https://emea2.softfactors.com/job-opening/rgum-UtuGzrXTpseTskgjY9#!/?lang=en) returned a small JavaScript shell without a readable form or status; body SHA-256 `bc6e675731137a3e2fbb6fecaf2f510b60a325da0e87e9e5dd881f265170b2cf`. Current acceptance remains **unknown**. |
| Lund senior lecturer in GIS | [Lund Varbi detail and application route](https://lu.varbi.com/en/what:job/jobID:930481/type:job/where:4/apply:1), 2026-10-23 12:21:35–12:21:42 UTC; SHA-256 `96a83c4a1a9e0467c231855a0a030bb4301405a2c13d6c1dbcd791b0d91e6c3b` | Deadline 2026-11-04; full-time permanent role. Salary amount is not stated. | Application/login page observed 12:22:34–12:22:36 UTC (SHA-256 `c887539ce0d635b52202f484481cdb1a909cd0c8cb1d4e73492a0ee94294d592`). Current acceptance remains **unknown**. |
| University of South Carolina assistant professor in GIScience (`FAC00131PO26`) | [USC job detail](https://uscjobs.sc.edu/postings/213942), 2026-10-23 12:21:42–12:21:45 UTC; SHA-256 `7a70c3ccf3733617c97aa4547c462f13eb4afdc350e9d6f140faf4e63a2a8267` | Listing says “Open Until Filled” and review begins 2026-11-01. Salary is described as competitive; no amount is stated. The listing label does not confirm that the application portal is accepting submissions. | [Application route](https://uscjobs.sc.edu/pre_apply) required login, observed 12:22:36–12:22:39 UTC (SHA-256 `f7a60158da78566cabb9311c3c279be1e1f83d927fc4b6a2aa6de59673b73e71`). Current acceptance remains **unknown**. |

### Limits of the observations

- Five official detail pages were reviewed. These page observations are not five confirmed-open applications.
- The ETH AI, Vienna and ETH Atmospheric Chemistry records each map to a unique existing formal record and have evidence-bound pending patches below. Lund and USC were reviewed as official pages, but no unique matching formal record was staged in this change set.
- No source field was filled from inference. In particular, no fixed date was invented for ETH Atmospheric Chemistry; no prorated Vienna salary or Lund/USC salary amount was inferred; all five records retain current application acceptance as unknown.
- Separate endpoint discovery work found the University of Vienna and UvA list pages paginate (Vienna: 42 results across two 25-item pages; UvA: 27 English entries with 20 per page and additional Dutch results). Those are source-route observations, not full opportunity-content verification and are not counted among the five reviews above.

## Evidence-bound pending data

The preparation script loaded candidate records from the actual Actions artifact `39946276972`, bound each result to its stable candidate ID and content fingerprint, appended review history, and wrote review-only JSON plus branch-local preview JSON. It verified rollback round-trips. The old cross-disciplinary `positions.mjs` is not the data source used by the public homepage, so this change adds an exact-URL active-catalog match before treating a record as displayable.

| Formal record | Pending field change | Stable candidate ID | Review status |
|---|---|---|---|
| `eth-ai-12136` | `funding` and `salary` from the official ETH AI Center fellowship page (SHA-256 `0378110a…e1fbf2`), separate from the job detail's deadline and eligibility | `tcand-97c57c520daa0ba0fdd1e11b` | Verified page content; direct portal acceptance remains unknown |
| `vienna-6233` | Deadline `2026-10-24` → `2026-10-31` | `tcand-cfc80986c8e96017c3258140` | Verified page content; current acceptance unknown |
| `eth-86a50882f2d1` | Funding text specifies four years secured and the March–September 2027 start window | `tcand-180658fc2dd19f7a8aa98180` | Verified page content; no fixed deadline; current acceptance unknown |

Each patch includes the previous value, proposed value, evidence URL/locator/hash, review event ID, and rollback values in `pending-data/`. The matching files under `pending-data/previews/` are branch-only data previews; they do not change the public page or alter its design. Duplicate execution was replayed: Vienna's review history remained at one entry and the patch bytes stayed stable after an unrelated ledger revision.

### Active homepage data path and branch-only correction

The homepage imports `geography-catalog.mjs`, which is built from `geography-opportunities.mjs` and the adjacent catalogue modules; it does not render `positions.mjs`. Exact URL resolution maps the verified atmospheric-chemistry candidate to the single active row `geo-eth-atmosphere`. This PR therefore includes a branch-only correction in the active row and its catalogue review metadata: `checkedAt` advances to 2026-10-23, the item becomes `listed`/unconfirmed rather than “open at last check”, the no-fixed-deadline and 15 November review facts remain, and the official application route is recorded with an explicit unknown acceptance status. Funding and eligibility remain the values supported by the official detail page.

The change is held on this feature branch and has not been merged or deployed. ETH AI and Vienna match the old `positions.mjs` records but have no unique match in the active geography entry module; their evidence-bound patches remain pending and are not presented as homepage data. A local disposable copy of the static homepage was rendered at `http://127.0.0.1:8765/?view=opportunity&id=geo-eth-atmosphere`. Its detail view showed the updated date, unknown acceptance label, verified review date, and official application link. This is a local branch preview, not a GitHub Pages preview URL.

## Expired-deadline display audit

Previously the card styled a past deadline as closed while retaining the original status text; detail, comparison and exports could continue showing the older status label. The shared `opportunityStatusLabel` now returns “deadline passed; current acceptance unknown; recheck official source” for past dates. It is used by cards, details, comparison and TSV/JSON exports. It does not promote a record to open or claim that the employer has closed the role. Layout, styling, navigation, spacing, colors and media are unchanged.

The working diff contains no HTML, CSS, image, icon or layout-file edits. The frozen 26-file visual baseline has four historical HTML hash mismatches (source/dist index and feedback pages); `git diff HEAD` confirms those four files are unchanged by this PR. Source and hosted static copies remain byte-for-byte synchronized.

## Run and scope evidence

The registry currently contains **411** sources; tests also assert retention of the original 264-ID baseline subset and all 133 seed mappings. The latest actual full-registry Actions artifact available for this branch was run **39946276972** (`terrafar-maintenance-39946276972-1`, 2026-10-23 11:28:17–11:28:28 UTC):

| Source-level outcome | Count |
|---|---:|
| Planned | 411 |
| Executed | 10 |
| Complete range checks (`checked_changed`, `checked_unchanged`, `checked_empty`) | 0 |
| Partial | 2 |
| Entry needs locating/adapting | 7 |
| Blocked | 1 |
| Failed | 0 |
| Not attempted | 401 |

The run had 14 endpoint results: 2 `checked_unchanged`, 4 `partial`, 7 `needs_endpoint`, and 1 `blocked`; 27 HTTP request budget units were used. Zero complete checks means no full source range can be claimed from that run. These counts are historical run evidence, not a new all-source run in this change.

The candidate ledger inside that actual artifact held 138 tasks: 122 pending, 6 insufficient-evidence, 10 verified, and no excluded/duplicate decisions. A separate local replay applied the three saved review results (ETH AI, ETH atmospheric chemistry, and the captured Vienna page) to a copy of that ledger. It retained 139 unique tasks: 121 pending, 6 insufficient-evidence, 12 verified, and no excluded/duplicate decisions. The 12 verified-content records all remain queued for current-portal status review because acceptance is unknown; the combined local review queue is 127 content tasks plus 12 current-status tasks. This is a local replay, not a new remote Actions run.

The exact-url active-catalog review path was exercised again against candidate `tcand-180658fc2dd19f7a8aa98180` from run `39946276972`: content status `verified`, active row `geo-eth-atmosphere`, unique URL match, rollback round-trip passed, pending-data preview emitted, formal data writes `false`.

The GitHub Actions maintenance workflow remains on the default branch schedule (`02:17 UTC`, `10:17 Asia/Shanghai`). It is not enabled by this feature-branch change. The workflow files reviewed here declare read-only repository permissions and contain no Pages publish/deploy job. Repository-level Pages settings are not exposed by these workflow files; no settings were changed. The application-board PR workflow only runs Node/Python checks and verifies the hosted static copy against source.

## Validation

- Python after the concurrency, strict-assignment, restore-version, exact-evidence and anti-rollback fixes: `python3 -m unittest discover -s tests -v` — 90 passed.
- Node: `node --test tests/*.test.mjs` — 91 passed.
- `diff -r portfolio/application-board/dist docs/apps/application-board` — passed.
- Python byte-compilation of the five maintenance scripts — passed.
- YAML parsing of both relevant workflow files and `git diff --check` — passed.
- Candidate replay from Actions artifact 39946276972 migrated the candidate ledger from schema v1 to v2 without losing existing tasks; the replayed ledger retained 139 stable candidates after adding the captured VINAR observation. Re-running the VINAR review preserved its single review-history entry. This is a local replay of a historical artifact, not a new remote Actions run.
- The three pending patch files and previews were regenerated from the imported 39946276972 ledger and their result records. All three outputs were byte-stable on a second generation. The ETH atmospheric-chemistry candidate resolves to exactly one active catalogue entry (`geo-eth-atmosphere`); ETH AI and Vienna have no active entry URL match. Formal data and public files were not written.
- Review assignment imports now require the pinned Skill digest, a complete candidate identity and fingerprint, exact source provenance and task kind, and the assigned reviewer. State compatibility v2 is rejected; v3 restore checks runner, adapter and candidate-ledger implementation hashes. Only versioned v3 artifacts participate in normal restoration; the legacy Round 002 artifact is accepted only before any v3 artifact exists. Explicit restores must name the latest compatible v3 run across repository branches, preventing old candidate-ledger replay. Bootstrap selectors are ignored on workflow reruns.
- No hosted PR preview URL, merge, or deployment was created in this change. The disposable local static-site preview is not a public deployment.
