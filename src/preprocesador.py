"""
preprocesador.py — Pipeline de preprocesamiento para IntApp v2.3.

Transforma el DataFrame crudo de evaluación en un conjunto de features listo
para el entrenamiento o la inferencia del modelo. El orden del pipeline es:

    1. calcular_ratios           → N → N/kg; ratios clínicos H:Q y ADD/ABD
    2. calcular_ratios_normativos → N/kg → ratio_ref por perfil (edad×género×actividad)
    3. calcular_asimetrias       → asimetría bilateral (%) para cada par _der / _izq
    4. codificar_categoricas     → encoding de genero y nivel_actividad
    5. eliminar_columnas_aux     → elimina columnas auxiliares del generador
    6. normalizar                → StandardScaler sobre variables continuas

Cambios v1 → v2.2
------------------
ELIMINADOS del v1: ybalance_anterior/posteromedial/posterolateral (3 direcciones YBT),
    triple_hop, rotacion_externa_cadera (movilidad), flexoextension_rodilla,
    thomas_test_iliopsoas + thomas_test_recto_femoral (continuas separadas).
AÑADIDOS en v2.2: y_balance_cs (score compuesto), rotadores_externos_cadera,
    nivel_actividad, thomas_test (binaria bilateral).
ELIMINADOS en v2.3: acwr, pss4, horas_sueno.
AÑADIDOS en v2.3: 12 features ratio_ref = valor_nkg / umbral_efectivo(genero, edad, actividad).
RATIO NUEVO: ratio_add_abd (aductores / glúteo medio, predictor inguinal).
COLUMNA ETIQUETA: renombrada de "nivel_riesgo" a "riesgo_lesion".
COLUMNAS AUXILIARES: score_total, confianza_score, confianza_categoria,
    reglas_activadas → se eliminan antes de normalizar (no son features del modelo).
ENCODING NUEVO: nivel_actividad (ordinal 0-3).

Uso típico (entrenamiento):
    df_procesado, scaler = preprocesar(df_crudo)
    joblib.dump(scaler, "modelos/scaler.pkl")

Uso típico (inferencia en la app):
    scaler = joblib.load("modelos/scaler.pkl")
    df_procesado, _ = preprocesar(df_nuevo, scaler=scaler)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Path del proyecto
# ---------------------------------------------------------------------------
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from src.variables import (  # noqa: E402
    VARIABLES,
    VARIABLES_FUERZA,
    VARIABLES_MOVILIDAD,
    VARIABLES_CONTROL,
    VARIABLES_CONTEXTO,
    COLUMNAS_FUERZA,
    COLUMNAS_MOVILIDAD,
    COLUMNAS_CONTROL,
    COLUMNAS_CONTEXTO,
    FACTORES_ACTIVIDAD,
    grupo_edad_clave,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Nombres base de todas las variables bilaterales (sin sufijo _der / _izq)
_BASES_BILATERALES: list[str] = [
    nombre
    for nombre, info in {
        **VARIABLES_FUERZA,
        **VARIABLES_MOVILIDAD,
        **VARIABLES_CONTROL,
    }.items()
    if info.get("bilateral", False)
]

# Columna etiqueta del modelo
COLUMNA_ETIQUETA: str = "riesgo_lesion"

# Columnas auxiliares generadas por generar_label() — NO son features del modelo
COLUMNAS_AUXILIARES: list[str] = [
    "score_total",
    "confianza_score",
    "confianza_categoria",
    "reglas_activadas",
]

# Encoding binario de género
_ENCODING_GENERO: dict[str, int] = {"masculino": 0, "femenino": 1}

# Encoding ordinal de nivel de actividad
_ENCODING_NIVEL_ACTIVIDAD: dict[str, int] = {
    "sedentario":   0,
    "recreacional": 1,
    "activo":       2,
    "elite":        3,
}

# Columnas ordinales y binarias que NO deben normalizarse con StandardScaler
_COLUMNAS_EXCLUIDAS_SCALER: set[str] = {
    "single_leg_squat_valgo_der",
    "single_leg_squat_valgo_izq",
    "thomas_test_der",
    "thomas_test_izq",
    "historial_lesional",
    "dolor_percibido_nrs",
    "hooper_index",
    "nivel_actividad",
    "genero",
    COLUMNA_ETIQUETA,
}


# ===========================================================================
# 1. CÁLCULO DE RATIOS CLÍNICOS
# ===========================================================================

def calcular_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Añade ratios clínicos derivados al DataFrame.

    Ratios calculados:
        - ratio_hq_der / ratio_hq_izq : isquiotibiales / cuádriceps (H:Q ratio).
          Referencia: Croisier et al. (2008) — < 0.60 = factor de riesgo LCA.
        - ratio_add_abd_der / ratio_add_abd_izq : aductores / glúteo medio.
          Referencia: Thorborg et al. (2011) — < 0.90 = riesgo inguinal.

    Args:
        df: DataFrame con las columnas crudas de evaluación.

    Returns:
        Copia del DataFrame con las columnas de ratios añadidas.
    """
    df = df.copy()

    # --- Ratio H:Q por lado (isquiotibiales / cuádriceps) ---
    for lado in ("der", "izq"):
        col_quad = f"cuadriceps_{lado}"
        col_isq  = f"isquiotibiales_{lado}"
        if col_quad in df.columns and col_isq in df.columns:
            denominador = df[col_quad].replace(0, np.nan)
            df[f"ratio_hq_{lado}"] = df[col_isq] / denominador
            logger.debug("Ratio H:Q %s calculado.", lado)
        else:
            logger.warning("Columnas H:Q %s no encontradas.", lado)

    # --- Ratio ADD/ABD (aductores / glúteo medio) por lado ---
    for lado in ("der", "izq"):
        col_add = f"aductores_cadera_{lado}"
        col_abd = f"gluteo_medio_{lado}"
        if col_add in df.columns and col_abd in df.columns:
            denominador = df[col_abd].replace(0, np.nan)
            df[f"ratio_add_abd_{lado}"] = df[col_add] / denominador
            logger.debug("Ratio ADD/ABD %s calculado.", lado)
        else:
            logger.warning("Columnas ADD/ABD %s no encontradas.", lado)

    # --- Fuerza normalizada por peso (N/kg) — cada músculo individualmente ---
    # Hace explícita la relación N/kg para que el modelo no tenga que inferirla.
    # Un sujeto de 60 kg con 240 N = 4.0 N/kg; uno de 100 kg con 240 N = 2.4 N/kg.
    _VARS_FUERZA = [
        "cuadriceps",
        "isquiotibiales",
        "gluteo_medio",
        "rotadores_externos_cadera",
        "aductores_cadera",
    ]
    if "peso_corporal" in df.columns:
        peso = df["peso_corporal"].replace(0, np.nan)
        cols_raw_a_eliminar = []
        for var in _VARS_FUERZA:
            for lado in ("der", "izq"):
                col = f"{var}_{lado}"
                if col in df.columns:
                    df[f"{col}_nkg"] = df[col] / peso
                    cols_raw_a_eliminar.append(col)
                    logger.debug("N/kg calculado para %s.", col)
        # Eliminar columnas raw en N: el modelo solo necesita N/kg
        # (a peso fijo, N y N/kg son perfectamente colineales — tener ambas
        # duplica la superficie de fuerza y distorsiona la importancia relativa)
        df = df.drop(columns=cols_raw_a_eliminar, errors="ignore")

    return df


