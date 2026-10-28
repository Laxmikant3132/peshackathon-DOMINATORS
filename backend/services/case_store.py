"""
Case Management & Forensic Evidence Preservation / Chain of Custody

Lightweight, file-backed store providing:
- Case IDs, status, severity, risk score, classification
- Investigation notes (append-only, with analyst + timestamp)
- Related emails & indicators
- Campaign grouping
- Timestamps + analyst/audit information
- Searchable cases
- Evidence identifiers, evidence hashes (SHA-256), action log
- Immutable analysis metadata: every analysis snapshot is hashed; prior hashes
  are chained so any tampering is detectable.

This provides TECHNICAL evidence-preservation support. It does NOT claim any
legal certification or qualified digital-signature status.
"""
import os
import re
import json
import uuid
import hashlib
import threading
from datetime import datetime as dt, timezone
from typing import Dict, Any, List, Optional

from services.privacy import (
    load_config, mask_sensitive_text, minimize_body, content_fingerprint,
    log_audit_event, is_authorized, is_expired,
)

_LOCK = threading.RLock()
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_STORE_PATH = os.path.join(_DATA_DIR, "forensic_cases.json")

VALID_STATUSES = ["open", "in_progress", "escalated", "closed_false_positive", "closed_resolved"]
VALID_SEVERITIES = ["low", "medium", "high", "critical"]

os.makedirs(_DATA_DIR, exist_ok=True)


def _now() -> str:
    return dt.now(timezone.utc).isoformat()


def _sha256(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    return hashlib.sha256(data).hexdigest()


def _load_store() -> List[Dict[str, Any]]:
    with _LOCK:
        if not os.path.exists(_STORE_PATH):
            return []
        try:
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []


def _save_store(cases: List[Dict[str, Any]]) -> None:
    with _LOCK:
        tmp = _STORE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2)
        os.replace(tmp, _STORE_PATH)


def _hash_case_metadata(case: Dict[str, Any]) -> str:
    """Chain-of-custody hash over the case's immutable analysis snapshot."""
    payload = json.dumps({
        "analysis_hash": case.get("analysis_metadata", {}).get("analysis_hash"),
        "case_id": case.get("case_id"),
        "created_at": case.get("created_at"),
        "risk_score": case.get("risk_score"),
        "classification": case.get("classification"),
        "indicators": case.get("analysis_metadata", {}).get("indicators"),
    }, sort_keys=True)
    return _sha256(payload)


