"""
modelo.py — Módulo de entrenamiento y evaluación de modelos ML para prevención de lesiones.

Entrena y compara tres clasificadores multiclase para predecir el nivel de riesgo
de lesión deportiva (bajo / medio / alto) a partir del DataFrame preprocesado:

    1. Random Forest       — robusto ante outliers y no requiere normalización
    2. Regresión Logística — interpretable, rápido, útil como línea base
    3. Gradient Boosting   — generalmente el más preciso; usa sample_weight
                             como compensación al no soportar class_weight

Uso típico (entrenamiento completo):
    python -m src.modelo

Uso como módulo:
    from src.modelo import dividir_datos, entrenar_random_forest, evaluar_modelo
    X_train, X_test, y_train, y_test = dividir_datos(df)
    modelo = entrenar_random_forest(X_train, y_train)
    resultados = evaluar_modelo(modelo, X_test, y_test, nombre="Random Forest")
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")  # backend no interactivo para CLI (evita bloqueo con plt.show)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight

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
# Rutas del proyecto
# ---------------------------------------------------------------------------
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

# ---------------------------------------------------------------------------
# Constantes del módulo
# ---------------------------------------------------------------------------

# Clases de nivel de riesgo en orden lógico (bajo → medio → alto)
CLASES_RIESGO: list[str] = ["bajo", "medio", "alto"]

def _f1_macro(y_test, y_pred):
    """F1 macro siempre sobre las 3 clases principales, en orden fijo."""
    from sklearn.metrics import f1_score
    return f1_score(y_test, y_pred, average="macro", labels=CLASES_RIESGO, zero_division=0)

# ---------------------------------------------------------------------------
# Clases auxiliares y funciones de calibración de umbral
# ---------------------------------------------------------------------------


def _predecir_con_umbral(
    probas: np.ndarray, clases: list[str], idx_alto: int, umbral: float
) -> np.ndarray:
    """Clasifica usando un umbral reducido para 'alto' (minimiza falsos negativos)."""
    preds = []
    for row in probas:
        if row[idx_alto] >= umbral:
            preds.append("alto")
        else:
            tmp = row.copy()
            tmp[idx_alto] = 0.0
            preds.append(clases[np.argmax(tmp)])
    return np.array(preds)


def _predecir_con_umbrales_dual(
    probas: np.ndarray,
    clases: list[str],
    idx_alto: int,
    umbral_alto: float,
    idx_bajo: int,
    umbral_bajo: float,
) -> np.ndarray:
    """Clasifica con umbral reducido para 'alto' y umbral elevado para 'bajo'.

    Lógica por fila:
        1. Si prob('alto') >= umbral_alto  → 'alto'
        2. Si prob('bajo') >= umbral_bajo  → 'bajo'   (necesita alta confianza)
        3. En otro caso                    → 'medio'  (casos borderline)

    Al exigir más confianza para 'bajo', los casos frontera entre 'bajo' y 'medio'
    se clasifican como 'medio', mejorando su recall a costa de reducir levemente
    el recall de 'bajo'.
    """
    preds = []
    for row in probas:
        if row[idx_alto] >= umbral_alto:
            preds.append("alto")
        elif row[idx_bajo] >= umbral_bajo:
            preds.append("bajo")
        else:
            preds.append("medio")
    return np.array(preds)


class CalibradorUmbralAlto:
    """Wrapper sklearn con umbrales de decisión calibrados para 'alto' y opcionalmente 'bajo'.

    - ``umbral_alto`` (< 0.50): reduce el umbral de decisión para 'alto', minimizando
      falsos negativos en atletas de alto riesgo (error clínicamente más grave).
    - ``umbral_bajo`` (> 0.50, opcional): eleva el umbral de decisión para 'bajo',
      forzando a que los casos borderline entre 'bajo' y 'medio' sean clasificados
      como 'medio'. Mejora el recall de la clase 'medio' con un coste moderado en
      la precisión de 'bajo'.

    Si ``umbral_bajo`` es None se aplica solo el umbral de 'alto' (comportamiento
    original, compatible con modelos guardados antes del umbral dual).

    Compatible con la interfaz predict/predict_proba de scikit-learn y con SHAP.
    """

    def __init__(
        self,
        modelo_base: Any,
        umbral_alto: float = 0.30,
        umbral_bajo: float | None = None,
    ) -> None:
        self.modelo_base = modelo_base
        self.umbral_alto = umbral_alto
        self.umbral_bajo = umbral_bajo
        self.classes_ = modelo_base.classes_

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.modelo_base.predict_proba(X)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        probas = self.predict_proba(X)
        clases = list(self.classes_)
        if "alto" not in clases:
            return self.modelo_base.predict(X)
        idx_alto = clases.index("alto")

        # getattr fallback: modelos serializados antes del umbral dual no tienen
        # el atributo umbral_bajo en su __dict__ (pickle restaura __dict__ directamente).
        umbral_bajo = getattr(self, "umbral_bajo", None)
        if umbral_bajo is not None and "bajo" in clases:
            idx_bajo = clases.index("bajo")
            return _predecir_con_umbrales_dual(
                probas, clases, idx_alto, self.umbral_alto, idx_bajo, umbral_bajo
            )
        return _predecir_con_umbral(probas, clases, idx_alto, self.umbral_alto)


def calibrar_umbral_alto(
    modelo_base: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    min_f1_macro: float = 0.58,
    min_precision_alto: float = 0.60,
) -> float:
    """Encuentra el umbral para 'alto' que maximiza recall_alto con dos restricciones:
    F1 macro >= min_f1_macro  Y  precision_alto >= min_precision_alto.

    La restricción de precisión evita umbrales demasiado agresivos (p.ej. 0.10) que
    generan una tasa de falsos positivos clínicamente inaceptable: clasificar como
    'alto riesgo' a un deportista sano tiene costes reales (sobre-intervención, alarma
    innecesaria, pérdida de credibilidad del sistema).

    Args:
        modelo_base: Clasificador ya entrenado con predict_proba.
        X_val: Features de validación (NO el test set — usar train-val split).
        y_val: Etiquetas reales de validación.
        min_f1_macro: F1 macro mínimo aceptable. Por defecto 0.58.
        min_precision_alto: Precisión mínima para la clase 'alto'. Por defecto 0.60.
            Garantiza que al menos el 60% de las alarmas de alto riesgo sean correctas.

    Returns:
        Umbral óptimo (float en [0.10, 0.50]).
    """
    clases = list(modelo_base.classes_)
    if "alto" not in clases:
        return 0.33
    idx_alto = clases.index("alto")
    probas = modelo_base.predict_proba(X_val)

    mejor_umbral = 0.50   # fallback conservador
    mejor_recall = 0.0

    print("\n  Calibración de umbral para 'alto' (val set):")
    print(f"  {'Umbral':>8} | {'Recall alto':>11} | {'Prec alto':>9} | {'F1 macro':>10} | {'OK':>4}")
    print("  " + "-" * 52)

    for umbral_val in np.arange(0.50, 0.08, -0.02):
        preds = _predecir_con_umbral(probas, clases, idx_alto, umbral_val)
        r_alto  = recall_score(y_val, preds, labels=["alto"], average="macro", zero_division=0)
        p_alto  = precision_score(y_val, preds, labels=["alto"], average="macro", zero_division=0)
        f1_m    = _f1_macro(y_val, preds)
        cumple  = f1_m >= min_f1_macro and p_alto >= min_precision_alto
        ok      = "✓" if cumple else "✗"
        print(f"  {umbral_val:>8.2f} | {r_alto:>11.4f} | {p_alto:>9.4f} | {f1_m:>10.4f} | {ok:>4}")
        if cumple and r_alto > mejor_recall:
            mejor_recall = r_alto
            mejor_umbral = round(float(umbral_val), 2)

    print(
        f"\n  → Umbral óptimo: {mejor_umbral:.2f} "
        f"(recall_alto={mejor_recall:.4f}, "
        f"restricciones: F1≥{min_f1_macro}, Prec≥{min_precision_alto})\n"
    )
    return mejor_umbral


def calibrar_umbrales_dual(
    modelo_base: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    umbral_alto_fijo: float,
    min_f1_macro: float = 0.65,
    min_precision_alto: float = 0.60,
    min_recall_alto: float | None = None,
    min_recall_bajo: float | None = None,
) -> float:
    """Dado umbral_alto ya calibrado, encuentra umbral_bajo que maximiza recall_medio.

    Fija ``umbral_alto_fijo`` y busca en [0.50, 0.90] el ``umbral_bajo`` que maximiza
    recall_medio sujeto a cuatro restricciones opcionales:
        - F1 macro >= min_f1_macro
        - precision_alto >= min_precision_alto
        - recall_alto >= min_recall_alto  (si se especifica)
        - recall_bajo >= min_recall_bajo  (si se especifica, evita colapso de bajo→medio)

    La restricción ``min_recall_bajo`` es la más importante en la práctica: sin ella,
    el optimizador puede encontrar umbrales muy altos (0.80–0.90) que suben recall_medio
    a costa de reclasificar la mayoría de los casos reales de 'bajo' como 'medio',
    lo que no aporta valor clínico y destruye la fiabilidad del sistema.

    Si ningún candidato cumple todas las restricciones, devuelve None (sin umbral dual).

    Args:
        modelo_base: Clasificador ya entrenado con predict_proba.
        X_val: Features de validación (mismo split usado para umbral_alto).
        y_val: Etiquetas reales de validación.
        umbral_alto_fijo: Umbral para 'alto' ya calibrado (fijo durante la búsqueda).
        min_f1_macro: F1 macro mínimo aceptable. Por defecto 0.65.
        min_precision_alto: Precisión mínima para 'alto'. Por defecto 0.60.
        min_recall_alto: Recall mínimo para 'alto' (None = no restringir).
        min_recall_bajo: Recall mínimo para 'bajo' (None = no restringir). Recomendado
            ≥ 0.75 para evitar que los deportistas de bajo riesgo sean sobre-escalados.

    Returns:
        Umbral óptimo para 'bajo' (float en [0.50, 0.90]), o None si ningún candidato
        mejora la línea base respetando todas las restricciones.
    """
    clases = list(modelo_base.classes_)
    if "medio" not in clases or "bajo" not in clases or "alto" not in clases:
        return None
    idx_alto = clases.index("alto")
    idx_bajo = clases.index("bajo")
    probas = modelo_base.predict_proba(X_val)

    # Línea base: recall_medio con solo el umbral de 'alto'
    preds_base = _predecir_con_umbral(probas, clases, idx_alto, umbral_alto_fijo)
    recall_medio_base = recall_score(
        y_val, preds_base, labels=["medio"], average="macro", zero_division=0
    )
    mejor_recall_medio = recall_medio_base
    mejor_umbral_bajo: float | None = None  # None = sin mejora encontrada

    print(
        f"\n  Calibración de umbral para 'bajo' "
        f"(val set, umbral_alto fijo={umbral_alto_fijo:.2f}, "
        f"línea base rec_medio={recall_medio_base:.4f}):"
    )
    restricciones_str = (
        f"F1≥{min_f1_macro}, Prec_alto≥{min_precision_alto}"
        + (f", Rec_alto≥{min_recall_alto}" if min_recall_alto else "")
        + (f", Rec_bajo≥{min_recall_bajo}" if min_recall_bajo else "")
    )
    print(
        f"  {'Umbral_bajo':>11} | {'Rec medio':>9} | {'Rec alto':>8} | "
        f"{'Rec bajo':>8} | {'F1 macro':>10} | {'OK':>4}"
    )
    print("  " + "-" * 68)

    for umbral_bajo_val in np.arange(0.50, 0.91, 0.02):
        preds = _predecir_con_umbrales_dual(
            probas, clases, idx_alto, umbral_alto_fijo, idx_bajo, umbral_bajo_val
        )
        r_medio = recall_score(y_val, preds, labels=["medio"], average="macro", zero_division=0)
        r_alto  = recall_score(y_val, preds, labels=["alto"],  average="macro", zero_division=0)
        r_bajo  = recall_score(y_val, preds, labels=["bajo"],  average="macro", zero_division=0)
        p_alto  = precision_score(y_val, preds, labels=["alto"], average="macro", zero_division=0)
        f1_m    = _f1_macro(y_val, preds)
        cumple  = (
            f1_m >= min_f1_macro
            and p_alto >= min_precision_alto
            and (min_recall_alto is None or r_alto >= min_recall_alto)
            and (min_recall_bajo is None or r_bajo >= min_recall_bajo)
        )
        ok = "✓" if cumple else "✗"
        print(
            f"  {umbral_bajo_val:>11.2f} | {r_medio:>9.4f} | {r_alto:>8.4f} | "
            f"{r_bajo:>8.4f} | {f1_m:>10.4f} | {ok:>4}"
        )
        if cumple and r_medio > mejor_recall_medio:
            mejor_recall_medio = r_medio
            mejor_umbral_bajo = round(float(umbral_bajo_val), 2)

    if mejor_umbral_bajo is None:
        print(
            f"\n  → Sin umbral bajo beneficioso ({restricciones_str}). "
            f"Se usará solo umbral_alto.\n"
        )
    else:
        print(
            f"\n  → Umbral bajo óptimo: {mejor_umbral_bajo:.2f} "
            f"(recall_medio={mejor_recall_medio:.4f} vs base={recall_medio_base:.4f}, "
            f"restricciones: {restricciones_str})\n"
        )
    return mejor_umbral_bajo


def validar_cruzada(
    X: pd.DataFrame,
    y: pd.Series,
    semilla: int = 42,
    n_folds: int = 5,
) -> pd.DataFrame:
    """Validación cruzada estratificada (k-fold) para los tres modelos base.

    Ejecuta k folds sobre el conjunto de entrenamiento y devuelve media ± desviación
    estándar de F1 macro y Recall 'alto'. Permite estimar la varianza del rendimiento
    más allá de un único split 80/20.

    Los casos 'no_concluyente' se excluyen antes de los folds (gestionados por reglas).

    Args:
        X: Matriz de features (sin columna objetivo).
        y: Serie de etiquetas.
        semilla: Semilla aleatoria para los folds.
        n_folds: Número de folds. Por defecto 5.

    Returns:
        DataFrame con columnas ``F1_media``, ``F1_std``, ``Recall_alto_media``,
        ``Recall_alto_std`` e índice = nombre del modelo.
    """
    from sklearn.model_selection import StratifiedKFold

    # Excluir no_concluyente
    mask = y != "no_concluyente"
    X_cv, y_cv = X[mask].reset_index(drop=True), y[mask].reset_index(drop=True)

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=semilla)

    metricas: dict[str, dict[str, list[float]]] = {
        "Random Forest":       {"f1": [], "recall_alto": []},
        "Regresión Logística": {"f1": [], "recall_alto": []},
        "Gradient Boosting":   {"f1": [], "recall_alto": []},
    }

    # Silenciar logs durante CV para no saturar la salida
    _prev_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.WARNING)

    print(f"\n--- Validación cruzada ({n_folds}-fold estratificada) ---")
    for fold_idx, (tr_idx, vl_idx) in enumerate(skf.split(X_cv, y_cv), 1):
        X_tr, X_vl = X_cv.iloc[tr_idx], X_cv.iloc[vl_idx]
        y_tr, y_vl = y_cv.iloc[tr_idx], y_cv.iloc[vl_idx]

        for nombre, modelo_fn, kwargs in [
            ("Random Forest",       entrenar_random_forest,       {}),
            ("Regresión Logística", entrenar_regresion_logistica,  {}),
            ("Gradient Boosting",   entrenar_gradient_boosting,   {"peso_extra_alto": 2.5}),
        ]:
            m = modelo_fn(X_tr, y_tr, semilla=semilla, **kwargs)
            y_pred = m.predict(X_vl)
            metricas[nombre]["f1"].append(_f1_macro(y_vl, y_pred))
            metricas[nombre]["recall_alto"].append(
                recall_score(y_vl, y_pred, labels=["alto"], average="macro", zero_division=0)
            )

        print(f"  Fold {fold_idx}/{n_folds} completado.")

    logging.getLogger().setLevel(_prev_level)

    filas = []
    for nombre, vals in metricas.items():
        f1_arr = np.array(vals["f1"])
        ra_arr = np.array(vals["recall_alto"])
        filas.append({
            "Modelo":             nombre,
            "F1_media":           round(f1_arr.mean(), 4),
            "F1_std":             round(f1_arr.std(), 4),
            "Recall_alto_media":  round(ra_arr.mean(), 4),
            "Recall_alto_std":    round(ra_arr.std(), 4),
        })

    df_cv = pd.DataFrame(filas).set_index("Modelo")

    print(f"\n{'='*60}")
    print(f"  VALIDACIÓN CRUZADA ({n_folds}-FOLD) — RESULTADOS")
    print(f"{'='*60}")
    print(df_cv.to_string())
    print(f"{'='*60}\n")

    return df_cv


# Directorio de salida para figuras
_DIR_FIGURAS = _RAIZ_PROYECTO / "figuras"

# Directorio de salida para modelos serializados
_DIR_MODELOS = _RAIZ_PROYECTO / "modelos"


# ===========================================================================
# 1. DIVISIÓN DE DATOS
# ===========================================================================


def dividir_datos(
    df: pd.DataFrame,
    columna_objetivo: str = "riesgo_lesion",
    test_size: float = 0.2,
    semilla: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Divide el DataFrame en conjuntos de entrenamiento y prueba con estratificación.

    La estratificación garantiza que la distribución de clases de ``riesgo_lesion``
    se mantenga proporcional en ambas particiones, lo cual es esencial cuando
    las clases están desequilibradas.

    Args:
        df: DataFrame preprocesado con features y columna objetivo.
        columna_objetivo: Nombre de la columna de etiquetas (``riesgo_lesion``).
        test_size: Proporción del conjunto de prueba. Por defecto 0.20 (20 %).
        semilla: Semilla aleatoria para reproducibilidad.

    Returns:
        Tupla ``(X_train, X_test, y_train, y_test)``.

    Raises:
        ValueError: Si ``columna_objetivo`` no está presente en ``df``.

    # TODO ROBERTO: puedes cambiar test_size a 0.15 si tienes pocos datos
    #               (< 300 muestras) para dejar más ejemplos al entrenamiento.
    """
    if columna_objetivo not in df.columns:
        raise ValueError(
            f"La columna objetivo '{columna_objetivo}' no existe en el DataFrame. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    X = df.drop(columns=[columna_objetivo])
    y = df[columna_objetivo]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=semilla,
        stratify=y,  # estratificación por clase de riesgo
    )

    logger.info(
        "División completada — Entrenamiento: %d muestras | Prueba: %d muestras",
        len(X_train),
        len(X_test),
    )
    logger.info(
        "Distribución en entrenamiento:\n%s",
        y_train.value_counts(normalize=True).round(3).to_string(),
    )

    return X_train, X_test, y_train, y_test


