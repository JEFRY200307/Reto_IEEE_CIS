#!/bin/bash
# Se ejecuta EN LA INSTANCIA cada 5 min (cron). Termina la instancia si lleva ~20 min sin trabajo (ADR-17):
# sin el proceso de bootstrap vivo y con la GPU por debajo del 5 % de uso en 4 lecturas seguidas.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin

STATE=/run/dsqa-idle-count
GPU_ACTIVE_PCT=5
MAX_IDLE_CHECKS=4

count=$(cat "$STATE" 2>/dev/null || echo 0)

busy=false
if [[ -s /run/dsqa-busy ]] && kill -0 "$(cat /run/dsqa-busy)" 2>/dev/null; then
  busy=true
fi

gpu_active=false
if command -v nvidia-smi >/dev/null 2>&1; then
  util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | sort -n | tail -1 | tr -d ' ')
  if [[ "$util" =~ ^[0-9]+$ ]] && (( util >= GPU_ACTIVE_PCT )); then
    gpu_active=true
  fi
fi

if $busy || $gpu_active; then
  count=0
else
  count=$((count + 1))
fi
echo "$count" > "$STATE"
echo "$(date -u +%FT%TZ) busy=$busy gpu_active=$gpu_active idle_checks=$count/$MAX_IDLE_CHECKS"

if (( count >= MAX_IDLE_CHECKS )); then
  echo "$(date -u +%FT%TZ) inactiva ~$((count * 5)) min: guardando resultados y apagando"
  [[ -x /usr/local/bin/dsqa-sync.sh ]] && /usr/local/bin/dsqa-sync.sh
  shutdown -h now "dsqa: instancia inactiva"
fi
