# 1. Referencias seleccionadas

Se seleccionaron 16 referencias de una revisión inicial de 171. El criterio: cada referencia debe respaldar una decisión concreta del pipeline o de las estrategias E0 a E6.

- **Núcleo (8):** sostienen decisiones centrales; son el mínimo para el paper de 4 páginas.
- **Complementarias (8):** respaldan detalles de implementación; se añaden si hay espacio.

## Leyenda

- **Cuartil:** según SJR (SCImago), verificado en fuentes que replican sus datos (octubre 2026). Las conferencias no tienen cuartil; se indica su ranking CORE (no verificado en esta revisión).
- **Pendiente:** dato que debe confirmarse en el DOI antes de enviar el paper.

---

## Núcleo (8)

### [1] RAG: fundamento del enfoque

P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459–9474. [Online]. Available: https://arxiv.org/abs/2005.11401

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Conferencia | No aplica (CORE A*) | Todas (E0 a E6) |

**Aporte a la investigación:** define el paradigma de recuperar pasajes de un corpus externo y condicionar la generación del LLM en ellos, sin modificar sus pesos. Es el marco en el que se sitúa todo el sistema y la base del baseline E0.

### [2] Olmo 3: modelo obligatorio

Team OLMo, "Olmo 3," arXiv:2512.13961, 2025. [Online]. Available: https://arxiv.org/abs/2512.13961

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Preprint (reporte técnico) | No | Todas |

**Aporte a la investigación:** documenta el modelo fijo del reto (OLMo 3.1 32B Instruct): arquitectura, contexto de 65k tokens y post-entrenamiento. Citarlo es obligatorio y permite discutir sus límites con conocimiento especializado.

### [3] BM25: recuperación léxica

S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Found. Trends Inf. Retr.*, vol. 3, no. 4, pp. 333–389, 2009, doi: 10.1561/1500000019.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | Q1 probable (no confirmado en SJR) | E2 a E6 |

**Aporte a la investigación:** fundamento formal de la recuperación léxica. Justifica incorporar BM25 en la recuperación híbrida (E2), clave en IFMIF-DONES, donde abundan siglas (ICS, HEBT), isótopos (Be-7) y valores exactos que los embeddings densos representan mal.

### [4] RRF: fusión de rankings (baseline de la CI)

G. V. Cormack, C. L. A. Clarke, and S. Büttcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in *Proc. 32nd Int. ACM SIGIR Conf. Res. Develop. Inf. Retrieval (SIGIR)*, 2009, pp. 758–759, doi: 10.1145/1571941.1572114.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Conferencia | No aplica (CORE A*) | E2 a E4 (y baseline de E5) |

**Aporte a la investigación:** método estándar para fusionar las listas de BM25 y del buscador denso. Es el **baseline** contra el que se compara la fusión difusa (salto E4 → E5). Sin él, la mejora de la CI no tendría una referencia de comparación aceptada.

### [5] CRAG: verificación de la evidencia

S.-Q. Yan, J.-C. Gu, Y. Zhu, and Z.-H. Ling, "Corrective retrieval augmented generation," arXiv:2401.15884, 2024. [Online]. Available: https://arxiv.org/abs/2401.15884

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Preprint | No | E4 a E6 |

**Aporte a la investigación:** propone evaluar la calidad de lo recuperado antes de generar y clasificarlo en correcto, ambiguo o incorrecto, con una acción correctiva para cada caso. Justifica la **etapa 3 (verificación)** del pipeline. Sus categorías son naturalmente difusas, lo que motiva la versión con q-FCM (E6).

### [6] OWA: operador de la fusión difusa (CI 1)

R. R. Yager, "On ordered weighted averaging aggregation operators in multicriteria decisionmaking," *IEEE Trans. Syst., Man, Cybern.*, vol. 18, no. 1, pp. 183–190, 1988, doi: 10.1109/21.87068.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista histórica (anterior a SJR) | No | E5, E6 |

**Aporte a la investigación:** define el operador de agregación ponderada por orden que se usa para fusionar los puntajes de los buscadores como grados de pertenencia a "relevante". Es la **primera contribución de CI** (E5) y permite modelar el acuerdo entre evidencias, algo que RRF no captura.

