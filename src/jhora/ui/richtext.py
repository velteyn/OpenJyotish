"""Rich-text helpers for the GUI output windows.

LLMs respond in Markdown (bold, headings, lists, code, tables...), but the
output widgets are Qt ``QTextEdit`` documents. This module provides a small,
dependency-free Markdown → HTML renderer tuned for a dark theme, plus a helper
to bump the font of plain-text output panels.
"""

import html
import re

# ── Theme colours (kept in sync with ui/theme.py) ──────────────────────────
TEXT = "#e8e9f2"
DIM = "#8b90a8"
GOLD = "#d4af37"
BORDER = "#2a3350"
CODE_BG = "#1a2135"

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_FENCE_OPEN_RE = re.compile(r"^```\s*([\w+-]*)")
_HR_RE = re.compile(r"^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$")
_LIST_RE = re.compile(r"^\s{0,3}([-*+]|\d+[.)])\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)|(?<!_)_([^_\s][^_]*?)_(?!_)")
_STRIKE_RE = re.compile(r"~~([^~]+)~~")
_SEP_CELL_RE = re.compile(r"^:?-{2,}:?$")


def _inline(text: str) -> str:
    """Escape and apply inline Markdown (code, bold, italic, strike, links)."""
    text = html.escape(text)
    text = _LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = _CODE_RE.sub(r"<code style='background:%(bg)s; padding:1px 4px; "
                        r"border-radius:4px; font-family:Consolas,monospace;"
                        r"'>\1</code>" % {"bg": CODE_BG}, text)
    text = _BOLD_RE.sub(lambda m: "<b>%s</b>" % (m.group(1) or m.group(2)), text)
    text = _ITALIC_RE.sub(lambda m: "<i>%s</i>" % (m.group(1) or m.group(2)), text)
    text = _STRIKE_RE.sub(r"<s>\1</s>", text)
    return text


def _render_paragraph(lines: list) -> str:
    body = "<br>".join(_inline(ln) for ln in lines)
    return f"<p style='margin:6px 0;'>{body}</p>"


def _render_heading(level: int, text: str) -> str:
    return (f"<h{level} style='color:{GOLD}; margin:10px 0 6px 0;'>"
            f"{_inline(text)}</h{level}>")


def _render_list(ordered: bool, items: list) -> str:
    tag = "ol" if ordered else "ul"
    lis = "".join(f"<li style='margin:2px 0;'>{_inline(i)}</li>" for i in items)
    return f"<{tag} style='margin:6px 0 6px 22px;'>{lis}</{tag}>"


def _render_blockquote(lines: list) -> str:
    body = "<br>".join(_inline(ln) for ln in lines)
    return (f"<blockquote style='margin:6px 0; padding:2px 12px; color:{DIM}; "
            f"border-left:3px solid {BORDER};'>{body}</blockquote>")


def _render_code(lang: str, content: str) -> str:
    esc = html.escape(content)
    return (f"<pre style='background:{CODE_BG}; border:1px solid {BORDER}; "
            f"border-radius:6px; padding:8px; white-space:pre-wrap; "
            f"font-family:Consolas,monospace;'>{esc}</pre>")


def _render_table(rows: list) -> str:
    cells = []
    for raw in rows:
        body = raw.strip()
        body = body[1:] if body.startswith("|") else body
        body = body[:-1] if body.endswith("|") else body
        parts = [c.strip() for c in body.split("|")]
        if parts and all(_SEP_CELL_RE.match(p.replace(" ", "")) for p in parts):
            continue
        cells.append(parts)
    if not cells:
        return ""
    th = "".join(f"<th style='border:1px solid {BORDER}; padding:4px 10px; "
                 f"background:{CODE_BG}; text-align:left;'>{_inline(c)}</th>"
                 for c in cells[0])
    body = "".join(
        "<tr>" + "".join(
            f"<td style='border:1px solid {BORDER}; padding:4px 10px;'>{_inline(c)}</td>"
            for c in row) + "</tr>"
        for row in cells[1:])
    return (f"<table cellspacing='0' "
            f"style='border-collapse:collapse; margin:8px 0;'>"
            f"<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>")


def _parse_blocks(lines) -> list:
    """Split raw lines into block tuples for rendering."""
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue

        fence = _FENCE_OPEN_RE.match(line)
        if fence:
            lang = fence.group(1)
            j, buf = i + 1, []
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            blocks.append(("code", lang, "\n".join(buf)))
            i = j + 1
            continue

        head = _HEADING_RE.match(line)
        if head:
            blocks.append((f"h{len(head.group(1))}",
                           head.group(2).strip()))
            i += 1
            continue

        if _HR_RE.match(line):
            blocks.append(("hr",))
            i += 1
            continue

        if line.strip().startswith(">"):
            j, q = i, []
            while j < n and lines[j].strip().startswith(">"):
                q.append(lines[j].strip().lstrip(">").strip())
                j += 1
            blocks.append(("quote", q))
            i = j
            continue

        item = _LIST_RE.match(line)
        if item:
            ordered = item.group(1) not in ("-", "*", "+")
            j, items = i, []
            while j < n:
                m = _LIST_RE.match(lines[j])
                if not m:
                    break
                items.append(m.group(2).strip())
                j += 1
            blocks.append(("ol" if ordered else "ul", items))
            i = j
            continue

        if line.startswith("|"):
            j, rows = i, []
            while j < n and lines[j].strip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            blocks.append(("table", rows))
            i = j
            continue

        j, para = i, []
        while j < n and lines[j].strip():
            nxt = lines[j].rstrip()
            if (_HEADING_RE.match(nxt) or _HR_RE.match(nxt)
                    or nxt.startswith(("```", "|")) or _LIST_RE.match(nxt)
                    or nxt.strip().startswith(">")):
                break
            para.append(nxt)
            j += 1
        blocks.append(("p", para))
        i = j
    return blocks


def md_to_html(text: str) -> str:
    """Render Markdown-ish LLM output to an HTML body fragment (dark theme)."""
    if not text or not text.strip():
        return ""
    out = []
    for kind, *args in _parse_blocks(text.splitlines()):
        if kind == "hr":
            out.append(f"<hr style='border:none; border-top:1px solid {BORDER}; "
                       f"margin:8px 0;'>")
        elif kind.startswith("h"):
            out.append(_render_heading(int(kind[1:]), args[0]))
        elif kind == "p":
            out.append(_render_paragraph(args[0]))
        elif kind == "ul":
            out.append(_render_list(False, args[0]))
        elif kind == "ol":
            out.append(_render_list(True, args[0]))
        elif kind == "quote":
            out.append(_render_blockquote(args[0]))
        elif kind == "code":
            out.append(_render_code(args[0], args[1]))
        elif kind == "table":
            out.append(_render_table(args[0]))
    return "\n".join(out)


def md_document(text: str, size_px: int = 15) -> str:
    """Wrap ``md_to_html`` in a full HTML document for ``QTextEdit.setHtml``."""
    return (
        "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.0//EN' "
        "'http://www.w3.org/TR/REC-html40/strict.dtd'>"
        "<html><head><meta charset='utf-8'></head>"
        f"<body style='font-family:Segoe UI, sans-serif; font-size:{size_px}px; "
        f"color:{TEXT};'>{md_to_html(text)}</body></html>"
    )


def apply_output_font(widget, size_pt: int = 11):
    """Bump the font of a plain-text output panel (slightly larger than the app)."""
    from PyQt6.QtGui import QFont
    f = QFont(widget.font())
    f.setPointSize(size_pt)
    widget.setFont(f)
    return widget