# Public scope and methods

## Reused implementation

Three original modules were selected from an existing local scientist-mobility project: document normalization, rule extraction, and event-to-spell/move derivation. They were inspected as source code, not presented as independently validated research methods. No third-party vendor code, reference datasets, manuscripts, private protocols or real CVs were copied.

The public edition adds a real three-command CLI (`extract`, `derive`, `verify`), packaging, synthetic examples and isolated tests. It deliberately omits the original placeholder stage dispatcher and unfinished review page. No SQL database, historical state or scientific analysis is distributed.

Public-edition fixes include month validation/canonicalization, PDF page-line locators, spell IDs that distinguish an A→B→A return, conservative handling of uncertain temporal order, create-only runs, CSV formula escaping, explicit organization-ID review and bounded manifest file names. These are software changes, not new scientific findings.

## Interpretation

1. Normalization keeps extracted text and parser locators. A DOM block ordinal is not a stable live-page XPath; PDF lines depend on parser output, not geometric truth.
2. Rule extraction recognizes a narrow English heading/date pattern. The fixed score is a rule marker, not an estimated probability. Missed events and wrong headings remain possible.
3. Before derivation, users provide organization IDs. Raw names are not sufficient identity evidence. The synthetic helper is not reusable identity matching.
4. Consecutive same-organization events are grouped within training/career and primary/concurrent tracks. These groups do not establish continuous employment or gap-free coverage. Primary flags are heuristic and require inspection.
5. Moves join neighboring primary groups with different reviewed organization IDs. Unknown primary start dates suppress the whole affected track; same-year transitions are not automatically ordered. These are candidate data transformations, not verified moves, lifetime coverage or causal effects.
6. Append-only human coding, inter-rater reliability, validated production extraction, authenticated review and scientific publication are outside this edition.

## Reproducibility

For identical input bytes, person ID and software version, extraction artifacts are deterministic. Derivation records hashes of the supplied event-review file and normalized file. Files and manifests are UTF-8 and cannot overwrite an existing output directory. The original source bytes are not distributed in run outputs, and a stored digest alone cannot authenticate them.

The example is entirely invented. Tests exercise expected synthetic behavior and negative cases, not real-person extraction accuracy or human-review quality. No historical 127-test count, large-cohort coverage result or prior benchmark accuracy is claimed for this release.
