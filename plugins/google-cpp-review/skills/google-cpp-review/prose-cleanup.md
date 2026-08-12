# Prose cleanup

Two passes over every comment, doc comment, and piece of documentation the
change touched. Both are edits you make directly — no sub-agents.

Only touch prose inside the review scope. Rewriting comments the change did not
introduce buries the real diff.

## Pass A — remove redundant comments

Delete a comment when the code already says it. Specifically:

- **Restatement.** `// increment i` above `i++`. `// Close the file` above
  `f.Close()`. If deleting the comment loses nothing, delete it.
- **Signature echo.** A comment that names the parameters and return values in
  prose and adds nothing else. `// Adds a and b and returns the sum.` on
  `int Add(int a, int b)` earns its keep only if there is something to say about
  overflow, units, or ownership.
- **Narration.** `// Step 1: parse the config`, `// First, we validate the
  input`, `// Now handle the error case`. Sequence is visible in the code.
- **Section banners.** `// ===== Helpers =====`, `// --- types ---`. Structure
  belongs in file and package layout.
- **Changelog and process notes.** `// Added error handling`, `// Refactored
  from the old version`, `// As requested`. Version control owns this.
- **Type restatement.** `// The user ID, a string.` next to
  `std::string user_id_;`.
- **Dead scaffolding.** Commented-out code, and `// TODO` items the change
  itself resolved.

Keep, and improve if the wording is weak:

- Why the code is the way it is: the constraint, the bug, the benchmark, the
  upstream quirk it works around.
- Invariants and preconditions a caller cannot infer from the signature.
- References to an issue, a spec section, or a standard.
- Warnings about a non-obvious failure mode or a surprising cost.
- Ownership, lifetime, and thread-safety contracts. Who deletes this, how long
  the pointee outlives the call, which mutex guards which member. None of it is
  visible in the types.
- File comments, and the comments the style guide requires on classes,
  functions, and non-obvious members. Make them say something rather than
  deleting them — see the Comments section of the style guide chunks.

When in doubt, ask what a reader who understands C++ but not this change needs.
Write that. Delete the rest.

## Pass B — rewrite AI-sounding prose

Generated comments have a register: eager, padded, and faintly promotional.
Rewrite them to sound like a colleague who is busy.

**Vocabulary to cut.** `comprehensive`, `robust`, `seamless`, `powerful`,
`elegant`, `modern`, `intuitive`, `crucial`, `essential`, `vital`, `leverage`,
`utilize` (say "use"), `delve`, `showcase`, `facilitate`, `ensure` where "make
sure" or nothing at all would do, `gracefully`, `under the hood`, `out of the
box`, `battle-tested`, `first-class`, `best practices`, `production-ready`.

**Phrasings to cut.**

| Instead of                                       | Write                                  |
| ------------------------------------------------ | -------------------------------------- |
| `// This function is responsible for parsing X`  | `// Parses X.` or nothing              |
| `// It's important to note that the mutex ...`   | `// The mutex ...`                     |
| `// Here we simply iterate over the results`     | nothing                                |
| `// Let's handle the error case`                 | nothing                                |
| `// We'll use a flat_hash_map for fast lookups`  | `// Lookups are on the hot path.`      |
| `// This ensures thread safety`                  | `// Guarded by mu_; callers may race.` |
| `// Handle edge cases gracefully`                | name the edge case                     |
| `// A comprehensive validation of the input`     | `// Rejects unset fields.`             |

**Structural tells.**

- Every function carrying a comment of the same shape and length. Real comments
  are uneven, because the need for them is uneven.
- Lists that always have three items.
- `Not only ... but also`, and paired em-dashes used for emphasis in a comment.
- Hedging stacked on hedging: `this may potentially cause issues in some cases`.
- Enthusiasm. `// Nice and clean!`, `// 🚀 Fast path`. Cut it.
- Second person addressed to nobody: `// You can use this to ...` on an
  implementation-detail helper in an anonymous namespace.

**What to write instead.** The shortest true sentence. Present tense, active
voice, subject first. Terminology from the reference documents rather than
approximations of it — see the terminology rule in `SKILL.md`. A comment that
now says nothing is a comment to delete, not to rephrase.
