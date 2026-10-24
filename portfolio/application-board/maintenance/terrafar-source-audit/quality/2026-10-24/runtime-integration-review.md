# Runtime integration review — 2026-10-24

## Scope

Integrated the earlier full-source runtime with remote privacy branch `e3d77d4de9267f521c54617588f0c2703ff442fd` using `65ebd3d587f5cad74150dfcb5fb461d7e9f3f5db` as the three-way merge base. No published-site files or source-registry IDs were modified by this integration.

The source runner had five overlapping merge regions. The final version preserves the newer exact HTTP request counters, uncertain send-failure markers, redirect counts, target-request/response metrics, and response byte counts. It also preserves strict semantic-baseline validation, conditional-304 evidence identity, hash-verified private response capture, all-source execution, and the explicit completeness gate. Existing source-audit tests merged without conflicts.

Adapters, candidate ledger, data-review preparation, and adapter catalog were copied only after confirming the remote files were unchanged from the merge base. New detail scopes remain explicitly limited to each registered job page; they do not claim institution-wide recruitment coverage. The USF parser excludes historical and navigation sections.

## Local verification

- Python compilation: passed for the four changed runtime/data scripts.
- Detail adapter tests: 9 passed.
- Raw response evidence tests: 7 passed.
- Data pipeline tests: 10 passed.
- Full-runtime/migration tests: 6 passed after the restore module was integrated.
- Combined source-audit tests: 85 passed, 1 workflow-string expectation still pending the root workflow integration at the time of this report (`test_restore_selection_is_versioned_and_rejects_legacy_replay`). This report does not label that suite fully passing.
- No live source HTTP requests were made by this integration agent. Local cryptographic tests use temporary synthetic keys and do not validate the owner's production key.

## Migration binding

`migrations/current.json` targets the exact five integrated implementation hashes and preserves all 411 registered IDs. Its origin implementation hashes are derived from commit `cec22378b038491f6af29afdba2fbafcb993bcc9`, the reported latest complete encrypted census checkpoint, Actions run `40088463064`. Those five origin files are byte-identical at remote head `e3d77d4`. The actual checkpoint must still be decrypted using the owner's matching key and pass its independent artifact provenance and hash checks; the migration manifest does not replace that validation or permit falling back to older plaintext state.

## Remaining release gates

The real encrypted-checkpoint restore, new live all-source run, persistent encrypted review journal, and current user review have not been proven by these local tests. Source completeness and field accuracy remain independent of successful code tests. Formal opportunity publication remains blocked.
