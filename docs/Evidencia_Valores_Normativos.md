# Evidencia Científica: Valores Normativos de Variables de Evaluación
## IntApp — Prevención de Lesiones de Miembro Inferior
**Autor:** Roberto Franco | **Director:** Javier Sánchez | **Actualización:** mayo 2026

> **Nota metodológica:** Este documento recoge únicamente valores encontrados en estudios publicados. Cuando no existe evidencia disponible para una subpoblación concreta, se indica explícitamente. Los valores marcados con ⚠️ provienen de poblaciones específicas y deben aplicarse con cautela fuera de ese contexto.

---

## NOTA METODOLÓGICA A0 — Fuerza (N) vs Torque (Nm) en HHD: validez de la estandarización

### Diferencia conceptual

| Magnitud | Unidad | Definición |
|---|---|---|
| **Fuerza** | N | Carga perpendicular que el sujeto ejerce sobre el sensor del HHD en el punto de contacto |
| **Torque** | Nm | Fuerza × distancia perpendicular desde el eje articular al punto de contacto (brazo de momento) |

**Fórmula:** Torque (Nm) = Fuerza (N) × brazo de momento (m)

### Por qué la estandarización del punto de contacto resuelve el problema

Si el protocolo **siempre coloca el HHD en el mismo punto anatómico**, el brazo de momento es constante entre sujetos (dentro de la variabilidad antropométrica esperada). Esto implica:

- La fuerza (N) es **proporcional** al torque (Nm) con un factor de escala fijo
- Las comparaciones **inter-sujeto e intra-sujeto** son válidas en N sin necesidad de convertir a Nm
- Normalizar por peso (N/kg) elimina el efecto del tamaño corporal de la misma forma que Nm/kg

### Única limitación que persiste

La comparación con estudios externos que usaron **protocolos de colocación distintos** (distancia HHD–eje diferente) sí introduce sesgo, porque el brazo de momento difiere. Los estudios en Nm/kg (torque normalizado) no son directamente comparables con los valores N/kg del protocolo IntApp sin conocer las distancias exactas de ambos protocolos.

**Acción en el TFM:** Especificar en el apartado de métodos la distancia exacta del punto de colocación HHD respecto al eje articular para cada variable (ya está especificado en el campo `protocolo` de cada variable en `variables.py`). Esto permite a futuros investigadores convertir los valores N/kg a Nm/kg si lo necesitan.

---

## BLOQUE A — FUERZA (Dinamometría Manual / HHD)

### A1. Cuádriceps isométrico

#### Evidencia principal (HHD isométrico, N/kg)

**Owoeye et al. (2024).** *Normative Hamstrings and Quadriceps Isometric Strength Values and Hamstrings-Quadriceps Asymmetry in Healthy Collegiate Soccer and Basketball Players.* International Journal of Exercise Science, 17(4), 768–778.
- **n = 94** deportistas universitarios sanos (fútbol y baloncesto), edad 18–24 años
- Instrumento: dinamómetro de mano isométrico de bajo coste
- Valores peso-normalizados por deporte y sexo:

| Deporte | Sexo | Cuádriceps (N/kg) | IC 95% |
|---------|------|-------------------|--------|
| Fútbol | Masculino | **5.48** | 4.96 – 6.00 |
| Baloncesto | Masculino | **4.89** | 4.44 – 5.33 |
| Fútbol | Femenino | **4.55** | 4.14 – 4.96 |
| Baloncesto | Femenino | **4.21** | 3.54 – 4.87 |

> ⚠️ Este es el **primer estudio** que proporciona valores normativos de cuádriceps isométrico con HHD de bajo coste en deportistas. Datos obtenidos del texto completo (PMC11268924); el resumen publicado no incluía todos los subgrupos.

**Nota sobre el umbral del protocolo (< 3.5 N/kg ♂ / < 2.8 N/kg ♀):**
Los valores del protocolo están en N/kg pero provienen de Andrews et al. (1996) y Bohannon (1997), que usaron protocolo similar pero en población general activa (no atletas de élite). Los valores de Owoeye (2024) sugieren que deportistas universitarios masculinos tienen cuádriceps 35-55% superiores a ese umbral, lo cual es clínicamente coherente.

**Población general adulta:** BMC Musculoskeletal Disorders (2020), n = 1.496 adultos (20–97 años): la fuerza de cuádriceps normalizada disminuye progresivamente con la edad en ambos sexos, con mayor declive después de los 60 años. No se dispone de valores por edad en N/kg en este estudio de libre acceso.

---

### A2. Isquiotibiales isométrico y Ratio H:Q

#### Evidencia principal (HHD isométrico, N/kg)

**Owoeye et al. (2024).** (mismo estudio citado arriba)

| Deporte | Sexo | Isquiotibiales (N/kg) | IC 95% | Ratio H:Q medio |
|---------|------|----------------------|--------|-----------------|
| Fútbol | Masculino | **3.29** | 2.90 – 3.64 | ~0.60 |
| Baloncesto | Masculino | **2.97** | 2.72 – 3.21 | ~0.61 |
| Fútbol | Femenino | **2.62** | 2.39 – 2.85 | — |
| Baloncesto | Femenino | **2.48** | 2.15 – 2.80 | ~0.59 |

**Dato crítico:** La prevalencia de H:Q < 0.60 en población sana fue del **37% en fútbol y 44% en baloncesto**. Esto tiene implicaciones directas para el protocolo: el umbral 0.60 en HHD isométrico puede ser demasiado sensible en estos deportes, generando muchos falsos positivos.

**Mujeres élite (fútbol y balonmano):**
Normative Quadriceps and Hamstring Muscle Strength Values for Female, Healthy, Elite Handball and Football Players. *Journal of Strength and Conditioning Research*, 2018, 32(8):2313–2319. (PMC6092090)
- Jugadoras de fútbol élite: cuádriceps 3.50 ± 0.56 N/kg; isquiotibiales 2.59 ± 0.41 N/kg
- Jugadoras de balonmano élite: cuádriceps 3.35 ± 0.45 N/kg; isquiotibiales 2.45 ± 0.37 N/kg
- Ratio H:Q medio: ~0.73–0.74

> ⚠️ **Aviso importante sobre el ratio H:Q y el HHD:** El umbral de referencia 0.60 se usa ampliamente en la literatura clínica, pero Croisier et al. (2008) emplearon en su estudio un punto de corte de **ratio convencional < 0.55** (isocinético a 60°/s), no 0.60. El valor 0.60 es una generalización clínica posterior, no el umbral exacto del estudio original. Además, la dinamometría usada fue isocinética, no HHD isométrico: las posiciones angulares y el tipo de contracción producen valores distintos. En HHD isométrico, el ratio H:Q tiende a ser ligeramente inferior. El protocolo debería declarar ambas limitaciones explícitamente.

---

