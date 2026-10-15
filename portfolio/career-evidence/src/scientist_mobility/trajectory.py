"""Versioned event-to-spell consolidation and source-backed moves."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_rules(path: str | Path) -> dict: return json.loads(Path(path).read_text())


def _key(event: dict) -> tuple:
    value = event["start"]["value"]
    parts = str(value or '0').split('.')
    return (value is None, int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, event.get("source_order", 0))


def consolidate_spells(events: list[dict], rules: dict, run_id: str) -> list[dict]:
    tracks: dict[tuple, list[dict]] = {}
    excluded = set(rules["excluded_from_primary_moves"])
    for index, event in enumerate(events):
        if not event.get("evidence_exact") or not event.get("evidence_locator"): raise ValueError("spell input event lacks evidence")
        flags = event["role_flags"]
        kind = "training" if event["event_type"] in {"education", "postdoc"} else "career"
        is_concurrent = bool(flags.get("concurrent") or any(flags.get(k) for k in excluded))
        is_primary = not is_concurrent and bool(flags.get("primary") or kind == "training")
        event = {**event, "source_order": event.get("source_order", index)}
        event["_kind"] = kind; event["_primary"] = is_primary; event["_concurrent"] = is_concurrent
        tracks.setdefault((kind, is_primary, is_concurrent), []).append(event)
    grouped: list[tuple[tuple, list[dict]]] = []
    for (kind, primary, concurrent), items in tracks.items():
        items.sort(key=_key)
        current: list[dict] = []
        for item in items:
            if current and current[-1]["organization_id"] != item["organization_id"]:
                grouped.append(((current[0]["organization_id"], kind, primary, concurrent), current)); current = []
            current.append(item)
        if current: grouped.append(((current[0]["organization_id"], kind, primary, concurrent), current))
    spells = []
    for (org, kind, primary, concurrent), items in grouped:
        items.sort(key=_key); first, last = items[0], items[-1]
        token = f"{first['scientist_id']}|{org}|{kind}|{primary}|{concurrent}|" + '|'.join(x['career_event_id'] for x in items)
        spells.append({"career_spell_id":"spell-"+hashlib.sha256(token.encode()).hexdigest()[:16], "scientist_id":first["scientist_id"], "organization_id":org, "organization_name":first.get("organization_name",first["organization_raw"]), "city":first.get("city"), "country":first.get("country"), "sector":first.get("sector"), "start":first["start"], "end":last["end"], "spell_kind":kind, "is_primary":primary, "is_concurrent":concurrent, "source_event_ids":[x["career_event_id"] for x in items], "source_evidence":[{"event_id":x["career_event_id"],"exact":x["evidence_exact"],"locator":x["evidence_locator"]} for x in items], "derivation_rule_version":rules["version"], "status":"candidate", "created_run_id":run_id, "source_order":min(x["source_order"] for x in items)})
    for spell in spells:
        spell['temporal_order_uncertain'] = any(
            item['start']['value'] is None
            for _, items in grouped for item in items
            if item['career_event_id'] in spell['source_event_ids']
        )
    return sorted(spells, key=lambda s: (s["spell_kind"], _key({"start":s["start"],"source_order":s["source_order"]})))


def derive_moves(spells: list[dict], rules: dict, run_id: str) -> list[dict]:
    moves=[]
    for kind in ("training","career"):
        primary=sorted([s for s in spells if s["spell_kind"]==kind and s["is_primary"] and not s["is_concurrent"]], key=lambda s:_key({"start":s["start"],"source_order":s["source_order"]}))
        # Unknown starts and year-level ties do not establish temporal order.
        # Keep those spells as evidence, but do not guess moves around them.
        if any(s['start']['value'] is None or s.get('temporal_order_uncertain') for s in primary):
            continue
        start_years = [s['start']['value'].split('.')[0] for s in primary]
        if len(set(start_years)) != len(start_years):
            continue
        history=[]
        for before, after in zip(primary,primary[1:]):
            if before["organization_id"]==after["organization_id"]: continue
            if before['start']['value'].split('.')[0] == after['start']['value'].split('.')[0]:
                continue
            if not before["source_evidence"] or not after["source_evidence"]: raise ValueError("move lacks source-backed spells")
            move_kind="return" if after["organization_id"] in history else ("sector_transition" if before.get("sector") and after.get("sector") and before["sector"]!=after["sector"] else "organization")
            token=f"{before['career_spell_id']}|{after['career_spell_id']}|{rules['version']}"
            moves.append({"mobility_move_id":"move-"+hashlib.sha256(token.encode()).hexdigest()[:16],"scientist_id":before["scientist_id"],"from_spell_id":before["career_spell_id"],"to_spell_id":after["career_spell_id"],"move_kind":move_kind,"move_date":after["start"],"source_event_ids":{"from":before["source_event_ids"],"to":after["source_event_ids"]},"derivation_rule_version":rules["version"],"status":"candidate","created_run_id":run_id})
            history.append(before["organization_id"])
    return moves
