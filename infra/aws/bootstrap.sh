#!/bin/bash
# Se ejecuta EN LA INSTANCIA al arrancar (user data de cloud-init, como root).
# launch.sh antepone las variables de la sesión (DSQA_*) y el watchdog. No ejecutar en la laptop.
#
# Pasos: seguro de tiempo → watchdog → código → entorno Python → modelo → trabajos → resultados → apagado.
# Resultados en s3://$DSQA_BUCKET/runs/$DSQA_SESSION/ (los trabajos escriben en experiments/runs/$DSQA_SESSION/).
set -uo pipefail

export HOME=/root
export PATH=/opt/dsqa-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
LOG=/var/log/dsqa-bootstrap.log
exec > >(tee -a "$LOG") 2>&1
say() { echo "[dsqa] $(date -u +%H:%M:%S) $*"; }

: "${DSQA_SESSION:?}" "${DSQA_BUCKET:?}" "${AWS_REGION:?}" "${DSQA_MAX_HOURS:?}"
DSQA_KEEP_ALIVE="${DSQA_KEEP_ALIVE:-false}"
DSQA_OFFLINE="${DSQA_OFFLINE:-true}"
DSQA_MODEL_ID="${DSQA_MODEL_ID:-allenai/Olmo-3.1-32B-Instruct}"

say "inicio de la sesión $DSQA_SESSION (máx. ${DSQA_MAX_HOURS} h, keep-alive=$DSQA_KEEP_ALIVE)"

# --- 1. Seguro de tiempo: la plantilla convierte el apagado en terminación ----------------------
shutdown -h "+$(( DSQA_MAX_HOURS * 60 ))" "dsqa: límite de ${DSQA_MAX_HOURS} h" || true

# --- 2. Rutas y marca de "trabajando" (el watchdog no apaga mientras este proceso viva) ---------
WORK=/opt/dsqa
REPO=$WORK/repo
RUNS=$REPO/experiments/runs
SESSION_DIR=$RUNS/$DSQA_SESSION
ATTEMPT=$(date -u +%Y%m%dT%H%M%SZ)
LOGS=$SESSION_DIR/logs/$ATTEMPT
S3=s3://$DSQA_BUCKET
export HF_HOME=$WORK/hf
export HF_HUB_CACHE=$HF_HOME/hub
export DSQA_SESSION DSQA_BUCKET AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"
mkdir -p "$REPO" "$HF_HUB_CACHE"
echo $$ > /run/dsqa-busy

command -v aws >/dev/null 2>&1 || { say "instalando AWS CLI"; snap install aws-cli --classic; }
# Más concurrencia y partes grandes: el modelo (~64 GB) baja de S3 en pocos minutos.
aws configure set default.s3.max_concurrent_requests 64
aws configure set default.s3.multipart_chunksize 64MB

# Sincronización de resultados, usada por el bucle periódico, el aviso spot y el watchdog.
cat > /usr/local/bin/dsqa-sync.sh <<EOF
#!/bin/bash
export PATH=/usr/local/bin:/usr/bin:/bin:/snap/bin HOME=/root
mkdir -p "$LOGS"
cp -f "$LOG" "$LOGS/bootstrap.log" 2>/dev/null
aws s3 sync "$RUNS/" "$S3/runs/" --only-show-errors
EOF
chmod +x /usr/local/bin/dsqa-sync.sh

# --- 3. Watchdog de inactividad (no en keep-alive: la instancia debe vivir para crear la AMI) --
if [[ "$DSQA_KEEP_ALIVE" != "true" ]]; then
  echo "*/5 * * * * root /usr/local/bin/dsqa-watchdog.sh >> /var/log/dsqa-watchdog.log 2>&1" > /etc/cron.d/dsqa-watchdog
  chmod 644 /etc/cron.d/dsqa-watchdog
fi