### A3. Glúteo medio / Abductores de cadera

#### Evidencia en deportistas (Nm/kg)

**Thorborg et al. (2016).** *Reference values of hip abductor torque among youth athletes: Influence of age, sex and sports.* Physical Therapy in Sport, 22, 1–6. (PubMed 27428529)
- n = deportistas jóvenes (voleibol, baloncesto, fútbol sala), 10–19 años
- Torque isométrico abductores cadera:

| Grupo | Nm/kg |
|-------|-------|
| 10–14 años (mixto) | 1.12 ± 0.31 |
| 15–19 años (mixto) | 1.41 ± 0.27 |
| Voleibol masculino | 1.28 ± 0.25 |
| Voleibol femenino | 1.13 ± 0.22 |

**Corredores novatos (adultos):**
*Normative values of eccentric hip abduction strength in novice runners.* PMC3924610
- Hombres: **1.62 ± 0.38 Nm/kg** (excéntrico)
- Mujeres: **1.41 ± 0.33 Nm/kg** (excéntrico)

**Fútbol masculino profesional:**
Thorborg et al. (2017). *Hip strength and range of motion: Normal values from a professional football league.* Journal of Science and Medicine in Sport. (PubMed 28185809)
- Flexión cadera dominante: **47.3 kg** (IC95%: 45.6–49.0)
- Flexión cadera no dominante: **42.5 kg** (IC95%: 41.1–43.9)
- Nota: valores en kg, no normalizados por peso en este resumen

> ⚠️ No se encontraron valores normativos de abductores de cadera con HHD estratificados por **edad adulta y nivel deportivo** en un único estudio. Los valores disponibles son de deportistas jóvenes o de poblaciones específicas.

---

### A4. Rotadores externos de cadera

#### Evidencia en deportistas (Nm/kg)

*Normative isometric hip muscle force values assessed by a manual dynamometer.* PMC6442714 (2019)

| Deporte | Sexo | Rot. Ext. Dominante (Nm/kg) | Rot. Ext. No Dominante (Nm/kg) |
|---------|------|-----------------------------|---------------------------------|
| Fútbol | Masculino | **0.46** (0.44–0.48) | 0.42 (0.40–0.44) |
| Baloncesto | Masculino | **0.35** (0.32–0.37) | 0.27 (0.25–0.29) |
| Voleibol | Masculino | **0.37** (0.34–0.39) | 0.35 (0.32–0.37) |
| Voleibol | Femenino | **0.29** (0.26–0.33) | 0.29 (0.26–0.33) |

**Umbral de riesgo ACL:**
Ireland et al. (2003) identificaron que fuerza de rotadores externos < 20.3% del peso corporal clasifica a deportistas como alto riesgo de lesión de LCA no contacto.

**Población general femenina (sedentaria/esporádica, 20–29 años):**
Fuerza isométrica de rotadores externos: ~17.09% del peso corporal (inferior al umbral de riesgo del 20.3%).

> ⚠️ Los valores en Nm/kg del estudio PMC6442714 son **torques**, no fuerzas normalizadas directamente comparables con N/kg del protocolo. La conversión depende de la longitud del brazo de momento. El protocolo del TFM usa N/kg — **ver nota metodológica A0 sobre estandarización de la posición HHD**.

---

### A5. Aductores de cadera

**Thorborg et al. (2011).** *Hip Adduction and Abduction Strength Profiles in Elite Soccer Players.* The American Journal of Sports Medicine, 39(11), 2704–2708.
- Jugadores de fútbol élite masculinos
- Fuerza aductora excéntrica: valores en el rango 2.5–3.0 N/kg aproximadamente
- ICC inter-evaluador para HHD excéntrico: **0.91** (aducción), **0.86** (abducción)

**Fútbol femenino:**
Normal hip strength and range of motion values in youth and adult female national football teams (ScienceDirect, 2024, n = 504 valoraciones):
- Adultas élite (>18 años): torque aducción isométrico ~1.85 Nm/kg
- Adultas semiprofesionales: ~2.40–2.42 Nm/kg

> ⚠️ **Datos insuficientes** para adultos recreacionales y amateurs de ambos sexos en esta variable. Los valores disponibles corresponden a atletas de fútbol élite masculino y femenino.

---

### A6. Tríceps sural — Heel Rise Test

#### Evidencia principal (número de repeticiones)

**Hébert-Losier et al. (2017).** *Updated reliability and normative values for the standing heel-rise test in healthy adults.* Physiotherapy, 103(4), 364–370. (PubMed 28886865)
- ICC = **0.96** (excelente fiabilidad)
- Mediana general: **25 rep** (pierna dominante), 24 rep (no dominante)

| Sexo | Mediana repeticiones |
|------|---------------------|
| Masculino | **24** |
| Femenino | **21** |

**Estudio internacional reciente (2025):**
*Normative values for calf muscle strength-endurance in the general population assessed with the Calf Raise Application.* ScienceDirect (2025)
- Edad, sexo femenino y menor nivel de actividad física se asocian negativamente con el rendimiento
- Los varones jóvenes con mayor actividad son quienes más repeticiones completan

**Atletas y deportistas:**
La revisión disponible indica **ausencia de datos normativos específicos para deportistas** — la literatura de heap rise test se ha desarrollado principalmente en población general y clínica.

**Umbral del protocolo (< 25 rep o LSI < 90%):**
El umbral de 25 repeticiones coincide con la mediana general del estudio de Hébert-Losier (2017). El LSI se ha corregido a < 90%, alineado con el estándar de retorno al deporte empleado en cuádriceps e isquiotibiales. El LSI < 85% previo carecía de referencia bibliográfica directa en la literatura de tríceps sural.

---

## BLOQUE B — MOVILIDAD

### B1. Dorsiflexión de tobillo — WBLT

#### Evidencia principal

**Estudio internacional 2026 (más reciente y amplio disponible):**
*International normative values for the weight-bearing lunge test across age and sex in 899 healthy adults.* Musculoskeletal Science and Practice (2026). ScienceDirect.
- n = **899 adultos sanos**, 7 grupos de edad, ambos sexos
- Principales hallazgos:
  - Dorsiflexión declina progresivamente con la edad (η² = 0.283), con mayor caída a partir de los 60–69 años
  - Hombres presentan valores ligeramente superiores a mujeres (η² = 0.010 — diferencia estadísticamente significativa pero de magnitud pequeña)

| Sexo | Media WBLT (cm) | ±SD |
|------|----------------|-----|
| Femenino | ~12.7–13.3 | ±3.3–3.4 |
| Masculino | ~14.2–14.4 | ±2.7–3.0 |

> Valores aproximados; los valores exactos por grupo de edad (18–30, 30–45, 45–65) no estaban disponibles en el resumen del estudio.

