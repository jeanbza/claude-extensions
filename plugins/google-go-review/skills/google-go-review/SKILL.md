---
name: google-go-review
description: Review Go code against Effective Go, the Google Go Style Guide (guide, decisions, best practices), and the go.dev module and language references. Fans out one sub-agent per guide section, applies the findings worth applying, then simplifies, trims redundant comments, and rewrites AI-sounding prose. Use after writing or generating Go code, or when asked for a Go style review, Go readability review, or Google Go review.
---

# Google Go code review

Six passes over a Go change, in order. Passes 1–3 fan out to read-only
sub-agents, one per section of a style document; you collect their findings and
decide what to apply. Passes 4–6 you do yourself.

Finish each pass — including its edits — before starting the next. Later passes
read code the earlier ones rewrote.

This skill assumes the code already works. It reviews style, idiom, and clarity.
It is not a bug hunt and not a security review.

## Step 0 — preflight, then scope

**Check reference access first.** Read
`${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/finding-format.md` before anything else.

An installed plugin lives under `~/.claude/plugins/cache/`, outside the project,
so reading its files can need a permission grant that a sub-agent cannot obtain
on its own. If that read is denied or blocked, **stop**. Do not start the review.
A reviewer that cannot open its style document falls back on what it already
believes about Go, which is the exact failure this skill exists to prevent, and
it does so without the result looking any different.

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

Reduce to Go files. Drop vendored paths, `testdata/`, and generated files —
anything whose first lines match `^// Code generated .* DO NOT EDIT\.$`.

If nothing is left, say so and stop.

Then establish a baseline so you can tell your own breakage from what you
inherited:

```sh
gofmt -l .
go build ./...
go vet ./...
```

Tell the user what you are reviewing — file count, package names, and the
baseline result — before you start dispatching.

## Passes 1–3 — the fan-out

Each pass covers one document. Run them in this order, because later documents
are more specific and take precedence over earlier ones:

| Pass | Document                | Chunk index                                            |
| ---- | ----------------------- | ------------------------------------------------------ |
| 1    | Effective Go            | `${CLAUDE_PLUGIN_ROOT}/references/effective-go/index.md`        |
| 2    | Go Style Best Practices | `${CLAUDE_PLUGIN_ROOT}/references/style-best-practices/index.md` |
| 3    | Go Style Decisions      | `${CLAUDE_PLUGIN_ROOT}/references/style-decisions/index.md`     |

Read `${CLAUDE_PLUGIN_ROOT}/references/style-guide.md` yourself before pass 1.
It is short, it is the canonical document, and it settles disputes among the
others.

For each pass:

1. Read the chunk index to get the chunk list.
2. Dispatch one `jeanbza:go-style-reviewer` sub-agent per chunk, **all in
   a single message** so they run in parallel. Use the prompt template below.
3. Collect every reviewer's findings. If any reviewer returns
   `BLOCKED: <path>`, stop — sub-agents lack the read permission from the
   preflight. Report which chunks were unreviewed rather than applying a
   partial pass as if it were complete. Otherwise deduplicate: parallel
   reviewers converge on the same naming and error-handling problems.
4. Adjudicate and apply, per the rules in
   `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/finding-format.md`.
5. Re-run `gofmt -l`, `go build ./...`, and `go vet ./...`. Fix what you broke
   before moving on.
6. Report the pass in one line: chunks dispatched, findings received, findings
   applied.

### Dispatch prompt template

> Review a Go change against your assigned section of **<document title>**.
>
> Your reference chunk: `<absolute path to NN-*.md>`
> Read it in full before reading any code. Review against that chunk only.
>
> Files in scope:
> `<explicit list of file paths>`
>
> See the change with: `<the exact git command from Step 0>`
> If that command returns nothing, review the listed files as written.
>
> Report findings in the format at
> `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/finding-format.md`. Read that file first.
> Output findings and nothing else. If you have none, output `NO FINDINGS`.

### Precedence

When findings conflict, the Google Go style documents rank themselves:

1. **Style Guide** (`style-guide.md`) — normative and canonical. Wins outright.
2. **Style Decisions** — normative, not canonical.
3. **Best Practices** — neither; guidance to follow absent a reason not to.
4. **Effective Go** — background on idiom, and not actively maintained. Where it
   predates modules or generics, prefer the newer documents.

Below all four: the code's own established local convention. A change that is
internally consistent with a package that has its own house style is usually
better left consistent — note the divergence in the report instead.

## Pass 4 — simplify

Invoke the `simplify` skill on the same scope.

If it is unavailable, do the pass directly: collapse needless indirection,
delete unused parameters and dead branches, replace hand-rolled loops with
standard library calls that already do the job, unify duplicated helpers, and
pull code to a consistent level of abstraction. Reuse what the repository
already has instead of adding a second way to do the same thing.

Re-run the baseline commands afterward.

## Pass 5 — redundant comments

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/prose-cleanup.md`, Pass A.

## Pass 6 — AI-sounding prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/prose-cleanup.md`, Pass B.

## Terminology (applies to every pass)

Whenever you write or rewrite a comment, doc comment, commit message, or piece
of documentation:

- **Modules.** Use the vocabulary of the Go Modules Reference —
  `${CLAUDE_PLUGIN_ROOT}/references/go-modules/`. Module path, module graph,
  main module, build list, minimal version selection, replace directive,
  vendoring, module cache, `go.sum`, canonical version, pseudo-version. Do not
  call a module a package, a package a library, or a version a release.
- **The language.** Use the vocabulary of the Go specification —
  `${CLAUDE_PLUGIN_ROOT}/references/go-spec/`. Method set, receiver, type
  parameter, type set, underlying type, composite literal, conversion versus
  assertion, panic versus error, goroutine, channel direction. Do not call a
  method a function, a struct an object, or a type assertion a cast.

Both directories carry an `index.md`; grep them when you are unsure of a term
rather than approximating one. Correcting terminology in a comment is a Pass 5
or Pass 6 edit — do not derail an earlier pass for it.

## Final report

Structure it as:

- **Scope** — what was reviewed.
- **Per pass** — findings received, applied, and rejected. Give the reason for
  each rejection; one line each is enough.
- **Not applied, needs a decision** — anything correct that would change
  behavior, plus conflicts you resolved by precedence that the user might want
  resolved the other way.
- **Verification** — the final `gofmt -l`, `go build ./...`, `go vet ./...`
  results, and the test result if you ran tests.

State test results honestly. If you did not run the tests, say you did not run
them.
