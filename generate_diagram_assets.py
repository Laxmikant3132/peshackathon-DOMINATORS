import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('generated_assets', exist_ok=True)

# -------------------------------------------------------------
# 1. Flowchart Architecture Diagram for Slide 3
# -------------------------------------------------------------
def generate_flowchart_architecture():
    fig, ax = plt.subplots(figsize=(12, 3.4), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.4)
    ax.axis('off')

    # Stages definition
    stages = [
        {
            "num": "01",
            "title": "TELEMETRY INGESTION",
            "bg": "#EBF3FC",
            "border": "#1A56A0",
            "hdr_bg": "#1A56A0",
            "items": [
                "• Gmail API (2s Poller)",
                "• Raw EML RFC 5322",
                "• YouTube v3 Comments",
                "• Browser MV3 Hooks",
                "• UPI VPA / QR Inputs"
            ],
            "x": 0.2
        },
        {
            "num": "02",
            "title": "AI THREAT TRIAGE",
            "bg": "#E6F4F1",
            "border": "#00838F",
            "hdr_bg": "#00838F",
            "items": [
                "• SPF/DKIM/DMARC Audit",
                "• Return-Path Spoof Check",
                "• NLP Urgency & Lure Score",
                "• Levenshtein Typo Engine",
                "• Attachment SHA-256 Hash"
            ],
            "x": 3.2
        },
        {
            "num": "03",
            "title": "GEOLOCATION & GRAPH",
            "bg": "#F3EBF6",
            "border": "#78328C",
            "hdr_bg": "#78328C",
            "items": [
                "• Hop-by-Hop Received Trace",
                "• IPinfo ASN & Geo-Coords",
                "• Tor / VPN / Relay Detect",
                "• Threat Correlation Graph",
                "• Offender Attribution"
            ],
            "x": 6.2
        },
        {
            "num": "04",
            "title": "ACTION & FORENSICS",
            "bg": "#EAF5EA",
            "border": "#166534",
            "hdr_bg": "#166534",
            "items": [
                "• Instant Inbox Quarantine",
                "• MV3 URL Warning Modal",
                "• IT Act Sec 65B Dossier",
                "• CERT-In Threat Feed",
                "• Adaptive Phishing Drill"
            ],
            "x": 9.2
        }
    ]

    card_w = 2.6
    card_h = 3.0

    for s in stages:
        x = s["x"]
        y = 0.2
        # Card body
        rect = patches.FancyBboxPatch((x, y), card_w, card_h,
                                      boxstyle="round,pad=0.04,rounding_size=0.15",
                                      facecolor=s["bg"], edgecolor=s["border"], linewidth=1.5)
        ax.add_patch(rect)

        # Header banner
        hdr = patches.FancyBboxPatch((x, y + card_h - 0.55), card_w, 0.55,
                                     boxstyle="round,pad=0.02,rounding_size=0.1",
                                     facecolor=s["hdr_bg"], edgecolor="none")
        ax.add_patch(hdr)

        # Header text
        ax.text(x + 0.12, y + card_h - 0.28, f"STAGE {s['num']}", color="#A0D2FF", fontsize=7.5, fontweight='bold')
        ax.text(x + 0.12, y + card_h - 0.44, s["title"], color="white", fontsize=8.5, fontweight='bold')

        # Items
        item_y = y + card_h - 0.82
        for item in s["items"]:
            ax.text(x + 0.14, item_y, item, color="#1E293B", fontsize=7.2, fontweight='bold' if "•" in item else 'normal')
            item_y -= 0.42

        # Connecting arrow
        if s["num"] != "04":
            arr_x = x + card_w + 0.05
            arr_y = y + card_h / 2
            ax.annotate("", xy=(arr_x + 0.30, arr_y), xytext=(arr_x, arr_y),
                        arrowprops=dict(arrowstyle="->", color="#1A56A0", lw=2.5, mutation_scale=15))

    plt.tight_layout()
    out_path = "generated_assets/flowchart_architecture.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#F8FAFC')
    plt.close()
    print("Generated:", out_path)

