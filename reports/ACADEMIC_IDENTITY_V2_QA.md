# Academic Identity V2 QA

Date: 2026-08-17

## Simulated reader review

### US PhD professor: 30-second homepage review

- Research question identifiable: yes. Homepage now states scientific mobility, relational ties, and knowledge production directly.
- Strongest evidence identifiable: yes. Evidence section names longitudinal career data, current methods, and research outputs.
- Methods identifiable: yes. Methods are visible through homepage evidence and Methods & Data page.
- Current outputs identifiable: yes. Publications page separates accepted, submitted, thesis, selected output, and software/data product.
- Potential collaboration identifiable: yes. For Collaboration page explains data and analytical capabilities.

### European advertised-PhD PI: 30-second profile review

- Research identity identifiable: yes. It is framed as quantitative social science / science of science rather than a mixed identity list.
- Evidence and status identifiable: yes. Public CV and Research Profile PDF are directly linked.
- CV policy: global no-photo CV preserved; European photo is optional only when required by convention or vacancy.

### Potential research collaborator: 60-second website review

- Objects identifiable: scientists, high-skilled mobility, collaboration networks, organisations, cities.
- Data capabilities identifiable: career reconstruction, publication/institution linkage, relational datasets, entity matching, spatial/network integration.
- Analytical capabilities identifiable: choice modelling, network analysis, spatial analysis, longitudinal design, reproducible workflows.

## Claim audit

- Numerical claims are limited to public CV-supported database, manuscript, and project descriptions.
- Publication statuses are explicit and conservative.
- Institutional affiliations are unchanged and evidence-backed.
- No causal overclaiming was introduced.
- No sensitive IDs, submission details, raw data, or transcripts were exposed.

## Build and link checks

- English build: `quarto render` completed with no fenced-div warnings after syntax correction.
- Chinese build: `quarto render zh` completed. Quarto emitted the existing `zh-CN` translation-file warning, but output pages were generated.
- HTTP status: key English pages, Chinese pages, selected paper pages, public CV PDF, and Research Collaboration Profile PDF returned 200 on local server.
- Internal links: generated HTML internal links checked with a local parser; no missing internal target found.
- Responsive QA: Browser DOM checks at 390px and 1440px found zero horizontal overflow on sampled homepage and key pages.
- Language switch: English pages expose Chinese switch; Chinese pages expose English switch.
- Privacy scan: public generated HTML contains no local filesystem path, private-audit marker, internal submission identifiers, review details, or deprecated Publication-Location title.
- PDF QA: Research Collaboration Profile rendered to one page; PNG inspection showed no clipping or overlap. Poppler produced fontconfig cache warnings in the local environment, but the PNG output was created and readable.
- Screenshots: after-state homepage screenshots were saved through the browser QA tool; before-state screenshots were not captured before the first edit.

## Remaining human checks

- Add a user-owned professional headshot only after explicit user verification.
- Confirm whether Application Agent `knowledge/PUBLICATIONS.md` should be updated to match the public CV manuscript-status list.
- Confirm whether a new long-term academic email should replace the current public email after mailbox testing.
