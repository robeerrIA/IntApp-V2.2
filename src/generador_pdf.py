from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.variables import VARIABLES, VARIABLES_ORIGINALES

_NOMBRES_NIVEL: dict[str, str] = {
    "bajo": "RIESGO BAJO", "medio": "RIESGO MEDIO", "alto": "RIESGO ALTO",
}

_RATIOS_CLINICOS_DISPLAY: dict[str, str] = {
    "ratio_hq_der":      "Ratio H:Q (derecho)",
    "ratio_hq_izq":      "Ratio H:Q (izquierdo)",
    "ratio_hq":          "Ratio H:Q",
    "ratio_add_abd_der": "Ratio ADD/ABD (derecho)",
    "ratio_add_abd_izq": "Ratio ADD/ABD (izquierdo)",
    "ratio_add_abd":     "Ratio ADD/ABD",
}


def _nombre_display_variable(clave: str) -> str:
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
