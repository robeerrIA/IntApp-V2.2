"""
streamlit_app.py — Aplicación web IntApp para evaluación individual de riesgo de lesión.

Uso:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.variables import VARIABLES, VARIABLES_ORIGINALES

# CalibradorUmbralAlto se serializa como __main__.CalibradorUmbralAlto cuando
# src/modelo.py se ejecuta como script. Este import la registra en __main__
# (que es este archivo cuando Streamlit lo ejecuta) para que pickle la encuentre.
try:
    from src.modelo import CalibradorUmbralAlto  # noqa: F401
except ImportError:
    pass

st.set_page_config(
    page_title="IntApp — Riesgo de Lesión",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Sidebar clínica ── */
[data-testid="stSidebar"] {
    background: #0a0f1a !important;
    border-right: 1px solid #1e3a5f;
}
[data-testid="stSidebar"] * { color: #94c5d8 !important; }
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 { color: #38bdf8 !important; font-weight: 600 !important; }
[data-testid="stSidebar"] hr { border-color: #1e3a5f; }
[data-testid="stSidebar"] code {
    background: #0d1f33 !important; color: #38bdf8 !important;
}

/* ── Layout ── */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* ── Cabecera de sección ── */
.section-header {
    font-size: 1.05rem; font-weight: 700; color: #e2e8f0;
    border-left: 4px solid #38bdf8; padding-left: 0.65rem;
    margin-bottom: 0.9rem; margin-top: 0.2rem;
    letter-spacing: 0.01em;
}

/* ── Badges de contexto ── */
.badge {
    display: inline-block; border-radius: 6px;
    padding: 0.2rem 0.75rem; font-size: 0.8rem; font-weight: 600;
    margin-right: 0.4rem; margin-bottom: 0.35rem;
    border: 1px solid transparent;
}
.badge-green  { background: #0d2b1e; color: #34d399; border-color: #065f46; }
.badge-yellow { background: #2b1e05; color: #fbbf24; border-color: #78350f; }
.badge-red    { background: #2b0d0d; color: #f87171; border-color: #7f1d1d; }

/* ── Semáforo ── */
.sema-box {
    border-radius: 10px; padding: 1.5rem 2rem; text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.08);
}
.sema-label {
    font-size: 0.78rem; font-weight: 600; color: rgba(255,255,255,0.75);
    letter-spacing: 0.12em; text-transform: uppercase;
}
.sema-nivel {
    font-size: 1.8rem; font-weight: 800; color: #fff;
    letter-spacing: 0.04em; margin-top: 0.4rem;
}
.sema-bajo  { background: linear-gradient(135deg, #064e3b, #065f46); }
.sema-medio { background: linear-gradient(135deg, #451a03, #78350f); }
.sema-alto  { background: linear-gradient(135deg, #450a0a, #7f1d1d); }

/* ── Tarjetas de probabilidad ── */
.prob-card {
    border-radius: 8px; padding: 0.9rem 1rem; text-align: center;
    background: #161d2a;
}
.prob-label {
    font-size: 0.78rem; font-weight: 600; color: #64748b;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.25rem;
}
.prob-value { font-size: 1.7rem; font-weight: 800; }

/* ── Banderas fuera de rango ── */
.flag-item {
    background: #1a0a0a; border-left: 3px solid #ef4444;
    border-radius: 0 6px 6px 0; padding: 0.4rem 0.8rem;
    margin-bottom: 0.35rem; font-size: 0.86rem; color: #fca5a5;
}

/* ── Títulos bilaterales (dentro de tabs) ── */
.bloque-titulo {
    font-size: 0.93rem; font-weight: 700; color: #e2e8f0;
    border-left: 3px solid #38bdf8; padding-left: 0.5rem;
    margin-bottom: 0.5rem; margin-top: 0.5rem;
}

/* ── Aviso modelo no encontrado ── */
.aviso-modelo {
    background: #1a150a; border: 1px solid #78350f;
    border-radius: 8px; padding: 1.2rem; color: #fbbf24;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Carga del modelo (cacheada)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Cargando modelo...")
def _cargar_pipeline_cached():
    try:
        from src.evaluador_riesgo import cargar_pipeline
        return cargar_pipeline()
    except FileNotFoundError:
        return None
    except Exception as exc:
        st.error(f"Error inesperado al cargar el modelo: {exc}")
        return None


# ---------------------------------------------------------------------------
# Constantes de presentación
# ---------------------------------------------------------------------------

_ETIQUETAS_VALGO: dict[int, str] = {
    0: "0 — Sin valgo", 1: "1 — Leve", 2: "2 — Moderado", 3: "3 — Severo",
}
_ETIQUETAS_GENERO: dict[str, str] = {"masculino": "Masculino", "femenino": "Femenino"}

_COLORES_PROB: dict[str, str] = {"bajo": "#28a745", "medio": "#e6a817", "alto": "#dc3545"}
_NOMBRES_CLASE_ES: dict[str, str] = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}
_NOMBRES_NIVEL: dict[str, str] = {
    "bajo": "RIESGO BAJO", "medio": "RIESGO MEDIO", "alto": "RIESGO ALTO",
}
_CLASES_CSS_SEMA: dict[str, str] = {
    "bajo": "sema-bajo", "medio": "sema-medio", "alto": "sema-alto",
}

# Orden explícito de las variables contextuales
_KEYS_NRS       = ["dolor_percibido_nrs"]
_KEYS_DEMOGRAFIA = ["edad", "genero", "peso_corporal"]
_KEYS_ACTIVIDAD  = ["nivel_actividad"]
_KEYS_CARGA      = ["historial_lesional", "hooper_index"]


# ---------------------------------------------------------------------------
# Protocolo de medición (popover)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Widget genérico
# ---------------------------------------------------------------------------

def _widget_variable(key: str, info: dict, lado: str | None = None):
    tipo   = info.get("tipo", "continua")
    nombre = info["nombre_display"]
    unidad = info.get("unidad", "")
    rango  = info.get("rango_sintetico") or info.get("rango_normal", (0, 100))
    rango_normal = info.get("rango_normal") or rango

    if lado:
        etiqueta = f"{'Der.' if lado == 'derecha' else 'Izq.'} ({unidad})"
    else:
        etiqueta = f"{nombre} ({unidad})" if unidad else nombre

    if tipo == "continua":
        minv, maxv = float(rango[0]), float(rango[1])
        paso = 0.5 if (maxv - minv) <= 50 else 1.0
        default = round((float(rango_normal[0]) + float(rango_normal[1])) / 2, 1)
        default = max(minv, min(maxv, default))
        return st.slider(
            etiqueta, min_value=minv, max_value=maxv,
            value=default, step=paso,
            key=f"slider_{key}",
        )

    elif tipo == "ordinal":
        categorias = info.get("categorias", [])
        if key in ("single_leg_squat_valgo_der", "single_leg_squat_valgo_izq"):
            opciones = [_ETIQUETAS_VALGO[c] for c in categorias]
            sel = st.select_slider(etiqueta, options=opciones, value=opciones[0], key=f"slider_{key}")
            return int(sel[0])
        else:
            minv, maxv = int(rango[0]), int(rango[1])
            default = (int(rango_normal[0]) + int(rango_normal[1])) // 2
            default = max(minv, min(maxv, default))
            return st.slider(
                etiqueta, min_value=minv, max_value=maxv,
                value=default, step=1,
                key=f"slider_{key}",
            )

    elif tipo == "categorica":
        categorias = info.get("categorias", [])
        if key == "genero":
            opciones_display = [_ETIQUETAS_GENERO.get(c, c) for c in categorias]
            idx = st.selectbox(
                etiqueta, options=range(len(categorias)),
                format_func=lambda i: opciones_display[i],
                key=f"select_{key}",
            )
            return categorias[idx]
        if key == "nivel_actividad" and "recreacional" in categorias:
            return st.selectbox(etiqueta, options=categorias,
                                index=categorias.index("recreacional"),
                                key=f"select_{key}")
        return st.selectbox(etiqueta, options=categorias, key=f"select_{key}")

    elif tipo == "binaria":
        return st.selectbox(
            etiqueta, options=[0, 1],
            format_func=lambda x: "Negativo (0)" if x == 0 else "Positivo (1)",
            key=f"select_{key}",
        )

    return st.number_input(etiqueta, value=0.0, key=f"num_{key}")


# ---------------------------------------------------------------------------
# Sección 1 — Variables contextuales (al inicio del formulario)
# ---------------------------------------------------------------------------

def _nrs_badge_html(nrs: int) -> str:
    if nrs == 0:
        return f'<span class="badge badge-green">🟢 Sin dolor — NRS {nrs}</span>'
    elif nrs <= 3:
        return f'<span class="badge badge-green">🟢 Dolor leve — NRS {nrs}</span>'
    elif nrs <= 5:
        return f'<span class="badge badge-yellow">🟡 Dolor moderado — NRS {nrs} (se evaluará con el modelo)</span>'
    elif nrs <= 7:
        return f'<span class="badge badge-red">🔴 Dolor intenso — NRS {nrs} (caso no concluyente)</span>'
    else:
        return f'<span class="badge badge-red">🔴 Dolor severo — NRS {nrs} (valoración urgente presencial)</span>'


def _historial_badge_html(historial: int) -> str:
    if historial == 0:
        return '<span class="badge badge-green">Sin lesiones previas 🟢</span>'
    elif historial == 1:
        return '<span class="badge badge-yellow">1 lesión previa 🟡</span>'
    return f'<span class="badge badge-red">{historial}+ lesiones previas 🔴</span>'


def _renderizar_contexto() -> dict:
    """Renderiza Section 1: variables contextuales. Devuelve dict de valores."""
    vars_ctx = {k: v for k, v in VARIABLES.items() if v.get("bloque") == "contexto"}
    valores: dict = {}

    st.markdown('<div class="section-header">📋 Perfil del deportista</div>', unsafe_allow_html=True)

    # ── NRS — destacado en la parte superior ────────────────────────────── #
    nrs_key = _KEYS_NRS[0]
    if nrs_key in vars_ctx:
        info = vars_ctx[nrs_key]
        rango = info.get("rango_sintetico") or info.get("rango_normal", (0, 10))
        nrs_val = st.slider(
            "🔴  Dolor percibido — Escala NRS  (0 = sin dolor · 10 = máximo dolor)",
            min_value=int(rango[0]), max_value=int(rango[1]),
            value=0, step=1, key=f"slider_{nrs_key}",
        )
        valores[nrs_key] = nrs_val
        st.markdown(_nrs_badge_html(nrs_val), unsafe_allow_html=True)
    st.markdown("")

    # ── Demografía ──────────────────────────────────────────────────────── #
    st.markdown("**Datos demográficos**")
    demograficas = [k for k in _KEYS_DEMOGRAFIA if k in vars_ctx]
    if demograficas:
        cols = st.columns(len(demograficas))
        for col, k in zip(cols, demograficas):
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])

    # ── Nivel y perfil de actividad ──────────────────────────────────────── #
    st.markdown("**Nivel de actividad deportiva**")
    actividad_keys = [k for k in _KEYS_ACTIVIDAD if k in vars_ctx]
    if actividad_keys:
        cols = st.columns(len(actividad_keys))
        for col, k in zip(cols, actividad_keys):
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])

    # ── Factores de carga ────────────────────────────────────────────────── #
    st.markdown("**Factores de carga y riesgo contextual**")
    carga_keys = [k for k in _KEYS_CARGA if k in vars_ctx]
    if carga_keys:
        cols = st.columns(len(carga_keys))
        for col, k in zip(cols, carga_keys):
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])

    # Resto de variables contextuales no capturadas explícitamente
    rendered_keys = set(_KEYS_NRS) | set(_KEYS_DEMOGRAFIA) | set(_KEYS_ACTIVIDAD) | set(_KEYS_CARGA)
    otras = [k for k in vars_ctx if k not in rendered_keys]
    for k in otras:
        valores[k] = _widget_variable(k, vars_ctx[k])

    # ── Resumen de badges ────────────────────────────────────────────────── #
    st.markdown("")
    nrs_v   = int(valores.get(nrs_key, 0)) if nrs_key in vars_ctx else 0
    hist_v  = int(valores.get("historial_lesional", 0))
    st.markdown(
        "<div style='margin-top:0.3rem;'>"
        + _nrs_badge_html(nrs_v)
        + _historial_badge_html(hist_v)
        + "</div>",
        unsafe_allow_html=True,
    )

    return valores


# ---------------------------------------------------------------------------
# Sección 2 — Evaluación física con pestañas
# ---------------------------------------------------------------------------

def _renderizar_bloque_en_tab(nombre_bloque: str) -> dict:
    """Renderiza las variables de un bloque dentro de un tab activo."""
    valores: dict = {}
    vars_originales_bloque = {
        k: v for k, v in VARIABLES_ORIGINALES.items() if v.get("bloque") == nombre_bloque
    }
    variables_bloque = {k: v for k, v in VARIABLES.items() if v.get("bloque") == nombre_bloque}

    for clave_orig, info_orig in vars_originales_bloque.items():
        protocolo = info_orig.get("protocolo")
        if info_orig.get("bilateral", False):
            col_titulo, col_proto = st.columns([8, 2])
            with col_titulo:
                st.markdown(
                    f"<div class='bloque-titulo'>{info_orig['nombre_display']}</div>",
                    unsafe_allow_html=True,
                )
            if protocolo:
                with col_proto:
                    with st.popover("ℹ️ Protocolo", use_container_width=True):
                        st.markdown(protocolo)
            col_der, col_izq = st.columns(2)
            clave_der, clave_izq = f"{clave_orig}_der", f"{clave_orig}_izq"
            with col_der:
                st.caption("Lado derecho")
                valores[clave_der] = _widget_variable(
                    clave_der, variables_bloque.get(clave_der, info_orig),
                    lado="derecha",
                )
            with col_izq:
                st.caption("Lado izquierdo")
                valores[clave_izq] = _widget_variable(
                    clave_izq, variables_bloque.get(clave_izq, info_orig),
                    lado="izquierda",
                )
        else:
            clave = clave_orig
            info  = variables_bloque.get(clave, info_orig)
            col_widget, col_proto = st.columns([8, 2])
            with col_widget:
                valores[clave] = _widget_variable(clave, info)
            if protocolo:
                with col_proto:
                    with st.popover("ℹ️ Protocolo", use_container_width=True):
                        st.markdown(protocolo)

    return valores


def _renderizar_evaluacion_fisica() -> dict:
    """Renderiza Section 2: evaluación física con tres pestañas."""
    st.markdown(
        '<div class="section-header">🔬 Evaluación física</div>',
        unsafe_allow_html=True,
    )
    tab_fuerza, tab_movilidad, tab_control = st.tabs(
        ["💪  Fuerza muscular", "🔄  Movilidad articular", "⚖️  Control neuromuscular"]
    )
    valores: dict = {}
    with tab_fuerza:
        valores.update(_renderizar_bloque_en_tab("fuerza"))
    with tab_movilidad:
        valores.update(_renderizar_bloque_en_tab("movilidad"))
    with tab_control:
        valores.update(_renderizar_bloque_en_tab("control"))
    return valores


# ---------------------------------------------------------------------------
# Helpers de resultados
# ---------------------------------------------------------------------------

def _mostrar_semaforo(prediccion: str) -> None:
    clase_css   = _CLASES_CSS_SEMA.get(prediccion, "sema-medio")
    nivel_texto = _NOMBRES_NIVEL.get(prediccion, prediccion.upper())
    st.markdown(
        f'<div class="sema-box {clase_css}">'
        f'<div class="sema-label">Nivel de riesgo</div>'
        f'<div class="sema-nivel">{nivel_texto}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _mostrar_probabilidades(probabilidades: dict[str, float]) -> None:
    st.markdown("**Probabilidades por clase**")
    cols = st.columns(3)
    for col, clase in zip(cols, ["bajo", "medio", "alto"]):
        prob   = probabilidades.get(clase, 0.0)
        color  = _COLORES_PROB[clase]
        nombre = _NOMBRES_CLASE_ES[clase]
        with col:
            st.markdown(
                f'<div class="prob-card" style="border:2px solid {color};">'
                f'<div class="prob-label">Riesgo {nombre}</div>'
                f'<div class="prob-value" style="color:{color};">{prob:.1%}</div>'
                f'<div style="background:rgba(255,255,255,0.12);border-radius:4px;height:6px;margin-top:0.6rem;">'
                f'<div style="background:{color};border-radius:4px;height:6px;width:{prob*100:.1f}%;"></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _nombre_display_variable(clave: str) -> str:
    if clave in VARIABLES:
        return VARIABLES[clave]["nombre_display"]
    return clave.replace("_", " ").title()


def _mostrar_importancia_variables(importancias: list[tuple[str, float]]) -> None:
    import pandas as pd
    if not importancias:
        st.info("Importancia de variables no disponible para este modelo.")
        return
    st.markdown("**Importancia global de variables del modelo**")
    st.caption("Contribución media de cada variable al aprendizaje del modelo (no específica de este deportista).")
    max_imp = float(importancias[0][1]) if importancias[0][1] > 0 else 1.0
    filas = [
        {
            "Variable": _nombre_display_variable(n) or str(n).replace("_", " ").title(),
            "Importancia": float(max(0.0, imp)),
        }
        for n, imp in importancias
    ]
    df_imp = pd.DataFrame(filas)
    st.dataframe(
        df_imp,
        column_config={
            "Variable": st.column_config.TextColumn("Variable"),
            "Importancia": st.column_config.ProgressColumn(
                "Importancia",
                min_value=0.0,
                max_value=max_imp,
                format="%.3f",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


def _mostrar_banderas_fuera_rango(valores_deportista: dict) -> list[str]:
    """Muestra banderas de variables fuera de rango. Devuelve la lista para el informe."""
    flags: list[str] = []
    for clave, valor in valores_deportista.items():
        if clave not in VARIABLES:
            continue
        info        = VARIABLES[clave]
        rango_normal = info.get("rango_normal")
        if rango_normal is None:
            continue
        try:
            val_num = float(valor)
        except (TypeError, ValueError):
            continue
        minr, maxr = rango_normal
        if not (minr <= val_num <= maxr):
            nombre = info["nombre_display"]
            unidad = info.get("unidad", "")
            flags.append(
                f"{nombre}: {val_num} {unidad} (ref: {minr}–{maxr} {unidad})".strip()
            )

    if flags:
        st.markdown("**Variables fuera de rango de referencia**")
        for f in flags:
            st.markdown(f'<div class="flag-item">⚠️ {f}</div>', unsafe_allow_html=True)
    else:
        st.success("Todos los valores dentro de los rangos de referencia.", icon="✅")

    return flags


def _generar_informe_pdf(
    valores_deportista: dict,
    prediccion: str,
    probabilidades: dict[str, float],
    flags: list[str],
) -> bytes:
    from fpdf import FPDF

    LOGO_PATH = Path(__file__).resolve().parent.parent / "docs" / "ue-logo.png"

    # Fuentes TTF con soporte Unicode completo (español + caracteres especiales)
    _FONT_CANDIDATES = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    _FONT_REGULAR = next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)
    _FONT_BOLD    = next(
        (p for p in [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Unicode.ttf",
        ] if Path(p).exists()),
        _FONT_REGULAR,
    )

    COLOR_NIVEL = {
        "bajo":  (6,  78, 59),
        "medio": (120, 53,  15),
        "alto":  (127, 29, 29),
    }
    COLOR_TEXTO_NIVEL = {
        "bajo":  (209, 250, 229),
        "medio": (254, 243, 199),
        "alto":  (254, 226, 226),
    }

    pdf = FPDF()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=20)

    # Registrar fuente Unicode
    if _FONT_REGULAR:
        pdf.add_font("Arial", "", _FONT_REGULAR)
        pdf.add_font("Arial", "B", _FONT_BOLD if _FONT_BOLD else _FONT_REGULAR)
        _FONT = "Arial"
    else:
        _FONT = "Helvetica"  # fallback sin Unicode

    pdf.add_page()

    # ── Encabezado ────────────────────────────────────────────────────────── #
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=18, y=14, h=16)
    pdf.set_font(_FONT, "B", 16)
    pdf.set_text_color(15, 23, 42)
    pdf.set_xy(42, 14)
    pdf.cell(0, 8, "IntApp v2 — Informe de Evaluacion de Riesgo")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.set_xy(42, 23)
    pdf.cell(
        0, 5,
        f"Universidad Europea  ·  Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}  ·  v2.2",
    )
    pdf.ln(18)
    pdf.set_draw_color(56, 189, 248)
    pdf.set_line_width(0.5)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(6)

    # ── Resultado principal ────────────────────────────────────────────────── #
    nivel_texto = _NOMBRES_NIVEL.get(prediccion, prediccion.upper())
    bg = COLOR_NIVEL.get(prediccion, (30, 41, 59))
    fg = COLOR_TEXTO_NIVEL.get(prediccion, (226, 232, 240))
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font(_FONT, "B", 13)
    pdf.cell(0, 12, f"  {nivel_texto}", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(4)

    # ── Probabilidades ────────────────────────────────────────────────────── #
    pdf.set_text_color(15, 23, 42)
    pdf.set_font(_FONT, "B", 10)
    pdf.cell(0, 7, "Probabilidades por clase", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", 9)
    col_w = 57
    for clase, etiqueta in [("bajo", "Riesgo Bajo"), ("medio", "Riesgo Medio"), ("alto", "Riesgo Alto")]:
        prob = probabilidades.get(clase, 0.0)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(col_w, 6, f"{etiqueta}: {prob:.1%}")
    pdf.ln(10)

    # ── Variables fuera de rango ───────────────────────────────────────────── #
    if flags:
        pdf.set_font(_FONT, "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "Variables fuera de rango de referencia", new_x="LMARGIN", new_y="NEXT")
        pdf.set_fill_color(255, 240, 240)
        pdf.set_text_color(153, 27, 27)
        pdf.set_font(_FONT, "", 8.5)
        for f in flags:
            pdf.cell(0, 6, f"  !  {f}", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(0.5)
        pdf.set_text_color(15, 23, 42)
        pdf.ln(4)

    # ── Datos del deportista ───────────────────────────────────────────────── #
    pdf.set_font(_FONT, "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, "Datos del deportista", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.2)

    fila_alt = False
    for clave, valor in valores_deportista.items():
        if clave not in VARIABLES:
            continue
        nombre = VARIABLES[clave]["nombre_display"]
        unidad = VARIABLES[clave].get("unidad", "")
        valor_str = f"{valor} {unidad}".strip()
        if not fila_alt:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(51, 65, 85)
        pdf.set_font(_FONT, "", 8.5)
        pdf.cell(110, 5.5, f"  {nombre}", fill=True)
        pdf.set_font(_FONT, "B", 8.5)
        pdf.cell(0, 5.5, valor_str, new_x="LMARGIN", new_y="NEXT", fill=True)
        fila_alt = not fila_alt

    pdf.ln(6)

    # ── Pie de página ─────────────────────────────────────────────────────── #
    pdf.set_y(-22)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.3)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(2)
    pdf.set_font(_FONT, "", 7.5)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(
        0, 4,
        "Herramienta de apoyo a la decision clinica - IntApp v2. "
        "No sustituye el criterio del profesional sanitario. "
        "Uso exclusivo para evaluacion clinica en el contexto del TFM, Universidad Europea.",
        align="C",
    )

    return pdf.output()


def _mostrar_tabla_referencia(valores_deportista: dict) -> None:
    with st.expander("📊 Tabla de comparación con rangos de referencia clínicos", expanded=False):
        filas = []
        for clave, valor in valores_deportista.items():
            if clave not in VARIABLES:
                continue
            info         = VARIABLES[clave]
            rango_normal = info.get("rango_normal")
            if rango_normal is None:
                continue
            try:
                val_num = float(valor)
                dentro  = rango_normal[0] <= val_num <= rango_normal[1]
            except (TypeError, ValueError):
                continue
            nombre = info["nombre_display"]
            unidad = info.get("unidad", "")
            filas.append({
                "Variable": nombre,
                "Valor":    f"{valor} {unidad}".strip(),
                "Rango":    f"{rango_normal[0]}–{rango_normal[1]} {unidad}".strip(),
                "Estado":   "✓ Dentro" if dentro else "✗ Fuera",
                "_color":   "#27ae60" if dentro else "#c0392b",
            })

        if not filas:
            st.info("No hay rangos de referencia disponibles.")
            return

        filas_html = "".join(
            f'<tr>'
            f'<td style="padding:0.35rem 0.6rem;">{f["Variable"]}</td>'
            f'<td style="padding:0.35rem 0.6rem;text-align:center;font-weight:600;">{f["Valor"]}</td>'
            f'<td style="padding:0.35rem 0.6rem;text-align:center;color:#555;">{f["Rango"]}</td>'
            f'<td style="padding:0.35rem 0.6rem;text-align:center;font-weight:700;color:{f["_color"]};">'
            f'{f["Estado"]}</td></tr>'
            for f in filas
        )
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
            f'<thead><tr style="background:#ecf0f1;">'
            f'<th style="padding:0.5rem 0.6rem;text-align:left;">Variable</th>'
            f'<th style="padding:0.5rem 0.6rem;text-align:center;">Valor</th>'
            f'<th style="padding:0.5rem 0.6rem;text-align:center;">Rango normal</th>'
            f'<th style="padding:0.5rem 0.6rem;text-align:center;">Estado</th>'
            f'</tr></thead><tbody>{filas_html}</tbody></table>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Layout principal
# ---------------------------------------------------------------------------

def main() -> None:

    # ── Sidebar ─────────────────────────────────────────────────────────── #
    with st.sidebar:
        st.markdown("### 🏃 IntApp v2")
        st.markdown("#### Evaluación de Riesgo de Lesión")
        st.divider()
        st.markdown("**Instrucciones**")
        st.markdown(
            "1. Completa el **perfil del deportista** (arriba).\n"
            "2. Registra los datos en las tres pestañas de **evaluación física**.\n"
            "3. Pulsa **Calcular Riesgo** y revisa el resultado.\n"
            "4. Descarga el **informe** si necesitas documentarlo."
        )
        st.divider()
        st.markdown("**Semáforo de riesgo**")
        st.markdown(
            "🟢 **Bajo** — Continuar programa habitual.\n\n"
            "🟡 **Medio** — Revisar factores de riesgo identificados.\n\n"
            "🔴 **Alto** — Intervención prioritaria recomendada."
        )
        st.divider()
        st.markdown("**Nota clínica**")
        st.caption(
            "NRS > 5: caso no concluyente. "
            "Se recomienda valoración presencial antes de continuar."
        )
        st.divider()
        st.caption("v2.2 · IntApp · Universidad Europea")

    # ── Cabecera ─────────────────────────────────────────────────────────── #
    st.markdown("# IntApp — Evaluación de Riesgo de Lesión")
    st.markdown(
        "Herramienta de apoyo a la decisión clínica para la valoración individualizada "
        "del riesgo de lesión en miembro inferior. "
        "Completa el perfil y la evaluación física, luego pulsa **Calcular Riesgo**."
    )
    st.divider()

    # ── Sección 1: Variables contextuales (al inicio del formulario) ─────── #
    with st.container(border=True):
        valores_ctx = _renderizar_contexto()

    st.markdown("")

    # ── Sección 2: Evaluación física con tabs ────────────────────────────── #
    with st.container(border=True):
        valores_fisica = _renderizar_evaluacion_fisica()

    valores_totales: dict = {**valores_ctx, **valores_fisica}
    st.markdown("")
    st.divider()

    # ── Botón de cálculo ─────────────────────────────────────────────────── #
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        calcular = st.button("⚡ Calcular Riesgo", type="primary", use_container_width=True)
    with col_info:
        st.caption(
            "El cálculo puede tardar unos segundos la primera vez "
            "mientras el modelo se carga en memoria."
        )

    if not calcular:
        return

    # ── Modelo no encontrado ─────────────────────────────────────────────── #
    pipeline = _cargar_pipeline_cached()
    if pipeline is None:
        st.markdown(
            '<div class="aviso-modelo">'
            "<strong>Modelo no encontrado</strong><br>"
            "No se ha localizado el modelo en <code>modelos/mejor_modelo.pkl</code>.<br><br>"
            "Genera el modelo ejecutando desde la raíz del proyecto:<br>"
            "<pre>python -m src.modelo</pre>"
            "Una vez entrenado, vuelve a pulsar <strong>Calcular Riesgo</strong>."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Regla clínica: NRS > 5 = caso no concluyente ────────────────────── #
    nrs = int(valores_totales.get("dolor_percibido_nrs", 0))
    if nrs > 5:
        st.markdown("## Resultado")
        st.divider()
        st.markdown(
            f'<div style="background:#f8d7da;border:1px solid #f5c6cb;'
            f'border-radius:10px;padding:1.5rem 2rem;">'
            f'<h3 style="color:#721c24;margin-top:0;">⚠️ Dolor agudo activo — Caso no concluyente</h3>'
            f'<p style="color:#721c24;margin-bottom:0.5rem;">'
            f'Dolor percibido (NRS) <strong>{nrs}/10</strong> — superior al umbral clínico de 5.</p>'
            f'<p style="color:#721c24;margin-bottom:0;">'
            f'<strong>Valoración clínica presencial urgente</strong> antes de continuar '
            f'con el programa de prevención.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.divider()
        st.caption(
            "Este resultado es una ayuda a la decisión clínica y no sustituye "
            "el criterio del profesional."
        )
        return

    # ── Inferencia ───────────────────────────────────────────────────────── #
    with st.spinner("Calculando riesgo..."):
        try:
            from src.evaluador_riesgo import (
                preparar_deportista,
                predecir_riesgo,
                importancia_variables_modelo,
            )

            modelo, scaler = pipeline
            df_procesado   = preparar_deportista(valores_totales, scaler)
            resultado_pred = predecir_riesgo(modelo, df_procesado)
            importancias   = importancia_variables_modelo(modelo, df_procesado, n_top=10)

            prediccion     = resultado_pred["prediccion"]
            probabilidades = resultado_pred["probabilidades"]

        except Exception as exc:
            st.error(
                f"Error durante la evaluación: {exc}\n\n"
                "Verifica que todos los campos estén correctamente cumplimentados "
                "y que el modelo sea compatible con los datos introducidos."
            )
            return

    # ── Resultados ───────────────────────────────────────────────────────── #
    st.markdown("## Resultado de la evaluación")
    st.divider()

    # Semáforo + probabilidades en paralelo
    col_sema, col_probs = st.columns([1, 2])
    with col_sema:
        _mostrar_semaforo(prediccion)
    with col_probs:
        _mostrar_probabilidades(probabilidades)

    st.divider()

    # Importancia de variables + banderas fuera de rango
    col_imp, col_flags = st.columns([1, 1])
    with col_imp:
        _mostrar_importancia_variables(importancias)
    with col_flags:
        flags = _mostrar_banderas_fuera_rango(valores_totales)

    st.divider()

    # Descarga del informe PDF
    informe_pdf = _generar_informe_pdf(valores_totales, prediccion, probabilidades, flags)
    st.download_button(
        label="📄 Descargar informe (.pdf)",
        data=bytes(informe_pdf),
        file_name=f"intapp_informe_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
        help="",
    )

    # Tabla de referencia (colapsable)
    _mostrar_tabla_referencia(valores_totales)

    st.divider()
    st.caption(
        "Este resultado es una ayuda a la decisión clínica y no sustituye "
        "el criterio profesional del fisioterapeuta o médico responsable."
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
