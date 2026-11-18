# ADR-11: Program of Thoughts en subproceso aislado

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Generación · **Relacionado:** RF-PT-*, RNF-SE-01, [SPEC-024](../spec/SPEC-024-program-of-thoughts.md)

## Contexto
Las preguntas numéricas de DONES exigen cálculos. El código que genera el LLM puede fallar, colgarse o intentar acciones peligrosas.

## Decisión
El programa se ejecuta en un subproceso con límite de tiempo y de memoria, sin red ni archivos, y solo con `math` disponible. Si falla, se responde por la vía directa.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| `exec` en el mismo proceso | Un bucle infinito o un error tumba el proceso principal |
| Sin PoT | Peor precisión en cálculos |

## Consecuencias
- Positivas: el proceso principal queda protegido.
- Negativas: ~0,2 s de arranque del subproceso cada vez que se usa.
- Verificación: CA-PT-01, CA-PT-02.
