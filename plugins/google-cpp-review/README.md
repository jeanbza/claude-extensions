# google-cpp-review

Reviews C++ code against the Google C++ Style Guide and, for code that uses
Abseil, the Abseil guides.

```
/plugin marketplace add jeanbza/claude-extensions
/plugin install google-cpp-review@jeanbza
```

Then grant read access to installed plugin files, once, in
`~/.claude/settings.json`:

```json
{ "permissions": { "allow": ["Read(~/.claude/plugins/cache/**)"] } }
```

The plugin ships the style guides it reviews against, and every sub-agent reads
its assigned section from the plugin directory — which lives outside your
project, so it needs the grant. Without it the skill stops at its preflight
check rather than reviewing from memory.

Then, after writing or generating C++ code:

```
/jeanbza:google-cpp-review
```

Review the changed files by default; name files or directories to narrow it.
Headers travel with their implementation files.

## Passes

| # | Pass                    | How                                                          |
| - | ----------------------- | ------------------------------------------------------------ |
| 0 | Scope and baseline      | whatever the project uses: Bazel, CMake, Make, `clang-format` |
| 1 | Google C++ Style Guide  | 9 sub-agents, one per section group                           |
| 2 | The danger of atomics   | 1 sub-agent, skipped only if the change has no atomics        |
| 3 | Abseil guides           | 1 sub-agent per Abseil library the change actually uses       |
| 4 | Simplify                | the `simplify` skill                                          |
| 5 | Redundant comments      | direct edits                                                  |
| 6 | AI-sounding prose       | direct edits                                                  |

Sub-agents are read-only: they report findings with a citation and a severity,
and never edit. The orchestrating agent adjudicates, applies what is worth
applying, and rebuilds between passes.

Pass 2 is the exception to "this is not a bug hunt". It reviews `std::atomic`
use and hand-rolled lock-free reasoning against Abseil's
[atomics guidance](https://abseil.io/docs/cpp/atomic_danger), and it runs
whether or not the project uses Abseil. Its findings outrank style findings, and
an unsound lock-free construction is reported for a human decision rather than
quietly restyled.

Pass 3 dispatches only for the guides the change engages — `absl/strings/` pulls
in the strings guide, `absl/synchronization/` the synchronization guide, and so
on. Code that does not use Abseil skips the pass entirely.

Comments and documentation the review rewrites are checked against
[cppreference](https://en.cppreference.com/) for correctness, then written for a
working engineer rather than for the standard: precise terms, plain phrasing,
and jargon only where the distinction is the point.

## References

Shipped under `references/`, generated from the submodules in the repository
root. See `references/NOTICE.md` for upstream URLs, pinned commits, and
licenses.

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [Abseil: the danger of atomics](https://abseil.io/docs/cpp/atomic_danger)
- [Abseil C++ guides](https://abseil.io/docs/cpp/guides/)

cppreference is consulted over the network when a terminology question comes up;
it is not vendored.

## Scope

Style, idiom, and clarity, plus the atomics pass. It assumes the code already
compiles and works.