# ===========================================================================
# 2. RATIOS NORMATIVOS POR PERFIL (edad × género × nivel_actividad)
# ===========================================================================

# Claves de género/edad válidas en las tablas normativas de variables.py
_CLAVES_NORMATIVAS: set[str] = {
    "M_18_35", "M_36_50", "M_51_65",
    "F_18_35", "F_36_50", "F_51_65",
}


def calcular_ratios_normativos(df: pd.DataFrame) -> pd.DataFrame:
    """Añade ratios valor / umbral_efectivo(genero, edad, nivel_actividad).

    Para cada variable de fuerza con tabla normativa estratificada calcula:
        <var>_ratio_ref = valor_nkg / (umbral_base(genero, edad) × factor_actividad)

    Ratio 1.0 → exactamente en el umbral de referencia para ese perfil.
    Ratio < 1.0 → déficit; Ratio > 1.0 → por encima de la referencia.

    Esto hace al modelo invariante ante diferencias de edad, género y nivel:
    un cuádriceps de 3.0 N/kg es deficitario en un hombre de 25 (ratio ~0.75)
    pero aceptable en una mujer de 55 sedentaria (ratio ~1.06).

    Debe ejecutarse ANTES de codificar_categoricas (necesita genero y
    nivel_actividad como strings).

    Args:
        df: DataFrame con columnas crudas de fuerza ya en N/kg (tras calcular_ratios)
            más edad, genero (str) y nivel_actividad (str).

    Returns:
        Copia del DataFrame con columnas <var>_ratio_ref añadidas.
    """
    df = df.copy()

    requeridas = {"edad", "genero", "nivel_actividad"}
    if not requeridas.issubset(df.columns):
        logger.warning(
            "calcular_ratios_normativos: faltan columnas %s — paso omitido.",
            requeridas - set(df.columns),
        )
        return df

    # Vectorizar la clave de tabla y el factor por fila
    genero_str = df["genero"].astype(str).str.lower().str.strip()
    prefijo_g = genero_str.map({"masculino": "M", "femenino": "F"}).fillna("M")
    grupo_e = df["edad"].apply(grupo_edad_clave)
    clave_tabla_s = prefijo_g + "_" + grupo_e          # "M_18_35", "F_51_65" ...
    factor_act_s = (
        df["nivel_actividad"].astype(str).str.lower().str.strip()
        .map(FACTORES_ACTIVIDAD)
        .fillna(1.0)
    )

    for nombre_var, info in VARIABLES.items():
        if info["bloque"] != "fuerza":
            continue
        tabla = info.get("umbral_riesgo_base")
        if not isinstance(tabla, dict):
            continue
        # Solo tablas con estratificación por género/edad
        lookup = {k: v for k, v in tabla.items() if k in _CLAVES_NORMATIVAS}
        if not lookup:
            continue

        es_repeticiones = tabla.get("_unidad_umbral") == "repeticiones"
        col_src = nombre_var if es_repeticiones else f"{nombre_var}_nkg"
        if col_src not in df.columns:
            continue

        col_out = f"{nombre_var}_ratio_ref"
        umbral_base_s = clave_tabla_s.map(lookup)
        umbral_efectivo_s = (umbral_base_s * factor_act_s).replace(0, np.nan)
        ratio = df[col_src] / umbral_efectivo_s

        # Filas sin contexto suficiente → ratio neutro 1.0 (sin penalización)
        ratio = ratio.fillna(1.0)
        df[col_out] = ratio
        logger.debug("Ratio normativo calculado: %s", col_out)

    return df


