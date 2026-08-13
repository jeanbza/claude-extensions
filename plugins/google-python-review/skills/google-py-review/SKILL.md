---
name: google-py-review
description: Review Python code against the Google Python Style Guide and — for code that uses Abseil — the Abseil Python guides. Dispatches one sub-agent per guide section, applies what is worth applying, then simplifies and cleans up comments. Use after writing or generating Python code, or when asked for a Python style, Google Python, or pyguide review.
---

# Google Python code review

We're going to do a Python code review.

## Preflight

Read `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/finding-format.md` first.

If that read is blocked, stop. Sub-agents cannot grant themselves access, and one
that cannot open its style document reviews from memory instead — which looks
identical to the real thing. Ask for this in `~/.claude/settings.json`, then wait:

```json
{ "permissions": { "allow": ["Read(~/.claude/plugins/cache/**)"] } }
```

## Scope

In order of preference:

1. Files or directories the user named.
2. Uncommitted changes, if `git status --porcelain` shows any.
3. `git diff $(git merge-base HEAD origin/main)...HEAD`.

For this code review, you're going to look at `.py` and `.pyi` files. Not
vendored trees, `site-packages`, or generated output like `_pb2.py` and
`_pb2.pyi`.

Gather a baseline from whatever the project configures — `pyproject.toml`,
`setup.cfg`, `.pylintrc`, `ruff.toml`, `mypy.ini` — and run the tools that are
actually set up, over the scope rather than the whole repository. Usually some
of `ruff check`, `ruff format --check`, `black --check`, `pylint`, `mypy`,
`pyright`. Say what you found and what you ran.

Do not add a linter the project does not use, and do not reformat to a style it
has not adopted.

Report scope and baseline before dispatching.

## Passes 1–2 — fan-out

These should be fanned out to sub-agents in chunks, in appropriate measure with
respect to how much code is being reviewed. Less code, fewer sub-agents (or
none). Lots of code, more sub-agents.

| Pass | Document                  | Chunk index                                                    |
| ---- | ------------------------- | -------------------------------------------------------------- |
| 1    | Google Python Style Guide | `${CLAUDE_PLUGIN_ROOT}/references/python-style-guide/index.md`  |
| 2    | Abseil Python guides      | `${CLAUDE_PLUGIN_ROOT}/references/abseil/guides/index.md`       |

The guide's section 3 layout rules — indentation, line length, blank lines,
whitespace — belong to the formatter wherever the project runs one. Do not
hand-edit those, and drop findings that only restate what it already enforces.

Pass 2 runs only if the change uses Abseil:

```sh
grep -rn 'from absl\|import absl' <files in scope>
```

If it does, dispatch one sub-agent per guide the change actually engages. A
reviewer holding a guide for a module the code never imports produces nothing
but latency.

| What the change uses                          | Guide        |
| --------------------------------------------- | ------------ |
| `absl.app`, `app.run`, a `main()` entry point | `app.md`     |
| `absl.flags`, `FLAGS`, `DEFINE_*`             | `flags.md`   |
| `absl.logging`                                | `logging.md` |
| `absl.testing` — `absltest`, `parameterized`  | `testing.md` |

Per pass:

1. Read the chunk index.
2. Dispatch one `jeanbza:python-style-reviewer` per chunk, all in one message.
3. On any `BLOCKED: <path>`, stop and report which chunks went unreviewed.
   Otherwise deduplicate — parallel reviewers converge on the same problems.
4. Adjudicate and apply per `finding-format.md`.
5. Re-run the baseline checks. Fix what you broke.
6. Report: chunks dispatched, findings received, findings applied.

### Dispatch prompt

> Review a Python change against **<document>**.
>
> Your reference document: `<absolute path>`
> Read it in full before any code. Review against that document only.
>
> Files in scope:
> `<paths>`
>
> See the change with: `<the scope command>`
> If it returns nothing, review the listed files as written.
>
> Report in the format at
> `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/finding-format.md`. Read it
> first. Findings only. If you have none, output `NO FINDINGS`.

### Precedence

Style Guide beats Abseil guides. The project's configured formatter beats the
guide on layout — that is what runs in CI — and the surrounding module's own
convention beats all of them. Note divergences in the report rather than erasing
them.

The guide states most rules with explicit exceptions. Check them before applying
a finding — the exception is part of the rule.

## Pass 3 — simplify

Invoke the `simplify` skill on the same scope. If it is unavailable: collapse
indirection, delete unused parameters and dead branches, replace hand-rolled
loops with standard library calls, unify duplicated helpers. Prefer what the
repository already has. Re-run the baseline checks.

## Passes 4 and 5 — prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/prose-cleanup.md`: Pass A
for redundant comments, then Pass B for AI-sounding prose.

## Pass 6 — modernize

If the project runs ruff, apply its pyupgrade rules (`ruff check --select UP`)
over the scope. Stay inside the `requires-python` the project declares — do not
introduce syntax its floor does not support. If the project runs neither ruff
nor pyupgrade, skip this.

## Pass 7 — test

Make a judicious judgement about whether to run tests before declaring victory.
Most of the time the answer is yes, unless the context in your conversation
suggests otherwise.

## Report

- **Per pass** — received, applied, rejected, one line per rejection. Say if you
  skipped pass 2, and why.
- **Needs a decision** — findings that were right but would change behavior, and
  conflicts you resolved by precedence.
