"""Envía la URL del túnel por email al arrancar."""
import sys, json, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from datetime import datetime

url = sys.argv[1] if len(sys.argv) > 1 else "URL no disponible"

CREDS = json.loads(Path("/Users/juanriera/Documents/Claude/Outputs/etf_email.json").read_text())
ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

html = f"""
<div style="font-family:Georgia;max-width:500px;margin:0 auto;background:#0d1117;padding:28px;border-radius:12px;color:#e6edf3">
  <h2 style="color:#58a6ff;margin-top:0">🔬 Dashboard HoLEP — Activo</h2>
  <p style="color:#8b949e;font-size:13px">{ahora}</p>
  <div style="background:#161b22;border:1px solid #21262d;border-radius:8px;padding:20px;margin:16px 0">
    <p style="margin:0 0 8px 0;color:#8b949e;font-size:13px">URL de acceso:</p>
    <a href="{url}" style="color:#58a6ff;font-size:18px;font-weight:700;word-break:break-all">{url}</a>
  </div>
  <p style="color:#8b949e;font-size:13px">Funciona desde cualquier navegador, en cualquier lugar.<br>
  La URL cambia solo si el Mac se reinicia.</p>
</div>
"""

msg = MIMEText(html, "html")
msg["Subject"] = f"🔬 Dashboard HoLEP activo — {ahora}"
msg["From"]    = CREDS["gmail_user"]
msg["To"]      = CREDS["gmail_user"]

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(CREDS["gmail_user"], CREDS["gmail_app_password"])
    s.sendmail(CREDS["gmail_user"], CREDS["gmail_user"], msg.as_string())

print(f"✉ Email enviado: {url}")