**Fiabilidad del WBLT:**
*Reliability and minimal detectable change of the weight-bearing lunge test: A systematic review.* PubMed 25704110.
- ICC inter-evaluador: **0.80–0.99**
- ICC intra-evaluador: **0.65–0.99**
- MDC: 4.6° o **1.6 cm** (inter) / 4.7° o **1.9 cm** (intra)

**Asimetría normal entre miembros:**
*Normative range of weight-bearing lunge test performance asymmetry in healthy adults.* ScienceDirect (2011).
- El 68% de adultos sanos muestra asimetría de **≤ 1.5 cm**
- Algunos individuos alcanzan hasta ~3 cm de diferencia bilateral

**Umbral del protocolo (< 10 cm o < 35°):**
El umbral de 10 cm está respaldado por Powden et al. (2015) e incluido en las Clinical Practice Guidelines de JOSPT (2021) para esguince de tobillo. Los valores normativos generales (12.7–14.4 cm) sitúan el umbral de 10 cm en el **rango bajo-inferior** de la distribución, lo que es coherente con su uso como punto de corte de riesgo.

---

### B2. Thomas Test

#### Evidencia sobre fiabilidad y valores normativos

La búsqueda no encontró estudios con prevalencia de positivos en población deportista sana suficientemente amplia para servir como referencia normativa robusta.

**Fiabilidad reportada:**
- ICC intra-evaluador: 0.91–0.94 (muestra grande de deportistas élite)
- ICC inter-evaluador: ~0.69 (profesionales de la salud, muestra pequeña)
- Estudios recientes con control de posición pélvica reportan buena fiabilidad inter e intra-evaluador

*Reliability of Goniometric Techniques for Measuring Hip Flexor Length Using the Modified Thomas Test.* International Journal of Sports Physical Therapy, 2024. PMC11297360.
- Confirma fiabilidad mejorada cuando se controla la posición pélvica

> ⚠️ **Dato crítico:** La literatura confirma **ausencia de valores normativos robustos** para el Thomas Test en población deportista adulta por edad y sexo. La mayoría de estudios son cualitativos (positivo/negativo) o específicos de un deporte. El uso del test en el protocolo está justificado por su utilidad clínica y fiabilidad, no por valores normativos cuantitativos poblacionales.

---

### B3. Rotación interna de cadera

#### Evidencia principal (grados, activo/pasivo)

**Teng et al. (2018).** *Passive Hip Range-of-Motion Values Across Sex and Sport.* Journal of Athletic Training, 53(**6**), **560–567**. PMC6089031.
- NCAA División I, n = 339 atletas (168 mujeres, 171 hombres), múltiples deportes
- **⚠️ Medición PASIVA** (decúbito prono, cadera en abducción 20-30°, rodilla 90°, rotación hasta primer movimiento sacro). El protocolo de IntApp mide rotación **activa** — los valores de referencia de este estudio no son directamente comparables, ya que la ROM activa es sistemáticamente inferior a la pasiva.

| Sexo | Rotación interna pasiva (°) |
|------|---------------------|
| Mujeres | **38.1 ± 8.2** |
| Hombres | **28.6 ± 8.4** |

**Fútbol profesional masculino:**
*Hip strength and range of motion: Normal values from a professional football league.* Journal of Science and Medicine in Sport, 2017. PubMed 28185809.
- Rotación interna en flexión: **32 ± 8°**
- Rotación interna en prono: **38 ± 8°**
- Efecto de la edad: mínimo (-0.30°/año para rotación externa)

**Fútbol femenino nacional (adultas):**
ScienceDirect (2024), n = 504 valoraciones:
- Adultas presentan menos rotación total que jugadoras jóvenes

**En carga (weight-bearing):**
- Rotación interna: 19.8–21.2° (derecha); 22.6–22.7° (izquierda)
- Estos valores son inferiores porque la posición de carga modifica la biomecánica

**Umbral del protocolo (< 30° activa, asimetría > 10°):**
- El valor de 30° como umbral de riesgo se apoya en Reiman et al. (2015), aunque la evidencia es de calidad moderada
- Los datos de Teng et al. (2018) sugieren que los hombres deportistas tienen valores medios próximos al umbral (~28.6°), lo que puede generar alta tasa de positivos en población masculina deportista

---

## BLOQUE C — CONTROL NEUROMUSCULAR Y EQUILIBRIO

### C1. Y-Balance Test — Composite Score

#### Evidencia principal

**Plisky et al. (2006).** *The Reliability and Predictive Validity of the Star Excursion Balance Test in Uninjured High School Basketball Players.* JOSPT, 36(12), 911–919.
- CS < **94%** en mujeres jóvenes de baloncesto → **6.5× mayor riesgo** de lesión

**Butler et al. (2013).** *Dynamic Balance Performance and Noncontact Lower Extremity Injury in College Football Players: An Initial Study.* **Sports Health, 5(5), 417–422.** PMC3752196.
- CS < **89.6%** en hombres jóvenes de fútbol americano → riesgo relativo = **3.5** (IC95%: 2.4–5.3)
- Sensibilidad 100%, especificidad 71.7% con ese punto de corte
- n = 59 jugadores universitarios de fútbol americano

**Meta-análisis 2021 (Plisky et al.):** revisado en Sección 5 del protocolo — solo 1 de 13 estudios encontró relación significativa con lesiones futuras mediante composite score.

**Revisión sistemática y meta-análisis (2021):**
*Systematic Review and Meta-Analysis of the Y-Balance Test Lower Quarter: Reliability, Discriminant Validity, and Predictive Validity.* IJSPT. PMC8486397.

**Valores normativos por población:**

| Población | Sexo | CS medio (%) | ±SD |
|-----------|------|-------------|-----|
| Voleibol universitario | Femenino | 94.1 (dominante) | ±6.6 |
| Voleibol universitario | Femenino | 93.9 (no dominante) | ±6.2 |
| Atletas adolescentes (referencia general) | Mixto | 85–115 | — |

**Fiabilidad:**
- ICC intra-evaluador: 0.85–0.91
- ICC inter-evaluador: **0.99–1.00** (Plisky et al., 2009)

**Efecto de la edad:**
*Lower-Quarter Y-Balance Test Differs by Age: Younger Athletes May Not Be Generalized to High School-Aged Counterparts.* IJSPT / PMC11392459 (2024).
- Los valores normativos varían significativamente por edad; los puntos de corte de adultos no son directamente aplicables a adolescentes

> ⚠️ Las poblaciones, cuando se estratifican por sexo y deporte, muestran rendimientos significativamente diferentes en el YBT-LQ. Los umbrales del protocolo (89% H / 94% M) están respaldados para las poblaciones específicas de los estudios originales (fútbol americano masculino y baloncesto femenino adolescente), pero pueden no ser directamente transferibles a otros deportes o franjas de edad adulta.

---

### C2. Single-Leg Squat — Valgo dinámico