# ===========================================================================
# 3. CÁLCULO DE ASIMETRÍAS BILATERALES
# ===========================================================================

def calcular_asimetrias(df: pd.DataFrame) -> pd.DataFrame:
    """Añade el índice de asimetría bilateral (%) para cada par _der / _izq.

    Fórmula:
        asimetria_X = |X_der - X_izq| / max(|X_der|, |X_izq|) × 100

    0 = simetría perfecta. Umbral clínico habitual: 10-15 % según variable.
    También calcula la asimetría de los ratios y features derivados si existen.

    Args:
        df: DataFrame con columnas <variable>_der y <variable>_izq.

    Returns:
        Copia del DataFrame con columnas asimetria_<variable> añadidas.
    """
    df = df.copy()

    # Variables originales bilaterales
    bases_a_calcular = list(_BASES_BILATERALES)

    # Añadir ratios derivados bilaterales si existen
    for sufijo in ("ratio_hq", "ratio_add_abd"):
        if f"{sufijo}_der" in df.columns and f"{sufijo}_izq" in df.columns:
            bases_a_calcular.append(sufijo)

    for base in bases_a_calcular:
        col_der = f"{base}_der"
        col_izq = f"{base}_izq"

        if col_der not in df.columns or col_izq not in df.columns:
            logger.debug("Par bilateral '%s' no encontrado; se omite.", base)
            continue

        maximo = df[[col_der, col_izq]].abs().max(axis=1).replace(0, np.nan)
        df[f"asimetria_{base}"] = (df[col_der] - df[col_izq]).abs() / maximo * 100
        logger.debug("Asimetría '%s' calculada.", base)

    # Rellenar NaN en columnas de asimetría con 0.
    # Ocurre cuando ambos lados valen 0 (ej. thomas_test negativo bilateral,
    # valgo SLS grado 0 bilateral): 0/0 = NaN, pero clínicamente significa
    # simetría perfecta → asimetría = 0 %.
    cols_asimetria = [c for c in df.columns if c.startswith("asimetria_")]
    df[cols_asimetria] = df[cols_asimetria].fillna(0.0)

    return df


