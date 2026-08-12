# claude-extensions

Claude Code plugins, hooks, and advisors.

This repository is a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).
Install it like so:

```
/plugin marketplace add jeanbza/claude-extensions
```

## Google code style reviewers

A few plugins which let AI agents review your code against the Google style
guides. They fan out many sub-agents, use a lot of tokens, and can take some
time. But they tend to result in better code. Use at your discretion.

```
/plugin install google-go-review@jeanbza
/plugin install google-cpp-review@jeanbza
/plugin install google-python-review@jeanbza
```

Then grant read access to installed plugin files, once, in
`~/.claude/settings.json`:

```json
{ "permissions": { "allow": ["Read(~/.claude/plugins/cache/**)"] } }
```

To refresh them later and pick up new changes to this repo, run
`/reload-plugins` and `/reload-skills`.

Run them like so:

```
/jeanbza:google-go-review
/jeanbza:google-cpp-review
/jeanbza:google-py-review
```

## Hacking on this repo

See [DEV.md](DEV.md).
