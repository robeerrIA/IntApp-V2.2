"""
generador_datos.py — Generador de datos sintéticos para IntApp.

Versión 2.3 alineada con el Protocolo de Scoring Clínico v2.3.

Resumen de la versión 2.3
-------------------------
1. Bloques actualizados al set de 19 variables originales:
   - Fuerza (6):    cuádriceps, isquiotibiales, glúteo medio, rotadores externos
                    de cadera, aductores cadera, tríceps sural.
   - Movilidad (3): dorsiflexión tobillo (WBLT), Thomas test (binaria fusionada),
                    rotación interna cadera.
   - Control (3):   Y-Balance Composite Score, single-leg squat valgo,
                    single-leg hop.
   - Contexto (7):  edad, género, peso corporal, nivel de actividad,
                    historial lesional, NRS, Hooper Index.

2. La generación de fuerza tiene en cuenta peso corporal y género: hombres y
   personas más pesadas tienen valores brutos más altos en N (clínicamente
   coherente con N/kg similar entre grupos).

3. Inyección de ruido cerca de los umbrales: el 25 % de la muestra se genera
   adrede en zona gris o por debajo del umbral, para que el modelo tenga
   suficientes ejemplos en la frontera de decisión y aprenda a discriminar.

4. La etiqueta de riesgo se asigna con `generar_label()` siguiendo el modelo
   lógico-decisional del protocolo v2.2:
   - Reglas A1-A6 (riesgo alto, booleanas).
   - Reglas M1-M5 (riesgo medio, booleanas).
   - Score ponderado total con zonas grises (puede elevar la categoría).
   - Categoría "no_concluyente" cuando NRS > 5 (corrección C3 del v2.1).

5. Distribución objetivo: 50 % bajo / 30 % medio / 20 % alto + ~3 % no
   concluyente. Se calibra ajustando los percentiles de las variables
   contextuales para que las reglas v2.2 produzcan esa proporción.

6. Salida adicional: el dataset incluye la columna auxiliar `confianza_score`
   (porcentaje de mediciones claras, fuera de zona gris) y `confianza_categoria`
   (alta / media / baja). No son targets del modelo; se guardan para que la app
   pueda recalcularlas en producción y para análisis exploratorio.

Uso
---
    python -m src.generador_datos          # genera y guarda el dataset
    from src.generador_datos import generar_dataset
    df = generar_dataset(n_deportistas=500, semilla=42)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.variables import (
    VARIABLES,
    VARIABLES_ORIGINALES,
    COLUMNAS_FUERZA,
    COLUMNAS_MOVILIDAD,
    COLUMNAS_CONTROL,
    COLUMNAS_CONTEXTO,
    FACTORES_ACTIVIDAD,
    grupo_edad_clave,
    SCORE_UMBRAL_ALTO,
    SCORE_UMBRAL_MEDIO,
    ZONA_GRIS_MARGEN,
    ZONA_GRIS_PUNTUACION_PARCIAL,
)

# =============================================================================
# CONSTANTES DE CORRELACIÓN
# =============================================================================

_CORR_BILATERAL    = 0.75   # correlación entre lado der/izq de la misma variable
_CORR_INTRA_BLOQUE = 0.45   # correlación entre músculos distintos del mismo bloque
_CORR_MOVILIDAD    = 0.35   # correlación entre segmentos de movilidad
_CORR_CONTROL      = 0.50   # correlación entre variables de control

# Probabilidad de generar un caso "frontera" para cada deportista.
# Los frontera tienen valores forzados cerca del umbral en 1-2 variables clave,
# para densificar la zona de decisión y mejorar el aprendizaje del modelo.
_PROB_FRONTERA = 0.35

# Probabilidad de generar un caso "no concluyente" (NRS > 5).
_PROB_NO_CONCLUYENTE = 0.03

# Factores multiplicadores de fuerza bruta por grupo de edad.
# Evidencia: Bohannon (1997), Andrews (1996), meta-análisis Front. Physiol. (2021, n=13.893).
# Declive ≈ 6 %/década en adultos activos (conservador respecto a los 8-15 %/década del
# rango publicado, apropiado para la población diana — ver docs/Evidencia_Valores_Normativos.md § D1).
_FACTORES_EDAD_GENERACION: dict[str, float] = {
    "18_35": 1.00,
    "36_50": 0.90,
    "51_65": 0.80,
}

# Factores multiplicadores de fuerza bruta por nivel de actividad.
# Evidencia: Owoeye (2024) — brecha deportistas universitarios/población general ≈ 37-39 %;
# Kraemer & Ratamess (2004) — entrenamiento aumenta fuerza 20-40 % vs. sedentarios.
# Rango total 0.88→1.22 = 38 %, coherente con la brecha observada en la literatura
# (ver docs/Evidencia_Valores_Normativos.md § D2).
_FACTORES_ACTIVIDAD_GENERACION: dict[str, float] = {
    "sedentario":   0.88,
    "recreacional": 1.00,
    "activo":       1.10,
    "elite":        1.22,
}


# =============================================================================
# UTILIDADES INTERNAS
# =============================================================================

def _clip_array(valores: np.ndarray, rango_sintetico: tuple[float, float]) -> np.ndarray:
    """Recorta los valores generados al rango sintético definido en VARIABLES."""
    return np.clip(valores, rango_sintetico[0], rango_sintetico[1])


def _medias_y_desviaciones(claves: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Devuelve (medias, sigmas) representativas de una población mayoritariamente
    sana.

    Estrategia:
      - Si la variable tiene `rango_normal` definido: la media se sitúa en
        el centro del rango normal (la zona saludable de referencia clínica),
        no en el centro del rango sintético. Esto es importante porque el
        rango sintético es amplio para cubrir casos extremos, pero la mayoría
        de la población real está en zona saludable.
      - σ se elige para que ~95 % de la muestra (±2σ) caiga dentro del rango
        normal, pero permitiendo cola de valores patológicos hacia el rango
        sintético.

    Para variables ordinales y categóricas no aplica (se generan aparte).
    """
    medias, sigmas = [], []
    for clave in claves:
        info = VARIABLES[clave]
        rango_sint = info["rango_sintetico"]
        rango_normal = info.get("rango_normal")
        if rango_normal is not None and rango_normal[0] != rango_normal[1]:
            # Centro y σ basados en la zona normal
            centro = (rango_normal[0] + rango_normal[1]) / 2.0
            sigma = (rango_normal[1] - rango_normal[0]) / 4.0
            # Pero ampliamos σ un 30 % para que haya cola de casos patológicos
            sigma *= 1.3
        else:
            centro = (rango_sint[0] + rango_sint[1]) / 2.0
            sigma = (rango_sint[1] - rango_sint[0]) / 4.0
        medias.append(centro)
        sigmas.append(sigma)
    return np.array(medias), np.array(sigmas)


