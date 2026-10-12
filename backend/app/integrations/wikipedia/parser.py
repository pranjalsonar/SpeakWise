"""Turn a Wikipedia plain-text extract into clean sections. Pure functions, no I/O.

Input is the output of `prop=extracts&explaintext=1&exsectionformat=wiki`, where
headings look like "== History ==" / "=== Early years ===".
"""
import re
from typing import Any

_HEADING = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)

# Leftovers from stripped markup: "[citation needed]", "[1]", empty "( )" / "(; )" from removed
# pronunciations, and space before punctuation.
_CLEANUPS = [
    (re.compile(r"\[(?:citation needed|clarification needed|when\?|who\?|according to whom\?|"
                r"dubious[^\]]*|update[^\]]*|\d+)\]", re.IGNORECASE), ""),
    (re.compile(r"\(\s*[;,]?\s*\)"), ""),
    (re.compile(r"\s+([,.;:!?])"), r"\1"),
    (re.compile(r"[ \t ]{2,}"), " "),
]

_SENTENCE_END = re.compile(r"[.!?…\"”')]$")


def clean_paragraph(text: str) -> str:
    text = text.strip()
    for pattern, replacement in _CLEANUPS:
        text = pattern.sub(replacement, text)
    return text.strip()


def word_count(text: str) -> int:
    return len(text.split())


def _looks_like_list_item(paragraph: str) -> bool:
    """Short lines that don't end like a sentence are usually list items or table rows."""
    return word_count(paragraph) < 12 and not _SENTENCE_END.search(paragraph)


def _make_section(heading: str | None, path: list[str], level: int, body: str) -> dict[str, Any]:
    paragraphs = [p for p in (clean_paragraph(line) for line in body.split("\n")) if p]
    words = sum(word_count(p) for p in paragraphs)
    list_items = sum(1 for p in paragraphs if _looks_like_list_item(p))
    return {
        "heading": heading,
        "path": path,
        "level": level,
        "paragraphs": paragraphs,
        "words": words,
        "list_ratio": round(list_items / len(paragraphs), 2) if paragraphs else 0.0,
    }


def parse_extract(extract: str) -> list[dict[str, Any]]:
    """Split an extract into sections. The lead (text before the first heading) has heading None.

    `path` holds the heading chain, e.g. ["Potential benefits", "Cost reduction"], so a
    subsection can be shown with its parent. Sections with no text are dropped.
    """
    sections: list[dict[str, Any]] = []
    matches = list(_HEADING.finditer(extract))
    lead_end = matches[0].start() if matches else len(extract)
    lead = _make_section(None, [], 1, extract[:lead_end])
    if lead["paragraphs"]:
        sections.append(lead)

    stack: list[tuple[int, str]] = []  # (level, heading) of the current heading chain
    for index, match in enumerate(matches):
        level = len(match.group(1))  # "==" -> 2
        heading = clean_paragraph(match.group(2))
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))

        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(extract)
        section = _make_section(heading, [h for _, h in stack], level, extract[match.end():body_end])
        if section["paragraphs"]:
            sections.append(section)

    return sections


def total_words(sections: list[dict[str, Any]]) -> int:
    return sum(section["words"] for section in sections)
