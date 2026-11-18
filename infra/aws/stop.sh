#!/usr/bin/env bash
# Termina las instancias de una sesión (o todas las del proyecto). Los resultados ya subidos a S3 se conservan.
#
# Uso: infra/aws/stop.sh <sesion> | --all
source "$(dirname "$0")/lib.sh"

TARGET="${1:-}"
[[ -n "$TARGET" ]] || { sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

require aws
load_config

FILTERS=("Name=tag:Project,Values=$PROJECT_TAG" "Name=instance-state-name,Values=pending,running,stopping,stopped")
if [[ "$TARGET" != "--all" ]]; then
  valid_session "$TARGET"
  FILTERS+=("Name=tag:Session,Values=$TARGET")
fi

IDS="$(awsr ec2 describe-instances --filters "${FILTERS[@]}" --query 'Reservations[].Instances[].InstanceId' --output text)"
[[ -n "$IDS" ]] || { log "no hay instancias que terminar"; exit 0; }

log "terminando: $IDS"
# shellcheck disable=SC2086
awsr ec2 terminate-instances --instance-ids $IDS \
  --query 'TerminatingInstances[].[InstanceId,CurrentState.Name]' --output text
