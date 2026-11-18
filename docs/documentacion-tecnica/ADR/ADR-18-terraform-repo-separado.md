# ADR-18: Infraestructura de AWS como código con Terraform, en un repositorio separado

**Estado:** Propuesta · **Fecha:** 2026-11-17 · **Área:** Infraestructura · **Relacionado:** [ADR-14](ADR-14-computo-aws-p5-spot.md), [ADR-15](ADR-15-instancias-desechables-y-s3.md), [ADR-16](ADR-16-acceso-seguro-aws.md), [ADR-17](ADR-17-control-de-costos-aws.md), [SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md), [Guía de despliegue](../08-guia-de-despliegue.md)

## Contexto
- La [guía de despliegue](../08-guia-de-despliegue.md) (pasos 2 a 6) crea a mano, con comandos de la CLI, varios recursos de AWS: bucket, rol IAM, security group, launch template, presupuesto y alertas.
- Hacerlo a mano es propenso a errores (un permiso de más, un puerto abierto, olvidar un recurso al limpiar) y no deja registro de qué existe en la cuenta.
- La infraestructura **no forma parte de la entrega**: Codabench solo recibe el zip con `main.py`. No debe mezclarse con el código del sistema `dsqa`.

## Decisión
1. **Repositorio separado `dsqa-infra`**, en la cuenta de GitHub del autor, con Terraform. Este repositorio (`Reto_IEEE_CIS`) no depende de Terraform ni lo incluye.
2. **Terraform gestiona solo los recursos permanentes:**

| Módulo | Recursos | Equivale a |
|---|---|---|
| `storage` | Bucket S3 privado (acceso público bloqueado, cifrado por defecto) | Guía §8.4.1 |
| `iam` | Rol `dsqa-ec2`, perfil de instancia, política de acceso al bucket, `AmazonSSMManagedInstanceCore` | Guía §8.4.2, [ADR-16](ADR-16-acceso-seguro-aws.md) |
| `network` | Security group sin reglas de entrada en la VPC por defecto | Guía §8.4.3 |
| `compute` | Launch templates `dsqa-p5` (H100) y `dsqa-g6e` (plan B), con `terminate` al apagar, disco que se borra e IMDSv2; AMI base de DLAMI leída de SSM con un `data` source | Guía §8.6 |
| `cost` | AWS Budgets (USD 150, alertas 50/80/100 % real y 100 % pronosticado) y monitor de Cost Anomaly Detection | Guía §8.3, [ADR-17](ADR-17-control-de-costos-aws.md) |

3. **Terraform no gestiona** lo que es efímero o asíncrono:

| Fuera de Terraform | Por qué | Quién lo hace |
|---|---|---|
| Instancias EC2 de cada sesión | Son desechables y viven 1-3 h | `infra/aws/launch.sh` de este repositorio ([SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md)) |
| Solicitud de cuotas (Service Quotas) | La aprobación de AWS es manual y asíncrona | A mano (guía §8.2) |
| AMI propia y subida del modelo a S3 | Se crean desde una instancia de preparación, no con la API de recursos | Guía §8.5 (opcional a futuro: Packer) |

4. **Estado de Terraform** en un bucket S3 aparte, con versionado y bloqueo nativo (`use_lockfile = true`, Terraform ≥ 1.10). Ese bucket se crea una vez con una configuración mínima `bootstrap/` de estado local.
5. **Contrato entre repositorios:** `envs/dev` expone el output `config_env`, que es el archivo `infra/aws/config.env` de este repositorio ya escrito:
   ```bash
   terraform -chdir=envs/dev output -raw config_env > ../Reto_IEEE_CIS/infra/aws/config.env
   ```
   Contiene `AWS_REGION`, `DSQA_BUCKET`, `LAUNCH_TEMPLATE` (p5), `LAUNCH_TEMPLATE_FALLBACK` (g6e), `LAUNCH_TEMPLATE_PREP`, `INSTANCE_PROFILE` y `MAX_HOURS_DEFAULT`. Si no se usa Terraform, el mismo archivo se escribe a mano, así que el reto **no depende** de Terraform.
6. **Una sola pasada de `apply`:** mientras no exista la AMI propia (`custom_ami_id = null`), las plantillas usan la AMI base de Deep Learning de AWS, leída del parámetro público de SSM. Al crear la AMI propia se pone su ID y se vuelve a aplicar. La plantilla `dsqa-prep` (CPU, para la preparación) siempre usa la AMI base.

### Estructura de `dsqa-infra` (construida el 2026-11-17)

Carpeta hermana de este repositorio: `../dsqa-infra/`. Validada con `terraform validate` (Terraform 1.16.4, proveedor AWS 6.73.0).

