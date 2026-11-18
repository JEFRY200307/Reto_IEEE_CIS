# infra/aws — sesiones de trabajo en AWS

Scripts para correr OLMo 3.1 32B en una instancia GPU **desechable**: se sube el trabajo a S3, se lanza la instancia, esta ejecuta la lista de comandos, guarda los resultados en S3 y **se termina sola**.

- Especificación: [SPEC-031](../../docs/documentacion-tecnica/spec/SPEC-031-ejecucion-remota-aws.md)
- Decisiones: [ADR-14 a ADR-18](../../docs/documentacion-tecnica/ADR/README.md)
- Guía completa: [08-guia-de-despliegue.md](../../docs/documentacion-tecnica/08-guia-de-despliegue.md)
- Los recursos permanentes (bucket, rol, plantillas, presupuesto) los crea el repositorio aparte `dsqa-infra` con Terraform.

## Archivos

| Archivo | Dónde corre | Qué hace |
|---|---|---|
| `config.env` | — | Región, bucket y plantillas. Lo genera `dsqa-infra` (`terraform output -raw config_env`); no se sube a git |
| `config.env.example` | — | Ejemplo para escribirlo a mano |
| `lib.sh` | Laptop | Funciones comunes de los scripts |
| `push.sh <sesión>` | Laptop | Sube código, `jobs/<sesión>.txt` y `data/public_pdfs/` a S3 |
| `launch.sh <sesión>` | Laptop | Lanza la instancia (spot primero, probando todas las zonas) |
| `status.sh` | Laptop | Lista instancias encendidas, horas que llevan y sesiones con resultados |
| `stop.sh <sesión>\|--all` | Laptop | Termina instancias a mano |
| `pull.sh <sesión>` | Laptop | Baja resultados y logs a `experiments/runs/<sesión>/` y muestra el resumen |
| `ami.sh <instance-id>` | Laptop | Crea la AMI propia desde la instancia de preparación y la termina |
| `bootstrap.sh` | Instancia | User data: prepara la máquina, ejecuta los trabajos, sube resultados, apaga |
| `watchdog.sh` | Instancia | Cada 5 min: si no hay trabajo y la GPU está inactiva 20 min, guarda y apaga |
| `jobs/*.txt` | Instancia | Listas de trabajos: `prep.txt` (preparación), `smoke.txt` (prueba de humo) |

## Requisitos en la laptop

- AWS CLI v2 con tus credenciales (`aws sts get-caller-identity` debe funcionar).
- *Session Manager plugin* (solo para entrar a la instancia con `aws ssm start-session`).
- Bash: Git Bash en Windows, o WSL, Linux o macOS. Ejecutar desde la raíz del repo.
- `infra/aws/config.env` creado.

## Primera vez: preparación (CPU, ~USD 0,5)

Sube OLMo y los modelos auxiliares a S3 y crea la AMI con el entorno Python instalado.

```bash
infra/aws/push.sh prep
```
```bash
infra/aws/launch.sh prep --template prep --keep-alive --max-hours 2
```
Espera a que termine (~45-60 min). `pull.sh prep` muestra el resumen cuando acaba:
```bash
infra/aws/pull.sh prep
```
Con el ID de la instancia que imprimió `launch.sh`:
```bash
infra/aws/ami.sh i-0123456789abcdef0
```
Luego pon el ID de la AMI en `dsqa-infra` (`custom_ami_id`) y ejecuta `terraform apply`.

## Prueba de humo (GPU, ~15 min)

Confirma que la H100 carga OLMo antes de gastar en sesiones largas:
```bash
infra/aws/push.sh smoke && infra/aws/launch.sh smoke --max-hours 1
```

## Ciclo de una sesión

1. Crea `infra/aws/jobs/<sesión>.txt`, con **un comando por línea** (las líneas con `#` se ignoran):
   ```text
   python eval/run_local.py --configs configs/e3.yaml configs/e4.yaml --bench eval/bench --corpus data/public_pdfs --model-id allenai/Olmo-3.1-32B-Instruct --out experiments/runs/$DSQA_SESSION --resume
   python eval/judge.py --run experiments/runs/$DSQA_SESSION/e3 --backend olmo
   ```