### [7] Regla cuasi-no lineal para FCM (CI 2)

G. Nápoles, I. Grau, L. Concepción, L. Koutsoviti Koumeri, and J. P. Papa, "Modeling implicit bias with fuzzy cognitive maps," *Neurocomputing*, vol. 481, pp. 33–45, 2022, doi: 10.1016/j.neucom.2022.01.070.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | **Q1** | E6 |

**Aporte a la investigación:** introduce la regla de razonamiento cuasi-no lineal, $A^{(t+1)} = \varphi f(A^{(t)}W) + (1-\varphi)A^{(0)}$, que evita que el FCM "olvide" la evidencia inicial al converger. Es la base del **controlador de verificación de E6**, la contribución más original del sistema.

### [8] Computación evolutiva y LLM (CI 3)

X. Wu, S.-H. Wu, J. Wu, L. Feng, and K. C. Tan, "Evolutionary computation in the era of large language model: Survey and roadmap," *IEEE Trans. Evol. Comput.*, vol. 29, no. 2, pp. 534–554, 2025, doi: 10.1109/TEVC.2024.3506731.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | **Q1** | E6 |

**Aporte a la investigación:** sistematiza la línea "EA-enhanced LLM" y enmarca la **calibración evolutiva** de pesos y umbrales del pipeline. Uno de sus autores (Xingyu Wu) integra el Comité Científico del reto.

---

## Complementarias (8)

### [9] FCM: fundamento

B. Kosko, "Fuzzy cognitive maps," *Int. J. Man-Mach. Stud.*, vol. 24, no. 1, pp. 65–75, 1986, doi: 10.1016/S0020-7373(86)80040-2.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista histórica (anterior a SJR) | No | E6 |

**Aporte a la investigación:** artículo fundacional de los mapas cognitivos difusos. **Primera en volver al núcleo** si hay espacio: para un jurado de CI, citar el FCM original es lo esperable.

### [10] CMA-ES

N. Hansen, "The CMA evolution strategy: A tutorial," arXiv:1604.00772, 2016. [Online]. Available: https://arxiv.org/abs/1604.00772

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Preprint | No | E6 |

**Aporte a la investigación:** describe el algoritmo usado para calibrar offline φ, los pesos del q-FCM y los umbrales. **Segunda en volver.** Para el paper conviene citar la versión revisada: N. Hansen and A. Ostermeier, "Completely derandomized self-adaptation in evolution strategies," *Evol. Comput.*, 2001 (pendiente de verificar datos).

### [11] Lost in the middle: tamaño y orden del contexto

N. F. Liu et al., "Lost in the middle: How language models use long contexts," *Trans. Assoc. Comput. Linguistics*, vol. 12, pp. 157–173, 2024, doi: 10.1162/tacl_a_00638.

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | **Q1** | E1, E3 |

**Aporte a la investigación:** demuestra que los LLM usan peor la información situada en el medio de contextos largos. Justifica reducir el contexto de 10k a ~4k tokens y poner el pasaje más relevante primero.

### [12] Reranking con cross-encoder

R. Nogueira and K. Cho, "Passage re-ranking with BERT," arXiv:1901.04085, 2019. [Online]. Available: https://arxiv.org/abs/1901.04085

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Preprint | No | E3 a E6 |

**Aporte a la investigación:** propone el reranking con cross-encoder, segunda fase de la recuperación (E3). Sus puntajes alimentan además las señales de la verificación (E4 a E6).

### [13] C-Pack: modelos BGE

S. Xiao, Z. Liu, P. Zhang, N. Muennighoff, D. Lian, and J.-Y. Nie, "C-Pack: Packed resources for general Chinese embeddings," in *Proc. 47th Int. ACM SIGIR Conf. Res. Develop. Inf. Retrieval (SIGIR)*, 2024. [Online]. Available: https://arxiv.org/abs/2309.07597

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Conferencia | No aplica (CORE A*) | E1 a E6 |

**Aporte a la investigación:** documenta la familia BGE (embedder bge-base y reranker bge-reranker-base). Es una cita de herramienta; puede ir como nota al pie. **Pendiente:** páginas y DOI de la versión SIGIR.

