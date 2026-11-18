# 8. Guía de despliegue (AWS + Codabench)

[← Calidad y pruebas](07-calidad-y-pruebas.md) · [Índice](README.md) · Siguiente: [Estrategias implementadas →](09-estrategias-implementadas.md)

Esta guía explica cómo montar el entorno de AWS para correr OLMo 3.1 32B y cómo llevar cada versión del sistema hasta un envío en Codabench, **gastando lo mínimo**. Las decisiones que la justifican están en [ADR-14](ADR/ADR-14-computo-aws-p5-spot.md) a [ADR-17](ADR/ADR-17-control-de-costos-aws.md); los scripts, en [SPEC-031](spec/SPEC-031-ejecucion-remota-aws.md).

## 8.0 La decisión en una tabla

| Tema | Decisión | Por qué |
|---|---|---|
| Dónde se desarrolla | **Laptop** para todo lo que no usa OLMo | Costo 0; es la mayor parte del sistema |
| Dónde corre OLMo | **AWS `p5.4xlarge`** (1× H100 80 GB) | Misma GPU que Codabench: tiempos y resultados comparables |
| Cómo se paga | **Spot primero** (~USD 1,3-2,6/h); on-demand (~USD 6,88/h) solo si no hay capacidad spot | 60-80 % más barato; el hardware es idéntico |
| Cómo se usa | **Sesiones por lotes** de 1-3 h, instancia **desechable** que se termina sola | Solo se paga mientras se trabaja |
| Dónde viven los datos | **S3** (modelo, corpus público, código, resultados) | Barato (~USD 2/mes) y no depende de la zona |
| Preparación única | En una instancia **CPU barata** (~USD 0,2/h), no en la GPU | Descargar 64 GB y crear la AMI no necesita GPU |
| Seguridad | Session Manager + rol IAM; sin puertos abiertos ni claves | Evita que una instancia comprometida genere costos |
| Tope de gasto | Presupuesto de **USD 150** con alertas; apagado a las 3 h; watchdog de inactividad | Un olvido cuesta como mucho 3 h |
| **Gasto esperado** | **~USD 45-70** hasta el 30 nov (≈15-17 h de GPU, con reserva on-demand) | Ver [ADR-17](ADR/ADR-17-control-de-costos-aws.md) |

> Los precios son de referencia (trackers públicos, datos de abril-julio 2026). Antes de lanzar, confirma el precio actual en la consola de EC2 o con el comando de §8.7.

> **Terraform (opcional, [ADR-18](ADR/ADR-18-terraform-repo-separado.md)):** los recursos permanentes de los pasos 2 a 6 (bucket, rol IAM, security group, launch templates, presupuesto y alertas) pueden crearse con el repositorio separado `dsqa-infra` en lugar de los comandos de esta guía. Las cuotas (§8.2), la AMI y la subida del modelo (§8.5) y las sesiones (§8.7) siguen igual. Si la infraestructura ya se creó a mano, se migra después con bloques `import`, sin recrearla.

```
Laptop ──push──▶ S3 ◀──sync──▶ Instancia p5.4xlarge (spot, desechable)
  ▲              │                 │  bootstrap → trabajos → resultados → se termina sola
  └────pull──────┘                 │
                                   ▼
                       Resultados en S3 → laptop → decisión → zip → Codabench (1/día)
```

## 8.1 Requisitos en la laptop

| Herramienta | Para qué | Comprobar |
|---|---|---|
| AWS CLI v2 | Todos los comandos de esta guía | `aws --version` |
| Session Manager plugin | Abrir una terminal en la instancia sin SSH | `session-manager-plugin --version` |
| Python ≥ 3.10 + `requirements-dev.txt` | Desarrollo, pruebas, calibración | `python --version` |
| Git | Versionar y etiquetar envíos | `git --version` |

En Windows, los scripts `.sh` se ejecutan desde **Git Bash** (o WSL).

## 8.2 Paso 1: cuenta y cuotas (hacerlo hoy)

Las cuotas de instancias GPU suelen ser **0** en cuentas nuevas y su aprobación puede tardar **de horas a varios días**. Es el paso más urgente.