2. Sube y lanza:
   ```bash
   infra/aws/push.sh s04
   ```
   ```bash
   infra/aws/launch.sh s04 --max-hours 3
   ```
3. Sigue el estado:
   ```bash
   infra/aws/status.sh
   ```
4. Cuando termine, baja los resultados:
   ```bash
   infra/aws/pull.sh s04
   ```
5. Comprueba que no quede nada encendido (`status.sh` debe decir *no hay instancias*).

### Reglas de los trabajos

- Se ejecutan desde la raíz del repo, con `/opt/dsqa-venv` activo, uno tras otro. Si uno falla, se sigue con el siguiente.
- Escriben sus resultados en `experiments/runs/$DSQA_SESSION/`. Esa carpeta se sube a S3 cada 5 min y al terminar cada trabajo.
- Variables disponibles: `DSQA_SESSION`, `DSQA_BUCKET`, `AWS_REGION`, `HF_HOME`, `HF_HUB_CACHE`.
- Sin internet para Hugging Face (`HF_HUB_OFFLINE=1`), como en Codabench. La plantilla `prep` sí tiene acceso.
- Cada trabajo deja su log en `experiments/runs/<sesión>/logs/<intento>/job-NN.log`, y el resumen en `SUMMARY.txt`.

### Si la instancia spot se interrumpe

Los resultados hasta ese momento ya están en S3: la instancia los guarda al recibir el aviso de 2 minutos. Relanza la misma sesión:
```bash
infra/aws/launch.sh s04
```
La instancia nueva descarga lo que ya existía, y `run_local.py --resume` continúa donde quedó.

## Opciones de `launch.sh`

| Opción | Efecto |
|---|---|
| `--template p5\|g6e\|prep` | H100 (por defecto), L40S del plan B, o CPU de preparación |
| `--on-demand` | No intentar spot |
| `--fallback-on-demand` | Si no hay spot en ninguna zona, lanzar on-demand |
| `--max-hours N` | Apagado forzado a las N h (más de 4 exige `--force`) |
| `--keep-alive` | No apagar al terminar los trabajos (solo para `ami.sh`) |
| `--force` | Lanzar aunque haya otra instancia del proyecto encendida |
| `--dry-run` | Mostrar el comando sin lanzar nada |

## Protecciones de costo

| Protección | Dónde |
|---|---|
| La instancia se apaga, y por tanto se **termina**, al acabar los trabajos | `bootstrap.sh` + plantilla de `dsqa-infra` |
| Apagado forzado a las `--max-hours` horas (3 por defecto) | `bootstrap.sh` (`shutdown -h +N`) |
| Apagado tras ~20 min sin trabajo ni uso de GPU | `watchdog.sh` |
| No se lanza una segunda instancia si ya hay una encendida | `launch.sh` |
| Presupuesto mensual con alertas por correo | `dsqa-infra` (módulo `cost`) |

## Problemas frecuentes

| Síntoma | Qué hacer |
|---|---|
| `VcpuLimitExceeded` | Faltan cuotas de GPU: `dsqa-infra/scripts/request-quotas.sh --apply` |
| "no hubo capacidad en ninguna zona" | Reintentar más tarde, añadir `--fallback-on-demand`, o cambiar `AWS_REGION` |
| La sesión no termina | `aws ssm start-session --target <id>` y `sudo tail -f /var/log/dsqa-bootstrap.log`; si está colgada, `stop.sh <sesión>` |
| `pull.sh` no muestra `SUMMARY.txt` | La sesión sigue en curso o se cortó; mirar `status.sh` y `logs/` |
| Errores raros de bash en la instancia | Los `.sh` deben tener saltos de línea LF (`.gitattributes` lo asegura) |
