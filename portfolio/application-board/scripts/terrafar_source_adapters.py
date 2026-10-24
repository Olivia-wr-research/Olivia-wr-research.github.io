#!/usr/bin/env python3
"""Conservative source-scope catalog and page/list adapters for TERRAFAR."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

APP = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP / "maintenance/terrafar-source-audit/adapter_catalog.json"


class _Element:
    def __init__(self, tag, attrs=None, parent=None, order=0):
        self.tag, self.attrs, self.parent, self.order = tag, dict(attrs or []), parent, order
        self.children, self.closed = [], False

    def elements(self, tag=None):
        for child in self.children:
            if isinstance(child, _Element):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.elements(tag)

    def text(self, include_scripts=False):
        if not include_scripts and self.tag in {"script", "style", "svg", "noscript"}:
            return ""
        return re.sub(r"\s+", " ", " ".join(
            child.text(include_scripts) if isinstance(child, _Element) else child
            for child in self.children)).strip()


class _DetailTree(HTMLParser):
    """Small standard-library tree for observed HTML structures, never script execution."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.root, self.nodes = _Element("document"), []
        self.stack = [self.root]
        self.feed(body.decode("utf-8", "strict"))
        self.close()

    def handle_starttag(self, tag, attrs):
        node = _Element(tag, attrs, self.stack[-1], len(self.nodes))
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag in self.VOID:
            node.closed = True
        else:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack[index].closed = True
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def unique(self, tag=None, attribute=None, value=None, within=None):
        rows = list((within or self.root).elements(tag))
        if attribute:
            rows = [row for row in rows if row.attrs.get(attribute) == value]
        if len(rows) != 1 or not rows[0].closed:
            raise ValueError("detail_structure_missing_duplicate_or_unclosed:" + str(value or tag))
        return rows[0]


def _sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _date_from_english(value):
    value = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", value)
    for pattern in ("%d %B %Y", "%B %d %Y", "%d %b %Y"):
        try:
            return dt.datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError("detail_date_unrecognized")


def _detail_document(body, url, host, path_pattern):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != host or parsed.query
            or not re.fullmatch(path_pattern, parsed.path)):
        raise ValueError("detail_registered_url_scope_mismatch")
    tree = _DetailTree(body)
    tree.unique("html")
    main = tree.unique("main")
    if len(main.text()) < 200:
        raise ValueError("detail_body_missing_or_too_short")
    return tree, main


def _links(node, url):
    result = []
    for anchor in node.elements("a"):
        target = urljoin(url, anchor.attrs.get("href", ""))
        if urlsplit(target).scheme in {"http", "https"} and anchor.text():
            result.append({"url": target, "title": anchor.text()})
    return result


def _detail_result(adapter, url, row, section_nodes):
    row.update({"id": url, "url": url, "record_kind": "official_job_detail",
                "current_open_status": "unknown", "human_reviewed": False,
                "source_sections": {name: {"text_sha256": _sha_text(node.text()), "characters": len(node.text())}
                                    for name, node in section_nodes.items()}})
    return [row], {"adapter": adapter, "scope_kind": "one_registered_job_detail_page",
                   "registered_detail_url": url, "_complete": True, "pagination_detected": False,
                   "institution_wide_vacancy_list_complete": False, "application_portal_acceptance_verified": False,
                   "parsed_distinct_rows": 1, "sections_validated": sorted(section_nodes),
                   "completeness_reason": "One identity-bound, closed HTML detail document with all required observed template sections; no claim about other jobs or live portal acceptance."}


