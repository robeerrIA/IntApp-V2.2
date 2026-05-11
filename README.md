# IntApp — Evaluación del Riesgo de Lesión Deportiva

Sistema de evaluación clínica basado en machine learning para la predicción del riesgo
de lesión de miembro inferior en deportistas. Desarrollado como TFM de Fisioterapia.

A partir de 23 variables clínicas (fuerza muscular, movilidad articular, control
neuromuscular y contexto del deportista), el sistema clasifica el riesgo en tres
niveles (bajo / medio / alto) y explica qué variables han influido más en la
predicción mediante análisis SHAP.

---

## Inicio rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar los notebooks en orden (01 → 06) desde JupyterLab
jupyter lab

# 3. Lanzar la aplicación
streamlit run app.py
```

Para instrucciones detalladas dirigidas al autor clínico del proyecto, consulta
`INSTRUCCIONES_ROBERTO.md`.

---

## Estructura del proyecto

```
IntApp/
│
├── notebooks/                    # Pipeline paso a paso
│   ├── 01_generacion_datos.ipynb       Generación de datos sintéticos
│   ├── 02_exploracion_datos.ipynb      Análisis exploratorio
│   ├── 03_entrenamiento_modelo.ipynb   Entrenamiento y comparación de modelos
│   ├── 04_interpretacion_modelo.ipynb  Importancia de variables (SHAP)
│   ├── 05_analisis_sensibilidad.ipynb  Análisis de sensibilidad
│   └── 06_validacion_sinteticos.ipynb  Validación final
│
├── src/                          # Módulos Python del proyecto
│   ├── variables.py                    Definición de las 23 variables clínicas
│   ├── generador_datos.py              Generación de datos sintéticos
│   ├── preprocesador.py                Pipeline de preprocesamiento
│   ├── modelo.py                       Entrenamiento (RF, RL, GB)
│   └── evaluador_riesgo.py             Evaluación individual + SHAP
│
├── docs/                         # Documentación clínica
│   └── protocolo_scoring.md            Protocolo de scoring (completar antes del código)
│
├── datos/
│   └── sinteticos/                     Dataset sintético generado
│
├── figuras/                      # Gráficos generados automáticamente
│
├── modelos/                      # Modelos entrenados (generados al ejecutar nb 03)
│
├── requirements.txt              # Dependencias Python
├── INSTRUCCIONES_ROBERTO.md      # Guía completa para el autor clínico
└── README.md                     # Este archivo
```

---

## Autor

- **Nombre**: [TODO — nombre completo]
- **Titulación**: Grado en Fisioterapia — TFM
- **Institución**: Universidad Europea
- **Tutor/a**: [TODO — nombre del tutor]
- **Curso**: 2025-2026
