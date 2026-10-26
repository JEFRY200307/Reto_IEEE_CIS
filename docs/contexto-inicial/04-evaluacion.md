# 4. Evaluación

**Fuentes:** [Evaluation (página oficial)](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/evaluation/) · [Codabench — fases](https://www.codabench.org/competitions/17954/)

La evaluación tiene **dos fases** y mide tres cosas: **precisión balanceada por dominio**, **juicio experto sobre las respuestas** e **innovación técnica**.

---

## Fase 1 — Evaluación automática (Codabench)

### Veredicto por pregunta

Un **LLM juez oculto** (su identidad se revela al final) da un veredicto binario por cada pregunta:

$$
v_i \in \{0, 1\}, \qquad v_i = 1 \text{ si la respuesta se juzga correcta, } 0 \text{ en caso contrario (sin crédito parcial)}
$$

### Precisión balanceada por dominio

Sea $\mathcal{D}$ el conjunto de preguntas de IFMIF-DONES y $\mathcal{P}$ el de papers de IA, con $N_\mathcal{D}$ y $N_\mathcal{P}$ preguntas respectivamente:

$$
A = \frac{1}{2}\left(\frac{1}{N_\mathcal{D}}\sum_{i \in \mathcal{D}} v_i \;+\; \frac{1}{N_\mathcal{P}}\sum_{i \in \mathcal{P}} v_i\right)
$$

El dominio más pequeño **pesa lo mismo** que el más grande.

- **Desempate:** tiempo total de inferencia (segundos) para todas las preguntas. **Menos es mejor.**
- **Public Leaderboard:** se evalúa sobre el **50 %** del benchmark. Es solo orientativo.
- **Private Leaderboard:** al cerrar los envíos, se reevalúa tu **mejor** envío público sobre el **100 %** del benchmark (límite de 2 h). Este define el ranking final de la Fase 1.
- En Codabench el leaderboard muestra dos columnas: *Domain-Balanced Accuracy* (desc.) e *Inference time (seconds)* (asc.). Regla de envío: **Force_Best** (cuenta tu mejor envío).
- **No ves ninguna salida** de tu código: solo el estado (*Finished* / *Failed*) y la puntuación.

---

## Fase 2 — Evaluación de expertos

Pasan las **20 mejores soluciones** de la Fase 1 (o menos, si hay menos envíos).

### Puntuación final

$$
\text{Final}(s) = 0.30 \cdot A + 0.30 \cdot Q(s) + 0.40 \cdot I(s)
$$

| Componente | Peso |
|------------|------|
| $A$ — precisión balanceada de la Fase 1 | **30 %** |
| $Q(s)$ — evaluación cualitativa de las respuestas por expertos del dominio | **30 %** |
| $I(s)$ — innovación técnica (Comité Científico) | **40 %** |

### Construcción de la puntuación φ (para Q e I)

Cada revisor **ordena** las $M$ soluciones preseleccionadas y además indica la **diferencia de calidad** entre cada par de posiciones consecutivas:

$$
g_k \in \{0, 1, 2, 3\} \quad (\text{empate} = 0,\ \text{leve} = 1,\ \text{clara} = 2,\ \text{decisiva} = 3)
$$

Estas brechas se acumulan **de abajo hacia arriba** y se normalizan entre 0 y 1:

$$
u_M = 0, \qquad u_k = u_{k+1} + g_k \quad (k = M-1, \ldots, 1), \qquad \varphi(k) = \frac{u_k}{u_1}
$$

Así, el primero obtiene $\varphi = 1$, el último $\varphi = 0$, y los intermedios reflejan **la magnitud** de las diferencias, no solo el orden. Caso degenerado (todas las brechas empatadas): $\varphi(k) = 0.5$ para todo $k$.

### Evaluación cualitativa, Q(s)

Un panel de **expertos de cada dominio** (seleccionado por separado para cada uno) lee las respuestas de cada solución y las ordena **por pregunta**. Con $K_\mathcal{D}$, $K_\mathcal{P}$ revisores por dominio:

$$
Q(s) = \frac{1}{2}\left[\frac{1}{K_\mathcal{D} N_\mathcal{D}}\sum_{k=1}^{K_\mathcal{D}}\sum_{i \in \mathcal{D}} \varphi_{i,k}(s) \;+\; \frac{1}{K_\mathcal{P} N_\mathcal{P}}\sum_{k=1}^{K_\mathcal{P}}\sum_{i \in \mathcal{P}} \varphi_{i,k}(s)\right]
$$

La identidad de estos revisores no se revela hasta el final.

### Innovación técnica, I(s)

Cada uno de los $J$ miembros del **Comité Científico** ordena las soluciones **una vez** según el **uso adecuado de técnicas de Inteligencia Computacional** y la **originalidad del enfoque**:

$$
I(s) = \frac{1}{J}\sum_{j=1}^{J} \varphi_j(s)
$$

La innovación se juzga a partir del **paper de 4 páginas en formato IEEE**.

---

Ver composición del Comité Científico en [09-premios-y-organizacion.md](09-premios-y-organizacion.md).