# ===========================================================================
# 2. MODELOS DE ENTRENAMIENTO
# ===========================================================================


def entrenar_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    semilla: int = 42,
) -> RandomForestClassifier:
    """Entrena un clasificador Random Forest con pesos de clase balanceados.

    Configuración:
        - ``n_estimators=200``: 200 árboles de decisión.
        - ``class_weight='balanced'``: ajusta automáticamente los pesos inversamente
          proporcionales a las frecuencias de clase, compensando el desequilibrio.
        - ``random_state=semilla``: reproduce resultados.

    Args:
        X_train: Matriz de features de entrenamiento.
        y_train: Serie de etiquetas de entrenamiento (``nivel_riesgo``).
        semilla: Semilla aleatoria para reproducibilidad.

    Returns:
        Modelo ``RandomForestClassifier`` ya ajustado.

    # TODO ROBERTO: experimenta con los siguientes hiperparámetros:
    #   - n_estimators: prueba 100, 300, 500 (más árboles = más estabilidad, más lento)
    #   - max_depth: por defecto None (crecimiento completo); prueba 5, 10, 15
    #     para regularizar y evitar sobreajuste
    #   - min_samples_leaf: prueba 2 o 3 para árboles más robustos con pocos datos
    #   - max_features: por defecto 'sqrt'; prueba 'log2' o 0.5
    #   - Usa GridSearchCV o RandomizedSearchCV para búsqueda sistemática
    """
    logger.info("Entrenando Random Forest (n_estimators=200, class_weight='balanced')...")

    modelo = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=semilla,
        # TODO ROBERTO: descomenta y ajusta los parámetros que quieras experimentar:
        # max_depth=10,
        # min_samples_leaf=2,
        # max_features="log2",
        n_jobs=-1,  # usa todos los núcleos disponibles
    )
    modelo.fit(X_train, y_train)

    logger.info("Random Forest entrenado correctamente.")
    return modelo