# -------------------------------------------------------------
# 2. GeoLocation & Threat Attribution Visual for Slide 2 / 4
# -------------------------------------------------------------
def generate_geolocation_visual():
    fig, ax = plt.subplots(figsize=(5.6, 3.8), dpi=300)
    fig.patch.set_facecolor('#0B192C')
    ax.set_facecolor('#0B192C')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title Banner
    ax.text(0.5, 9.3, "🌐 HOP-BY-HOP IP GEOLOCATION FORENSICS", color="#38BDF8", fontsize=10, fontweight='bold')
    ax.text(0.5, 8.7, "RFC 5322 Received Header Hop Traversal & Infrastructure Triage", color="#94A3B8", fontsize=7.5)

    # Hop chain nodes
    hops = [
        {"name": "Hop 1: Origin Client", "ip": "185.220.101.5", "type": "Tor Exit Relay", "loc": "Frankfurt, DE", "col": "#EF4444", "asn": "AS200052"},
        {"name": "Hop 2: Open Relay", "ip": "194.26.29.112", "type": "Hosting Datacenter", "loc": "Amsterdam, NL", "col": "#F59E0B", "asn": "AS49981"},
        {"name": "Hop 3: Border Gateway", "ip": "209.85.216.174", "type": "Google Mail Edge", "loc": "Mountain View, US", "col": "#10B981", "asn": "AS15169"},
        {"name": "Destination: Target", "ip": "10.0.4.12", "type": "Recipient Inbox", "loc": "New Delhi, IN", "col": "#38BDF8", "asn": "Internal"}
    ]

    y = 7.6
    for i, h in enumerate(hops):
        # Card
        rect = patches.FancyBboxPatch((0.5, y - 1.2), 9.0, 1.2,
                                      boxstyle="round,pad=0.02,rounding_size=0.1",
                                      facecolor="#1E293B", edgecolor=h["col"], linewidth=1.2)
        ax.add_patch(rect)

        # Node Badge
        badge = patches.FancyBboxPatch((0.7, y - 0.45), 2.2, 0.35,
                                       boxstyle="round,pad=0.02,rounding_size=0.08",
                                       facecolor=h["col"], edgecolor="none")
        ax.add_patch(badge)
        ax.text(0.8, y - 0.33, h["name"], color="white" if h["col"] != "#F59E0B" else "#0B192C", fontsize=6.8, fontweight='bold')

        # Details
        ax.text(3.1, y - 0.32, f"IP: {h['ip']}  |  ASN: {h['asn']}", color="#F1F5F9", fontsize=7.5, fontweight='bold')
        ax.text(3.1, y - 0.72, f"Classification: {h['type']}  •  Location: {h['loc']}", color="#94A3B8", fontsize=7.0)

        # Status flag
        if "Tor" in h["type"] or "Hosting" in h["type"]:
            status_txt = "⚠️ HIGH ANONYMIZATION DETECTED" if "Tor" in h["type"] else "⚠️ BULK CLOUD INFRASTRUCTURE"
            ax.text(3.1, y - 1.05, status_txt, color=h["col"], fontsize=6.8, fontweight='bold')
        else:
            ax.text(3.1, y - 1.05, "✓ AUTHENTICATED SMTP TRANSPORT", color="#10B981", fontsize=6.8, fontweight='bold')

        # Arrow down
        if i < len(hops) - 1:
            ax.annotate("", xy=(1.8, y - 1.45), xytext=(1.8, y - 1.25),
                        arrowprops=dict(arrowstyle="->", color="#38BDF8", lw=1.5))

        y -= 1.85

    # Bottom Disclaimer Bar
    discl = patches.FancyBboxPatch((0.5, 0.2), 9.0, 0.65,
                                  boxstyle="round,pad=0.02,rounding_size=0.08",
                                  facecolor="#0F172A", edgecolor="#334155", linewidth=1.0)
    ax.add_patch(discl)
    ax.text(0.7, 0.55, "⚖️ Legal Forensic Disclaimer: Infrastructure mapping provides network routing evidence", color="#CBD5E1", fontsize=6.5)
    ax.text(0.7, 0.32, "complies with Indian IT Act 2000 Section 65B without relying on physical user presumptions.", color="#94A3B8", fontsize=6.0)

    plt.tight_layout()
    out_path = "generated_assets/geolocation_forensic_visual.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#0B192C')
    plt.close()
    print("Generated:", out_path)

