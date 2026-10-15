# Research Software Portfolio

Small, inspectable tools for research workflows. Projects are selected for runnable code, traceable inputs, explicit limitations and reproducibility—not for the number of repositories or an “AI agent” label.

## NextPosition · Guided opportunity exploration

[Open the app](https://olivia-wr-research.github.io/apps/application-board/) · [Source](application-board/README.md) · [0.4 source ledger and limits](application-board/docs/RELEASE_04.md)

A Chinese-language research-opportunity explorer with all-field vacancy browsing, guided topic/method choices, browser-local DOCX/TXT/Markdown CV reading, explicit review of suggested tags, research-unit evidence cards, up-to-three-job comparisons and a preserved application tracker.

- Sixteen official-employer advertisement snapshots across three countries, dated 2026-10-15; no live or exhaustive index. Five official external search portals are separate from snapshot counts.
- Six research-unit pointers distinguish institutes, a group and a project; linked vacancies are explicit. No alumni outcomes, publication metrics, supervisory-quality or funding-continuity estimates are fabricated.
- Fixed-vocabulary CV suggestions are not semantic analysis or an admission prediction. Raw CV text is not transmitted or persisted; reviewed labels alone join local state. PDF/OCR are not implemented; paste locally copied text instead.
- 60 JavaScript and 9 Python tests; browser flows exercised with synthetic text, no real-user adoption or accuracy benchmark.
- Unencrypted browser-local profiles, no accounts, analytics, CV cloud service, model APIs, automatic applications or reference-site dataset copying.

## FrontierSignal · Research discovery and screening

[Source and quick start](frontiersignal/README.md) · [中文说明](frontiersignal/README.zh-CN.md) · [Methods](frontiersignal/docs/METHOD.md) · [Example receipt](frontiersignal/docs/EXAMPLE_RECEIPT.md)

Turn a public research topic into a portable research map: inspect source-linked papers, authors and publication affiliations; screen papers; export a shortlist and review decisions; replay a minimized metadata snapshot offline.

- Python CLI and self-contained HTML interface; no runtime Python dependencies.
- Included example: 100 public OpenAlex records for battery recycling, 2021–2025. No private research material, abstracts or full texts.
- Stable-ID/DOI deduplication, explicit missingness, identity non-merging and source-linked authorship evidence.
- Twenty Python tests plus JavaScript logic checks. These are engineering checks, not scientific accuracy or usability validation.

```sh
git clone https://github.com/Olivia-wr-research/Olivia-wr-research.github.io.git
cd Olivia-wr-research.github.io/portfolio/frontiersignal
python -m pip install .
python -m unittest discover -s tests -v
frontiersignal replay examples/battery-recycling/snapshot.json --out runs/replay
frontiersignal verify runs/replay
```

The example HTML is downloadable source, not a hosted application. FrontierSignal is an early-stage research utility, not an LLM agent, systematic review, expert ranking or production service. OpenAlex identifiers are not independently verified identities, and publication affiliations are not current employment.

## Career Evidence Pipeline · Document extraction and candidate trajectories

[Source and quick start](career-evidence/README.md) · [中文说明](career-evidence/README.zh-CN.md) · [Example events](career-evidence/examples/expected/extracted/events.json) · [Example trajectory](career-evidence/examples/expected/trajectory/trajectory.json)

An offline CLI and Python library for extracting source-linked candidate career events from local documents, then deriving candidate spells and moves after explicit organization-ID review.

- Preserves exact source text, locators, date uncertainty and review input hashes.
- Entirely synthetic example: 5 events, 5 spells, 2 candidate moves; no real-person records.
- 31 offline tests; a built wheel was installed and exercised outside the source directory.
- No LLM, scraping service, automatic gold labels or hosted upload interface. English rule patterns are limited and no real-person accuracy benchmark is claimed.
- An intentionally scoped public subset of an existing project, not its complete private pipeline. MIT licensed.

From a clone of this repository: `cd portfolio/career-evidence`, then follow the project README. Generated real-person outputs must remain private.

## Literature & Theory Workbench · Agent workflow design

[Toolkit and quick start](literature-workbench/README.md) · [中文说明](literature-workbench/README.zh-CN.md) · [Synthetic fixture](literature-workbench/examples/synthetic/evidence.csv) · [Compatibility](literature-workbench/docs/COMPATIBILITY.md)

A repository-scoped toolkit that separates literature discovery, evidence extraction, theory/method comparison, framework building and claim audits.

- 11 skills, 8 advisory role configurations, 13 artifact templates and local Python helpers.
- 21 offline regression tests; all 11 skills also passed the skill-creator structural validator.
- Creates isolated project scaffolds, summarizes records and checks evidence CSV structure, including negative cases.
- Includes no private research topic, manuscript, live search history or model-generated review.
- Not a standalone app or autonomous review service. Client/model behavior and scientific quality are not benchmarked. Role instructions are not security sandboxes.

Open the complete `portfolio/literature-workbench` subfolder in a compatible client. The scripts work without a model; activating agent skills may send content to the client's providers/tools. MIT licensed.

## Author–Institution–City Linkage · Research data engineering

[Standalone repository](https://github.com/Olivia-wr-research/author-institution-city-linkage)

A separate reproducible author–institution–city linkage toolkit with synthetic examples. It demonstrates structured bibliographic data processing without distributing a private research dataset. Its own repository documents installation, methodology and tests.

## Publication boundaries

This collection intentionally excludes private application systems, unpublished manuscripts, personal research questions, historical feedback databases, contact lists, credentials, restricted datasets and third-party tools presented as original work. Other local prototypes are not listed as released products.

FrontierSignal code is MIT licensed; its OpenAlex example metadata is CC0 according to the provider. Linked papers retain their own rights. Code and documentation were prepared with AI assistance. No user adoption, measured productivity gain or scientific validity is claimed.