### [14] Program of Thoughts: preguntas numéricas

W. Chen, X. Ma, X. Wang, and W. W. Cohen, "Program of thoughts prompting: Disentangling computation from reasoning for numerical reasoning tasks," *Trans. Mach. Learn. Res.*, 2023. [Online]. Available: https://arxiv.org/abs/2211.12588

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | No confirmado (SJR 0,744 en 2025, sin cuartil visible) | E4 a E6 |

**Aporte a la investigación:** separa el razonamiento del cálculo generando código que se ejecuta. Respalda la acción "pregunta numérica → PoT" de la verificación, útil en preguntas de DONES como la constante de decaimiento del Be-7.

### [15] FCM sin datos de entrenamiento

G. Nápoles et al., "Learning of fuzzy cognitive map models without training data," *Neurocomputing*, 2025. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S0925231225000815

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Revista | **Q1** | E6 |

**Aporte a la investigación:** justifica fijar los pesos iniciales del q-FCM a partir de conocimiento experto, dado que solo hay 25 preguntas de muestra. **Pendiente:** autores completos, volumen y DOI.

### [16] LLM-as-a-judge

L. Zheng et al., "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), Datasets and Benchmarks Track*, vol. 36, 2023. [Online]. Available: https://arxiv.org/abs/2306.05685

| Tipo | Cuartil | Estrategias |
|---|---|---|
| Conferencia | No aplica (CORE A*) | Evaluación local, E6 |

**Aporte a la investigación:** analiza la fiabilidad y los sesgos (verbosidad, posición) de los LLM como jueces. Respalda el juez local usado para comparar estrategias, el juez OLMo de la etapa 3 en E6 y la decisión de producir respuestas concisas.

---

## Resumen

| # | Referencia | Año | Tipo | Cuartil | Grupo | Estrategias |
|---|---|---|---|---|---|---|
| 1 | Lewis et al., RAG | 2020 | Conferencia | CORE A* | Núcleo | Todas |
| 2 | Team OLMo, Olmo 3 | 2025 | Preprint | No | Núcleo | Todas |
| 3 | Robertson y Zaragoza, BM25 | 2009 | Revista | Q1 probable | Núcleo | E2-E6 |
| 4 | Cormack et al., RRF | 2009 | Conferencia | CORE A* | Núcleo | E2-E5 |
| 5 | Yan et al., CRAG | 2024 | Preprint | No | Núcleo | E4-E6 |
| 6 | Yager, OWA | 1988 | Revista histórica | No | Núcleo | E5-E6 |
| 7 | Nápoles et al., q-FCM | 2022 | Revista | Q1 | Núcleo | E6 |
| 8 | Wu et al., EC + LLM | 2025 | Revista | Q1 | Núcleo | E6 |
| 9 | Kosko, FCM | 1986 | Revista histórica | No | Complementaria | E6 |
| 10 | Hansen, CMA-ES | 2016 | Preprint | No | Complementaria | E6 |
| 11 | Liu et al., Lost in the middle | 2024 | Revista | Q1 | Complementaria | E1, E3 |
| 12 | Nogueira y Cho, reranking | 2019 | Preprint | No | Complementaria | E3-E6 |
| 13 | Xiao et al., C-Pack | 2024 | Conferencia | CORE A* | Complementaria | E1-E6 |
| 14 | Chen et al., PoT | 2023 | Revista | No confirmado | Complementaria | E4-E6 |
| 15 | Nápoles et al., FCM sin datos | 2025 | Revista | Q1 | Complementaria | E6 |
| 16 | Zheng et al., LLM-as-a-judge | 2023 | Conferencia | CORE A* | Complementaria | Evaluación, E6 |

## Pendientes antes de enviar el paper

- Confirmar en cada DOI autores, páginas y volumen (varias referencias no se abrieron en esta revisión).
- Completar [13] (páginas y DOI) y [15] (autores, volumen, DOI).
- Confirmar cuartiles del año de publicación en https://www.scimagojr.com y rankings CORE en https://portal.core.edu.au/conf-ranks/.
- Citar también la página oficial del reto y el starter kit (fuentes del reto, no cuentan como referencias académicas).
- Renumerar según el orden de aparición en el texto del paper.
