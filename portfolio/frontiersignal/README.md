# FrontierSignal

**A public research topic → an inspectable research map → a source-linked shortlist.**

FrontierSignal builds a self-contained HTML report from OpenAlex metadata. Filter papers, inspect which authors and institutions are actually supported by those papers, and export a shortlist with your own review notes. Each run keeps the retrieval receipt, minimized bibliographic snapshot and file hashes.

## Try it without an API call

Open [`examples/battery-recycling/report.html`](examples/battery-recycling/report.html) in a browser. It contains a real, bounded public-metadata snapshot, not invented paper records. No server, account, JavaScript build or external CDN is needed to explore the report.

GitHub displays HTML source rather than executing it: download or clone the repository and open the file locally.

## Install and search your own public topic

Python 3.11+; no runtime Python dependencies.

```sh
python -m pip install .
frontiersignal search "battery recycling" --from-year 2021 --to-year 2025 --limit 100 --out runs/battery
```

Open `runs/battery/report.html`. Choose a new output directory for each run; existing reports and reviews are never overwritten. Search terms are sent to OpenAlex. Use only public, non-confidential topics.

If OpenAlex requires authentication or its rate limit is reached, set your own `OPENALEX_API_KEY` environment variable. The key is sent in an HTTP authorization header and never saved in the report or request receipt. Failures produce an explicit error, not substitute data. [API access](https://help.openalex.org/api/authentication/).

## What can I do with the report?

- Filter titles and exclude unwanted phrases; restrict year, work type or DOI availability.
- Click an author to inspect the source papers supporting that person's presence in the sample.
- Inspect paper-level affiliations, source records and missing metadata.
- Shortlist or exclude papers, add review notes, export CSV and save/restore review decisions.
- Explore a bounded coauthorship graph and sample publication-year counts.
- Rebuild the same report offline:

```sh
frontiersignal replay examples/battery-recycling/snapshot.json --out runs/replayed
frontiersignal verify runs/replayed
```

Review state stays in the browser tab until explicitly exported; it is not sent to a server. Restore files are bound to the exact snapshot hash.

## Why this exists

A list of search results is a starting point. A reusable research artifact also needs an inspectable sample, source-linked people and institutions, screening decisions, exports and a way to reproduce what was seen. FrontierSignal packages those steps in a portable report. It does not add an LLM layer or sell arbitrary scores as scientific judgment.

## Outputs

| File | Purpose |
|---|---|
| `report.html` | Offline interactive report; all CSS, JavaScript and data are embedded |
| `snapshot.json` | Minimized provider metadata and retrieval parameters for replay; no raw affiliations or contacts |
| `data.json` | Normalized works, authors, institutions, edges and audit counts |
| `works.csv` | Paper-level reading inventory |
| `author_evidence.csv` | One authorship row linked to the supporting paper |
| `quality.json` | Coverage, duplicate removal, exclusions and truncation |
| `manifest.json` | SHA-256 hashes of run artifacts |

## Boundaries that change interpretation

The report is a relevance-ordered, bounded sample of at most 200 records per search, not a systematic review or an expert ranking. OpenAlex author IDs are provider assignments, not independently verified identities. Same-name people are never merged. Missing IDs remain work-local. Publication affiliations do not establish employment. Network edges are omitted for teams over 30 resolved authors; graph nodes are capped at 12 for legibility. The underlying evidence tables retain all parsed authorships.

Retraction flags are taken from the provider; a missing flag remains unknown. Raw retracted records, malformed works and duplicate identifiers/DOIs are recorded as exclusions. Citation counts are displayed as snapshot metadata only. The reports and examples do not contain abstracts or full texts.

## Tests and provenance

```sh
python -m unittest discover -s tests -v
```

See [measurement choices](docs/METHOD.md), [public example receipt](docs/EXAMPLE_RECEIPT.md), [privacy](SECURITY.md) and [contribution guide](CONTRIBUTING.md). CI checks the offline behavior; live retrieval is tested separately and is time-dependent. No user adoption or efficiency improvement has been measured.

Code: MIT. OpenAlex metadata: CC0 according to [OpenAlex's data description](https://help.openalex.org/data/how-its-built/). This does not grant rights to linked papers. Code and documentation were prepared with AI assistance.