1. **Plan de la cuenta.** Si la cuenta está en el plan gratuito (*Free plan*), las instancias GPU no están disponibles: hay que pasar al plan de pago (*Paid plan*) en *Billing*. Según AWS, los créditos promocionales que tengas se conservan; verifícalo en *Billing → Credits*.
2. **Usuarios.** No trabajes con el usuario raíz: crea un usuario por miembro (IAM Identity Center o IAM), con MFA, y configura la CLI:
   ```bash
   aws configure sso
   ```
   (o `aws configure` con las claves del usuario IAM, guardadas solo en la laptop).
3. **Comprobar que la región ofrece p5.4xlarge:**
   ```bash
   aws ec2 describe-instance-type-offerings --region us-east-1 --location-type availability-zone --filters Name=instance-type,Values=p5.4xlarge --query "InstanceTypeOfferings[].Location" --output text
   ```
4. **Pedir las cuotas** (en vCPU; p5.4xlarge usa 16). Los códigos son los habituales de EC2; confírmalos en *Service Quotas → Amazon EC2* si un comando falla:

| Cuota | Código | Pedir |
|---|---|---|
| All P Spot Instance Requests | `L-7212CCBC` | 16 |
| Running On-Demand P instances | `L-417A185B` | 16 |
| All G and VT Spot Instance Requests (plan B) | `L-3819A6DF` | 8 |
| Running On-Demand G and VT instances (plan B) | `L-DB2E81BA` | 8 |

   ```bash
   aws service-quotas request-service-quota-increase --region us-east-1 --service-code ec2 --quota-code L-7212CCBC --desired-value 16
   ```
   ```bash
   aws service-quotas request-service-quota-increase --region us-east-1 --service-code ec2 --quota-code L-417A185B --desired-value 16
   ```
   En la justificación (si la piden): *"Research project for the IEEE CIS Technical Challenge on Domain-Specific QA with LLMs. Need 1 H100 (p5.4xlarge) for short batch sessions of up to 3 hours to evaluate a 32B open model, until Nov 30, 2026."*
5. **Seguir el estado:**
   ```bash
   aws service-quotas list-requested-service-quota-change-history --region us-east-1 --service-code ec2 --query "RequestedQuotas[].[QuotaName,Status,DesiredValue]" --output table
   ```

## 8.3 Paso 2: control de costos (antes de lanzar nada)

1. **Presupuesto:** consola → *Billing and Cost Management → Budgets → Create budget → Cost budget*:
   - Monto mensual: **USD 150**.
   - Alertas por correo: 50 %, 80 % y 100 % del costo **real**, y 100 % del costo **pronosticado**.
   - Destinatarios: todos los miembros del equipo.
2. **Alertas de anomalías:** *Cost Anomaly Detection* → crear un monitor por servicio con alerta por correo.
3. **Registro de sesiones:** crea `experiments/aws-sessions.md` con columnas *fecha, sesión, tipo (spot/on-demand), horas, costo estimado, resultado*.

## 8.4 Paso 3: bucket, rol IAM y red

Define tus nombres una sola vez en `infra/aws/config.env`:
```bash
AWS_REGION=us-east-1
DSQA_BUCKET=dsqa-<equipo>-2026          # nombre único global, en minúsculas
LAUNCH_TEMPLATE=dsqa-p5
MAX_HOURS_DEFAULT=3
```

1. **Bucket privado** (bloqueo de acceso público activado por defecto):
   ```bash
   aws s3 mb s3://$DSQA_BUCKET --region $AWS_REGION
   ```
2. **Rol de la instancia** con solo dos permisos ([ADR-16](ADR/ADR-16-acceso-seguro-aws.md)):
   - `trust-ec2.json`:
     ```json
     {"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
     ```
   - `bucket-policy.json` (reemplaza el nombre del bucket):
     ```json
     {"Version":"2012-10-17","Statement":[
       {"Effect":"Allow","Action":["s3:ListBucket"],"Resource":"arn:aws:s3:::dsqa-<equipo>-2026"},
       {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::dsqa-<equipo>-2026/*"}]}
     ```
   - Crear el rol y el perfil:
     ```bash
     aws iam create-role --role-name dsqa-ec2 --assume-role-policy-document file://trust-ec2.json
     aws iam attach-role-policy --role-name dsqa-ec2 --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
     aws iam put-role-policy --role-name dsqa-ec2 --policy-name dsqa-bucket --policy-document file://bucket-policy.json
     aws iam create-instance-profile --instance-profile-name dsqa-ec2
     aws iam add-role-to-instance-profile --instance-profile-name dsqa-ec2 --role-name dsqa-ec2
     ```
