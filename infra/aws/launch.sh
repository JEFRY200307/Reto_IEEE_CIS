#!/usr/bin/env bash
# Lanza la instancia de una sesión. Spot primero; on-demand solo si se pide (ADR-14).
# La instancia ejecuta los trabajos, sube los resultados y se termina sola (ADR-17).
#
# Uso: infra/aws/launch.sh <sesion> [opciones]
#   --template p5|g6e|prep   plantilla a usar (por defecto p5)
#   --on-demand              no intentar spot
#   --fallback-on-demand     si no hay capacidad spot en ninguna zona, lanzar on-demand
#   --max-hours N            apagado forzado a las N horas (por defecto MAX_HOURS_DEFAULT; > 4 exige --force)
#   --keep-alive             no apagar al terminar los trabajos (solo para crear la AMI; sigue el límite de horas)
#   --force                  lanzar aunque ya haya instancias del proyecto encendidas
#   --dry-run                mostrar lo que se haría, sin lanzar nada
source "$(dirname "$0")/lib.sh"

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

SESSION="${1:-}"; [[ -n "$SESSION" ]] || usage; shift
TEMPLATE_KEY="p5"; MARKET="spot"; FALLBACK_OD=false; MAX_HOURS=""; KEEP_ALIVE=false; FORCE=false; DRY_RUN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --template) TEMPLATE_KEY="${2:-}"; shift ;;
    --on-demand) MARKET="on-demand" ;;
    --fallback-on-demand) FALLBACK_OD=true ;;
    --max-hours) MAX_HOURS="${2:-}"; shift ;;
    --keep-alive) KEEP_ALIVE=true ;;
    --force) FORCE=true ;;
    --dry-run) DRY_RUN=true ;;
    *) usage ;;
  esac
  shift
done

valid_session "$SESSION"
require aws
load_config

case "$TEMPLATE_KEY" in
  p5)   TEMPLATE="$LAUNCH_TEMPLATE" ;;
  g6e)  TEMPLATE="${LAUNCH_TEMPLATE_FALLBACK:?falta LAUNCH_TEMPLATE_FALLBACK en config.env}" ;;
  prep) TEMPLATE="${LAUNCH_TEMPLATE_PREP:?falta LAUNCH_TEMPLATE_PREP en config.env}" ;;
  *) die "plantilla desconocida '$TEMPLATE_KEY' (p5, g6e o prep)" ;;
esac

MAX_HOURS="${MAX_HOURS:-$MAX_HOURS_DEFAULT}"
[[ "$MAX_HOURS" =~ ^[0-9]+$ ]] && (( MAX_HOURS >= 1 )) || die "--max-hours debe ser un entero >= 1"
(( MAX_HOURS <= 4 )) || $FORCE || die "--max-hours $MAX_HOURS supera 4 h; añade --force si es intencional"

# 1. Evitar instancias duplicadas u olvidadas.
RUNNING="$(running_instances)"
if [[ -n "$RUNNING" ]] && ! $FORCE; then
  printf '%s\n' "$RUNNING" >&2
  die "ya hay instancias del proyecto encendidas (arriba). Termínalas con stop.sh o usa --force."
fi

# 2. La lista de trabajos debe estar en S3 (push.sh).
if ! $DRY_RUN; then
  awsr s3 ls "s3://$DSQA_BUCKET/jobs/$SESSION.txt" >/dev/null 2>&1 \
    || die "no está s3://$DSQA_BUCKET/jobs/$SESSION.txt. Ejecuta antes: infra/aws/push.sh $SESSION"
fi

# 3. User data = variables de la sesión + watchdog + bootstrap.
TMP_DIR="$AWS_DIR/.tmp"; mkdir -p "$TMP_DIR"
USER_DATA="$TMP_DIR/user-data-$SESSION.sh"
{
  echo '#!/bin/bash'
  echo "export DSQA_SESSION='$SESSION'"
  echo "export DSQA_BUCKET='$DSQA_BUCKET'"
  echo "export AWS_REGION='$AWS_REGION'"
  echo "export AWS_DEFAULT_REGION='$AWS_REGION'"
  echo "export DSQA_MAX_HOURS='$MAX_HOURS'"
  echo "export DSQA_KEEP_ALIVE='$KEEP_ALIVE'"
  # La preparación necesita internet para descargar modelos; las sesiones de evaluación imitan a Codabench.
  if [[ "$TEMPLATE_KEY" == "prep" ]]; then echo "export DSQA_OFFLINE='false'"; else echo "export DSQA_OFFLINE='true'"; fi
  echo "mkdir -p /usr/local/bin"
  echo "cat > /usr/local/bin/dsqa-watchdog.sh <<'DSQA_WATCHDOG_EOF'"
  tr -d '\r' < "$AWS_DIR/watchdog.sh"
  echo "DSQA_WATCHDOG_EOF"
  echo "chmod +x /usr/local/bin/dsqa-watchdog.sh"
  tr -d '\r' < "$AWS_DIR/bootstrap.sh" | sed '1{/^#!/d}'
} > "$USER_DATA"
SIZE=$(wc -c < "$USER_DATA")
(( SIZE < 16000 )) || die "el user data ocupa $SIZE bytes (límite de AWS: 16 KB)"

