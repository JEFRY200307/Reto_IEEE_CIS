# 3. Reglas y bases oficiales

**Fuentes:** [Join the Challenge](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/join-the-challenge/) · [Codabench — Terms](https://www.codabench.org/competitions/17954/) · [Bases oficiales (PDF)](https://cis.taskforce.ieee.org/gpais/wp-content/uploads/sites/6/2026/09/IEEE-CIS-Technical-Challenge-on-Domain-Specific-Question-Answering-with-LLMs-Contest-Rules.pdf) (copia local: [recursos/bases-oficiales-contest-rules.pdf](recursos/bases-oficiales-contest-rules.pdf))

## Reglas de la competición

### Elegibilidad y equipos

- Equipos de **máximo 4 miembros**.
- Cada participante debe llenar **individualmente** el [formulario de inscripción](https://forms.gle/F7YHkE7PALziNpqk6) con el **mismo correo de su cuenta de Codabench**. La solicitud en Codabench se aprueba solo después de llenar el formulario.
- Los equipos se gestionan como **organizaciones** en Codabench.
- Una persona solo puede participar como **un único participante**: individualmente **o** en un solo equipo (no ambas cosas, ni en varios equipos).
- Edad mínima: **18 años**. Cada miembro del equipo debe cumplir los requisitos por su cuenta.

### Requisitos del código

- Se ejecuta en el entorno de evaluación con **1 GPU H100**.
- **Tiempo máximo: 1 hora** (2 horas en el Private Leaderboard). Cubre **todo**: carga del modelo y del índice, preprocesamiento e inferencia de todas las preguntas. Si se excede, el envío se cancela y se marca como fallido.
- Dependencias **preinstaladas** en un entorno común (ver [08-entorno-y-dependencias.md](08-entorno-y-dependencias.md)).
- **Sin internet** durante la evaluación. Internet solo se puede usar **antes**, para preparar archivos auxiliares (índices, embeddings, prompts, etc.) que se incluyen en el envío.

### Entrega

- **Límite estricto de 1 GB** (descomprimido).
- **1 envío por día por equipo.**
- Se envía: código de inferencia + archivos auxiliares (adaptadores, índices de recuperación, plantillas de prompts, archivos de reglas…).
- Se envía también un **borrador de la metodología**. Para la Fase 2: **paper de 4 páginas en formato IEEE** (la plantilla se dará más adelante). Si es en equipo, debe indicarse claramente; solo se considera un envío por equipo.

### Juego limpio

- Se permiten **datos externos libres y públicos**, siempre que se **citen correctamente**.
- Cualquier intento de **manipular, atacar o hacer jailbreak al LLM juez** = **descalificación inmediata**.

## Resumen de las bases legales (Official Rules, PDF de 4 páginas)

| Sección | Contenido |
|---------|-----------|
| **No se requiere pago** | No hace falta comprar ni pagar nada para participar o ganar. |
| **Patrocinador** | The Institute of Electrical and Electronics Engineers, Inc. (IEEE), 445 Hoes Lane, Piscataway, NJ 08854, EE. UU. |
| **Elegibilidad** | Abierto a empleados del IEEE excepto los de la unidad *IEEE Technical Activities*. Participantes de EE. UU. y otros países donde la ley lo permita, **mayores de 18 años**. "Participante" = individuo o equipo registrado como organización en la plataforma. |
| **Aceptación** | Al participar se aceptan las bases. El IEEE puede modificarlas en cualquier momento y sus decisiones son finales. |
| **Período** | 28 sep 2026 00:00 UTC – 30 nov 2026 23:59 UTC. UTC es el reloj oficial. |
| **Cómo participar** | Registrarse en [Codabench](https://www.codabench.org), solicitar unirse a la [competición 17954](https://www.codabench.org/competitions/17954/). La aprobación depende del IEEE. El **primer envío válido** constituye la inscripción. Los envíos pasan a ser propiedad del patrocinador. |
| **Selección de ganadores** | Dos etapas: Fase 1 (ranking automático en Codabench) y Fase 2 (revisión de expertos). El ranking final se publica solo en https://cis.taskforce.ieee.org/gpais/leaderboard. El IEEE puede verificar la validez de cada envío. |
| **Premios** | 1.º USD 9 000 · 2.º USD 5 000 · 3.º USD 3 000 · 4.º USD 1 500 · 5.º USD 1 500. No hay sustitución en efectivo; los impuestos corren por cuenta del ganador. |
| **Notificación** | Por correo, dentro de los 14 días posteriores a la selección. Si un ganador no es elegible, se elige otro con el mismo procedimiento. |
| **Liberación y publicidad** | Los envíos no se devuelven. El ganador libera al IEEE de reclamaciones derivadas de la participación. El IEEE no se responsabiliza por fallos técnicos, de red o envíos perdidos. |
| **Declaraciones sobre el envío** | Garantizas que tienes todos los derechos sobre el envío, que es **obra original tuya**, no publicada antes, y que no infringe derechos de terceros. |
| **Limitación de responsabilidad** | El IEEE puede **descalificar** a quien manipule o abuse del proceso, y cancelar/modificar el concurso por fallos técnicos o manipulación. |
| **Disputas** | Arbitraje individual (sin demandas colectivas) bajo la American Arbitration Association; ley del estado de **Nueva Jersey**. |
| **Resultados** | Para conocer los ganadores o pedir copia de las bases: carta a Thomas Compton, IEEE, 445 Hoes Lane, Piscataway, NJ 08854. |
