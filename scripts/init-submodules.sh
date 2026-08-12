#!/usr/bin/env bash
# Check out the upstream style guides in third_party/.
#
# `git submodule update --init` also works and needs nothing from this script,
# but golang/go and golang/website are large repositories that this project uses
# a handful of directories from. These are blobless, shallow, sparse checkouts
# of just those directories: about 30 MB in total rather than several hundred.
#
# Each checkout lands on the commit the superproject pins, so this and
# `git submodule update --init` produce the same content.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

# path <TAB> url <TAB> sparse paths (empty for a full checkout)
modules=$(
  cat <<'EOF'
third_party/styleguide	https://github.com/google/styleguide
third_party/abseil-docs	https://github.com/abseil/abseil.github.io	docs/cpp docs/python
third_party/go	https://github.com/golang/go	doc
third_party/go-website	https://github.com/golang/website	_content/doc _content/ref
EOF
)

pinned_commit() {
  # Read from the index rather than HEAD so this works before the first commit.
  git ls-files -s "$1" | awk '$1 == 160000 { print $2 }'
}

while IFS=$'\t' read -r path url sparse; do
  [[ -n "$path" ]] || continue

  sha=$(pinned_commit "$path")
  if [[ -z "$sha" ]]; then
    echo "error: $path is not registered as a submodule" >&2
    exit 1
  fi

  if [[ -e "$path/.git" ]]; then
    echo "==> $path already checked out, skipping"
    continue
  fi

  echo "==> $path"
  git clone --quiet --filter=blob:none --no-checkout --depth 1 "$url" "$path"
  if [[ -n "$sparse" ]]; then
    # shellcheck disable=SC2086 -- sparse is a list of paths
    git -C "$path" sparse-checkout set $sparse
  fi
  # The pin is usually older than the shallow tip, so fetch it by SHA.
  git -C "$path" fetch --quiet --depth 1 origin "$sha"
  git -C "$path" checkout --quiet "$sha"
done <<<"$modules"

echo
echo "Done. Next: ./scripts/sync-references.sh"
