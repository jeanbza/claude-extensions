#!/usr/bin/env python3
"""Split a reference document into review-sized chunks.

Each review skill dispatches one sub-agent per chunk, so the chunks decide how
the work is divided. Sections are packed greedily up to a target size and never
split mid-section: a sub-agent that sees half a guideline gives half an answer.

Usage:
    chunk.py --source-url URL --title TITLE --out DIR [options] INPUT

INPUT is Markdown, or HTML when --html is given.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import htmlmd

DEFAULT_TARGET = 28000
GENERATED_BY = "scripts/sync-references.sh"


def slugify(text):
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"[`*_]", "", text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:48] or "section"


def fenced_spans(text):
    """Return (start, end) offsets of fenced code blocks.

    Style guides quote preprocessor directives and shell comments, which look
    exactly like Markdown headings. Sectioning has to skip over them.
    """
    spans, open_at = [], None
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            if open_at is None:
                open_at = offset
            else:
                spans.append((open_at, offset + len(line)))
                open_at = None
        offset += len(line)
    if open_at is not None:
        spans.append((open_at, len(text)))
    return spans


def split_sections(text, level):
    """Split Markdown into (title, body) pairs at the given heading level.

    Content before the first heading becomes a leading "Preamble" section so
    that document-wide notes are not dropped.
    """
    pattern = re.compile(r"^#{1,%d} +(.*)$" % level, re.M)
    spans = fenced_spans(text)
    matches = [
        m for m in pattern.finditer(text)
        if not any(start <= m.start() < end for start, end in spans)
    ]
    if not matches:
        return [("Preamble", text)]

    sections = []
    if text[: matches[0].start()].strip():
        sections.append(("Preamble", text[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = re.sub(r"<!--.*?-->", "", m.group(1)).strip()
        sections.append((title, text[m.start() : end]))
    return sections


def pack(sections, target):
    """Group sections into chunks no larger than target, when possible."""
    chunks, current, size = [], [], 0
    for title, body in sections:
        if current and size + len(body) > target:
            chunks.append(current)
            current, size = [], 0
        current.append((title, body))
        size += len(body)
    if current:
        chunks.append(current)
    return chunks


def upstream_commit(path):
    repo = os.path.dirname(os.path.abspath(path))
    try:
        sha = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return sha.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", required=True, help="output directory for chunks")
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--level", type=int, default=3,
                    help="heading level to split on (default: 3)")
    ap.add_argument("--target", type=int, default=DEFAULT_TARGET,
                    help=f"target chunk size in characters (default: {DEFAULT_TARGET})")
    ap.add_argument("--html", action="store_true", help="input is HTML")
    ap.add_argument("--code-lang", default="", help="language tag for code fences")
    ap.add_argument("--single", action="store_true",
                    help="emit one chunk regardless of size")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        text = f.read()
    if args.html:
        text = htmlmd.convert(text, code_lang=args.code_lang)
    # Jekyll's raw guards are an artifact of how Google publishes the guides.
    text = re.sub(r"^\{%\s*(end)?raw\s*%\}\s*$", "", text, flags=re.M)

    sha = upstream_commit(args.input)
    synced = date.today().isoformat()
    sections = split_sections(text, args.level)
    chunks = [[s for s in sections]] if args.single else pack(sections, args.target)

    os.makedirs(args.out, exist_ok=True)
    for stale in os.listdir(args.out):
        if re.match(r"^\d\d-.*\.md$", stale) or stale == "index.md":
            os.remove(os.path.join(args.out, stale))

    index = []
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        titles = [t for t, _ in chunk]
        name = f"{i:02d}-{slugify(titles[0])}.md"
        header = (
            f"<!-- Generated by {GENERATED_BY}. Do not edit. -->\n"
            f"# {args.title} ({i} of {total})\n\n"
            f"Source: {args.source_url} (upstream {sha}, synced {synced})\n\n"
            f"Sections in this chunk: {', '.join(titles)}\n\n---\n\n"
        )
        body = "\n\n".join(b.strip() for _, b in chunk)
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(header + body + "\n")
        index.append((name, titles))

    with open(os.path.join(args.out, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"<!-- Generated by {GENERATED_BY}. Do not edit. -->\n")
        f.write(f"# {args.title} — chunk index\n\n")
        f.write(f"Source: {args.source_url} (upstream {sha}, synced {synced})\n\n")
        f.write(f"Dispatch one sub-agent per chunk below ({total} total).\n\n")
        f.write("| Chunk | Sections |\n|---|---|\n")
        for name, titles in index:
            f.write(f"| `{name}` | {', '.join(titles)} |\n")

    print(f"{args.title}: {total} chunk(s) -> {args.out}")


if __name__ == "__main__":
    main()
