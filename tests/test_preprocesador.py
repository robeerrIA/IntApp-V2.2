"""Tests unitarios para src/preprocesador.py."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.preprocesador import (
    calcular_ratios,
    calcular_asimetrias,
    codificar_categoricas,
    preprocesar,
)
from src.generador_datos import generar_dataset


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def df_crudo():
    """Dataset crudo pequeño para pruebas (semilla fija para reproducibilidad)."""
    return generar_dataset(n_deportistas=40, semilla=0)


# ── calcular_ratios ───────────────────────────────────────────────────────────

def test_ratios_hq_formula(df_crudo):
    """ratio_hq_der == isquiotibiales_der / cuadriceps_der."""
    df = calcular_ratios(df_crudo)
    for lado in ("der", "izq"):
        esperado = (
            df_crudo[f"isquiotibiales_{lado}"]
            / df_crudo[f"cuadriceps_{lado}"].replace(0, np.nan)
        )
        pd.testing.assert_series_equal(
            df[f"ratio_hq_{lado}"].reset_index(drop=True),
            esperado.reset_index(drop=True),
            check_names=False,
        )


def test_ratios_add_abd_formula(df_crudo):
    """ratio_add_abd_der == aductores_cadera_der / gluteo_medio_der."""
    df = calcular_ratios(df_crudo)
    for lado in ("der", "izq"):
        esperado = (
            df_crudo[f"aductores_cadera_{lado}"]
            / df_crudo[f"gluteo_medio_{lado}"].replace(0, np.nan)
        )
        pd.testing.assert_series_equal(
            df[f"ratio_add_abd_{lado}"].reset_index(drop=True),
            esperado.reset_index(drop=True),
            check_names=False,
        )


def test_ratios_crea_columnas_esperadas(df_crudo):
    """Verifica que existen las 4 columnas de ratio principales."""
    df = calcular_ratios(df_crudo)
    for col in ("ratio_hq_der", "ratio_hq_izq", "ratio_add_abd_der", "ratio_add_abd_izq"):
        assert col in df.columns, f"Falta columna: {col}"


def test_ratios_no_modifica_entrada(df_crudo):
    """calcular_ratios no debe modificar el DataFrame original (copia defensiva)."""
    cols_antes = list(df_crudo.columns)
    calcular_ratios(df_crudo)
    assert list(df_crudo.columns) == cols_antes


# ── calcular_asimetrias ───────────────────────────────────────────────────────

def test_asimetria_simetria_perfecta():
    """Con lados iguales, la asimetría debe ser 0."""
    df_mini = pd.DataFrame({"cuadriceps_der": [200.0], "cuadriceps_izq": [200.0]})
    df_out = calcular_asimetrias(df_mini)
    assert "asimetria_cuadriceps" in df_out.columns
    assert df_out["asimetria_cuadriceps"].iloc[0] == pytest.approx(0.0)


def test_asimetria_valor_conocido():
    """|300 - 200| / max(300, 200) × 100 = 33.33 %."""
    df_mini = pd.DataFrame({"cuadriceps_der": [300.0], "cuadriceps_izq": [200.0]})
    df_out = calcular_asimetrias(df_mini)
    assert "asimetria_cuadriceps" in df_out.columns
    assert df_out["asimetria_cuadriceps"].iloc[0] == pytest.approx(100 / 3, rel=1e-3)


def test_asimetria_bilateral_cero_no_nan():
    """Cuando ambos lados son 0 (0/0), la asimetría debe ser 0.0, nunca NaN."""
    df_mini = pd.DataFrame({"thomas_test_der": [0], "thomas_test_izq": [0]})
    df_out = calcular_asimetrias(df_mini)
    assert "asimetria_thomas_test" in df_out.columns
    assert not df_out["asimetria_thomas_test"].isna().any()
    assert df_out["asimetria_thomas_test"].iloc[0] == pytest.approx(0.0)


def test_asimetria_no_modifica_entrada(df_crudo):
    """calcular_asimetrias no debe modificar el DataFrame original."""
    df_con_ratios = calcular_ratios(df_crudo)
    cols_antes = list(df_con_ratios.columns)
    calcular_asimetrias(df_con_ratios)
    assert list(df_con_ratios.columns) == cols_antes


# ── codificar_categoricas ─────────────────────────────────────────────────────

def test_codificar_genero_binario():
    """masculino → 0, femenino → 1."""
    df = pd.DataFrame({"genero": ["masculino", "femenino", "masculino"]})
    df_out = codificar_categoricas(df)
    assert list(df_out["genero"]) == [0, 1, 0]


def test_codificar_nivel_actividad_ordinal():
    """sedentario=0, recreacional=1, activo=2, elite=3."""
    df = pd.DataFrame(
        {"nivel_actividad": ["sedentario", "recreacional", "activo", "elite"]}
    )
    df_out = codificar_categoricas(df)
    assert list(df_out["nivel_actividad"]) == [0, 1, 2, 3]



def test_codificar_valor_desconocido_produce_nan():
    """Un género no reconocido produce NaN, no una excepción."""
    df = pd.DataFrame({"genero": ["desconocido"]})
    df_out = codificar_categoricas(df)
    assert df_out["genero"].isna().iloc[0]


# ── preprocesar (integración) ─────────────────────────────────────────────────

def test_preprocesar_shape(df_crudo):
    """El pipeline produce 57 columnas (56 features + riesgo_lesion) — v2.3 + 12 ratio_ref."""
    df_out, _ = preprocesar(df_crudo)
    assert df_out.shape[1] == 57


def test_preprocesar_sin_nans(df_crudo):
    """El DataFrame de salida no debe contener NaN."""
    df_out, _ = preprocesar(df_crudo)
    assert df_out.isnull().sum().sum() == 0


def test_preprocesar_elimina_columnas_auxiliares(df_crudo):
    """Las columnas auxiliares del generador no deben aparecer en el output."""
    df_out, _ = preprocesar(df_crudo)
    for col in ("score_total", "confianza_score", "confianza_categoria", "reglas_activadas"):
        assert col not in df_out.columns, f"Columna auxiliar no eliminada: {col}"


def test_preprocesar_devuelve_scaler(df_crudo):
    """El segundo elemento de la tupla debe ser un StandardScaler ajustado."""
    from sklearn.preprocessing import StandardScaler
    _, scaler = preprocesar(df_crudo)
    assert isinstance(scaler, StandardScaler)


def test_preprocesar_inferencia_reproducible(df_crudo):
    """Pasar el mismo scaler en modo inferencia produce el mismo output."""
    _, scaler = preprocesar(df_crudo)
    df_run1, _ = preprocesar(df_crudo, scaler=scaler)
    df_run2, _ = preprocesar(df_crudo, scaler=scaler)
    pd.testing.assert_frame_equal(df_run1, df_run2)
