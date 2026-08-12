# google-go-review

Reviews Go code against Google's published Go style documents and go.dev's
language and module references.

```
/plugin marketplace add jeanbza/claude-extensions
/plugin install google-go-review@jeanbza
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

Then, after writing or generating Go code:

```
/jeanbza:google-go-review
```

Review the changed files by default; name files or directories to narrow it.

## Passes

| # | Pass                    | How                                                        |
| - | ----------------------- | ---------------------------------------------------------- |
| 0 | Scope and baseline      | `gofmt -l`, `go build ./...`, `go vet ./...`                |
| 1 | Effective Go            | 4 sub-agents, one per section group                         |
| 2 | Go Style Best Practices | 6 sub-agents                                                |
| 3 | Go Style Decisions      | 5 sub-agents                                                |
| 4 | Simplify                | the `simplify` skill                                        |
| 5 | Redundant comments      | direct edits                                                |
| 6 | AI-sounding prose       | direct edits                                                |

Sub-agents are read-only: they report findings with a citation and a severity,
and never edit. The orchestrating agent adjudicates, applies what is worth
applying, and re-runs the build between passes. Conflicts resolve by the
precedence the Google documents set for themselves — the core style guide is
canonical, decisions are normative, best practices are neither, and Effective Go
is background where it has not been overtaken by modules and generics.

Comments and documentation the review rewrites use the vocabulary of the
[Go Modules Reference](https://go.dev/ref/mod) for anything about modules and
the [Go specification](https://go.dev/ref/spec) for anything about the language.
Both ship with the plugin.

## References

Shipped under `references/`, generated from the submodules in the repository
root. See `references/NOTICE.md` for upstream URLs, pinned commits, and
licenses.

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Style Guide](https://google.github.io/styleguide/go/guide),
  [Decisions](https://google.github.io/styleguide/go/decisions),
  [Best Practices](https://google.github.io/styleguide/go/best-practices)
- [Go specification](https://go.dev/ref/spec),
  [Go Modules Reference](https://go.dev/ref/mod)

## Scope

Style, idiom, and clarity. Not a bug hunt, and not a security review. It assumes
the code already works.
