# Public example and verification receipt

The example uses **battery recycling**, a general public topic unrelated to the project owner's private research. It contains only publicly available bibliographic metadata from OpenAlex, minimized before redistribution. No manuscript, private database or user profile was used.

| Item | Recorded value |
|---|---|
| Topic | battery recycling |
| Requested publication window | 2021–2025 |
| Retrieved at | 2026-10-15T07:28:30.647500+00:00 |
| Requested / received records | 100 / 100 |
| Provider-reported matches | 78,810; this is not the report sample size |
| Included after ID/DOI deduplication and exclusions | 100 |
| With DOI | 97 |
| With any author metadata | 98 |
| With any publication affiliation | 80 |
| Resolved provider author IDs | 346 |
| Work-local unresolved authorship rows | 44 |
| Minimized snapshot SHA-256 | `fea4e375dc2457631081b4a31268684f6b5a59052c818c0d1821275797a48216` |

Inspect `snapshot.json`, `data.json` and `author_evidence.csv` to audit these counts. Run `frontiersignal verify examples/battery-recycling` to check the six artifact hashes. The hash covers the minimized source snapshot, not the untouched HTTP response.

## Additional bounded live checks

- `solid state batteries`, 2022–2025: 60 records received; 59 with DOI, 56 with publication affiliation. One large-team work was omitted from graph pair construction, while its authorship evidence was retained.
- `perovskite solar cell stability`, 2021–2025: first attempt failed with an explicit connection error. A separate retry returned 60 records; 57 with DOI, 54 with publication affiliation. The failed attempt was not reclassified as a zero-result query.

These additional live outputs were used for local validation, not included as private datasets or substituted for the bundled example. Provider access and metadata can change.

## Executed engineering checks

- Python unit tests cover stable-ID and DOI deduplication, missingness, identity non-merging, retraction exclusions, graph caps, network failure behavior, header-only keys, privacy projection, CSV escaping, script injection, deterministic replay, output preservation and manifest verification.
- `tests/report_logic.mjs` executes application logic in an in-memory DOM stub. It checks title/year/DOI/author filters, shortlist and exclusion, CSV export, decision export/restore, snapshot mismatch rejection and output escaping. It does not establish browser rendering or usability.
- A built wheel was installed in an isolated local environment and used for offline replay. Report artifacts were compared with the source example.
- Browser preview was blocked by the agent browser's policy against local-file URLs. No alternative browser route was used to bypass that restriction; real-browser visual acceptance has not been claimed.

No user adoption, manual scientific accuracy or productivity improvement is asserted. The concrete improvement over the earlier synthetic scaffold is a usable topic-search / inspect / screen / export / reproduce workflow exercised on real public metadata.
