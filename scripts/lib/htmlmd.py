"""Minimal HTML-to-Markdown converter for the vendored style guides.

Only handles the subset of markup that appears in the Go and C++ style guides:
headings, paragraphs, lists, code, tables, and definition lists. It is not a
general purpose converter, and it does not try to be one. Everything it emits
is meant to be read by a model, so exact fidelity matters less than keeping
headings, code blocks, and good/bad example labels intact.
"""

import re
from html.parser import HTMLParser

# Google's C++ guide tags examples as good, bad, or neutral via the pre class.
# That distinction carries most of the guide's meaning, so it survives into the
# generated Markdown as a label above the fence.
_PRE_LABELS = {
    "goodcode": "**Good:**",
    "badcode": "**Bad:**",
    "neutralcode": "**Neutral:**",
}

_SKIP_TAGS = {"script", "style", "head", "nav"}
_BLOCK_TAGS = {"p", "div", "section", "article", "blockquote", "figure"}
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


class _Converter(HTMLParser):
    def __init__(self, code_lang=""):
        super().__init__(convert_charrefs=True)
        self.code_lang = code_lang
        self.out = []
        self.skip_depth = 0
        self.pre_depth = 0
        self.list_stack = []
        self.heading = None
        self.pending_id = None
        self.cell = None
        self.row = None
        self.table = None

    # -- helpers ----------------------------------------------------------

    def emit(self, text):
        if self.cell is not None:
            self.cell.append(text)
            return
        # Collapsed whitespace often lands right after a newline, which would
        # indent the line and, at four spaces, read as a code block.
        if text.startswith(" ") and (not self.out or self.out[-1].endswith("\n")):
            text = text.lstrip(" ")
        if text:
            self.out.append(text)

    def blank(self):
        if self.out and self.out[-1] != "\n\n":
            self.out.append("\n\n")

    def result(self):
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    # -- tags -------------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in _SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        if tag == "pre":
            self.blank()
            label = _PRE_LABELS.get(attrs.get("class", "").strip())
            if label:
                self.out.append(label + "\n\n")
            self.out.append("```" + self.code_lang + "\n")
            self.pre_depth += 1
        elif tag in _HEADINGS:
            self.blank()
            self.heading = _HEADINGS[tag]
            self.pending_id = attrs.get("id")
            self.out.append("#" * self.heading + " ")
        elif tag in ("ul", "ol"):
            self.blank()
            self.list_stack.append([tag, 0])
        elif tag == "li":
            if self.list_stack:
                kind, n = self.list_stack[-1]
                self.list_stack[-1][1] = n + 1
                indent = "    " * (len(self.list_stack) - 1)
                bullet = f"{n + 1}." if kind == "ol" else "-"
                self.out.append(f"\n{indent}{bullet} ")
        elif tag == "dt":
            self.blank()
            self.out.append("**")
        elif tag == "dd":
            self.out.append("\n")
        elif tag == "table":
            self.table = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "code" and not self.pre_depth:
            self.emit("`")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "br":
            self.emit("\n")
        elif tag in _BLOCK_TAGS:
            self.blank()

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return

        if tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)
            if not self.out[-1].endswith("\n"):
                self.out.append("\n")
            self.out.append("```\n\n")
        elif tag in _HEADINGS:
            # Keep the upstream anchor so findings can cite a stable URL fragment.
            if self.pending_id:
                self.out.append(f" <!-- #{self.pending_id} -->")
            self.heading = None
            self.pending_id = None
            self.out.append("\n\n")
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.blank()
        elif tag == "dt":
            self.out.append("**\n")
        elif tag in ("td", "th"):
            if self.row is not None and self.cell is not None:
                self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr":
            if self.table is not None and self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self._flush_table()
        elif tag == "code" and not self.pre_depth:
            self.emit("`")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag in _BLOCK_TAGS:
            self.blank()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.pre_depth:
            # <pre> content usually starts on the line after the tag; keeping
            # that newline leaves a blank first line inside the fence.
            if self.out[-1].endswith("\n") and data.startswith("\n"):
                data = data.lstrip("\n")
            self.out.append(data)
            return
        text = re.sub(r"\s+", " ", data)
        if not text.strip():
            if self.out and not self.out[-1].endswith((" ", "\n")):
                self.emit(" ")
            return
        self.emit(text)

    def _flush_table(self):
        rows, self.table = self.table, None
        if not rows:
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        self.blank()
        self.out.append("| " + " | ".join(rows[0]) + " |\n")
        self.out.append("|" + "---|" * width + "\n")
        for row in rows[1:]:
            self.out.append("| " + " | ".join(row) + " |\n")
        self.blank()


def convert(source, code_lang=""):
    """Convert an HTML document to Markdown."""
    # Go's website templates wrap metadata in <!--{...}--> and use {{...}}
    # actions; neither is content, and both confuse a reader.
    source = re.sub(r"<!--\{.*?\}-->", "", source, flags=re.S)
    source = re.sub(r"\{\{.*?\}\}", "", source, flags=re.S)
    # convert_charrefs already resolves entities as data arrives.
    conv = _Converter(code_lang=code_lang)
    conv.feed(source)
    conv.close()
    return conv.result()