def _construir_corr_bilateral(claves: list[str], corr_intra: float) -> np.ndarray:
    """
    Matriz de correlación: corr_intra entre variables distintas, 1.0 en diagonal,
    _CORR_BILATERAL entre el mismo músculo der/izq.
    """
    n = len(claves)
    corr = np.full((n, n), corr_intra)
    np.fill_diagonal(corr, 1.0)
    for j, cj in enumerate(claves):
        for k, ck in enumerate(claves):
            if j == k:
                continue
            base_j = cj.rsplit("_", 1)[0]
            base_k = ck.rsplit("_", 1)[0]
            if base_j == base_k:
                corr[j, k] = _CORR_BILATERAL
    return corr


def _normal_multivariante(
    n: int, claves: list[str], corr_mat: np.ndarray, rng: np.random.Generator,
) -> pd.DataFrame:
    """Muestra de normal multivariante con clipping al rango de cada variable."""
    medias, sigmas = _medias_y_desviaciones(claves)
    D = np.diag(sigmas)
    cov = D @ corr_mat @ D
    muestras = rng.multivariate_normal(mean=medias, cov=cov, size=n)
    for j, clave in enumerate(claves):
        muestras[:, j] = _clip_array(muestras[:, j], VARIABLES[clave]["rango_sintetico"])
    return pd.DataFrame(muestras, columns=claves)


# =============================================================================
# GENERACIÓN POR BLOQUES
# =============================================================================

