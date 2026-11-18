# Speech — Proposta de Projeto Final

**Presentación:** *Mineração de textos e recuperação de informação para resposta a perguntas em domínios científicos especializados com LLMs* (SCC0233)
**Autores:** Cristhian J. Maylle Briceño · Jefferson D. Flores Montenegro

Cada texto dura **alrededor de 1 minuto** leído a ritmo normal (140–170 palabras). Contexto del reto: [../contexto-inicial/README.md](../contexto-inicial/README.md).

---

## Slide 1 — Título

### 🇪🇸 Español

Buenas tardes. Somos Cristhian Maylle y Jefferson Flores, y les presentamos nuestra propuesta de proyecto final: *minería de textos y recuperación de información para responder preguntas en dominios científicos especializados con LLMs*.

El proyecto nace de un reto real: el **IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs**, organizado por la IEEE Computational Intelligence Society junto con la Universidad de Granada. La idea del reto es someter a un modelo de lenguaje a una especie de **entrevista de trabajo para un puesto de experto**: tiene que responder preguntas que solo sabría alguien que conoce a fondo una instalación científica o una línea de investigación concreta.

Y debe hacerlo con recursos limitados: un modelo fijo, **OLMo 3.1 de 32 mil millones de parámetros**, **una sola GPU H100**, **una hora** para responder todas las preguntas y **sin acceso a internet**. En los próximos minutos explicamos el problema, los datos y cómo pensamos abordarlo.

### 🇧🇷 Português

Boa tarde. Somos Cristhian Maylle e Jefferson Flores, e apresentamos a nossa proposta de projeto final: *mineração de textos e recuperação de informação para resposta a perguntas em domínios científicos especializados com LLMs*.

O projeto nasce de um desafio real: o **IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs**, organizado pela IEEE Computational Intelligence Society junto com a Universidade de Granada. A ideia do desafio é submeter um modelo de linguagem a uma espécie de **entrevista de emprego para uma vaga de especialista**: ele precisa responder perguntas que só alguém que conhece a fundo uma instalação científica ou uma linha de pesquisa específica saberia responder.

E precisa fazer isso com recursos limitados: um modelo fixo, o **OLMo 3.1 de 32 bilhões de parâmetros**, **uma única GPU H100**, **uma hora** para responder todas as perguntas e **sem acesso à internet**. Nos próximos minutos, explicamos o problema, os dados e como pretendemos abordá-lo.

---

## Slide 2 — Problema, motivação e pergunta de pesquisa

### 🇪🇸 Español

Los LLMs generan respuestas fluidas y convincentes, pero no siempre correctas. Cuando no conocen un tema, tienden a **inventar** —lo que llamamos alucinación— o a responder sin apoyarse en evidencia.

En dominios científicos y técnicos esto es crítico, porque el conocimiento relevante **no está en el entrenamiento del modelo**: está disperso en documentos no estructurados, como artículos y reportes técnicos en PDF. Además, en el reto el modelo no ve el corpus por adelantado: solo puede consultarlo durante la evaluación, y ese corpus **incluye documentos distractores**. Entonces el problema central no es solo generar texto, sino **encontrar y seleccionar la evidencia correcta a tiempo**.

De ahí nuestra pregunta de investigación: **¿cómo influyen distintas estrategias de recuperación y selección de información textual en la precisión y la eficiencia de un LLM al responder preguntas especializadas?** Hablamos de precisión porque un juez automático marca cada respuesta como correcta o incorrecta, sin puntos parciales; y de eficiencia, porque todo el proceso debe caber en una hora.

### 🇧🇷 Português

Os LLMs geram respostas fluentes e convincentes, mas nem sempre corretas. Quando não conhecem um assunto, tendem a **inventar** —o que chamamos de alucinação— ou a responder sem se apoiar em evidências.

Em domínios científicos e técnicos isso é crítico, porque o conhecimento relevante **não está no treinamento do modelo**: está espalhado em documentos não estruturados, como artigos e relatórios técnicos em PDF. Além disso, no desafio o modelo não vê o corpus com antecedência: só pode consultá-lo durante a avaliação, e esse corpus **inclui documentos distratores**. Então o problema central não é só gerar texto, mas **encontrar e selecionar a evidência certa a tempo**.

Daí vem a nossa pergunta de pesquisa: **como diferentes estratégias de recuperação e seleção de informações textuais influenciam a precisão e a eficiência de um LLM ao responder perguntas especializadas?** Falamos de precisão porque um juiz automático marca cada resposta como correta ou incorreta, sem crédito parcial; e de eficiência, porque todo o processo precisa caber em uma hora.

---

## Slide 3 — Tipo de dado e tarefa

### 🇪🇸 Español

Nuestros datos son **no estructurados y predominantemente textuales**. Hay dos tipos: primero, **artículos científicos de inteligencia artificial**; segundo, **documentos técnicos sobre IFMIF-DONES**, un acelerador de partículas que se está construyendo en Granada, España, para probar los materiales de los futuros reactores de fusión nuclear.

Trabajamos con textos completos, resúmenes y contenido extraído de PDFs, con todo lo que eso implica: tablas, fórmulas, figuras y ruido de extracción.

Nuestro objetivo es **investigar y comparar estrategias de recuperación de información textual** para apoyar a un LLM. La tarea combina dos cosas: **recuperación de información**, es decir, encontrar los fragmentos relevantes dentro del corpus, y **respuesta a preguntas**, es decir, generar una respuesta concisa y fundamentada.

Las preguntas del reto son de cinco tipos, de dificultad creciente: **fácticas, comparativas, procedimentales, causales y predictivas**. Algunas piden un dato exacto de una tabla; otras exigen razonar o incluso calcular a partir de lo recuperado.