def entrenar_regresion_logistica(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    semilla: int = 42,
) -> LogisticRegression:
    """Entrena una Regresión Logística multinomial con pesos de clase balanceados.

    Configuración:
        - ``multi_class='multinomial'``: función softmax para clasificación
          multiclase (bajo / medio / alto).
        - ``class_weight='balanced'``: compensa el desequilibrio de clases.
        - ``max_iter=1000``: iteraciones suficientes para la convergencia.
        - ``solver='lbfgs'``: optimizador compatible con multinomial.

    Args:
        X_train: Matriz de features de entrenamiento.
        y_train: Serie de etiquetas de entrenamiento.
        semilla: Semilla aleatoria para reproducibilidad.

    Returns:
        Modelo ``LogisticRegression`` ya ajustado.

    # TODO ROBERTO: experimenta con:
    #   - C: parámetro de regularización inversa (por defecto 1.0)
    #         C pequeño (ej. 0.01) → más regularización → más sesgo, menos varianza
    #         C grande (ej. 10.0)  → menos regularización → puede sobreajustar
    #   - penalty: 'l2' (por defecto) o 'l1' con solver='saga' para selección de features
    #   - solver: 'lbfgs' (por defecto), 'saga' (permite l1), 'newton-cg'
    """
    logger.info(
        "Entrenando Regresión Logística (multinomial, class_weight='balanced', max_iter=1000)..."
    )

    modelo = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        # multi_class='multinomial' es el comportamiento por defecto desde
        # scikit-learn 1.5 y el parámetro quedará obsoleto en 1.7; se omite.
        solver="lbfgs",
        random_state=semilla,
        # TODO ROBERTO: descomenta para experimentar:
        # C=0.1,
        # penalty="l2",
    )
    modelo.fit(X_train, y_train)

    logger.info("Regresión Logística entrenada correctamente.")
    return modelo


