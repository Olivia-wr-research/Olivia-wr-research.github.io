# Task plan

## Outcome and boundary
Audit PR #9 persistence; implement reversible, reviewable private-state transport and tests. No source adaptation, real key access, private-evidence upload, public-archive approval, website release or merge.

## Phases
| Phase | Status | Acceptance |
|---|---|---|
| Inspect current code and run metadata | completed | PR heads, failures, artifact expiry and split authorities verified |
| Build private persistence and inactive workflow | completed | Single encrypted inventory; CAS; version-pinned objects; no public sinks |
| Validate and publish code-only review branch | completed | Offline suite, SDK contracts, workflow shell validation; exact changed-file review |
| Activate production and migrate actual history | blocked | Owner destination/region/budget approval; matching existing key; reviewed legacy reconciliation; live two-cycle drill |

## Decisions
Recommend private runner + versioned private S3, existing recipient certificate retained. No infrastructure or credentials provisioned. Existing public guard remains unchanged.

## Delivery
Draft PR #11 is stacked on unchanged PR #9: https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/pull/11 . Code commit 0cc861fa45268ec35a5d5c16fe4f22038ef8f954 passed GitHub Actions push run 40159718880. Production activation remains blocked for the explicit owner decisions above.
