# Literature & Theory Workbench — Agent Operating Rules

## Mission

Operate this repository as a standalone academic literature-review and theoretical-framework workbench. Optimize for traceability, conceptual precision, methodological literacy, and defensible synthesis rather than fluent prose alone.

## Hard workspace boundary

1. Treat this repository as independent from every other local AI/Research Agent project.
2. Never inspect, index, modify, import from, or write to another project directory unless the user explicitly supplies that exact source for the current task.
3. Write generated research artifacts only under `projects/<project-slug>/` unless the user explicitly names another path inside this repository.
4. Custom subagents are advisory evidence workers. They should return structured findings rather than edit files. This is an instruction, not a separate read-only sandbox; permissions are inherited from the parent session. Set actual permissions in the parent client.
5. Do not create symlinks to external research-agent directories.

## Evidence ontology

Always distinguish:

- **SOURCE_FACT**: bibliographic, methodological, sample, result, or quoted information directly verifiable in a source.
- **AUTHOR_CLAIM**: an interpretation or proposition explicitly advanced by the source authors.
- **AGENT_INTERPRETATION**: a defensible inference made by the analyst but not explicitly stated by the source.
- **CROSS_SOURCE_SYNTHESIS**: a pattern inferred from multiple sources.
- **PROPOSED_FRAMEWORK**: the user's/analyst's new conceptual structure or hypothesis.

Never silently convert one type into another.

## Evidence levels

Use E0–E4 from `references/evidence-levels.md`. E3/E4 material must never be written as if it were an established source claim.

## Default pipeline

For a full literature-review request, follow these gates unless the user asks for a narrower task:

- **G0 Scope** — research question, construct definitions, review boundaries, date/geography/discipline, target output.
- **G1 Search** — query families, databases/sources actually used, search log, backward/forward citation chasing, stopping rule.
- **G2 Screening** — inclusion/exclusion decisions with reasons; preserve ambiguous cases.
- **G3 Evidence** — structured paper-level extraction with source locators and confidence.
- **G4 Theory/Mechanism/Methods** — map theory, mechanisms, constructs, methods and contradictions.
- **G5 Synthesis** — thematic/mechanism/theory synthesis and gap diagnosis.
- **G6 Framework** — constructs, arrows, mechanism logic, boundary conditions, rival explanations, propositions/hypotheses.
- **G7 Audit** — claim–citation verification, unsupported generalization, missing contradictory evidence, terminology consistency.
- **G8 Writing** — draft only from the audited evidence base, unless the user explicitly requests an early provisional draft.

A task may stop at any gate if that is what the user asked for.

## Multi-agent policy

Use parallel subagents for read-heavy work when it materially improves quality or context hygiene, especially when any of these conditions hold:

- >= 20 papers or source documents;
- >= 3 independent search/theory/method/mechanism workstreams;
- multiple disciplinary literatures need separate treatment;
- the source corpus is too large for reliable single-thread reading.

Preferred delegation:

- `source_scout`: search/query/citation discovery and source metadata.
- `evidence_reader`: structured paper extraction in bounded batches.
- `theory_analyst`: theory/construct mapping.
- `mechanism_analyst`: causal mechanism synthesis.
- `methods_analyst`: data/method/identification comparison.
- `framework_architect`: framework construction after evidence gates.
- `skeptical_reviewer`: adversarial audit and competing explanations.
- `synthesis_editor`: prose architecture after evidence audit.

Wait for all required agents before final synthesis. Do not let parallel agents independently write overlapping final sections.

## Search discipline

1. Record only sources actually accessed.
2. Distinguish discovery sources from evidence sources.
3. Prefer publisher/DOI/full-text sources for claims; metadata aggregators can support discovery but not substitute for inaccessible evidence.
4. For current or rapidly evolving literatures, verify dates and use fresh sources.
5. Search in concept families, not one giant Boolean query only.
6. Use backward citation chasing for foundations and forward citation chasing for developments when available.
7. Stop using a documented saturation/stopping rule rather than an arbitrary paper count.

## Reading discipline

For each included source, extract at minimum:

- bibliographic identity;
- research question/object;
- theory and level of analysis;
- data, sample, context and period;
- method/identification strategy;
- focal constructs and operationalization;
- main findings;
- mechanisms explicitly claimed or tested;
- moderators/boundary conditions;
- limitations;
- contradictory/null findings;
- exact source locator for decisive claims;
- agent interpretation separately from author claims.

## Theory discipline

Do not label a topical category as a theory. Separate:

- theory;
- construct;
- mechanism;
- policy/intervention/institutional condition;
- outcome;
- empirical regularity.

For every theory, identify its level of analysis, explanatory object, causal logic, boundary conditions, and competing explanations.

## Mechanism discipline

A mechanism must describe a process linking cause to outcome. A list of policy areas, variables, or themes is not a mechanism.

Use the pattern:

`Antecedent / intervention → change in state/opportunity/constraint → decision/behavioral process → outcome`

Mark whether the mechanism is directly tested, explicitly asserted, indirectly supported, or analyst-inferred.

## Gap discipline

Do not generate novelty by claiming “few studies” without search evidence. Prefer specific gaps:

- theoretical integration gap;
- mechanism gap;
- boundary-condition gap;
- construct/measurement gap;
- identification/method gap;
- context/scope gap;
- temporal/dynamic gap;
- contradiction/anomaly gap.

## Writing discipline

1. Organize by argument, mechanism, theory, or debate—not paper-by-paper chronology unless historically necessary.
2. Each paragraph should have a synthesis claim, evidence, qualification, and implication.
3. Keep disagreements visible.
4. Do not overstate causality when designs are associational.
5. Do not cite a paper for a claim it does not support.
6. Preserve the user's requested language; default to academic Chinese when the user writes in Chinese.
7. Use precise discipline-appropriate terminology and avoid generic AI prose.

## Mandatory audit before a final academic draft

Run the equivalent of `lit-audit-citations` and inspect:

- unsupported claims;
- citations without locators for strong claims;
- author claim vs agent interpretation leakage;
- causal language unsupported by design;
- overbroad “consensus” language;
- missing contrary evidence;
- duplicate/near-duplicate sources;
- construct drift and label inconsistency.

If the evidence base is incomplete, label the draft as provisional and state the missing gate rather than fabricating completeness.
