"""
Privacy & Compliance Controls for Email Forensics
- Sensitive-data masking (emails, IPs, UPI, phone numbers, credit cards)
- Configurable retention / controlled access / audit logging
- Minimized storage of email content
No fabricated data: all controls are deterministic and auditable.
"""
import os
import re
import json
import hashlib
from datetime import datetime as dt, timezone, timedelta
from typing import Dict, Any, List, Optional

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "privacy_config.json")
_AUDIT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audit_log.jsonl")

DEFAULT_CONFIG: Dict[str, Any] = {
    "mask_sensitive_data": True,
    "store_raw_email": False,
    "store_body_snippet": True,
    "body_snippet_max_chars": 280,
    "retention_days": 90,
    "authorized_access_required": True,
    "authorized_analysts": [],
    "updated_at": None,
    "updated_by": None,
}


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)


def load_config() -> Dict[str, Any]:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(update: Dict[str, Any], updated_by: str = "system") -> Dict[str, Any]:
    cfg = load_config()
    for k in set(DEFAULT_CONFIG.keys()) - {"updated_at", "updated_by"}:
        if k in update:
            cfg[k] = update[k]
    cfg["updated_at"] = dt.now(timezone.utc).isoformat()
    cfg["updated_by"] = updated_by
    _ensure_dir()
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    log_audit_event("privacy_config_updated", {"updated_by": updated_by, "keys": sorted(update.keys())})
    return cfg


EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE_RE = re.compile(r"\b(?:\+?\d[\d\-\s]{7,13}\d)\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
UPI_RE = re.compile(r"\b[A-Za-z0-9._-]{2,}@(?:ok[a-z]+|ybl|ibl|axl|apl|paytm|upi|airtel)\b")


def mask_email_address(addr: str) -> str:
    if not addr or "@" not in addr:
        return addr
    local, domain = addr.rsplit("@", 1)
    masked_local = ((local[0] if local else "") + "***") if len(local) <= 2 else (local[0] + "***" + local[-1])
    dom_parts = domain.split(".")
    masked_domain = dom_parts[0][0] + "***" + ("." + ".".join(dom_parts[1:]) if len(dom_parts) > 1 else "")
    return f"{masked_local}@{masked_domain}"


def mask_sensitive_text(text: str, enabled: Optional[bool] = None) -> str:
    cfg = load_config()
    if enabled is None:
        enabled = cfg.get("mask_sensitive_data", True)
    if not enabled or not text:
        return text

    def _card(m: re.Match) -> str:
        return "****-****-****-" + re.sub(r"\D", "", m.group(0))[-4:]

    def _phone(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        return "******" + digits[-3:] if len(digits) >= 3 else "***"

    out = CARD_RE.sub(_card, text)
    out = EMAIL_RE.sub(lambda m: mask_email_address(m.group(0)), out)
    out = UPI_RE.sub(lambda m: m.group(0).split("@")[0][:2] + "***@" + m.group(0).split("@")[1], out)
    out = PHONE_RE.sub(_phone, out)
    return out


def minimize_body(body: str) -> Optional[str]:
    """Returns a minimized, masked snippet (or None when minimized storage disables snippets)."""
    cfg = load_config()
    if not cfg.get("store_body_snippet", True) or not body:
        return None
    snippet = body[: int(cfg.get("body_snippet_max_chars", 280))]
    return mask_sensitive_text(snippet)


def content_fingerprint(content: str) -> str:
    """Stable SHA-256 fingerprint enabling duplicate detection without storing content."""
    return hashlib.sha256((content or "").encode("utf-8", errors="replace")).hexdigest()


def is_authorized(analyst_id: Optional[str]) -> bool:
    cfg = load_config()
    if not cfg.get("authorized_access_required", True):
        return True
    allowed = cfg.get("authorized_analysts", [])
    if not allowed:  # open mode explicitly configured (dev / single-analyst deployment)
        return True
    return bool(analyst_id) and analyst_id in allowed


def log_audit_event(action: str, details: Optional[Dict[str, Any]] = None, analyst_id: str = "system") -> None:
    event = {
        "event_id": hashlib.sha256(f"{action}{details}{dt.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
        "action": action,
        "analyst_id": analyst_id,
        "timestamp": dt.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    _ensure_dir()
    with open(_AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def read_audit_log(limit: int = 200) -> List[Dict[str, Any]]:
    if not os.path.exists(_AUDIT_PATH):
        return []
    events: List[Dict[str, Any]] = []
    with open(_AUDIT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    return events[-limit:]


def is_expired(timestamp_iso: str) -> bool:
    cfg = load_config()
    try:
        created = dt.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    except Exception:
        return False
    age = dt.now(timezone.utc) - created
    return age > timedelta(days=int(cfg.get("retention_days", 90)))

