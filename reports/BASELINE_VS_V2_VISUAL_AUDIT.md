# Baseline vs V2 Visual Audit

Scope: comparison between `origin/main` and the current `codex/academic-identity-v2` branch after the baseline-preserving correction pass.

Screenshot evidence is stored in:

`reports/academic_identity_visual_comparison/`

## Method

- Rendered `origin/main` in an isolated temporary copy.
- Rendered the V2 branch in an isolated temporary copy before source edits.
- Rendered the corrected V2 branch from the working tree.
- Captured desktop, tablet, and mobile screenshots at 1440px, 768px, and 390px.
- Compared English and Chinese pages for homepage, Research, Publications, Methods & Data, CV, and Collaboration where applicable.

## Page-Level Assessment

| Page | Baseline Strength | V2 Risk Found | Correction | Result |
| --- | --- | --- | --- | --- |
| Homepage | Strong mountain-led visual identity and compact academic presentation. | V2 duplicated identity details in a right-side card and weakened the hero hierarchy. | Removed the duplicate card, restored a single-column hero emphasis, and split primary/secondary CTAs. | V2 now improves academic positioning without losing the baseline atmosphere. |
| Research | Clear baseline layout, but less developed research narrative. | Raw `###` headings appeared inside research cards. | Replaced markdown headings with explicit card headings in EN/ZH source. | V2 is stronger than baseline on research agenda clarity and no longer shows markup artifacts. |
| Publications | Baseline had strong scanability and clear status tags. | V2 added a status summary area that created a weak top white block. | Removed the top status-summary block and kept publication entries as the main information surface. | V2 preserves baseline scanability while keeping richer output metadata. |
| Methods & Data | Baseline was concise and readable. | No critical visual regression after the V2 package. | Retained V2 academic methods organization. | Acceptable. |
| CV | Baseline was direct. | No critical visual regression observed. | No source correction required. | Acceptable. |
| Collaboration | Not present in baseline. | Risk of repeating homepage identity content. | Kept as a distinct collaboration-facing page linked from nav and profile package. | Useful addition, not a replacement for core pages. |

## Verdict

The corrected V2 branch is baseline-preserving. It keeps the production site's mountain-led academic identity while repairing the specific regressions introduced by the initial V2 package.
