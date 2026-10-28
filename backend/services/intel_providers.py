import os
import ipaddress
import re
from datetime import datetime as dt
from typing import Dict, Any, Tuple, Optional, List
import requests

class IntelProvider:
    pass

def classify_ip_address(ip_str: str) -> Dict[str, Any]:
    """
    Standards-aware IP classifier used by origin tracing, geolocation gating,
    diagnostics, and tests. Documentation/test-network addresses are deliberately
    separate from RFC1918/private so they are never described as internal origin
    evidence.
    """
    raw = (ip_str or "").strip().strip("[]")
    if raw.lower().startswith("ipv6:"):
        raw = raw[5:]
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        return {
            "ip": ip_str,
            "valid": False,
            "version": None,
            "category": "invalid",
            "label": "Invalid IP address",
            "is_publicly_routable": False,
            "usable_origin_evidence": False,
            "reason": "Malformed or non-IP candidate rejected by ipaddress parser",
        }

    category = "global_public"
    label = "Global/Public Routable"
    reason = "Address is globally routable and may be used as observable infrastructure evidence."

    if isinstance(ip, ipaddress.IPv4Address):
        networks = [
            ("10.0.0.0/8", "rfc1918_private", "Internal / RFC1918 Private"),
            ("172.16.0.0/12", "rfc1918_private", "Internal / RFC1918 Private"),
            ("192.168.0.0/16", "rfc1918_private", "Internal / RFC1918 Private"),
            ("192.0.2.0/24", "documentation_test_net", "Documentation / TEST-NET-1"),
            ("198.51.100.0/24", "documentation_test_net", "Documentation / TEST-NET-2"),
            ("203.0.113.0/24", "documentation_test_net", "Documentation / TEST-NET-3"),
            ("127.0.0.0/8", "loopback", "Loopback"),
            ("169.254.0.0/16", "link_local", "Link-local"),
            ("224.0.0.0/4", "multicast", "Multicast"),
            ("100.64.0.0/10", "carrier_grade_nat", "Carrier-grade NAT / Shared Address Space"),
            ("198.18.0.0/15", "benchmark_test", "Benchmark Testing / Non-routable"),
            ("0.0.0.0/8", "reserved", "Reserved / This Network"),
            ("240.0.0.0/4", "reserved", "Reserved / Future Use"),
            ("255.255.255.255/32", "reserved", "Limited Broadcast"),
        ]
        for cidr, cat, lab in networks:
            if ip in ipaddress.ip_network(cidr):
                category, label = cat, lab
                break
    else:
        networks = [
            ("::1/128", "loopback", "IPv6 Loopback"),
            ("fe80::/10", "link_local", "IPv6 Link-local"),
            ("fc00::/7", "ipv6_ula", "IPv6 Unique Local Address (ULA)"),
            ("ff00::/8", "multicast", "IPv6 Multicast"),
            ("2001:db8::/32", "documentation_test_net", "IPv6 Documentation / Reserved"),
            ("::/128", "reserved", "IPv6 Unspecified / Reserved"),
        ]
        for cidr, cat, lab in networks:
            if ip in ipaddress.ip_network(cidr):
                category, label = cat, lab
                break
        if category == "global_public" and (ip.is_reserved or not ip.is_global):
            category, label = "reserved", "IPv6 Reserved / Non-routable"

    if category != "global_public":
        if category == "documentation_test_net":
            reason = "Documentation/test-network address; cannot be used as real-world origin evidence."
        elif category in {"rfc1918_private", "ipv6_ula"}:
            reason = "Private/internal address; useful for internal routing context only, not public origin attribution."
        else:
            reason = "Non-routable/special-use address; rejected as reliable public origin evidence."

    return {
        "ip": str(ip),
        "valid": True,
        "version": ip.version,
        "category": category,
        "label": label,
        "is_publicly_routable": category == "global_public" and ip.is_global,
        "usable_origin_evidence": category == "global_public" and ip.is_global,
        "reason": reason,
    }