3. **Security group sin entradas** en la VPC por defecto (la salida queda abierta para S3, SSM y Hugging Face):
   ```bash
   aws ec2 create-security-group --region $AWS_REGION --group-name dsqa-no-ingress --description "dsqa: no inbound"
   ```

## 8.5 Paso 4: preparación única en una instancia CPU barata

> **Atajo con los scripts:** todo este paso se automatiza con `infra/aws/push.sh prep`, `infra/aws/launch.sh prep --template prep --keep-alive --max-hours 2` y, al terminar, `infra/aws/ami.sh <instance-id>`. Ver [infra/aws/README.md](../../infra/aws/README.md). Lo que sigue es el detalle manual equivalente.

Descargar el modelo y construir la AMI **no necesita GPU**. Se hace una vez en una `m7i.xlarge` (~USD 0,20/h on-demand) usando la AMI base de Deep Learning de AWS, que ya trae los drivers de NVIDIA que luego usará la p5.

1. **Obtener la AMI base** (Ubuntu 22.04 con drivers NVIDIA; verifica el nombre del parámetro en la documentación de DLAMI si cambia):
   ```bash
   aws ssm get-parameter --region $AWS_REGION --name /aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id --query Parameter.Value --output text
   ```
2. **Lanzar la instancia de preparación** (disco de 200 GB, rol `dsqa-ec2`, security group `dsqa-no-ingress`, apagado = terminar) y entrar con:
   ```bash
   aws ssm start-session --region $AWS_REGION --target <instance-id>
   ```
3. **Dentro de la instancia:**
   ```bash
   sudo shutdown -h +120                                   # seguro: se termina a las 2 h
   python3 -m venv /opt/dsqa-venv && source /opt/dsqa-venv/bin/activate
   aws s3 cp s3://$DSQA_BUCKET/code/requirements-runtime.txt .   # subido antes con push.sh
   pip install -r requirements-runtime.txt "cma" "pytest"
   hf download allenai/Olmo-3.1-32B-Instruct                     # ~64 GB a ~/.cache/huggingface/hub
   python -c "from sentence_transformers import SentenceTransformer as S; S('BAAI/bge-base-en-v1.5')"
   python -c "from FlagEmbedding import FlagReranker as R; R('BAAI/bge-reranker-base')"
   aws s3 sync ~/.cache/huggingface/hub s3://$DSQA_BUCKET/hf-cache/
   ```
4. **Quitar los pesos del disco antes de crear la AMI** (los pesos viven en S3, no en la AMI — [ADR-15](ADR/ADR-15-instancias-desechables-y-s3.md)):
   ```bash
   rm -rf ~/.cache/huggingface/hub/models--*
   ```
5. **Crear la AMI** desde la laptop y terminar la instancia:
   ```bash
   aws ec2 create-image --region $AWS_REGION --instance-id <instance-id> --name dsqa-base-2026-10-30 --no-reboot
   aws ec2 terminate-instances --region $AWS_REGION --instance-ids <instance-id>
   ```

Costo de este paso: ~1 h de `m7i.xlarge` ≈ USD 0,20 + almacenamiento de S3 y AMI ≈ USD 4/mes.

## 8.6 Paso 5: launch template de la GPU

Una sola plantilla con todo lo que debe cumplirse siempre (`launch-template.json`):
```json
{
  "ImageId": "<ami-de-dsqa-base>",
  "InstanceType": "p5.4xlarge",
  "IamInstanceProfile": {"Name": "dsqa-ec2"},
  "SecurityGroupIds": ["<sg-dsqa-no-ingress>"],
  "InstanceInitiatedShutdownBehavior": "terminate",
  "MetadataOptions": {"HttpTokens": "required"},
  "BlockDeviceMappings": [{"DeviceName": "/dev/sda1",
    "Ebs": {"VolumeSize": 200, "VolumeType": "gp3", "DeleteOnTermination": true}}],
  "TagSpecifications": [{"ResourceType": "instance", "Tags": [{"Key": "Project", "Value": "dsqa"}]}]
}
```
```bash
aws ec2 create-launch-template --region $AWS_REGION --launch-template-name dsqa-p5 --launch-template-data file://launch-template.json
```

