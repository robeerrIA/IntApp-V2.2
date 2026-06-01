"""
streamlit_app.py — Aplicación web IntApp para evaluación individual de riesgo de lesión.

Uso:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import base64 as _base64
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import streamlit.components.v1 as _components

from src.variables import VARIABLES, VARIABLES_ORIGINALES

# CalibradorUmbralAlto se serializa como __main__.CalibradorUmbralAlto cuando
# src/modelo.py se ejecuta como script. Este import la registra en __main__
# (que es este archivo cuando Streamlit lo ejecuta) para que pickle la encuentre.
try:
    from src.modelo import CalibradorUmbralAlto  # noqa: F401
except ImportError:
    pass

st.set_page_config(
    page_title="IntApp | Riesgo de Lesión",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Header nativo de Streamlit: borde rojo UE, limpio ── */
[data-testid="stHeader"] {
    background: #ffffff !important;
    border-top: 4px solid #ff3228 !important;
    border-bottom: 1px solid #dde2f0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
/* Ocultar la decoración de color de Streamlit (si aparece) */
[data-testid="stDecoration"] { display: none !important; }

/* ── Base ── */
.block-container { padding-top: 1.5rem; padding-bottom: 8rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #f4f6fa !important;
    border-right: 1px solid #dde2f0 !important;
}
[data-testid="stSidebar"] hr { border-color: #dde2f0; }
.sidebar-heading {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #2d41b4;
    margin-top: 0.25rem; margin-bottom: 0.6rem;
}
.sema-dot-row {
    display: flex; align-items: flex-start; gap: 0.5rem;
    margin-bottom: 0.45rem; font-size: 0.82rem; color: #1e1e1e; line-height: 1.4;
}
.sema-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 0.22rem; }
.dot-green { background: #14935a; }
.dot-amber { background: #c77700; }
.dot-red   { background: #d92d20; }
.nota-clinica {
    background: #fff8e6; border: 1px solid #f0d475; border-radius: 6px;
    padding: 0.6rem 0.75rem; font-size: 0.8rem; color: #7a4500; line-height: 1.45;
    margin-top: 0.25rem;
}
.sidebar-footer {
    font-size: 0.72rem; color: #9ca3af; margin-top: 0.75rem; line-height: 1.55;
}

/* ── Cabecera de sección ── */
.section-header {
    display: flex !important; align-items: center !important; gap: 0.55rem !important;
    font-size: 1.05rem !important; font-weight: 700 !important; color: #1e1e1e !important;
    margin-bottom: 1.25rem !important; margin-top: 0.25rem !important;
    border-left: 4px solid #2d41b4; padding-left: 0.6rem;
}
.section-icon {
    width: 22px; height: 22px; border-radius: 5px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0; line-height: 1;
}
.icon-perfil  { background: #fff3e0; color: #c77700; }
.icon-fisica  { background: #e8ecfc; color: #2d41b4; }
.icon-result  { background: #eaf6f1; color: #14935a; }

/* ── Inputs numéricos: fondo blanco, borde gris ── */
[data-testid="stNumberInput"] > div > div {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 6px !important;
}
[data-testid="stNumberInput"] input {
    background-color: #ffffff !important;
}



/* ── Thumb de todos los sliders: blanco, borde azul, más grande ── */
[data-testid="stSlider"] [role="slider"] {
    width: 15px !important;
    height: 15px !important;
    background-color: #ffffff !important;
    border: 2.5px solid #2d41b4 !important;
    box-shadow: 0 1px 4px rgba(45,65,180,0.25) !important;
}

/* ── Botón Protocolo (popover): fondo gris, borde y texto azul ── */
[data-testid="stPopover"] button {
    background: #f4f6fa !important;
    border: 1px solid #2d41b4 !important;
    color: #2d41b4 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    padding: 0.2rem 0.65rem !important;
}
[data-testid="stPopover"] button:hover {
    background: #e8ecfc !important;
}

/* ── Botón Descargar PDF: fondo blanco, texto y borde azul ── */
[data-testid="stDownloadButton"] button {
    background: #ffffff !important;
    border: 1.5px solid #2d41b4 !important;
    color: #2d41b4 !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #f4f6fa !important;
}

/* ── Etiquetas de subsección ── */
.subsec-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #9ca3af;
    margin-bottom: 0.5rem; margin-top: 1rem;
}

/* ── Badges (píldora) ── */
.badge {
    display: inline-block; border-radius: 999px;
    padding: 0.2rem 0.7rem; font-size: 0.75rem; font-weight: 600;
    margin-right: 0.35rem; margin-bottom: 0.35rem;
}
.badge-green  { background: #eaf6f1; color: #0d6e42; border: 1px solid #14935a; }
.badge-yellow { background: #fff8e6; color: #8a5300; border: 1px solid #c77700; }
.badge-red    { background: #fdf0ef; color: #a3221a; border: 1px solid #d92d20; }

/* ── Semáforo ── */
.sema-box {
    border-radius: 8px; padding: 2rem 1.5rem;
    text-align: center; color: #fff; height: 100%;
}
.sema-tri  { font-size: 2rem; line-height: 1; margin-bottom: 0.6rem; }
.sema-label {
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.14em; opacity: 0.85; margin-bottom: 0.3rem;
}
.sema-nivel { font-size: 1.4rem; font-weight: 800; letter-spacing: 0.02em; }
.sema-bajo  { background: #14935a; }
.sema-medio { background: #c77700; }
.sema-alto  { background: #d92d20; }

/* ── Tarjetas de probabilidad ── */
.prob-card {
    border: 1px solid #dde2f0; border-radius: 8px; padding: 1rem;
    text-align: center; background: #fff;
}
.prob-label {
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.4rem;
}
.prob-value { font-size: 1.75rem; font-weight: 800; }

/* ── Banderas fuera de rango ── */
.flags-header {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.5rem;
}
.flag-item {
    background: #fdf0ef; border-left: 4px solid #d92d20;
    padding: 0.4rem 0.75rem; margin-bottom: 0.3rem;
    font-size: 0.85rem; color: #a3221a; border-radius: 0 4px 4px 0;
}

/* ── Importancia: cabecera ── */
.vars-header {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.5rem;
}

/* ── Títulos bilaterales ── */
.bloque-titulo {
    font-size: 0.9rem; font-weight: 700; color: #1e1e1e;
    border-bottom: 1px solid #e8ecf5; padding-bottom: 0.35rem;
    margin-bottom: 0.5rem; margin-top: 0.75rem;
}

/* ── Aviso modelo / NRS ── */
.aviso-modelo {
    background: #fff8e6; border-left: 4px solid #c77700; border-radius: 0 6px 6px 0;
    padding: 1rem 1.25rem; color: #8a5300;
}

/* ── Splash ── */
.splash-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 68vh; text-align: center;
    padding: 3rem 1rem;
}
.splash-title {
    font-size: 2.4rem; font-weight: 900; color: #1e1e1e;
    letter-spacing: -0.02em; margin-bottom: 0.4rem;
}
.splash-sub {
    font-size: 1.05rem; font-weight: 500; color: #4b5563; margin-bottom: 0.25rem;
}
.splash-meta { font-size: 0.8rem; color: #9ca3af; margin-bottom: 2.5rem; }
.splash-divider {
    width: 48px; height: 3px; border-radius: 2px;
    background: linear-gradient(to right, #2d41b4, #ff3228);
    margin: 0 auto 2.5rem;
}

/* ── Breadcrumb ── */
.breadcrumb-wrap {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.65rem 1rem; background: #f4f6fa;
    border: 1px solid #dde2f0; border-radius: 8px; margin-bottom: 1.5rem;
}
.bc-dot-active {
    background: #2d41b4; color: #fff; border-radius: 50%;
    width: 22px; height: 22px; display: inline-flex; align-items: center;
    justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}
.bc-dot-done {
    background: #eaf6f1; color: #14935a; border-radius: 50%;
    width: 22px; height: 22px; display: inline-flex; align-items: center;
    justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}
.bc-dot-pending {
    background: #f4f6fa; color: #9ca3af; border: 1px solid #dde2f0; border-radius: 50%;
    width: 22px; height: 22px; display: inline-flex; align-items: center;
    justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}
.bc-label-active { font-size: 0.85rem; font-weight: 600; color: #1e1e1e; }
.bc-label-done   { font-size: 0.85rem; font-weight: 600; color: #14935a; }
.bc-label-pending { font-size: 0.85rem; color: #9ca3af; }
.bc-sep { color: #dde2f0; font-size: 1rem; }

/* ── Resumen paciente ── */
.resumen-paciente {
    background: #f4f6fa; border: 1px solid #dde2f0; border-radius: 8px;
    padding: 0.75rem 1.25rem; margin-bottom: 1.25rem;
    display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: center;
}
.res-item-label {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.1rem;
}
.res-item-value { font-size: 0.9rem; font-weight: 600; color: #1e1e1e; }

/* ── Tarjetas de instrucción para el cuestionario paciente ── */
.instruccion-card {
    background: #f8f9ff; border: 1px solid #e8ecfc;
    border-left: 3px solid #2d41b4; border-radius: 0 6px 6px 0;
    padding: 0.55rem 0.85rem; font-size: 0.81rem; color: #374151;
    margin-bottom: 0.5rem; line-height: 1.5;
}
.instruccion-card strong { color: #2d41b4; }
.hooper-total-ok   { color: #14935a; font-weight: 700; }
.hooper-total-mid  { color: #c77700; font-weight: 700; }
.hooper-total-bad  { color: #d92d20; font-weight: 700; }

/* ── Tabla de referencia ── */
table { border-collapse: collapse; width: 100%; font-size: 0.875rem; }
thead tr { background: #f4f6fa; }
th { padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; color: #3d3d3d; border-bottom: 2px solid #dde2f0; }
td { padding: 0.4rem 0.75rem; border-bottom: 1px solid #e8ecf5; color: #1e1e1e; }
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
    0: "0: Sin valgo", 1: "1: Leve", 2: "2: Moderado", 3: "3: Severo",
}
_ETIQUETAS_GENERO: dict[str, str] = {"masculino": "Masculino", "femenino": "Femenino"}

_COLORES_PROB: dict[str, str] = {"bajo": "#14935a", "medio": "#c77700", "alto": "#d92d20"}
_NOMBRES_CLASE_ES: dict[str, str] = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}
_NOMBRES_NIVEL: dict[str, str] = {
    "bajo": "RIESGO BAJO", "medio": "RIESGO MEDIO", "alto": "RIESGO ALTO",
}
_CLASES_CSS_SEMA: dict[str, str] = {
    "bajo": "sema-bajo", "medio": "sema-medio", "alto": "sema-alto",
}

# Badges de nivel de evidencia
_BADGE_EVIDENCIA: dict[str, str] = {
    "alto":     "badge-green",
    "moderado": "badge-yellow",
    "bajo":     "badge-red",
}
_LABEL_EVIDENCIA: dict[str, str] = {
    "alto":     "Evidencia alta",
    "moderado": "Evidencia moderada",
    "bajo":     "Evidencia baja",
}

# Orden explícito de las variables contextuales
_KEYS_NRS       = ["dolor_percibido_nrs"]
_KEYS_DEMOGRAFIA = ["edad", "genero", "peso_corporal"]
_KEYS_ACTIVIDAD  = ["nivel_actividad"]
_KEYS_CARGA      = ["historial_lesional", "hooper_index"]


# ---------------------------------------------------------------------------
# Header nativo: inyección de logo + título vía JavaScript
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _logo_b64() -> str:
    path = Path(__file__).resolve().parent.parent / "docs" / "ue-logo.png"
    if path.exists():
        return _base64.b64encode(path.read_bytes()).decode()
    return ""


def _inyectar_header_content() -> None:
    logo = _logo_b64()
    img_html = (
        f'<img src="data:image/png;base64,{logo}" height="26" '
        f'style="flex-shrink:0;object-fit:contain;" alt="UE">'
        if logo else ''
    )
    _components.html(
        f"""
        <script>
        (function() {{
            try {{
                var doc = window.parent.document;

                // ── Header (solo una vez) ──────────────────────────────────────
                if (!doc.getElementById('intapp-hdr')) {{
                    var hdr = doc.querySelector('[data-testid="stHeader"]');
                    if (hdr) {{
                        var deco = doc.querySelector('[data-testid="stDecoration"]');
                        if (deco) deco.style.display = 'none';
                        var el = doc.createElement('div');
                        el.id = 'intapp-hdr';
                        el.style.cssText = [
                            'position:absolute','left:3.5rem','right:10rem',
                            'top:0','bottom:0','display:flex','align-items:center',
                            'gap:0.75rem','pointer-events:none'
                        ].join(';');
                        el.innerHTML = `
                            {img_html}
                            <div style="display:flex;flex-direction:column;justify-content:center;min-width:0;flex:1;">
                                <div style="font-size:0.88rem;font-weight:700;color:#1e1e1e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                    IntApp · Evaluación de Riesgo de Lesión
                                </div>
                                <div style="font-size:0.7rem;color:#6b7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                    Herramienta de apoyo a la decisión clínica · Miembro inferior
                                </div>
                            </div>
                            <span style="background:#f4f6fa;border:1px solid #dde2f0;padding:0.15rem 0.65rem;font-size:0.7rem;font-weight:700;color:#2d41b4;border-radius:4px;white-space:nowrap;flex-shrink:0;">
                                TFM · v2.3
                            </span>
                        `;
                        hdr.style.position = 'relative';
                        hdr.appendChild(el);
                    }}
                }}

                // ── Engrosar tracks de todos los sliders ──────────────────────
                function styleSliders() {{
                    var bws = doc.querySelectorAll('[data-baseweb="slider"]');
                    for (var i = 0; i < bws.length; i++) {{
                        var divs = bws[i].querySelectorAll('div');
                        for (var j = 0; j < divs.length && j < 25; j++) {{
                            var d = divs[j];
                            var h = parseFloat(window.parent.getComputedStyle(d).height);
                            if (h >= 3 && h <= 10) {{
                                d.style.setProperty('height', '6px', 'important');
                                d.style.setProperty('border-radius', '3px', 'important');
                                break;
                            }}
                        }}
                    }}
                }}
                styleSliders();
                setTimeout(styleSliders, 300);

            }} catch(e) {{}}
        }})();
        </script>
        """,
        height=0,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re as _re

def _strip_emojis(text: str) -> str:
    return _re.sub(r'[^\x00-\x7FÀ-ɏ°·–—]', '', text).strip()


def _format_protocolo(text: str) -> str:
    """Convierte el texto de protocolo (una línea por paso) en HTML de lista numerada."""
    lines = [l.strip() for l in _strip_emojis(text).split('\n') if l.strip()]
    if not lines:
        return ''
    items = ''.join(
        f'<li style="margin-bottom:0.45rem;line-height:1.45;">{l}</li>'
        for l in lines
    )
    return (
        '<ol style="margin:0.25rem 0 0 0;padding-left:1.3rem;'
        'font-size:0.84rem;color:#1e1e1e;">'
        + items + '</ol>'
    )


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
        slider_key = f"slider_{key}"
        num_key    = f"ninput_{key}"

        def _sync_from_slider(sk=slider_key, nk=num_key):
            st.session_state[nk] = st.session_state[sk]

        def _sync_from_num(sk=slider_key, nk=num_key, lo=minv, hi=maxv):
            st.session_state[sk] = max(lo, min(hi, float(st.session_state[nk])))

        # Valor actual (número editable, visible primero)
        st.number_input(
            etiqueta, min_value=minv, max_value=maxv,
            value=float(st.session_state.get(slider_key, default)),
            step=paso, key=num_key, on_change=_sync_from_num,
        )
        # Barra deslizante debajo (oculta etiqueta para no duplicarla)
        st.slider(
            etiqueta, min_value=minv, max_value=maxv,
            value=float(st.session_state.get(num_key, default)),
            step=paso, key=slider_key, on_change=_sync_from_slider,
            label_visibility="collapsed",
        )
        return float(st.session_state.get(slider_key, default))

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
            slider_key = f"slider_{key}"
            num_key    = f"ninput_{key}"

            def _sync_ord_slider(sk=slider_key, nk=num_key):
                st.session_state[nk] = int(st.session_state[sk])

            def _sync_ord_num(sk=slider_key, nk=num_key, lo=minv, hi=maxv):
                st.session_state[sk] = int(max(lo, min(hi, st.session_state[nk])))

            st.number_input(
                etiqueta, min_value=minv, max_value=maxv,
                value=int(st.session_state.get(slider_key, default)),
                step=1, key=num_key, on_change=_sync_ord_num,
            )
            st.slider(
                etiqueta, min_value=minv, max_value=maxv,
                value=int(st.session_state.get(num_key, default)),
                step=1, key=slider_key, on_change=_sync_ord_slider,
                label_visibility="collapsed",
            )
            return int(st.session_state.get(slider_key, default))

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
        return f'<span class="badge badge-green">Sin dolor (NRS {nrs})</span>'
    elif nrs <= 3:
        return f'<span class="badge badge-green">Dolor leve (NRS {nrs})</span>'
    elif nrs <= 5:
        return f'<span class="badge badge-yellow">Dolor moderado (NRS {nrs})</span>'
    elif nrs <= 7:
        return f'<span class="badge badge-red">Dolor intenso (NRS {nrs}, caso no concluyente)</span>'
    else:
        return f'<span class="badge badge-red">Dolor severo (NRS {nrs}, valoración urgente presencial)</span>'


def _widget_y_balance(lado: str) -> float:
    """Inputs A/PM/PL + longitud → calcula CS% automáticamente.

    Devuelve el Composite Score como float (% longitud miembro).
    """
    key_sfx = "der" if lado == "derecha" else "izq"
    caption  = "Lado derecho" if lado == "derecha" else "Lado izquierdo"

    st.caption(caption)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        a   = st.number_input("Anterior (cm)",       min_value=0.0, max_value=120.0,
                               value=60.0, step=0.5, key=f"ybt_a_{key_sfx}")
    with c2:
        pm  = st.number_input("Posteromedial (cm)",  min_value=0.0, max_value=120.0,
                               value=80.0, step=0.5, key=f"ybt_pm_{key_sfx}")
    with c3:
        pl  = st.number_input("Posterolateral (cm)", min_value=0.0, max_value=120.0,
                               value=75.0, step=0.5, key=f"ybt_pl_{key_sfx}")
    with c4:
        long = st.number_input("Longitud (cm)", min_value=60.0, max_value=120.0,
                                value=90.0, step=0.5, key=f"ybt_long_{key_sfx}")

    cs = round((a + pm + pl) / (3 * long) * 100, 1) if long > 0 else 0.0
    color = "#dc3545" if cs < 89 else "#28a745"
    st.markdown(
        f"<div style='text-align:center; font-size:1.1rem; font-weight:600; "
        f"color:{color}; margin-top:0.2rem;'>CS = {cs:.1f}%</div>",
        unsafe_allow_html=True,
    )
    return cs


def _historial_badge_html(historial: int) -> str:
    if historial == 0:
        return '<span class="badge badge-green">Sin lesiones previas</span>'
    elif historial == 1:
        return '<span class="badge badge-yellow">1 lesión previa</span>'
    return f'<span class="badge badge-red">{historial}+ lesiones previas</span>'


_NIVEL_ACTIVIDAD_DESC: dict[str, str] = {
    "sedentario":   "Menos de 150 min/semana de actividad física sin pauta estructurada.",
    "recreacional": "150-300 min/semana, práctica habitual sin competición.",
    "activo":       "Más de 300 min/semana o competición amateur federada.",
    "elite":        "Deporte de alto rendimiento o competición profesional.",
}


def _widget_hooper_paciente() -> int:
    """Muestra las 4 sub-preguntas del Hooper Wellbeing Index y devuelve el total."""
    items = [
        ("hooper_sq0", "Calidad del sueño",
         "1 = muy buena, sin interrupciones · 7 = muy mala, casi sin dormir"),
        ("hooper_sq1", "Nivel de estrés",
         "1 = muy relajado, sin preocupaciones · 7 = muy estresado"),
        ("hooper_sq2", "Fatiga general",
         "1 = totalmente descansado · 7 = agotado, sin energía"),
        ("hooper_sq3", "Dolor muscular",
         "1 = sin dolor · 7 = dolor intenso que limita el movimiento"),
    ]
    st.markdown(
        '<div class="instruccion-card">'
        '<strong>Cómo responder:</strong> valore del 1 (muy bueno) al 7 (muy malo) '
        'cómo se ha encontrado en los <strong>últimos 3 días</strong>. '
        'Se sumarán los 4 ítems (rango total 4-28).'
        '</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    total = 0
    for i, (key, label, ayuda) in enumerate(items):
        col = c1 if i % 2 == 0 else c2
        with col:
            v = st.number_input(
                label, min_value=1, max_value=7, value=1, step=1,
                key=key, help=ayuda,
            )
            total += int(v)
    cls = "hooper-total-ok" if total <= 12 else ("hooper-total-mid" if total <= 18 else "hooper-total-bad")
    st.markdown(
        f'<div style="text-align:center;margin-top:0.3rem;">'
        f'<span class="{cls}">Hooper Index: {total} / 28</span></div>',
        unsafe_allow_html=True,
    )
    return total


def _renderizar_contexto(instrucciones: bool = False) -> dict:
    """Renderiza Section 1: variables contextuales. Devuelve dict de valores."""
    vars_ctx = {k: v for k, v in VARIABLES.items() if v.get("bloque") == "contexto"}
    valores: dict = {}

    st.markdown(
        '<div class="section-header">'
        '<span class="section-icon icon-perfil">+</span>'
        'Perfil del deportista'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── NRS — destacado en la parte superior ────────────────────────────── #
    nrs_key = _KEYS_NRS[0]
    if nrs_key in vars_ctx:
        info  = vars_ctx[nrs_key]
        rango = info.get("rango_sintetico") or info.get("rango_normal", (0, 10))
        nrs_sk = f"slider_{nrs_key}"

        if instrucciones:
            st.markdown(
                '<div class="instruccion-card">'
                '<strong>¿Cómo puntuar?</strong> Mueva el deslizador hasta el número que mejor '
                'describe su dolor <strong>en este momento</strong>.<br>'
                '0 = sin ningún dolor &nbsp;·&nbsp; '
                '1-3 = dolor leve (no limita actividades) &nbsp;·&nbsp; '
                '4-6 = dolor moderado (limita parcialmente) &nbsp;·&nbsp; '
                '7-10 = dolor severo (impide realizar actividades).'
                '</div>',
                unsafe_allow_html=True,
            )

        st.slider(
            "Dolor percibido · Escala NRS",
            min_value=int(rango[0]), max_value=int(rango[1]),
            value=0, step=1, key=nrs_sk,
        )
        nrs_val = int(st.session_state.get(nrs_sk, 0))
        st.markdown(
            '<div style="margin-top:0.1rem;margin-bottom:0.5rem;">'
            '<div style="height:6px;border-radius:3px;'
            'background:linear-gradient(to right,#14935a 0%,#7dc23e 25%,#c77700 55%,#d92d20 100%);"></div>'
            '<div style="display:flex;justify-content:space-between;'
            'font-size:0.68rem;color:#9ca3af;margin-top:0.2rem;">'
            '<span>0 · sin dolor</span><span>5 · umbral clínico</span><span>10 · máximo</span>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        valores[nrs_key] = nrs_val
        st.markdown(_nrs_badge_html(nrs_val), unsafe_allow_html=True)
    st.markdown("")

    # ── Demografía ──────────────────────────────────────────────────────── #
    st.markdown('<div class="subsec-label">Datos demográficos</div>', unsafe_allow_html=True)
    if instrucciones:
        st.caption("Introduzca sus datos personales tal como aparecen en su historial clínico.")
    demograficas = [k for k in _KEYS_DEMOGRAFIA if k in vars_ctx]
    if demograficas:
        cols = st.columns(len(demograficas))
        for col, k in zip(cols, demograficas):
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])

    # ── Nivel y perfil de actividad ──────────────────────────────────────── #
    st.markdown('<div class="subsec-label">Nivel de actividad deportiva</div>', unsafe_allow_html=True)
    if instrucciones:
        st.markdown(
            '<div class="instruccion-card">'
            '<strong>Seleccione el nivel que mejor describe su práctica habitual:</strong><br>'
            '<b>Sedentario</b> — menos de 150 min/semana sin pauta estructurada.<br>'
            '<b>Recreacional</b> — 150-300 min/semana, práctica regular sin competición.<br>'
            '<b>Activo</b> — más de 300 min/semana o competición amateur.<br>'
            '<b>Elite</b> — deporte de alto rendimiento o competición profesional.'
            '</div>',
            unsafe_allow_html=True,
        )
    actividad_keys = [k for k in _KEYS_ACTIVIDAD if k in vars_ctx]
    if actividad_keys:
        cols = st.columns(len(actividad_keys))
        for col, k in zip(cols, actividad_keys):
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])

    # ── Factores de carga ────────────────────────────────────────────────── #
    st.markdown('<div class="subsec-label">Factores de carga y riesgo contextual</div>', unsafe_allow_html=True)
    carga_keys = [k for k in _KEYS_CARGA if k in vars_ctx]

    if instrucciones:
        # Historial lesional
        if "historial_lesional" in carga_keys:
            st.markdown(
                '<div class="instruccion-card">'
                '<strong>Historial lesional:</strong> indique cuántas lesiones '
                'musculoesqueléticas ha sufrido en los <strong>últimos 12 meses</strong> '
                'que hayan requerido al menos <strong>3 días de baja deportiva</strong> '
                '(esguinces, roturas, tendinopatías, etc.).'
                '</div>',
                unsafe_allow_html=True,
            )
        cols_h = st.columns(len(carga_keys))
        for col, k in zip(cols_h, carga_keys):
            if k == "hooper_index":
                continue
            with col:
                valores[k] = _widget_variable(k, vars_ctx[k])
        # Hooper con sub-preguntas
        if "hooper_index" in carga_keys:
            st.markdown('<div class="subsec-label" style="margin-top:1.25rem;">Hooper Wellbeing Index</div>', unsafe_allow_html=True)
            valores["hooper_index"] = _widget_hooper_paciente()
    else:
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
                    with st.popover("Protocolo", use_container_width=True):
                        st.markdown(_format_protocolo(protocolo), unsafe_allow_html=True)
            clave_der, clave_izq = f"{clave_orig}_der", f"{clave_orig}_izq"
            if clave_orig == "y_balance_cs":
                col_der, col_izq = st.columns(2)
                with col_der:
                    valores[clave_der] = _widget_y_balance("derecha")
                with col_izq:
                    valores[clave_izq] = _widget_y_balance("izquierda")
            else:
                col_der, col_izq = st.columns(2)
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
                    with st.popover("Protocolo", use_container_width=True):
                        st.markdown(_format_protocolo(protocolo), unsafe_allow_html=True)

    return valores


def _renderizar_evaluacion_fisica() -> dict:
    """Renderiza Section 2: evaluación física con tres pestañas."""
    st.markdown(
        '<div class="section-header">'
        '<span class="section-icon icon-fisica">▶</span>'
        'Evaluación física'
        '</div>',
        unsafe_allow_html=True,
    )
    tab_fuerza, tab_movilidad, tab_control = st.tabs(
        ["Fuerza muscular", "Movilidad articular", "Control neuromuscular"]
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
        f'<div class="sema-tri">▲</div>'
        f'<div class="sema-label">Nivel de riesgo</div>'
        f'<div class="sema-nivel">{nivel_texto}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _mostrar_probabilidades(probabilidades: dict[str, float]) -> None:
    st.markdown('<div class="prob-label" style="margin-bottom:0.6rem;">Probabilidades por clase</div>', unsafe_allow_html=True)
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


_RATIOS_CLINICOS_DISPLAY: dict[str, str] = {
    "ratio_hq_der":      "Ratio H:Q (derecho)",
    "ratio_hq_izq":      "Ratio H:Q (izquierdo)",
    "ratio_hq":          "Ratio H:Q",
    "ratio_add_abd_der": "Ratio ADD/ABD (derecho)",
    "ratio_add_abd_izq": "Ratio ADD/ABD (izquierdo)",
    "ratio_add_abd":     "Ratio ADD/ABD",
}


def _nombre_display_variable(clave: str) -> str:
    """Resuelve el nombre legible de cualquier feature, incluidas las derivadas."""
    if clave in VARIABLES:
        return VARIABLES[clave]["nombre_display"]
    if clave in VARIABLES_ORIGINALES:
        return VARIABLES_ORIGINALES[clave]["nombre_display"]
    if clave in _RATIOS_CLINICOS_DISPLAY:
        return _RATIOS_CLINICOS_DISPLAY[clave]
    if clave.endswith("_ratio_ref"):
        base = clave[:-len("_ratio_ref")]
        return f"{_nombre_display_variable(base)} (ratio normativo)"
    if clave.endswith("_nkg"):
        base = clave[:-len("_nkg")]
        return f"{_nombre_display_variable(base)} (N/kg)"
    if clave.startswith("asimetria_"):
        base = clave[len("asimetria_"):]
        return f"Asimetría {_nombre_display_variable(base)}"
    return clave.replace("_", " ").title()


def _mostrar_importancia_variables(importancias: list[tuple[str, float]]) -> None:
    import pandas as pd
    if not importancias:
        st.info("Importancia de variables no disponible para este modelo.")
        return
    st.markdown('<div class="vars-header">Variables mas influyentes en el modelo</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="flags-header">Variables fuera de rango de referencia</div>', unsafe_allow_html=True)
        for f in flags:
            st.markdown(f'<div class="flag-item">△ {f}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="flags-header">Variables fuera de rango de referencia</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.85rem;color:#14935a;padding:0.3rem 0;">Todos los valores dentro de los rangos de referencia.</div>', unsafe_allow_html=True)

    return flags


def _generar_informe_pdf(
    valores_deportista: dict,
    prediccion: str,
    probabilidades: dict[str, float],
    flags: list[str],
    top_variables: list[tuple[str, float]] | None = None,
) -> bytes:
    from fpdf import FPDF

    LOGO_PATH = Path(__file__).resolve().parent.parent / "docs" / "ue-logo.png"

    # Fuentes TTF con soporte Unicode completo (español + caracteres especiales).
    # Se busca en macOS, Windows y Linux (Streamlit Cloud) en ese orden.
    _FONT_CANDIDATES = [
        # macOS
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        # Linux / Streamlit Cloud
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    _FONT_BOLD_CANDIDATES = [
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/ArialBD.ttf",
        # Linux / Streamlit Cloud
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    _FONT_REGULAR = next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)
    _FONT_BOLD    = next((p for p in _FONT_BOLD_CANDIDATES if Path(p).exists()), _FONT_REGULAR)

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
    pdf.cell(0, 8, "IntApp v2 - Informe de Evaluación de Riesgo")
    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.set_xy(42, 23)
    pdf.cell(
        0, 5,
        f"Universidad Europea  ·  Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}  ·  v2.3",
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

    # ── Variables más influyentes (SHAP) ───────────────────────────────────── #
    if top_variables:
        pdf.set_font(_FONT, "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "Factores determinantes (SHAP)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(_FONT, "", 7.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 4.5, "Contribucion especifica para este deportista. + aumenta riesgo / - lo reduce.",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font(_FONT, "", 8.5)
        fila_alt_shap = False
        for nombre_feat, valor_shap in top_variables:
            nombre_legible = _nombre_display_variable(nombre_feat)
            direccion = "+ " if valor_shap >= 0 else "- "
            if not fila_alt_shap:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(241, 245, 249)
            color_shap = (180, 30, 30) if valor_shap >= 0 else (30, 80, 180)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(120, 5.5, f"  {nombre_legible}", fill=True)
            pdf.set_text_color(*color_shap)
            pdf.set_font(_FONT, "B", 8.5)
            pdf.cell(0, 5.5, f"{direccion}{abs(valor_shap):.4f}", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_font(_FONT, "", 8.5)
            fila_alt_shap = not fila_alt_shap
        pdf.set_text_color(15, 23, 42)
        pdf.ln(4)

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
        "Herramienta de apoyo a la decisión clínica - IntApp v2. "
        "No sustituye el criterio del profesional sanitario. "
        "Uso exclusivo para evaluación clínica en el contexto del TFM, Universidad Europea.",
        align="C",
    )

    return pdf.output()


def _mostrar_shap_explicacion(resultado_shap: dict) -> None:
    import matplotlib.pyplot as plt
    import pandas as pd

    fig = resultado_shap.get("figura_waterfall")
    top_vars = resultado_shap.get("top_variables", [])

    st.caption(
        "Barras rojas: la variable aumenta el riesgo predicho. "
        "Barras azules: la variable lo reduce. "
        "Específico para esta evaluación individual, no para el modelo en general."
    )

    if fig is not None:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    elif top_vars:
        filas = [
            {
                "Variable": _nombre_display_variable(n),
                "Impacto SHAP": round(v, 4),
                "Dirección": "▲ Aumenta riesgo" if v > 0 else "▼ Reduce riesgo",
            }
            for n, v in top_vars
        ]
        st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    else:
        st.info("Explicación SHAP no disponible para este modelo.")


def _mostrar_tabla_referencia(valores_deportista: dict) -> None:
    with st.expander("Comparación con rangos de referencia clínicos", expanded=False):
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
# Splash, breadcrumb y resumen de paciente
# ---------------------------------------------------------------------------

def _renderizar_splash() -> None:
    logo = _logo_b64()
    img_tag = (
        f'<img src="data:image/png;base64,{logo}" '
        f'style="height:72px;object-fit:contain;margin-bottom:1.75rem;" alt="UE">'
        if logo else ''
    )
    st.markdown(
        f'<div class="splash-wrap">'
        f'{img_tag}'
        f'<div class="splash-title">IntApp</div>'
        f'<div class="splash-sub">Evaluación de Riesgo de Lesión · Miembro inferior</div>'
        f'<div class="splash-meta">'
        f'Herramienta de apoyo a la decisión clínica<br>'
        f'Universidad Europea · Máster en IA aplicada al deporte · Roberto Franco · v2.3'
        f'</div>'
        f'<div class="splash-divider"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        if st.button("Iniciar evaluación", type="primary", use_container_width=True):
            st.session_state["app_step"] = "paciente"
            st.rerun()


def _mostrar_breadcrumb(paso: int) -> None:
    def _dot(n: int) -> str:
        if n < paso:
            return f'<span class="bc-dot-done">✓</span>'
        if n == paso:
            return f'<span class="bc-dot-active">{n}</span>'
        return f'<span class="bc-dot-pending">{n}</span>'

    def _label(n: int, txt: str) -> str:
        cls = "bc-label-done" if n < paso else ("bc-label-active" if n == paso else "bc-label-pending")
        return f'<span class="{cls}">{txt}</span>'

    st.markdown(
        '<div class="breadcrumb-wrap">'
        + _dot(1) + _label(1, "Datos del deportista")
        + '<span class="bc-sep">›</span>'
        + _dot(2) + _label(2, "Evaluación física")
        + '</div>',
        unsafe_allow_html=True,
    )


def _mostrar_resumen_paciente(valores_ctx: dict) -> None:
    if not valores_ctx:
        return
    edad     = valores_ctx.get("edad", "?")
    genero   = "Masculino" if valores_ctx.get("genero") == "masculino" else "Femenino"
    peso     = valores_ctx.get("peso_corporal", "?")
    actividad = str(valores_ctx.get("nivel_actividad", "")).capitalize()
    nrs      = int(valores_ctx.get("dolor_percibido_nrs", 0))
    historial = int(valores_ctx.get("historial_lesional", 0))
    nrs_color = "#14935a" if nrs <= 3 else ("#c77700" if nrs <= 5 else "#d92d20")

    def _item(label: str, value: str, color: str = "#1e1e1e") -> str:
        return (
            f'<div><div class="res-item-label">{label}</div>'
            f'<div class="res-item-value" style="color:{color};">{value}</div></div>'
        )

    st.markdown(
        '<div class="resumen-paciente">'
        + _item("Deportista", f"{edad} años · {genero} · {peso} kg")
        + _item("Nivel de actividad", actividad)
        + _item("NRS dolor", f"{nrs}/10", nrs_color)
        + _item("Lesiones previas", str(historial))
        + '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout principal
# ---------------------------------------------------------------------------

def main() -> None:

    # ── Sidebar ─────────────────────────────────────────────────────────── #
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-heading">Cómo usar la herramienta</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "1. Completa el **perfil del deportista**.\n"
            "2. Registra los datos en las tres pestañas de **evaluación física**.\n"
            "3. Pulsa **Calcular riesgo** y revisa el resultado.\n"
            "4. Descarga el **informe en PDF** si necesitas documentarlo."
        )
        st.divider()
        st.markdown('<div class="sidebar-heading">Semáforo de riesgo</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sema-dot-row"><span class="sema-dot dot-green"></span>'
            '<span><strong>Bajo</strong> · Continuar programa habitual.</span></div>'
            '<div class="sema-dot-row"><span class="sema-dot dot-amber"></span>'
            '<span><strong>Medio</strong> · Revisar factores de riesgo identificados.</span></div>'
            '<div class="sema-dot-row"><span class="sema-dot dot-red"></span>'
            '<span><strong>Alto</strong> · Intervención prioritaria recomendada.</span></div>',
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown('<div class="sidebar-heading">Nota clínica</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="nota-clinica">'
            'NRS > 5: caso no concluyente. Se recomienda valoración presencial antes de continuar.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-footer">'
            'Universidad Europea · Máster en IA aplicada al deporte<br>'
            'Roberto Franco · IntApp v2.3'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Inyectar logo + título en el header nativo ──────────────────────── #
    _inyectar_header_content()

    step = st.session_state.get("app_step", "splash")

    # ══ PASO 0: Splash ═══════════════════════════════════════════════════════
    if step == "splash":
        _renderizar_splash()
        return

    # ══ PASO 1: Cuestionario del deportista ══════════════════════════════════
    if step == "paciente":
        _mostrar_breadcrumb(1)
        st.markdown("## Cuestionario del deportista")
        st.caption(
            "Complete los datos antes de la valoración. "
            "El fisioterapeuta continuará con la evaluación física."
        )
        st.markdown("")
        valores_ctx = _renderizar_contexto(instrucciones=True)
        st.markdown("")
        col_btn, col_volver, _ = st.columns([2, 1, 4])
        with col_btn:
            if st.button("Continuar a la evaluación", type="primary", use_container_width=True):
                st.session_state["valores_ctx"] = valores_ctx
                st.session_state["app_step"] = "evaluacion"
                st.rerun()
        with col_volver:
            if st.button("Volver al inicio", use_container_width=True):
                st.session_state["app_step"] = "splash"
                st.rerun()
        return

    # ══ PASO 2: Evaluación física ═════════════════════════════════════════════
    _mostrar_breadcrumb(2)

    valores_ctx: dict = st.session_state.get("valores_ctx", {})
    _mostrar_resumen_paciente(valores_ctx)

    # ── Sección: Evaluación física con tabs ──────────────────────────────── #
    valores_fisica = _renderizar_evaluacion_fisica()

    valores_totales: dict = {**valores_ctx, **valores_fisica}
    st.markdown("")

    # ── Botón de cálculo ─────────────────────────────────────────────────── #
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        calcular = st.button("Calcular riesgo", type="primary", use_container_width=True)
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
        st.markdown(
            f'<div class="aviso-modelo">'
            f'<strong>Evaluación no concluyente. Dolor agudo activo</strong><br><br>'
            f'Dolor percibido (NRS) <strong>{nrs}/10</strong>, superior al umbral clínico de 5. '
            f'Se recomienda valoración clínica presencial antes de continuar con el programa de prevención.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")
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
                explicar_prediccion,
            )

            modelo, scaler = pipeline
            df_procesado   = preparar_deportista(valores_totales, scaler)
            resultado_pred = predecir_riesgo(modelo, df_procesado)
            importancias   = importancia_variables_modelo(modelo, df_procesado, n_top=10)
            resultado_shap = explicar_prediccion(modelo, df_procesado, max_variables=10)

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
    st.markdown(
        '<div class="section-header" style="font-size:1.25rem;margin-top:1rem;">'
        '<span class="section-icon icon-result">✓</span>'
        'Resultado de la evaluación'
        '</div>',
        unsafe_allow_html=True,
    )

    col_sema, col_probs = st.columns([1, 2])
    with col_sema:
        _mostrar_semaforo(prediccion)
    with col_probs:
        _mostrar_probabilidades(probabilidades)

    st.markdown("")

    col_imp, col_flags = st.columns([1, 1])
    with col_imp:
        _mostrar_importancia_variables(importancias)
    with col_flags:
        flags = _mostrar_banderas_fuera_rango(valores_totales)

    st.markdown("")

    informe_pdf = _generar_informe_pdf(
        valores_totales, prediccion, probabilidades, flags,
        top_variables=resultado_shap.get("top_variables"),
    )
    st.download_button(
        label="Descargar informe (PDF)",
        data=bytes(informe_pdf),
        file_name=f"intapp_informe_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
        help="",
    )

    with st.expander("Factores determinantes para este deportista (SHAP)"):
        _mostrar_shap_explicacion(resultado_shap)

    _mostrar_tabla_referencia(valores_totales)

    st.markdown("")
    st.caption(
        "Este resultado es una ayuda a la decisión clínica y no sustituye "
        "el criterio profesional del fisioterapeuta o médico responsable."
    )

    st.divider()
    if st.button("Nueva evaluación", use_container_width=False):
        keys_to_keep = {"app_step"}
        for k in list(st.session_state.keys()):
            if k not in keys_to_keep:
                del st.session_state[k]
        st.session_state["app_step"] = "splash"
        st.rerun()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
