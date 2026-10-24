# Writing a new report

Read this when there is no report yet and the user wants one written. The
review workflow in SKILL.md still applies — the draft goes through it before
anything is created.

1. **Collect the evidence analysis needs first.** Take what the user has
   already given you — a pasted error, a log, a screenshot — and ask in one
   message for what is missing, in this order: the exact error text or stack
   trace, as text; the failing input and a comparable working one; the last
   version where it worked and the first where it fails; any workaround,
   phrased as the condition under which it works; when it happened, on which
   system, and where the logs are. Then: steps from a known starting state with
   the concrete data used, the expected result and where that expectation comes
   from, and how often it happens. A request for material is not a stop point —
   the one-question rule is for decisions.
2. **Write the draft** with
   [assets/description-template.txt](../assets/description-template.txt), and a
   summary that names the object, the observable failure and the trigger. Keep
   the user's words and data verbatim, mark anything you inferred as
   `(assumed)`, and write "not known yet" rather than inventing a value.
   Propose a severity from the effect on the system, with a one-clause reason;
   leave priority to the team.
3. **Review the draft** with steps 2-4 of SKILL.md — screen it with `--text`,
   judge it against the rubric — and list the remaining gaps under the draft as
   open questions.
4. **Stop.** Ask whether to revise the draft or create the issue. Creating it
   is a write: the exact text must be confirmed first (SKILL.md, step 5,
   *Writing to Jira*).
