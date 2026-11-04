# TERRAFAR V1 — 2026-11-04

Production: https://olivia-wr-research.github.io/apps/application-board/
Public data: https://olivia-wr-research.github.io/apps/application-board/public-dataset.json

This release contains 181 records: 97 concrete-opportunity records and 84 programme/resource records. Of the concrete records, 64 have verified content: one has explicit portal acceptance verified at review, while 63 still require availability review. Eight historical deadlines have passed and 25 older records need further evidence. These categories must not be added to imply a larger number of open jobs.

The release adds 59 content-verified records, corrects six existing records and updates two application/programme routes. Fifteen proposed additions remain private because of elapsed deadlines, unresolved conflicts or incomplete identity/scope evidence. Original public IDs, bookmarks and browser-local profiles are preserved.

The default view shows only records passing the conservative open-state rule. Other statuses can be explored with the timing filter. A readable advertisement, application button or future deadline alone does not prove acceptance. Portal evidence expires from open recommendations after seven days; no scheduled maintenance was enabled by this release.

The existing orthographic globe, colours, typography and assets are reused. The dormant map mount is reconnected; no map or page redesign is included.

## Rebuild and rollback

Use `scripts/terrafar_public_export.py --help` with a privately stored reviewed packet, exact recovered state, baseline catalogue and current portal validation. The exporter emits only allowlisted public fields and a separate private validation report. Copy the eight changed static data/runtime files from `dist` to the hosted `docs/apps/application-board` directory; the workflow verifies that both trees match.

Run the existing Node and Python test suites. Merge the reviewed release commit to main; the existing GitHub Pages configuration publishes `/docs`. Keep private evidence, candidate histories and owner records out of the public diff. To roll back, revert the release with an ordinary reviewed commit; do not reset history, keys or browser storage.

Coverage is expanding. The release data identifies 19 registered sources associated with verified published content; it does not claim complete extraction of the source registry. Unfinished adapters, broader collection, maintenance capacity and periodic status checks remain backlog items and do not block use of this reviewed snapshot.
