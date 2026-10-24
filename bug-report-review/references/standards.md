# Where the checks come from

Read this to justify a verdict, to answer "says who?", or to adapt the rubric
to a project that already mandates a different template.

## The three layers

| Layer | Source | Contributes |
|---|---|---|
| Structure | **ISO/IEC/IEEE 29119-3**, incident report | Which fields must exist at all (groups A, B) |
| Vocabulary | **IEEE 1044-2009** | Which values those fields may take, and the severity/priority split (group D) |
| Evidence | Kaner *Bug Advocacy*; Mozilla/Chromium bug-writing guidelines; `root-cause-fix` phase 1 | What makes a report analysable rather than merely complete (groups B, C) |

### ISO/IEC/IEEE 29119-3 — Test documentation

The current international standard for testing documentation. Its incident
report covers identification, context and environment, description of the
event, expected vs. actual result, impact, severity, priority, status,
originator and references. It supersedes the Test Incident Report of
IEEE 829-2008 — cite 29119-3, not 829.

It is deliberately process-neutral, which is why it maps cleanly onto a Jira
Bug screen: summary, environment, description, versions, priority, status,
reporter, links. Group A and the shape of group B come from here.

What it does *not* give you: how much evidence is enough. It says an incident
report has a description of the event; it does not say that a screenshot of a
stack trace is worthless. Hence layer 3.

### IEEE 1044-2009 — Classification for software anomalies

Supplies the attribute vocabulary for classifying software anomalies — among
them defect type, insertion activity, disposition, severity and priority.

Two things matter for this skill:

1. **Severity and priority are different attributes.** Severity is a property
   of the anomaly's effect on the system; priority is a management decision
   about when to address it. Conflating them destroys both.
2. **Disposition must be recorded.** "Closed" is not an outcome; "duplicate of
   X", "not reproducible after N attempts", "works as designed because …" are.

Without this layer, a conformance check degrades into "is the field non-empty",
which is the failure mode of every field-validation plugin.

### Kaner, Mozilla, Chromium — practitioner rules

No authority, high value. They contribute:

- one defect per report (B5);
- minimal reproducer with concrete data (B1);
- verbatim observed behaviour (B3);
- regression range — "worked in build N, fails in N+1" (C3);
- the reporter's workaround read as a triggering condition (C4).

### `root-cause-fix` phase 1 — why group C is normative here

The `root-cause-fix` skill (a companion skill; this one works without it) mines
a ticket in its first phase in a fixed order of value: the
deepest application stack frame, the failing and working input side by side,
and the reporter's workaround. Group C simply promotes those to entry criteria.

This is the reason the skill issues two verdicts instead of a single score. A
report can satisfy 29119-3 completely and still leave analysis with nothing to
anchor on; conversely, the unstructured prose ticket that contains a trace, a
version delta and two SQL statements is fix-ready today. Structure serves
analysis, not the reverse.

## Deliberately not used as the basis

| Candidate | Why not |
|---|---|
| **ISTQB** defect-report contents | A training syllabus, not a standard, and its defect-report contents build on 29119-3. Fine to quote when talking to testers. |
| **IEEE 829-2008** | Superseded by 29119-3. Citing it dates the review. |
| **SARIF 2.1.0** (OASIS) | An interchange format for *tool-generated* findings (SAST, linters). Right answer for scanner output, wrong shape for a human report. If a ticket originates from a scanner, take the rule id and location from the SARIF result and treat them as A1/C1 evidence. |
| **Bugzilla / Mozilla guidelines alone** | Excellent heuristics, no classification vocabulary, no authority to cite in an audit. Used as layer 3, not as the spine. |

## Adapting to a project that mandates its own template

Keep the rubric, remap the evidence:

1. Fetch the project's Bug screen (see [jira.md](jira.md)) and the mandated
   description headings.
2. Map each rubric check to the field or heading that is supposed to carry it,
   and pass the mandated headings to the screening script with `--alias`
   (SKILL.md, step 2) so its section signals follow the project's template.
3. Report a check as a gap only when *no* location in the ticket carries the
   evidence — never because the project's template lacks a section for it.
4. If the mandated template has no place for group C at all, say so once, and
   recommend adding an "Isolation" heading rather than fighting the template on
   every ticket.

## Traceability

When a review must be defensible (audit, customer escalation, process
assessment), cite the check by name and id, the layer it comes from, and the
evidence, e.g.

> Stack trace (C1) — gap, blocker. No trace as text: the attached PNG crops the
> `Caused by:` block, so the failing component cannot be identified. Basis: the
> description of the incident that an ISO/IEC/IEEE 29119-3 incident report
> calls for, and the isolation-evidence layer (group C).

Do not quote or paraphrase a standard's wording, and do not cite clause
numbers, unless you have verified them against the actual standard text.
Naming the standard and what it covers is enough; a wrong quotation or clause
number is worse than none.