# -------------------------------------------------------------
# 3. Correlation Threat Graph Visual for Slide 2 / 5
# -------------------------------------------------------------
def generate_correlation_graph_visual():
    fig, ax = plt.subplots(figsize=(5.6, 3.8), dpi=300)
    fig.patch.set_facecolor('#0B192C')
    ax.set_facecolor('#0B192C')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(0.5, 9.3, "🕸️ FORENSIC ENTITY CORRELATION GRAPH", color="#A855F7", fontsize=10, fontweight='bold')
    ax.text(0.5, 8.7, "Multi-Vector Threat Topology Linking IPs, Domains, VPAs & Actors", color="#94A3B8", fontsize=7.5)

    # Central Threat Actor Node
    center_circle = patches.Circle((5.0, 5.0), 1.1, facecolor="#7E22CE", edgecolor="#C084FC", linewidth=2.0)
    ax.add_patch(center_circle)
    ax.text(5.0, 5.2, "THREAT ACTOR", color="white", fontsize=7.5, fontweight='bold', ha='center')
    ax.text(5.0, 4.7, "Cluster #841", color="#E9D5FF", fontsize=6.8, ha='center')

    # Satellite Nodes
    nodes = [
        {"x": 1.8, "y": 7.4, "label": "Spoofed Domain\nsbi-secure-portal.in", "col": "#EF4444", "sub": "Typosquat (Dist: 2)"},
        {"x": 8.2, "y": 7.4, "label": "Origin Tor Node\n185.220.101.5", "col": "#F59E0B", "sub": "Exit Relay (DE)"},
        {"x": 1.8, "y": 2.6, "label": "Fraudulent UPI\nsupport@sbikyc.okaxis", "col": "#EC4899", "sub": "Deceptive VPA"},
        {"x": 8.2, "y": 2.6, "label": "Target Inboxes\n142 Employees", "col": "#10B981", "sub": "Spear-Phish Campaign"}
    ]

    for n in nodes:
        # Line connecting to center
        ax.plot([5.0, n["x"]], [5.0, n["y"]], color="#64748B", linestyle="--", lw=1.2, zorder=1)
        # Node Box
        box = patches.FancyBboxPatch((n["x"] - 1.5, n["y"] - 0.7), 3.0, 1.4,
                                     boxstyle="round,pad=0.03,rounding_size=0.1",
                                     facecolor="#1E293B", edgecolor=n["col"], linewidth=1.5, zorder=2)
        ax.add_patch(box)
        ax.text(n["x"], n["y"] + 0.25, n["label"], color="white", fontsize=6.8, fontweight='bold', ha='center')
        ax.text(n["x"], n["y"] - 0.45, n["sub"], color=n["col"], fontsize=6.2, ha='center')

    # Bottom Metric Banner
    bot = patches.FancyBboxPatch((0.5, 0.2), 9.0, 0.65,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor="#0F172A", edgecolor="#334155", linewidth=1.0)
    ax.add_patch(bot)
    ax.text(0.7, 0.55, "🔍 Multi-Incident Correlation: Unveils repeated campaigns targeting multiple vectors", color="#CBD5E1", fontsize=6.5)
    ax.text(0.7, 0.32, "enabling proactive enterprise defense before credential harvesting succeeds.", color="#94A3B8", fontsize=6.0)

    plt.tight_layout()
    out_path = "generated_assets/correlation_graph_visual.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#0B192C')
    plt.close()
    print("Generated:", out_path)

# -------------------------------------------------------------
# 4. Multi-Vector Security Shield Architecture Graphic for Slide 1 / 2
# -------------------------------------------------------------
def generate_shield_architecture_visual():
    fig, ax = plt.subplots(figsize=(5.4, 4.6), dpi=300)
    fig.patch.set_facecolor('#0B192C')
    ax.set_facecolor('#0B192C')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(5.0, 9.4, "🛡️ SENTINEL AI MULTI-VECTOR ARCHITECTURE", color="#38BDF8", fontsize=9.5, fontweight='bold', ha='center')
    ax.text(5.0, 8.8, "Unified Autonomous Cyber Interception Stack", color="#94A3B8", fontsize=7.2, ha='center')

    layers = [
        {"y": 7.0, "title": "1. INBOX GUARDIAN (GMAIL / RFC 5322)", "desc": "SPF, DKIM, DMARC alignment, Return-Path & Reply-To spoof triage", "col": "#1A56A0"},
        {"y": 5.4, "title": "2. HOP-BY-HOP IP GEOLOCATION ENGINE", "desc": "Received chain parsing, IPinfo intelligence, ASN & Tor/VPN classifier", "col": "#00838F"},
        {"y": 3.8, "title": "3. FORENSIC CORRELATION & LEGAL DOSSIER", "desc": "Interactive threat topology graph & IT Act Sec 65B PDF reports", "col": "#7E22CE"},
        {"y": 2.2, "title": "4. ACTIVE ENDPOINT SHIELD (CHROMIUM MV3)", "desc": "declarativeNetRequest, real-time DOM scanner & quarantine modal", "col": "#166534"},
        {"y": 0.6, "title": "5. AWARENESS & SIMULATION SANDBOX", "desc": "Live neutralized lures converted into hands-on workforce drills", "col": "#B45309"}
    ]

    for lay in layers:
        card = patches.FancyBboxPatch((0.5, lay["y"] - 0.5), 9.0, 1.25,
                                      boxstyle="round,pad=0.03,rounding_size=0.1",
                                      facecolor="#1E293B", edgecolor=lay["col"], linewidth=1.5)
        ax.add_patch(card)
        # Accent left bar
        bar = patches.FancyBboxPatch((0.5, lay["y"] - 0.5), 0.35, 1.25,
                                     boxstyle="round,pad=0.01,rounding_size=0.05",
                                     facecolor=lay["col"], edgecolor="none")
        ax.add_patch(bar)
        ax.text(1.1, lay["y"] + 0.32, lay["title"], color="white", fontsize=7.5, fontweight='bold')
        ax.text(1.1, lay["y"] - 0.15, lay["desc"], color="#CBD5E1", fontsize=6.8)

    plt.tight_layout()
    out_path = "generated_assets/shield_architecture_visual.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#0B192C')
    plt.close()
    print("Generated:", out_path)

if __name__ == "__main__":
    generate_flowchart_architecture()
    generate_geolocation_visual()
    generate_correlation_graph_visual()
    generate_shield_architecture_visual()
    print("All diagram assets generated successfully!")
