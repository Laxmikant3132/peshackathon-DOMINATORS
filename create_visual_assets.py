import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('generated_assets', exist_ok=True)

FONTS_DIR = r"C:\Windows\Fonts"
FONT_REG = os.path.join(FONTS_DIR, "calibri.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "calibrib.ttf")

def get_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# -------------------------------------------------------------
# 1. Flowchart Pipeline Diagram (for Slide 3)
# -------------------------------------------------------------
def generate_pipeline_flowchart():
    w, h = 2400, 720
    img = Image.new('RGB', (w, h), color='#F8FAFC')
    draw = ImageDraw.Draw(img)

    # Title Banner
    draw.rounded_rectangle([20, 15, w - 20, 75], radius=10, fill='#0B192C')
    draw.text((40, 25), "SENTINEL AI: END-TO-END AUTONOMOUS THREAT INTERCEPTION & FORENSIC PIPELINE", 
              font=get_font(28, bold=True), fill='#38BDF8')
    draw.text((1720, 30), "RFC 5322 • OAUTH 2.0 • IT ACT SEC 65B", 
              font=get_font(20, bold=True), fill='#94A3B8')

    stages = [
        {
            "num": "STAGE 01",
            "title": "TELEMETRY INGESTION",
            "col_hdr": "#1A56A0",
            "col_bg": "#F0F6FE",
            "col_border": "#1A56A0",
            "items": [
                ("Gmail API Poller", "2-second polling via OAuth 2.0"),
                ("Raw EML Importer", "RFC 5322 MIME tree structure"),
                ("Browser MV3 Hook", "Captures URL redirect chains"),
                ("YouTube Scraper", "Data API v3 comment streams"),
                ("UPI Payment Hook", "Virtual Payment Address inputs")
            ]
        },
        {
            "num": "STAGE 02",
            "title": "AI THREAT TRIAGE",
            "col_hdr": "#00838F",
            "col_bg": "#E6F6F8",
            "col_border": "#00838F",
            "items": [
                ("Authentication Audit", "SPF, DKIM & DMARC alignment"),
                ("Spoofing Detector", "Return-Path vs From mismatch"),
                ("NLP Phishing Engine", "Urgency & credential lure intent"),
                ("Typosquat Engine", "Levenshtein distance (500+ banks)"),
                ("Attachment Hashing", "SHA-256 / double-extension triage")
            ]
        },
        {
            "num": "STAGE 03",
            "title": "GEOLOCATION & GRAPH",
            "col_hdr": "#6B21A8",
            "col_bg": "#F5EEFA",
            "col_border": "#6B21A8",
            "items": [
                ("Received Hop Traversal", "Extracts origin client public IP"),
                ("IPinfo Geo-Telemetry", "City, country, ASN & ISP profile"),
                ("Anonymizer Classifier", "Flags Tor relays, VPNs, proxies"),
                ("Correlation Graph", "Links IPs, domains & threat nodes"),
                ("Confidence Scoring", "Explainable multi-factor scoring")
            ]
        },
        {
            "num": "STAGE 04",
            "title": "ACTION & FORENSICS",
            "col_hdr": "#166534",
            "col_bg": "#ECF8EE",
            "col_border": "#166534",
            "items": [
                ("Inbox Quarantine", "Immediate isolation in mail client"),
                ("Edge Browser Warning", "Network-level credential block"),
                ("Court-Ready Dossier", "PDF with timestamps & SHA-256"),
                ("Threat Sharing Feed", "Anonymized national CERT-In feed"),
                ("Adaptive Simulation", "Neutralized lures to employee drills")
            ]
        }
    ]

    card_w = 540
    gap = 46
    start_x = 35
    top_y = 100
    card_h = 580

    for idx, s in enumerate(stages):
        x = start_x + idx * (card_w + gap)
        
        draw.rounded_rectangle([x, top_y, x + card_w, top_y + card_h], radius=16, 
                               fill=s["col_bg"], outline=s["col_border"], width=3)
        
        draw.rounded_rectangle([x, top_y, x + card_w, top_y + 90], radius=14, fill=s["col_hdr"])
        draw.text((x + 20, top_y + 12), s["num"], font=get_font(18, bold=True), fill='#E0F2FE')
        draw.text((x + 20, top_y + 42), s["title"], font=get_font(25, bold=True), fill='white')

        cur_y = top_y + 110
        for head, body in s["items"]:
            draw.ellipse([x + 20, cur_y + 8, x + 30, cur_y + 18], fill=s["col_hdr"])
            draw.text((x + 40, cur_y), head, font=get_font(21, bold=True), fill='#0B192C')
            draw.text((x + 40, cur_y + 30), body, font=get_font(18, bold=False), fill='#334155')
            cur_y += 78

        if idx < 3:
            arr_start_x = x + card_w + 8
            arr_end_x = arr_start_x + 30
            arr_y = top_y + (card_h // 2)
            draw.line([arr_start_x, arr_y, arr_end_x, arr_y], fill='#1A56A0', width=6)
            draw.polygon([
                (arr_end_x, arr_y),
                (arr_end_x - 14, arr_y - 10),
                (arr_end_x - 14, arr_y + 10)
            ], fill='#1A56A0')

    img.save('generated_assets/flowchart_pipeline.png', quality=95)
    print("Generated flowchart_pipeline.png")

# -------------------------------------------------------------
# 2. GeoLocation Hop-by-Hop Forensic Traceroute Diagram
# -------------------------------------------------------------
def generate_geolocation_diagram():
    w, h = 1350, 800
    img = Image.new('RGB', (w, h), color='#0B192C')
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([25, 20, w - 25, 80], radius=10, fill='#1E293B')
    draw.text((45, 30), "[GEO-TRACE] HOP-BY-HOP IP GEOLOCATION FORENSIC AUDIT", font=get_font(24, bold=True), fill='#38BDF8')
    draw.text((950, 36), "RECEIVED HEADER PROVENANCE", font=get_font(18, bold=True), fill='#94A3B8')

    hops = [
        {
            "hop": "HOP 1: ORIGINATING CLIENT",
            "ip": "185.220.101.5",
            "type": "TOR EXIT RELAY",
            "loc": "Frankfurt, Germany",
            "asn": "AS200052 (Tor Project Relay Network)",
            "alert": "[!] ANONYMIZATION DETECTED",
            "badge_col": "#DC2626",
            "border_col": "#EF4444"
        },
        {
            "hop": "HOP 2: UNPROTECTED SMTP RELAY",
            "ip": "194.26.29.112",
            "type": "HOSTING DATACENTER",
            "loc": "Amsterdam, Netherlands",
            "asn": "AS49981 (HostRoyale Datacenter Cloud)",
            "alert": "[!] BULK CLOUD INFRASTRUCTURE",
            "badge_col": "#D97706",
            "border_col": "#F59E0B"
        },
        {
            "hop": "HOP 3: GOOGLE MX BORDER GATEWAY",
            "ip": "209.85.216.174",
            "type": "AUTHENTICATED MAIL EDGE",
            "loc": "Mountain View, CA, United States",
            "asn": "AS15169 (Google LLC Infrastructure)",
            "alert": "[OK] TLS 1.3 ENCRYPTED SMTP HOP",
            "badge_col": "#16A34A",
            "border_col": "#10B981"
        },
        {
            "hop": "DESTINATION: ENTERPRISE INBOX",
            "ip": "10.0.4.12",
            "type": "RECIPIENT WORKSTATION",
            "loc": "New Delhi, India",
            "asn": "National Research & Academic Network",
            "alert": "[SAFE] PROTECTED BY SENTINEL AI",
            "badge_col": "#0284C7",
            "border_col": "#38BDF8"
        }
    ]

    y = 105
    card_h = 125

    for idx, h_data in enumerate(hops):
        draw.rounded_rectangle([30, y, w - 30, y + card_h], radius=12, fill='#1E293B', outline=h_data["border_col"], width=2)
        
        draw.rounded_rectangle([45, y + 15, 340, y + 55], radius=8, fill=h_data["badge_col"])
        draw.text((55, y + 22), h_data["hop"], font=get_font(15, bold=True), fill='white')

        draw.text((360, y + 20), f"IP: {h_data['ip']}  |  Location: {h_data['loc']}", 
                  font=get_font(21, bold=True), fill='#F8FAFC')
        draw.text((360, y + 55), f"ASN Profile: {h_data['asn']}  •  Infrastructure: {h_data['type']}", 
                  font=get_font(17, bold=False), fill='#94A3B8')

        draw.text((360, y + 88), h_data["alert"], font=get_font(17, bold=True), fill=h_data["badge_col"])

        if idx < len(hops) - 1:
            draw.line([(w // 2), y + card_h, (w // 2), y + card_h + 25], fill='#38BDF8', width=3)
            draw.polygon([
                ((w // 2), y + card_h + 25),
                ((w // 2) - 8, y + card_h + 15),
                ((w // 2) + 8, y + card_h + 15)
            ], fill='#38BDF8')

        y += card_h + 28

    draw.rounded_rectangle([30, y, w - 30, y + 55], radius=8, fill='#0F172A', outline='#334155', width=1)
    draw.text((45, y + 16), 
              "[LEGAL COMPLIANCE] IT Act 2000 Sec 65B: Hop analysis maps network routing infrastructure for court attribution without privacy intrusion.", 
              font=get_font(15, bold=False), fill='#CBD5E1')

    img.save('generated_assets/geolocation_diagram.png', quality=95)
    print("Generated geolocation_diagram.png")

# -------------------------------------------------------------
# 3. Threat Correlation Graph Visual
# -------------------------------------------------------------
def generate_correlation_diagram():
    w, h = 1350, 800
    img = Image.new('RGB', (w, h), color='#0B192C')
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([25, 20, w - 25, 80], radius=10, fill='#1E293B')
    draw.text((45, 30), "[CORRELATION GRAPH] FORENSIC ENTITY TOPOLOGY", font=get_font(24, bold=True), fill='#C084FC')
    draw.text((880, 36), "CROSS-CAMPAIGN THREAT ACTOR GRAPH", font=get_font(18, bold=True), fill='#94A3B8')

    cx, cy = 675, 420

    satellites = [
        {"x": 220, "y": 200, "w": 320, "h": 140, "title": "SPOOFED DOMAIN", "sub": "sbi-kyc-verify.in\n(Levenshtein Distance: 2)", "col": "#EF4444"},
        {"x": 1130, "y": 200, "w": 320, "h": 140, "title": "ORIGIN TOR RELAY", "sub": "185.220.101.5\n(Frankfurt, DE - AS200052)", "col": "#F59E0B"},
        {"x": 220, "y": 640, "w": 320, "h": 140, "title": "DECEPTIVE UPI VPA", "sub": "support@sbikyc.okaxis\n(Flagged Fraudulent Handle)", "col": "#EC4899"},
        {"x": 1130, "y": 640, "w": 320, "h": 140, "title": "TARGET ENTERPRISE", "sub": "142 Employee Inboxes\n(Spear-Phish Campaign)", "col": "#10B981"}
    ]

    # Draw lines FIRST so center circle sits on top
    for s in satellites:
        draw.line([cx, cy, s["x"], s["y"]], fill='#64748B', width=4)

    # Draw Center Threat Actor Node
    draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill='#7E22CE', outline='#C084FC', width=4)
    draw.text((cx - 90, cy - 40), "THREAT ACTOR", font=get_font(22, bold=True), fill='white')
    draw.text((cx - 80, cy - 5), "CLUSTER #841", font=get_font(20, bold=True), fill='#E9D5FF')
    draw.text((cx - 70, cy + 28), "(Organized Ring)", font=get_font(16, bold=False), fill='#D8B4FE')

    # Draw Satellite Boxes
    for s in satellites:
        bx1, by1 = s["x"] - (s["w"] // 2), s["y"] - (s["h"] // 2)
        bx2, by2 = s["x"] + (s["w"] // 2), s["y"] + (s["h"] // 2)
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=14, fill='#1E293B', outline=s["col"], width=3)
        draw.rounded_rectangle([bx1, by1, bx2, by1 + 45], radius=12, fill=s["col"])
        draw.text((bx1 + 20, by1 + 10), s["title"], font=get_font(17, bold=True), fill='white')
        draw.text((bx1 + 15, by1 + 58), s["sub"], font=get_font(16, bold=False), fill='#F1F5F9')

    draw.rounded_rectangle([30, 725, w - 30, 780], radius=8, fill='#0F172A', outline='#334155', width=1)
    draw.text((45, 742), 
              "[AUDIT] Multi-Vector Entity Correlation: Links isolated email lures, fraudulent payment VPAs, and network infrastructure into an actionable threat dossier.", 
              font=get_font(15, bold=False), fill='#CBD5E1')

    img.save('generated_assets/correlation_diagram.png', quality=95)
    print("Generated correlation_diagram.png")

if __name__ == "__main__":
    generate_pipeline_flowchart()
    generate_geolocation_diagram()
    generate_correlation_diagram()
    print("All visual assets recreated cleanly!")