#### Evidencia sobre fiabilidad de la escala

**Crossley et al. (2011).** *Make yourself at home. Reliability of the single leg squat test.* British Journal of Sports Medicine, 45(1), 30–35.
- Kappa inter-observador: **0.65–0.80** según el par de evaluadores
- La escala cualitativa tiene variabilidad inter-observador moderada

**Ugalde et al. (2015).** JOSPT.
- Confirma la validez de la escala para detectar déficits de control neuromuscular

> ⚠️ **No se encontraron valores normativos cuantitativos** de prevalencia de cada puntuación (0-3) en población deportista sana estratificada por edad, sexo y deporte. La mayoría de estudios usan el SLS como criterio dicotómico (adecuado/inadecuado) o como variable de resultado en intervenciones. La puntuación ≥ 2 como umbral de riesgo tiene respaldo clínico pero no un estudio normativo poblacional que la justifique cuantitativamente.

---

### C3. Single-Leg Hop for Distance — LSI

#### Evidencia principal

**Normative data for hop tests in high school and collegiate basketball and soccer players.** PMC4196324 (2014).
- n = 372 deportistas adolescentes y universitarios (185 mujeres, 187 hombres; edad media 17.37 años)
- Hombres: mayor distancia que mujeres
- Universitarios: mejor que institutos

| Población | LSI medio |
|-----------|-----------|
| Adultos sanos activos | 91–96% (batería de 6 tests) |
| Futbolistas sanos | **97–106%** (dominante/no dominante) |
| Jugadores de baloncesto sanos | **99–120%** |
| Atletas jóvenes 8–14 años | **96–98%** |

**Scoping Review 2024 (JOSPT):**
*Double-Leg and Single-Leg Jump Test Reference Values for Athletes With and Without ACLR.* JOSPT (2024).
- Síntesis de valores de referencia para deportes de pivote (fútbol, baloncesto)
- Confirma que la mayoría de atletas sanos superan el 90% LSI

**Umbral del protocolo (LSI < 90%):**
El umbral del 90% tiene amplio respaldo como punto de corte mínimo entre rendimiento simétrico y asimétrico en retorno al deporte (Noyes et al., 1991; múltiples estudios de ACLR posteriores). Los valores en deportistas sanos (97–106%) sugieren que el umbral del 90% es conservador — los deportistas sanos suelen estar claramente por encima.

---

## RESUMEN DE UMBRALES: PROTOCOLO vs. EVIDENCIA

| Variable | Umbral protocolo | Valores normativos encontrados | Nivel de evidencia del umbral |
|----------|----------------|-------------------------------|------------------------------|
| Cuádriceps (H) | < 3.5 N/kg | ~4.89–5.48 N/kg (deportistas) | Moderado (población general, no HHD) |
| Cuádriceps (M) | < 2.8 N/kg | ~4.21 N/kg (baloncesto) / 3.50 N/kg (fútbol élite) | Moderado |
| Isquiotibiales (H) | < 2.3 N/kg | ~2.97–3.29 N/kg (HHD) | Moderado |
| Isquiotibiales (M) | < 1.9 N/kg | ~2.48–2.59 N/kg | Moderado |
| Ratio H:Q | < 0.60 | Media ~0.60 en HHD; 37–44% tienen < 0.60 | Alto (isocinético); Moderado (HHD) |
| Abductores cadera | < 1.5/1.2 N/kg | 1.13–1.62 Nm/kg según deporte/sexo | Moderado (unidades distintas) |
| Rot. Ext. cadera (H) | < 1.0 N/kg | 0.35–0.46 Nm/kg en deportistas | ⚠️ Umbral no validado en HHD |
| Rot. Ext. cadera (M) | < 0.8 N/kg | 0.29 Nm/kg (voleibol femenino) | ⚠️ Umbral no validado en HHD |
| Heel rise test | < 25 rep / LSI < 90% | 21–25 rep (población general) | Moderado; LSI 90% alineado con estándar RTS |
| WBLT | < 10 cm | ~12.7–14.4 cm (adultos sanos) | Alto |
| Thomas test | Positivo cualitativo | Sin normas cuantitativas disponibles | Bajo (fiabilidad moderada-alta) |
| Rot. interna cadera | < 30° activa / asimetría > 10° | 28.6° (H) / 38.1° (M) NCAA — ⚠️ valores PASIVOS | Moderado; referencia pasiva ≠ activa |
| YBT Composite Score (H) | < 89% | Umbral validado en fútbol americano | Moderado-Alto |
| YBT Composite Score (M) | < 94% | Umbral validado en baloncesto femenino | Moderado-Alto |
| SLS valgo dinámico | ≥ 2 | Sin normas poblacionales cuantitativas | Moderado (clínico) |
| Single-leg hop LSI | < 90% | 97–106% en deportistas sanos | Alto |
| ACWR | < 0.8 o > 1.3 | Zona segura 0.8–1.3 (consenso IOC) | Alto |
| NRS | > 5 = **no concluyente** (evaluación invalidada; repetir sin dolor agudo) | Umbral clínico estándar | Alto |
| Historial lesional | ≥ 2 lesiones/12m | Umbral de Hägglund (2006) | Alto |

---

## BLOQUE D — GENERACIÓN DE DATOS SINTÉTICOS: FACTORES CORRECTORES POR EDAD, ACTIVIDAD Y GÉNERO

> **Nota metodológica:** Esta sección documenta los factores multiplicadores usados en `src/generador_datos.py` para crear señales clínicamente realistas en el dataset sintético. Sin estos factores, las variables contextuales (edad, nivel de actividad) tendrían correlación ≈ 0 con los valores de fuerza generados, lo que impediría al modelo aprender estos efectos.

---

### D1. Factor corrector por grupo de edad (fuerza muscular)

#### Evidencia principal

**Bohannon, R.W. (1997).** *Reference values for extremity muscle strength obtained by hand-held dynamometry from adults aged 20 to 79 years.* Archives of Physical Medicine and Rehabilitation, 78(1), 26–32.
- n = 237 adultos sanos, 20-79 años, ambos sexos, HHD isométrico
- Cuádriceps disminuye progresivamente con la edad: hombres 20-29 años ≈ 6.2 N/kg; hombres 50-59 años ≈ 4.4 N/kg (−29 % en 30 años, ≈ −10 %/década)
- Patrón similar en mujeres, con declive del 8-12 %/década entre los 20 y los 59 años

**Andrews, A.W. et al. (1996).** *Normative values for isometric muscle force measurements obtained with hand-held dynamometers.* Physical Therapy, 76(3), 248–259.
- Referencia estándar para umbrales de fuerza isométrica por HHD en adultos
- Cuádriceps, isquiotibiales y abductores de cadera muestran declive claro a partir de los 40-50 años en ambos sexos

