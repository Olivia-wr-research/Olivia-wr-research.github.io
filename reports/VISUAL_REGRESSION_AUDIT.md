# Visual Regression Audit

Scope: corrected `codex/academic-identity-v2` against `origin/main`.

## Regressions Identified and Fixed

| Issue | Evidence | Fix | Status |
| --- | --- | --- | --- |
| Literal `###` rendered in research question cards. | Browser screenshots and generated HTML review. | Converted markdown headings inside card containers to explicit `<h3>` elements in English and Chinese Research pages. | Fixed. |
| Literal `###` rendered in homepage research theme cards. | Source review after the first Research fix. | Converted homepage theme-card markdown headings to explicit `<h3>` elements in English and Chinese homepage source. | Fixed. |
| Duplicate homepage identity card. | Desktop homepage comparison at 1440px. | Removed right-side hero card and preserved a single, stronger hero identity block. | Fixed. |
| Awkward CTA wrapping and hierarchy. | Desktop homepage comparison at 1440px. | Kept Research, Publications, and CV as primary buttons; moved Research Profile and GitHub to secondary text links. | Fixed. |
| Publications page top white block weakened scanability. | Publications comparison at 1440px. | Removed the V2-only Output Status section and restored the publication list as the first substantive content. | Fixed. |

## Visual QA

- Screenshot package contains 78 PNG files.
- Key side-by-side comparison files exist for English and Chinese homepage, Research, and Publications at 390px and 1440px.
- Generated HTML scan found no remaining literal `###` or Quarto `:::` markers in public HTML.
- The corrected V2 keeps the mountain background and the production site's editorial academic visual identity.

## Residual Risk

The visual review was performed through local browser screenshots. Final human review should still inspect spacing, rhythm, and bilingual navigation in a normal browser session before merge.
