import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('generated_assets', exist_ok=True)
fig, ax = plt.subplots(figsize=(13.33, 3.8), dpi=300)
fig.patch.set_facecolor('#0B192C')
ax.set_facecolor('#0B192C')
ax.set_xlim(0, 13.33)
ax.set_ylim(0, 3.8)
ax.axis('off')

# Title
ax.text(0.4, 3.48, '❖ END-TO-END EXECUTION PIPELINE & HOW IT WORKS FLOWCHART', color='#38BDF8', fontsize=12, fontweight='bold', fontfamily='sans-serif')
ax.text(0.4, 3.18, 'Deterministic, sub-50ms multi-vector forensic evaluation and cryptographic chain verification', color='#94A3B8', fontsize=8.5, fontfamily='sans-serif')

stages = [
    {
        'num': '01',
        'title': 'TELEMETRY INGESTION',
        'sub': 'Multi-Source Feeds',
        'bg': '#0F2744',
        'border': '#1A56A0',
        'badge_bg': '#1A56A0',
        'items': [
            '• Gmail REST API (2s Sync)',
            '• Raw RFC 5322 EML Stream',
            '• MV3 Chrome WebRequest',
            '• YouTube Comment Feeds',
            '• UPI Handle & VPA Inputs'
        ],
        'x': 0.35
    },
    {
        'num': '02',
        'title': 'RFC 5322 PARSING & AUTH',
        'sub': 'Cryptographic Validation',
        'bg': '#0A3338',
        'border': '#00838F',
        'badge_bg': '#00838F',
        'items': [
            '• SPF IP Authorization',
            '• DKIM RSA Signature Check',
            '• DMARC Domain Alignment',
            '• Return-Path Mismatch Flag',
            '• ARC Chain Validation'
        ],
        'x': 2.92
    },
    {
        'num': '03',
        'title': 'HOP TRAVERSAL & GEO',
        'sub': 'Infrastructure Profiling',
        'bg': '#24143D',
        'border': '#7E22CE',
        'badge_bg': '#7E22CE',
        'items': [
            '• Received Header Hop Trace',
            '• Origin IP Extraction',
            '• IPinfo ASN & Coordinates',
            '• Tor / VPN / Proxy Detection',
            '• ISP & Hosting Triage'
        ],
        'x': 5.49
    },
    {
        'num': '04',
        'title': 'AI THREAT ENGINE & NLP',
        'sub': 'Correlation & Scoring',
        'bg': '#311624',
        'border': '#BE123C',
        'badge_bg': '#BE123C',
        'items': [
            '• Transformer Urgency Score',
            '• Levenshtein Typo Engine',
            '• 31-Node Correlation Graph',
            '• Multi-Factor Risk Rating',
            '• Repeat Offender Tracking'
        ],
        'x': 8.06
    },
    {
        'num': '05',
        'title': 'ACTION & SECTION 65B',
        'sub': 'Zero-Hour Remediation',
        'bg': '#0D3322',
        'border': '#15803D',
        'badge_bg': '#15803D',
        'items': [
            '• Automated Inbox Quarantine',
            '• MV3 Edge Warning Overlay',
            '• SHA-256 Evidence Snapshot',
            '• IT Act Sec 65B PDF Dossier',
            '• Simulation Drill Generator'
        ],
        'x': 10.63
    }
]

card_w = 2.25
card_h = 2.70

for i, s in enumerate(stages):
    x = s['x']
    y = 0.25
    rect = patches.FancyBboxPatch((x, y), card_w, card_h, boxstyle='round,pad=0.04,rounding_size=0.15', facecolor=s['bg'], edgecolor=s['border'], linewidth=1.5)
    ax.add_patch(rect)
    hdr = patches.FancyBboxPatch((x, y + card_h - 0.65), card_w, 0.65, boxstyle='round,pad=0.02,rounding_size=0.1', facecolor=s['badge_bg'], edgecolor='none')
    ax.add_patch(hdr)
    ax.text(x + 0.12, y + card_h - 0.24, f"STAGE {s['num']}", color='#BAE6FD', fontsize=7.5, fontweight='bold')
    ax.text(x + 0.12, y + card_h - 0.44, s['title'], color='white', fontsize=7.8, fontweight='bold')
    ax.text(x + 0.12, y + card_h - 0.58, s['sub'], color='#E2E8F0', fontsize=6.8, fontstyle='italic')
    
    iy = y + card_h - 0.90
    for itm in s['items']:
        ax.text(x + 0.12, iy, itm, color='#F1F5F9', fontsize=7.2, fontweight='bold' if '•' in itm else 'normal')
        iy -= 0.33
        
    if i < len(stages) - 1:
        arr_x = x + card_w + 0.04
        arr_y = y + card_h / 2
        ax.annotate('', xy=(arr_x + 0.24, arr_y), xytext=(arr_x, arr_y),
                    arrowprops=dict(arrowstyle='->', color='#38BDF8', lw=2.2, mutation_scale=14))

plt.tight_layout()
out_path = 'generated_assets/sih_pipeline_flowchart_master.png'
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#0B192C')
plt.close()
print('Successfully generated flowchart:', out_path)
