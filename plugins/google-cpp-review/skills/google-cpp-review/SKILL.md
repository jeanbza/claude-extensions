---
name: google-cpp-review
description: Review C++ code against the Google C++ Style Guide, the Abseil atomics guidance, and — for code that uses Abseil — the Abseil library guides. Fans out one sub-agent per guide section, applies the findings worth applying, then simplifies, trims redundant comments, and rewrites AI-sounding prose. Use after writing or generating C++ code, or when asked for a C++ style review, Google C++ review, or Abseil review.
---

# Google C++ code review

Six passes over a C++ change, in order. Passes 1–3 fan out to read-only
sub-agents, one per reference document; you collect their findings and decide
what to apply. Passes 4–6 you do yourself.

Finish each pass — including its edits — before starting the next. Later passes
read code the earlier ones rewrote.

This skill assumes the code already compiles and works. It reviews style, idiom,
and clarity. It is not a bug hunt and not a security review — with one exception:
pass 2 is about a class of concurrency bug that style review is the last chance
to catch.

## Step 0 — preflight, then scope

**Check reference access first.** Read
`${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/finding-format.md` before anything else.

An installed plugin lives under `~/.claude/plugins/cache/`, outside the project,
so reading its files can need a permission grant that a sub-agent cannot obtain
on its own. If that read is denied or blocked, **stop**. Do not start the review.
A reviewer that cannot open its style document falls back on what it already
believes about C++, which is the exact failure this skill exists to prevent, and
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

