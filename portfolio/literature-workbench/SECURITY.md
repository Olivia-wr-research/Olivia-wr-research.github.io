# Privacy and execution boundaries

The included Python helpers run locally using the standard library and have no model or network client. Agent instructions are different: if you activate a skill or request literature searching, the surrounding client and its enabled model/providers/tools may receive source content or queries. This repository cannot sandbox, redact or prevent that disclosure.

Keep unpublished research, copyrighted source collections, personal notes and credentials out of public commits. Generated projects are ignored by Git, but ignore rules are not a data-loss prevention system. Only invented CSV fixtures are included.

Agent roles request read-only advisory behavior. They inherit parent permissions; their instructions do not create technical read-only enforcement. The project config intentionally does not override models, concurrency limits or approval policies.

`release_check.py` scans files within this toolkit directory for selected private-artifact patterns. When it has its own `.git` directory, it also scans committed blobs. In a parent/monorepo checkout, it does not audit the parent repository's history. Pattern scans can miss information and can flag harmless text. Manually inspect the exact files and Git history you plan to release.

Neither structure validation nor evidence CSV validation verifies that a citation exists, a paper was accessed, a source supports a claim, a synthesis is scientifically valid, or an agent followed instructions. Do not treat `PASS` as approval to submit or publish academic work.
