# ADR-14: Cómputo de desarrollo en AWS p5.4xlarge, spot primero

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Infraestructura · **Relacionado:** [ADR-15](ADR-15-instancias-desechables-y-s3.md), [ADR-17](ADR-17-control-de-costos-aws.md), [SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md), [Guía de despliegue](../08-guia-de-despliegue.md)

## Contexto
- OLMo 3.1 32B en bf16 necesita ~64 GB de VRAM. La laptop del equipo no puede correrlo.
- Codabench solo permite 1 envío por día y no muestra ninguna salida. Hace falta un lugar donde correr OLMo para medir precisión y tiempo con el banco local antes de gastar envíos.
- El equipo decidió usar AWS. El objetivo es **gastar lo mínimo** y aun así medir con fidelidad.

## Decisión
1. **Instancia:** `p5.4xlarge` (1× NVIDIA H100 80 GB, 16 vCPU, 256 GiB RAM). Es la misma GPU que Codabench, así que los tiempos y el comportamiento en bf16 son comparables.
2. **Mercado: spot primero, on-demand como respaldo.**
   - Sesiones de desarrollo y evaluación del banco local → **spot** (~USD 1,3-2,6/h observado en us-east-1, julio 2026).
   - Cuando no haya capacidad spot, o en una sesión crítica de la última semana que no pueda arriesgarse a una interrupción → **on-demand** (~USD 6,88/h).
   - El hardware es idéntico en spot y on-demand: los tiempos medidos valen igual en ambos.
3. **Región:** `us-east-1` por precio y capacidad. Si no hay capacidad spot, se prueba `us-east-2` o `us-west-2` (verificar con `describe-instance-type-offerings`).
4. **Plan B por cuota:** si AWS no aprueba la cuota de instancias P a tiempo, usar `g6e.2xlarge` (1× L40S 48 GB, 64 GiB RAM) con OLMo en **4 bits**, solo para pruebas funcionales y comparación relativa entre estrategias (no para medir tiempos).
5. **Lo que no necesita GPU** (ingesta, BM25, fusión, q-FCM, CMA-ES, recall@5, pruebas) **se queda en la laptop**, sin costo.

## Comparación de opciones (precios de referencia en us-east-1, verificar antes de usar)

| Opción | GPU / VRAM | ¿OLMo en bf16? | Fidelidad con Codabench | USD/h | Uso |
|---|---|---|---|---|---|
| **p5.4xlarge spot** | H100 80 GB | Sí | Alta (misma GPU) | ~1,3-2,6 (variable) | **Principal** |
| **p5.4xlarge on-demand** | H100 80 GB | Sí | Alta | ~6,88 | Sin capacidad spot o sesión crítica |
| g6e.2xlarge | L40S 48 GB | No (solo 8 o 4 bits) | Baja (otra GPU, cuantizado) | ~2,2 on-demand | Plan B funcional |
| g6e.xlarge | L40S 48 GB, 32 GiB RAM | No | Baja; poca RAM para cargar 32B | ~1,86 | Descartada |
| p4d.24xlarge | 8× A100 40 GB | Sí, repartido | Media | ~22 | Descartada: sobredimensionada |
| SageMaker | Varias | Sí | Media | Mayor que EC2 | Descartada: recargo y más complejidad |

Fuentes de precios: trackers públicos ([Holori](https://calculator.holori.com/aws/ec2/p5.4xlarge/us-east-1), [DoiT](https://compute.doit.com/spot/us-east-1/p5.4xlarge), [Vantage](https://instances.vantage.sh/aws/ec2/p5.4xlarge?region=us-east-1)), consultados el 29 oct 2026 con datos de abril-julio 2026. **El precio oficial es el de la consola de AWS.**

## Por qué spot es adecuado aquí
- Las sesiones son cortas (1-2 h) y por lotes.
- Los resultados se guardan pregunta por pregunta en S3, así que una interrupción solo pierde la pregunta en curso y se reanuda ([SPEC-030](../spec/SPEC-030-evaluacion-local-y-estadistica.md)).
- Una hora de H100 en spot cuesta parecido o menos que una L40S on-demand, y da fidelidad total.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Todo on-demand | ~3 veces más caro sin beneficio para el desarrollo |
| GPU más barata con cuantización como principal | Los resultados no se trasladan bien a Codabench (bf16, H100) |
| Capacity Blocks for ML | Reserva por bloques de días; sobredimensionado para sesiones cortas |
| Solo Codabench, sin AWS | 1 envío por día y sin salidas: no alcanza para comparar E0-E6 |

## Consecuencias
- Positivas: medición fiel de precisión y tiempo; costo estimado USD 45-70 con spot (USD 110-120 en el peor caso, todo on-demand) ([ADR-17](ADR-17-control-de-costos-aws.md)).
- Negativas: las cuotas de instancias P suelen empezar en 0 en cuentas nuevas y su aprobación puede tardar días; la capacidad spot de H100 no está garantizada.
- Acción inmediata: solicitar hoy las cuotas de instancias P (on-demand y spot) y la de G (plan B). Ver la [guía](../08-guia-de-despliegue.md#82-paso-1-cuenta-y-cuotas-hacerlo-hoy).
- Diferencia conocida con Codabench: p5.4xlarge tiene 16 vCPU (Codabench, 32). La ingesta medida en AWS será **más lenta** que en Codabench, así que el tiempo medido es una cota conservadora.
