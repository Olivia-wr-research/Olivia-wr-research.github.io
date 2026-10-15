"""Immutable document acquisition and locator-preserving normalization."""

from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path


class AcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedDocument:
    sha256: str
    mime_type: str
    text: str
    spans: tuple[dict, ...]
    parser_version: str
    quality_status: str
    ocr_required: bool


def detect_mime(data: bytes, name: str) -> str:
    suffix = Path(name).suffix.lower()
    if data.startswith(b"%PDF-") or suffix == ".pdf": return "application/pdf"
    if data.startswith(b"PK") and suffix == ".docx": return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix in {".html", ".htm"} or re.search(br"<html\b", data[:1000], re.I): return "text/html"
    return "text/plain"


def _clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\r", "")).strip()


class _HTML(HTMLParser):
    BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "tr", "section", "article", "div"}
    def __init__(self):
        super().__init__(convert_charrefs=True); self.hidden = 0; self.parts: list[str] = []; self.current: list[str] = []
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}: self.hidden += 1
        if tag == "br" and not self.hidden: self.current.append(" ")
    def handle_data(self, data):
        if not self.hidden: self.current.append(data)
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.hidden: self.hidden -= 1
        elif tag in self.BLOCKS and not self.hidden:
            value = _clean("".join(self.current)); self.current = []
            if value: self.parts.append(value)
    def finish(self):
        value = _clean("".join(self.current))
        if value: self.parts.append(value)
        return self.parts


def _spans(blocks: list[str], kind: str, key: str) -> tuple[dict, ...]:
    return tuple({"text": text, "locator": {"kind": kind, key: i}} for i, text in enumerate(blocks, 1) if text)


def normalize_bytes(data: bytes, name: str) -> NormalizedDocument:
    if not data:
        raise AcquisitionError("empty input")
    mime = detect_mime(data, name)
    try:
        if mime == "text/html":
            parser = _HTML(); parser.feed(data.decode("utf-8", errors="replace")); spans = _spans(parser.finish(), "dom_block", "block")
        elif mime.endswith("wordprocessingml.document"):
            with zipfile.ZipFile(BytesIO(data)) as archive: xml = archive.read("word/document.xml")
            root = ET.fromstring(xml); ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            blocks = [_clean("".join(n.text or "" for n in p.iter(ns + "t"))) for p in root.iter(ns + "p")]
            spans = _spans(blocks, "docx_paragraph", "paragraph")
        elif mime == "application/pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise AcquisitionError("PDF parser dependency pypdf is unavailable") from exc
            reader = PdfReader(BytesIO(data))
            spans = tuple(
                {"text": _clean(line), "locator": {"kind": "pdf_page_line", "page": page_number, "line": line_number}}
                for page_number, page in enumerate(reader.pages, 1)
                for line_number, line in enumerate((page.extract_text() or "").splitlines(), 1)
                if _clean(line)
            )
        else:
            blocks = [_clean(line) for line in data.decode("utf-8", errors="replace").splitlines()]
            spans = _spans(blocks, "text_line", "line")
    except AcquisitionError:
        raise
    except Exception as exc:
        raise AcquisitionError(f"corrupt or unsupported {mime}: {type(exc).__name__}") from exc
    text = "\n".join(span["text"] for span in spans)
    if not text:
        raise AcquisitionError("normalized text is empty")
    quality = "pass" if len(re.sub(r"\s", "", text)) >= 10 else "fail_short_text"
    return NormalizedDocument(hashlib.sha256(data).hexdigest(), mime, text, spans, "normalizer-1.0", quality, mime == "application/pdf" and quality != "pass")


def store_immutable(data: bytes, raw_dir: str | Path) -> tuple[Path, bool]:
    digest = hashlib.sha256(data).hexdigest(); target = Path(raw_dir) / digest[:2] / digest
    if target.exists():
        if target.read_bytes() != data: raise AcquisitionError("hash collision or cache corruption")
        return target, True
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data); target.chmod(0o444)
    return target, False


def retry(operation, attempts: int = 3, base_delay: float = 0.0):
    errors = []
    for attempt in range(attempts):
        try: return operation()
        except Exception as exc:
            errors.append(type(exc).__name__)
            if attempt + 1 < attempts: time.sleep(base_delay * (2 ** attempt))
    raise AcquisitionError(json.dumps({"attempts": attempts, "errors": errors}))
