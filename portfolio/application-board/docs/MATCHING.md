# Doctoral Compass v0.2 — matching and data boundaries

The homepage is now a Chinese-language discovery and matching interface, not the old progress board. The original public planning UI remains at `tracker.html`, and its browser storage key is preserved. No personal profile or private application database was migrated.

## Matching

Local inputs are comma-separated research interests, methods, optional degree level, self-reported English readiness and preferred countries. No name, nationality, protected trait, private manuscript or CV is requested. Profiles remain unencrypted in browser local storage; shared profiles and same-origin scripts are within the trust boundary.

The score is weighted token overlap: interests 70%, methods 30%. If only one component is populated, that component is normalized to 100. Tokens match explicit encoded bilingual tags, with conservative substring matching only for tokens of at least three characters. This is a small curated vocabulary, not a learned semantic model, calibrated fit measure, applicant-quality rating or admissions probability. A missing profile produces no score. Broad or ambiguous keywords can mislead; a zero score does not establish poor suitability.

Degree, language, deadline and country preference checks are displayed separately. Known gaps and unknowns cannot be compensated by a high interest score. Even a seemingly compatible degree remains subject to subject-specific, document and timing requirements. No final eligibility decision or automated application is performed.

## Public dataset

Six manually curated employer-page snapshots, checked on 2026-10-15, across two countries. This is not an exhaustive European index or a live feed. Employer links are embedded in every record. Chinese summaries and tags are this project's own short interpretations, not copied descriptions. Some requirements are deliberately unencoded and marked unknown. No salaries are converted into net income, exchange-rate estimates or living-cost projections.

The reference radar is an interaction/product benchmark only. Its data, paywalled content, source code, branding, salary estimates and group reports were not scraped, mirrored or redistributed. No claim of affiliation is made.

Imported JSON must follow the exported schema. Imports replace only the current browsable vacancy snapshot after confirmation; they do not overwrite the application checklist or profile. Locally imported facts are labelled unverified and remain the importer's responsibility. Exports include the browsable snapshot, not the private profile or personal notes.

## Official source pages

See `dist/positions.mjs` for all six source URLs, per-record notes and the checked date. Visit the original employer pages before relying on a deadline, salary, eligibility condition or continued availability. The data needs ongoing independent maintenance; no scheduled updating service is included.