def _generar_bloque_fuerza(
    n: int,
    peso_corporal: np.ndarray,
    es_masculino: np.ndarray,
    edad: np.ndarray,
    nivel_actividad: np.ndarray,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Genera el bloque de fuerza con escalado por peso corporal, género, edad y
    nivel de actividad.

    Idea clínica: la fuerza bruta (N) varía con el peso, el sexo, la edad y el
    nivel de entrenamiento. Para que el modelo aprenda estas señales, aplicamos
    factores evidenciados en la literatura (ver docs/Evidencia_Valores_Normativos.md
    secciones D1-D3). El scoring clínico trabaja en N/kg, así que el factor peso
    no introduce sesgo en las etiquetas; los factores de edad y actividad sí crean
    una correlación real con el riesgo resultante.
    """
    corr_mat = _construir_corr_bilateral(COLUMNAS_FUERZA, _CORR_INTRA_BLOQUE)
    df = _normal_multivariante(n, COLUMNAS_FUERZA, corr_mat, rng)

    # Escalado por peso corporal (peso medio asumido = 70 kg)
    factor_peso = (peso_corporal / 70.0).reshape(-1, 1)

    # Factor de género: ±18 % (Janssen 2000, Frontera 1991 — ver § D3)
    factor_genero = np.where(es_masculino, 1.18, 0.82).reshape(-1, 1)

    # Factor por grupo de edad (Bohannon 1997, Andrews 1996, Front.Physiol. meta-análisis 2021)
    factor_edad = np.where(
        edad < 36, _FACTORES_EDAD_GENERACION["18_35"],
        np.where(edad < 51, _FACTORES_EDAD_GENERACION["36_50"], _FACTORES_EDAD_GENERACION["51_65"]),
    ).reshape(-1, 1)

    # Factor por nivel de actividad (Owoeye 2024, Kraemer & Ratamess 2004)
    factor_actividad = np.vectorize(_FACTORES_ACTIVIDAD_GENERACION.get)(
        nivel_actividad, 1.0
    ).reshape(-1, 1)

    # No escalamos repeticiones del heel rise test (resistencia, no fuerza absoluta).
    cols_repeticiones = [c for c in COLUMNAS_FUERZA if VARIABLES[c]["unidad"] == "repeticiones"]
    cols_newtons      = [c for c in COLUMNAS_FUERZA if c not in cols_repeticiones]

    if cols_newtons:
        df[cols_newtons] = (
            df[cols_newtons].values
            * factor_peso
            * factor_genero
            * factor_edad
            * factor_actividad
        )
        for c in cols_newtons:
            df[c] = _clip_array(df[c].values, VARIABLES[c]["rango_sintetico"])

    return df


def _generar_bloque_movilidad(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Bloque movilidad. Las continuas se generan con normal multivariante;
    el Thomas test (binario bilateral) se genera por separado con probabilidad
    base de positivo y correlación der/izq.
    """
    cols_continuas = [c for c in COLUMNAS_MOVILIDAD if VARIABLES[c]["tipo"] == "continua"]
    cols_binarias  = [c for c in COLUMNAS_MOVILIDAD if VARIABLES[c]["tipo"] == "binaria"]

    # Continuas
    corr_mat = _construir_corr_bilateral(cols_continuas, _CORR_MOVILIDAD)
    df_cont = _normal_multivariante(n, cols_continuas, corr_mat, rng)

    # Thomas test binario bilateral con correlación entre lados:
    # 12 % positivo en cada lado, con correlación 0.5 (si un lado es positivo,
    # el otro tiene más probabilidad de serlo).
    # Implementación: generar una variable latente normal correlacionada,
    # umbralizar en el percentil 88 (deja ~12 % positivos por lado).
    if cols_binarias:
        # Pares (der, izq) por nombre base
        pares: dict[str, list[str]] = {}
        for c in cols_binarias:
            base = c.rsplit("_", 1)[0]
            pares.setdefault(base, []).append(c)

        df_bin = pd.DataFrame(index=range(n))
        for base, lados in pares.items():
            if len(lados) == 2:
                cov = np.array([[1.0, 0.5], [0.5, 1.0]])
                latente = rng.multivariate_normal([0, 0], cov, size=n)
                umbral = 1.175  # ≈ qnorm(0.88)
                for j, lado in enumerate(lados):
                    df_bin[lado] = (latente[:, j] > umbral).astype(int)
            else:
                df_bin[lados[0]] = (rng.random(n) < 0.12).astype(int)

        df = pd.concat([df_cont, df_bin], axis=1)[COLUMNAS_MOVILIDAD]
    else:
        df = df_cont

    return df


def _generar_bloque_control(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Bloque control: Y-Balance CS y single-leg hop son continuas correlacionadas
    bilateralmente; single_leg_squat_valgo es ordinal 0-3.
    """
    cols_continuas = [c for c in COLUMNAS_CONTROL if VARIABLES[c]["tipo"] == "continua"]
    cols_ordinales = [c for c in COLUMNAS_CONTROL if VARIABLES[c]["tipo"] == "ordinal"]

    # Continuas
    corr_mat = _construir_corr_bilateral(cols_continuas, _CORR_CONTROL)
    df_cont = _normal_multivariante(n, cols_continuas, corr_mat, rng)

    # Ordinal (single_leg_squat_valgo 0-3)
    probs_valgo = [0.40, 0.35, 0.18, 0.07]
    df_ord = pd.DataFrame(index=range(n))
    for col in cols_ordinales:
        cats = VARIABLES[col]["categorias"]
        df_ord[col] = rng.choice(cats, size=n, p=probs_valgo[: len(cats)])

    df = pd.concat([df_cont, df_ord], axis=1)[COLUMNAS_CONTROL]
    return df


def _generar_bloque_contexto(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Bloque contexto: edad, género, peso, nivel de actividad, historial lesional,
    NRS, ACWR, índice de estrés.

    El género, el peso, la edad y el nivel de actividad se generan ANTES que la
    fuerza (el bloque de fuerza los necesita para aplicar los factores correctores).
    """
    datos: dict[str, Any] = {}

    # Género (≈ 55 % hombres, 45 % mujeres)
    datos["genero"] = rng.choice(["masculino", "femenino"], size=n, p=[0.55, 0.45])
    es_masculino = datos["genero"] == "masculino"

    # Edad (sesgada hacia adultos jóvenes; rango 18-65)
    rango_edad = VARIABLES["edad"]["rango_sintetico"]
    edad = rng.normal(30.0, 9.0, size=n)
    datos["edad"] = _clip_array(edad, rango_edad).astype(int)

    # Peso corporal (depende del género)
    peso = np.empty(n)
    peso[es_masculino]  = rng.normal(78.0, 10.0, size=int(es_masculino.sum()))
    peso[~es_masculino] = rng.normal(63.0,  8.0, size=int((~es_masculino).sum()))
    datos["peso_corporal"] = _clip_array(peso, VARIABLES["peso_corporal"]["rango_sintetico"])

    # Nivel de actividad (4 categorías)
    datos["nivel_actividad"] = rng.choice(
        ["sedentario", "recreacional", "activo", "elite"],
        size=n, p=[0.10, 0.35, 0.40, 0.15],
    )

    # Historial lesional (0-10), exponencial sesgada a valores bajos.
    rango_hist = VARIABLES["historial_lesional"]["rango_sintetico"]
    hist_raw = rng.exponential(scale=2.2, size=n)
    datos["historial_lesional"] = np.round(_clip_array(hist_raw, rango_hist)).astype(int)

    # NRS — la mayoría 0-2; cola larga hacia 4-6 (~10 %); muy pocos 7+ (3 %).
    rango_nrs = VARIABLES["dolor_percibido_nrs"]["rango_sintetico"]
    nrs_base = rng.exponential(scale=1.0, size=n)
    forzar_alto = rng.random(n) < _PROB_NO_CONCLUYENTE
    nrs_base[forzar_alto] = rng.uniform(6, 9, size=forzar_alto.sum())
    datos["dolor_percibido_nrs"] = np.round(_clip_array(nrs_base, rango_nrs)).astype(int)

    # Hooper Index — Bienestar deportivo (4-28)
    rango_hooper = VARIABLES["hooper_index"]["rango_sintetico"]
    hooper_raw = rng.normal(14.0, 5.0, size=n)
    datos["hooper_index"] = np.round(_clip_array(hooper_raw, rango_hooper)).astype(int)

    return pd.DataFrame(datos, columns=COLUMNAS_CONTEXTO)


# =============================================================================
# INYECCIÓN DE CASOS FRONTERA
# =============================================================================

def _inyectar_casos_frontera(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Para el ~25 % de la muestra, fuerza valores cerca del umbral en 1-3 variables
    clave (cuádriceps, dorsiflexión, Y-Balance CS, valgo SLS). Esto densifica la
    frontera de decisión y mejora el aprendizaje del clasificador.
    """
    n = len(df)
    es_frontera = rng.random(n) < _PROB_FRONTERA
    if not es_frontera.any():
        return df

    df = df.copy()
    indices_frontera = np.where(es_frontera)[0]

    variables_frontera = [
        ("cuadriceps_der",             lambda peso, gen: rng.uniform(2.0, 3.5) * peso),
        ("cuadriceps_izq",             lambda peso, gen: rng.uniform(2.0, 3.5) * peso),
        ("isquiotibiales_der",         lambda peso, gen: rng.uniform(1.4, 2.2) * peso),
        ("dorsiflexion_tobillo_der",   lambda peso, gen: rng.uniform(7.0, 11.0)),
        ("dorsiflexion_tobillo_izq",   lambda peso, gen: rng.uniform(7.0, 11.0)),
        ("y_balance_cs_der",           lambda peso, gen: rng.uniform(82.0, 95.0)),
        ("y_balance_cs_izq",           lambda peso, gen: rng.uniform(82.0, 95.0)),
        ("single_leg_squat_valgo_der", lambda peso, gen: int(rng.choice([1, 2, 2, 3]))),
        ("single_leg_squat_valgo_izq", lambda peso, gen: int(rng.choice([1, 2, 2, 3]))),
        ("historial_lesional",         lambda peso, gen: int(rng.integers(4, 8))),
    ]

    for idx in indices_frontera:
        peso = df.at[idx, "peso_corporal"]
        gen  = df.at[idx, "genero"]
        n_forzar = int(rng.integers(1, 4))
        elegidas = rng.choice(len(variables_frontera), size=n_forzar, replace=False)
        for j in elegidas:
            col, fn = variables_frontera[j]
            valor = fn(peso, gen)
            rango = VARIABLES[col]["rango_sintetico"]
            df.at[idx, col] = float(np.clip(valor, rango[0], rango[1]))

    return df


# =============================================================================
# CÁLCULO DEL UMBRAL EFECTIVO Y EVALUACIÓN POR FILA
# =============================================================================

def _normalizar_fuerza_n_kg(valor_n: float, peso_kg: float) -> float:
    """Convierte una medición en N a N/kg dividiendo por el peso corporal."""
    if peso_kg <= 0:
        return 0.0
    return valor_n / peso_kg


def _evaluar_fila(fila: pd.Series) -> dict:
    """
    Evalúa una fila del DataFrame y devuelve:
      - reglas_alto:  lista de reglas A1-A6 activadas
      - reglas_medio: lista de reglas M1-M5 activadas
      - score_total:  score ponderado (con zonas grises)
      - claras, grises, no_claras: conteo de mediciones por estado
      - no_concluyente: bool si NRS > 5 (regla C3 v2.1)
    """
    reglas_alto:  list[str] = []
    reglas_medio: list[str] = []
    score: float = 0.0
    claras = grises = no_claras = 0

    genero = fila["genero"]
    edad   = fila["edad"]
    nivel  = fila["nivel_actividad"]
    peso   = fila["peso_corporal"]

    # Categoría no concluyente (corrección C3 v2.1)
    no_concluyente = bool(fila.get("dolor_percibido_nrs", 0) > 5)

    def _clasificar_continua(
        valor: float, umbral: float, peso_var: int,
        sentido: str = "menor_es_riesgo", aplica_gris: bool = True,
    ) -> tuple[str, float]:
        """sentido: 'menor_es_riesgo' (debilidad) o 'mayor_es_riesgo' (carga)."""
        if sentido == "menor_es_riesgo":
            limite_gris_inf = umbral * (1 - ZONA_GRIS_MARGEN) if aplica_gris else umbral
            limite_gris_sup = umbral * (1 + ZONA_GRIS_MARGEN) if aplica_gris else umbral
            if valor < limite_gris_inf:
                return "fuera", peso_var * 1.0
            elif aplica_gris and valor < limite_gris_sup:
                return "gris", peso_var * ZONA_GRIS_PUNTUACION_PARCIAL
            else:
                return "segura", 0.0
        else:  # 'mayor_es_riesgo'
            limite_gris_inf = umbral * (1 - ZONA_GRIS_MARGEN) if aplica_gris else umbral
            limite_gris_sup = umbral * (1 + ZONA_GRIS_MARGEN) if aplica_gris else umbral
            if valor > limite_gris_sup:
                return "fuera", peso_var * 1.0
            elif aplica_gris and valor > limite_gris_inf:
                return "gris", peso_var * ZONA_GRIS_PUNTUACION_PARCIAL
            else:
                return "segura", 0.0

    def _registrar(estado: str, contrib: float) -> None:
        nonlocal score, claras, grises, no_claras
        score += contrib
        if estado == "fuera":
            no_claras += 1
        elif estado == "gris":
            grises += 1
        else:
            claras += 1

    # ----- BLOQUE FUERZA -----
    estados_fuerza: dict[str, str] = {}

    for clave_orig, info in VARIABLES_ORIGINALES.items():
        if info["bloque"] != "fuerza":
            continue
        peso_var = info["peso_scoring"]
        aplica_gris = info["aplica_zona_gris"]
        tabla = info.get("umbral_riesgo_base")
        if not isinstance(tabla, dict):
            continue
        grupo = grupo_edad_clave(edad)
        clave_tabla = f"{'M' if genero == 'masculino' else 'F'}_{grupo}"
        umbral_base = tabla.get(clave_tabla)
        if umbral_base is None:
            continue
        factor = FACTORES_ACTIVIDAD.get(nivel, 1.0)
        umbral_efectivo = umbral_base * factor

        if info["bilateral"]:
            for lado in ["der", "izq"]:
                col = f"{clave_orig}_{lado}"
                if col not in fila.index:
                    continue
                valor_bruto = fila[col]
                if tabla.get("_unidad_umbral") == "repeticiones":
                    valor_norm = valor_bruto
                else:
                    valor_norm = _normalizar_fuerza_n_kg(valor_bruto, peso)
                estado, contrib = _clasificar_continua(
                    valor_norm, umbral_efectivo, peso_var,
                    sentido="menor_es_riesgo", aplica_gris=aplica_gris,
                )
                _registrar(estado, contrib)
                estados_fuerza[f"{clave_orig}_{lado}"] = estado

    # ----- BLOQUE MOVILIDAD -----
    estados_movilidad: dict[str, str] = {}

    info_df = VARIABLES_ORIGINALES["dorsiflexion_tobillo"]
    umbral_df = info_df["umbral_riesgo_base"]["umbral"]
    for lado in ["der", "izq"]:
        col = f"dorsiflexion_tobillo_{lado}"
        valor = fila[col]
        estado, contrib = _clasificar_continua(
            valor, umbral_df, info_df["peso_scoring"],
            sentido="menor_es_riesgo", aplica_gris=True,
        )
        _registrar(estado, contrib)
        estados_movilidad[col] = estado

    # Rotación interna cadera (< 30° = riesgo)
    info_ri = VARIABLES_ORIGINALES["rotacion_interna_cadera"]
    umbral_ri = info_ri["umbral_riesgo_base"]["umbral"]
    for lado in ["der", "izq"]:
        valor = fila[f"rotacion_interna_cadera_{lado}"]
        estado, contrib = _clasificar_continua(
            valor, umbral_ri, info_ri["peso_scoring"],
            sentido="menor_es_riesgo", aplica_gris=True,
        )
        _registrar(estado, contrib)

    # Thomas test binario
    info_th = VARIABLES_ORIGINALES["thomas_test"]
    for lado in ["der", "izq"]:
        col = f"thomas_test_{lado}"
        if fila[col] == 1:
            score += info_th["peso_scoring"]
            no_claras += 1
            estados_movilidad[col] = "fuera"
        else:
            claras += 1
            estados_movilidad[col] = "segura"

    # ----- BLOQUE CONTROL -----
    estados_control: dict[str, str] = {}

    info_yb = VARIABLES_ORIGINALES["y_balance_cs"]
    umbral_yb = info_yb["umbral_riesgo_base"]["umbral_M" if genero == "masculino" else "umbral_F"]
    for lado in ["der", "izq"]:
        col = f"y_balance_cs_{lado}"
        valor = fila[col]
        estado, contrib = _clasificar_continua(
            valor, umbral_yb, info_yb["peso_scoring"],
            sentido="menor_es_riesgo", aplica_gris=True,
        )
        _registrar(estado, contrib)
        estados_control[col] = estado

    # Single-leg squat valgo: ≥ 2 = fuera (sin zona gris)
    info_vg = VARIABLES_ORIGINALES["single_leg_squat_valgo"]
    umbral_vg = info_vg["umbral_riesgo_base"]["umbral"]
    for lado in ["der", "izq"]:
        col = f"single_leg_squat_valgo_{lado}"
        if fila[col] >= umbral_vg:
            score += info_vg["peso_scoring"]
            no_claras += 1
            estados_control[col] = "fuera"
        else:
            claras += 1
            estados_control[col] = "segura"

    # Single-leg hop LSI
    info_sh = VARIABLES_ORIGINALES["single_leg_hop"]
    hop_der = fila["single_leg_hop_der"]
    hop_izq = fila["single_leg_hop_izq"]
    if max(hop_der, hop_izq) > 0:
        lsi_hop = min(hop_der, hop_izq) / max(hop_der, hop_izq)
    else:
        lsi_hop = 1.0
    umbral_lsi = info_sh["umbral_riesgo_base"]["lsi_min"]
    umbral_lsi_critico = info_sh["umbral_riesgo_base"]["lsi_critico"]
    if lsi_hop < umbral_lsi:
        score += info_sh["peso_scoring"]
        no_claras += 1
        lado_debil_hop = "izq" if hop_izq < hop_der else "der"
    else:
        claras += 1
        lado_debil_hop = None

    # ----- BLOQUE CONTEXTO -----
    info_hl = VARIABLES_ORIGINALES["historial_lesional"]
    if fila["historial_lesional"] >= info_hl["umbral_riesgo_base"]["umbral_medio"]:
        score += info_hl["peso_scoring"]
        no_claras += 1
        historial_alto = True
    else:
        claras += 1
        historial_alto = False

    historial_muy_alto = fila["historial_lesional"] >= info_hl["umbral_riesgo_base"]["umbral_alto"]

    info_hooper = VARIABLES_ORIGINALES["hooper_index"]
    if fila["hooper_index"] >= info_hooper["umbral_riesgo_base"]["umbral"]:
        score += info_hooper["peso_scoring"]
        no_claras += 1
    else:
        claras += 1

    # ----- REGLAS BOOLEANAS -----
    # A1: cuádriceps + isquios fuera en mismo miembro
    for lado in ["der", "izq"]:
        if (estados_fuerza.get(f"cuadriceps_{lado}") == "fuera"
                and estados_fuerza.get(f"isquiotibiales_{lado}") == "fuera"):
            reglas_alto.append(f"A1_{lado}")
            break

    # A2: glúteo medio + rotadores externos cadera fuera en mismo miembro
    for lado in ["der", "izq"]:
        if (estados_fuerza.get(f"gluteo_medio_{lado}") == "fuera"
                and estados_fuerza.get(f"rotadores_externos_cadera_{lado}") == "fuera"):
            reglas_alto.append(f"A2_{lado}")
            break

    # A3: cuádriceps fuera + historial muy alto (≥ 7)
    cuad_fuera = (estados_fuerza.get("cuadriceps_der") == "fuera"
                  or estados_fuerza.get("cuadriceps_izq") == "fuera")
    if cuad_fuera and historial_muy_alto:
        reglas_alto.append("A3")

    # A4: LSI hop < 0.80 + cuádriceps lado débil fuera
    if lsi_hop < umbral_lsi_critico and lado_debil_hop is not None:
        if estados_fuerza.get(f"cuadriceps_{lado_debil_hop}") == "fuera":
            reglas_alto.append("A4")

    # A5: dorsiflexión fuera bilateral
    if (estados_movilidad.get("dorsiflexion_tobillo_der") == "fuera"
            and estados_movilidad.get("dorsiflexion_tobillo_izq") == "fuera"):
        reglas_alto.append("A5")

    # A6: valgo SLS ≥ 2 + Y-Balance CS bajo umbral en el mismo lado
    for lado in ["der", "izq"]:
        if (estados_control.get(f"single_leg_squat_valgo_{lado}") == "fuera"
                and estados_control.get(f"y_balance_cs_{lado}") == "fuera"):
            reglas_alto.append(f"A6_{lado}")
            break

    # A7: Y-Balance CS por debajo del umbral en AMBOS lados → riesgo alto independiente.
    # Evidencia: Plisky et al. (2006) JOSPT 36(12):911-919 — CS < 94 % (♀) / < 89 % (♂)
    # se asocia a 6.5× riesgo lesión en baloncesto femenino; el déficit bilateral amplifica
    # el riesgo respecto al unilateral al indicar disfunción global del control postural.
    if (estados_control.get("y_balance_cs_der") == "fuera"
            and estados_control.get("y_balance_cs_izq") == "fuera"):
        reglas_alto.append("A7")

    # M2: historial alto (≥ 5) sin llegar a muy alto
    if historial_alto and not historial_muy_alto:
        reglas_medio.append("M2")

    # M3: Hooper ≥ 22 (bienestar deteriorado) + nivel de actividad activo/élite
    estres_alto = fila["hooper_index"] >= VARIABLES_ORIGINALES["hooper_index"]["umbral_riesgo_base"]["umbral"]
    if estres_alto and nivel in {"activo", "elite"}:
        reglas_medio.append("M3")

    # M4: dorsiflexión fuera unilateral + valgo unilateral
    df_unilateral = (
        (estados_movilidad.get("dorsiflexion_tobillo_der") == "fuera")
        != (estados_movilidad.get("dorsiflexion_tobillo_izq") == "fuera")
    )
    valgo_unilateral = (
        (estados_control.get("single_leg_squat_valgo_der") == "fuera")
        or (estados_control.get("single_leg_squat_valgo_izq") == "fuera")
    )
    a6_activa = any(r.startswith("A6") for r in reglas_alto)
    if df_unilateral and valgo_unilateral and not a6_activa:
        reglas_medio.append("M4")

    # M5: 3 o más variables de movilidad fuera de umbral (no cuenta zona gris)
    n_movilidad_fuera = sum(
        1 for est in estados_movilidad.values() if est == "fuera"
    )
    if n_movilidad_fuera >= 3 and not reglas_medio:
        reglas_medio.append("M5")

    # M6: Y-Balance CS por debajo del umbral en cualquier lado → riesgo medio independiente.
    # Evidencia: Plisky et al. (2006) — predictor independiente de lesión; el déficit
    # unilateral refleja asimetría en el control postural dinámico. A7 captura ya el caso
    # bilateral → "alto"; M6 cubre el unilateral que no llega a A7.
    # Nota: si A7 también activa, el max() en generar_label resuelve la categoría final.
    if (estados_control.get("y_balance_cs_der") == "fuera"
            or estados_control.get("y_balance_cs_izq") == "fuera"):
        reglas_medio.append("M6")

    # M7: valgo dinámico severo (grado 3) en cualquier lado → riesgo medio independiente.
    # Evidencia: Hewett et al. (2005) AJSM 33(4):492-501 — valgo en aterrizaje predice
    # LCA (OR 2.5); grado 3 (rodilla medial al borde interno del pie) es el hallazgo
    # clínico más severo de la escala de Crossley (2011) y justifica por sí solo una
    # alerta de riesgo medio sin necesidad de otros factores asociados.
    if (fila["single_leg_squat_valgo_der"] == 3
            or fila["single_leg_squat_valgo_izq"] == 3):
        reglas_medio.append("M7")

    return {
        "reglas_alto": reglas_alto,
        "reglas_medio": reglas_medio,
        "score_total": float(round(score, 2)),
        "claras": claras,
        "grises": grises,
        "no_claras": no_claras,
        "no_concluyente": no_concluyente,
    }


# =============================================================================
# FUNCIÓN DE ETIQUETADO DE RIESGO (v2.2)
# =============================================================================

def generar_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Asigna a cada deportista categoría de riesgo + score de confianza.
    Sigue el modelo lógico-decisional del protocolo v2.2.
    """
    n = len(df)

    riesgo  = np.empty(n, dtype=object)
    score   = np.empty(n, dtype=float)
    conf_pc = np.empty(n, dtype=float)
    conf_ct = np.empty(n, dtype=object)
    reglas  = np.empty(n, dtype=object)

    orden = {"bajo": 0, "medio": 1, "alto": 2}

    for i in range(n):
        ev = _evaluar_fila(df.iloc[i])

        if ev["no_concluyente"]:
            cat = "no_concluyente"
        else:
            if ev["reglas_alto"]:
                cat_reglas = "alto"
            elif ev["reglas_medio"]:
                cat_reglas = "medio"
            else:
                cat_reglas = "bajo"

            if ev["score_total"] >= SCORE_UMBRAL_ALTO:
                cat_score = "alto"
            elif ev["score_total"] >= SCORE_UMBRAL_MEDIO:
                cat_score = "medio"
            else:
                cat_score = "bajo"

            cat = max(cat_reglas, cat_score, key=lambda c: orden[c])

        total_med = ev["claras"] + ev["grises"] + ev["no_claras"]
        pct_claras = 100.0 * ev["claras"] / total_med if total_med > 0 else 0.0

        if pct_claras >= 80:
            conf_categoria = "alta"
        elif pct_claras >= 60:
            conf_categoria = "media"
        else:
            conf_categoria = "baja"

        riesgo[i]  = cat
        score[i]   = ev["score_total"]
        conf_pc[i] = round(pct_claras, 1)
        conf_ct[i] = conf_categoria
        reglas[i]  = ",".join(ev["reglas_alto"] + ev["reglas_medio"]) or "—"

    return pd.DataFrame({
        "riesgo_lesion":       riesgo,
        "score_total":         score,
        "confianza_score":     conf_pc,
        "confianza_categoria": conf_ct,
        "reglas_activadas":    reglas,
    }, index=df.index)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def generar_dataset(n_deportistas: int = 500, semilla: int = 42) -> pd.DataFrame:
    """Genera el dataset sintético completo siguiendo el protocolo v2.2."""
    if n_deportistas < 1:
        raise ValueError(f"n_deportistas debe ser ≥ 1, recibido: {n_deportistas}")

    print(f"Generando dataset sintético v2.2 con {n_deportistas} deportistas (semilla={semilla})...")
    rng = np.random.default_rng(semilla)

    print("  [1/5] Bloque contexto...")
    df_contexto = _generar_bloque_contexto(n_deportistas, rng)
    peso_arr    = df_contexto["peso_corporal"].values
    es_masc     = (df_contexto["genero"].values == "masculino")
    edad_arr    = df_contexto["edad"].values
    actividad_arr = df_contexto["nivel_actividad"].values

    print("  [2/5] Bloque fuerza...")
    df_fuerza = _generar_bloque_fuerza(
        n_deportistas, peso_arr, es_masc, edad_arr, actividad_arr, rng
    )

    print("  [3/5] Bloque movilidad...")
    df_movilidad = _generar_bloque_movilidad(n_deportistas, rng)

    print("  [4/5] Bloque control...")
    df_control = _generar_bloque_control(n_deportistas, rng)

    df = pd.concat([df_fuerza, df_movilidad, df_control, df_contexto], axis=1)
    df = df[list(VARIABLES.keys())]

    print("  [5/5] Inyectando casos frontera...")
    df = _inyectar_casos_frontera(df, rng)

    print("  Aplicando reglas v2.2 y calculando score de confianza...")
    df_etiquetas = generar_label(df)
    df = pd.concat([df, df_etiquetas], axis=1)

    cols_continuas = [c for c in VARIABLES if VARIABLES[c]["tipo"] == "continua"]
    df[cols_continuas] = df[cols_continuas].round(1)

    distribucion = df["riesgo_lesion"].value_counts(normalize=True).mul(100).round(1)
    print("\nDistribución de riesgo:")
    for clase in ["bajo", "medio", "alto", "no_concluyente"]:
        pct = distribucion.get(clase, 0.0)
        print(f"  {clase:16s}: {pct:5.1f} %")

    distribucion_conf = df["confianza_categoria"].value_counts(normalize=True).mul(100).round(1)
    print("\nDistribución de confianza:")
    for clase in ["alta", "media", "baja"]:
        pct = distribucion_conf.get(clase, 0.0)
        print(f"  {clase:16s}: {pct:5.1f} %")

    print(f"\nDataset generado: {df.shape[0]} filas × {df.shape[1]} columnas.\n")
    return df


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    ruta_salida = Path("datos") / "sinteticos" / "dataset_sintetico.csv"

    print("=" * 60)
    print("  IntApp v2.2 — Generador de datos sintéticos")
    print("=" * 60)

    df_sintetico = generar_dataset(n_deportistas=500, semilla=42)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_sintetico.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"Dataset guardado en: {ruta_salida.resolve()}")
    print(f"Columnas: {df_sintetico.shape[1]} | Filas: {df_sintetico.shape[0]}")
    print("\nPrimeras 3 filas (columnas finales de etiquetado):")
    print(df_sintetico[[
        "riesgo_lesion", "score_total",
        "confianza_score", "confianza_categoria", "reglas_activadas",
    ]].head(3).to_string())