Puntos clave: **`terminate` al apagarse** (nada queda detenido cobrando disco), **disco que se borra** al terminar, **IMDSv2** obligatorio, **etiqueta** `Project=dsqa` para encontrar y contar las instancias.

## 8.7 Paso 6: ciclo de una sesión de trabajo

Cada sesión sigue siempre los mismos 6 pasos. Ejemplo: sesión `s04` para comparar E3 y E4.

**1. Preparar en la laptop** la lista de trabajos `infra/aws/jobs/s04.txt`:
```text
python eval/run_local.py --configs configs/e3.yaml configs/e4.yaml --bench eval/bench --corpus data/public_pdfs --model-id allenai/Olmo-3.1-32B-Instruct --out experiments/runs/s04 --resume --sync-s3 s3://$DSQA_BUCKET/runs/s04
python eval/judge.py --run experiments/runs/s04/e3 --backend olmo
python eval/judge.py --run experiments/runs/s04/e4 --backend olmo
```
Antes de subir: pruebas unitarias en verde y la lista revisada. Nada de "abrir la instancia para ver qué pasa".

**2. Revisar el precio spot del momento** (elige la AZ más barata):
```bash
aws ec2 describe-spot-price-history --region $AWS_REGION --instance-types p5.4xlarge --product-descriptions "Linux/UNIX" --start-time $(date -u +%Y-%m-%dT%H:%M:%S) --query "SpotPriceHistory[].[AvailabilityZone,SpotPrice]" --output table
```

**3. Subir y lanzar:**
```bash
infra/aws/push.sh s04
```
```bash
infra/aws/launch.sh s04 --max-hours 3
```
`launch.sh` pide spot; si no hay capacidad, prueba otras zonas. Usa `--on-demand` solo si es urgente.

**4. Seguir** (opcional):
```bash
infra/aws/status.sh
```
Para mirar los logs en vivo: `aws ssm start-session --target <instance-id>` y luego `tail -f ~/logs/*.log`.

**5. La instancia se termina sola** al acabar los trabajos, a las 3 h o tras 20 min de GPU inactiva.

**6. Bajar resultados y cerrar:**
```bash
infra/aws/pull.sh s04
```
```bash
aws ec2 describe-instances --region $AWS_REGION --filters Name=tag:Project,Values=dsqa Name=instance-state-name,Values=pending,running --query "Reservations[].Instances[].InstanceId" --output text
```
El último comando debe devolver **vacío**. Anota la sesión en `experiments/aws-sessions.md`.

**Si una instancia spot se interrumpe:** los resultados hasta ese momento ya están en S3. Relanza la misma sesión (`launch.sh s04`); `--resume` continúa donde quedó.

## 8.8 Paso 7: despliegue en Codabench (cada envío)

| # | Paso | Comando / acción |
|---|---|---|
| 1 | Elegir la config y etiquetar el commit | `git tag sub-2026-11-10` |
| 2 | Construir el zip | `python scripts/build_submission.py --config configs/e4.yaml --out dist/` |
| 3 | Chequeo estático | `python scripts/check_submission.py dist/dsqa_e4_2026-11-10.zip` |
| 4 | **Ensayo general en AWS** (para cambios grandes o la versión final): el zip descomprimido en una carpeta limpia, sin red, con OLMo real y 50 preguntas cronometradas | Línea en `jobs/<sesion>.txt`: `python scripts/check_submission.py dist/<zip> --smoke --model-id allenai/Olmo-3.1-32B-Instruct --corpus data/public_pdfs --n 50 --timed` |
| 5 | Confirmar el tiempo del ensayo | ≤ 45 min para 50 preguntas (con 16 vCPU la ingesta es más lenta que en Codabench: el tiempo real será igual o menor) |
| 6 | Subir el zip en Codabench | *Competition → My Submissions → Upload*, antes de las **23:55 UTC (18:55 en Perú)** |
| 7 | Adjuntar el borrador de metodología | Donde lo pida el formulario de envío |
| 8 | Registrar el resultado | Fila en `experiments/submissions.md` (estado, precisión, tiempo) |

