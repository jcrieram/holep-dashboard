#!/bin/bash
# Inicia el Dashboard HoLEP
# Acceso desde cualquier dispositivo Tailscale: http://100.84.66.88:8501

cd /Users/juanriera/Documents/Claude/holep_dashboard
/Library/Developer/CommandLineTools/usr/bin/python3 -m streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