Reduce to C++ files — `.cc`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.inc`. Keep headers
and their implementation files together even when only one side changed; the
guide's rules on ownership, inlining, and include order span both. Drop
third-party and vendored trees, and generated files such as `.pb.h`, `.pb.cc`,
and anything marked generated in a leading comment.

If nothing is left, say so and stop.

Then establish a baseline, using whatever the repository actually has. Look for
`BUILD`/`BUILD.bazel`, `CMakeLists.txt`, a `Makefile`, or `compile_commands.json`
and use the matching command; if a `.clang-format` exists, run
`clang-format --dry-run --Werror` over the scope. Say what you found and what
you ran. If the project has no build you can invoke, say that too and continue —
you will be relying on review rather than the compiler, which is worth telling
the user.

Tell the user what you are reviewing — file count, targets, and the baseline
result — before you start dispatching.

## Pass 1 — Google C++ Style Guide

Read `${CLAUDE_PLUGIN_ROOT}/references/cpp-style-guide/index.md` for the chunk
list. Dispatch one `jeanbza:cpp-style-reviewer` sub-agent per chunk, **all
in a single message** so they run in parallel.

Use the dispatch template below with document title *Google C++ Style Guide*.

Then collect, deduplicate, adjudicate, and apply per
`${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/finding-format.md`. Rebuild and re-run the
formatter check afterward.

If any reviewer returns `BLOCKED: <path>`, stop — sub-agents lack the read
permission from the preflight. Report which chunks were unreviewed rather than
applying a partial pass as if it were complete. The same applies to passes 2
and 3.

## Pass 2 — the danger of atomics

Dispatch a single `jeanbza:cpp-style-reviewer` sub-agent against
`${CLAUDE_PLUGIN_ROOT}/references/abseil/atomic-danger.md`.

Run this pass whether or not the code uses Abseil — it is about
`std::atomic` and lock-free reasoning, not about the library.

Skip it only when the scope contains no atomics, no `std::memory_order`, no
hand-rolled synchronization, and no lock-free data structures. Say that you
skipped it and why.

Findings from this pass outrank style findings. If a reviewer says a lock-free
construction is unsound, do not restyle it — surface it in the final report as a
correctness question for the user, and leave the code alone unless the fix is
unambiguous.

## Pass 3 — Abseil guides

First determine whether the change uses Abseil at all:

```sh
grep -rn 'absl::\|#include "absl/' <files in scope>
```

If it does not, skip this pass and say so.

If it does, map the Abseil headers the change includes or uses to guides, and
dispatch one sub-agent per matched guide, all in a single message. The full list
is in `${CLAUDE_PLUGIN_ROOT}/references/abseil/guides/index.md`.

| Abseil headers used                                              | Guide                       |
| ---------------------------------------------------------------- | --------------------------- |
| `absl/base/` — attributes, optimization, casts, call_once, thread_annotations | `base.md`         |
| `absl/base/options.h`                                            | `options.md`                |
| `absl/container/`                                                | `container.md`              |
| `absl/flags/`                                                    | `flags.md`                  |
| `absl/hash/`                                                     | `hash.md`                   |
| `absl/log/`, `absl/log/check.h`                                  | `logging.md`                |
| `absl/meta/type_traits.h`                                        | `meta.md`                   |
| `absl/numeric/` — int128, bits                                   | `numeric.md`                |
| `absl/random/`                                                   | `random.md`                 |
| `absl/status/`                                                   | `status.md`, `status-codes.md` |
| `absl/strings/`                                                  | `strings.md`                |
| `absl/strings/str_format.h`                                      | `format.md`                 |
| an `AbslStringify` overload, or a type formatted by one          | `abslstringify.md`          |
| `absl/synchronization/` — mutex, notification, barrier           | `synchronization.md`        |
| `absl/time/`                                                     | `time.md`                   |
| `absl/types/` — span, optional, variant, any                     | `types.md`                  |

Dispatch only for guides the change actually engages. A reviewer holding a guide
for a library the code never touches produces nothing but latency.

Then collect, adjudicate, and apply as in pass 1.

## Dispatch prompt template

> Review a C++ change against **<document title>**.
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
> `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/finding-format.md`. Read that file first.
> Output findings and nothing else. If you have none, output `NO FINDINGS`.

## Precedence

When findings conflict:

1. **Atomics correctness** (pass 2) beats everything. Style never justifies an
   unsound memory model.
2. **Google C++ Style Guide** — the normative document for style.
3. **Abseil guides** — authoritative on how to use the library, and on the
   idioms the style guide leaves open.
4. The code's own established local convention. A change that is internally
   consistent with a file that has its own house style is usually better left
   consistent; note the divergence in the report instead.

The style guide states most rules with explicit exceptions. Check them before
applying a finding — the exception is part of the rule.

## Pass 4 — simplify

Invoke the `simplify` skill on the same scope.

If it is unavailable, do the pass directly: collapse needless indirection,
delete unused parameters and dead branches, replace hand-rolled loops with
standard library or Abseil algorithms that already do the job, unify duplicated
helpers, and pull code to a consistent level of abstraction. Reuse what the
repository already has instead of adding a second way to do the same thing.

Re-run the baseline build afterward.

## Pass 5 — redundant comments

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/prose-cleanup.md`, Pass A.

## Pass 6 — AI-sounding prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/prose-cleanup.md`, Pass B.

## Terminology (applies to every pass)

Whenever you write or rewrite a comment, commit message, or piece of
documentation about the C++ language itself, get the terms right. Check
https://en.cppreference.com/ when you are unsure — it is the reference of
record for value categories, lifetime, initialization, overload resolution, and
the memory model.

Then write it for a working engineer, not for the standard. cppreference is the
source of truth about *what is correct*, not a model for *how to say it*:

| cppreference register                                             | What to write                             |
| ----------------------------------------------------------------- | ----------------------------------------- |
| "the behavior is undefined if the referent's lifetime has ended"  | "dangles if the parent is destroyed first" |
| "participates in overload resolution only if ..."                 | "only picked when ..."                    |
| "an lvalue of type T designating the object"                      | "the object itself, not a copy"           |

Precision without jargon. Say *xvalue* only when the distinction from *prvalue*
is what the reader needs; say "a temporary" when that is enough. Never trade
accuracy for approachability — if the precise term is the only correct one, use
it and explain it in the same breath.

Correcting terminology in a comment is a Pass 5 or Pass 6 edit — do not derail
an earlier pass for it.

## Final report

Structure it as:

- **Scope** — what was reviewed, and what build or format check you ran.
- **Per pass** — findings received, applied, and rejected. Give the reason for
  each rejection; one line each is enough. Say explicitly if you skipped pass 2
  or pass 3, and why.
- **Not applied, needs a decision** — anything correct that would change
  behavior, every atomics finding you did not act on, and conflicts you resolved
  by precedence that the user might want resolved the other way.
- **Verification** — the final build and format-check results, and the test
  result if you ran tests.

State build and test results honestly. If the project has no build you could
run, say so plainly rather than implying the change was verified.