La lista completa de "listo para enviar" está en [§6.3](06-criterios-de-aceptacion.md#63-definición-de-listo-para-enviar).

## 8.9 Plan de sesiones hasta el 30 nov

| Sesión | Fecha objetivo | Tipo | Trabajo | Horas aprox. |
|---|---|---|---|---|
| S0 | 30-31 oct | CPU `m7i.xlarge` | Preparación única: modelo a S3 y AMI | 1 |
| S1 | 1-2 nov | p5 spot | Humo de punta a punta; E0 y E1 en el banco; tiempos por etapa | 1,5 |
| S2 | 3-5 nov | p5 spot | Generar QA sintético ([SPEC-028](spec/SPEC-028-banco-local-y-qa-sintetico.md)) | 1,5 |
| S3 | 6-8 nov | p5 spot | E1 vs E2 (+ juez local) | 1,5 |
| S4 | 9-11 nov | p5 spot | E3 vs E4; ensayo general del zip E4 | 2 |
| S5 | 12-15 nov | p5 spot | Caché de señales con $s_5$ para CMA-ES ([SPEC-029](spec/SPEC-029-calibracion-cmaes.md)) | 1,5 |
| — | 15-18 nov | Laptop | Calibración CMA-ES (sin GPU) | 0 |
| S6 | 18-20 nov | p5 spot | E5 vs E6 calibrado | 1,5 |
| S7 | 20-22 nov | p5 spot | Ablación leave-one-out | 2 |
| S8 | 23-26 nov | p5 spot | Ensayo general de la versión candidata | 1 |
| S9 | 27-29 nov | p5 spot u on-demand | Ensayo de la versión final (on-demand si no hay spot) | 1 |
| Reserva | — | — | Repetir una sesión interrumpida o fallida | 1-2 |
| **Total** | | | | **≈ 15-17 h de GPU** |

Con spot (~USD 1,3-2,6/h): **~USD 20-45**. Con todo on-demand: **~USD 105-115**. Más S3 y AMI: ~USD 4.

## 8.10 Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `VcpuLimitExceeded` / `MaxSpotInstanceCountExceeded` | Cuota aún en 0 | Revisar §8.2; mientras tanto, plan B `g6e.2xlarge` en 4 bits solo para pruebas funcionales |
| `InsufficientInstanceCapacity` | No hay H100 spot en esa zona | Otra AZ u otra región (`us-east-2`, `us-west-2`); si es urgente, `--on-demand` |
| `start-session` no conecta | Falta el plugin, el rol o salida a internet | Verificar el plugin local, que el perfil sea `dsqa-ec2` y que la subred asigne IP pública |
| `LocalEntryNotFoundError` al cargar OLMo | La caché de S3 no está en la ruta esperada | Comprobar `~/.cache/huggingface/hub/models--allenai--Olmo-3.1-32B-Instruct`; respaldo: `hf download` |
| `No space left on device` | Disco raíz pequeño | Subir `VolumeSize` en la plantilla (cada 100 GB gp3 ≈ USD 0,01/h) |
| `CUDA out of memory` | Contexto demasiado largo | Bajar `context.max_tokens`; revisar el pico de VRAM en la traza |
| La instancia sigue viva tras la sesión | Un trabajo colgado mantiene la GPU ocupada | `aws ec2 terminate-instances --instance-ids <id>`; revisar el log del trabajo |
| La factura sube más de lo esperado | Instancia olvidada, volúmenes o snapshots huérfanos | *Cost Explorer* por servicio; borrar volúmenes `available` y AMIs viejas |

## 8.11 Limpieza al terminar el reto

Cuando el reto termine (después del ranking final o de la Fase 2):

1. Descargar a la laptop lo que quieras conservar de `s3://<bucket>/runs/`.
2. Vaciar y borrar el bucket:
   ```bash
   aws s3 rb s3://$DSQA_BUCKET --force
   ```
3. Dar de baja la AMI y borrar su snapshot (*EC2 → AMIs → Deregister*, luego *Snapshots → Delete*).
4. Borrar la launch template, el security group, el rol y el perfil de instancia. Con Terraform: poner `force_destroy = true` en el bucket y ejecutar `terraform destroy` en `envs/dev/` (la AMI y su snapshot se borran a mano, como en el punto 3).
5. Comprobar en *Cost Explorer* que el gasto diario baja a 0 y dejar el presupuesto activo un mes más.
