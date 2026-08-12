# Finding format

Every reviewer sub-agent reports in this format, and nothing else. The
orchestrating agent parses these, so the field names matter.

```
### <imperative one-line title>
- file: relative/path.cc:120
- guideline: <section title> (<source url>#<anchor>)
- severity: must-fix | should-fix | consider
- problem: <one sentence: what the code does and which rule it misses>
- fix: <the concrete change; include a short before/after when it clarifies>
```

If a reviewer has nothing to report, its entire response is `NO FINDINGS`.

## Severity

| Severity     | Means                                                                          |
| ------------ | ------------------------------------------------------------------------------ |
| `must-fix`   | Violates a rule the guide states outright, with no stated exception that applies. |
| `should-fix` | Violates guidance the code has no particular reason to depart from.             |
| `consider`   | A judgment call the guide raises; reasonable code could go either way.          |

## Rules for reviewers

- Report only what your assigned section actually supports. If a change would be
  an improvement but your section does not speak to it, leave it out — another
  reviewer owns that ground.
- Cite the section you are reviewing against by title and anchor. A finding
  without a citation is noise.
- Read enough of the surrounding file to be sure the code really does what you
  think. Guessing at a call site you did not open produces false positives.
- One finding per problem. If the same mistake repeats across five call sites,
  file one finding and list the locations under `file:`.
- Do not report formatting a formatter already owns.
- Do not edit files. You are read-only; the orchestrating agent applies changes.

## Rules for the orchestrating agent

Apply findings by judgment, not by count:

- Apply `must-fix` and `should-fix` unless the finding is wrong, is based on a
  misreading, or conflicts with a higher-precedence source.
- Apply `consider` when it makes the code clearer to the next reader. Skip it
  when it is churn, or when it trades one defensible choice for another.
- Never silently change behavior. If a finding is right but implies a semantic
  change (different error text, different nil handling, a new API shape), raise
  it in the final report and leave the code alone.
- Deduplicate across reviewers before editing. Several will independently notice
  the same naming problem.
- When two findings conflict, follow the precedence order in `SKILL.md`.
- Record what you rejected and why. The report is as much a deliverable as the
  edits.
