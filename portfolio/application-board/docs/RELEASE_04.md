# NextPosition 0.4 — guided research-opportunity exploration

## Product changes

Visitors can browse all fields without a profile, start from a guided checklist, derive candidate tags from a locally read CV, inspect research-unit evidence, compare up to three vacancies, and keep the existing application tracker. No admission score is displayed prominently on cards. Keyword weights still order results; the details explain the limited method.

The snapshot now contains 16 distinct advertisements across 3 countries, not 16 guaranteed open places. One UvA advertisement describes two places and is counted once. All snapshots are dated 2026-10-15; nine are retained from 0.3 and seven were newly checked in 0.4. No automatic refresh, comprehensive European coverage or measured search recall is claimed.

## New official vacancy evidence

- [UvA 15555 — political science](https://werkenbij.uva.nl/en/vacancies/phd-position-in-political-science-netherlands-15555): November 11; quantitative methods, English, MSCA arrangements and planned institutional moves require checking.
- [UvA 15557 — Latin America](https://werkenbij.uva.nl/en/vacancies/phd-position-in-political-science-militarization-and-democratic-erosion-in-latin-america-netherlands-15557): November 6; Spanish and/or Portuguese, fieldwork and MSCA mobility restrictions are material requirements.
- [UvA 15548 — groundwater care](https://werkenbij.uva.nl/en/vacancies/phd-position-groundwater-care-and-the-politics-of-transformation-india-netherlands-15548): November 2; ethnographic work in India and Hindi are important. European employer does not mean all work takes place in Europe.
- [UvA 15530 — digital enforcement](https://werkenbij.uva.nl/en/vacancies/phd-candidate-in-systemic-actors-and-the-enforcement-of-digital-rules-netherlands-15530): November 2; relevant master's/equivalent, English and MSCA restrictions need individual documentary review.
- [UvA 15503 — synthetic content and youth](https://werkenbij.uva.nl/en/vacancies/2-phd-positions-agents-of-doubt-synthetic-content-and-adolescents-knowledge-formation-netherlands-15503): October 16; two places in one advertisement. Near deadline; recheck local closing time.
- [Copenhagen 170772 — face recognition](https://jobportal.ku.dk/phd/?show=170772): November 10; relevant master's-level qualifications; foreign equivalence and any exception require institutional assessment.
- [Copenhagen 170003 — attention](https://jobportal.ku.dk/phd/?show=170003): November 3; philosophy/cognitive science background and master's-level qualification assessment.

All Chinese summaries are short original paraphrases. No emails, personal contacts or full vacancy texts are included. Check original sources before acting.

## Research-unit evidence, not a group ranking

Six entries distinguish institutes, a project and a research group; they are not equivalent units. Official AISSR, IViR, Leiden Public Administration, ASCoR and Youth & Media pages, plus the TU Delft Infra-PaX employer page, support identity/topic/association pointers. Links to vacancies use explicit IDs. Parent and child units may share a vacancy; do not sum counts as independent opportunities. Imported records cannot create verified unit associations.

Graduate counts, three/five-year career outcomes, annual publication rates, funding continuity and supervisory quality remain unknown/unassessed. No thesis-name inference, author-ID matching or alumni career pipeline has been run. The reference website was inspected only for visible functionality; its dataset, reports and paid content were not scraped, copied or unlocked.

## CV privacy and capability

DOCX, TXT and Markdown files up to 5 MB, or pasted text up to 100,000 characters, are processed in browser memory. DOCX processing reads only bounded `word/document.xml`; encrypted documents, unsupported compression and entity declarations are rejected. No macros, external document links or embedded media are executed/fetched. The reader is a minimal extractor, not a complete Word renderer or security certification.

PDF, scanned images, OCR and semantic/LLM CV understanding are **not implemented**. PDF users must copy text locally and paste it. A browser without native raw-deflate decompression receives a clear DOCX fallback message. No silent upload fallback exists.

Only fixed-vocabulary candidate topic/method labels are generated. Contact-like email/URL strings are removed before suggestions. A mention can reflect a course, an old project or negation; it does not establish proficiency or interest. Users must inspect, edit and explicitly confirm suggestions. No degree, English proficiency, nationality, eligibility or protected traits are inferred. Raw text is cleared after extraction or dialog close and is not written to localStorage, GitHub or any model service. Confirmed labels alone join the existing unencrypted local profile. Shared-origin scripts and browser extensions remain in the trust boundary.

## Multidisciplinary review checklist applied by the implementation agent

These are review perspectives, **not independent human expert opinions or a user study**.

| Perspective | Decision | Still missing |
| --- | --- | --- |
| User research | Provide browse, experience-based guidance and CV-derived draft labels; no prior-interest requirement | Consented real-user tasks and observed evidence |
| Product | Connect discover → understand unit → compare → save → plan | Reliable recurring supply and retention evidence |
| Domain | Preserve language, degree-equivalence, mobility and contract exceptions | Individual documentary eligibility review |
| Data/retrieval | Explicit source links, dated snapshots, unique vacancy IDs; separate sources/units/jobs | Licensed refresh pipeline, closure detection and coverage audit |
| Engineering/QA | Bounded file parsing, versioned assets, tests, source/static parity, local flow checks | Cross-browser/mobile real-device matrix and external security review |
| Privacy/compliance | No CV transmission, no third-party CV processor, no alumni profiles or reference-site copying | Legal review before commercial collection or analytics |
| Growth | Free browse and clear scope; no fabricated adoption or demand | Voluntary recruitment, consent and evidence of repeated value |

Next release gates: robust local PDF extraction; broader independently sourced vacancy coverage with freshness metadata; real-device validation; then consented user research. Accounts, cloud CVs, emails, payments and automated applications remain outside this release.
