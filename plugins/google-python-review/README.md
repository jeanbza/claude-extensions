# google-python-review

Reviews Python code against the Google Python Style Guide and, for code that
uses Abseil, the Abseil Python guides.

```
/plugin marketplace add jeanbza/claude-extensions
/plugin install google-python-review@jeanbza
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

Then, after writing or generating Python code:

```
/jeanbza:google-py-review
```

Review the changed files by default; name files or directories to narrow it.

## Passes

| # | Pass                       | How                                                       |
| - | -------------------------- | --------------------------------------------------------- |
| 0 | Scope and baseline         | whatever the project configures: Ruff, Black, Pylint, mypy |
| 1 | Google Python Style Guide  | 5 sub-agents, one per section group                        |
| 2 | Abseil Python guides       | 1 sub-agent per Abseil module the change actually uses     |
| 3 | Simplify                   | the `simplify` skill                                       |
| 4 | Redundant comments         | direct edits                                               |
| 5 | AI-sounding prose          | direct edits                                               |

Sub-agents are read-only: they report findings with a citation and a severity,
and never edit. The orchestrating agent adjudicates, applies what is worth
applying, and re-runs the project's checks between passes.

Layout rules stay with the formatter. Where the project's configured formatter
disagrees with the guide, the formatter wins — that is what runs in CI — and the
divergence goes in the report. The review will not add a linter the project does
not use, or reformat to a style it has not adopted.

Pass 2 dispatches only for the guides the change engages: `absl.flags` pulls in
the flags guide, `absl.testing` the testing guide, and so on. Code that does not
import Abseil skips the pass entirely.

Docstrings the review rewrites keep the guide's form — a one-line summary, then
`Args:`, `Returns:`, and `Raises:` sections that carry real information rather
than restating the signature.

## References

Shipped under `references/`, generated from the submodules in the repository
root. See `references/NOTICE.md` for upstream URLs, pinned commits, and
licenses.

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Abseil Python guides](https://abseil.io/docs/python/guides/)

## Scope

Style, idiom, and clarity. Not a bug hunt, and not a security review. It assumes
the code already works.