# ===========================================================================
# 4. ENCODING DE VARIABLES CATEGÓRICAS
# ===========================================================================

def codificar_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica las variables categóricas y ordinales del bloque de contexto.

    Transformaciones:
        - genero              : binario (masculino=0, femenino=1)
        - nivel_actividad     : ordinal (sedentario=0, recreacional=1,
                                         activo=2, elite=3)


    Args:
        df: DataFrame con las columnas en sus valores originales.

    Returns:
        Copia del DataFrame con las columnas ya codificadas en su lugar.
    """
    df = df.copy()

    # Género: binario
    if "genero" in df.columns:
        df["genero"] = (
            df["genero"].astype(str).str.lower().str.strip().map(_ENCODING_GENERO)
        )
        n_nulos = df["genero"].isna().sum()
        if n_nulos > 0:
            logger.warning("%d valor(es) de 'genero' no reconocidos → NaN.", n_nulos)
    else:
        logger.warning("Columna 'genero' no encontrada.")

    # Nivel de actividad: ordinal 0-3
    if "nivel_actividad" in df.columns:
        df["nivel_actividad"] = (
            df["nivel_actividad"].astype(str).str.lower().str.strip()
            .map(_ENCODING_NIVEL_ACTIVIDAD)
        )
        n_nulos = df["nivel_actividad"].isna().sum()
        if n_nulos > 0:
            logger.warning(
                "%d valor(es) de 'nivel_actividad' no reconocidos → NaN.", n_nulos
            )
    else:
        logger.warning("Columna 'nivel_actividad' no encontrada.")

    return df


# ===========================================================================
# 5. ELIMINAR COLUMNAS AUXILIARES
# ===========================================================================

def eliminar_columnas_aux(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina columnas auxiliares que no son features del modelo.

    Las columnas score_total, confianza_score, confianza_categoria y
    reglas_activadas las genera generar_label() para análisis exploratorio,
    pero no deben entrar al modelo como features (son derivadas de la
    etiqueta, lo que causaría fuga de datos).

    Args:
        df: DataFrame completo, posiblemente con columnas auxiliares.

    Returns:
        Copia del DataFrame sin las columnas auxiliares.
    """
    cols_a_eliminar = [c for c in COLUMNAS_AUXILIARES if c in df.columns]
    if cols_a_eliminar:
        logger.info("Eliminando columnas auxiliares: %s", cols_a_eliminar)
        df = df.drop(columns=cols_a_eliminar)
    return df


