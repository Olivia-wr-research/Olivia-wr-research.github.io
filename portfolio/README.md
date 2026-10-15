# Research Software Portfolio

Small, inspectable tools for research workflows. Projects are selected for runnable code, traceable inputs, explicit limitations and reproducibility—not for the number of repositories or an “AI agent” label.

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

## Author–Institution–City Linkage · Research data engineering

[Standalone repository](https://github.com/Olivia-wr-research/author-institution-city-linkage)

A separate reproducible author–institution–city linkage toolkit with synthetic examples. It demonstrates structured bibliographic data processing without distributing a private research dataset. Its own repository documents installation, methodology and tests.

## Publication boundaries

This collection intentionally excludes private application systems, unpublished manuscripts, personal research questions, historical feedback databases, contact lists, credentials, restricted datasets and third-party tools presented as original work. Other local prototypes are not listed as released products.

FrontierSignal code is MIT licensed; its OpenAlex example metadata is CC0 according to the provider. Linked papers retain their own rights. Code and documentation were prepared with AI assistance. No user adoption, measured productivity gain or scientific validity is claimed.
