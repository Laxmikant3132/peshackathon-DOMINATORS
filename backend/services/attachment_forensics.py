import os
from typing import Dict, Any, List

SUSPICIOUS_EXTENSIONS = {
    '.exe', '.scr', '.vbs', '.bat', '.js', '.jar', '.ps1', '.cmd', '.pif', '.application', '.gadget', '.msi', '.msp', '.com', '.wsf', '.hta', '.cpl', '.msc'
}

def analyze_attachment_metadata(filename: str, size_bytes: int, mime_type: str, file_hash: str = None) -> List[Dict[str, Any]]:
    """
    Performs static analysis on attachment metadata without executing or opening the file.
    Returns a list of forensic findings.
    """
    findings = []
    
    # Check for missing basic information
    if not filename:
        findings.append({
            "type": "Evidence",
            "description": "Attachment missing filename.",
            "confidence": 1.0,
            "source": "Attachment Forensics"
        })
        return findings

    parts = filename.split('.')
    ext = f".{parts[-1].lower()}" if len(parts) > 1 else ""
    
    # 1. Double extension check (e.g. invoice.pdf.exe)
    if len(parts) > 2:
        prev_ext = f".{parts[-2].lower()}"
        if ext in SUSPICIOUS_EXTENSIONS:
            findings.append({
                "type": "Evidence",
                "description": f"Double extension detected on attachment: {filename}",
                "confidence": 0.98,
                "source": "Attachment Forensics"
            })
            
    # 2. Suspicious extension check
    if ext in SUSPICIOUS_EXTENSIONS:
        findings.append({
            "type": "Evidence",
            "description": f"Suspicious executable attachment: {filename}",
            "confidence": 0.95,
            "source": "Attachment Forensics"
        })
        
    # 3. Size mismatch/limits
    if size_bytes > 50 * 1024 * 1024:
        findings.append({
            "type": "Evidence",
            "description": f"Unusually large attachment: {filename} ({size_bytes} bytes)",
            "confidence": 0.70,
            "source": "Attachment Forensics"
        })
        
    # 4. MIME type mismatch heuristics (Inference based on ext vs mime)
    # Simple check for PDF vs Executable mismatch
    if ext == '.pdf' and 'application/x-msdownload' in mime_type.lower():
        findings.append({
            "type": "Evidence",
            "description": f"MIME type mismatch. File is .pdf but MIME is executable: {mime_type}",
            "confidence": 0.90,
            "source": "Attachment Forensics"
        })

    return findings
