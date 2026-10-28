"""
Identity Correlation & Attribution SUPPORT (never certainty)
Produces infrastructure-level attribution hypotheses with explicit confidence,
indicator flags, and limitations. Never claims to identify a human.
"""
from typing import Dict, Any, List, Optional


def compute_attribution(analysis: Dict[str, Any], prior_incidents: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    auth = analysis.get("authentication") or {}
    geo = analysis.get("geolocation") or {}
    findings = analysis.get("indicators") or []
    descs = [f.get("description", "") if isinstance(f, dict) else "" for f in findings]

    flags: List[Dict[str, Any]] = []

    def flag(category: str, description: str, confidence: float, basis: str) -> None:
        flags.append({"category": category, "description": description, "confidence": confidence, "basis": basis})

    spoofed_domain_indicators = 0
    compromised_account_indicators = 0
    anonymized_infrastructure_indicators = 0
    malicious_infrastructure_indicators = 0

    if auth.get("dmarc") == "FAIL" or auth.get("spf") == "FAIL":
        spoofed_domain_indicators += 1
        flag("spoofed-domain", "Authentication failure consistent with sender-domain spoofing (not proof; forwarding can also cause SPF failures without DMARC fail)", 0.85, "SPF/DMARC results")

    for d in descs:
        dl = d.lower()
        if "reply-to domain mismatch" in dl or "reply-to mailbox divergence" in dl or "reply-to full-address difference" in dl:
            compromised_account_indicators += 1
            flag("compromised-account", "Reply-To diversion suggests either account compromise or deliberate response interception", 0.75, "Header forensics")
        if "lookalike domain" in dl or "display name impersonation" in dl or "typosquatting" in dl:
            spoofed_domain_indicators += 1
            flag("spoofed-domain", d, 0.9, "Domain/display-name analysis")
        if "return-path domain" in dl and "differs" in dl:
            spoofed_domain_indicators += 1
            flag("spoofed-domain", d, 0.7, "Envelope/header mismatch")
    # Threat intel evidence
    for ind in analysis.get("threat_intel", []) or []:
        if ind.get("status") == "Evidence" and isinstance(ind.get("stats"), dict):
            mal = ind["stats"].get("malicious", 0)
            if mal and mal > 0:
                malicious_infrastructure_indicators += 1
                flag("malicious-infrastructure", f"{ind.get('target_type', 'indicator')} flagged malicious by {mal} vendors", 0.95, "VirusTotal")

    # Cross-incident campaign correlation
    prior_matches: List[Dict[str, Any]] = []
    if prior_incidents:
        for inc in prior_incidents:
            shared = []
            if (analysis.get("diagnostics") or {}).get("sender_domain") in (inc.get("sender_domains") or []):
                shared.append("sender domain")
            for ip in (analysis.get("diagnostics") or {}).get("public_ips_detected", []):
                if ip in (inc.get("ips") or []):
                    shared.append(f"IP {ip}")
            if shared:
                prior_matches.append({"case_id": inc.get("case_id"), "shared": shared, "severity": inc.get("severity")})

    # Probable infrastructure attribution (NOT human identification)
    origin_ip = geo.get("ip")
    attribution_target = None
    confidence = 0.0
    basis_parts: List[str] = []
    if origin_ip:
        attribution_target = f"Observed origin infrastructure (IP {origin_ip}, {geo.get('isp') or geo.get('org') or 'ISP unknown'})"
        confidence = float(geo.get("confidence") or 0.5)
        basis_parts.append("earliest public relay IP")
        if geo.get("asn"):
            basis_parts.append(f"ASN {geo.get('asn')}")
    if spoofed_domain_indicators:
        confidence = max(confidence, 0.6)
        basis_parts.append("spoofing indicators")
    if prior_matches:
        confidence = max(confidence, 0.7)
        basis_parts.append(f"{len(prior_matches)} prior incident(s) share infrastructure")

    level = "LOW"
    if confidence >= 0.8:
        level = "HIGH"
    elif confidence >= 0.55:
        level = "MEDIUM"

    return {
        "probable_infrastructure_attribution": attribution_target,
        "attribution_confidence": round(confidence, 2),
        "attribution_confidence_level": level,
        "attribution_basis": basis_parts,
        "compromised_account_indicators": compromised_account_indicators,
        "spoofed_domain_indicators": spoofed_domain_indicators,
        "anonymized_infrastructure_indicators": anonymized_infrastructure_indicators,
        "malicious_infrastructure_indicators": malicious_infrastructure_indicators,
        "flags": flags,
        "sender_domain_relationships": {
            "sender_domain": (analysis.get("diagnostics") or {}).get("sender_domain"),
            "urls": [u.get("url") for u in (analysis.get("urls_forensics") or [])],
            "ips": (analysis.get("diagnostics") or {}).get("public_ips_detected", []),
            "prior_incident_matches": prior_matches,
        },
        "campaign_correlation": prior_matches,
        "limitations": [
            "This is infrastructure-level attribution support only. It does not identify a human being.",
            "IP geolocation indicates network infrastructure position, not a person's physical location or identity.",
            "Spoofing and shared infrastructure are common across unrelated actors; correlation is probabilistic support, not proof.",
        ],
    }
