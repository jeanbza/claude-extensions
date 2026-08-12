---
name: google-py-review
description: Review Python code against the Google Python Style Guide and — for code that uses Abseil — the Abseil Python guides. Fans out one sub-agent per guide section, applies the findings worth applying, then simplifies, trims redundant comments, and rewrites AI-sounding prose. Use after writing or generating Python code, or when asked for a Python style review, Google Python review, or pyguide review.
---

# Google Python code review

Five passes over a Python change, in order. Passes 1–2 fan out to read-only
sub-agents, one per reference document; you collect their findings and decide
what to apply. Passes 3–5 you do yourself.

Finish each pass — including its edits — before starting the next. Later passes
read code the earlier ones rewrote.

This skill assumes the code already works. It reviews style, idiom, and clarity.
It is not a bug hunt and not a security review.

## Step 0 — preflight, then scope

**Check reference access first.** Read
`${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/finding-format.md` before anything else.

An installed plugin lives under `~/.claude/plugins/cache/`, outside the project,
so reading its files can need a permission grant that a sub-agent cannot obtain
on its own. If that read is denied or blocked, **stop**. Do not start the review.
A reviewer that cannot open its style document falls back on what it already
believes about Python, which is the exact failure this skill exists to prevent,
and it does so without the result looking any different.

Tell the user to grant it once, in `~/.claude/settings.json`:

```json
{ "permissions": { "allow": ["Read(~/.claude/plugins/cache/**)"] } }
```

Or to start the session with `--add-dir` pointing at the plugin directory. Then
stop and wait.

### Scope

Pick the review set, in this order:

1. Files or directories the user named.
2. Uncommitted changes, if `git status --porcelain` shows any.
3. Otherwise the branch: `git diff $(git merge-base HEAD origin/main)...HEAD`.

Reduce to `.py` and `.pyi` files. Drop vendored trees, `site-packages`, and
generated files — anything marked generated in a leading comment, and `_pb2.py`
and `_pb2.pyi` protocol buffer output.

If nothing is left, say so and stop.

Then establish a baseline from whatever the repository configures. Check
`pyproject.toml`, `setup.cfg`, `.pylintrc`, `ruff.toml`, and `mypy.ini`, and run
the linters, formatters, and type checkers that are actually set up — commonly
some of `ruff check`, `ruff format --check`, `black --check`, `pylint`, `mypy`,
`pyright`. Run them over the scope, not the whole repository. Say what you found
and what you ran. If the project configures none, say that and continue.

Do not add a linter the project does not use, and do not reformat to a style the
project has not adopted.

Tell the user what you are reviewing — file count, modules, and the baseline
result — before you start dispatching.

## Pass 1 — Google Python Style Guide

Read `${CLAUDE_PLUGIN_ROOT}/references/python-style-guide/index.md` for the
chunk list. Dispatch one `jeanbza:python-style-reviewer` sub-agent per
chunk, **all in a single message** so they run in parallel.

Use the dispatch template below with document title *Google Python Style Guide*.

Then collect, deduplicate, adjudicate, and apply per
`${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/finding-format.md`. Re-run the baseline
checks afterward.

If any reviewer returns `BLOCKED: <path>`, stop — sub-agents lack the read
permission from the preflight. Report which chunks were unreviewed rather than
applying a partial pass as if it were complete. The same applies to pass 2.

Note that the guide's section 3 rules on layout — indentation, line length,
blank lines, whitespace — are the formatter's job wherever the project runs one.
Do not hand-edit those; let the configured formatter settle them, and drop
findings that only restate what it already enforces.

## Pass 2 — Abseil Python guides

First determine whether the change uses Abseil at all:

```sh
grep -rn 'from absl\|import absl' <files in scope>
```

If it does not, skip this pass and say so.

If it does, map what the change uses to guides and dispatch one sub-agent per
matched guide, all in a single message. The full list is in
`${CLAUDE_PLUGIN_ROOT}/references/abseil/guides/index.md`.

| What the change uses                             | Guide         |
| ------------------------------------------------ | ------------- |
| `absl.app`, `app.run`, a `main()` entry point    | `app.md`      |
| `absl.flags`, `FLAGS`, `DEFINE_*`                | `flags.md`    |
| `absl.logging`                                   | `logging.md`  |
| `absl.testing` — `absltest`, `parameterized`     | `testing.md`  |

Dispatch only for guides the change actually engages. A reviewer holding a guide
for a module the code never imports produces nothing but latency.

Then collect, adjudicate, and apply as in pass 1.

## Dispatch prompt template

> Review a Python change against **<document title>**.
>
> Your reference document: `<absolute path>`
> Read it in full before reading any code. Review against that document only.
>
> Files in scope:
> `<explicit list of file paths>`
>
> See the change with: `<the exact git command from Step 0>`
> If that command returns nothing, review the listed files as written.
>
> Report findings in the format at
> `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/finding-format.md`. Read that file first.
> Output findings and nothing else. If you have none, output `NO FINDINGS`.

## Precedence

When findings conflict:

1. **Google Python Style Guide** — the normative document.
2. **Abseil Python guides** — authoritative on how to use the library.
3. The project's configured formatter and linter. Where they disagree with the
   guide on layout, the configured tool wins; that is what will run in CI. Note
   the divergence in the report.
4. The code's own established local convention.

The guide states most rules with explicit exceptions. Check them before applying
a finding — the exception is part of the rule.

## Pass 3 — simplify

Invoke the `simplify` skill on the same scope.

If it is unavailable, do the pass directly: collapse needless indirection,
delete unused parameters and dead branches, replace hand-rolled loops with
standard library calls that already do the job, unify duplicated helpers, and
pull code to a consistent level of abstraction. Reuse what the repository
already has instead of adding a second way to do the same thing.

Re-run the baseline checks afterward.

## Pass 4 — redundant comments

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/prose-cleanup.md`, Pass A.

## Pass 5 — AI-sounding prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-py-review/prose-cleanup.md`, Pass B.

## Final report

Structure it as:

- **Scope** — what was reviewed, and which checks you ran.
- **Per pass** — findings received, applied, and rejected. Give the reason for
  each rejection; one line each is enough. Say explicitly if you skipped pass 2,
  and why.
- **Not applied, needs a decision** — anything correct that would change
  behavior, and conflicts you resolved by precedence that the user might want
  resolved the other way.
- **Verification** — the final linter, formatter, and type-checker results, and
  the test result if you ran tests.

State check and test results honestly. If the project configures no checks you
could run, say so plainly rather than implying the change was verified.
