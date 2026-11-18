# ADR-15: Instancias desechables; S3 como almacenamiento persistente

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Infraestructura · **Relacionado:** [ADR-14](ADR-14-computo-aws-p5-spot.md), [ADR-17](ADR-17-control-de-costos-aws.md), [SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md)

## Contexto
- Una instancia GPU encendida sin uso cuesta lo mismo que una trabajando.
- Las instancias spot pueden interrumpirse en cualquier momento y pueden quedar en otra zona de disponibilidad (AZ) cada vez. Un volumen EBS solo se puede montar en su propia AZ.
- Los pesos de OLMo (~64 GB) tardan minutos en descargarse en cada sesión.

## Decisión
1. **Cada sesión crea una instancia nueva y la termina al acabar** (`InstanceInitiatedShutdownBehavior=terminate`, disco raíz con `DeleteOnTermination=true`). No hay instancias detenidas acumulando costo de disco.
2. **Un bucket S3 privado en la misma región** guarda todo lo que debe sobrevivir:

| Prefijo en S3 | Contenido | Tamaño aprox. |
|---|---|---|
| `hf-cache/` | Caché de Hugging Face con OLMo, embedder y reranker (misma estructura que `~/.cache/huggingface/hub`) | ~66 GB |
| `corpus/` | PDFs públicos del banco local | < 2 GB |
| `code/` | Copia del repositorio subida desde la laptop | < 50 MB |
| `runs/` | Resultados y trazas de cada sesión | < 1 GB |

3. Al iniciar, la instancia copia `hf-cache/` desde S3 al disco local (transferencia gratuita dentro de la región) y fija `HF_HUB_OFFLINE=1`. Así `from_pretrained("allenai/Olmo-3.1-32B-Instruct")` se resuelve desde la caché, **igual que en Codabench**.
4. Si la copia desde S3 falla, se descarga desde Hugging Face como respaldo.
5. Una **AMI propia** (base Deep Learning de AWS + entorno Python con `requirements-runtime.txt`) evita reinstalar dependencias en cada sesión. Los pesos **no** van en la AMI: un snapshot se carga en diferido y leer 64 GB desde él la primera vez es lento.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Detener la instancia en lugar de terminarla | Paga el EBS (~200 GB) todo el mes y no sirve con spot en otra AZ |
| Volumen EBS de datos persistente | Atado a una AZ; spot puede caer en otra |
| Pesos dentro de la AMI | Lectura inicial lenta (carga diferida del snapshot) |
| Descargar de Hugging Face cada vez | Funciona, pero depende de un servicio externo; queda como respaldo |
| EFS | Más caro y lento para leer archivos grandes una sola vez |

## Consecuencias
- Positivas: solo se paga GPU mientras se trabaja; independiente de la AZ; el entorno replica la caché local de Codabench.
- Costos fijos: S3 ~70 GB ≈ USD 1,6/mes; AMI ~40 GB ≈ USD 2/mes.
- Negativas: ~5-10 min de preparación por sesión (copia desde S3 + carga del modelo). Se compensa agrupando el trabajo en sesiones largas ([ADR-17](ADR-17-control-de-costos-aws.md)).
- Licencia: OLMo se publica con licencia abierta; guardar una copia privada para uso propio es compatible. No se comparte el bucket.
