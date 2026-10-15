# Research Software Portfolio

Small, inspectable tools for research workflows. Projects are selected for runnable code, traceable inputs, explicit limitations and reproducibility—not for the number of repositories or an “AI agent” label.

## Application Board · A browser-local application workspace

[Open the app](https://olivia-wr-research.github.io/apps/application-board/) · [Source and local launcher](application-board/README.md) · [中文说明](application-board/README.zh-CN.md)

A public-facing implementation of the opportunity → materials → progress workflow. Add and edit roles, search/filter opportunities, track date-only deadlines, maintain material checklists, manually update stages and export/import private backups.

- An empty workspace for each browser profile/origin; only fictional opt-in examples.
- 27 JavaScript logic tests and 8 Python launcher tests. Local browser create/checklist/stage/reload flows were exercised with invented records.
- No applicant profile, CV upload, inbox integration, automatic submission or vacancy recommendation.
- Static hosting serves the interface, not an applicant database. Records stay in the visitor's browser and are unencrypted; this is not an authenticated multi-tenant SaaS.
- This is a new public implementation inspired by a private dashboard, not a distribution of that private system or its data. MIT licensed; AI-assisted implementation.

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
