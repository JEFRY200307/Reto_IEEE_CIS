#!/usr/bin/env bash
# Muestra las instancias del proyecto encendidas, cuánto llevan y el estado de las sesiones en S3.
#
# Uso: infra/aws/status.sh
source "$(dirname "$0")/lib.sh"

require aws
load_config

RUNNING="$(running_instances)"
if [[ -z "$RUNNING" ]]; then
  log "no hay instancias del proyecto encendidas"
else
  now=$(date -u +%s)
  printf '%-20s %-12s %-10s %-12s %-8s %s\n' "INSTANCIA" "TIPO" "MERCADO" "ZONA" "HORAS" "SESIÓN"
  while read -r id type market az launched session; do
    started=$(date -u -d "$launched" +%s 2>/dev/null || echo "$now")
    hours=$(awk -v s="$(( now - started ))" 'BEGIN { printf "%.1f", s / 3600 }')
    printf '%-20s %-12s %-10s %-12s %-8s %s\n' "$id" "$type" "$market" "$az" "$hours" "$session"
  done <<< "$RUNNING"
  warn "recuerda: cada instancia cobra mientras esté encendida"
fi

echo
log "sesiones con resultados en s3://$DSQA_BUCKET/runs/"
awsr s3 ls "s3://$DSQA_BUCKET/runs/" 2>/dev/null | awk '{print "  " $2}' || true