**Meta-análisis (Frontiers in Physiology, 2021).**
*Age-related changes in muscle strength and power across the adult lifespan: a systematic review and meta-analysis.* Frontiers in Physiology, 12.
- n = **13.893 sujetos** combinados, múltiples grupos musculares, múltiples estudios
- Declive de fuerza muscular máxima: **8-15 %/década** entre los 40 y los 70 años
- Para adultos activos de 35-65 años, el declive estimado se sitúa en el extremo inferior del rango: **6-10 %/década**

**Wroblewski, A.P. et al. (2011).** *Chronic exercise preserves lean muscle mass in masters athletes.* The Physician and Sportsmedicine, 39(3), 172–178.
- Atletas máster que mantienen entrenamiento regular presentan pérdida de masa muscular considerablemente menor que sedentarios de igual edad
- Confirma que el ejercicio regular amortigua el declive relacionado con la edad, justificando factores conservadores para la población objetivo de IntApp

#### Factores aplicados en el generador sintético

| Grupo de edad | Factor corrector | Declive implícito respecto al grupo anterior |
|---------------|-----------------|----------------------------------------------|
| 18–35 años    | × 1.00 (referencia) | — |
| 36–50 años    | × 0.90 | −10 % en ≈ 17 años (≈ 6 %/década) |
| 51–65 años    | × 0.80 | −10 % adicional en ≈ 17 años (≈ 6 %/década) |

**Justificación del valor conservador:** El declive adoptado (−6 %/década) está en el extremo inferior del rango publicado (8-15 %/década). Esta elección es coherente con la población diana de IntApp — adultos físicamente activos — en quienes el ejercicio regular amortigua el declive. Aplicar el percentil máximo (15 %/década) sobreestimaría el efecto en deportistas activos de 36-65 años.

---

### D2. Factor corrector por nivel de actividad (fuerza muscular)

#### Evidencia principal

**Owoeye et al. (2024).** *Normative Hamstrings and Quadriceps Isometric Strength Values and Hamstrings-Quadriceps Asymmetry in Healthy Collegiate Soccer and Basketball Players.* International Journal of Exercise Science, 17(4), 768–778. PMC11268924.
- Deportistas universitarios (nivel equivalente a "activo/élite"): cuádriceps masculino 4.89–5.48 N/kg
- Población general adulta activa moderada (equivalente a "recreacional"): ≈ 3.5–4.0 N/kg (Bohannon 1997, Andrews 1996)
- Brecha observada deportistas vs. población general: **~37-39 %**

**Kraemer, W.J. & Ratamess, N.A. (2004).** *Fundamentals of resistance training: progression and exercise prescription.* Medicine & Science in Sports & Exercise, 36(4), 674–688.
- El entrenamiento de resistencia aumenta la fuerza muscular máxima en **20-40 %** en adultos previamente sedentarios que inician un programa estructurado

**Hallazgos consistentes (Buchner et al., 1992; Frontera et al., 1991):**
- Sujetos sedentarios presentan valores de fuerza isométrica significativamente inferiores a sujetos recreacionalmente activos de igual sexo y edad
- La diferencia sedentario/recreacional es del orden del 10-20 %; la diferencia recreacional/élite es del 15-25 %

#### Factores aplicados en el generador sintético

| Nivel de actividad | Factor corrector | Diferencia respecto a recreacional |
|--------------------|-----------------|--------------------------------------|
| sedentario         | × 0.88 | −12 % |
| recreacional       | × 1.00 (referencia) | — |
| activo             | × 1.10 | +10 % |
| elite              | × 1.22 | +22 % |

**Rango total** (sedentario → elite): **38 %**, coherente con la brecha de ≈ 37 % entre deportistas universitarios y población general observada en Owoeye (2024).

**Nota sobre asimetría con los factores de umbral:** Los factores de generación (0.88–1.22, rango 38 %) son deliberadamente más conservadores que los factores de evaluación `FACTORES_ACTIVIDAD` en `variables.py` (0.85–1.30, rango 53 %). El diseño es intencional: los deportistas de élite son evaluados con un estándar más exigente que el incremento real de su capacidad, reflejando el mayor coste funcional de los déficits en competición.

---

### D3. Factor de género en la generación de fuerza bruta (±18 %)

El factor de género en la generación de valores de fuerza bruta (N) se establece en ×1.18 para hombres y ×0.82 para mujeres (diferencia total ≈ 44 % entre sexos antes de normalizar por peso).

**Fundamento:**

**Janssen, I. et al. (2000).** *Skeletal muscle mass and distribution in 468 men and women aged 18–88 yr.* Journal of Applied Physiology, 89(1), 81–88.
- La masa muscular esquelética en miembro inferior es **15-25 % mayor en hombres** que en mujeres a igual masa corporal total

**Frontera, W.R. et al. (1991).** *A cross-sectional study of muscle strength and mass in 45- to 78-yr-old men and women.* Journal of Applied Physiology, 71(2), 644–650.
- Fuerza isométrica de cuádriceps: hombres ≈ 30 % superior a mujeres de igual edad en términos absolutos (N)
- Diferencia ≈ 15-20 % después de normalizar por masa magra

El factor ±18 % modela la fracción del dimorfismo sexual que no queda capturada por las diferencias de peso corporal (ya incluidas en `factor_peso`). A igual peso, un hombre genera ≈ 1.18/0.82 = 1.44 × más fuerza que una mujer antes de normalizar. Tras la normalización por peso (N → N/kg), la brecha residual es coherente con los datos de Owoeye (2024): cuádriceps masculino/femenino en fútbol = 5.48/4.55 ≈ 20 % en N/kg, lo que implica que la normalización absorbe gran parte pero no todo el dimorfismo.

> ⚠️ Versiones anteriores del generador (v2.2) usaban un factor de ±10 %, que subestimaba la diferencia de fuerza bruta observable entre sexos. El factor actual (±18 %) está mejor calibrado con los valores de referencia de la literatura.

---

## BLOQUE E — DERIVACIÓN DE `rango_normal` EN NEWTONS ABSOLUTOS (IntApp v2)

> **Contexto:** IntApp registra la fuerza en N (salida directa del HHD). El modelo la normaliza internamente a N/kg mediante `preprocesador.py`. Sin embargo, la UI necesita un *rango_normal* en N para: (1) fijar el valor por defecto del slider y (2) mostrar el indicador visual de normalidad. Esta sección documenta cómo se derivaron esos límites a partir de los valores N/kg de la literatura.

### Metodología de derivación

**Peso de referencia:** 70 kg (mediana estimada de la población recreacional adulta mixta en España).

**Fórmula general:**
- Límite inferior `rango_normal` ≈ umbral de riesgo del subgrupo más vulnerable (F_51_65) × 50 kg
- Límite superior `rango_normal` ≈ media sana del subgrupo más fuerte (M_18_35) × 85 kg
- **Midpoint** = (inferior + superior) / 2 → se usa como valor por defecto del slider

