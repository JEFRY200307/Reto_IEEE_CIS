# SPEC-031: Ejecución remota en AWS

**Módulo:** `infra/aws/` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-OF-08, RF-OF-09, RNF-CS-01..04 · **Criterios:** CA-AWS-01..04 · **ADR:** ADR-14, ADR-15, ADR-16, ADR-17 · **Guía:** [08-guia-de-despliegue.md](../08-guia-de-despliegue.md)

## Propósito
Ejecutar una sesión de trabajo con OLMo en una instancia GPU desechable, con un solo comando, y garantizar que la instancia se termina sola.

## Interfaz
```
infra/aws/
├── config.env            # Región, bucket, nombre de la launch template, presupuesto (sin secretos)
├── push.sh               # Sube código, configs, banco y la lista de trabajos a S3
├── launch.sh             # Crea la instancia (spot primero, on-demand con --on-demand)
├── bootstrap.sh          # user data: prepara la instancia y ejecuta los trabajos
├── watchdog.sh           # Termina la instancia si la GPU está inactiva 20 min
├── jobs/<sesion>.txt     # Lista de comandos de la sesión (uno por línea)
├── pull.sh               # Descarga los resultados de S3 a experiments/runs/
└── status.sh             # Lista instancias del proyecto en ejecución y su costo/hora
```

```bash
infra/aws/push.sh s04
infra/aws/launch.sh s04 [--on-demand] [--max-hours 3]
infra/aws/status.sh
infra/aws/pull.sh s04
```

## Comportamiento
1. **`push.sh <sesion>`:** `aws s3 sync` del repositorio (sin `models/`, `data/`, `experiments/runs/`) a `s3://<bucket>/code/` y de `jobs/<sesion>.txt`.
2. **`launch.sh <sesion>`:** `aws ec2 run-instances` con la launch template `dsqa-p5`, etiqueta `Project=dsqa, Session=<sesion>`, `--instance-market-options` spot (salvo `--on-demand`) y user data que pasa la sesión y `--max-hours`. Si spot falla por capacidad (`InsufficientInstanceCapacity`), prueba las otras AZ de la región y, si se indicó `--fallback-on-demand`, on-demand.
3. **`bootstrap.sh`** (en la instancia):
   1. `shutdown -h +<max_hours*60>` (la launch template termina la instancia al apagarse).
   2. Instalar el cron del `watchdog.sh`.
   3. `aws s3 sync s3://<bucket>/hf-cache/ ~/.cache/huggingface/hub/`, `code/`, `corpus/`.
   4. Activar el entorno de la AMI; exportar `HF_HUB_OFFLINE=1`.
   5. Ejecutar cada línea de `jobs/<sesion>.txt` en orden, con salida a `logs/`; un trabajo que falla no detiene los siguientes.
   6. `aws s3 sync` de `experiments/runs/` y `logs/` a `s3://<bucket>/runs/<sesion>/`.
   7. `shutdown -h now`.
4. **`watchdog.sh`:** cada 5 min lee `nvidia-smi --query-gpu=utilization.gpu`; si es < 5 % durante 4 lecturas seguidas y no hay trabajos en curso, sincroniza resultados y apaga.
5. **Interrupción spot:** el script consulta los metadatos de la instancia (`/latest/meta-data/spot/instance-action`) cada minuto; al recibir el aviso (2 min), sincroniza resultados con S3. La sesión se relanza con el mismo nombre y `run_local --resume` continúa.

## Reglas y casos borde
- Ningún script contiene credenciales; la instancia usa su rol IAM ([ADR-16](../ADR/ADR-16-acceso-seguro-aws.md)).
- `launch.sh` se niega a lanzar si `status.sh` ya muestra una instancia del proyecto en ejecución (evita duplicados olvidados), salvo con `--force`.
- `--max-hours` > 4 exige `--force`.

## Configuración (`infra/aws/config.env`)
Lo genera `dsqa-infra` con `terraform output -raw config_env` ([ADR-18](../ADR/ADR-18-terraform-repo-separado.md)), o se escribe a mano.

| Variable | Ejemplo |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `DSQA_BUCKET` | `dsqa-data-<id de la cuenta>` |
| `LAUNCH_TEMPLATE` | `dsqa-p5` |
| `LAUNCH_TEMPLATE_FALLBACK` | `dsqa-g6e` (plan B, 4 bits) |
| `LAUNCH_TEMPLATE_PREP` | `dsqa-prep` (preparación sin GPU) |
| `INSTANCE_PROFILE` | `dsqa-ec2` |
| `MAX_HOURS_DEFAULT` | `3` |

## Errores y respaldo
- Falla la copia de `hf-cache` desde S3 → descarga desde Hugging Face (`hf download`) y continúa.
- Falla un trabajo → se registra en `logs/` y se sigue con el siguiente.

## Pruebas
- Ejecución en seco (`--dry-run`) de `launch.sh` muestra el comando sin lanzar nada.
- Sesión de prueba de 15 min con `jobs/smoke.txt` → resultados en S3 e instancia terminada sola.
- Simular inactividad → el watchdog apaga en ≤ 25 min.
