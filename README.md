# IntApp — Evaluación del Riesgo de Lesión Deportiva

Sistema de evaluación clínica basado en machine learning para la predicción del riesgo
de lesión de miembro inferior en deportistas. Desarrollado como TFM de Fisioterapia.

A partir de 19 variables clínicas originales (fuerza muscular, movilidad articular, control
neuromuscular y contexto del deportista), expandidas a 31 columnas mediante medición bilateral,
el sistema clasifica el riesgo en tres niveles (bajo / medio / alto) y explica qué variables
han influido más en la predicción mediante importancia de variables del modelo (feature importance).

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

## Estructura del proyecto

```
IntApp v2/
│
├── app/
│   └── streamlit_app.py                Interfaz clínica web (Streamlit)
│
├── notebooks/                          # Pipeline paso a paso
│   ├── 01_generacion_datos.ipynb       Generación del dataset sintético (n=500, semilla=42)
│   ├── 02_exploracion_datos.ipynb      Análisis exploratorio y distribuciones
│   ├── 03_entrenamiento_modelo.ipynb   Entrenamiento y comparación de modelos (RF, RL, GB)
│   ├── 04_interpretacion_modelo.ipynb  Importancia de variables (SHAP)
│   ├── 05_analisis_sensibilidad.ipynb  Análisis de sensibilidad clínica
│   └── 06_validacion_sinteticos.ipynb  Validación final
│
├── src/                                # Módulos Python del proyecto
│   ├── variables.py                    19 variables clínicas, umbrales y protocolo v2.3
│   ├── generador_datos.py              Generación de datos sintéticos
│   ├── preprocesador.py                Pipeline de preprocesamiento y normalización
│   ├── modelo.py                       Entrenamiento (RF, RL, GB) y serialización
│   └── evaluador_riesgo.py             Evaluación individual + importancia de variables
│
├── docs/                               # Documentación clínica
│   ├── Protocolo_Scoring_Roberto_Franco.docx   Protocolo de scoring v2.3
│   └── Evidencia_Valores_Normativos.md         Evidencia bibliográfica de umbrales
│
├── datos/
│   ├── sinteticos/                     Dataset sintético de exploración (n=500)
│   └── procesados/                     Datasets preprocesados para entrenamiento
│
├── figuras/                            # Gráficos generados por los notebooks
│
├── modelos/                            # Modelos entrenados
│   ├── mejor_modelo.pkl                Modelo clínico desplegado (GB calibrado)
│   ├── scaler.pkl                      StandardScaler ajustado
│   ├── modelo_rf.joblib                Random Forest (comparación, nb04)
│   ├── modelo_rl.joblib                Regresión Logística (comparación, nb04)
│   └── modelo_gb.joblib                Gradient Boosting base (comparación, nb04)
│
├── scripts/
│   └── generar_shap.py                 Script standalone para análisis SHAP
│
├── tests/                              # Tests unitarios
│   ├── test_evaluador_riesgo.py
│   └── test_preprocesador.py
│
└── requirements.txt                    # Dependencias Python
```

---

## Autor

- **Nombre**: Roberto Franco Yagüe
- **Titulación**: MFP en IA Aplicada al Deporte — TFM
- **Institución**: Universidad Europea
- **Curso**: 2025-2026