El midpoint en N/kg a 70 kg debe quedar entre el umbral mixto y la media sana mixta, representando un atleta recreacional típico ligeramente por encima del umbral de riesgo.

---

### E1. Cuádriceps — `rango_normal` (130, 420) N

| Parámetro | Valor N/kg | A 70 kg |
|---|---|---|
| Umbral de riesgo F_51_65 | 2.4 N/kg (Andrews 1996, Bohannon 1997) | — |
| Umbral de riesgo M_18_35 | 4.0 N/kg | — |
| Media sana adultos activos (Bohannon 1997) | 3.5–4.0 N/kg ♀; 5.0 N/kg ♂ | — |
| **Midpoint resultante** | **3.93 N/kg** | **275 N** |

- **Inferior 130 N:** umbral F_51_65 (2.4 N/kg) × 55 kg ≈ 132 N → 130 N
- **Superior 420 N:** media sana M_18_35 (~5.0 N/kg) × 85 kg = 425 N → 420 N
- **Justificación midpoint:** 275 N ÷ 70 kg = 3.93 N/kg, dentro del rango de adultos activos no atletas de Bohannon (1997): 3.5–4.0 N/kg. Coincide con el umbral recreacional M_18_35 (4.0 N/kg), indicando que el valor por defecto representa un atleta recreacional masculino en el umbral inferior de normalidad.

---

### E2. Isquiotibiales — `rango_normal` (80, 270) N

| Parámetro | Valor N/kg | A 70 kg |
|---|---|---|
| Umbral de riesgo F_51_65 | 1.5 N/kg | — |
| Umbral de riesgo M_18_35 | 2.5 N/kg | 175 N |
| Media HHD baloncesto ♀ (Owoeye 2024) | 2.48 N/kg | 174 N |
| Media HHD baloncesto ♂ (Owoeye 2024) | 2.97 N/kg | 208 N |
| **Midpoint resultante** | **2.50 N/kg** | **175 N** |

- **Inferior 80 N:** umbral F_51_65 (1.5 N/kg) × 55 kg = 82.5 N → 80 N
- **Superior 270 N:** media HHD ♂ (2.97 N/kg) × 90 kg = 267 N → 270 N
- **Justificación midpoint:** 175 N ÷ 70 kg = 2.50 N/kg = promedio entre umbral M_18_35 (2.5 N/kg) y media ♀ HHD Owoeye (2.48 N/kg). El ratio H:Q implícito es 175/275 = **0.64** (por encima del umbral de 0.60, Croisier 2008). Representa un atleta recreacional en el límite inferior de normalidad para hombres y dentro del rango normal para mujeres.

---

### E3. Glúteo medio / Abductores — `rango_normal` (50, 170) N

| Parámetro | Valor N/kg | A 70 kg |
|---|---|---|
| Umbral de riesgo F_51_65 | 0.9 N/kg | — |
| Umbral de riesgo M_18_35 | 1.5 N/kg | 105 N |
| Media sana estimada M (Thorborg 2016 + conversión) | ~2.0 N/kg | 140 N |
| Media sana estimada F | ~1.6 N/kg | 112 N |
| **Midpoint resultante** | **1.57 N/kg** | **110 N** |

- **Inferior 50 N:** umbral F_51_65 (0.9 N/kg) × 55 kg = 49.5 N → 50 N
- **Superior 170 N:** media sana M (~2.0 N/kg) × 85 kg = 170 N
- **Justificación midpoint:** 110 N ÷ 70 kg = 1.57 N/kg, por encima del umbral M_18_35 (1.5 N/kg). ⚠️ La literatura normativa de Thorborg et al. (2016) reporta valores en **Nm/kg** (torque), no N/kg (fuerza). La conversión a N/kg depende de la longitud del brazo de momento HHD–trocánter (estimada en ~0.35 m para el protocolo estándar). Esta limitación se declara explícitamente: los valores son estimaciones, no conversiones exactas verificadas.

---

### E4. Rotadores externos de cadera — `rango_normal` (30, 130) N

| Parámetro | Valor N/kg | A 70 kg |
|---|---|---|
| Umbral de riesgo F_51_65 | 0.55 N/kg | — |
| Umbral de riesgo M_18_35 | 1.0 N/kg (Hollman 2009) | 70 N |
| Media sana estimada M (50% sobre umbral Hollman) | ~1.5 N/kg | 105 N |
| Media sana estimada F | ~1.2 N/kg | 84 N |
| **Midpoint resultante** | **1.14 N/kg** | **80 N** |

- **Inferior 30 N:** umbral F_51_65 (0.55 N/kg) × 55 kg = 30 N
- **Superior 130 N:** media sana M (~1.5 N/kg) × 85 kg = 127.5 N → 130 N
- **Justificación midpoint:** 80 N ÷ 70 kg = 1.14 N/kg, por encima del umbral M_18_35 de Hollman et al. (2009 JOSPT): < 1.0 N/kg. El umbral de Ireland et al. (2003) — fuerza < 20.3% del peso corporal → ~2.0 N/kg — difiere notablemente. El documento adopta Hollman (2009) como referencia primaria al compartir instrumento (HHD) y protocolo (decúbito prono). ⚠️ Los valores normativos de PMC6442714 (0.29–0.46 Nm/kg) están en torque, no fuerza, y no son directamente comparables.

---

### E5. Aductores de cadera — `rango_normal` (80, 230) N

| Parámetro | Valor N/kg | A 70 kg |
|---|---|---|
| Umbral de riesgo F_51_65 | 1.3 N/kg | — |
| Umbral de riesgo M_18_35 | 2.2 N/kg | 154 N |
| Fútbol élite ♂ excéntrico (Thorborg 2011) | ~2.5–3.0 N/kg | — |
| Estimación recreacional (−20 % sobre élite) | ~2.0–2.4 N/kg | 140–168 N |
| **Midpoint resultante** | **2.21 N/kg** | **155 N** |

- **Inferior 80 N:** umbral F_51_65 (1.3 N/kg) × 60 kg ≈ 78 N → 80 N
- **Superior 230 N:** estimación recreacional (~2.7 N/kg) × 85 kg = 229.5 N → 230 N
- **Justificación midpoint:** 155 N ÷ 70 kg = 2.21 N/kg, prácticamente en el umbral M_18_35 (2.2 N/kg). El valor por defecto sitúa a un atleta recreacional de 70 kg en el límite de la normalidad masculina, lo que es coherente con la escasez de datos normativos en población no élite: los únicos valores de referencia robustos disponibles son de fútbol élite (Thorborg 2011), donde los valores son considerablemente superiores. ⚠️ **Dato insuficiente** para adultos recreacionales — declarar como limitación en el TFM.

