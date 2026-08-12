#!/usr/bin/env python3
"""Check that the plugins hang together before they are published.

Catches the failures that only show up at review time, when a skill sends a
sub-agent to a path that isn't there:

  - a ${CLAUDE_PLUGIN_ROOT} path in a skill or agent that does not exist
  - a chunk index that lists a file the sync script did not write
  - a skill or agent missing the frontmatter that makes it loadable

Run alongside `claude plugin validate`, which checks the manifests this does not.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[\w./-]+)")
INDEX_ENTRY = re.compile(r"`([\w.-]+\.md)`")


def check_plugin_refs(plugin, problems):
    for md in sorted(plugin.rglob("*.md")):
        if "references" in md.relative_to(plugin).parts:
            continue
        for ref in sorted(set(PLUGIN_REF.findall(md.read_text()))):
            if not (plugin / ref.lstrip("/")).exists():
                problems.append(f"{md.relative_to(REPO)}: no such path {ref}")


def check_chunk_indexes(plugin, problems):
    for index in sorted(plugin.rglob("references/**/index.md")):
        for name in INDEX_ENTRY.findall(index.read_text()):
            if not (index.parent / name).exists():
                problems.append(f"{index.relative_to(REPO)}: lists missing {name}")


def check_frontmatter(plugin, problems):
    targets = list(plugin.glob("agents/*.md")) + list(plugin.glob("skills/*/SKILL.md"))
    if not targets:
        problems.append(f"{plugin.relative_to(REPO)}: no skills or agents")
    for md in sorted(targets):
        text = md.read_text()
        rel = md.relative_to(REPO)
        if not text.startswith("---\n"):
            problems.append(f"{rel}: no frontmatter")
            continue
        front = text.split("---\n", 2)[1]
        for field in ("name", "description"):
            if not re.search(rf"^{field}: *\S", front, re.M):
                problems.append(f"{rel}: frontmatter has no {field}")


def main():
    plugins = sorted(p for p in (REPO / "plugins").iterdir() if p.is_dir())
    if not plugins:
        print("no plugins found", file=sys.stderr)
        return 1

    problems = []
    for plugin in plugins:
        if not (plugin / ".claude-plugin/plugin.json").exists():
            problems.append(f"{plugin.relative_to(REPO)}: no plugin.json")
        check_plugin_refs(plugin, problems)
        check_chunk_indexes(plugin, problems)
        check_frontmatter(plugin, problems)

    for problem in problems:
        print(problem)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    print(f"{len(plugins)} plugin(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