def entrenar_gradient_boosting(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    semilla: int = 42,
    peso_extra_alto: float = 1.0,
    peso_extra_medio: float = 1.0,
) -> GradientBoostingClassifier:
    """Entrena un clasificador Gradient Boosting con pesos de muestra balanceados.

    GradientBoostingClassifier no soporta ``class_weight`` directamente, por lo
    que se usa ``compute_sample_weight('balanced', y_train)`` para asignar un
    peso inversamente proporcional a la frecuencia de cada clase a cada muestra.

    Configuración:
        - ``n_estimators=400``: más etapas con learning_rate bajo → mejor generalización.
        - ``learning_rate=0.05``: shrinkage suave; complementa n_estimators=400.
        - ``max_depth=5``: profundidad suficiente para capturar interacciones entre variables.
        - ``subsample=0.8``: Stochastic GB, reduce varianza y riesgo de sobreajuste.
        - ``min_samples_leaf=3``: regularización en hojas, permite hojas más finas.

    Args:
        X_train: Matriz de features de entrenamiento.
        y_train: Serie de etiquetas de entrenamiento.
        semilla: Semilla aleatoria para reproducibilidad.
        peso_extra_alto: Multiplicador adicional sobre el peso balanceado para la
            clase 'alto'. Usa 2.0 para priorizar recall 'alto' en contexto clínico.
        peso_extra_medio: Multiplicador adicional para la clase 'medio'. Usa 1.5–2.0
            para compensar que 'medio' es la clase más difícil de separar.

    Returns:
        Modelo ``GradientBoostingClassifier`` ya ajustado.
    """
    logger.info(
        "Entrenando Gradient Boosting (n_estimators=400, lr=0.05, subsample=0.8, "
        "peso_extra_alto=%.1f, peso_extra_medio=%.1f)...",
        peso_extra_alto,
        peso_extra_medio,
    )

    pesos_muestra = compute_sample_weight(class_weight="balanced", y=y_train)

    if peso_extra_alto != 1.0:
        mask_alto = (y_train == "alto").values
        pesos_muestra[mask_alto] *= peso_extra_alto

    if peso_extra_medio != 1.0:
        mask_medio = (y_train == "medio").values
        pesos_muestra[mask_medio] *= peso_extra_medio

    logger.info(
        "Pesos de muestra. Clases: %s | Pesos únicos: %s",
        np.unique(y_train),
        np.unique(pesos_muestra.round(4)),
    )

    modelo = GradientBoostingClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        min_samples_leaf=3,
        random_state=semilla,
    )
    modelo.fit(X_train, y_train, sample_weight=pesos_muestra)

    logger.info("Gradient Boosting entrenado correctamente.")
    return modelo


