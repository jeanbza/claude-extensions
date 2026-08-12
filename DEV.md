# Developing

The style guides live in `third_party/` as submodules. Each plugin ships its own
generated, chunked copy under `references/`, because installing a plugin copies
its directory into `~/.claude/plugins/cache` and a submodule's contents don't
follow.

**This repo can't be used with jj.** jj [doesn't support
submodules](https://docs.jj-vcs.dev/latest/design/git-submodules/) yet, and a
colocated `.jj` silently drops the gitlinks from the git index — `.gitmodules`
survives, the pins don't, and a fresh clone gets nothing.

## First-time checkout

`styleguide` and `abseil-docs` are small enough to take whole:

```sh
git submodule update --init third_party/styleguide third_party/abseil-docs
```

`golang/go` and `golang/website` are not — only `doc/` and `_content/{doc,ref}`
are used, so clone them blobless, shallow, and sparse. Plain
`git submodule update --init` also works and needs none of this; it just pulls a
few hundred MB more.

```sh
# golang/go — for doc/go_spec.html
sha=$(git rev-parse HEAD:third_party/go)
git clone --filter=blob:none --no-checkout --depth 1 \
    https://github.com/golang/go third_party/go
git -C third_party/go sparse-checkout set doc
git -C third_party/go fetch --depth 1 origin "$sha"
git -C third_party/go checkout "$sha"

# golang/website — for effective_go.html and ref/mod.md
sha=$(git rev-parse HEAD:third_party/go-website)
git clone --filter=blob:none --no-checkout --depth 1 \
    https://github.com/golang/website third_party/go-website
git -C third_party/go-website sparse-checkout set _content/doc _content/ref
git -C third_party/go-website fetch --depth 1 origin "$sha"
git -C third_party/go-website checkout "$sha"
```

A hand-clone leaves the submodule unregistered — `git submodule status` prints a
leading `-` and `git submodule` commands skip it. Register the two and move their
git directories under `.git/modules/`, where a normally-created submodule keeps
them:

```sh
git submodule init third_party/go third_party/go-website
git submodule absorbgitdirs third_party/go third_party/go-website
```

All four should now show a clean status, and `git status` should be clean:

```sh
git submodule status
```

About 50 MB total, a few seconds.

## Updating the guides

```sh
git submodule update --remote     # move each submodule to its upstream tip
./scripts/sync-references.sh      # regenerate plugins/*/references/
git add -A && git commit          # the moved gitlinks are the new pins
```

Sparse and shallow settings survive `--remote`; there is nothing to redo.

To pin one submodule to a specific commit instead:

```sh
git -C third_party/styleguide fetch origin
git -C third_party/styleguide checkout <sha>
./scripts/sync-references.sh
```

## Regenerating references

```sh
./scripts/sync-references.sh
```

Everything under `plugins/*/references/` is generated — edit
`scripts/sync-references.sh` or `scripts/lib/`, never the output. Read the diff
before committing: an upstream rewrite shifts chunk boundaries, and the skills
name chunk files.

## Checks

```sh
./scripts/check.py                          # plugin paths, chunk indexes, frontmatter
claude plugin validate .                    # marketplace manifest
claude plugin validate plugins/google-go-review
```

## Working on a plugin

```sh
claude --plugin-dir plugins/google-go-review          # load without installing
```

Or install from the working copy:

```sh
claude plugin marketplace add ./
claude plugin install google-go-review@jeanbza
```

Installs pin to `version` in `plugin.json`, so bump it — or uninstall and
reinstall — to pick up changes. A locally-sourced marketplace resolves
`${CLAUDE_PLUGIN_ROOT}` to this repo rather than to the plugin cache, so allow
reads from this path too, alongside the cache rule in the README.

## Naming

The marketplace entry name and the manifest name differ on purpose. The entry
name is what `/plugin install` resolves; `plugin.json`'s `name` is what
namespaces components. That is why installing `google-go-review@jeanbza` gives
you `/jeanbza:google-go-review`. All three plugins use `jeanbza` as their
manifest name, so their agents carry distinct names (`go-style-reviewer`,
`cpp-style-reviewer`, `python-style-reviewer`) to avoid colliding when more than
one is installed.

## Licensing

Upstream licenses and pinned commits are recorded per plugin in
`references/NOTICE.md`: CC-BY-3.0 for the Google style guides, BSD-3-Clause for
Go, Apache-2.0 for Abseil. This repo's own code is Apache-2.0.
