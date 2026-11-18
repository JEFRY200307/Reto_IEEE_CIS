# ADR-17: Presupuesto, auto-apagado y sesiones por lotes

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Infraestructura · **Relacionado:** RNF-CS-*, [ADR-14](ADR-14-computo-aws-p5-spot.md), [ADR-15](ADR-15-instancias-desechables-y-s3.md), [SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md)

## Contexto
El mayor riesgo de costo no es la tarifa por hora, sino **olvidar una instancia encendida**: una p5.4xlarge on-demand olvidada un fin de semana cuesta ~USD 330.

## Decisión
Cinco controles, todos obligatorios:

| # | Control | Cómo |
|---|---|---|
| 1 | **Presupuesto con alertas** | AWS Budgets: presupuesto mensual de **USD 150** con alertas por correo al 50 %, 80 % y 100 % (real) y al 100 % (pronosticado) |
| 2 | **Apagado máximo por sesión** | El *user data* ejecuta `shutdown -h +180`: la instancia se termina a las 3 h pase lo que pase. Se puede ampliar a mano, nunca desactivar |
| 3 | **Apagado por inactividad** | Un *watchdog* (cron cada 5 min) termina la instancia si la GPU está por debajo del 5 % de uso durante 20 min seguidos |
| 4 | **Sesiones por lotes** | Cada sesión corre una **lista de trabajos** preparada en la laptop (varias configs sobre el banco, reutilizando OLMo cargado). Nada de "abrir la instancia para ver qué pasa" |
| 5 | **Revisión al cerrar** | Al terminar cada sesión: comprobar en la consola que no queda ninguna instancia `running` y anotar las horas en `experiments/aws-sessions.md` |

## Estimación de gasto (hasta el 30 nov 2026)

| Concepto | Supuesto | Spot | On-demand |
|---|---|---|---|
| Preparación única (modelo a S3 + AMI) | 1 h de `m7i.xlarge` (CPU) | ~USD 0,2 | ~USD 0,2 |
| Sesiones con GPU (S1-S9 + reserva, ver [plan](../08-guia-de-despliegue.md#89-plan-de-sesiones-hasta-el-30-nov)) | ≈ 15-17 h de p5.4xlarge | ~USD 20-45 | ~USD 105-115 |
| Reserva on-demand por falta de capacidad spot | ≈ 3 h | ~USD 21 | (incluido) |
| S3 (~70 GB) + AMI (~40 GB) | 1 mes | ~USD 4 | ~USD 4 |
| **Total estimado** | | **~USD 45-70** | **~USD 110-120** |

El presupuesto de USD 150 cubre el peor caso con margen. Si la cuenta tiene créditos promocionales de AWS, verificar en *Billing → Credits* si aplican a instancias EC2 GPU.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Confiar en apagar a mano | Es la causa más común de facturas inesperadas |
| Savings Plans o reservas | Compromiso de 1-3 años; no aplica a un proyecto de un mes |

## Consecuencias
- Positivas: el gasto máximo está acotado y es visible; un olvido cuesta como mucho 3 h.
- Negativas: una ejecución larga legítima debe ampliar el apagado a mano (`sudo shutdown -c` y programar uno nuevo).
- Verificación: tras cada sesión, `aws ec2 describe-instances --filters Name=instance-state-name,Values=running` devuelve vacío.
