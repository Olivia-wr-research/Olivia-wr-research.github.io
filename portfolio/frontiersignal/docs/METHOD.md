# Measurement and implementation

## Task and unit

The tool supports initial public-topic exploration and a human reading shortlist. A work is a provider Work ID. An authorship is one parsed work–author record. An institution association is a publication-affiliation record, not a job or employment event.

## Retrieval

One OpenAlex Works request, standard search plus year and retraction filters, 5–200 requested records, selected metadata fields only. No abstract or full text is requested. Search is provider-ordered by relevance. The provider's total match count is displayed separately from the bounded sample. Wildcard punctuation is removed before requesting; no claim of optimal query expansion is made.

## Deduplication and missingness

Keep the first record per valid OpenAlex Work ID or normalized nonempty DOI in response order. Log later duplicates. Exclude records with missing IDs/titles and records explicitly flagged retracted. Unknown years and retraction flags remain unknown. Valid OpenAlex author IDs identify provider-level entities; name strings alone never merge entities. Missing author and institution IDs remain work-local, preventing false cross-paper consolidation.

## Counts and filters

The report recalculates visible works, distinct resolved author IDs, distinct resolved institution IDs and year counts after title, exclusion-phrase, year, work-type, DOI and author filters. The initial sample is provider relevance-selected; the report displays it newest-year first with Work ID tie breaks. A person's count is the number of distinct visible works they appear on. No global productivity or expertise score is generated. User shortlist and exclude decisions change the review list, not the underlying retrieval sample; this distinction is preserved in the displayed counts.

## Network

Pairwise coauthorship edges connect resolved author IDs on the same work. Works with over 30 resolved IDs are omitted from pair construction and explicitly counted; they remain in works and authorship evidence. The report visualizes up to 12 visible author IDs with links supported by at least one visible work. It is a sample view, not a full collaboration network or relationship measure.

## Reproducibility

The allowlisted bibliographic envelope and normalized outputs are saved. Raw affiliation strings, emails, ORCIDs, abstracts, full texts and unrelated nested provider fields are omitted before persistence, including on replay. Canonical JSON hashing covers this minimized snapshot, so changes to retained content or the receipt change its hash. It is not a hash of the untouched HTTP response. Review exports bind that hash. Replay runs offline. A populated output directory cannot be overwritten. A manifest hashes each artifact except the manifest itself.

## What has not been established

No human gold set, factual identity adjudication, market demand, user time savings or independent usability study is claimed. Engineering tests and three live searches establish only the behavior they actually exercise. Public source records remain inspectable; the tool does not certify their correctness.
