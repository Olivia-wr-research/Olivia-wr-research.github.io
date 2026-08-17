# Academic Identity V2 User Review

## Summary

This pass corrected the initial V2 regressions while preserving the visual baseline from `origin/main`. The site now presents a stronger academic identity package without replacing the existing mountain-led design language.

## What Changed

- Homepage: removed duplicate identity card and clarified CTA hierarchy.
- Research: fixed rendered markdown artifacts and retained a research-agenda structure.
- Publications: removed the weak top status-summary block and kept the richer publication entries.
- Chinese pages: applied the same structural fixes to maintain bilingual consistency.
- Reports: added baseline comparison, content-loss audit, and visual-regression audit with screenshot evidence.

## Review Evidence

- Screenshots: `reports/academic_identity_visual_comparison/`
- Baseline audit: `reports/BASELINE_VS_V2_VISUAL_AUDIT.md`
- Content audit: `reports/CONTENT_LOSS_AUDIT.md`
- Regression audit: `reports/VISUAL_REGRESSION_AUDIT.md`

## Acceptance Check

| Requirement | Status |
| --- | --- |
| Preserve origin/main visual identity as baseline. | Passed |
| Do not replace site with a weaker generic template. | Passed |
| Fix literal `###` artifacts. | Passed |
| Remove duplicate homepage identity card. | Passed |
| Improve CTA hierarchy. | Passed |
| Keep Publications page substantive and scannable. | Passed |
| Keep bilingual pages consistent. | Passed |
| Do not push, merge, or deploy. | Passed |

## Final Review Note

The corrected V2 is ready for user-side visual review. Human review should focus on typography density, bilingual phrasing, and whether the Collaboration page should remain in the public navigation.