### 🇧🇷 Português

Os nossos dados são **não estruturados e predominantemente textuais**. Há dois tipos: primeiro, **artigos científicos de inteligência artificial**; segundo, **documentos técnicos sobre o IFMIF-DONES**, um acelerador de partículas que está sendo construído em Granada, na Espanha, para testar os materiais dos futuros reatores de fusão nuclear.

Trabalhamos com textos completos, resumos e conteúdo extraído de PDFs, com tudo o que isso implica: tabelas, fórmulas, figuras e ruído de extração.

O nosso objetivo é **investigar e comparar estratégias de recuperação de informação textual** para apoiar um LLM. A tarefa combina duas coisas: **recuperação de informação**, ou seja, encontrar os trechos relevantes dentro do corpus, e **resposta a perguntas**, ou seja, gerar uma resposta concisa e fundamentada.

As perguntas do desafio são de cinco tipos, em dificuldade crescente: **factuais, comparativas, procedimentais, causais e preditivas**. Algumas pedem um dado exato de uma tabela; outras exigem raciocinar ou até calcular a partir do que foi recuperado.

---

## Slide 4 — Dataset e fontes de dados

### 🇪🇸 Español

¿De dónde vienen los datos? El reto publica la lista de **32 sitios** de los que se tomó el corpus, y los agrupamos en cuatro bloques.

Primero, **inteligencia artificial y computación**: ACL Anthology, arXiv, ACM e IEEE Xplore. Segundo, **aceleradores y fusión**: las actas de JACoW, del CERN y de EUROfusion, donde está el conocimiento sobre IFMIF-DONES. Tercero, **editoriales multidisciplinares** como Springer, IOP o SAGE. Y cuarto, **repositorios y preprints** como bioRxiv o PubMed Central, que probablemente funcionan como distractores.

Para validar contamos con **25 pares de pregunta y respuesta de ejemplo**: diez de DONES y quince de papers de IA, que usaremos para comparar nuestras estrategias de forma local.

El benchmark oficial tiene **100 preguntas ocultas**, y la nota es una **precisión balanceada**: cada dominio pesa la mitad, sin importar cuántas preguntas tenga. Por eso no podemos descuidar ninguno de los dos dominios.

### 🇧🇷 Português

De onde vêm os dados? O desafio publica a lista dos **32 sites** dos quais o corpus foi coletado, e nós os agrupamos em quatro blocos.

Primeiro, **inteligência artificial e computação**: ACL Anthology, arXiv, ACM e IEEE Xplore. Segundo, **aceleradores e fusão**: os anais da JACoW, do CERN e da EUROfusion, onde está o conhecimento sobre o IFMIF-DONES. Terceiro, **editoras multidisciplinares** como Springer, IOP ou SAGE. E quarto, **repositórios e preprints** como bioRxiv ou PubMed Central, que provavelmente funcionam como distratores.

Para validação, contamos com **25 pares de pergunta e resposta de exemplo**: dez do DONES e quinze de artigos de IA, que vamos usar para comparar as nossas estratégias localmente.

O benchmark oficial tem **100 perguntas ocultas**, e a nota é uma **acurácia balanceada**: cada domínio vale metade, independentemente de quantas perguntas tenha. Por isso, não podemos descuidar de nenhum dos dois domínios.

---

## Slide 5 — Referências

### 🇪🇸 Español

Estas referencias resumen la base de nuestra metodología. Partimos de **RAG**, la generación aumentada por recuperación de Lewis y colaboradores, aplicada sobre **OLMo 3**, el modelo que impone el reto.

Para la recuperación léxica usaremos **BM25**, que funciona muy bien con términos técnicos exactos, como nombres de isótopos o de métodos, y lo combinaremos con búsqueda por embeddings mediante **Reciprocal Rank Fusion**. Para controlar la calidad de lo recuperado nos inspiramos en **Corrective RAG**, que evalúa si la evidencia es suficiente antes de responder.

Además, en la fase final del reto un jurado asigna un **40 % de la nota a la innovación con inteligencia computacional**. Por eso exploraremos la agregación con **operadores OWA de Yager**, los **mapas cognitivos difusos** y la **computación evolutiva** para ajustar el pipeline.

Compararemos todas estas estrategias contra los baselines del reto —respuesta directa sin recuperación y RAG simple—, midiendo precisión y tiempo. Muchas gracias.

### 🇧🇷 Português

Estas referências resumem a base da nossa metodologia. Partimos do **RAG**, a geração aumentada por recuperação de Lewis e colaboradores, aplicada ao **OLMo 3**, o modelo imposto pelo desafio.

Para a recuperação léxica, vamos usar o **BM25**, que funciona muito bem com termos técnicos exatos, como nomes de isótopos ou de métodos, e vamos combiná-lo com busca por embeddings usando **Reciprocal Rank Fusion**. Para controlar a qualidade do que é recuperado, nos inspiramos no **Corrective RAG**, que avalia se a evidência é suficiente antes de responder.

Além disso, na fase final do desafio, um júri atribui **40% da nota à inovação com inteligência computacional**. Por isso, vamos explorar a agregação com **operadores OWA de Yager**, os **mapas cognitivos fuzzy** e a **computação evolutiva** para ajustar o pipeline.

Vamos comparar todas essas estratégias com os baselines do desafio —resposta direta sem recuperação e RAG simples—, medindo precisão e tempo. Muito obrigado.

---

## Notas sobre las diapositivas

- En la slide 5 el pie dice **"Pag. 4"**; debería ser **"Pag. 5"**.
- En la slide 4 el bloque "Repositórios, Preprints" no menciona arXiv, que está en el bloque de IA; está bien así, pero si alguien pregunta, arXiv también es un repositorio de preprints.