# ===========================================================================
# 6. NORMALIZACIÓN
# ===========================================================================

def normalizar(
    df: pd.DataFrame,
    scaler: Optional[StandardScaler] = None,
) -> tuple[pd.DataFrame, StandardScaler]:
    """Normaliza variables continuas con StandardScaler (media=0, std=1).

    Se excluyen de la normalización:
        - Variables ordinales (valgo SLS, historial, NRS, perfil exigencia,
          nivel actividad ya codificado como 0-3)
        - Variables binarias (thomas_test, género)
        - La etiqueta riesgo_lesion
        - Columnas no numéricas

    Args:
        df: DataFrame ya procesado por los pasos anteriores.
        scaler: Si se proporciona, aplica el scaler existente (modo inferencia).
                Si es None, ajusta uno nuevo (modo entrenamiento).

    Returns:
        Tupla (df_normalizado, scaler).
    """
    df = df.copy()

    columnas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    columnas_a_normalizar = [
        c for c in columnas_numericas
        if c not in _COLUMNAS_EXCLUIDAS_SCALER
    ]

    # Excluir columnas 100% NaN
    cols_solo_nan = [c for c in columnas_a_normalizar if df[c].isna().all()]
    if cols_solo_nan:
        logger.warning("Columnas 100%% NaN excluidas del scaler: %s", cols_solo_nan)
        columnas_a_normalizar = [c for c in columnas_a_normalizar if c not in cols_solo_nan]

    if not columnas_a_normalizar:
        logger.warning("No hay columnas numéricas para normalizar.")
        return df, scaler or StandardScaler()

    if scaler is None:
        scaler = StandardScaler()
        df[columnas_a_normalizar] = scaler.fit_transform(df[columnas_a_normalizar])
        logger.info("StandardScaler ajustado sobre %d columnas.", len(columnas_a_normalizar))
    else:
        cols_scaler = (
            list(scaler.feature_names_in_)
            if hasattr(scaler, "feature_names_in_")
            else columnas_a_normalizar
        )
        cols_comunes  = [c for c in cols_scaler if c in df.columns]
        cols_faltantes = [c for c in cols_scaler if c not in df.columns]
        if cols_faltantes:
            logger.warning("Columnas esperadas por el scaler no encontradas: %s", cols_faltantes)
        df[cols_comunes] = scaler.transform(df[cols_comunes])
        logger.info("Normalización aplicada con scaler existente (%d columnas).", len(cols_comunes))

    return df, scaler


# ===========================================================================
# 7. PIPELINE COMPLETO
# ===========================================================================

def preprocesar(
    df: pd.DataFrame,
    scaler: Optional[StandardScaler] = None,
) -> tuple[pd.DataFrame, StandardScaler]:
    """Pipeline completo: ratios → ratios normativos → asimetrías → encoding → eliminar aux → normalizar.

    Paso 2 (calcular_ratios_normativos) requiere genero y nivel_actividad
    como strings, por lo que debe ejecutarse antes del encoding categórico.

    Args:
        df: DataFrame crudo con las columnas del protocolo v2.3.
        scaler: Scaler ya ajustado (inferencia) o None para ajustar uno nuevo
                (entrenamiento).

    Returns:
        Tupla (df_procesado, scaler).

    Raises:
        ValueError: Si df está vacío.
    """
    if df.empty:
        raise ValueError("El DataFrame de entrada está vacío.")

    logger.info(
        "Inicio preprocesamiento v2.3. Filas: %d | Columnas: %d",
        len(df), len(df.columns),
    )

    df = calcular_ratios(df)
    logger.info("Paso 1/6: ratios clínicos y N/kg calculados.")

    df = calcular_ratios_normativos(df)
    logger.info("Paso 2/6: ratios normativos por perfil calculados.")

    df = calcular_asimetrias(df)
    logger.info("Paso 3/6: asimetrías bilaterales calculadas.")

    df = codificar_categoricas(df)
    logger.info("Paso 4/6: variables categóricas codificadas.")

    df = eliminar_columnas_aux(df)
    logger.info("Paso 5/6: columnas auxiliares eliminadas.")

    df, scaler = normalizar(df, scaler=scaler)
    logger.info("Paso 6/6: normalización aplicada.")

    logger.info(
        "Preprocesamiento finalizado. Filas: %d | Columnas: %d",
        len(df), len(df.columns),
    )

    return df, scaler


