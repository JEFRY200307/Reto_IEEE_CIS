# SPEC-023: Generación con OLMo

**Módulo:** `dsqa/generate/llm.py`, `dsqa/generate/prompts.py` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-GE-01..07 · **Criterios:** CA-GE-01..03, CA-RP-01 · **ADR:** ADR-01, ADR-06, ADR-12

## Propósito
Cargar el modelo base y producir una respuesta concisa y fundamentada.

## Interfaz
```python
class LLM:
    @classmethod
    def load(cls, model_id: str) -> "LLM": ...
    def generate(self, messages: list[dict], max_new_tokens: int) -> str: ...
    def next_token_probs(self, messages: list[dict], tokens: list[str]) -> dict[str, float]: ...
    def count_tokens(self, text: str) -> int: ...

def render(kind: Literal["answer_dones", "answer_ai", "answer_generic", "zero_shot", "judge_s5", "pot"], **vars) -> list[dict]: ...
def postprocess(text: str) -> str: ...
```

## Comportamiento
1. `load`: `AutoTokenizer` + `AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=bfloat16, device_map="cuda", attn_implementation="sdpa")`; `model.eval()`.
2. Elegir plantilla: `answer_dones` si $\mu_{DONES} > \mu_{AI}$, `answer_ai` en caso contrario, `answer_generic` en E0.
3. Instrucciones del prompt (E1+):
   - Responder en inglés, con el **dato o la conclusión clave en la primera oración** y luego una justificación breve.
   - Usar el contexto; si no alcanza, dar la mejor respuesta con conocimiento propio, **sin negarse**.
   - Incluir unidades en los valores numéricos.
   - No citar el formato `[Doc: …]` ni hablar del contexto ("according to the context").
4. `generate`: `apply_chat_template` + `generate(do_sample=False, max_new_tokens=…)` bajo `torch.inference_mode()`.
5. `postprocess`: quitar restos de plantilla, bloques de razonamiento interno si los hubiera, frases de relleno iniciales y espacios sobrantes.

## Reglas y casos borde
- Nunca se usa una ruta fija del modelo: siempre `model_id`.
- Los prompts no mencionan al juez ni la evaluación (RNF-CU-03).
- Si la respuesta queda vacía tras `postprocess`, se devuelve el texto sin postprocesar.

## Configuración
| Clave | E0 | E1+ |
|---|---|---|
| `generate.max_new_tokens` | 2048 | 300 |
| `generate.max_new_tokens_fast` | — | 200 |
| `generate.prompts_dir` | `resources/prompts` | = |

## Errores y respaldo
- OOM → lo gestiona [SPEC-004](SPEC-004-degradacion-y-respaldo.md).

## Pruebas
- Con LLM simulado: plantilla correcta según dominio.
- `postprocess` elimina `<|assistant|>` y espacios dobles.
- Revisión manual de 20 respuestas (dato clave primero ≥ 90 %).
- Dos ejecuciones idénticas → misma respuesta.