```
dsqa-infra/
├── README.md                     # Requisitos, puesta en marcha, costos, destruir, problemas frecuentes
├── .gitignore                    # .terraform/, *.tfstate*, *.tfvars, backend.hcl
├── .github/workflows/terraform.yml   # fmt + validate en cada push
├── bootstrap/                    # Bucket del estado (estado local, se aplica una vez, prevent_destroy)
│   ├── versions.tf  main.tf  variables.tf  outputs.tf  .terraform.lock.hcl
├── modules/
│   ├── storage/                  # Bucket del proyecto: privado, cifrado, solo HTTPS
│   ├── iam/                      # Rol dsqa-ec2 + perfil: SSM y acceso solo al bucket
│   ├── network/                  # Security group dsqa-no-ingress
│   ├── compute/                  # Launch templates dsqa-p5, dsqa-g6e, dsqa-prep
│   └── cost/                     # Presupuesto USD 150 + monitor de anomalías
├── envs/dev/                     # Raíz que se aplica en la cuenta
│   ├── versions.tf  backend.tf  main.tf  variables.tf  outputs.tf  .terraform.lock.hcl
│   ├── backend.hcl.example       # bucket y región del estado
│   └── terraform.tfvars.example  # correos de alerta, presupuesto, custom_ami_id
└── scripts/request-quotas.sh     # Muestra y solicita las cuotas de GPU (--apply)
```

Detalles de implementación que no estaban en la propuesta inicial:
- Los nombres de los buckets incluyen el ID de la cuenta (`dsqa-data-<cuenta>`, `dsqa-tfstate-<cuenta>`), así que son únicos sin inventar nada.
- Ambos buckets niegan el acceso sin HTTPS; el del proyecto aborta subidas incompletas a los 3 días y borra `logs/` a los 30.
- El disco gp3 de las plantillas tiene 8000 IOPS y 1000 MiB/s, para que los 64 GB del modelo se lean en ~1 min en lugar de ~9 (unos USD 0,10/h extra, solo mientras existe la instancia).

### Reglas
- Versiones fijadas: Terraform y proveedor AWS con restricción de versión y `.terraform.lock.hcl` en el repositorio.
- Sin secretos en el código ni en `terraform.tfvars` versionado; las credenciales vienen del perfil de la AWS CLI (SSO).
- Todo recurso lleva las etiquetas `Project=dsqa` y `ManagedBy=terraform` (`default_tags` del proveedor).
- El bucket del proyecto tiene `force_destroy = false`; solo se cambia a `true` en la limpieza final, para no borrar el modelo y los resultados por accidente.
- Cada cambio se revisa con `terraform plan` antes de `terraform apply`.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Seguir con comandos de la CLI (guía actual) | Funciona, pero no es reproducible ni deja inventario; la limpieza depende de la memoria |
| Terraform dentro de este repositorio | Mezcla infraestructura con la entrega; el repo del reto debe contener solo el sistema y su documentación |
| AWS CloudFormation / CDK | Válidos; Terraform es más portable y el autor lo prefiere |
| Gestionar también las instancias de cada sesión con Terraform | Recursos de vida corta; `apply`/`destroy` por sesión es más lento y frágil que `run-instances` con una plantilla |

## Consecuencias
- **Positivas:** la cuenta se puede levantar y **destruir completa** con un comando (`terraform destroy`), lo que garantiza que no quede nada cobrando tras el reto; los permisos y el firewall quedan revisables en código; sirve como portafolio independiente.
- **Negativas:** curva de aprendizaje y tiempo de montaje. Quedan **13 días** hasta el último envío (30 nov 2026).
- **Regla de calendario:** Terraform **no bloquea el reto**. Si la infraestructura ya se creó a mano y funciona, se sigue usando y se migra después con bloques `import` de Terraform, sin recrear nada. Si aún no existe, se puede crear directamente con Terraform siempre que esté listo en ≤ 1 día; si no, se usa la guía manual.
- **Costo:** Terraform es gratuito; el bucket del estado cuesta céntimos al mes.
- **Verificación:** `terraform plan` sin cambios pendientes tras aplicar; el security group sin reglas de entrada y el rol con solo los dos permisos ([CA-AWS-05](../06-criterios-de-aceptacion.md#infraestructura-aws)); tras `terraform destroy`, *Cost Explorer* muestra gasto diario 0 (salvo la AMI y su snapshot, que se borran a mano).

## Pendiente para pasar a "Aceptada"
- [x] Crear el repositorio `dsqa-infra` (código validado, sin aplicar).
- [ ] Aplicar `bootstrap/` y `envs/dev/` en la cuenta.
- [ ] Confirmar que `launch.sh` funciona con el `config.env` generado por Terraform.
