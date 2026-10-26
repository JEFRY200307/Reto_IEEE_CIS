# 7. Dataset de muestra y corpus

**Fuentes:** [sample/sample_qa.json](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/sample/sample_qa.json) · [sample/sites.txt](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/sample/sites.txt) · Copias locales: [recursos/sample_qa.json](recursos/sample_qa.json), [recursos/sites.txt](recursos/sites.txt)

## Dataset de muestra (`sample_qa.json`)

25 pares pregunta–respuesta. Sirven para ver **el estilo, la longitud y el razonamiento esperado**; **no** forman parte del benchmark real.

### Esquema

```json
{
  "id": 1,
  "domain": "DONES",               // "DONES" o "AI Papers"
  "question": "...",
  "question_type": "comparative",  // factual | comparative | procedural | causal | predictive
  "answer": "..."                   // respuesta de referencia (Markdown, puede incluir LaTeX)
}
```

### Distribución

| Tipo | DONES | AI Papers | Total |
|------|:-----:|:---------:|:-----:|
| factual | 3 | 4 | 7 |
| comparative | 1 | 2 | 3 |
| procedural | 4 | 1 | 5 |
| causal | 1 | 5 | 6 |
| predictive | 1 | 3 | 4 |
| **Total** | **10** | **15** | **25** |

### Preguntas de ejemplo

**IFMIF-DONES**

| id | tipo | pregunta |
|----|------|----------|
| 1 | comparative | Both OTR and scintillation are proposed for experimental beam imaging diagnostics… Which physical process does scintillation require that OTR does not? |
| 2 | factual | What does a "destructive" beam diagnostic do to the beam it measures? |
| 3 | procedural | What would be the radioactive decay constant of Be7 if we round its half life in days to the nearest integer? |
| 4 | factual | At what point in time does Be7 stop being the main source of activity in the Heat Exchanger of DONES? |
| 5 | causal | How are the inventories of Be7 and Tritium calculated for DONES Li loop? |
| 6 | procedural | What is the approximate volumetric flow rate in the primary heat exchanger? |
| 7 | predictive | What is the temperature of the on-line Nitrogen trap in IFMIF-DONES? |
| 8 | procedural | What is the bypass ratio of the ICS Branch of the DONES Li loop? |
| 9 | procedural | What will be volumen of the main building in the IFMIF DONES facilities? |
| 10 | factual | When would be required hands-on or remote handling maintenance in areas with neutronics activity? |

**AI Papers**

| id | tipo | tema / paper |
|----|------|--------------|
| 11 | comparative | OneSearch (búsqueda generativa e-commerce): RQ-Kmeans vs RQ-VAE |
| 12 | factual | ONB-MACF: ¿comparación injusta por restricciones de inmutabilidad? |
| 13 | causal | Espacios *lush* y espacios de Banach con índice numérico 1 (Teorema 4.1) |
| 14 | causal | REVEL: por qué importa una métrica entre 0 y 1 |
| 15 | predictive | WinStat: tamaño de ventana para $L = 512$ |
| 16 | causal | Mapas cognitivos difusos (FCM): valores de activación relativos |
| 17 | factual | Comportamiento dinámico de FCM: cubrimiento de FCM estables |
| 18 | factual | *Fairness by Brute Force* (generación texto-imagen) |
| 19 | procedural | WinStat: mecanismo de ponderación normalizada de WinStatFlex |
| 20 | causal | ZeroDiff: propósito del generador de representaciones (R) |
| 21 | factual | ThinkMore (búsqueda neuro-simbólica en ajedrez): tests bayesianos |
| 22 | predictive | SimCLR: debilidad de una sola aumentación fija |
| 23 | comparative | Aprendizaje federado: resiliencia $(\alpha,f)$-bizantina vs otros enfoques |
| 24 | predictive | *General Purpose AI Systems: Definition and Taxonomy*: aprendizaje activo en GPAIS |
| 25 | causal | Mamba: por qué los modelos LTI fallan en *selective copying* |

### Observaciones sobre los ejemplos

- Las preguntas de **DONES** son sobre la instalación concreta (lazo de litio, intercambiador de calor, Be-7, tritio, diagnósticos de haz, edificio principal). Varias requieren **datos numéricos exactos** de tablas o figuras, o un **cálculo** a partir de ellos (p. ej. constante de desintegración $\lambda = \ln 2 / T_{1/2}$).
- Las preguntas de **AI Papers** suelen **nombrar el paper** o el método, lo que ayuda a la recuperación. Varias vienen de grupos de la Universidad de Granada / DaSCI (FCM, GPAIS, ThinkMore, Fairness by Brute Force, REVEL…), e incluyen matemática pura (espacios de Banach).
- Hay preguntas mal redactadas o con erratas ("volumen", "le $G$"): el sistema debe ser robusto a eso.
- Las respuestas de referencia del ejemplo son **más largas** de lo que la página describe como "concisas"; suelen dar el dato clave y luego una justificación breve.

## Corpus

- En la plataforma de evaluación hay un **corpus de documentos PDF** del dominio, disponible en `corpus_dir`.
- **No hay acceso directo** al corpus de evaluación: solo se consulta en tiempo de ejecución.
- El corpus incluye **documentos reales y distractores**.
- Se publica la lista de **sitios fuente** para que los equipos construyan sus propios recursos (índices, datos de entrenamiento, etc.) con antelación.

### Sitios fuente del corpus (`sites.txt`)

| Tipo | Sitios |
|------|--------|
| Aceleradores / fusión | [accelconf.web.cern.ch](https://accelconf.web.cern.ch), [indico.jacow.org](https://indico.jacow.org), [proceedings.jacow.org](https://proceedings.jacow.org), [www.jacow.org](https://www.jacow.org), [scipub.euro-fusion.org](https://scipub.euro-fusion.org) |
| IA / ML | [aclanthology.org](https://aclanthology.org), [arxiv.org](https://arxiv.org), [openreview.net](https://openreview.net), [ojs.aaai.org](https://ojs.aaai.org), [proceedings.neurips.cc](https://proceedings.neurips.cc), [www.ijcai.org](https://www.ijcai.org), [www.jmlr.org](https://www.jmlr.org) |
| Editoriales generales | [ieeexplore.ieee.org](https://ieeexplore.ieee.org), [dl.acm.org](https://dl.acm.org), [link.springer.com](https://link.springer.com), [www.sciencedirect.com](https://www.sciencedirect.com), [onlinelibrary.wiley.com](https://onlinelibrary.wiley.com), [www.tandfonline.com](https://www.tandfonline.com), [iopscience.iop.org](https://iopscience.iop.org), [journals.sagepub.com](https://journals.sagepub.com), [digital-library.theiet.org](https://digital-library.theiet.org), [www.mdpi.com](https://www.mdpi.com), [www.frontiersin.org](https://www.frontiersin.org), [www.hindawi.com](https://www.hindawi.com), [www.nature.com](https://www.nature.com) |
| Matemáticas | [ems.press](https://ems.press), [www.impan.pl](https://www.impan.pl) |
| Otros (probables distractores) | [escholarship.org](https://escholarship.org), [papers.ssrn.com](https://papers.ssrn.com), [pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov), [www.biorxiv.org](https://www.biorxiv.org), [www.thelancet.com](https://www.thelancet.com) |

> La agrupación por tipo es nuestra, no oficial. El archivo original lista 32 dominios sin clasificar.
