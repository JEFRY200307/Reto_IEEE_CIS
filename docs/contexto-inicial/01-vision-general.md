# 1. Visión general del reto

**Fuentes:** [Página oficial](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/) · [Codabench — The Challenge](https://www.codabench.org/competitions/17954/) · [Video de presentación](https://youtu.be/e-Bnc7yLDWg)

## Video de presentación

- **Título:** *The 2026 IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs*
- **Canal:** [IEEE CIS Task Force on GPAIS](https://www.youtube.com/@IEEECISTaskForceonGPAIS)
- **Enlace:** https://youtu.be/e-Bnc7yLDWg

## La idea: una "entrevista de trabajo" para un LLM

A los LLM se les suele pedir tareas que casi cualquiera podría hacer (redactar un correo, resumir un informe). Este reto propone otra cosa: someter al modelo a una **entrevista para un puesto de experto interno muy especializado**. Las preguntas no son de cultura general, sino las que se hacen entre sí los colegas expertos: cómo se diseñó una instalación, un proceso o un sistema concreto y cómo funciona día a día.

Ese conocimiento vive en un **corpus privado y especializado**, y responder bien exige más que encontrar el pasaje correcto: requiere el **criterio de un experto** cuando el texto no da la respuesta de forma directa.

## Por qué es difícil

- Los LLM de propósito general tienen mucho conocimiento del mundo, pero su rendimiento **cae mucho** ante conocimiento técnico especializado y novedoso.
- Un modelo que "pasa la entrevista" puede usarse como **asistente**: consulta la documentación técnica privada, responde preguntas fundamentadas y apoya decisiones reales. La ambición a futuro es darle más autonomía (asistente activo que asume tareas, a veces críticas).
- Verificar ese conocimiento antes es el primer paso, y es lo que mide esta competición.

## Objetivos

El reto se centra solo en **preguntas y respuestas (Q&A) en un dominio concreto**. Partiendo del conocimiento general de un LLM, busca:

1. **Diseñar una estrategia de adaptación** para que el modelo dé respuestas más precisas en dominios muy especializados.
2. **Hacerlo con recursos computacionales realistas**, porque los entornos técnicos de estos dominios suelen tener recursos limitados.

Aquí entra la **Inteligencia Computacional (CI)**: estrategias de adaptación que no dependen de escalar el modelo, de hacer ajuste fino masivo ni de usar grandes cantidades de datos.

### Líneas de investigación sugeridas

- Ajuste fino eficiente en parámetros (PEFT, p. ej. LoRA)
- Ingeniería de prompts
- Mejora con grafos de conocimiento
- Fusión dinámica de conocimiento
- Modelado difuso (fuzzy) de conocimiento incierto

## Dominios objetivo

| Código | Dominio | Descripción |
|--------|---------|-------------|
| **D** | **IFMIF-DONES** | *International Fusion Materials Irradiation Facility – DEMO Oriented Neutron Source.* Acelerador de partículas en construcción en Granada, España. Gran infraestructura científica: alta complejidad y criticidad operativa. |
| **P** | **Literatura de investigación en IA** | Papers muy especializados producidos por institutos de investigación universitarios. Trabajo científico denso y en rápida evolución. |

Estos dos dominios sirven para medir **qué tan bien se adapta** un método a un campo especializado y **cuánto generaliza** esa adaptación.

## Conjunto de evaluación

- **100 pares pregunta–respuesta** seleccionados por expertos de ambos dominios. **Nunca se publica.**
- Elaborados con una metodología sistemática de obtención de conocimiento.
- **Tipos de pregunta** (dificultad creciente): **fácticas, comparativas, procedimentales, causales y predictivas**. Se evalúan distintos niveles de razonamiento, desde recordar un dato hasta inferencia comparativa, causal y predictiva.
- **Respuestas de referencia deliberadamente concisas**, para que un LLM juez pueda verificar la corrección de forma automática y fiable.

Ver detalles de evaluación en [04-evaluacion.md](04-evaluacion.md) y ejemplos en [07-dataset-de-muestra-y-corpus.md](07-dataset-de-muestra-y-corpus.md).

## Organización

Organiza el **IEEE CIS Task Force on Large Language Models and Computational Intelligence for General-Purpose AI Systems (GPAIS)**, parte de la IEEE Computational Intelligence Society. Es la continuación del reto **FLAME 2024** (*Fusing Large Language Models with Computational Intelligence*). Colaboran **DaSCI** (Instituto Andaluz de Investigación en Ciencia de Datos e Inteligencia Computacional) e **IFMIF-DONES Granada**.

Más detalles en [09-premios-y-organizacion.md](09-premios-y-organizacion.md).
