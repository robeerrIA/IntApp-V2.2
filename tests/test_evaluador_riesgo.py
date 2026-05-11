"""Tests unitarios para src/evaluador_riesgo.py.

El modelo y el scaler reales NO se cargan desde disco — se usan mocks o
scalers generados sobre datos sintéticos mínimos para aislar las funciones.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.evaluador_riesgo import preparar_deportista, predecir_riesgo
from src.generador_datos import generar_dataset
from src.preprocesador import preprocesar


# ── helpers ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def scaler():
    """Scaler ajustado sobre 20 muestras sintéticas (reutilizado en todos los tests)."""
    df = generar_dataset(n_deportistas=20, semilla=7)
    _, sc = preprocesar(df)
    return sc


@pytest.fixture(scope="module")
def datos_deportista():
    """Diccionario con un deportista completo generado sintéticamente."""
    df = generar_dataset(n_deportistas=1, semilla=0)
    return df.iloc[0].to_dict()


def _make_modelo(prediccion: str = "bajo") -> MagicMock:
    """Modelo mock que siempre predice la clase indicada con predict_proba [0.8, 0.1, 0.1]."""
    m = MagicMock()
    m.classes_ = np.array(["alto", "bajo", "medio"])
    m.predict.return_value = np.array([prediccion])
    if prediccion == "alto":
        m.predict_proba.return_value = np.array([[0.80, 0.10, 0.10]])
    elif prediccion == "medio":
        m.predict_proba.return_value = np.array([[0.10, 0.10, 0.80]])
    else:
        m.predict_proba.return_value = np.array([[0.10, 0.80, 0.10]])
    return m


# ── preparar_deportista ───────────────────────────────────────────────────────

def test_preparar_devuelve_una_fila(scaler, datos_deportista):
    """preparar_deportista debe devolver exactamente 1 fila."""
    df_out = preparar_deportista(datos_deportista, scaler)
    assert len(df_out) == 1


def test_preparar_no_contiene_etiqueta(scaler, datos_deportista):
    """La columna 'riesgo_lesion' no debe estar en el DataFrame de salida."""
    df_out = preparar_deportista(datos_deportista, scaler)
    assert "riesgo_lesion" not in df_out.columns


def test_preparar_sin_nans(scaler, datos_deportista):
    """El DataFrame resultante no debe tener valores NaN."""
    df_out = preparar_deportista(datos_deportista, scaler)
    assert df_out.isnull().sum().sum() == 0


def test_preparar_dict_vacio_lanza_error(scaler):
    """Un dict vacío debe lanzar ValueError."""
    with pytest.raises(ValueError):
        preparar_deportista({}, scaler)


def test_preparar_claves_desconocidas_no_rompen(scaler):
    """Claves no reconocidas deben ignorarse sin lanzar excepción."""
    datos_con_extras = {"campo_inventado": 99, "otro_campo": "xyz"}
    # No debe lanzar — simplemente rellenará todo con NaN y devolverá 0 tras fillna
    df_out = preparar_deportista(datos_con_extras, scaler)
    assert len(df_out) == 1


# ── predecir_riesgo ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("clase", ["bajo", "medio", "alto"])
def test_prediccion_clase_valida(scaler, datos_deportista, clase):
    """La predicción debe ser exactamente la clase indicada por el mock."""
    modelo = _make_modelo(clase)
    df_proc = preparar_deportista(datos_deportista, scaler)
    resultado = predecir_riesgo(modelo, df_proc)
    assert resultado["prediccion"] == clase


def test_probabilidades_suman_uno(scaler, datos_deportista):
    """Las probabilidades de las tres clases deben sumar 1 (±tolerancia de redondeo)."""
    modelo = _make_modelo("bajo")
    df_proc = preparar_deportista(datos_deportista, scaler)
    resultado = predecir_riesgo(modelo, df_proc)
    total = sum(resultado["probabilidades"].values())
    assert total == pytest.approx(1.0, abs=1e-3)


def test_probabilidades_contiene_tres_clases(scaler, datos_deportista):
    """El dict de probabilidades debe tener las tres clases de riesgo."""
    modelo = _make_modelo("medio")
    df_proc = preparar_deportista(datos_deportista, scaler)
    resultado = predecir_riesgo(modelo, df_proc)
    assert set(resultado["probabilidades"].keys()) == {"bajo", "medio", "alto"}


def test_color_semaforo_formato_hex(scaler, datos_deportista):
    """color_semaforo debe empezar por '#'."""
    modelo = _make_modelo("alto")
    df_proc = preparar_deportista(datos_deportista, scaler)
    resultado = predecir_riesgo(modelo, df_proc)
    assert resultado["color_semaforo"].startswith("#")


@pytest.mark.parametrize("clase,color", [
    ("bajo",  "#28a745"),
    ("medio", "#ffc107"),
    ("alto",  "#dc3545"),
])
def test_color_semaforo_por_clase(scaler, datos_deportista, clase, color):
    """Cada clase de riesgo debe tener su color de semáforo correcto."""
    modelo = _make_modelo(clase)
    df_proc = preparar_deportista(datos_deportista, scaler)
    resultado = predecir_riesgo(modelo, df_proc)
    assert resultado["color_semaforo"] == color


def test_modelo_sin_predict_proba_lanza_error(scaler, datos_deportista):
    """Un modelo sin predict_proba debe lanzar ValueError con mensaje claro."""
    modelo_sin_proba = MagicMock(spec=["predict"])  # sin predict_proba
    df_proc = preparar_deportista(datos_deportista, scaler)
    with pytest.raises(ValueError, match="predict_proba"):
        predecir_riesgo(modelo_sin_proba, df_proc)
