"""
RDAP / WHOIS Domain Registration Intelligence
Uses the public, keyless RDAP bootstrap service (rdap.org), which redirects to the
authoritative registry RDAP server for gTLDs. This is a public service — no API key
required — but network availability is provider-dependent and always surfaced honestly.
Never fabricates data: all failure modes return status UNAVAILABLE with a reason.
"""
import os
import re
import requests
from typing import Dict, Any, Optional
from datetime import datetime as dt, timezone

RDAP_BOOTSTRAP_URL = os.getenv("RDAP_BOOTSTRAP_URL", "https://rdap.org/domain/{domain}")
RDAP_TIMEOUT = float(os.getenv("RDAP_TIMEOUT", "5"))


def _first(events: list, event_type: str) -> Optional[Dict[str, Any]]:
    for e in events or []:
        if e.get("eventAction", "").lower() == event_type:
            return e
    return None


def _parse_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    # RDAP dates like 1997-09-15T04:00:00Z or 2021-05-03T15:45:00.000Z
    cleaned = re.sub(r"\.\d+Z$", "Z", raw)
    try:
        return dt.fromisoformat(cleaned.replace("Z", "+00:00")).isoformat()
    except Exception:
        return raw


def query_domain_rdap(domain: str) -> Dict[str, Any]:
    """
    Queries public RDAP for domain registration intelligence.
    Returns status AVAILABLE / UNAVAILABLE with explicit reason — never mock data.
    """
    if not domain or "." not in domain or domain in ["localhost", "invalid"]:
        return {"status": "UNAVAILABLE", "provider_state": "CONFIGURED", "query_state": "NOT_RUN", "result_state": "UNAVAILABLE", "domain": domain, "reason": "No valid registrable domain", "source": "RDAP (rdap.org)"}

    url = RDAP_BOOTSTRAP_URL.format(domain=domain)
    try:
        resp = requests.get(url, timeout=RDAP_TIMEOUT, headers={"Accept": "application/rdap+json"})
    except Exception as e:
        return {
            "status": "UNAVAILABLE",
            "provider_state": "CONFIGURED",
            "query_state": "FAILED",
            "result_state": "UNAVAILABLE",
            "domain": domain,
            "reason": f"RDAP service unreachable: {e}",
            "source": "RDAP (rdap.org)",
        }

    if resp.status_code == 404:
        return {"status": "UNAVAILABLE", "provider_state": "CONFIGURED", "query_state": "FAILED", "result_state": "UNAVAILABLE", "domain": domain, "reason": "Domain not found in registry RDAP (possibly non-gTLD or unregistered)", "source": "RDAP (rdap.org)"}
    if resp.status_code == 429:
        return {"status": "UNAVAILABLE", "provider_state": "CONFIGURED", "query_state": "FAILED", "result_state": "UNAVAILABLE", "domain": domain, "reason": "RDAP rate limit exceeded (HTTP 429)", "source": "RDAP (rdap.org)"}
    if resp.status_code != 200:
        return {"status": "UNAVAILABLE", "provider_state": "CONFIGURED", "query_state": "FAILED", "result_state": "UNAVAILABLE", "domain": domain, "reason": f"RDAP provider returned HTTP {resp.status_code}", "source": "RDAP (rdap.org)"}

    try:
        data = resp.json()
    except Exception as e:
        return {"status": "UNAVAILABLE", "provider_state": "CONFIGURED", "query_state": "FAILED", "result_state": "UNAVAILABLE", "domain": domain, "reason": f"RDAP response not valid JSON: {e}", "source": "RDAP (rdap.org)"}

    events = data.get("events", [])
    registration = _first(events, "registration")
    expiration = _first(events, "expiration")
    last_changed = _first(events, "last changed")

    registrar = None
    registrar_url = None
    for ent in data.get("entities", []):
        roles = ent.get("roles", [])
        if "registrar" in roles:
            vcard = ent.get("vcardArray")
            if vcard and len(vcard) > 1:
                for item in vcard[1]:
                    if item and item[0] == "fn":
                        registrar = item[3]
            if not registrar:
                registrar = ent.get("handle")
            for link in ent.get("links", []) or []:
                if link.get("href"):
                    registrar_url = link["href"]
            break

    nameservers = [ns.get("ldhName", "").lower().strip(".") for ns in data.get("nameservers", []) if ns.get("ldhName")]

    return {
        "status": "AVAILABLE",
        "provider_state": "CONFIGURED",
        "query_state": "SUCCESS",
        "result_state": "AVAILABLE",
        "domain": domain,
        "registrar": registrar,
        "registrar_url": registrar_url,
        "registration_date": _parse_date((registration or {}).get("eventDate")),
        "expiration_date": _parse_date((expiration or {}).get("eventDate")),
        "last_changed_date": _parse_date((last_changed or {}).get("eventDate")),
        "nameservers": nameservers,
        "registry_handle": data.get("handle"),
        "domain_status": data.get("status"),
        "source": "RDAP (rdap.org)",
        "lookup_time": dt.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "limitations": "RDAP coverage is limited to participating registries (primarily gTLDs). Country-code registries and privacy-proxied contacts may not expose full WHOIS data.",
    }
