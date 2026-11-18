# SPEC-018: Juez OLMo $s_5$

**Módulo:** `dsqa/verify/signals.py` (usa `generate/llm.py`) · **Estrategia:** E6 · **Prioridad:** M
**Requisitos:** RF-VE-02 · **Criterios:** CA-VE-02 · **ADR:** ADR-09

## Propósito
Obtener una estimación semántica, del propio OLMo, de si la evidencia permite responder.

## Interfaz
```python
def judge_sufficiency(llm: LLM, question: str, evidence: list[str]) -> float: ...   # ∈ [0,1]
```

## Comportamiento
1. Construir el prompt `resources/prompts/judge_s5.txt` con la pregunta y los top-`judge_topk` pasajes:
   ```
   Question: <pregunta>
   Evidence: <pasajes>
   Does the evidence contain the information needed to answer the question? Answer Yes or No.
   ```
2. Aplicar la plantilla de chat y hacer **una pasada hacia adelante** (sin `generate`).
3. Tomar los logits del siguiente token para los ids de `"Yes"` y `"No"` (incluidas las variantes con espacio inicial, sumando probabilidades).
4. $s_5 = P(\text{Yes}) / (P(\text{Yes}) + P(\text{No}))$.

## Reglas y casos borde
- Se omite en modo `FAST` o `EMERGENCY` (queda `None`; el q-FCM usa 0,5 como valor neutro).
- Los pasajes se truncan para que el prompt no supere `judge_max_tokens`.

## Configuración
| Clave | Por defecto |
|---|---|
| `verify.judge_topk` | 3 |
| `verify.judge_max_tokens` | 2000 |

## Errores y respaldo
- Error u OOM → $s_5 = $ `None` y registro.

## Pruebas
- LLM simulado con logits conocidos → valor igual a la fórmula.
- Verificar que no se llama a `generate()`.
- Tiempo < 3 s por pregunta en AWS.
