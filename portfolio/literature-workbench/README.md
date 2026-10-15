# Literature & Theory Workbench

A repository-scoped literature workflow with **11 skills, 8 advisory agent roles, 13 artifact templates and local Python helpers**. It helps separate source facts, author claims, interpretation and synthesis instead of generating a polished review from an unexamined search list.

This is a workflow toolkit, not a hosted app, a standalone model, an automatic systematic-review service or a guarantee of citation accuracy.

## Try the offline helpers first

Python 3.11+; no Python dependencies. From this workbench folder:

```sh
python3 scripts/validate_workspace.py
python3 scripts/validate_evidence.py examples/synthetic/evidence.csv --strict
python3 scripts/bootstrap_project.py --name "Example review" --slug example-review --language en
python3 scripts/summarize_project.py projects/example-review
python3 -m unittest discover -s tests -v
```

These commands create an empty, organized review workspace—not a completed review. Existing project folders cannot be overwritten. The checker has 21 offline regression tests, including negative cases. The included synthetic evidence passes strict checks; unsupported interpretation-as-author-claim, duplicate IDs and malformed CSV rows fail. `--strict` also rejects warnings such as a direct claim without a locator or a blank evidence table. A structurally consistent table can still be scientifically wrong.

## Use the skills in a compatible client

Open **this subfolder**, not only the parent portfolio repository. Keep the toolkit together; its skills use shared root-level references and scripts. Ask the client:

> Use `$lit-review-orchestrate` for `projects/example-review`. Begin with the protocol. Do not invent sources or mark any scientific gate complete without evidence. Do not search externally or send confidential content without checking my instructions and the client settings.

The Python helpers do not need a model. Using the agent workflow does require a configured compatible client/model and whatever search/source tools the task needs. The 8 roles are configurations, not evidence that eight agents have read papers. They inherit parent permissions; advisory read-only instructions are not a technical sandbox. Model, concurrency and approval settings are intentionally not overridden.

Current configuration choices were checked against official documentation; see [compatibility and scope](docs/COMPATIBILITY.md). Actual end-to-end model behavior and discovery across client versions were not tested in this release.

## Workflow

Define scope, log searches, screen sources, extract evidence, compare theories and methods, synthesize disagreements, build a framework, audit claims, then draft. A narrower request may stop at any stage.

The central distinction is source fact, author claim, agent interpretation and cross-source synthesis. Preserve locators and contradictory evidence. Human decisions remain necessary for scientific judgments.

## Public example

`examples/synthetic/evidence.csv` contains an explicitly invented reading-comfort example. It has no real authors, DOI, paper titles or study results. It demonstrates validation only. Existing local projects and research topics are excluded from this repository.

## Privacy

Work with copies of materials you are authorized to use. Generated projects are ignored by Git. External search or model providers may receive content when invoked by the agent client; review that client's settings before supplying confidential material. This repository does not itself provide a data-loss prevention sandbox.

Run `python3 scripts/release_check.py` before sharing, and inspect the exact release files yourself. The scanner ignores environment/build/bytecode directories; it does not certify privacy or audit the parent portfolio repository's Git history. See [security boundaries](SECURITY.md).

[中文说明](README.zh-CN.md) · [Evidence levels](references/evidence-levels.md) · [Claim ledger template](templates/claim-ledger.csv) · [Synthetic example](examples/synthetic/README.md)

MIT licensed. Instructions and public-edition improvements were prepared with AI assistance. No productivity gain, user adoption, model-evaluated skill quality or scientific validity is claimed.