# ===========================================================================
# 8. UTILIDAD: OBTENER LISTA DE FEATURES
# ===========================================================================

def obtener_columnas_features(df: pd.DataFrame) -> list[str]:
    """Devuelve las columnas de features, excluyendo la etiqueta y auxiliares.

    Args:
        df: DataFrame preprocesado.

    Returns:
        Lista de nombres de columnas que son features del modelo.
    """
    excluir = {COLUMNA_ETIQUETA} | set(COLUMNAS_AUXILIARES)
    return [col for col in df.columns if col not in excluir]


# ===========================================================================
# BLOQUE PRINCIPAL
# ===========================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocesa el dataset sintético v2.3 y guarda el resultado."
    )
    parser.add_argument("--entrada",    type=str, default=None)
    parser.add_argument("--salida",     type=str, default=None)
    parser.add_argument("--scaler-out", type=str, default=None, dest="scaler_out")
    args = parser.parse_args()

    RAIZ           = Path(__file__).resolve().parents[1]
    DIR_SINTETICOS = RAIZ / "datos" / "sinteticos"
    DIR_PROCESADOS = RAIZ / "datos" / "procesados"
    DIR_MODELOS    = RAIZ / "modelos"

    DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    DIR_MODELOS.mkdir(parents=True, exist_ok=True)

    if args.entrada:
        ruta_entrada = Path(args.entrada)
    else:
        csvs = sorted(DIR_SINTETICOS.glob("*.csv"))
        if not csvs:
            logger.error("No hay CSVs en '%s'. Ejecuta primero el generador.", DIR_SINTETICOS)
            sys.exit(1)
        ruta_entrada = csvs[-1]

    logger.info("Archivo de entrada: %s", ruta_entrada)

    try:
        df_crudo = pd.read_csv(ruta_entrada)
        logger.info("CSV cargado: %d filas × %d columnas.", len(df_crudo), len(df_crudo.columns))
    except FileNotFoundError:
        logger.error("Archivo no encontrado: %s", ruta_entrada)
        sys.exit(1)

    df_procesado, scaler_ajustado = preprocesar(df_crudo)

    nombre_salida = f"procesado_{ruta_entrada.stem}.csv"
    ruta_salida = Path(args.salida) if args.salida else DIR_PROCESADOS / nombre_salida
    df_procesado.to_csv(ruta_salida, index=False)
    logger.info("DataFrame procesado guardado en: %s", ruta_salida)

    ruta_scaler = Path(args.scaler_out) if args.scaler_out else DIR_MODELOS / "scaler.pkl"
    joblib.dump(scaler_ajustado, ruta_scaler)
    logger.info("Scaler guardado en: %s", ruta_scaler)

    features = obtener_columnas_features(df_procesado)

    print("\n--- Resumen del preprocesamiento v2.3 ---")
    print(f"  Archivo de entrada  : {ruta_entrada}")
    print(f"  Filas procesadas    : {len(df_procesado)}")
    print(f"  Columnas totales    : {len(df_procesado.columns)}")
    print(f"  Features del modelo : {len(features)}")
    print(f"  CSV guardado en     : {ruta_salida}")
    print(f"  Scaler guardado en  : {ruta_scaler}")
