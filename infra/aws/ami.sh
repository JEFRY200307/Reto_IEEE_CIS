#!/usr/bin/env bash
# Crea la AMI propia a partir de la instancia de preparación (lanzada con --template prep --keep-alive)
# y después la termina. Ver guía de despliegue §8.5 y ADR-15.
#
# Uso: infra/aws/ami.sh <instance-id> [nombre]
#   nombre  por defecto dsqa-base-AAAAMMDD-HHMM
source "$(dirname "$0")/lib.sh"

INSTANCE_ID="${1:-}"
[[ "$INSTANCE_ID" =~ ^i-[0-9a-f]+$ ]] || { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
NAME="${2:-dsqa-base-$(date -u +%Y%m%d-%H%M)}"

require aws
load_config

SESSION_TAG="$(awsr ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].Tags[?Key==`Session`]|[0].Value' --output text)"
log "instancia $INSTANCE_ID (sesión $SESSION_TAG)"

# La preparación debe haber terminado (SUMMARY.txt en S3) para no capturar una instalación a medias.
if ! awsr s3 ls "s3://$DSQA_BUCKET/runs/$SESSION_TAG/SUMMARY.txt" >/dev/null 2>&1; then
  die "la sesión $SESSION_TAG no ha terminado (no hay SUMMARY.txt). Espera y revisa infra/aws/pull.sh $SESSION_TAG"
fi

log "creando la AMI $NAME (sin reiniciar la instancia)"
AMI_ID="$(awsr ec2 create-image --instance-id "$INSTANCE_ID" --name "$NAME" --no-reboot \
  --description "dsqa: AMI base de DLAMI + entorno Python del reto" \
  --tag-specifications "ResourceType=image,Tags=[{Key=Project,Value=$PROJECT_TAG}]" "ResourceType=snapshot,Tags=[{Key=Project,Value=$PROJECT_TAG}]" \
  --query ImageId --output text)"
log "AMI $AMI_ID en creación; esperando a que esté disponible (suele tardar 10-20 min)"

for _ in $(seq 1 120); do
  state="$(awsr ec2 describe-images --image-ids "$AMI_ID" --query 'Images[0].State' --output text)"
  case "$state" in
    available) break ;;
    failed|error) die "la creación de la AMI falló (estado: $state)" ;;
  esac
  sleep 20
done
[[ "$state" == "available" ]] || die "la AMI no estuvo lista a tiempo; revisa la consola (estado: $state)"

log "AMI lista: $AMI_ID. Terminando la instancia de preparación"
awsr ec2 terminate-instances --instance-ids "$INSTANCE_ID" --query 'TerminatingInstances[0].CurrentState.Name' --output text

cat >&2 <<EOF

Siguientes pasos:
  1. En dsqa-infra/envs/dev/terraform.tfvars:   custom_ami_id = "$AMI_ID"
  2. terraform apply   (las plantillas p5 y g6e pasan a usar la AMI)
  3. Las AMI viejas se borran a mano (EC2 → AMIs → Deregister, y su snapshot)
EOF
echo "$AMI_ID"
