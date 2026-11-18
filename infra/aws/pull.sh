#!/usr/bin/env bash
# Descarga los resultados y logs de una sesión a experiments/runs/<sesion>/.
#
# Uso: infra/aws/pull.sh <sesion>
source "$(dirname "$0")/lib.sh"

SESSION="${1:-}"
[[ -n "$SESSION" ]] || { sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
valid_session "$SESSION"
require aws
load_config

DEST="$REPO_ROOT/experiments/runs/$SESSION"
mkdir -p "$DEST"

log "descargando s3://$DSQA_BUCKET/runs/$SESSION/ → experiments/runs/$SESSION/"
awsr s3 sync "s3://$DSQA_BUCKET/runs/$SESSION/" "$DEST/" --only-show-errors

if [[ -f "$DEST/SUMMARY.txt" ]]; then
  echo
  cat "$DEST/SUMMARY.txt"
else
  warn "la sesión aún no terminó (no hay SUMMARY.txt). Revisa infra/aws/status.sh"
fi