def _wur_job_detail(url, body):
    tree, main = _detail_document(body, url, "www.wur.nl", r"/en/vacancy/[a-z0-9-]+")
    title = tree.unique("h1", within=main).text()
    canonical = tree.unique("link", "rel", "canonical").attrs.get("href")
    if canonical != url:
        raise ValueError("wur_canonical_identity_mismatch")
    postings = []
    for script in tree.root.elements("script"):
        if script.attrs.get("type") != "application/ld+json":
            continue
        data = json.loads(script.text(include_scripts=True))
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        postings += [item for item in graph if isinstance(item, dict) and item.get("@type") == "JobPosting"]
    if len(postings) != 1:
        raise ValueError("wur_single_jobposting_not_confirmed")
    job = postings[0]
    if (job.get("@id", "").split("#")[0] != url or job.get("title") != title
            or not job.get("identifier") or job.get("hiringOrganization", {}).get("name") != "Wageningen University & Research"):
        raise ValueError("wur_jobposting_identity_mismatch")
    sections = {}
    for section in main.elements("section"):
        if not re.fullmatch(r"text-wrapper--\d+", section.attrs.get("id", "")):
            continue
        headings = list(section.elements("h2"))
        if len(headings) == 1:
            key = headings[0].text()
            if key in sections or not section.closed or len(section.text()) <= len(key) + 20:
                raise ValueError("wur_detail_section_invalid")
            sections[key] = section
    required = {"Your job", "Your qualities", "We offer", "Coming from abroad", "Important information", "We are"}
    if not required <= sections.keys():
        raise ValueError("wur_required_detail_sections_missing")
    info, offer, profile = (sections[key].text() for key in ("Important information", "We offer", "Your qualities"))
    deadlines = re.findall(r"You can apply up to and including\s+((?:\d{1,2}\s+[A-Z][a-z]+\s+\d{4})|(?:[A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?\s+\d{4}))", info)
    if len(deadlines) != 1:
        raise ValueError("wur_inclusive_body_deadline_missing_or_ambiguous")
    if not any("apply" in button.text().lower() for button in main.elements("button")) or "website" not in info.lower():
        raise ValueError("wur_application_route_structure_missing")
    supplement = [item for item in _links(sections["Important information"], url)
                  if urlsplit(item["url"]).hostname == "forms.cloud.microsoft"]
    form_required = "must fill in a mandatory form" in info
    if form_required and len(supplement) != 1:
        raise ValueError("wur_mandatory_supplementary_form_missing")
    row = {"title": title, "institution": job["hiringOrganization"]["name"], "posting_id": str(job["identifier"]),
           "opportunity_type": "postdoc" if title.lower().startswith("postdoc") else "phd" if title.lower().startswith("phd") else "unknown",
           "location": job.get("jobLocation"), "salary": job.get("baseSalary"), "salary_gross_stated": "gross salary" in offer.lower(),
           "deadline": {"date": _date_from_english(deadlines[0]), "raw": deadlines[0], "precision": "day", "timezone": None, "inclusive": True},
           "metadata_valid_through_raw": job.get("validThrough"), "metadata_date_posted_raw": job.get("datePosted"),
           "metadata_cutoff_note": "JSON-LD validThrough retained separately; it does not override the body inclusive date or prove portal acceptance.",
           "fully_funded_statement_present": "fully funded PhD position" in offer,
           "requirements_text": profile, "employment_conditions_text": offer,
           "application_instructions_text": info,
           "application_route": {"status": "stated_route_only", "url": url, "kind": "embedded_application_button",
                                 "portal_status": "unknown", "supplementary_form_required": form_required, "supplementary_forms": supplement}}
    return _detail_result("wur_job_detail", url, row, {key: sections[key] for key in sorted(required)})


def _eth_job_detail(url, body):
    tree, main = _detail_document(body, url, "jobs.ethz.ch", r"/job/view/JOPG_ethz_[A-Za-z0-9]+")
    heading = tree.unique("h1", "id", "job-title", main)
    sections = {}
    for name in ("project-background", "job-description", "profile", "we-offer", "application-info"):
        section_heading = tree.unique("h2", "id", name, main)
        parent = section_heading.parent
        paragraphs = [node for node in parent.elements("div") if "description__paragraph" in node.attrs.get("class", "").split()]
        if not parent.closed or not paragraphs or len(paragraphs[0].text()) < 25:
            raise ValueError("eth_required_detail_region_missing:" + name)
        sections[name] = paragraphs[0]
    application_links = [node for node in main.elements("a") if "application__button--link" in node.attrs.get("class", "").split()]
    token = urlsplit(url).path.rsplit("JOPG_ethz_", 1)[1]
    if len(application_links) != 1:
        raise ValueError("eth_job_specific_application_link_missing")
    application_url = application_links[0].attrs.get("href", "")
    portal = urlsplit(application_url)
    if portal.scheme != "https" or portal.hostname != "emea2.softfactors.com" or portal.path != "/job-opening/rgum-" + token:
        raise ValueError("eth_job_specific_application_link_identity_mismatch")
    header = tree.unique("h4", within=heading.parent).text()
    contract = re.fullmatch(r"(\d{1,3})%,\s*([^,]+),\s*(fixed-term|permanent)", header)
    if not contract or not 0 < int(contract[1]) <= 100:
        raise ValueError("eth_employment_header_structure_missing")
    profile, application = sections["profile"].text(), sections["application-info"].text()
    if not re.search(r"online application portal", application, re.I):
        raise ValueError("eth_online_application_instruction_missing")
    review = re.search(r"begin reviewing applications on\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})", application)
    until_filled = "applications will close once a suitable candidate is found" in application
    required_desired = re.search(r"Required\s*:\s*(.*?)\s*Desired\s+(.*)", profile)
    row = {"title": heading.text(), "institution": "ETH Zürich", "posting_id": "JOPG_ethz_" + token,
           "opportunity_type": "phd" if re.search(r"\bdoctoral\b|\bphd\b", heading.text(), re.I) else "unknown",
           "employment": {"percentage": int(contract[1]), "location": contract[2], "contract": contract[3]},
           "salary": None, "requirements_text": profile,
           "requirements_required_text": required_desired[1] if required_desired else profile,
           "requirements_desired_text": required_desired[2] if required_desired else None,
           "deadline": {"date": None, "review_start": _date_from_english(review[1]) if review else None,
                        "review_start_raw": review[1] if review else None, "rolling": True if until_filled else None, "timezone": None},
           "application_instructions_text": application,
           "application_route": {"status": "official_detail_link_identified", "url": application_url,
                                 "portal_status": "unknown", "related_links": _links(sections["application-info"], url)}}
    return _detail_result("eth_job_detail", url, row, sections)