def is_publicly_routable_ip(ip_str: str) -> bool:
    """
    Checks if an IP address string is a valid, publicly routable IPv4 or IPv6 address.
    Filters out:
    - private IP addresses
    - loopback addresses
    - reserved / multicast / unspecified / link-local addresses
    - documentation addresses (e.g. 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32)
    - invalid strings
    """
    return classify_ip_address(ip_str).get("is_publicly_routable", False)

def extract_all_ips_from_received(received_headers: List[str]) -> List[str]:
    """
    Extracts all IPv4 and IPv6 addresses from a list of Received header strings.
    Maintains observed order.
    """
    found: List[str] = []
    # Regex matching IPv4 and IPv6
    ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    # IPv6 in brackets [2001:...] or standalone
    ipv6_pattern = re.compile(r'(?:\[([0-9a-fA-F:.]+)\]|\b([0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){2,7})\b)')

    for header in received_headers:
        # IPv4
        for ip in ipv4_pattern.findall(header):
            if ip not in found:
                found.append(ip)
        # IPv6
        for match in ipv6_pattern.findall(header):
            ip = match[0] or match[1]
            if ip and ip not in found:
                try:
                    # Validate format
                    ipaddress.IPv6Address(ip)
                    found.append(ip)
                except ValueError:
                    pass
    return found

def identify_earliest_public_ip(received_headers: List[str]) -> Optional[str]:
    """
    Identifies the earliest reliable publicly routable IP from the observable Received chain.
    Standard email Received headers are prepended by each MTA, so the oldest/earliest hop
    is typically at the bottom of the list (or last in chronologically ordered headers).
    We search from the earliest hop (reverse order) to find the first publicly routable IP.
    """
    # Reverse to examine the earliest origin hops first
    for header in reversed(received_headers):
        ips = extract_all_ips_from_received([header])
        for ip in ips:
            if is_publicly_routable_ip(ip):
                return ip
    return None

