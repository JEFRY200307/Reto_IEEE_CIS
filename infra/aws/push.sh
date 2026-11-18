#!/usr/bin/env bash
# Sube a S3 todo lo que necesita una sesión: código, lista de trabajos y (si existe) el corpus público.
#
# Uso: infra/aws/push.sh <sesion> [--no-corpus]
#   <sesion>  nombre de la sesión; debe existir infra/aws/jobs/<sesion>.txt
source "$(dirname "$0")/lib.sh"

usage() { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

SESSION="${1:-}"; [[ -n "$SESSION" ]] || usage; shift
WITH_CORPUS=true
for arg in "$@"; do
  case "$arg" in
    --no-corpus) WITH_CORPUS=false ;;
    *) usage ;;
  esac
done

valid_session "$SESSION"
require aws
load_config

JOBS="$AWS_DIR/jobs/$SESSION.txt"
[[ -f "$JOBS" ]] || die "no existe $JOBS (una línea por comando)"
grep -qvE '^\s*(#|$)' "$JOBS" || die "$JOBS no tiene ningún comando"

cd "$REPO_ROOT"

log "subiendo código a s3://$DSQA_BUCKET/code/"
awsr s3 sync . "s3://$DSQA_BUCKET/code/" --delete --only-show-errors \
  --exclude ".git/*" --exclude "*/.git/*" \
  --exclude "models/*" --exclude "data/*" --exclude "dist/*" \
  --exclude "experiments/runs/*" --exclude "docs/*" \
  --exclude "*__pycache__/*" --exclude "*.pyc" --exclude ".venv/*" \
  --exclude "infra/aws/config.env" --exclude "infra/aws/.tmp/*"

log "subiendo lista de trabajos a s3://$DSQA_BUCKET/jobs/$SESSION.txt"
awsr s3 cp "$JOBS" "s3://$DSQA_BUCKET/jobs/$SESSION.txt" --only-show-errors

if $WITH_CORPUS && [[ -d data/public_pdfs ]]; then
  log "sincronizando corpus público a s3://$DSQA_BUCKET/corpus/"
  awsr s3 sync data/public_pdfs "s3://$DSQA_BUCKET/corpus/" --only-show-errors
fi

log "listo. Siguiente paso: infra/aws/launch.sh $SESSION"
