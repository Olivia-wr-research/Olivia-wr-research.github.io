#!/usr/bin/env python3
"""Conservative source-scope catalog and page/list adapters for TERRAFAR."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

APP = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP / "maintenance/terrafar-source-audit/adapter_catalog.json"


class PageParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.text_parts: list[str] = []
        self.headings: list[str] = []
        self.links: list[dict[str, str]] = []
        self.title_parts: list[str] = []
        self._heading = False
        self._title = False
        self._skip_depth = 0
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if re.fullmatch(r"h[1-6]", tag.lower()):
            self._heading = True
        if tag.lower() == "title":
            self._title = True
        if tag.lower() == "a" and values.get("href"):
            self._anchor = {"url": urljoin(self.page_url, html.unescape(values["href"])), "title": ""}

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if re.fullmatch(r"h[1-6]", tag.lower()):
            self._heading = False
        if tag.lower() == "title":
            self._title = False
        if tag.lower() == "a" and self._anchor:
            title = re.sub(r"\s+", " ", self._anchor["title"]).strip()
            if title:
                self.links.append({"url": self._anchor["url"], "title": title})
            self._anchor = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        self.text_parts.append(value)
        if self._heading:
            self.headings.append(value)
        if self._title:
            self.title_parts.append(value)
        if self._anchor is not None:
            self._anchor["title"] += " " + value


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def apply_catalog(sources: list[dict], catalog: dict | None = None) -> list[dict]:
    """Overlay adapter metadata at runtime without changing the frozen registry."""
    catalog = catalog or load_catalog()
    overrides = catalog.get("source_overrides", {})
    result = []
    for source in sources:
        spec = overrides.get(source.get("source_id"))
        if not spec:
            result.append(source)
            continue
        patched = copy.deepcopy(source)
        patched["adapter_scope"] = {key: spec[key] for key in ("institution", "opportunity_type", "filter", "pagination", "completeness_rule")}
        patched["monitor_endpoints"] = []
        for configured in spec.get("endpoints", []):
            endpoint = dict(configured)
            endpoint["adapter_scope"] = patched["adapter_scope"]
            patched["monitor_endpoints"].append(endpoint)
        result.append(patched)
    return result


def _doc(body: bytes, url: str) -> tuple[str, str, list[str], list[dict[str, str]]]:
    parser = PageParser(url)
    parser.feed(body.decode("utf-8", "replace"))
    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    title = re.sub(r"\s+", " ", " ".join(parser.title_parts) or (parser.headings[0] if parser.headings else "")).strip()
    headings = list(dict.fromkeys(re.sub(r"\s+", " ", item).strip() for item in parser.headings if item.strip()))
    unique_links = {}
    for link in parser.links:
        if link["url"].startswith(("https://", "http://")):
            unique_links.setdefault(link["url"], link["title"])
    links = [{"url": link, "title": label} for link, label in unique_links.items()]
    return title, text, headings, links


def _page_row(url: str, title: str, text: str, headings: list[str], links: list[dict[str, str]]) -> dict:
    return {
        "id": url,
        "url": url,
        "title": title,
        "page_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "headings": headings[:80],
        "links": links[:250],
    }


def _scope(url: str, adapter: str, title: str, text: str, headings: list[str], links: list[dict[str, str]], complete: bool, reason: str, result_count: int | None = None) -> tuple[list[dict], dict]:
    rows = [_page_row(url, title, text, headings, links)] if title and text else []
    return rows, {
        "adapter": adapter,
        "scope_kind": "single_page_snapshot_or_configured_list",
        "parsed_title": title,
        "headings_seen": headings,
        "links_seen": len(links),
        "explicit_result_count": result_count,
        "_complete": complete,
        "pagination_detected": not complete,
        "completeness_reason": reason,
    }


def semantic_result(adapter: str, url: str, body: bytes):
    title, text, headings, links = _doc(body, url)
    low = text.lower()
    if adapter == "university_page_snapshot":
        if not title or len(text) < 80:
            raise ValueError("institutional_page_structure_not_confirmed")
        has_more = bool(re.search(r"\b(load more|show more|next page|next results)\b", low))
        return _scope(url, adapter, title, text, headings, links, not has_more,
                      "complete page snapshot" if not has_more else "page advertises dynamic expansion; list completeness not proven")

    if adapter == "helsinki_successfactors":
        if "jobs.helsinki.fi" not in url or len(text) < 80:
            raise ValueError("helsinki_successfactors_scope_not_confirmed")
        rows = [link for link in links if "jobs.helsinki.fi" in link["url"] and re.search(r"/(?:job|position|go)/", link["url"], re.I)]
        count_match = re.search(r"\b(\d+)\s+(?:jobs|positions|results|open positions)\b", low)
        total = int(count_match.group(1)) if count_match else None
        next_link = any(re.search(r"\bnext\b|[?&](?:page|start)=\d+", link["title"] + " " + link["url"], re.I) for link in links)
        complete = total is not None and len({row["url"] for row in rows}) == total and not next_link
        normalized = [{"id": row["url"], "url": row["url"], "title": row["title"]} for row in rows]
        scope = {"scope_kind": "employment_result_list", "explicit_result_count": total, "parsed_distinct_rows": len(normalized),
                 "pagination_detected": next_link or not complete, "_complete": complete,
                 "completeness_reason": "result total equals unique parsed rows" if complete else "result total or terminal pagination proof missing"}
        return normalized, scope

    if adapter == "mpg_jobboard":
        if "mpg.de" not in url or not title:
            raise ValueError("mpg_jobboard_structure_not_confirmed")
        has_more = bool(re.search(r"\b(show more|load more|young researchers)\b", low))
        rows = [{"id": row["url"], "url": row["url"], "title": row["title"]}
                for row in links if re.search(r"/(?:job|jobs|stellenangebote)/", row["url"], re.I)]
        # The base URL does not prove that Young Researchers is the active filter.
        complete = False
        scope = {"scope_kind": "jobboard_route_not_complete_opportunity_list", "parsed_distinct_rows": len({row["url"] for row in rows}),
                 "filter_confirmed": False, "dynamic_expansion_detected": has_more, "pagination_detected": True,
                 "_complete": complete, "completeness_reason": "Young Researchers filter and Show more terminal state not confirmed"}
        return rows or [_page_row(url, title, text, headings, links)], scope

    if adapter == "ubc_geography_admissions":
        required = ("geography" in low and bool(re.search(r"\bm\.?a\.?\b", low))
                    and bool(re.search(r"\bm\.?sc\.?\b", low)) and bool(re.search(r"\bph\.?d\.?\b", low))
                    and "funding" in low and ("apply" in low or "application" in low))
        return _scope(url, adapter, title, text, headings, links, required,
                      "MA, MSc, PhD, funding, and application groups present" if required else "one or more required admissions sections absent")

    if adapter == "helsinki_doctoral_programme":
        required = "geography" in low and "doctoral" in low and any("programme" in item.lower() for item in headings)
        return _scope(url, adapter, title, text, headings, links, required,
                      "programme page identifies geography and doctoral programme" if required else "geography or doctoral programme structure not confirmed")

    if adapter == "oxford_course_page":
        required = "geography" in low and "dphil" in low and "funding" in low and ("full-time" in low or "full time" in low) and ("part-time" in low or "part time" in low)
        return _scope(url, adapter, title, text, headings, links, required,
                      "course, full-time/part-time, and funding sections present" if required else "required course or study-mode sections not confirmed")

    if adapter == "rmit_scholarship_detail":
        page_fields = sum(bool(re.search(pattern, low)) for pattern in (r"scholarship", r"eligibility", r"value|stipend", r"duration", r"closing date|application deadline", r"how to apply|application"))
        required = "rmit" in url and "scholarship" in low and page_fields >= 4 and bool(title)
        return _scope(url, adapter, title, text, headings, links, required,
                      "single scholarship detail contains stable title and at least four expected field groups" if required else "scholarship detail field structure incomplete")

    if adapter == "usf_current_funding":
        current = re.search(r"current opportunities", low)
        historical = re.search(r"grants awarded", low)
        if not current or not historical or historical.start() <= current.start():
            return _scope(url, adapter, title, text, headings, links, False, "Current opportunities and historical boundary not both confirmed")
        current_text = text[current.end():historical.start()]
        current_links = [link for link in links if link["title"].lower() in current_text.lower() or link["url"].lower().find("grant") >= 0]
        has_more = bool(re.search(r"\b(load more|next page|view more)\b", current_text, re.I))
        rows = [{"id": link["url"], "url": link["url"], "title": link["title"]} for link in current_links]
        complete = not has_more and bool(rows)
        scope = {"scope_kind": "current_funding_opportunities_only", "parsed_current_opportunity_links": len(rows),
                 "historical_awards_excluded": True, "pagination_detected": has_more, "_complete": complete,
                 "completeness_reason": "current section bounded before historical awards" if complete else "current section empty or dynamic expansion unresolved"}
        return rows, scope

    if adapter in {"eth_listing", "jobbnorge_rss"}:
        return None, None
    return None, None


def enrich_scope(endpoint: dict, scope: dict | None) -> dict | None:
    if scope is None:
        return None
    scope["configured_endpoint_scope"] = endpoint.get("scope")
    scope["adapter_scope"] = endpoint.get("adapter_scope", {})
    return scope
