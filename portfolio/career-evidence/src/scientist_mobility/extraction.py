"""Deterministic extraction, provider interface, and evidence validation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from .acquisition import NormalizedDocument

DATE_RANGE = re.compile(r"(?P<start>\d{4}(?:\.\d{1,2})?)\s*[-–—]\s*(?P<end>Present|present|current|\d{4}(?:\.\d{1,2})?)")


def parse_date(value: str | None) -> dict:
    if not value or value.casefold() in {"present", "current", "unknown"}:
        return {"value": None, "precision": "unknown"}
    if not re.fullmatch(r"\d{4}(?:\.\d{1,2})?", value):
        raise ValueError("unsupported date format")
    if "." in value:
        year, month = value.split(".")
        if not 1 <= int(month) <= 12:
            raise ValueError("month must be between 1 and 12")
        value = f"{year}.{int(month):02d}"
    return {"value": value, "precision": "month" if "." in value else "year"}


def chunk_spans(spans: tuple[dict, ...], size: int = 20, overlap: int = 2) -> list[tuple[dict, ...]]:
    if size <= overlap or overlap < 0: raise ValueError("size must exceed nonnegative overlap")
    chunks = []; start = 0
    while start < len(spans):
        chunks.append(spans[start:start + size])
        if start + size >= len(spans): break
        start += size - overlap
    return chunks


def _event_type(section: str, role: str) -> str:
    text = f"{section} {role}".casefold()
    if "education" in text or any(x in text for x in ("bachelor", "master", "ph.d", "doctor of")): return "education"
    if "industry" in section.casefold(): return "industry_rd"
    if "postdoc" in text: return "postdoc"
    return "academic"


def extract_rules(document: NormalizedDocument, scientist_id: str, source_document_id: str, run_id: str) -> list[dict]:
    section = ""; organization = ""; events = []
    for span in document.spans:
        line = span["text"].strip()
        if line.upper() == line and not DATE_RANGE.search(line):
            if "EXPERIENCE" in line or line == "EDUCATION": section = line
            elif len(line.split()) >= 2: organization = line
            continue
        match = DATE_RANGE.search(line)
        if not match: continue
        role = line[:match.start()].strip(" ,—-")
        etype = _event_type(section, role)
        flags = {key: False for key in ("primary","concurrent","education","postdoc","visiting","leave","consulting","honorary","leadership","board","advisory","short_visit")}
        flags["education"] = etype == "education"; flags["postdoc"] = etype == "postdoc"
        low = role.casefold()
        for key, terms in {"visiting":("visiting",), "leave":("leave","sabbatical"), "consulting":("consult",), "honorary":("honorary","courtesy"), "leadership":("director","dean","chair"), "board":("board",), "advisory":("advis",), "short_visit":("short visit",)}.items():
            flags[key] = any(t in low for t in terms)
        flags["concurrent"] = any(flags[k] for k in ("visiting","leave","consulting","honorary","board","advisory","short_visit"))
        flags["primary"] = not flags["concurrent"] and not flags["education"]
        event_id = "evt-" + hashlib.sha256(f"{scientist_id}|{source_document_id}|{span['locator']}|{line}".encode()).hexdigest()[:16]
        events.append({"career_event_id": event_id, "scientist_id": scientist_id, "source_document_id": source_document_id, "event_type": etype, "organization_raw": organization or "UNKNOWN_EXPLICIT_REVIEW", "role_raw": role, "start": parse_date(match.group("start")), "end": parse_date(match.group("end")), "role_flags": flags, "evidence_exact": line, "evidence_locator": span["locator"], "confidence": 0.75, "status": "candidate", "extraction_method": "rules", "extraction_version": "rules-1.0", "created_run_id": run_id})
    return deduplicate_events(events)


def deduplicate_events(events: list[dict]) -> list[dict]:
    result = {} 
    for event in events: result[event["career_event_id"]] = event
    return list(result.values())


def validate_evidence(events: list[dict], document: NormalizedDocument) -> None:
    by_locator = {str(span["locator"]): span["text"] for span in document.spans}
    for event in events:
        exact = event.get("evidence_exact", "")
        if not exact or by_locator.get(str(event.get("evidence_locator"))) != exact:
            raise ValueError(f"unresolvable evidence for {event.get('career_event_id')}")
        if event["start"]["precision"] == "unknown" and event["start"]["value"] is not None: raise ValueError("imputed start")
        if event["end"]["precision"] == "unknown" and event["end"]["value"] is not None: raise ValueError("imputed end")


class ExtractionProvider(Protocol):
    provider_name: str
    def extract(self, *, spans: tuple[dict, ...], schema: dict, prompt_version: str) -> dict: ...


@dataclass
class MockProvider:
    response: dict
    provider_name: str = "mock"
    calls: int = 0
    def extract(self, *, spans: tuple[dict, ...], schema: dict, prompt_version: str) -> dict:
        self.calls += 1
        return self.response
