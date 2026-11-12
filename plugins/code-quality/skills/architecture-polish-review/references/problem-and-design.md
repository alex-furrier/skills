# Problem and design understanding

Use this optional lens when a consequential design choice depends on recovering
why behavior belongs where it does, or when a plausible plan leaves that unclear.
Skip it for mechanical changes and established local fixes. Keep the result in
the existing plan or review; add no report, grade, approval gate, or required ADR.

## Reconstruct before reshaping

Start with one concrete user or caller scenario. Connect the relevant domain
facts to behavior, the owning module, its interface and a discriminating test.
For existing code, trace actual callers, state, effects and nearby decisions.
Distinguish observed behavior, documented rationale, inferred rationale and the
proposed change. Do not infer intent from a tidy-looking module map. Ask only
when a missing answer could change the decision; otherwise state the limit.

For greenfield work, sketch realistic caller usage before choosing modules.
Separate requirements from assumptions. Compare two small designs only when
an unresolved choice could materially change caller burden or ownership.

## Reduce knowledge callers must carry

Inspect ordering rules, configuration, errors and duplicated decisions as part
of the interface. Name what a proposed module hides and what callers still
must understand. Prefer a general mechanism when it simplifies current uses;
keep application policy with its existing owner. Remove a special case only
when the general behavior preserves its real contract. Keep distinctions that
represent genuine domain, authorization or lifecycle rules.

Treat depth, the deletion test and adapter counts as heuristics. A single
side-effect adapter can earn isolation; a long coherent implementation can earn
its interface. Do not introduce a framework for hypothetical consumers or delete
internal tests merely because a new interface exists.

## Rehearse a change and stop

Use one requested or evidenced plausible next change to test the design: show
where it belongs, what callers would change, which invariant survives and what
observation could refute the claim. Skip this exercise when no useful extension
is known; do not manufacture scope. Preserve characterization evidence before a
brownfield extraction. Recommend the current structure when it already fits.

Fold only useful conclusions into the owning output. A short caller example,
reason for the chosen owner and focused proof can be enough. Stop when the next
implementation step is supported; more documentation cannot establish shared
understanding by itself. Leave product choices and adoption to their actual
owners rather than recording an unresolved choice as adopted.

## Sources and adaptation

Peter Naur's [Programming as Theory Building](https://pages.cs.wisc.edu/~remzi/Naur.pdf)
(1985), section “The Theory To Be Built by the Programmer,” describes understanding
through problem correspondence, justification and modification. The scanned
reprint's printed page 231 begins these three areas. This lens adapts them as
questions; it does not claim a document captures a programmer's theory.

John Ousterhout's [A Philosophy of Software Design](https://web.stanford.edu/~ouster/cgi-bin/book.php)
(second edition, 2021), especially the author-provided Chapter 6 extract, informs
the current-needs mechanism and caller-knowledge prompts. The Matt-derived depth,
locality and interface vocabulary remains in the existing architecture references.
These are contextual design heuristics, not rules that override local contracts.
