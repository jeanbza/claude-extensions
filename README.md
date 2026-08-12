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

The style guides live in `third_party/` as submodules, and each plugin ships a
generated, chunked copy under `references/` — a plugin's directory is copied
into a cache at install time and can't reach outside itself, so the references
have to travel with it.

```sh
./scripts/init-submodules.sh          # blobless sparse checkouts, ~25 MB
./scripts/sync-references.sh          # regenerate from the pinned commits
./scripts/sync-references.sh --update # pull upstream first, then regenerate
./scripts/check.py                    # paths, chunk indexes, frontmatter
claude plugin validate .
```

`git submodule update --init` works too; it just pulls a few hundred MB more,
because `golang/go` and `golang/website` are large and only a few directories
are needed.

Everything under `plugins/*/references/` is generated — edit the script, not the
output — and upstream rewrites shift chunk boundaries, so read the diff.

Note that this repo can't be used with jj: [jj doesn't support
submodules](https://docs.jj-vcs.dev/latest/design/git-submodules/) yet, and a
colocated `.jj` silently drops the gitlinks from the git index.

To iterate on a plugin, install it from the working copy:

```sh
claude plugin marketplace add ./
claude plugin install google-go-review@jeanbza
```

Installs pin to `version` in `plugin.json`, so bump it — or uninstall and
reinstall — to pick up changes. A locally-sourced marketplace also resolves
`${CLAUDE_PLUGIN_ROOT}` to this repo rather than to the plugin cache, so allow
reads from it too.

Upstream licenses and pinned commits are recorded in each plugin's
`references/NOTICE.md`: CC-BY-3.0 for the Google style guides, BSD-3-Clause for
Go, Apache-2.0 for Abseil. This repo's own code is Apache-2.0.
