# Developing

## Checking out

```sh
git clone --recurse-submodules git@github.com:jeanbza/claude-extensions.git
```

## Updating the guides

```sh
git submodule update --remote     # move each submodule to its upstream tip
./scripts/sync-references.sh      # regenerate plugins/*/references/
```

## Checks after updating plugins

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
