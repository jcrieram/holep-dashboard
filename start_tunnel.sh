#!/bin/bash
# Inicia el túnel Cloudflare para el Dashboard HoLEP
# y envía la URL por email a jcrieram@gmail.com

LOG=/Users/juanriera/Documents/Claude/logs/cloudflare_tunnel.log
mkdir -p "$(dirname "$LOG")"

# Matar instancia anterior si existe
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 2

# Iniciar túnel y capturar URL
/Users/juanriera/bin/cloudflared tunnel --url http://localhost:8501 --no-autoupdate > "$LOG" 2>&1 &
CF_PID=$!

# Esperar hasta que aparezca la URL (máx 30s)
for i in $(seq 1 30); do
    URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        echo "$(date): Túnel activo → $URL" >> "$LOG"
        break
    fi
    sleep 1
done

# Enviar email con la nueva URL
if [ -n "$URL" ]; then
    python3 /Users/juanriera/Documents/Claude/holep_dashboard/send_url_email.py "$URL"
fi

wait $CF_PID