def _usf_current_section(url, body):
    if urlsplit(url).hostname != "www.urbanstudiesfoundation.org" or urlsplit(url).path.rstrip("/") != "/funding":
        raise ValueError("usf_registered_funding_scope_mismatch")
    tree = _DetailTree(body)
    tree.unique("html")
    current, past = tree.unique("h2", "id", "current"), tree.unique("h2", "id", "past")
    if (current.text().lower() != "current opportunities" or past.text().lower() != "grants awarded"
            or current.parent is not past.parent or current.order >= past.order):
        raise ValueError("usf_current_and_history_section_boundary_not_confirmed")
    nodes = [node for node in current.parent.elements() if current.order < node.order < past.order]
    anchors = [node for node in nodes if node.tag == "a"]
    rows, unrecognized = {}, []
    for anchor in anchors:
        target = urljoin(url, anchor.attrs.get("href", "")); path = urlsplit(target)
        if (path.scheme != "https" or path.hostname != "www.urbanstudiesfoundation.org"
                or not re.fullmatch(r"/funding/[a-z0-9-]+/", path.path)
                or path.path in {"/funding/grantees/", "/funding/grants-awarded/"} or path.query or path.fragment
                or not anchor.text()):
            unrecognized.append(target); continue
        label = anchor.text(); closed = bool(re.search(r"\(closed\)", label, re.I))
        rows[target] = {"id": target, "url": target, "title": re.sub(r"\s*\(closed\)", "", label, flags=re.I).strip(),
                        "announcement_status": "closed" if closed else "unknown", "current_open_status": "unknown",
                        "record_kind": "funding_programme_in_current_section"}
    section_text = " ".join(node.text() for node in nodes if node.parent is current.parent)
    has_more = bool(re.search(r"\b(load more|next page|view more)\b", section_text, re.I))
    complete = bool(rows) and not unrecognized and not has_more and all(node.closed for node in nodes)
    return list(rows.values()), {"scope_kind": "current_funding_section_programmes_not_open_vacancies",
                                "parsed_current_opportunity_links": len(rows), "historical_awards_excluded": True,
                                "section_start": "h2#current", "section_end": "h2#past", "unrecognized_current_links": unrecognized,
                                "pagination_detected": has_more, "_complete": complete,
                                "completeness_reason": "Actual current-section DOM boundaries parsed; historical awards and navigation excluded. Programme labels may explicitly be closed." if complete else "Current-section structure, links or terminal scope incomplete."}


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
    if adapter == "wur_job_detail":
        return _wur_job_detail(url, body)
    if adapter == "eth_job_detail":
        return _eth_job_detail(url, body)
    if adapter == "usf_current_funding":
        return _usf_current_section(url, body)
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

    if adapter in {"eth_listing", "jobbnorge_rss"}:
        return None, None
    return None, None


def enrich_scope(endpoint: dict, scope: dict | None) -> dict | None:
    if scope is None:
        return None
    scope["configured_endpoint_scope"] = endpoint.get("scope")
    scope["adapter_scope"] = endpoint.get("adapter_scope", {})
    return scope