class IPGeolocationProvider(IntelProvider):
    @staticmethod
    def get_geolocation(ip: str) -> Dict[str, Any]:
        """
        Queries IP intelligence / geolocation provider (IPinfo.io).
        Returns a structured dictionary adhering strictly to the required contract:
        - provider_state: "AVAILABLE" | "UNAVAILABLE" | "UNKNOWN"
        - Never fabricates missing data.
        """
        try:
            from datetime import timezone
            lookup_time = dt.now(timezone.utc).isoformat()
        except Exception:
            lookup_time = dt.utcnow().isoformat() + "Z"
        token = os.getenv("IPINFO_TOKEN") or os.getenv("IPINFO_API_KEY")

        if not is_publicly_routable_ip(ip):
            ip_class = classify_ip_address(ip)
            return {
                "provider_state": "UNKNOWN",
                "provider": "IPinfo",
                "provider_config": "CONFIGURED" if token else "NOT CONFIGURED",
                "query_state": "NOT_RUN",
                "result_state": "UNAVAILABLE",
                "ip": ip,
                "ip_classification": ip_class,
                "error": ip_class.get("reason") or "IP is not publicly routable",
                "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual.",
                "source": "Local IP Validator",
                "lookup_time": lookup_time
            }

        if not token:
            return {
                "provider_state": "UNAVAILABLE",
                "provider": "IPinfo",
                "provider_config": "NOT CONFIGURED",
                "query_state": "NOT_RUN",
                "result_state": "UNAVAILABLE",
                "ip": ip,
                "error": "IP Geolocation Provider not configured (IPINFO_TOKEN missing)",
                "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual.",
                "source": "IPinfo",
                "lookup_time": lookup_time
            }

        url = f"https://ipinfo.io/{ip}?token={token}"
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                
                # Parse location coordinates if present
                loc = data.get("loc", "")
                lat, lon = None, None
                if loc and "," in loc:
                    try:
                        parts = loc.split(",")
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                    except ValueError:
                        pass

                # Parse ASN / Org
                org = data.get("org", "")
                asn = None
                isp = org
                if org and org.startswith("AS"):
                    tokens = org.split(" ", 1)
                    asn = tokens[0]
                    isp = tokens[1] if len(tokens) > 1 else org

                # Privacy / Anonymization Detection
                privacy = data.get("privacy", {})
                is_vpn = privacy.get("vpn")
                is_proxy = privacy.get("proxy")
                is_tor = privacy.get("tor")
                is_relay = privacy.get("relay")
                is_hosting = privacy.get("hosting")

                # Determine infrastructure type & caution notice
                infrastructure_types: List[str] = []
                if is_tor:
                    infrastructure_types.append("Tor Exit Node")
                if is_vpn:
                    infrastructure_types.append("VPN")
                if is_proxy:
                    infrastructure_types.append("Proxy")
                if is_relay:
                    infrastructure_types.append("Mail Relay / CDN")
                if is_hosting:
                    infrastructure_types.append("Cloud Hosting / Datacenter")
                if not infrastructure_types:
                    infrastructure_types.append("Unknown")

                infrastructure_type_str = ", ".join(infrastructure_types)

                is_anonymized = is_vpn or is_proxy or is_tor or is_hosting or is_relay
                anonymization_status = "Anonymized / Proxy / Hosting" if is_anonymized else "Unknown (no positive provider indicators)"
                
                infrastructure_notice = (
                    "Notice: This IP belongs to a VPN, proxy, Tor exit node, cloud host, CDN, or mail relay. "
                    "This result represents intermediary infrastructure and does not represent the sender's physical location."
                    if is_anonymized else
                    "Estimated location reflects network routing infrastructure and may differ from the sender's device location."
                )

                return {
                    "provider_state": "AVAILABLE",
                    "provider": "IPinfo",
                    "provider_config": "CONFIGURED",
                    "query_state": "SUCCESS",
                    "result_state": "AVAILABLE",
                    "ip": ip,
                    "country": data.get("country"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "latitude": lat,
                    "longitude": lon,
                    "timezone": data.get("timezone"),
                    "asn": asn,
                    "isp": isp,
                    "org": org,
                    "network_type": data.get("company", {}).get("type") or ("Hosting" if is_hosting else None),
                    "infrastructure_type": infrastructure_type_str,
                    "privacy_status": anonymization_status,
                    "is_hosting": is_hosting,
                    "is_vpn": is_vpn,
                    "is_proxy": is_proxy,
                    "is_tor": is_tor,
                    "is_relay": is_relay,
                    "confidence": None,
                    "source": "IPinfo",
                    "lookup_time": lookup_time,
                    "infrastructure_notice": infrastructure_notice,
                    "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
                }
            elif resp.status_code == 429:
                return {
                    "provider_state": "UNAVAILABLE",
                    "provider": "IPinfo",
                    "provider_config": "CONFIGURED",
                    "query_state": "FAILED",
                    "result_state": "UNAVAILABLE",
                    "ip": ip,
                    "error": "IP Geolocation Provider rate limited (HTTP 429)",
                    "source": "IPinfo",
                    "lookup_time": lookup_time,
                    "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
                }
            else:
                return {
                    "provider_state": "UNAVAILABLE",
                    "provider": "IPinfo",
                    "provider_config": "CONFIGURED",
                    "query_state": "FAILED",
                    "result_state": "UNAVAILABLE",
                    "ip": ip,
                    "error": f"Provider returned HTTP {resp.status_code}",
                    "source": "IPinfo",
                    "lookup_time": lookup_time,
                    "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
                }
        except requests.exceptions.Timeout:
            return {
                "provider_state": "UNAVAILABLE",
                "provider": "IPinfo",
                "provider_config": "CONFIGURED",
                "query_state": "FAILED",
                "result_state": "UNAVAILABLE",
                "ip": ip,
                "error": "IP Geolocation Provider request timed out (3s limit exceeded)",
                "source": "IPinfo",
                "lookup_time": lookup_time,
                "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
            }
        except Exception as e:
            return {
                "provider_state": "UNAVAILABLE",
                "provider": "IPinfo",
                "provider_config": "CONFIGURED",
                "query_state": "FAILED",
                "result_state": "UNAVAILABLE",
                "ip": ip,
                "error": "Provider query failed",
                "source": "IPinfo",
                "lookup_time": lookup_time,
                "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
            }

class ThreatIntelligenceProvider(IntelProvider):
    @staticmethod
    def _vt_result(status: str, stats: Dict[str, Any], configured: bool, query_state: str, reason: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        payload = dict(stats or {})
        payload.update({
            "provider": "VirusTotal",
            "provider_state": "CONFIGURED" if configured else "NOT CONFIGURED",
            "query_state": query_state,
            "result_state": "AVAILABLE" if status == "Evidence" else "UNAVAILABLE",
        })
        if reason:
            payload["error"] = reason
        return status, payload

    @staticmethod
    def check_hash(file_hash: str) -> Tuple[str, Dict[str, Any]]:
        api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not api_key:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, False, "NOT_RUN", "Threat Intelligence Provider not configured")
        
        headers = {"x-apikey": api_key}
        try:
            resp = requests.get(f"https://www.virustotal.com/api/v3/files/{file_hash}", headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                return ThreatIntelligenceProvider._vt_result("Evidence", stats, True, "SUCCESS")
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider returned HTTP {resp.status_code}")
        except Exception as e:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider exception: {str(e)}")

    @staticmethod
    def check_ip(ip: str) -> Tuple[str, Dict[str, Any]]:
        api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not api_key:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, False, "NOT_RUN", "Threat Intelligence Provider not configured")
        
        headers = {"x-apikey": api_key}
        try:
            resp = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}", headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                return ThreatIntelligenceProvider._vt_result("Evidence", stats, True, "SUCCESS")
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider returned HTTP {resp.status_code}")
        except Exception as e:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider exception: {str(e)}")

