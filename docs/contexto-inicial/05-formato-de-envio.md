# 5. Formato de envío y proceso de participación

**Fuentes:** [Codabench — How to participate](https://www.codabench.org/competitions/17954/) · [Join the Challenge](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/join-the-challenge/) · [Starter kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit)

## Pasos para participar

1. Crear una cuenta en [Codabench](https://www.codabench.org).
2. Llenar el [formulario de inscripción](https://forms.gle/F7YHkE7PALziNpqk6) **individualmente**, con el mismo correo de Codabench.
3. Solicitar unirse a la [competición en Codabench](https://www.codabench.org/competitions/17954/). Se aprueba después del formulario.
4. Si es en equipo: crear/unirse a una **organización** en Codabench (antes del **1 nov 2026**).
5. Unirse al [Discord](https://discord.gg/q6H7cJVkQQ) (anuncios, aclaraciones, soporte).
6. Subir el `.zip` (1 por día).

## Qué es un envío

Un único archivo **`.zip`** con **`main.py` en la raíz** (no dentro de una subcarpeta):

```
my_submission.zip
├── main.py        (obligatorio, en la raíz)
├── script.py      (opcional: módulos propios, importables desde main.py)
└── ...            (índices, adaptadores, prompts, modelos pequeños, etc.)
```

### Interfaz obligatoria

```python
def answer(question: str, corpus_dir: str, model_id: str) -> str:
    ...
```

- Se llama **una vez por cada pregunta** de la fase activa, **en el mismo proceso** (se puede cachear el modelo y el índice entre llamadas).
- Debe devolver la respuesta como **texto plano**. Si devuelve algo que no sea `str`, esa pregunta cuenta como sin respuesta.

### Argumentos

| Argumento | Significado |
|-----------|-------------|
| `question` | Texto de la pregunta. |
| `corpus_dir` | Carpeta local con los **documentos de referencia en PDF** para recuperación. **Usar siempre esta ruta**, no fijar una a mano. |
| `model_id` | Repo de Hugging Face del modelo base, actualmente **`allenai/Olmo-3.1-32B-Instruct`**. Se carga normalmente con `AutoModelForCausalLM.from_pretrained(model_id)` y se resuelve desde una **caché local**. |

## Entorno de ejecución

| Recurso | Valor |
|---------|-------|
| GPU | **1× NVIDIA H100 (80 GB VRAM)** |
| CPU | **32 núcleos** |
| RAM | **128 GB** |
| Internet | **No** (solo antes, para preparar archivos) |
| Tiempo límite (reloj de pared, incluye carga del modelo) | **1 h** en Public Leaderboard · **hasta 2 h** en Private Leaderboard |
| Tamaño del envío | **1 GB máx. descomprimido** |
| Cola | Los envíos corren **de uno en uno**; el reloj empieza cuando le toca al tuyo |
| Imagen Docker | `ieee-cis-competition:latest` |

**No hay vLLM ni flash-attn**: la inferencia va por `transformers`/`accelerate` (atención `sdpa`/`eager`). Lista completa de librerías en [08-entorno-y-dependencias.md](08-entorno-y-dependencias.md).

### Nuevas librerías

Si tu método necesita algo que no está instalado, pídelo en el canal **#dependencies** (sección *Submission Support*) de Discord. Las solicitudes se atienden en privado, pero las librerías nuevas se agregan para todos y se anuncian periódicamente.

## Qué recibes de vuelta

No ves ninguna salida de tu código, solo:

- **Finished:** tu puntuación aparece en el leaderboard (precisión balanceada y, como desempate, el tiempo).
- **Failed:** al pasar el ratón sobre el estado se ve un motivo corto (p. ej. falta `main.py`, error en el código o límite de recursos excedido).

## Probar antes de enviar

Como solo hay **1 envío por día**, conviene detectar localmente errores de sintaxis, typos o que `answer()` no devuelva un `str`. La carga del modelo desde caché local no se puede reproducir fuera de los servidores del reto, pero el resto de `main.py` es Python normal.

## Documentación de la metodología

- Con el envío en Codabench se adjunta un **borrador** de la metodología.
- Los preseleccionados para la Fase 2 entregan un **paper de 4 páginas en formato IEEE** (plantilla pendiente de publicación). Es la base para evaluar la **innovación técnica (40 % de la nota final)**.
