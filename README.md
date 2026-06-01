# IntApp v2.3 — Evaluación del Riesgo de Lesión Deportiva

Sistema de evaluación clínica basado en machine learning para la predicción del riesgo
de lesión de miembro inferior en deportistas. Desarrollado como TFM del Máster en IA
Aplicada al Deporte, Universidad Europea. Autor: Roberto Franco Yagüe.

A partir de 19 variables clínicas originales (fuerza muscular, movilidad articular,
control neuromuscular y contexto del deportista), el sistema genera 56 features mediante:
expansión bilateral, normalización por peso (N/kg), ratios clínicos (H:Q, ADD/ABD),
asimetrías bilaterales y —novedad de v2.3— 12 features de ratio normativo que expresan
el valor del deportista como fracción del umbral ajustado a su perfil (edad × género × nivel de actividad).

El modelo clasifica el riesgo en tres niveles (bajo / medio / alto) y explica los factores
determinantes para cada evaluación individual mediante SHAP.

---

## Métricas del modelo (conjunto de test, n = 1 000)

| Métrica | Valor |
|---|---|
| Accuracy | 0.860 |
| F1 macro | 0.844 |
| Recall clase 'alto' | **0.964** [IC95%: 0.944–0.981] |
| Recall clase 'medio' | 0.670 |
| Precision clase 'alto' | 0.852 |
| CV 5-fold F1 | 0.876 ± 0.015 |

Modelo: Gradient Boosting con umbral calibrado `p = 0.12` para la clase 'alto'
(prioridad clínica: minimizar falsos negativos). Dataset sintético: 4 826 deportistas
generados con reglas clínicas basadas en la literatura (ver `docs/Evidencia_Valores_Normativos.md`).

---

## Inicio rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar los notebooks en orden (01 → 06) desde JupyterLab
jupyter lab

# 3. Lanzar la aplicación
streamlit run app/streamlit_app.py
```

---

## Pipeline de preprocesamiento (v2.3)

| Paso | Función | Salida |
|---|---|---|
| 1 | `calcular_ratios` | N → N/kg; ratio H:Q y ADD/ABD |
| 2 | `calcular_ratios_normativos` | `<var>_ratio_ref = nkg / umbral(género, edad, actividad)` |
| 3 | `calcular_asimetrias` | `asimetria_<var>` = `\|der − izq\| / max × 100` |
| 4 | `codificar_categoricas` | genero binario; nivel_actividad ordinal 0–3 |
| 5 | `eliminar_columnas_aux` | elimina score_total, confianza_*, reglas_activadas |
| 6 | `normalizar` | StandardScaler sobre 47 columnas continuas |

**Columnas resultantes:** 57 (56 features + riesgo_lesion). El ratio normativo
es la principal innovación: `ratio = 1.0` significa exactamente en el umbral
de referencia para ese perfil; `< 1.0` es déficit; `> 1.0` está por encima.

---

## Estructura del proyecto

```
IntApp v2/
│
├── app/
│   └── streamlit_app.py                Interfaz clínica web (Streamlit)
│
├── notebooks/                          Pipeline paso a paso
│   ├── 01_generacion_datos.ipynb       Generación del dataset sintético (n=4 861, semilla=42)
│   ├── 02_exploracion_datos.ipynb      Análisis exploratorio y distribuciones
│   ├── 03_entrenamiento_modelo.ipynb   Entrenamiento y comparación de modelos (RF, RL, GB)
│   ├── 04_interpretacion_modelo.ipynb  Importancia de variables (SHAP)
│   ├── 05_analisis_sensibilidad.ipynb  Análisis de sensibilidad clínica
│   └── 06_validacion_sinteticos.ipynb  Validación final
│
├── src/                                Módulos Python del proyecto
│   ├── variables.py                    19 variables clínicas, umbrales y protocolo v2.3
│   ├── generador_datos.py              Generación de datos sintéticos con reglas clínicas
│   ├── preprocesador.py                Pipeline de preprocesamiento v2.3 (6 pasos)
│   ├── modelo.py                       Entrenamiento (RF, RL, GB) y serialización
│   └── evaluador_riesgo.py             Evaluación individual + SHAP + importancias
│
├── docs/                               Documentación clínica
│   ├── Protocolo_Scoring_Roberto_Franco.docx   Protocolo de scoring clínico v2.3
│   ├── Evidencia_Valores_Normativos.md         Evidencia bibliográfica de umbrales
│   └── Manual_IntApp_v2.pdf                    Manual de uso para no técnicos
│
├── datos/
│   ├── sinteticos/                     Dataset sintético (n=4 861)
│   └── procesados/                     Dataset preprocesado para entrenamiento
│
├── figuras/                            Gráficos generados por los notebooks
│
├── modelos/                            Modelos entrenados
│   ├── mejor_modelo.pkl                Modelo clínico desplegado (GB calibrado, umbral=0.12)
│   ├── scaler.pkl                      StandardScaler ajustado (47 columnas)
│   ├── modelo_rf.joblib                Random Forest (comparación)
│   ├── modelo_rl.joblib                Regresión Logística (comparación)
│   └── modelo_gb.joblib                Gradient Boosting base (comparación)
│
├── tests/                              Tests unitarios (31 tests, todos pasan)
│   ├── test_evaluador_riesgo.py
│   └── test_preprocesador.py
│
└── requirements.txt                    Dependencias Python
```

---

## Regla clínica de seguridad

**NRS > 5 (dolor agudo activo):** el sistema bloquea el cálculo del modelo y
muestra un aviso de evaluación no concluyente. Se requiere valoración presencial
antes de continuar con el programa de prevención.

---

## Autor

- **Nombre**: Roberto Franco Yagüe
- **Titulación**: Máster en IA Aplicada al Deporte — TFM
- **Institución**: Universidad Europea
- **Curso**: 2025-2026