# 4. Zonas de la región que ofrecen el tipo de instancia de la plantilla.
INSTANCE_TYPE="$(awsr ec2 describe-launch-template-versions --launch-template-name "$TEMPLATE" \
  --versions '$Default' --query 'LaunchTemplateVersions[0].LaunchTemplateData.InstanceType' --output text)"
ZONES="$(awsr ec2 describe-instance-type-offerings --location-type availability-zone \
  --filters "Name=instance-type,Values=$INSTANCE_TYPE" --query 'InstanceTypeOfferings[].Location' --output text)"
[[ -n "$ZONES" ]] || die "$INSTANCE_TYPE no está disponible en $AWS_REGION"

SUBNETS=()
for az in $ZONES; do
  subnet="$(awsr ec2 describe-subnets --filters "Name=availability-zone,Values=$az" "Name=default-for-az,Values=true" \
    --query 'Subnets[0].SubnetId' --output text)"
  [[ "$subnet" != "None" && -n "$subnet" ]] && SUBNETS+=("$subnet")
done
(( ${#SUBNETS[@]} > 0 )) || die "no hay subred por defecto en las zonas con $INSTANCE_TYPE ($ZONES)"

log "sesión=$SESSION plantilla=$TEMPLATE tipo=$INSTANCE_TYPE mercado=$MARKET máx=${MAX_HOURS}h keep-alive=$KEEP_ALIVE"
log "zonas candidatas: $ZONES"

TAGS="ResourceType=instance,Tags=[{Key=Project,Value=$PROJECT_TAG},{Key=Session,Value=$SESSION},{Key=Name,Value=$PROJECT_TAG-$SESSION}]"
SPOT_OPTS='{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"one-time","InstanceInterruptionBehavior":"terminate"}}'
USER_DATA_ARG="file://$(native_path "$USER_DATA")"

try_launch() {  # $1 = mercado, $2 = subred
  local args=(ec2 run-instances --launch-template "LaunchTemplateName=$TEMPLATE,Version=\$Default"
              --subnet-id "$2" --user-data "$USER_DATA_ARG" --tag-specifications "$TAGS"
              --count 1 --query 'Instances[0].InstanceId' --output text)
  [[ "$1" == "spot" ]] && args+=(--instance-market-options "$SPOT_OPTS")
  if $DRY_RUN; then
    printf '[dry-run] aws --region %s' "$AWS_REGION" >&2; printf ' %q' "${args[@]}" >&2; echo >&2
    echo "i-dryrun"; return 0
  fi
  awsr "${args[@]}"
}

launch_any_zone() {  # $1 = mercado
  local subnet out
  if $DRY_RUN; then
    try_launch "$1" "${SUBNETS[0]}"; return 0
  fi
  for subnet in "${SUBNETS[@]}"; do
    if out="$(try_launch "$1" "$subnet" 2>&1)"; then
      echo "$out"; return 0
    fi
    if grep -qE 'InsufficientInstanceCapacity|SpotMaxPriceTooLow|capacity-not-available|InsufficientCapacity' <<< "$out"; then
      warn "sin capacidad $1 en la subred $subnet; probando otra zona"
      continue
    fi
    printf '%s\n' "$out" >&2
    grep -qE 'VcpuLimitExceeded|MaxSpotInstanceCountExceeded' <<< "$out" \
      && warn "cuota de GPU insuficiente: revisa dsqa-infra/scripts/request-quotas.sh"
    return 2
  done
  return 1
}

set +e
INSTANCE_ID="$(launch_any_zone "$MARKET")"; rc=$?
if (( rc == 1 )) && [[ "$MARKET" == "spot" ]] && $FALLBACK_OD; then
  warn "no hubo capacidad spot en ninguna zona; lanzando on-demand (~3-5 veces más caro)"
  INSTANCE_ID="$(launch_any_zone on-demand)"; rc=$?
fi
set -e

case $rc in
  0) ;;
  1) die "no hubo capacidad en ninguna zona. Prueba más tarde, otra región, o --fallback-on-demand / --on-demand." ;;
  *) die "no se pudo lanzar la instancia (ver el error arriba)" ;;
esac

log "instancia lanzada: $INSTANCE_ID"
log "seguir:      infra/aws/status.sh"
log "terminal:    aws ssm start-session --region $AWS_REGION --target $INSTANCE_ID"
log "log en vivo: (dentro) sudo tail -f /var/log/dsqa-bootstrap.log"
log "resultados:  infra/aws/pull.sh $SESSION"
echo "$INSTANCE_ID"
