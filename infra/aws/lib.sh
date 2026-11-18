#!/usr/bin/env bash
# Funciones comunes de los scripts que se ejecutan en la laptop (Git Bash, WSL, Linux o macOS).
# Uso: source "$(dirname "$0")/lib.sh"

set -euo pipefail

AWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$AWS_DIR/../.." && pwd)"
PROJECT_TAG="dsqa"

log()  { printf '\033[1;34m[dsqa]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[1;33m[dsqa] aviso:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[dsqa] error:\033[0m %s\n' "$*" >&2; exit 1; }

require() {
  local cmd
  for cmd in "$@"; do
    command -v "$cmd" >/dev/null 2>&1 || die "falta el comando '$cmd'"
  done
}

load_config() {
  local cfg="$AWS_DIR/config.env"
  [[ -f "$cfg" ]] || die "no existe $cfg. Genéralo con dsqa-infra (terraform output -raw config_env) o copia config.env.example."
  # El archivo puede venir de Windows con CRLF.
  # shellcheck disable=SC1090
  source <(tr -d '\r' < "$cfg")
  : "${AWS_REGION:?falta AWS_REGION en config.env}"
  : "${DSQA_BUCKET:?falta DSQA_BUCKET en config.env}"
  : "${LAUNCH_TEMPLATE:?falta LAUNCH_TEMPLATE en config.env}"
  MAX_HOURS_DEFAULT="${MAX_HOURS_DEFAULT:-3}"
  export AWS_REGION DSQA_BUCKET
  # Perfil de la CLI del proyecto: evita usar por error las credenciales por defecto de otra cuenta.
  if [[ -n "${AWS_PROFILE:-}" ]]; then
    export AWS_PROFILE
  fi
  check_account
}

# Se detiene si las credenciales activas no son de la cuenta esperada (AWS_ACCOUNT_ID en config.env).
check_account() {
  [[ -n "${AWS_ACCOUNT_ID:-}" ]] || { warn "config.env no define AWS_ACCOUNT_ID: no se comprueba la cuenta"; return 0; }
  local actual
  actual="$(AWS_PAGER="" aws sts get-caller-identity --query Account --output text 2>/dev/null | tr -d '\r')" \
    || die "no se pudieron leer las credenciales (perfil '${AWS_PROFILE:-default}'). ¿Ejecutaste aws configure --profile ${AWS_PROFILE:-dsqa}?"
  [[ "$actual" == "$AWS_ACCOUNT_ID" ]] \
    || die "las credenciales son de la cuenta $actual, pero config.env espera $AWS_ACCOUNT_ID. Revisa AWS_PROFILE."
}

# aws con la región del proyecto y sin paginador interactivo.
awsr() { AWS_PAGER="" aws --region "$AWS_REGION" "$@"; }

# Ruta que entiende aws.exe en Windows; en Linux/macOS la deja igual.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi
}

valid_session() {
  [[ "${1:-}" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]] || die "nombre de sesión inválido '${1:-}': usa minúsculas, números y guiones (p. ej. s04)"
}

# Instancias del proyecto que están encendidas o arrancando.
running_instances() {
  awsr ec2 describe-instances \
    --filters "Name=tag:Project,Values=$PROJECT_TAG" "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[].Instances[].[InstanceId,InstanceType,InstanceLifecycle || `on-demand`,Placement.AvailabilityZone,LaunchTime,Tags[?Key==`Session`]|[0].Value]' \
    --output text
}
