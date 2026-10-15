# 0.5 public pilot — 2026-10-15

This release supports a small public trial, not a comprehensive European vacancy service or a paid subscription promise.

- 19 official advertisement snapshots across five countries. New sources: ETH AI fellowship, ETH soft robotics and HVL physiology. Multiple places in one advertisement count once. Existing sources retain their original check date.
- Text-layer PDF extraction stays in the browser. Bundled PDF.js 5.6.205, Apache-2.0, no CDN; see `dist/PDFJS-LICENSE.txt`. Max 5 MB, 20 pages, 100,000 characters, 15-second processing timeout. Scans, password-protected files and unsupported fonts may require local text copying. No OCR service is used.
- Expanded interdisciplinary vocabulary, controlled trigger phrases and explicit unchecked topic/method choices. Mentions are suggestions, not proven skills; negation and semantic intent are not fully understood. No raw CV phrases are persisted or published.
- Coverage distribution and snapshot age are visible. A future deadline never proves the employer is still accepting applications. Empty results provide clear-filter and official-source actions.

## Validation

79 JavaScript tests and 9 Python launcher tests. Actual browser successfully parsed a synthetic PDF, produced research/method suggestions, cleared raw text and left all choices unchecked. The parser unit tests cover page/text/file caps, missing text, password and malformed errors with cleanup; these mock the PDF library and do not constitute a complete PDF format benchmark. No real personal CV is bundled.

## Next market step

Invite a small initial cohort to try three tasks: find relevant opportunities, confirm CV-derived directions, and save/compare a shortlist. Record with consent whether each task succeeds, where users hesitate, and whether they return. Do not collect their raw CVs or application materials for feedback. No such study or user-demand validation has yet been conducted.

Before broad promotion or charging: establish an ongoing employer-source update process, per-record change history, broader country coverage, cross-browser and real-mobile checks, and a clear feedback channel. Manual snapshots remain the principal product limitation. Accounts, cloud sync, automatic alerts and payments are not implemented.

## Dependency provenance

Unmodified PDF.js distribution from the installed bundled runtime; upstream API: https://mozilla.github.io/pdf.js/api/draft/module-pdfjsLib.html

- pdf.min.mjs SHA-256: `2221020ea508479dcc1221f36f2731656339230097c69ba1f78802832c0ad685`
- pdf.worker.min.mjs SHA-256: `51a2fd1ea47f1a9b0814e65e0c336c739c54957795ee774e8f93cb81e8028dd1`