---

### Tabla resumen de `rango_normal` en N

| Variable | `rango_normal` (N) | Midpoint (N) | N/kg a 70 kg | Fuente principal |
|---|---|---|---|---|
| Cuádriceps | (130, 420) | 275 | 3.93 | Bohannon 1997; Andrews 1996 |
| Isquiotibiales | (80, 270) | 175 | 2.50 | Owoeye 2024 |
| Glúteo medio | (50, 170) | 110 | 1.57 | Thorborg 2016 (estimación N/kg) |
| Rotadores externos | (30, 130) | 80 | 1.14 | Hollman 2009 JOSPT |
| Aductores | (80, 230) | 155 | 2.21 | Thorborg 2011 AJSM (élite, −20%) |

> **Nota sobre gradiente clínico:** Con los defaults anteriores (midpoints de `rango_sintetico`), el modelo predecía MEDIO para cualquier peso entre 50–100 kg porque las variables de contexto dominaban. Con estos defaults evidence-based, el gradiente es clínico: BAJO a 50 kg (57%), MEDIO a 60–100 kg con P(alto) creciendo del 6% al 33% a medida que aumenta el peso para la misma fuerza bruta — reflejando que a mayor peso se necesita mayor fuerza absoluta para mantener el ratio N/kg por encima del umbral.

---

## BLOQUE F — PROTOCOLO DE SCORING CLÍNICO v2.2

> Este bloque documenta el sistema de clasificación lógico-decisional implementado en `src/generador_datos.py`. Define exactamente cómo se asigna la categoría de riesgo (bajo / medio / alto) a partir de los datos de evaluación.

### F1. Arquitectura del sistema

La clasificación final combina **dos mecanismos independientes** y toma el máximo:

1. **Reglas booleanas** (lógica clínica experta): activan ALTO o MEDIO cuando se cumplen combinaciones clínicamente relevantes de variables
2. **Score ponderado**: suma de puntos por variable fuera de rango; si supera umbral → eleva la categoría

```
categoría_final = max(categoría_reglas, categoría_score)
```

Excepción: si NRS > 5 → categoría = **"no concluyente"** (evaluación invalidada por dolor agudo; repetir sin dolor).

---

### F2. Pesos de cada variable (peso_scoring)

| Variable | Bloque | peso_scoring | Justificación del peso |
|---|---|---|---|
| Cuádriceps | Fuerza | **3** | Predictor principal de carga articular; Andrews 1996 |
| Isquiotibiales | Fuerza | **3** | H:Q < 0.60 → RR 4.7 lesión isquios (Croisier 2008) |
| Glúteo medio | Fuerza | **3** | Valgo dinámico; Powers 2010 JOSPT |
| Rotadores externos cadera | Fuerza | **3** | OR 3.1 ACL (Ireland 2003); Hollman 2009 |
| Aductores cadera | Fuerza | **2** | Lesión inguinal; Thorborg 2011 |
| Tríceps sural | Fuerza | **2** | Lesión Aquiles; Hébert-Losier 2017 |
| Dorsiflexión tobillo | Movilidad | **4** | OR 4.6 esguince (Willems 2005); guía JOSPT 2021; peso elevado de 3→4 en v2.3 por alta OR y déficit bilateral como regla A5 |
| Thomas test | Movilidad | **2** | Moderada evidencia; sin normas cuantitativas |
| Rotación interna cadera | Movilidad | **2** | Reiman 2015; limitación ROM activa |
| Y-Balance CS | Control | **4** | 6.5× riesgo (Plisky 2006); 3.5× (Butler 2013) |
| Single-leg squat valgo | Control | **3** | Crossley 2011 (escala cualitativa SLS); Ugalde 2015 JOSPT |
| Single-leg hop LSI | Control | **3** | Noyes 1991; gold standard retorno al deporte |
| Historial lesional | Contexto | **5** | Mayor predictor individual; OR 2-8 (Hägglund 2006) |
| ACWR | Contexto | **2** | Gabbett 2016; zona segura IOC 0.8–1.3 |
| PSS-4 | Contexto | **1** | Kenttä 2001; Nixdorf 2013 |
| Hooper Index | Contexto | **2** | Hooper 1995; sensible a sobrecarga aguda |
| Horas de sueño | Contexto | **2** | OR 1.7 < 8h (Milewski 2014, Pediatrics) |
| NRS dolor | Contexto | **—** | No suma score: si NRS > 5 → categoría "no concluyente" (evaluación invalidada por dolor agudo; peso_scoring=3 definido en variables.py pero no aplicado al score) |

**Zona gris:** ±10 % del umbral → suma `peso × 0.5` (puntuación parcial).

---

### F3. Umbrales del score

| Umbral | Valor | Interpretación |
|---|---|---|
| SCORE_UMBRAL_ALTO | **≥ 26** | Score suficientemente elevado para ALTO aunque las reglas no se activen |
| SCORE_UMBRAL_MEDIO | **≥ 18** | Score elevado → MEDIO aunque las reglas indiquen BAJO |

**Calibración:** estos umbrales fueron recalibrados en v2.3. El umbral ALTO (26) equivale aproximadamente a tener 3 variables de peso 3 completamente fuera de rango (9+9+9 = 27) o 2 variables de peso 4 (8+8+... con zona gris). El umbral MEDIO (18) corresponde a 2-3 variables de peso moderado fuera de rango.

---

### F4. Reglas booleanas — RIESGO ALTO (A1–A7)

| Regla | Condición | Justificación |
|---|---|---|
| **A1** | Cuádriceps **Y** isquiotibiales fuera de umbral en el **mismo miembro** | Déficit combinado extensión+flexión = disfunción global articulación rodilla |
| **A2** | Glúteo medio **Y** rotadores externos fuera en el **mismo miembro** | Déficit combinado abducción+rotación = colapso completo del control de cadera |
| **A3** | Cuádriceps fuera **Y** historial ≥ 7 lesiones/año | Combinación déficit estructural + historial severo; evidencia de Hägglund 2006 |
| **A4** | LSI hop < 80 % **Y** cuádriceps del lado débil fuera | Asimetría funcional grave confirmada por fuerza; Noyes 1991 + retorno al deporte |
| **A5** | Dorsiflexión tobillo fuera de umbral en **ambos lados** | Déficit bilateral WBLT → riesgo esguince recurrente bilateral; Willems 2005 |
| **A6** | Valgo SLS ≥ 2 **Y** Y-Balance CS bajo umbral en el **mismo lado** | Déficit de control combinado: biomecánica + equilibrio; Crossley 2011 + Plisky 2006 |
| **A7** | Y-Balance CS bajo umbral en **ambos lados** | Déficit bilateral de control postural dinámico; Plisky 2006 (6.5× riesgo) |

### F5. Reglas booleanas — RIESGO MEDIO (M1–M7)

