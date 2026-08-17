# Content Loss Audit

Scope: `origin/main` compared with corrected `codex/academic-identity-v2`.

## Findings

| Area | Baseline Content | Corrected V2 Status | Assessment |
| --- | --- | --- | --- |
| Homepage identity | Name, school, degree, interests, academic paragraph, personal paragraph, CTAs. | Name, school, degree, refined academic identity, research themes, CTAs. | No academic content loss. The personal paragraph was intentionally removed from the main hero because it was less relevant for supervisor review. |
| Homepage right-side card | Not present in baseline. | Removed from corrected V2. | Removal is a regression fix, not content loss. |
| Research agenda | Baseline presented research focus, framework, streams, trajectory, foundations. | V2 keeps a clearer agenda around careers, networks, innovation, and trajectory. | No substantive loss; research framing is more compact and supervisor-facing. |
| Publications | Baseline displayed accepted article, submitted manuscripts, thesis, and earlier research outputs. | V2 retains the same output categories with verified status labels and detail links. | No publication category loss observed. |
| Publication-status block | Not in baseline; added in initial V2. | Removed from corrected V2. | Removal improves scanability and avoids a large weak visual block. |
| Methods & Data | Baseline organized data systems, construction, modelling, and reproducibility. | V2 keeps the same methodological logic. | No content loss observed. |
| Chinese pages | Baseline localized core pages. | V2 keeps Chinese navigation and localized page content. | No cross-language loss observed in inspected pages. |
| Research collaboration profile | Not present in baseline. | Added as a separate PDF and Collaboration page. | Additive content. |

## Protected Publication Content

The corrected V2 keeps the publication page as a rich academic output page rather than reducing it to a plain status list. Accepted, submitted, thesis, and earlier research outputs remain visible.

## Verdict

No unintentional academic content loss was identified. The removals made in this correction pass address duplication, weak presentation, or non-essential homepage text rather than eliminating substantive research content.
