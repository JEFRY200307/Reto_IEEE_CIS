# Registro de decisiones de arquitectura (ADR)

[← Documentación técnica](../README.md)

Cada archivo registra **una** decisión: el contexto, lo que se decidió, las alternativas descartadas y sus consecuencias. Una decisión no se edita para cambiarla: se crea un ADR nuevo que la **reemplaza**, y el anterior pasa a estado *Reemplazada*.

## Estados

| Estado | Significado |
|---|---|
| **Propuesta** | En discusión o pendiente de un dato |
| **Aceptada** | Vigente; el código debe cumplirla |
| **Reemplazada** | Sustituida por otro ADR (se indica cuál) |
| **Rechazada** | Evaluada y descartada |

## Índice

| ADR | Decisión | Estado | Área |
|---|---|---|---|
| [ADR-01](ADR-01-inferencia-bf16-sin-cuantizar.md) | Inferencia en bf16 con `transformers` y atención `sdpa`, sin cuantizar | Aceptada | Generación |
| [ADR-02](ADR-02-estrategias-como-configuracion-yaml.md) | Cada estrategia E0-E6 es un archivo YAML sobre el mismo código | Aceptada | Configuración |
| [ADR-03](ADR-03-inicializacion-perezosa.md) | Inicializar modelo e índices en la primera llamada a `answer()` | Aceptada | Runtime |
| [ADR-04](ADR-04-carga-paralela-olmo-e-ingesta.md) | Cargar OLMo en paralelo con la ingesta del corpus | Aceptada | Runtime |
| [ADR-05](ADR-05-pymupdf-extractor-principal.md) | PyMuPDF en paralelo como extractor principal | Aceptada | Ingesta |
| [ADR-06](ADR-06-greedy-y-respuestas-cortas.md) | Decodificación greedy y respuestas de ≈300 tokens | Aceptada | Generación |
| [ADR-07](ADR-07-umbral-fijo-modo-rapido.md) | Umbral fijo del modo rápido sin conocer la fase | **Propuesta** | Runtime |
| [ADR-08](ADR-08-verificar-evidencia-no-respuesta.md) | Verificar la evidencia recuperada, no la respuesta generada | Aceptada | Verificación |
| [ADR-09](ADR-09-juez-olmo-como-entrada-qfcm.md) | El juez OLMo es una entrada del q-FCM, no el decisor | Aceptada | Verificación |
| [ADR-10](ADR-10-calibracion-solo-offline.md) | Calibración CMA-ES solo fuera de línea | Aceptada | CI |
| [ADR-11](ADR-11-pot-en-subproceso-aislado.md) | Program of Thoughts en subproceso aislado | Aceptada | Generación |
| [ADR-12](ADR-12-nunca-abstenerse.md) | El sistema nunca se abstiene | Aceptada | Generación |
| [ADR-13](ADR-13-modelos-auxiliares-fp16.md) | Modelos auxiliares guardados en fp16 | Aceptada | Empaquetado |
| [ADR-14](ADR-14-computo-aws-p5-spot.md) | Cómputo de desarrollo en AWS p5.4xlarge, spot primero | Aceptada | Infraestructura |
| [ADR-15](ADR-15-instancias-desechables-y-s3.md) | Instancias desechables; S3 como almacenamiento persistente | Aceptada | Infraestructura |
| [ADR-16](ADR-16-acceso-seguro-aws.md) | Acceso por SSM con rol IAM; sin SSH abierto ni claves en la instancia | Aceptada | Infraestructura |
| [ADR-17](ADR-17-control-de-costos-aws.md) | Presupuesto, auto-apagado y sesiones por lotes | Aceptada | Infraestructura |
| [ADR-18](ADR-18-terraform-repo-separado.md) | Infraestructura de AWS como código con Terraform, en un repositorio separado (fuera de la entrega) | **Propuesta** | Infraestructura |

## Plantilla

```markdown
# ADR-NN: <decisión en una frase>

**Estado:** Propuesta | Aceptada | Reemplazada por ADR-XX | Rechazada
**Fecha:** AAAA-MM-DD · **Área:** <área> · **Relacionado:** <RF/RNF/SPEC/ADR>

## Contexto
<Qué problema o restricción obliga a decidir.>

## Decisión
<Lo que se hace, en términos verificables.>

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|

## Consecuencias
- Positivas: …
- Negativas / riesgos: …
- Verificación: …
```