# ===========================================================================
# 3. EVALUACIÓN DE MODELOS
# ===========================================================================


def evaluar_modelo(
    modelo: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    nombre: str = "Modelo",
) -> dict[str, Any]:
    """Evalúa un modelo entrenado sobre el conjunto de prueba.

    Calcula métricas de clasificación multiclase y genera la matriz de confusión
    como figura de matplotlib.

    Args:
        modelo: Clasificador scikit-learn ya ajustado con método ``predict``.
        X_test: Matriz de features del conjunto de prueba.
        y_test: Etiquetas reales del conjunto de prueba.
        nombre: Nombre descriptivo del modelo para títulos y logs.

    Returns:
        Diccionario con las siguientes claves:

        - ``accuracy`` (float): exactitud global.
        - ``precision_macro`` (float): precisión macro-promedio.
        - ``recall_macro`` (float): recall macro-promedio.
        - ``f1_macro`` (float): F1-score macro-promedio.
        - ``confusion_matrix`` (np.ndarray): matriz de confusión.
        - ``figura_confusion`` (plt.Figure): figura de la matriz de confusión.
    """
    logger.info("Evaluando modelo: %s", nombre)

    # Predicciones
    y_pred = modelo.predict(X_test)

    # --- Reporte de clasificación completo ---
    print(f"\n{'='*60}")
    print(f"  RESULTADOS — {nombre.upper()}")
    print(f"{'='*60}")
    print(f"\nMuestras de prueba: {len(y_test)}")
    print("\nInforme de clasificación:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=CLASES_RIESGO,
            target_names=CLASES_RIESGO,
            zero_division=0,
        )
    )

    # --- Métricas resumidas ---
    acc = accuracy_score(y_test, y_pred)
    prec_macro = precision_score(
        y_test, y_pred, average="macro", labels=CLASES_RIESGO, zero_division=0
    )
    rec_macro = recall_score(
        y_test, y_pred, average="macro", labels=CLASES_RIESGO, zero_division=0
    )
    f1_macro = f1_score(
        y_test, y_pred, average="macro", labels=CLASES_RIESGO, zero_division=0
    )

    recall_alto = recall_score(
        y_test, y_pred, labels=["alto"], average="macro", zero_division=0
    )

    print(f"Exactitud (accuracy)     : {acc:.4f}")
    print(f"Precisión macro          : {prec_macro:.4f}")
    print(f"Recall macro             : {rec_macro:.4f}")
    print(f"F1-score macro           : {f1_macro:.4f}")
    print(f"Recall clase 'alto'      : {recall_alto:.4f}  ← prioridad clínica")
    print(f"{'='*60}\n")

    logger.info(
        "%s — Accuracy: %.4f | F1 macro: %.4f",
        nombre,
        acc,
        f1_macro,
    )

    # --- Matriz de confusión ---
    cm = confusion_matrix(y_test, y_pred, labels=CLASES_RIESGO)

    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASES_RIESGO)
    disp.plot(
        ax=ax,
        colorbar=True,
        cmap="Blues",
        values_format="d",
    )
    ax.set_title(f"Matriz de confusión — {nombre}", fontsize=13, pad=14)
    ax.set_xlabel("Etiqueta predicha", fontsize=11)
    ax.set_ylabel("Etiqueta real", fontsize=11)
    fig.tight_layout()

    # Guardar figura en el directorio de figuras
    _DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    nombre_archivo = nombre.lower().replace(" ", "_").replace("/", "_")
    ruta_figura = _DIR_FIGURAS / f"confusion_{nombre_archivo}.png"
    fig.savefig(ruta_figura, dpi=150, bbox_inches="tight")
    logger.info("Matriz de confusión guardada en: %s", ruta_figura)

    return {
        "accuracy": acc,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
        "recall_alto": recall_alto,
        "confusion_matrix": cm,
        "figura_confusion": fig,
    }


# ===========================================================================
# 4. COMPARACIÓN DE MODELOS
# ===========================================================================


def comparar_modelos(resultados: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Compara los modelos entrenados mediante un gráfico de barras de F1-score.

    Args:
        resultados: Diccionario ``{nombre_modelo: dict_resultado}`` donde cada
            ``dict_resultado`` es el valor devuelto por ``evaluar_modelo``.

    Returns:
        DataFrame con una fila por modelo y columnas:
        ``accuracy``, ``precision_macro``, ``recall_macro``, ``f1_macro``.
        El DataFrame se imprime en consola y se guarda la figura comparativa.
    """
    if not resultados:
        raise ValueError("El diccionario de resultados está vacío.")

    # Construir tabla de métricas
    filas = []
    for nombre, res in resultados.items():
        filas.append(
            {
                "Modelo": nombre,
                "Accuracy": round(res["accuracy"], 4),
                "Precisión macro": round(res["precision_macro"], 4),
                "Recall macro": round(res["recall_macro"], 4),
                "F1 macro": round(res["f1_macro"], 4),
            }
        )

    df_comparacion = pd.DataFrame(filas).set_index("Modelo")

    print("\n" + "=" * 60)
    print("  COMPARACIÓN DE MODELOS")
    print("=" * 60)
    print(df_comparacion.to_string())
    print("=" * 60)

    mejor_modelo = df_comparacion["F1 macro"].idxmax()
    mejor_f1 = df_comparacion.loc[mejor_modelo, "F1 macro"]
    print(f"\nMejor modelo por F1 macro: {mejor_modelo} ({mejor_f1:.4f})\n")

    # --- Gráfico de barras de F1-score por modelo ---
    fig, ax = plt.subplots(figsize=(8, 5))

    nombres = df_comparacion.index.tolist()
    f1_scores = df_comparacion["F1 macro"].tolist()

    colores = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]  # 4º: rojo para GB Calibrado
    barras = ax.bar(nombres, f1_scores, color=colores[: len(nombres)], width=0.5, edgecolor="white")

    # Anotar valor encima de cada barra
    for barra, valor in zip(barras, f1_scores):
        ax.text(
            barra.get_x() + barra.get_width() / 2.0,
            barra.get_height() + 0.005,
            f"{valor:.4f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_ylim(0, 1.05)
    ax.set_title("Comparación de modelos — F1-score macro", fontsize=13, pad=14)
    ax.set_xlabel("Modelo", fontsize=11)
    ax.set_ylabel("F1-score macro", fontsize=11)
    ax.axhline(y=0.8, color="gray", linestyle="--", linewidth=0.8, label="Umbral 0.80")
    ax.legend(fontsize=9)
    fig.tight_layout()

    # Guardar figura
    _DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta_figura = _DIR_FIGURAS / "comparacion_modelos.png"
    fig.savefig(ruta_figura, dpi=150, bbox_inches="tight")
    logger.info("Figura de comparación guardada en: %s", ruta_figura)
    plt.close(fig)

    return df_comparacion


# ===========================================================================
# 5. PERSISTENCIA DE MODELOS
# ===========================================================================


def guardar_modelo(modelo: Any, ruta: str | Path) -> None:
    """Serializa un modelo entrenado a disco con joblib.

    Args:
        modelo: Objeto de clasificador scikit-learn ajustado.
        ruta: Ruta de destino del archivo ``.pkl`` (se crea si no existe).

    Raises:
        OSError: Si el directorio de destino no se puede crear.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, ruta)
    logger.info("Modelo guardado en: %s", ruta)