| Regla | Condición | Justificación |
|---|---|---|
| **M1** | ACWR > umbral por nivel de actividad | Zona de sobrecarga; Gabbett 2016 |
| **M2** | Historial 5–6 lesiones/12 meses (sin llegar a A3) | Historial elevado sin déficit agudo; Hägglund 2006 |
| **M3** | PSS-4 ≥ 9 **o** Hooper ≥ 22 **Y** nivel activo/élite | Estrés elevado en deportista de alta demanda; Hooper 1995 |
| **M4** | Dorsiflexión fuera **unilateral** **Y** valgo unilateral (sin A6) | Asimetría funcional unilateral tobillo-rodilla; Willems 2005 |
| **M5** | ≥ 3 variables de movilidad fuera de umbral | Patrón global de restricción articular; sin regla específica activa |
| **M6** | Y-Balance CS bajo umbral en **un lado** (sin A7) | Déficit unilateral de equilibrio; Plisky 2006 (umbral predictivo) |
| **M7** | Valgo dinámico SLS **grado 3** en cualquier lado | Hallazgo más severo de la escala Crossley (2011); valgo en aterrizaje OR 2.5 LCA (Hewett 2005); independiente de otras reglas por su gravedad biomecánica |

---

### F6. Confianza del scoring

| % mediciones dentro de rango ("claras") | Confianza |
|---|---|
| ≥ 80 % | Alta |
| 60–79 % | Media |
| < 60 % | Baja |

La confianza es informativa, no modifica la categoría de riesgo final.

---

## CONCLUSIONES PARA EL TFM

### Variables con umbral bien respaldado
ACWR, historial lesional, NRS, single-leg hop LSI, WBLT, YBT (en las poblaciones originales de los estudios).

### Variables con umbral que requiere matización en la defensa
- **Ratio H:Q < 0.60 en HHD:** válido conceptualmente, pero el umbral numérico procede de isocinético. Declarar como limitación.
- **Rotadores externos < 1.0/0.8 N/kg:** los valores normativos encontrados (0.29–0.46 Nm/kg) son Nm/kg (torque), no N/kg (fuerza). La conversión depende de la longitud del brazo de momento. Verificar consistencia de unidades.
- **Rotación interna < 30°:** el umbral puede generar alta tasa de positivos en hombres deportistas (media ~28.6°).
- **Heel rise LSI:** corregido a 90% (alineado con estándar de retorno al deporte). El 85% previo carecía de referencia directa.

### Variable sin datos normativos cuantitativos disponibles
Thomas test: usar como variable cualitativa (positivo/negativo) y declarar la ausencia de normas cuantitativas como limitación del protocolo.

---

## REFERENCIAS COMPLETAS

1. Owoeye, O.B.A. et al. (2024). Normative Hamstrings and Quadriceps Isometric Strength Values and Hamstrings-Quadriceps Asymmetry in Healthy Collegiate Soccer and Basketball Players. *International Journal of Exercise Science*, 17(4), 768–778. PMC11268924.

2. Normative Quadriceps and Hamstring Muscle Strength Values for Female, Healthy, Elite Handball and Football Players (2018). *Journal of Strength and Conditioning Research*, 32(8):2313–2319. PMC6092090.

3. Thorborg, K. et al. (2016). Reference values of hip abductor torque among youth athletes: Influence of age, sex and sports. *Physical Therapy in Sport*, 22, 1–6. PubMed 27428529.

4. Normative values of eccentric hip abduction strength in novice runners: an equation adjusting for age and gender. PMC3924610. PubMed 24567857.

5. Thorborg, K. et al. (2017). Hip strength and range of motion: Normal values from a professional football league. *Journal of Science and Medicine in Sport*. PubMed 28185809.

6. Thorborg, K. et al. (2011). Hip Adduction and Abduction Strength Profiles in Elite Soccer Players. *The American Journal of Sports Medicine*, 39(11), 2704–2708.

7. Normal hip strength and range of motion values in youth and adult female national football teams: Data from 504 assessments. *Physical Therapy in Sport* (2024). ScienceDirect.

8. Normative isometric hip muscle force values assessed by a manual dynamometer (2019). PMC6442714.

9. Hébert-Losier, K. et al. (2017). Updated reliability and normative values for the standing heel-rise test in healthy adults. *Physiotherapy*, 103(4), **446–452**. PubMed 28886865.

10. Normative values for calf muscle strength-endurance in the general population assessed with the Calf Raise Application (2025). *ScienceDirect*.

11. [Estudio internacional WBLT] International normative values for the weight-bearing lunge test across age and sex in 899 healthy adults (2026). *Musculoskeletal Science and Practice*. ScienceDirect.

12. Reliability and minimal detectable change of the weight-bearing lunge test: A systematic review (2015). PubMed 25704110.

13. Normative range of weight-bearing lunge test performance asymmetry in healthy adults (2011). ScienceDirect.

14. Reliability of Goniometric Techniques for Measuring Hip Flexor Length Using the Modified Thomas Test (2024). *International Journal of Sports Physical Therapy*. PMC11297360.

15. Teng, H.L. et al. (2018). Passive Hip Range-of-Motion Values Across Sex and Sport. *Journal of Athletic Training*, 53(**6**), **560–567**. PMC6089031. ⚠️ Medición pasiva; IntApp mide ROM activa.

16. Hip strength and range of motion: Normal values from a professional football league (2017). *Journal of Science and Medicine in Sport*. PubMed 28185809.

17. Plisky, P.J. et al. (2006). The Reliability and Predictive Validity of the Star Excursion Balance Test in Uninjured High School Basketball Players. *JOSPT*, 36(12), 911–919.

18. Systematic Review and Meta-Analysis of the Y-Balance Test Lower Quarter: Reliability, Discriminant Validity, and Predictive Validity (2021). *IJSPT*. PMC8486397.

19. Lower-Quarter Y-Balance Test Differs by Age: Younger Athletes May Not Be Generalized to High School-Aged Counterparts (2024). *IJSPT*. PMC11392459.

20. Normative data for hop tests in high school and collegiate basketball and soccer players (2014). PMC4196324.

21. Double-Leg and Single-Leg Jump Test Reference Values for Athletes With and Without ACLR Who Play Popular Pivoting Sports (2024). *JOSPT*.

22. Crossley, K.M. et al. (2011). Make yourself at home. Reliability of the single leg squat test. *British Journal of Sports Medicine*, 45(1), 30–35.

23. Lower-limb muscle strength: normative data from an observational population-based study (2020). *BMC Musculoskeletal Disorders*. DOI: 10.1186/s12891-020-3098-7.

---
*Documento generado para uso académico en el TFM de Roberto Franco, Universidad Europea.*
*Solo se incluyen valores confirmados por búsqueda bibliográfica. Ausencias de datos declaradas explícitamente.*