class DomainReputationProvider(IntelProvider):
    @staticmethod
    def check_domain(domain: str) -> Tuple[str, Dict[str, Any]]:
        api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not api_key:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, False, "NOT_RUN", "Domain Reputation Provider not configured")
        
        headers = {"x-apikey": api_key}
        try:
            resp = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}", headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                return ThreatIntelligenceProvider._vt_result("Evidence", stats, True, "SUCCESS")
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider returned HTTP {resp.status_code}")
        except Exception as e:
            return ThreatIntelligenceProvider._vt_result("Unavailable", {}, True, "FAILED", f"Provider exception: {str(e)}")

def get_providers_health() -> Dict[str, Dict[str, Any]]:
    """
    Returns diagnostic health status for all external intelligence providers.
    Never exposes API keys.
    Status values: CONFIGURED | NOT CONFIGURED | AVAILABLE | FAILED
    """
    ipinfo_token = os.getenv("IPINFO_TOKEN") or os.getenv("IPINFO_API_KEY")
    vt_key = os.getenv("VIRUSTOTAL_API_KEY")

    health: Dict[str, Dict[str, Any]] = {
        "IPINFO": {
            "status": "CONFIGURED" if ipinfo_token else "NOT CONFIGURED",
            "reason": None if ipinfo_token else "IPINFO_TOKEN is not set in backend environment",
            "capabilities": ["IP Geolocation", "ASN Lookup", "Hosting / Proxy / VPN Detection"]
        },
        "VirusTotal": {
            "status": "CONFIGURED" if vt_key else "NOT CONFIGURED",
            "reason": None if vt_key else "VIRUSTOTAL_API_KEY is not set in backend environment",
            "capabilities": ["File Hash Intel", "Domain Reputation", "IP Threat Analysis"]
        },
        "DNS": {
            "status": "CONFIGURED",
            "reason": None,
            "capabilities": ["A / AAAA", "MX Exchangers", "SPF TXT", "DMARC TXT"]
        },
        "RDAP": {
            "status": "CONFIGURED",
            "reason": None,
            "capabilities": ["Domain Registration via public RDAP (rdap.org)", "Registrar", "Creation / Expiration Dates", "Nameservers"],
            "provider_dependent": True,
            "note": "Public keyless service; availability depends on registry RDAP coverage (primarily gTLDs) and network access. Failures are reported as Unavailable per domain."
        }
    }
    return health
