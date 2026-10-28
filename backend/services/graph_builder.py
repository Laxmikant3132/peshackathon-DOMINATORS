"""
Data-Driven Correlation Graph Builder (part 1)
Constructs a relationship graph purely from observable analysis results:
nodes are email / sender / domain / IP / mail server / URL / ASN / organization /
campaign / previous incident entities; edges carry labeled, evidence-backed
relationships. Nothing is invented: nodes without data are simply absent.
"""
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import email.utils as eutils


def _node(node_id: str, node_type: str, label: str, **props) -> Dict[str, Any]:
    n = {"id": node_id, "type": node_type, "label": label}
    n.update(props)
    return n


def _edge(source: str, target: str, relation: str, evidence: str, confidence: float = 0.9) -> Dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, "evidence": evidence, "confidence": confidence}


def build_correlation_graph(analysis: Dict[str, Any], prior_incidents: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_nodes = set()
    seen_edges = set()

    def add_node(node: Dict[str, Any]):
        if node["id"] not in seen_nodes:
            seen_nodes.add(node["id"])
            nodes.append(node)

    def add_edge(edge: Dict[str, Any]):
        key = (edge["source"], edge["target"], edge["relation"])
        rev = (edge["target"], edge["source"], edge["relation"])
        if key not in seen_edges and rev not in seen_edges:
            seen_edges.add(key)
            edges.append(edge)

    email_node = "email:current"
    add_node(_node(email_node, "email", analysis.get("subject") or "(current email)",
                   risk=analysis.get("score"), classification=analysis.get("safety")))
    # ---- Sender identity (observable From header) ----
    sender_raw = (analysis.get("parsed_metadata") or {}).get("from", "")
    if not sender_raw:
        for ind in analysis.get("indicators", []):
            d = ind.get("description", "") if isinstance(ind, dict) else ""
            if "Reply-To mismatch detected: From is" in d:
                sender_raw = d.split("From is '")[-1].split("'")[0]
                break

    sender_node = None
    sender_domain = None
    name, addr = eutils.parseaddr(sender_raw)
    if addr and "@" in addr:
        sender_node = f"sender:{addr.lower()}"
        sender_domain = addr.split("@")[-1].lower()
        add_node(_node(sender_node, "sender", addr.lower(), display_name=name or None))
        add_edge(_edge(email_node, sender_node, "sent_by", "From header", 1.0))

    # ---- Sender domain ----
    if sender_domain:
        dom_node = f"domain:{sender_domain}"
        add_node(_node(dom_node, "domain", sender_domain))
        add_edge(_edge(sender_node, dom_node, "belongs_to", "RFC 5322 address domain", 1.0))

        dns = analysis.get("domain_dns") or {}
        if dns.get("status") == "AVAILABLE":
            for ip in dns.get("resolved_ips", [])[:4]:
                ip_node = f"ip:{ip}"
                add_node(_node(ip_node, "ip", ip))
                add_edge(_edge(dom_node, ip_node, "resolves_to", "DNS A/AAAA record", 1.0))
            for mx in dns.get("mx_hosts", [])[:4]:
                host = mx.split()[-1].strip(".")
                if host:
                    mx_node = f"mailserver:{host}"
                    add_node(_node(mx_node, "mail_server", host))
                    add_edge(_edge(dom_node, mx_node, "mail_exchanger", "DNS MX record", 1.0))
        if dns.get("status") == "UNAVAILABLE":
            add_node(_node("unavailable:dns", "unavailable", "DNS Intelligence Unavailable"))

        whois = analysis.get("domain_whois") or {}
        if whois.get("status") == "AVAILABLE":
            registrar = whois.get("registrar")
            if registrar:
                reg_node = f"org:{registrar.lower()}"
                add_node(_node(reg_node, "organization", registrar))
                add_edge(_edge(dom_node, reg_node, "registered_with", "RDAP registrar record", 1.0))
            for ns in whois.get("nameservers", [])[:4]:
                ns_node = f"nameserver:{ns.lower()}"
                add_node(_node(ns_node, "nameserver", ns.lower()))
                add_edge(_edge(dom_node, ns_node, "delegated_to", "RDAP nameserver record", 1.0))
    # ---- Relay path: IPs, mail servers, ASN / org from geolocation ----
    geo = analysis.get("geolocation") or {}
    for hop in (analysis.get("relay_hops") or []):
        ip = hop.get("from_ip")
        by_host = hop.get("by_host") or ""
        is_origin = bool(hop.get("is_origin_candidate"))
        if ip:
            ip_node = f"ip:{ip}"
            add_node(_node(ip_node, "ip", ip,
                           is_public=hop.get("is_public"),
                           origin_candidate=is_origin,
                           position=hop.get("position")))
            if by_host:
                host_node = f"mailserver:{by_host.lower()}"
                add_node(_node(host_node, "mail_server", by_host.lower()))
                add_edge(_edge(ip_node, host_node, "connected_via", "Received header relay", 0.95))
            add_edge(_edge(ip_node, email_node, "relayed", f"Received hop #{hop.get('position')}", 0.95))

        if is_origin and geo.get("provider_state") == "AVAILABLE" and geo.get("ip") == ip:
            asn = geo.get("asn")
            org = geo.get("org") or geo.get("isp")
            if asn:
                asn_node = f"asn:{asn}"
                add_node(_node(asn_node, "asn", asn, isp=geo.get("isp")))
                add_edge(_edge(ip_node, asn_node, "announced_by", "Geolocation provider ASN data", 0.9))
            if org:
                org_node = f"org:{org.lower()}"
                add_node(_node(org_node, "organization", org))
                add_edge(_edge(asn_node if asn else ip_node, org_node, "operated_by", "Geo/ASN organization data", 0.85))

    # ---- URLs ----
    for u in (analysis.get("urls_forensics") or []):
        url = u.get("url")
        if not url:
            continue
        url_node = f"url:{url}"
        add_node(_node(url_node, "url", url, classification=u.get("classification")))
        add_edge(_edge(email_node, url_node, "contains_link", "Extracted from message body", 1.0))
        host = u.get("hostname") or (urlparse(url).hostname or "")
        if host:
            host_node = f"domain:{host.lower()}"
            add_node(_node(host_node, "domain", host.lower()))
            add_edge(_edge(url_node, host_node, "hosted_on", "URL hostname", 1.0))

    # ---- Attachments ----
    for a in (analysis.get("attachments_forensics") or []):
        fn = a.get("filename")
        if fn:
            att_node = f"attachment:{fn}"
            add_node(_node(att_node, "attachment", fn, hash=a.get("hash")))
            add_edge(_edge(email_node, att_node, "carries_attachment", "MIME part", 1.0))

    # ---- Campaign nodes (session-level) ----
    for c in (analysis.get("campaign_correlations") or []):
        target = c.get("target")
        if not target:
            continue
        camp_node = f"campaign:{target}"
        add_node(_node(camp_node, "campaign", target, relation=c.get("relation")))
        ctype = (c.get("type") or "").lower()
        tnode = f"ip:{target}" if "ip" in ctype else f"domain:{target}"
        if tnode in seen_nodes:
            add_edge(_edge(tnode, camp_node, "grouped_in", c.get("relation") or "Shared infrastructure", 0.8))

    # ---- Previous incidents: only real indicator matches create edges ----
    if prior_incidents:
        for inc in prior_incidents:
            matches: List[str] = []
            if sender_domain and sender_domain in (inc.get("sender_domains") or []):
                matches.append(f"sender domain {sender_domain}")
            for ip in (analysis.get("diagnostics") or {}).get("public_ips_detected", []):
                if ip in (inc.get("ips") or []):
                    matches.append(f"relay IP {ip}")
            for u in (analysis.get("urls_forensics") or []):
                if u.get("url") in (inc.get("urls") or []):
                    matches.append("shared URL")
            for att in (analysis.get("attachments_forensics") or []):
                if att.get("hash") and att["hash"] in (inc.get("attachment_hashes") or []):
                    matches.append("identical attachment hash")
            if matches:
                inc_node = f"incident:{inc.get('case_id')}"
                add_node(_node(inc_node, "previous_incident", inc.get("case_id"),
                               severity=inc.get("severity"), created_at=inc.get("created_at")))
                add_edge(_edge(email_node, inc_node, "correlated_with",
                               "Shared indicators: " + ", ".join(sorted(set(matches))), 0.9))

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": sorted({n["type"] for n in nodes}),
            "data_driven": True,
        },
    }