def _apply_retention(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Purge cases older than configured retention (returns surviving cases)."""
    kept: List[Dict[str, Any]] = []
    for c in cases:
        if is_expired(c.get("created_at", "")) and c.get("status") != "escalated":
            log_audit_event("retention_purge", {"case_id": c.get("case_id")})
            continue
        kept.append(c)
    return kept


def _derive_severity(analysis: Dict[str, Any]) -> str:
    score = analysis.get("score") or 0
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def create_case(analysis: Dict[str, Any], analyst_id: str = "system",
                severity: Optional[str] = None, campaign_id: Optional[str] = None,
                source: str = "manual") -> Dict[str, Any]:
    """
    Creates an investigation case from a completed analysis result.
    Evidence preservation: SHA-256 of the raw email source and of the analysis
    snapshot; minimized (masked) metadata only — raw bodies are not persisted
    by default per privacy config.
    """
    with _LOCK:
        cases = _apply_retention(_load_store())

        case_id = f"CASE-{dt.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        now = _now()

        diagnostics = analysis.get("diagnostics") or {}
        sender_domain = diagnostics.get("sender_domain")

        # Evidence / chain of custody
        evidence: List[Dict[str, Any]] = []
        raw_eml = analysis.get("source_raw_eml")
        if raw_eml:
            evidence.append({
                "evidence_id": f"EVD-{uuid.uuid4().hex[:12].upper()}",
                "evidence_type": "raw_email_source",
                "sha256": _sha256(raw_eml),
                "collected_at": now,
                "collected_by": analyst_id,
                "note": "SHA-256 of the submitted RFC 5322 source (content itself is not persisted under minimized-storage policy).",
            })
        analysis_snapshot = json.dumps(
            {k: analysis.get(k) for k in ["safety", "score", "indicators", "authentication", "relay_hops",
                                          "urls_forensics", "domain_dns", "attachments_forensics", "risk_factors"]},
            sort_keys=True, default=str)
        analysis_hash = _sha256(analysis_snapshot)

        indicators = analysis.get("indicators") or []
        evidence.append({
            "evidence_id": f"EVD-{uuid.uuid4().hex[:12].upper()}",
            "evidence_type": "analysis_snapshot",
            "sha256": analysis_hash,
            "collected_at": now,
            "collected_by": analyst_id,
            "note": "SHA-256 of immutable analysis result snapshot.",
        })
        for att in (analysis.get("attachments_forensics") or []):
            if att.get("hash"):
                evidence.append({
                    "evidence_id": f"EVD-{uuid.uuid4().hex[:12].upper()}",
                    "evidence_type": "attachment",
                    "sha256": att["hash"],
                    "filename": att.get("filename"),
                    "collected_at": now,
                    "collected_by": analyst_id,
                    "note": "Attachment content hash from MIME analysis (attachment not executed).",
                })

        auto_severity = severity or _derive_severity(analysis)

        case = {
            "case_id": case_id,
            "status": "open",
            "severity": auto_severity,
            "risk_score": analysis.get("score"),
            "classification": analysis.get("safety"),
            "detection_confidence": analysis.get("confidence"),
            "created_at": now,
            "updated_at": now,
            "created_by": analyst_id,
            "source": source,  # manual | gmail_auto_triage
            "source_message_id": analysis.get("source_message_id"),
            "subject_masked": mask_sensitive_text((analysis.get("parsed_metadata") or {}).get("subject") or analysis.get("subject") or ""),
            "sender_masked": mask_sensitive_text((analysis.get("parsed_metadata") or {}).get("from") or ""),
            "body_snippet": minimize_body(analysis.get("parsed_metadata", {}).get("body") or ""),
            "notes": [],
            "related_emails": [analysis.get("source_message_id")] if analysis.get("source_message_id") else [],
            "related_indicators": [
                {"description": f.get("description"), "type": f.get("type"), "confidence": f.get("confidence"), "source": f.get("source")}
                for f in indicators
            ],
            "sender_domains": [sender_domain] if sender_domain else [],
            "ips": diagnostics.get("public_ips_detected", []),
            "urls": [u.get("url") for u in (analysis.get("urls_forensics") or [])],
            "attachment_hashes": [a.get("hash") for a in (analysis.get("attachments_forensics") or []) if a.get("hash")],
            "campaign_id": campaign_id or (f"CAMPAIGN-{sender_domain.upper()}" if sender_domain else None),
            "evidence": evidence,
            "action_log": [{"action": "case_created", "analyst_id": analyst_id, "timestamp": now, "details": {"source": source}}],
            "analysis_metadata": {
                "analysis_hash": analysis_hash,
                "metadata_hash": None,
                "indicators": indicators,
                "collected_at": now,
                "engine_versions": {"forensic_pipeline": "1.1", "case_store": "1.0"},
            },
        }
        case["analysis_metadata"]["metadata_hash"] = _hash_case_metadata(case)
        cases.append(case)
        _save_store(cases)
        log_audit_event("case_created", {"case_id": case_id, "severity": auto_severity, "source": source}, analyst_id)
        return case
def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        for c in _load_store():
            if c.get("case_id") == case_id:
                return _with_integrity_check(c)
    return None


def _with_integrity_check(case: Dict[str, Any]) -> Dict[str, Any]:
    stored = case.get("analysis_metadata", {}).get("metadata_hash")
    recomputed = _hash_case_metadata(case)
    is_valid = bool(stored and stored == recomputed)
    case = dict(case)
    case["integrity"] = {
        "metadata_hash_stored": stored,
        "metadata_hash_recomputed": recomputed,
        "intact": (stored == recomputed) if stored else None,
        "metadata_hash_valid": is_valid,
        "note": "Recomputed hash must match the stored hash; a mismatch indicates post-collection modification.",
    }
    return case


def update_case(case_id: str, analyst_id: str = "system", status: Optional[str] = None,
                severity: Optional[str] = None, note: Optional[str] = None,
                campaign_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _LOCK:
        cases = _load_store()
        for c in cases:
            if c.get("case_id") == case_id:
                now = _now()
                changed = []
                if status:
                    if status not in VALID_STATUSES:
                        return None
                    c["status"] = status
                    changed.append("status")
                if severity:
                    if severity not in VALID_SEVERITIES:
                        return None
                    c["severity"] = severity
                    changed.append("severity")
                if campaign_id:
                    c["campaign_id"] = campaign_id
                    changed.append("campaign_id")
                if note:
                    c["notes"].append({
                        "note_id": f"N-{uuid.uuid4().hex[:8].upper()}",
                        "text": mask_sensitive_text(note),
                        "analyst_id": analyst_id,
                        "timestamp": now,
                    })
                    changed.append("note")
                c["updated_at"] = now
                c["action_log"].append({"action": "case_updated", "analyst_id": analyst_id, "timestamp": now,
                                        "details": {"changed": changed}})
                _save_store(cases)
                log_audit_event("case_updated", {"case_id": case_id, "changed": changed}, analyst_id)
                return _with_integrity_check(c)
    return None


def search_cases(query: Optional[str] = None, status: Optional[str] = None,
                 severity: Optional[str] = None, campaign_id: Optional[str] = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
    with _LOCK:
        cases = _apply_retention(_load_store())
    results = []
    q = (query or "").lower().strip()
    for c in reversed(cases):  # newest first
        if status and c.get("status") != status:
            continue
        if severity and c.get("severity") != severity:
            continue
        if campaign_id and c.get("campaign_id") != campaign_id:
            continue
        if q:
            haystack = " ".join([
                c.get("case_id", ""), c.get("subject_masked", ""), c.get("sender_masked", ""),
                c.get("classification", ""), c.get("campaign_id") or "",
                " ".join(c.get("sender_domains", [])), " ".join(c.get("ips", [])),
                " ".join(c.get("urls", [])),
            ]).lower()
            if q not in haystack:
                continue
        results.append(_with_integrity_check(c))
        if len(results) >= limit:
            break
    return results


def list_prior_incidents(exclude_case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lightweight incident index used by attribution & graph correlation."""
    with _LOCK:
        cases = _apply_retention(_load_store())
    return [
        {
            "case_id": c.get("case_id"),
            "sender_domains": c.get("sender_domains", []),
            "ips": c.get("ips", []),
            "urls": c.get("urls", []),
            "attachment_hashes": c.get("attachment_hashes", []),
            "severity": c.get("severity"),
            "created_at": c.get("created_at"),
            "campaign_id": c.get("campaign_id"),
        }
        for c in cases if c.get("case_id") != exclude_case_id
    ]


def list_campaigns() -> List[Dict[str, Any]]:
    with _LOCK:
        cases = _load_store()
    groups: Dict[str, Dict[str, Any]] = {}
    for c in cases:
        cid = c.get("campaign_id")
        if not cid:
            continue
        g = groups.setdefault(cid, {"campaign_id": cid, "case_count": 0, "case_ids": [],
                                    "severities": set(), "sender_domains": set(), "ips": set(),
                                    "first_seen": c.get("created_at"), "last_seen": c.get("created_at")})
        g["case_count"] += 1
        g["case_ids"].append(c.get("case_id"))
        g["severities"].add(c.get("severity"))
        g["sender_domains"].update(c.get("sender_domains", []))
        g["ips"].update(c.get("ips", []))
        if c.get("created_at") < g["first_seen"]:
            g["first_seen"] = c.get("created_at")
        if c.get("created_at") > g["last_seen"]:
            g["last_seen"] = c.get("created_at")
    out = []
    for g in groups.values():
        g["severities"] = sorted(s for s in g["severities"] if s)
        g["sender_domains"] = sorted(g["sender_domains"])
        g["ips"] = sorted(g["ips"])
        out.append(g)
    return out

