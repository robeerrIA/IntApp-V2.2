"""
evaluador_riesgo.py — Evaluación individual de riesgo de lesión deportiva.

Este módulo encapsula el flujo completo de inferencia para un único deportista:

    1. Cargar el modelo entrenado y el scaler desde disco.
    2. Construir el DataFrame de una fila a partir de un diccionario de valores crudos.
    3. Preprocesar la fila con el mismo pipeline usado en el entrenamiento.
    4. Predecir el nivel de riesgo y obtener las probabilidades por clase.
    5. Generar una explicación SHAP con las variables más influyentes.

Uso típico desde la aplicación Streamlit:

    from src.evaluador_riesgo import evaluar_deportista

    resultado = evaluar_deportista(datos_dict)
    print(resultado["prediccion"])        # "bajo", "medio" o "alto"
    print(resultado["color_semaforo"])    # "#28a745", "#ffc107" o "#dc3545"
    print(resultado["top_variables"])     # lista de (nombre, valor_shap)
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Optional

import joblib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Asegurar que la raíz del proyecto esté en sys.path cuando se ejecuta
# este módulo directamente (python src/evaluador_riesgo.py)
# ---------------------------------------------------------------------------
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from src.variables import VARIABLES  # noqa: E402
from src.preprocesador import preprocesar  # noqa: E402

# ---------------------------------------------------------------------------
# Configuración del logger del módulo
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Constantes del módulo
# ---------------------------------------------------------------------------

# Clases del modelo en el orden en que sklearn las devuelve (orden alfabético)
_CLASES: list[str] = ["alto", "bajo", "medio"]

# Colores del semáforo de riesgo (formato hex CSS)
_COLORES_SEMAFORO: dict[str, str] = {
    "bajo": "#28a745",   # verde
    "medio": "#ffc107",  # amarillo
    "alto": "#dc3545",   # rojo
}

# Rutas por defecto relativas a la raíz del proyecto
_RUTA_MODELO_DEFAULT: str = "modelos/mejor_modelo.pkl"
_RUTA_SCALER_DEFAULT: str = "modelos/scaler.pkl"


# ===========================================================================
# 1. CARGA DEL PIPELINE ENTRENADO
# ===========================================================================


def cargar_pipeline(
    ruta_modelo: str = _RUTA_MODELO_DEFAULT,
    ruta_scaler: str = _RUTA_SCALER_DEFAULT,
) -> tuple[Any, StandardScaler]:
    """Carga el modelo entrenado y el scaler desde disco.

    Las rutas relativas se resuelven desde la raíz del proyecto (directorio
    padre de ``src/``).

    Args:
        ruta_modelo: Ruta al archivo ``.joblib`` del modelo entrenado.
            Por defecto ``modelos/modelo_rf.joblib``.
        ruta_scaler: Ruta al archivo ``.joblib`` del StandardScaler ajustado
            durante el entrenamiento. Por defecto ``modelos/scaler.joblib``.

    Returns:
        Tupla ``(modelo, scaler)`` listos para inferencia.

    Raises:
        FileNotFoundError: Si alguno de los archivos no existe en la ruta indicada.
        RuntimeError: Si joblib no puede deserializar alguno de los archivos.

    Example:
        >>> modelo, scaler = cargar_pipeline()
        >>> modelo.predict(X)
    """
    ruta_modelo_abs = _resolver_ruta(ruta_modelo)
    ruta_scaler_abs = _resolver_ruta(ruta_scaler)

    if not ruta_modelo_abs.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en: {ruta_modelo_abs}\n"
            "Entrena el modelo primero y guárdalo con joblib.dump()."
        )
    if not ruta_scaler_abs.exists():
        raise FileNotFoundError(
            f"No se encontró el scaler en: {ruta_scaler_abs}\n"
            "El scaler se genera al ejecutar el preprocesador en modo entrenamiento."
        )

    try:
        modelo = joblib.load(ruta_modelo_abs)
        logger.info("Modelo cargado desde: %s", ruta_modelo_abs)
    except Exception as exc:
        raise RuntimeError(
            f"Error al deserializar el modelo desde {ruta_modelo_abs}: {exc}"
        ) from exc

    try:
        scaler = joblib.load(ruta_scaler_abs)
        logger.info("Scaler cargado desde: %s", ruta_scaler_abs)
    except Exception as exc:
        raise RuntimeError(
            f"Error al deserializar el scaler desde {ruta_scaler_abs}: {exc}"
        ) from exc

    return modelo, scaler


# ===========================================================================
# 2. PREPARACIÓN DEL DEPORTISTA
# ===========================================================================


def preparar_deportista(
    datos_dict: dict[str, Any],
    scaler: StandardScaler,
) -> pd.DataFrame:
    """Transforma el diccionario de valores crudos en un DataFrame preprocesado.

    Construye un DataFrame de una sola fila a partir de ``datos_dict``,
    aplica el pipeline completo de preprocesamiento (ratios, asimetrías,
    encoding, normalización) usando el scaler ya ajustado durante el
    entrenamiento y devuelve el DataFrame listo para pasar al modelo.

    Args:
        datos_dict: Diccionario con los valores crudos de la evaluación.
            Las claves deben coincidir con los nombres de columna definidos
            en ``src.variables.VARIABLES`` (por ejemplo ``"cuadriceps_der"``,
            ``"genero"``, ``"edad"``). Las claves no reconocidas se ignoran
            con un aviso en el log.
        scaler: Instancia de ``StandardScaler`` ya ajustada (cargada desde
            disco), usada en modo inferencia sin reajustar.

    Returns:
        DataFrame de una fila con todas las features preprocesadas, sin la
        columna ``riesgo_lesion``.

    Raises:
        ValueError: Si ``datos_dict`` está vacío.

    Note:
        Las variables ausentes en ``datos_dict`` se rellenan con ``NaN``.
        El modelo puede tolerar valores nulos si fue entrenado con imputation;
        de lo contrario, verificar que todas las variables requeridas estén
        presentes antes de llamar a esta función.
    """
    if not datos_dict:
        raise ValueError(
            "El diccionario de datos del deportista está vacío. "
            "Proporciona al menos las variables principales de evaluación."
        )

    # Verificar claves desconocidas respecto al esquema definido
    claves_desconocidas = [k for k in datos_dict if k not in VARIABLES]
    if claves_desconocidas:
        logger.warning(
            "Las siguientes claves no están definidas en VARIABLES y se ignorarán "
            "durante el preprocesamiento: %s",
            claves_desconocidas,
        )

    # Construir DataFrame de una sola fila con el orden canónico de columnas
    columnas_canonicas = list(VARIABLES.keys())
    fila = {col: datos_dict.get(col, np.nan) for col in columnas_canonicas}
    df_crudo = pd.DataFrame([fila])

    logger.info(
        "DataFrame crudo construido: %d fila × %d columnas.",
        len(df_crudo),
        len(df_crudo.columns),
    )

    # Ejecutar el pipeline de preprocesamiento en modo inferencia (scaler ya ajustado)
    df_procesado, _ = preprocesar(df_crudo, scaler=scaler)

    # Eliminar la columna etiqueta si por algún motivo apareció
    df_procesado = df_procesado.drop(columns=["riesgo_lesion"], errors="ignore")

    # Seguridad: rellenar cualquier NaN residual con 0 para no romper el modelo
    n_nan = df_procesado.isnull().sum().sum()
    if n_nan > 0:
        logger.warning(
            "%d valor(es) NaN en el DataFrame preprocesado. Rellenando con 0. "
            "Verifica que todos los campos del formulario están completos.",
            n_nan,
        )
        df_procesado = df_procesado.fillna(0.0)

    logger.info(
        "Preprocesamiento completado: %d features disponibles para el modelo.",
        len(df_procesado.columns),
    )

    return df_procesado


# ===========================================================================
# 3. PREDICCIÓN DE RIESGO
# ===========================================================================


def predecir_riesgo(
    modelo: Any,
    df_procesado: pd.DataFrame,
) -> dict[str, Any]:
    """Ejecuta la predicción del modelo y estructura el resultado.

    Llama a ``modelo.predict()`` para obtener la clase predicha y a
    ``modelo.predict_proba()`` para obtener las probabilidades por clase.
    El resultado incluye el nivel de riesgo en texto, las probabilidades
    nominadas por clase y el color del semáforo correspondiente.

    Args:
        modelo: Modelo de clasificación entrenado con interfaz scikit-learn.
            Debe exponer ``predict()``, ``predict_proba()`` y el atributo
            ``classes_`` para identificar el orden de las probabilidades.
        df_procesado: DataFrame de una fila devuelto por ``preparar_deportista``.

    Returns:
        Diccionario con las siguientes claves:

        - ``"prediccion"`` (str): Nivel de riesgo predicho: ``"bajo"``,
          ``"medio"`` o ``"alto"``.
        - ``"probabilidades"`` (dict[str, float]): Probabilidades por clase,
          por ejemplo ``{"bajo": 0.15, "medio": 0.35, "alto": 0.50}``.
        - ``"color_semaforo"`` (str): Código de color hexadecimal asociado
          al nivel predicho (verde / amarillo / rojo).

    Raises:
        ValueError: Si el modelo no dispone del método ``predict_proba``.
        RuntimeError: Si la predicción falla por incompatibilidad de features.
    """
    if not hasattr(modelo, "predict_proba"):
        raise ValueError(
            "El modelo no implementa predict_proba(). "
            "Usa un clasificador probabilístico (RandomForest, GradientBoosting, etc.)."
        )

    # Predicción de clase
    try:
        prediccion_raw = modelo.predict(df_procesado)[0]
    except Exception as exc:
        raise RuntimeError(
            f"Error al ejecutar modelo.predict(): {exc}\n"
            "Verifica que el DataFrame tiene las mismas features que en el entrenamiento."
        ) from exc

    prediccion = str(prediccion_raw).lower()

    # Probabilidades por clase
    try:
        probas_array = modelo.predict_proba(df_procesado)[0]
    except Exception as exc:
        raise RuntimeError(
            f"Error al ejecutar modelo.predict_proba(): {exc}"
        ) from exc

    # Mapear probabilidades a nombres de clase usando modelo.classes_
    clases_modelo = [str(c).lower() for c in modelo.classes_]
    probabilidades = {
        clase: float(round(proba, 4))
        for clase, proba in zip(clases_modelo, probas_array)
    }

    color_semaforo = _COLORES_SEMAFORO.get(prediccion, "#6c757d")  # gris si clase desconocida

    logger.info(
        "Predicción: '%s' | Probabilidades: %s | Semáforo: %s",
        prediccion,
        probabilidades,
        color_semaforo,
    )

    return {
        "prediccion": prediccion,
        "probabilidades": probabilidades,
        "color_semaforo": color_semaforo,
    }


# ===========================================================================
# 4. EXPLICACIÓN SHAP
# ===========================================================================


def explicar_prediccion(
    modelo: Any,
    df_procesado: pd.DataFrame,
    max_variables: int = 10,
) -> dict[str, Any]:
    """Genera una explicación SHAP para la predicción de un deportista.

    Intenta usar ``shap.TreeExplainer`` (eficiente para modelos de árboles
    como RandomForest o GradientBoosting). Si el modelo no es compatible,
    recurre a ``shap.KernelExplainer`` con una muestra de fondo sintética.

    Los valores SHAP se calculan para la clase de mayor probabilidad (la
    clase predicha), y se devuelven las ``max_variables`` variables con mayor
    impacto absoluto junto con una figura de cascada (waterfall plot).

    Args:
        modelo: Modelo de clasificación entrenado compatible con SHAP.
        df_procesado: DataFrame de una fila preprocesada (salida de
            ``preparar_deportista``).
        max_variables: Número máximo de variables a incluir en
            ``"top_variables"`` y en el gráfico. Por defecto 10.

    Returns:
        Diccionario con las siguientes claves:

        - ``"shap_values"``: Array de valores SHAP crudos para la instancia
          (forma ``(n_features,)`` para la clase predicha).
        - ``"top_variables"`` (list[tuple[str, float]]): Lista de tuplas
          ``(nombre_variable, valor_shap)`` ordenadas por importancia
          absoluta descendente, limitada a ``max_variables``.
        - ``"figura_waterfall"`` (matplotlib.figure.Figure | None): Figura
          con el gráfico de cascada SHAP. Puede ser ``None`` si SHAP no
          puede generar la figura en el entorno actual.

    Note:
        ``shap.KernelExplainer`` puede ser lento para modelos grandes.
        Se recomienda usar siempre un modelo compatible con TreeExplainer
        (scikit-learn RandomForest, XGBoost, LightGBM, CatBoost).
    """
    shap_values_instancia: np.ndarray
    explainer_usado: str

    # CalibradorUmbralAlto no es un árbol reconocible por TreeExplainer → ir
    # directamente a KernelExplainer. Para modelos de árbol puro (RF, GB sin
    # wrapper) se podría usar TreeExplainer, pero multiclass GBT tampoco es
    # compatible con él en SHAP 0.51.
    # El fondo de ceros equivale a la media del espacio escalado (StandardScaler
    # centra en 0), lo que es un punto de referencia razonable para 1 instancia.
    try:
        fondo = np.zeros((1, df_procesado.shape[1]))
        explainer = shap.KernelExplainer(
            modelo.predict_proba,
            fondo,
            feature_names=list(df_procesado.columns),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw = explainer.shap_values(df_procesado, nsamples=100)
        shap_values_instancia, indice_clase = _extraer_shap_clase_predicha(
            raw, modelo, df_procesado
        )
        explainer_usado = "KernelExplainer"
        logger.info("SHAP KernelExplainer aplicado correctamente.")
    except Exception as exc_kernel:
        logger.error("No se pudo generar explicación SHAP: %s", exc_kernel)
        return {
            "shap_values": None,
            "top_variables": [],
            "figura_waterfall": None,
        }

    # --- Top variables por importancia absoluta ---
    nombres_features = list(df_procesado.columns)
    pares = list(zip(nombres_features, shap_values_instancia.tolist()))
    top_variables = sorted(pares, key=lambda x: abs(x[1]), reverse=True)[:max_variables]

    logger.info(
        "Top %d variables por impacto SHAP (%s): %s",
        max_variables,
        explainer_usado,
        [(nombre, round(val, 4)) for nombre, val in top_variables],
    )

    # --- Figura waterfall ---
    figura_waterfall = _generar_figura_waterfall(
        shap_values=shap_values_instancia,
        nombres_features=nombres_features,
        valores_features=df_procesado.iloc[0].values,
        max_display=max_variables,
        clase_predicha=str(modelo.classes_[indice_clase]).lower(),
    )

    return {
        "shap_values": shap_values_instancia,
        "top_variables": top_variables,
        "figura_waterfall": figura_waterfall,
    }


# ===========================================================================
# 5. IMPORTANCIA DE VARIABLES DEL MODELO
# ===========================================================================


def importancia_variables_modelo(
    modelo: Any,
    df_procesado: pd.DataFrame,
    n_top: int = 10,
) -> list[tuple[str, float]]:
    """Devuelve las n_top variables más importantes según el modelo entrenado.

    Para ``CalibradorUmbralAlto`` accede al ``modelo_base`` subyacente.
    Usa ``feature_importances_`` (GBT, RF) si está disponible.

    Args:
        modelo: Clasificador entrenado (o wrapper ``CalibradorUmbralAlto``).
        df_procesado: DataFrame preprocesado de una fila (salida de
            ``preparar_deportista``). Solo se usan sus nombres de columna.
        n_top: Número de variables a devolver. Por defecto 10.

    Returns:
        Lista de tuplas ``(nombre_feature, importancia)`` ordenadas de mayor
        a menor importancia, limitada a ``n_top`` elementos. Lista vacía si
        el modelo no expone ``feature_importances_``.
    """
    modelo_base = getattr(modelo, "modelo_base", modelo)
    if not hasattr(modelo_base, "feature_importances_"):
        logger.warning("El modelo no expone feature_importances_; importancia no disponible.")
        return []

    nombres = list(df_procesado.columns)
    importancias = modelo_base.feature_importances_
    pares = sorted(zip(nombres, importancias), key=lambda x: x[1], reverse=True)
    return pares[:n_top]


# ===========================================================================
# 6. FUNCIÓN DE CONVENIENCIA — EVALUACIÓN COMPLETA
# ===========================================================================


def evaluar_deportista(
    datos_dict: dict[str, Any],
    ruta_modelo: str = _RUTA_MODELO_DEFAULT,
    ruta_scaler: str = _RUTA_SCALER_DEFAULT,
) -> dict[str, Any]:
    """Evalúa el riesgo de lesión de un deportista en un único paso.

    Combina la carga del pipeline, el preprocesamiento, la predicción y la
    explicación SHAP en una sola llamada. Es la función de entrada principal
    para la aplicación Streamlit y cualquier otro cliente.

    Args:
        datos_dict: Diccionario con los valores crudos de la evaluación del
            deportista. Las claves deben seguir la nomenclatura de
            ``src.variables.VARIABLES`` (ej. ``"cuadriceps_der": 320``).
        ruta_modelo: Ruta al archivo del modelo entrenado.
            Por defecto ``"modelos/mejor_modelo.pkl"`` (CalibradorUmbralAlto).
        ruta_scaler: Ruta al archivo del scaler ajustado.
            Por defecto ``"modelos/scaler.pkl"``.

    Returns:
        Diccionario con las siguientes claves:

        - ``"prediccion"`` (str): ``"bajo"``, ``"medio"`` o ``"alto"``.
        - ``"probabilidades"`` (dict[str, float]): Probabilidad de cada clase.
        - ``"color_semaforo"`` (str): Color hexadecimal del semáforo.
        - ``"top_variables"`` (list[tuple[str, float]]): Variables más
          influyentes según SHAP (nombre, valor SHAP).
        - ``"figura_waterfall"`` (matplotlib.figure.Figure | None): Gráfico
          de cascada SHAP o ``None`` si no se pudo generar.

    Raises:
        FileNotFoundError: Si el modelo o el scaler no existen en las rutas indicadas.
        ValueError: Si ``datos_dict`` está vacío.

    Example:
        >>> from src.evaluador_riesgo import evaluar_deportista
        >>> resultado = evaluar_deportista({"edad": 25, "genero": "masculino", ...})
        >>> print(resultado["prediccion"])
        "medio"
    """
    logger.info("Iniciando evaluación completa del deportista.")

    # Paso 1: Cargar modelo y scaler
    modelo, scaler = cargar_pipeline(ruta_modelo, ruta_scaler)

    # Paso 2: Preprocesar los datos del deportista
    df_procesado = preparar_deportista(datos_dict, scaler)

    # Paso 3: Predecir nivel de riesgo
    resultado_prediccion = predecir_riesgo(modelo, df_procesado)

    # Paso 4: Explicar la predicción con SHAP
    resultado_shap = explicar_prediccion(modelo, df_procesado)

    resultado_final = {
        **resultado_prediccion,
        "top_variables": resultado_shap["top_variables"],
        "figura_waterfall": resultado_shap["figura_waterfall"],
    }

    logger.info(
        "Evaluación completada. Nivel de riesgo: '%s' (prob. más alta: %.1f%%).",
        resultado_final["prediccion"],
        max(resultado_final["probabilidades"].values()) * 100,
    )

    return resultado_final


# ===========================================================================
# FUNCIONES AUXILIARES PRIVADAS
# ===========================================================================


def _resolver_ruta(ruta: str) -> Path:
    """Convierte una ruta relativa en absoluta usando la raíz del proyecto.

    Args:
        ruta: Ruta relativa (ej. ``"modelos/modelo_rf.joblib"``) o absoluta.

    Returns:
        Objeto ``Path`` absoluto.
    """
    p = Path(ruta)
    if p.is_absolute():
        return p
    return _RAIZ_PROYECTO / p


def _extraer_shap_clase_predicha(
    raw_shap: Any,
    modelo: Any,
    df_procesado: pd.DataFrame,
) -> tuple[np.ndarray, int]:
    """Extrae los valores SHAP correspondientes a la clase predicha.

    Maneja las distintas formas en que shap puede devolver los valores según
    la versión y el tipo de explainer:

    - Lista de arrays (una por clase): forma ``[array(n_inst, n_feat), ...]``
    - Array 3D: forma ``(n_inst, n_feat, n_clases)``
    - Array 2D: forma ``(n_inst, n_feat)`` — ya directamente la clase positiva

    Args:
        raw_shap: Salida directa de ``explainer.shap_values()``.
        modelo: Modelo con atributo ``classes_`` y método ``predict()``.
        df_procesado: DataFrame de la instancia evaluada.

    Returns:
        Tupla ``(shap_values_1d, indice_clase)`` donde ``shap_values_1d``
        es un array de forma ``(n_features,)`` y ``indice_clase`` es el
        índice de la clase predicha dentro de ``modelo.classes_``.
    """
    clases_modelo = [str(c).lower() for c in modelo.classes_]
    clase_predicha = str(modelo.predict(df_procesado)[0]).lower()

    # Determinar índice de la clase predicha
    try:
        indice_clase = clases_modelo.index(clase_predicha)
    except ValueError:
        logger.warning(
            "Clase predicha '%s' no encontrada en modelo.classes_. Se usa índice 0.",
            clase_predicha,
        )
        indice_clase = 0

    # Caso 1: Lista de arrays (una por clase) — formato habitual de TreeExplainer
    if isinstance(raw_shap, list):
        shap_2d = np.array(raw_shap[indice_clase])  # forma (n_inst, n_feat)
        return shap_2d[0], indice_clase

    raw_arr = np.array(raw_shap)

    # Caso 2: Array 3D (n_inst, n_feat, n_clases)
    if raw_arr.ndim == 3:
        return raw_arr[0, :, indice_clase], indice_clase

    # Caso 3: Array 2D (n_inst, n_feat)
    if raw_arr.ndim == 2:
        return raw_arr[0], indice_clase

    # Caso 4: Array 1D (n_feat) — ya listo
    return raw_arr, indice_clase


def _generar_figura_waterfall(
    shap_values: np.ndarray,
    nombres_features: list[str],
    valores_features: np.ndarray,
    max_display: int,
    clase_predicha: str,
) -> Optional[matplotlib.figure.Figure]:
    """Genera un gráfico de cascada (waterfall) con los valores SHAP.

    Muestra las ``max_display`` variables con mayor impacto absoluto sobre
    la predicción, con barras rojas para contribuciones positivas (aumentan
    el riesgo) y azules para negativas (reducen el riesgo).

    Args:
        shap_values: Array 1D de valores SHAP para la instancia.
        nombres_features: Lista con los nombres de todas las features.
        valores_features: Array 1D con los valores reales de las features.
        max_display: Número máximo de variables a mostrar.
        clase_predicha: Nombre de la clase predicha (para el título).

    Returns:
        Figura de matplotlib con el gráfico, o ``None`` si la generación falla.
    """
    try:
        # Construir objeto Explanation de shap para usar su API de plots
        explicacion = shap.Explanation(
            values=shap_values,
            base_values=0.0,  # valor base aproximado (sin expected_value exacto)
            data=valores_features,
            feature_names=nombres_features,
        )

        fig, ax = plt.subplots(figsize=(10, max(4, max_display * 0.5)))
        shap.plots.waterfall(
            explicacion,
            max_display=max_display,
            show=False,
        )
        fig = plt.gcf()
        fig.suptitle(
            f"Explicación SHAP — Clase predicha: {clase_predicha.upper()}",
            fontsize=12,
            fontweight="bold",
            y=1.01,
        )
        plt.tight_layout()
        logger.info("Figura waterfall SHAP generada correctamente.")
        return fig

    except Exception as exc:
        logger.warning(
            "No se pudo generar la figura waterfall SHAP: %s. "
            "Generando gráfico de barras alternativo.",
            exc,
        )
        return _generar_figura_barras_alternativa(
            shap_values=shap_values,
            nombres_features=nombres_features,
            max_display=max_display,
            clase_predicha=clase_predicha,
        )


def _generar_figura_barras_alternativa(
    shap_values: np.ndarray,
    nombres_features: list[str],
    max_display: int,
    clase_predicha: str,
) -> Optional[matplotlib.figure.Figure]:
    """Gráfico de barras horizontales como alternativa al waterfall de SHAP.

    Se usa como fallback cuando ``shap.plots.waterfall`` no está disponible
    o falla. Muestra las ``max_display`` variables más importantes ordenadas
    por valor SHAP absoluto descendente.

    Args:
        shap_values: Array 1D de valores SHAP.
        nombres_features: Nombres de todas las features.
        max_display: Número máximo de barras a mostrar.
        clase_predicha: Nombre de la clase predicha (para el título).

    Returns:
        Figura de matplotlib o ``None`` si también falla.
    """
    try:
        pares = sorted(
            zip(nombres_features, shap_values.tolist()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:max_display]

        nombres = [p[0] for p in reversed(pares)]
        valores = [p[1] for p in reversed(pares)]
        colores = ["#dc3545" if v > 0 else "#007bff" for v in valores]

        fig, ax = plt.subplots(figsize=(10, max(4, max_display * 0.45)))
        ax.barh(nombres, valores, color=colores)
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlabel("Valor SHAP (impacto en la predicción)")
        ax.set_title(
            f"Variables más influyentes — Clase predicha: {clase_predicha.upper()}",
            fontweight="bold",
        )
        ax.tick_params(axis="y", labelsize=9)
        plt.tight_layout()
        logger.info("Figura de barras alternativa generada correctamente.")
        return fig

    except Exception as exc:
        logger.error("No se pudo generar ninguna figura SHAP: %s", exc)
        return None


# ===========================================================================
# BLOQUE PRINCIPAL — Ejemplo con deportista de valores medianos
# ===========================================================================

if __name__ == "__main__":
    # Deportista de ejemplo construido con los valores medianos de cada variable
    # definida en src.variables.VARIABLES.
    # Los rangos se extraen del campo "rango_sintetico" (o "rango_normal" como
    # respaldo) para obtener el punto medio de cada variable continua.

    print("=" * 60)
    print("  IntApp — Evaluador de riesgo individual")
    print("  Deportista de ejemplo con valores medianos")
    print("=" * 60)

    deportista_ejemplo: dict[str, Any] = {}

    for nombre_col, info in VARIABLES.items():
        tipo = info.get("tipo", "continua")

        if tipo == "continua":
            # Usar el punto medio del rango sintético como valor representativo
            rango = info.get("rango_sintetico") or info.get("rango_normal")
            if rango:
                valor = (rango[0] + rango[1]) / 2.0
            else:
                valor = 0.0
            deportista_ejemplo[nombre_col] = round(valor, 1)

        elif tipo == "ordinal":
            categorias = info.get("categorias")
            rango = info.get("rango_sintetico") or info.get("rango_normal")
            if categorias:
                # Valor central de las categorías disponibles
                deportista_ejemplo[nombre_col] = categorias[len(categorias) // 2]
            elif rango:
                deportista_ejemplo[nombre_col] = int((rango[0] + rango[1]) / 2)
            else:
                deportista_ejemplo[nombre_col] = 0

        elif tipo == "categorica":
            categorias = info.get("categorias", [])
            # Primera categoría como valor por defecto
            deportista_ejemplo[nombre_col] = categorias[0] if categorias else "masculino"

        elif tipo == "binaria":
            # Variables binarias (ej. thomas_test): negativo=0 por defecto
            deportista_ejemplo[nombre_col] = 0

    print("\nVariables del deportista de ejemplo:")
    for clave, valor in sorted(deportista_ejemplo.items()):
        unidad = VARIABLES[clave].get("unidad", "")
        print(f"  {clave:<45} {valor} {unidad}")

    print("\n" + "-" * 60)
    print("Intentando evaluar con el modelo entrenado...")
    print("(Asegúrate de haber entrenado y guardado el modelo antes.)")
    print("-" * 60)

    try:
        resultado = evaluar_deportista(deportista_ejemplo)

        print(f"\n  Nivel de riesgo   : {resultado['prediccion'].upper()}")
        print(f"  Color semáforo    : {resultado['color_semaforo']}")
        print("\n  Probabilidades por clase:")
        for clase, prob in sorted(resultado["probabilidades"].items()):
            barra = "#" * int(prob * 30)
            print(f"    {clase:<8} {prob:.1%}  {barra}")

        print(f"\n  Top {len(resultado['top_variables'])} variables más influyentes (SHAP):")
        for nombre, valor_shap in resultado["top_variables"]:
            direccion = "▲" if valor_shap > 0 else "▼"
            print(f"    {direccion} {nombre:<45} {valor_shap:+.4f}")

        if resultado["figura_waterfall"] is not None:
            ruta_fig = _RAIZ_PROYECTO / "figuras" / "shap_ejemplo_deportista.png"
            ruta_fig.parent.mkdir(parents=True, exist_ok=True)
            resultado["figura_waterfall"].savefig(ruta_fig, bbox_inches="tight", dpi=150)
            print(f"\n  Figura SHAP guardada en: {ruta_fig}")
        else:
            print("\n  No se generó figura SHAP.")

    except FileNotFoundError as e:
        print(f"\n  [AVISO] Modelo no encontrado: {e}")
        print("  Ejecuta el notebook de entrenamiento para generar el modelo.")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
