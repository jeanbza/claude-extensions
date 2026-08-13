---
name: google-go-review
description: Review Go code against Effective Go, the Google Go Style Guide, and the go.dev module and language references. Dispatches one sub-agent per guide section, applies what is worth applying, then simplifies and cleans up comments. Use after writing or generating Go code, or when asked for a Go style, readability, or Google Go review.
---

# Google Go code review

We're going to do a Go code review.

## Preflight

Read `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/finding-format.md` first.

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

For this code review, you're going to look at Go files. Not vendored paths,
`testdata/`, and files matching
`^// Code generated .* DO NOT EDIT\.$`.

Gather a baseline, so you can tell your breakage from what you inherited:

```sh
gofmt -l . && go build ./... && go vet ./...
```

Report scope and baseline before dispatching.

## Passes 1–3 — fan-out

These should be fanned out to sub-agents in chunks, in appropriate measure with
respect to how much code is being reviewed. Fewer code, fewer sub-agents (or
none). Lots of code, more sub-agents.

| Pass | Document                | Chunk index                                                      |
| ---- | ----------------------- | ---------------------------------------------------------------- |
| 1    | Effective Go            | `${CLAUDE_PLUGIN_ROOT}/references/effective-go/index.md`          |
| 2    | Go Style Best Practices | `${CLAUDE_PLUGIN_ROOT}/references/style-best-practices/index.md`  |
| 3    | Go Style Decisions      | `${CLAUDE_PLUGIN_ROOT}/references/style-decisions/index.md`       |

Read `${CLAUDE_PLUGIN_ROOT}/references/style-guide.md` yourself first. It is
short, and it settles disputes.

Per pass:

1. Read the chunk index.
2. Dispatch one `jeanbza:go-style-reviewer` per chunk, all in one message.
3. On any `BLOCKED: <path>`, stop and report which chunks went unreviewed.
   Otherwise deduplicate — parallel reviewers converge on the same problems.
4. Adjudicate and apply per `finding-format.md`.
5. Re-run the baseline. Fix what you broke.
6. Report: chunks dispatched, findings received, findings applied.

### Dispatch prompt

> Review a Go change against your assigned section of **<document>**.
>
> Your reference chunk: `<absolute path to NN-*.md>`
> Read it in full before any code. Review against that chunk only.
>
> Files in scope:
> `<paths>`
>
> See the change with: `<the scope command>`
> If it returns nothing, review the listed files as written.
>
> Report in the format at
> `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/finding-format.md`. Read it
> first. Findings only. If you have none, output `NO FINDINGS`.

### Precedence

Style Guide beats Decisions beats Best Practices beats Effective Go. Effective
Go predates modules and generics; prefer the newer documents where they
disagree.

The surrounding package's own convention beats all four. Note divergences in the
report rather than erasing them.

## Pass 4 — simplify

Invoke the `simplify` skill on the same scope. If it is unavailable: collapse
indirection, delete unused parameters and dead branches, replace hand-rolled
loops with standard library calls, unify duplicated helpers. Prefer what the
repository already has. Re-run the baseline.

## Passes 5 and 6 — prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-go-review/prose-cleanup.md`: Pass A
for redundant comments, then Pass B for AI-sounding prose.

## Pass 7 - fix

Run `go fix` on the affected code. `go fix` brings in Go modernisations.

## Pass 8 - test

Make a judicious judgement about whether to run tests before declaring victory.
Most of the time the answer is yes, unless the context in your conversation
suggests otherwise.

## Terminology

Comments and docs you write should always take their vocabulary canonical
references, where available: `references/go-modules/` for Go modules,
`references/go-spec/` for the Go language.

Grep them rather than approximating. Do not refer to "pinning" modules, for=
example. Fix terminology in pass 5 or 6.

## Report

- **Per pass** — received, applied, rejected, one line per rejection.
- **Needs a decision** — findings that were right but would change behavior, and
  conflicts you resolved by precedence.