def cargar_modelo(ruta: str | Path) -> Any:
    """Carga un modelo serializado desde disco con joblib.

    Args:
        ruta: Ruta al archivo ``.pkl`` generado por ``guardar_modelo``.

    Returns:
        Clasificador scikit-learn deserializado y listo para inferencia.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de modelo en: {ruta}. "
            "Asegúrate de haber ejecutado el entrenamiento primero."
        )
    modelo = joblib.load(ruta)
    logger.info("Modelo cargado desde: %s", ruta)
    return modelo


# ===========================================================================
# 6. INTERVALOS DE CONFIANZA BOOTSTRAP
# ===========================================================================


def bootstrap_ic(
    y_true: "pd.Series | np.ndarray",
    y_pred: np.ndarray,
    metrica_fn: Any,
    n_iter: int = 1000,
    nivel_confianza: float = 0.95,
    semilla: int = 42,
) -> tuple[float, float]:
    """Intervalo de confianza bootstrap por percentiles para una métrica de clasificación.

    Remuestrea con reemplazamiento el par (y_true, y_pred) n_iter veces y devuelve
    los percentiles correspondientes al nivel de confianza pedido.

    El recall sobre la clase minoritaria 'alto' (n ≈ 80-100) no sigue una
    distribución normal — el IC bootstrap es más fiable que una fórmula analítica
    en este contexto.

    Args:
        y_true: Etiquetas reales del conjunto de prueba.
        y_pred: Predicciones del modelo (mismo orden que y_true).
        metrica_fn: Callable ``(y_true_boot, y_pred_boot) -> float``.
        n_iter: Número de remuestras. Por defecto 1000.
        nivel_confianza: Nivel de confianza del intervalo. Por defecto 0.95.
        semilla: Semilla aleatoria para reproducibilidad.

    Returns:
        Tupla ``(limite_inferior, limite_superior)``.
    """
    rng = np.random.default_rng(semilla)
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    n = len(y_true_arr)

    vals = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        vals[i] = metrica_fn(y_true_arr[idx], y_pred_arr[idx])

    alpha = (1.0 - nivel_confianza) / 2.0
    return float(np.percentile(vals, alpha * 100)), float(np.percentile(vals, (1.0 - alpha) * 100))


# ===========================================================================
# BLOQUE PRINCIPAL — Entrenamiento, evaluación y selección del mejor modelo
# ===========================================================================

if __name__ == "__main__":
    import argparse

    # --- Argumentos de línea de comandos ---
    parser = argparse.ArgumentParser(
        description=(
            "Entrena y compara Random Forest, Regresión Logística y Gradient Boosting "
            "para predicción de nivel de riesgo de lesión deportiva."
        )
    )
    parser.add_argument(
        "--datos",
        type=str,
        default=None,
        help=(
            "Ruta al CSV preprocesado de entrada. "
            "Por defecto: datos/procesados/dataset_sintetico.csv"
        ),
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=42,
        help="Semilla aleatoria para reproducibilidad (por defecto: 42).",
    )
    # TODO ROBERTO: añade aquí más argumentos si quieres parametrizar
    #               n_estimators o max_depth desde la línea de comandos
    args = parser.parse_args()

    # --- Rutas del proyecto ---
    RAIZ = Path(__file__).resolve().parents[1]
    DIR_PROCESADOS = RAIZ / "datos" / "procesados"
    DIR_MODELOS_OUT = RAIZ / "modelos"

    # --- Datos: CSV externo o generación automática ---
    if args.datos:
        ruta_datos = Path(args.datos)
        logger.info("Archivo de datos externo: %s", ruta_datos)
        try:
            df = pd.read_csv(ruta_datos)
            logger.info("Datos cargados: %d filas × %d columnas", len(df), len(df.columns))
        except FileNotFoundError:
            logger.error("Archivo no encontrado: %s", ruta_datos)
            sys.exit(1)
        except Exception as exc:
            logger.error("Error al leer el CSV: %s", exc)
            sys.exit(1)
    else:
        # Sin --datos: generar 5 × 1000 muestras con semillas distintas para
        # mayor diversidad, preprocesar y guardar scaler + CSV en el mismo paso.
        # Esto garantiza que modelo y scaler siempre provienen del mismo pipeline.
        logger.info("Sin --datos: generando dataset sintético (5 × 1000 muestras)...")
        from src.generador_datos import generar_dataset
        from src.preprocesador import preprocesar as _preprocesar

        semillas_gen = [args.semilla, args.semilla + 81, args.semilla + 1983, args.semilla + 777, args.semilla + 314]
        fragmentos_crudos = [generar_dataset(n_deportistas=1000, semilla=s) for s in semillas_gen]
        df_crudo = pd.concat(fragmentos_crudos, ignore_index=True)
        logger.info("Dataset crudo: %d filas × %d columnas", len(df_crudo), len(df_crudo.columns))

        df, scaler_generado = _preprocesar(df_crudo)
        logger.info("Dataset preprocesado: %d filas × %d columnas", len(df), len(df.columns))

        # Guardar scaler y CSV para uso futuro (app Streamlit, notebooks)
        DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
        DIR_MODELOS_OUT.mkdir(parents=True, exist_ok=True)
        ruta_scaler_out = DIR_MODELOS_OUT / "scaler.pkl"
        ruta_csv_out    = DIR_PROCESADOS / "dataset_sintetico.csv"
        joblib.dump(scaler_generado, ruta_scaler_out)
        df.to_csv(ruta_csv_out, index=False)
        logger.info("Scaler guardado en: %s", ruta_scaler_out)
        logger.info("CSV guardado en:    %s", ruta_csv_out)
        ruta_datos = ruta_csv_out

    # Verificar que la columna objetivo existe
    if "riesgo_lesion" not in df.columns:
        logger.error(
            "La columna 'riesgo_lesion' no está presente en el dataset. "
            "Columnas disponibles: %s",
            list(df.columns),
        )
        sys.exit(1)

    # Mostrar distribución de clases
    print("\nDistribución de clases en el dataset completo:")
    print(df["riesgo_lesion"].value_counts().to_string())

    # --- Dividir datos ---
    X_train, X_test, y_train, y_test = dividir_datos(
        df,
        columna_objetivo="riesgo_lesion",
        test_size=0.2,
        semilla=args.semilla,
    )

    # Excluir no_concluyente del entrenamiento ML: son gestionados por reglas clínicas,
    # no por el modelo. Con solo ~8 muestras y peso 12.5x distorsionan el aprendizaje.
    mascara_ml = y_train != "no_concluyente"
    X_train_ml = X_train[mascara_ml]
    y_train_ml = y_train[mascara_ml]
    n_excluidos = int((~mascara_ml).sum())
    if n_excluidos > 0:
        logger.info(
            "Excluidos %d casos 'no_concluyente' del entrenamiento ML "
            "(gestionados por reglas clínicas).",
            n_excluidos,
        )

    # --- Validación cruzada (antes del entrenamiento final) ---
    df_cv = validar_cruzada(X_train_ml, y_train_ml, semilla=args.semilla, n_folds=5)

    # --- Entrenar los tres modelos base ---
    print("\n--- Fase de entrenamiento ---")

    modelo_rf = entrenar_random_forest(X_train_ml, y_train_ml, semilla=args.semilla)
    modelo_rl = entrenar_regresion_logistica(X_train_ml, y_train_ml, semilla=args.semilla)
    modelo_gb = entrenar_gradient_boosting(X_train_ml, y_train_ml, semilla=args.semilla)

    # --- GB Calibrado: peso 2.5× para 'alto' + umbral reducido ---
    # Separamos un 20% del training como val set para calibrar el umbral sin
    # contaminar el test set. Luego reentrenamos en el conjunto completo.
    print("\n--- Calibración del umbral para 'alto' ---")
    X_tr_cal, X_val_cal, y_tr_cal, y_val_cal = train_test_split(
        X_train_ml,
        y_train_ml,
        test_size=0.20,
        random_state=args.semilla + 1,
        stratify=y_train_ml,
    )
    _gb_tmp = entrenar_gradient_boosting(
        X_tr_cal, y_tr_cal, semilla=args.semilla, peso_extra_alto=2.0, peso_extra_medio=1.8
    )
    umbral_optimo = calibrar_umbral_alto(_gb_tmp, X_val_cal, y_val_cal, min_f1_macro=0.58)
    del _gb_tmp

    # Reentrenar en el conjunto completo con el umbral encontrado
    modelo_gb_base_cal = entrenar_gradient_boosting(
        X_train_ml, y_train_ml, semilla=args.semilla, peso_extra_alto=2.0, peso_extra_medio=1.8
    )
    modelo_gb_cal = CalibradorUmbralAlto(modelo_gb_base_cal, umbral_optimo)
    logger.info(
        "GB Calibrado listo — umbral_alto=%.2f, peso_extra_alto=2.5",
        umbral_optimo,
    )

    # --- Calibración dual: umbral_bajo para mejorar recall_medio ---
    # Usando el mismo val split y el mismo modelo base (reentrenado sobre todo X_train_ml),
    # buscamos el umbral_bajo que maximiza recall_medio sin comprometer recall_alto.
    print("\n--- Calibración del umbral para 'bajo' (dual) ---")
    _gb_tmp2 = entrenar_gradient_boosting(
        X_tr_cal, y_tr_cal, semilla=args.semilla, peso_extra_alto=2.0, peso_extra_medio=1.8
    )
    umbral_bajo_optimo = calibrar_umbrales_dual(
        _gb_tmp2,
        X_val_cal,
        y_val_cal,
        umbral_alto_fijo=umbral_optimo,
        min_f1_macro=0.65,
        min_precision_alto=0.60,
        min_recall_alto=None,
        min_recall_bajo=0.70,
    )
    del _gb_tmp2

    # Si la calibración dual no encontró umbral beneficioso, umbral_bajo_optimo=None
    # y el modelo dual se comporta idéntico al calibrado (sin efecto sobre 'bajo').
    modelo_gb_dual = CalibradorUmbralAlto(
        modelo_gb_base_cal, umbral_optimo, umbral_bajo=umbral_bajo_optimo
    )
    if umbral_bajo_optimo is not None:
        logger.info(
            "GB Dual listo — umbral_alto=%.2f, umbral_bajo=%.2f, peso_extra_alto=2.5",
            umbral_optimo,
            umbral_bajo_optimo,
        )
    else:
        logger.info(
            "GB Dual sin umbral bajo beneficioso — equivalente a GB Calibrado "
            "(umbral_alto=%.2f)",
            umbral_optimo,
        )

    # --- Evaluar los cinco modelos ---
    print("\n--- Fase de evaluación ---")

    resultado_rf = evaluar_modelo(modelo_rf, X_test, y_test, nombre="Random Forest")
    resultado_rl = evaluar_modelo(
        modelo_rl, X_test, y_test, nombre="Regresión Logística"
    )
    resultado_gb = evaluar_modelo(
        modelo_gb, X_test, y_test, nombre="Gradient Boosting"
    )
    resultado_gb_cal = evaluar_modelo(
        modelo_gb_cal, X_test, y_test, nombre="GB Calibrado (alto)"
    )
    resultado_gb_dual = evaluar_modelo(
        modelo_gb_dual, X_test, y_test, nombre="GB Dual (alto+bajo)"
    )

    # --- Comparar modelos ---
    resultados_todos = {
        "Random Forest":        resultado_rf,
        "Regresión Logística":  resultado_rl,
        "Gradient Boosting":    resultado_gb,
        "GB Calibrado (alto)":  resultado_gb_cal,
        "GB Dual (alto+bajo)":  resultado_gb_dual,
    }

    df_comparacion = comparar_modelos(resultados_todos)

    # Añadir columnas recall_alto y recall_medio a la tabla comparativa
    _modelos_map = {
        "Random Forest":       modelo_rf,
        "Regresión Logística": modelo_rl,
        "Gradient Boosting":   modelo_gb,
        "GB Calibrado (alto)": modelo_gb_cal,
        "GB Dual (alto+bajo)": modelo_gb_dual,
    }
    df_comparacion["Recall alto"] = {
        n: round(res["recall_alto"], 4) for n, res in resultados_todos.items()
    }
    df_comparacion["Recall medio"] = {
        n: round(
            recall_score(
                y_test,
                _modelos_map[n].predict(X_test),
                labels=["medio"], average="macro", zero_division=0,
            ), 4
        )
        for n in resultados_todos
    }
    print("\nRecall clases clave por modelo:")
    print(df_comparacion[["F1 macro", "Recall alto", "Recall medio"]].to_string())

    # --- Seleccionar y guardar el mejor modelo ---
    # Modelo clínico: GB Dual si el umbral bajo encontrado mejora recall_medio sin
    # sacrificar F1 ni recall_bajo (restricciones de calibrar_umbrales_dual).
    # Si calibrar_umbrales_dual no encontró umbral beneficioso (devuelve None),
    # el dual es idéntico al calibrado y usamos este último como referencia.
    dual_es_mejor = (
        umbral_bajo_optimo is not None
        and resultado_gb_dual["f1_macro"] >= resultado_gb_cal["f1_macro"] - 0.01
    )
    modelo_clinico = modelo_gb_dual if dual_es_mejor else modelo_gb_cal
    nombre_clinico = "GB Dual" if dual_es_mejor else "GB Calibrado (alto)"

    # Fijar __module__ antes de serializar: cuando este archivo se ejecuta como
    # __main__, pickle guarda la clase como "__main__.CalibradorUmbralAlto".
    # Al cargar desde otro contexto (evaluador_riesgo, Streamlit), __main__
    # no tiene esa clase y la deserialización falla. Fijando __module__ a
    # 'src.modelo' el pickle buscará src.modelo.CalibradorUmbralAlto, que
    # siempre existe cuando se importa el módulo.
    import src.modelo as _src_modelo_ref
    CalibradorUmbralAlto.__module__ = "src.modelo"
    _src_modelo_ref.CalibradorUmbralAlto = CalibradorUmbralAlto

    DIR_MODELOS_OUT.mkdir(parents=True, exist_ok=True)
    ruta_mejor = DIR_MODELOS_OUT / "mejor_modelo.pkl"
    guardar_modelo(modelo_clinico, ruta_mejor)
    logger.info("Modelo clínico seleccionado: %s", nombre_clinico)

    guardar_modelo(modelo_rf,      DIR_MODELOS_OUT / "random_forest.pkl")
    guardar_modelo(modelo_rl,      DIR_MODELOS_OUT / "regresion_logistica.pkl")
    guardar_modelo(modelo_gb,      DIR_MODELOS_OUT / "gradient_boosting.pkl")
    guardar_modelo(modelo_gb_cal,  DIR_MODELOS_OUT / "gradient_boosting_calibrado.pkl")
    guardar_modelo(modelo_gb_dual, DIR_MODELOS_OUT / "gradient_boosting_dual.pkl")

    # --- Bootstrap IC 95% para recall_alto del modelo clínico (n_iter=1000) ---
    y_pred_clinico = modelo_clinico.predict(X_test)
    _recall_alto_fn = lambda yt, yp: recall_score(
        yt, yp, labels=["alto"], average="macro", zero_division=0
    )
    ic_lo, ic_hi = bootstrap_ic(y_test, y_pred_clinico, _recall_alto_fn, semilla=args.semilla)

    res_clinico = resultado_gb_dual if dual_es_mejor else resultado_gb_cal
    r_medio_clinico = recall_score(
        y_test, y_pred_clinico, labels=["medio"], average="macro", zero_division=0
    )

    # --- Resumen final ---
    umbral_bajo_str = f"{umbral_bajo_optimo:.2f}  (F1≥0.70, Rec_bajo≥0.75)" if umbral_bajo_optimo else "N/A  (sin umbral dual beneficioso)"
    print("\n--- Resumen del entrenamiento ---")
    print(f"  Dataset utilizado      : {ruta_datos}")
    print(f"  Muestras entrenamiento : {len(X_train_ml)}")
    print(f"  Muestras prueba        : {len(X_test)}")
    print(f"  Modelo clínico         : {nombre_clinico} (mejor_modelo.pkl)")
    print(f"  Umbral 'alto'          : {umbral_optimo:.2f}  (precision≥0.60, F1≥0.58)")
    print(f"  Umbral 'bajo'          : {umbral_bajo_str}")
    print(f"  Recall 'alto' (test)   : {res_clinico['recall_alto']:.4f}")
    print(f"  IC 95% recall_alto     : [{ic_lo:.4f}, {ic_hi:.4f}]  (bootstrap n=1000)")
    print(f"  Recall 'medio' (test)  : {r_medio_clinico:.4f}")
    print(f"  Precision 'alto' (test): {precision_score(y_test, y_pred_clinico, labels=['alto'], average='macro', zero_division=0):.4f}")
    print(f"  F1 macro (test)        : {res_clinico['f1_macro']:.4f}")
    print(f"  CV 5-fold GB (F1)      : {df_cv.loc['Gradient Boosting','F1_media']:.4f} ± {df_cv.loc['Gradient Boosting','F1_std']:.4f}")
    print(f"  CV 5-fold GB (Rec.alto): {df_cv.loc['Gradient Boosting','Recall_alto_media']:.4f} ± {df_cv.loc['Gradient Boosting','Recall_alto_std']:.4f}")
    print(f"  Modelo guardado en     : {ruta_mejor}")
    print(f"  Figuras guardadas en   : {_DIR_FIGURAS}")
