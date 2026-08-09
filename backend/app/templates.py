"""Parses catalog.json + templates/*.md into structured per-document data.

The 11 templates are real Common Paper legal documents. Their body text
uses a handful of `<span class="...">` conventions to mark fields the
cover page/order form/key-terms/etc. would otherwise fill in — this module
treats all of those uniformly as "fields the user needs to tell us about"
rather than preserving Common Paper's own cover-page/order-form/key-terms
distinction (PREL-6 scope: one generic document flow, not a faithful
reproduction of Common Paper's document architecture).

Parsed once at import time (the files are static and bundled into the
Docker image) so a malformed template fails fast at startup rather than on
first request.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from pydantic import BaseModel

from .config import REPO_ROOT

TEMPLATES_DIR = REPO_ROOT / "templates"
CATALOG_PATH = REPO_ROOT / "catalog.json"

_FIELD_SPAN_CLASSES = "coverpage_link|keyterms_link|orderform_link|sow_link|businessterms_link"
_HEADING_VARIANT_BY_CLASS = {"header_2": "header2", "header_3": "header3"}

_INLINE_TOKEN_RE = re.compile(
    r'<span\s+class="(?P<field_class>' + _FIELD_SPAN_CLASSES + r')"[^>]*>(?P<field_text>.*?)</span>'
    r'|<span\s+class="(?P<heading_class>header_2|header_3)"[^>]*>(?P<heading_text>.*?)</span>'
    r'|\*\*(?P<bold_text>.+?)\*\*'
    r'|\[(?P<link_text>[^\]]+)\]\((?P<link_href>[^)]+)\)'
    r'|<(?P<bare_url>https?://[^>\s]+)>'
)
_LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[0-9]+|[A-Za-z]+)\.\s+(?P<rest>.*)$")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_POSSESSIVE_RE = re.compile(r"[’']s$")


class Field(BaseModel):
    key: str
    label: str


class InlineSegment(BaseModel):
    type: str  # "text" | "field" | "link"
    text: str | None = None
    variant: str | None = None  # "plain" | "bold" | "header2" | "header3" (type == "text" only)
    field_key: str | None = None  # type == "field" only
    href: str | None = None  # type == "link" only


class BodyItem(BaseModel):
    depth: int
    inline: list[InlineSegment]


class DocumentSummary(BaseModel):
    id: str
    name: str
    description: str


class DocumentTemplate(DocumentSummary):
    fields: list[Field]
    body: list[BodyItem]
    attribution: str | None = None


# Every bilateral agreement needs to know who the two parties are, but (as
# with the original Mutual NDA prototype) the template bodies themselves
# rarely spell that out as a tagged field — it's conventionally a separate
# "Cover Page" document these Standard Terms incorporate by reference. So
# every document gets this fixed pair in addition to whatever fields its
# own body references.
PARTY_FIELDS: list[Field] = [
    Field(key="partyOneName", label="Party One — Legal Name"),
    Field(key="partyOneAddress", label="Party One — Address"),
    Field(key="partyTwoName", label="Party Two — Legal Name"),
    Field(key="partyTwoAddress", label="Party Two — Address"),
]


def _slugify_id(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def _field_key(label: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", label)
    if not words:
        return "field"
    first, *rest = words
    return first.lower() + "".join(word.capitalize() for word in rest)


def _clean_text(raw: str) -> str:
    return html.unescape(_HTML_TAG_RE.sub("", raw)).strip()


def _clean_plain_text(raw: str) -> str:
    # Collapses runs of whitespace but, unlike _clean_text, does NOT strip
    # leading/trailing whitespace entirely. Some templates put a header/
    # bold span directly adjacent to the prose that follows it with only
    # whitespace as the separator (e.g. DPA.md: `<span class="header_3">
    # Provider as Processor.</span>  In situations where...`, two spaces).
    # Stripping that away here would glue the two segments together with
    # no space at all once rendered as adjacent inline elements.
    return re.sub(r"\s+", " ", html.unescape(_HTML_TAG_RE.sub("", raw)))


def _normalize_label(raw_inner_html: str) -> str:
    text = _clean_text(raw_inner_html)
    text = _POSSESSIVE_RE.sub("", text)
    return text.strip().rstrip(".:")


def _clean_footer_text(raw: str) -> str:
    # Keeps link *text* (e.g. "Version 1.0") but drops the href — the
    # attribution line is rendered as plain text, not live links.
    return _clean_text(_MD_LINK_RE.sub(r"\1", raw))


class _TemplateParser:
    """Parses one template file, collecting fields as it encounters them."""

    def __init__(self) -> None:
        self.fields_by_key: dict[str, Field] = {field.key: field for field in PARTY_FIELDS}

    def parse_file(self, path: Path) -> tuple[list[BodyItem], str | None]:
        body: list[BodyItem] = []
        footer_lines: list[str] = []
        seen_list_item = False

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = _LIST_ITEM_RE.match(line)
            if match:
                seen_list_item = True
                depth = len(match.group("indent")) // 4
                inline = self._parse_inline(match.group("rest"))
                if inline:
                    body.append(BodyItem(depth=depth, inline=inline))
            elif seen_list_item:
                # Trailing non-list text after the numbered body (e.g. the
                # Mutual NDA's Common Paper attribution line). Templates
                # with no such trailing text just produce an empty footer.
                footer_lines.append(_clean_footer_text(line))
            # Non-list lines *before* the first list item (other than the
            # leading "# Title") don't occur in any of the 11 shipped
            # templates; if one shows up in a future template it's simply
            # dropped here rather than crashing the parse.

        attribution = " ".join(footer_lines) if footer_lines else None
        return body, attribution

    def _parse_inline(self, line: str) -> list[InlineSegment]:
        segments: list[InlineSegment] = []
        pos = 0
        for match in _INLINE_TOKEN_RE.finditer(line):
            if match.start() > pos:
                self._append_plain(segments, line[pos : match.start()])

            if match.group("field_class"):
                label = _normalize_label(match.group("field_text"))
                segments.append(InlineSegment(type="field", field_key=self._register_field(label)))
            elif match.group("heading_class"):
                text = _clean_text(match.group("heading_text"))
                if text:
                    variant = _HEADING_VARIANT_BY_CLASS[match.group("heading_class")]
                    segments.append(InlineSegment(type="text", text=text, variant=variant))
            elif match.group("bold_text") is not None:
                text = _clean_text(match.group("bold_text"))
                if text:
                    segments.append(InlineSegment(type="text", text=text, variant="bold"))
            elif match.group("link_text") is not None:
                segments.append(
                    InlineSegment(
                        type="link",
                        text=_clean_text(match.group("link_text")),
                        href=match.group("link_href"),
                    )
                )
            elif match.group("bare_url"):
                url = match.group("bare_url")
                segments.append(InlineSegment(type="link", text=url, href=url))

            pos = match.end()

        if pos < len(line):
            self._append_plain(segments, line[pos:])

        return segments

    def _append_plain(self, segments: list[InlineSegment], raw: str) -> None:
        text = _clean_plain_text(raw)
        if text:
            segments.append(InlineSegment(type="text", text=text, variant="plain"))

    def _register_field(self, label: str) -> str:
        key = _field_key(label)
        if key not in self.fields_by_key:
            self.fields_by_key[key] = Field(key=key, label=label)
        return key


def _load_all_documents() -> list[DocumentTemplate]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    documents = []
    for entry in catalog:
        parser = _TemplateParser()
        body, attribution = parser.parse_file(TEMPLATES_DIR / entry["filename"])
        documents.append(
            DocumentTemplate(
                id=_slugify_id(entry["filename"]),
                name=entry["name"],
                description=entry["description"],
                fields=list(parser.fields_by_key.values()),
                body=body,
                attribution=attribution,
            )
        )
    return documents


ALL_DOCUMENTS: list[DocumentTemplate] = _load_all_documents()
DOCUMENTS_BY_ID: dict[str, DocumentTemplate] = {document.id: document for document in ALL_DOCUMENTS}
DOCUMENT_IDS: list[str] = [document.id for document in ALL_DOCUMENTS]


def get_document(document_id: str) -> DocumentTemplate | None:
    return DOCUMENTS_BY_ID.get(document_id)