# --- 4. Aviso de interrupción spot (2 min de margen): guardar resultados ----------------------
(
  while true; do
    token=$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
    code=$(curl -s -m 2 -o /dev/null -w '%{http_code}' -H "X-aws-ec2-metadata-token: $token" \
      http://169.254.169.254/latest/meta-data/spot/instance-action)
    if [[ "$code" == "200" ]]; then
      say "AVISO DE INTERRUPCIÓN SPOT: guardando resultados en S3"
      /usr/local/bin/dsqa-sync.sh
      exit 0
    fi
    sleep 20
  done
) &

# --- 5. Código, corpus y resultados previos de la sesión (para --resume) ------------------------
say "descargando código"
aws s3 sync "$S3/code/" "$REPO/" --only-show-errors --delete --exclude "experiments/runs/*" --exclude "data/*"
say "descargando corpus público (si existe)"
aws s3 sync "$S3/corpus/" "$REPO/data/public_pdfs/" --only-show-errors
say "recuperando resultados anteriores de la sesión (si existen)"
aws s3 sync "$S3/runs/$DSQA_SESSION/" "$SESSION_DIR/" --only-show-errors --exclude "logs/*" --exclude "SUMMARY.txt"
mkdir -p "$LOGS"

# Copia periódica de resultados cada 5 min.
( while true; do sleep 300; /usr/local/bin/dsqa-sync.sh; done ) &
SYNC_LOOP=$!

# --- 6. Entorno Python (ya viene en la AMI propia; si no, se crea aquí) ------------------------
if [[ -x /opt/dsqa-venv/bin/python ]]; then
  say "entorno Python de la AMI: /opt/dsqa-venv"
else
  say "creando entorno Python (AMI base: tarda varios minutos)"
  python3 -m venv /opt/dsqa-venv 2>/dev/null || {
    apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv && python3 -m venv /opt/dsqa-venv
  }
  /opt/dsqa-venv/bin/pip install -q --upgrade pip
  for req in requirements-runtime.txt requirements-dev.txt; do
    if [[ -f "$REPO/$req" ]]; then
      say "instalando $req"
      /opt/dsqa-venv/bin/pip install -q -r "$REPO/$req" || say "AVISO: falló la instalación de $req"
    else
      say "AVISO: no existe $req en el repo"
    fi
  done
  /opt/dsqa-venv/bin/pip install -q "huggingface_hub[cli]" || true
fi
# shellcheck disable=SC1091
source /opt/dsqa-venv/bin/activate

# --- 7. Pesos del modelo: desde S3 (rápido) y, si faltan, desde Hugging Face --------------------
say "descargando caché de modelos desde S3"
aws s3 sync "$S3/hf-cache/" "$HF_HUB_CACHE/" --only-show-errors
MODEL_DIR="$HF_HUB_CACHE/models--${DSQA_MODEL_ID//\//--}"
if [[ ! -d "$MODEL_DIR/snapshots" ]]; then
  say "el modelo no está en S3: descargando $DSQA_MODEL_ID desde Hugging Face"
  HF_HUB_OFFLINE=0 hf download "$DSQA_MODEL_ID" || say "AVISO: falló la descarga del modelo"
fi
du -sh "$HF_HUB_CACHE" 2>/dev/null | sed 's/^/[dsqa] caché de modelos: /'

if [[ "$DSQA_OFFLINE" == "true" ]]; then
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # igual que en Codabench
fi

# --- 8. Trabajos de la sesión: uno por línea; un fallo no detiene los siguientes ----------------
aws s3 cp "$S3/jobs/$DSQA_SESSION.txt" "$WORK/jobs.txt" --only-show-errors
cd "$REPO" || exit 1
SUMMARY=$SESSION_DIR/SUMMARY.txt
token=$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
md() { curl -s -m 2 -H "X-aws-ec2-metadata-token: $token" "http://169.254.169.254/latest/meta-data/$1"; }
{
  echo "Sesión:     $DSQA_SESSION (intento $ATTEMPT)"
  echo "Instancia:  $(md instance-id) $(md instance-type) $(md instance-life-cycle) $(md placement/availability-zone)"
  echo "Inicio:     $(date -u +%FT%TZ)"
  echo
  echo "N   rc   seg    comando"
} > "$SUMMARY"

n=0
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%$'\r'}"
  trimmed="${line#"${line%%[![:space:]]*}"}"
  [[ -z "$trimmed" || "$trimmed" == \#* ]] && continue
  n=$((n + 1))
  joblog=$(printf '%s/job-%02d.log' "$LOGS" "$n")
  say "trabajo $n: $trimmed"
  start=$(date +%s)
  bash -c "$trimmed" > "$joblog" 2>&1 < /dev/null
  rc=$?
  printf '%-3s %-4s %-6s %s\n' "$n" "$rc" "$(( $(date +%s) - start ))" "$trimmed" >> "$SUMMARY"
  say "trabajo $n terminó con rc=$rc"
  /usr/local/bin/dsqa-sync.sh
done < "$WORK/jobs.txt"

{
  echo
  echo "Fin:        $(date -u +%FT%TZ)"
  echo "Trabajos:   $n (ver logs/$ATTEMPT/)"
} >> "$SUMMARY"

# --- 9. Resultados finales y apagado ------------------------------------------------------------
kill "$SYNC_LOOP" 2>/dev/null
rm -f /run/dsqa-busy
say "subiendo resultados finales"
/usr/local/bin/dsqa-sync.sh

if [[ "$DSQA_KEEP_ALIVE" == "true" ]]; then
  say "keep-alive: la instancia sigue encendida (se termina sola al llegar a ${DSQA_MAX_HOURS} h)"
else
  say "sesión terminada: apagando (la instancia se termina)"
  shutdown -h now "dsqa: sesión terminada"
fi
