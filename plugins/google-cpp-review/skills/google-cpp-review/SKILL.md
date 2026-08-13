---
name: google-cpp-review
description: Review C++ code against the Google C++ Style Guide, Abseil's atomics guidance, and — for code that uses Abseil — the Abseil library guides. Dispatches one sub-agent per guide section, applies what is worth applying, then simplifies and cleans up comments. Use after writing or generating C++ code, or when asked for a C++ style, Google C++, or Abseil review.
---

# Google C++ code review

We're going to do a C++ code review.

## Preflight

Read `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/finding-format.md` first.

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

For this code review, you're going to look at `.cc`, `.cpp`, `.cxx`, `.h`,
`.hpp`, and `.inc` files. Not third-party or vendored trees, and not generated
output like `.pb.h` and `.pb.cc`. Keep headers with their implementation files
even when only one side changed — the rules on ownership, inlining, and include
order span both.

Gather a baseline from whatever the project actually has: `BUILD`/`BUILD.bazel`,
`CMakeLists.txt`, a `Makefile`, `compile_commands.json`, `.clang-format`. Say
what you found and what you ran. If there is no build you can invoke, say that
too — you are relying on review rather than the compiler, and that is worth
knowing.

Report scope and baseline before dispatching.

## Passes 1–3 — fan-out

These should be fanned out to sub-agents in chunks, in appropriate measure with
respect to how much code is being reviewed. Less code, fewer sub-agents (or
none). Lots of code, more sub-agents.

| Pass | Document               | Chunk index                                                    |
| ---- | ---------------------- | -------------------------------------------------------------- |
| 1    | Google C++ Style Guide | `${CLAUDE_PLUGIN_ROOT}/references/cpp-style-guide/index.md`     |
| 2    | The danger of atomics  | `${CLAUDE_PLUGIN_ROOT}/references/abseil/atomic-danger.md`      |
| 3    | Abseil guides          | `${CLAUDE_PLUGIN_ROOT}/references/abseil/guides/index.md`       |

Pass 2 is one sub-agent, not a fan-out, and it runs whether or not the project
uses Abseil — it is about `std::atomic` and lock-free reasoning, not the
library. Skip it only when the scope has no atomics, no `std::memory_order`, and
no hand-rolled synchronization. Say that you skipped it.

Pass 3 runs only if the change uses Abseil:

```sh
grep -rn 'absl::\|#include "absl/' <files in scope>
```

If it does, dispatch one sub-agent per guide the change actually engages. A
reviewer holding a guide for a library the code never touches produces nothing
but latency.

| Headers used                                                     | Guide                          |
| ----------------------------------------------------------------- | ------------------------------ |
| `absl/base/` — attributes, optimization, casts, thread_annotations | `base.md`                      |
| `absl/base/options.h`                                            | `options.md`                   |
| `absl/container/`                                                | `container.md`                 |
| `absl/flags/`                                                    | `flags.md`                     |
| `absl/hash/`                                                     | `hash.md`                      |
| `absl/log/`, `absl/log/check.h`                                  | `logging.md`                   |
| `absl/meta/type_traits.h`                                        | `meta.md`                      |
| `absl/numeric/` — int128, bits                                   | `numeric.md`                   |
| `absl/random/`                                                   | `random.md`                    |
| `absl/status/`                                                   | `status.md`, `status-codes.md` |
| `absl/strings/`                                                  | `strings.md`                   |
| `absl/strings/str_format.h`                                      | `format.md`                    |
| an `AbslStringify` overload, or a type formatted by one           | `abslstringify.md`             |
| `absl/synchronization/` — mutex, notification, barrier            | `synchronization.md`           |
| `absl/time/`                                                     | `time.md`                      |
| `absl/types/` — span, optional, variant, any                     | `types.md`                     |

Per pass:

1. Read the chunk index.
2. Dispatch one `jeanbza:cpp-style-reviewer` per chunk, all in one message.
3. On any `BLOCKED: <path>`, stop and report which chunks went unreviewed.
   Otherwise deduplicate — parallel reviewers converge on the same problems.
4. Adjudicate and apply per `finding-format.md`.
5. Rebuild and re-run the format check. Fix what you broke.
6. Report: chunks dispatched, findings received, findings applied.

### Dispatch prompt

> Review a C++ change against **<document>**.
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
> `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/finding-format.md`. Read it
> first. Findings only. If you have none, output `NO FINDINGS`.

### Precedence

Atomics correctness beats everything — style never justifies an unsound memory
model. If a reviewer says a lock-free construction is wrong, do not restyle it;
put it in the report as a correctness question and leave the code alone unless
the fix is unambiguous.

Below that: Style Guide beats Abseil guides beats the surrounding file's own
convention. Note divergences in the report rather than erasing them.

The style guide states most rules with explicit exceptions. Check them before
applying a finding — the exception is part of the rule.

## Pass 4 — simplify

Invoke the `simplify` skill on the same scope. If it is unavailable: collapse
indirection, delete unused parameters and dead branches, replace hand-rolled
loops with standard library or Abseil algorithms, unify duplicated helpers.
Prefer what the repository already has. Rebuild.

## Passes 5 and 6 — prose

Follow `${CLAUDE_PLUGIN_ROOT}/skills/google-cpp-review/prose-cleanup.md`: Pass A
for redundant comments, then Pass B for AI-sounding prose.

## Pass 7 — modernize

If the project configures clang-tidy, run its `modernize-*` checks over the
scope and apply what fits. Do not introduce clang-tidy to a project that does
not already use it, and do not adopt a language version the build does not set.

## Pass 8 — test

Make a judicious judgement about whether to run tests before declaring victory.
Most of the time the answer is yes, unless the context in your conversation
suggests otherwise.

## Terminology

Comments and docs you write should get C++ terms right — value categories,
lifetime, initialization, overload resolution, the memory model. Check
https://en.cppreference.com/ when unsure.

Then write it for a working engineer, not for the standard. "Dangles if the
parent is destroyed first" beats "the behavior is undefined if the referent's
lifetime has ended". Say "a temporary" unless the reader actually needs
*xvalue*. Never trade accuracy for approachability — if the precise term is the
only correct one, use it and explain it in the same breath. Fix terminology in
pass 5 or 6.

## Report

- **Per pass** — received, applied, rejected, one line per rejection. Say if you
  skipped pass 2 or pass 3, and why.
- **Needs a decision** — findings that were right but would change behavior,
  every atomics finding you did not act on, and conflicts you resolved by
  precedence.
