# SPEC-027: Glosario de DONES

**Módulo:** `offline/build_glossary.py` → `resources/glossary_dones.json` · **Estrategia:** E2 · **Prioridad:** M
**Requisitos:** RF-OF-02, RF-CO-01, RNF-CU-02 · **Criterios:** CA-CO-01

## Propósito
Expandir las siglas de IFMIF-DONES de la pregunta para que BM25 y el denso encuentren el pasaje correcto.

## Interfaz
```bash
python offline/build_glossary.py --pdfs data/public_pdfs/ --seed resources/glossary_seed.yaml --out resources/glossary_dones.json
```

```json
{
  "ICS": {"expansions": ["Impurity Control System"], "source": "https://…", "domain": "DONES"},
  "HEBT": {"expansions": ["High Energy Beam Transport"], "source": "https://…", "domain": "DONES"}
}
```

## Comportamiento
1. Partir de una semilla escrita a mano (`glossary_seed.yaml`) con siglas conocidas.
2. Detectar en los PDFs públicos patrones `Nombre Largo (SIGLA)` y `SIGLA (Nombre Largo)`.
3. Unir: la semilla tiene prioridad; las detecciones automáticas se añaden si aparecen en ≥ 2 documentos.
4. Guardar la fuente (URL del PDF) de cada entrada.

## Reglas y casos borde
- Siglas ambiguas (dos expansiones) → se guardan ambas.
- Siglas de una letra o palabras comunes en mayúsculas (`THE`, `AND`) → descartadas.
- Tamaño < 1 MB.

## Configuración
Ver `retrieval.glossary` en [SPEC-012](SPEC-012-analisis-de-consulta.md).

## Errores y respaldo
- PDF ilegible → se omite.

## Pruebas
- Texto con "Impurity Control System (ICS)" → entrada `ICS`.
- `THE` no aparece en el glosario.
- Cada entrada tiene `source`.
