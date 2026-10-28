import os
from PIL import Image, ImageOps

os.makedirs('generated_assets', exist_ok=True)
proof_dir = 'screenshots_proofs'

def add_frame(img, border_color=(26, 86, 160), border_width=3):
    return ImageOps.expand(img, border=border_width, fill=border_color)

# 1. Slide 2 Proof: Dashboard Overview
# Keep full screenshot aspect ratio (1865 x 936 -> ~ 1.99:1)
img1 = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 130255.png'))
framed1 = add_frame(img1.convert('RGB'), border_color=(26, 86, 160), border_width=3)
framed1.save('generated_assets/proof_slide2_dashboard.jpg', quality=95)
print("Saved proof_slide2_dashboard.jpg:", framed1.size)

# 2. Slide 4 Proof A: Blocked Threat Inbox
# Focus on the blocked email item and stats (center-crop for crispness)
img_blocked = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 131524.png'))
w, h = img_blocked.size
# Crop from sidebar right to right edge, from header to stats
crop_blocked = img_blocked.crop((int(w * 0.15), int(h * 0.16), int(w * 0.98), int(h * 0.95)))
framed_blocked = add_frame(crop_blocked.convert('RGB'), border_color=(185, 28, 28), border_width=3)
framed_blocked.save('generated_assets/proof_slide4_blocked_threat.jpg', quality=95)
print("Saved proof_slide4_blocked_threat.jpg:", framed_blocked.size)

# 3. Slide 4 Proof B: RFC Forensics
img_forensics = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 130958.png'))
w, h = img_forensics.size
# Crop to focus on Safe badge, risk score, sender forensics, and authentication passes
crop_forensics = img_forensics.crop((int(w * 0.15), int(h * 0.05), int(w * 0.98), int(h * 0.95)))
framed_forensics = add_frame(crop_forensics.convert('RGB'), border_color=(0, 131, 143), border_width=3)
framed_forensics.save('generated_assets/proof_slide4_rfc_forensics.jpg', quality=95)
print("Saved proof_slide4_rfc_forensics.jpg:", framed_forensics.size)

# 4. Slide 4 Proof C: Infrastructure Geolocation World Map
img_geo = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 131025.png'))
w, h = img_geo.size
crop_geo = img_geo.crop((int(w * 0.15), int(h * 0.20), int(w * 0.98), int(h * 0.95)))
framed_geo = add_frame(crop_geo.convert('RGB'), border_color=(126, 34, 206), border_width=3)
framed_geo.save('generated_assets/proof_slide4_geolocation.jpg', quality=95)
print("Saved proof_slide4_geolocation.jpg:", framed_geo.size)

# 5. Slide 4 Proof D: Indicator Graph & SHA-256 Hashes
img_graph = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 131042.png'))
w, h = img_graph.size
crop_graph = img_graph.crop((int(w * 0.15), int(h * 0.12), int(w * 0.98), int(h * 0.95)))
framed_graph = add_frame(crop_graph.convert('RGB'), border_color=(26, 86, 160), border_width=3)

# Inset extension warning (Screenshot 2026-09-18 130837.png) on top right
img_ext = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 130837.png'))
ew, eh = img_ext.size
crop_ext = img_ext.crop((int(ew * 0.26), int(eh * 0.12), int(ew * 0.74), int(eh * 0.88)))
framed_ext = add_frame(crop_ext.convert('RGB'), border_color=(239, 68, 68), border_width=4)
inset_w = int(framed_graph.width * 0.36)
inset_h = int(framed_ext.height * (inset_w / framed_ext.width))
resized_ext = framed_ext.resize((inset_w, inset_h), Image.Resampling.LANCZOS)
framed_graph.paste(resized_ext, (framed_graph.width - inset_w - 20, 20))
framed_graph.save('generated_assets/proof_slide4_graph_extension.jpg', quality=95)
print("Saved proof_slide4_graph_extension.jpg:", framed_graph.size)

# 6. Slide 5 Proof: Online Abuse Forensics & Repeat Offender Tracking
img_abuse = Image.open(os.path.join(proof_dir, 'Screenshot 2026-09-18 130558.png'))
w, h = img_abuse.size
# Crop tight to the forensic stream and repeat offender cards
crop_abuse = img_abuse.crop((int(w * 0.05), int(h * 0.06), int(w * 0.95), int(h * 0.94)))
framed_abuse = add_frame(crop_abuse.convert('RGB'), border_color=(217, 119, 6), border_width=3)
framed_abuse.save('generated_assets/proof_slide5_abuse_analyzer.jpg', quality=95)
print("Saved proof_slide5_abuse_analyzer.jpg:", framed_abuse.size)
