"""
Genera el PDF explicativo de IntApp v2 para un lector no técnico.
Ejecutar: python docs/generar_manual_app.py
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "Manual_IntApp_v2.pdf"
LOGO = RAIZ / "docs" / "ue-logo.png"

_FONT_CANDIDATES = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_FR = next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)
_FB = next((p for p in _FONT_BOLD_CANDIDATES if Path(p).exists()), _FR)


# ── Paleta ──────────────────────────────────────────────────────────────────
AZUL      = (45, 65, 180)
ROJO_UE   = (255, 50, 40)
VERDE     = (20, 147, 90)
AMBAR     = (199, 119, 0)
ROJO      = (217, 45, 32)
GRIS_OSC  = (30, 30, 30)
GRIS_MED  = (107, 114, 128)
GRIS_CLAR = (244, 246, 250)
BLANCO    = (255, 255, 255)
BORDE     = (221, 226, 240)


class PDF(FPDF):
    F = "Arial" if _FR else "Helvetica"

    def setup_fonts(self):
        if _FR:
            self.add_font("Arial", "", _FR)
            self.add_font("Arial", "B", _FB if _FB else _FR)

    # ── Encabezado de página ────────────────────────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font(self.F, "", 7.5)
        self.set_text_color(*GRIS_MED)
        self.cell(0, 8, "IntApp v2  ·  Manual explicativo del sistema", align="L")
        self.cell(0, 8, f"Pág. {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BORDE)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    # ── Pie de página ───────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*BORDE)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font(self.F, "", 7)
        self.set_text_color(*GRIS_MED)
        self.cell(0, 5,
            "Herramienta de apoyo a la decisión clínica. No sustituye el criterio del profesional sanitario.  "
            f"Universidad Europea · TFM Roberto Franco · v2.3 · {datetime.now().strftime('%B %Y')}",
            align="C")

    # ── Título de sección ───────────────────────────────────────────────────
    def seccion(self, numero: str, titulo: str):
        self.ln(4)
        self.set_fill_color(*AZUL)
        self.set_text_color(*BLANCO)
        self.set_font(self.F, "B", 11)
        self.cell(0, 9, f"  {numero}  {titulo}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)
        self.set_text_color(*GRIS_OSC)

    # ── Subtítulo ───────────────────────────────────────────────────────────
    def subtitulo(self, texto: str):
        self.ln(2)
        self.set_font(self.F, "B", 9.5)
        self.set_text_color(*AZUL)
        self.cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*GRIS_OSC)

    # ── Párrafo normal ──────────────────────────────────────────────────────
    def parrafo(self, texto: str, indent: float = 0):
        self.set_font(self.F, "", 9)
        self.set_text_color(*GRIS_OSC)
        w = self.w - self.l_margin - self.r_margin - indent
        self.set_x(self.l_margin + indent)
        self.multi_cell(w, 5.2, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    # ── Viñeta ──────────────────────────────────────────────────────────────
    def vineta(self, texto: str, color_punto=AZUL, indent: float = 4):
        self.set_xy(self.l_margin + indent, self.get_y())
        self.set_font(self.F, "B", 9)
        self.set_text_color(*color_punto)
        self.cell(5, 5.5, "•")
        self.set_font(self.F, "", 9)
        self.set_text_color(*GRIS_OSC)
        w = self.w - self.l_margin - self.r_margin - indent - 5
        self.multi_cell(w, 5.5, texto, new_x="LMARGIN", new_y="NEXT")

    # ── Caja de aviso ───────────────────────────────────────────────────────
    def caja_aviso(self, texto: str, color_fondo=(255, 248, 230), color_borde=(199, 119, 0)):
        self.ln(2)
        self.set_fill_color(*color_fondo)
        self.set_draw_color(*color_borde)
        self.set_line_width(0.5)
        self.set_font(self.F, "", 8.5)
        self.set_text_color(*GRIS_OSC)
        self.set_x(self.l_margin)
        w = self.w - self.l_margin - self.r_margin
        self.multi_cell(w, 5.2, texto, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_line_width(0.2)

    # ── Fila de tabla ───────────────────────────────────────────────────────
    def fila_tabla(self, col1: str, col2: str, fondo: tuple = BLANCO):
        self.set_x(self.l_margin)
        self.set_fill_color(*fondo)
        self.set_font(self.F, "B", 8.5)
        self.set_text_color(*GRIS_OSC)
        self.cell(58, 6.5, f"  {col1}", fill=True)
        self.set_font(self.F, "", 8.5)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 58, 6.5, col2, fill=True,
                        new_x="LMARGIN", new_y="NEXT")

    # ── Caja de resultado (semáforo) ─────────────────────────────────────────
    def caja_resultado(self, nivel: str, color_fondo: tuple, color_texto: tuple, descripcion: str):
        self.set_x(self.l_margin)
        self.set_fill_color(*color_fondo)
        self.set_text_color(*color_texto)
        self.set_font(self.F, "B", 10)
        self.cell(45, 9, f"  {nivel.upper()}", fill=True)
        self.set_fill_color(*BLANCO)
        self.set_text_color(*GRIS_OSC)
        self.set_font(self.F, "", 8.5)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 45, 9, f"  {descripcion}", fill=True,
                        new_x="LMARGIN", new_y="NEXT")


def build_pdf() -> PDF:
    pdf = PDF()
    pdf.setup_fonts()
    pdf.set_margins(18, 22, 18)
    pdf.set_auto_page_break(auto=True, margin=22)

    # ════════════════════════════════════════════════════════════════════════
    # PORTADA
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Franja superior azul
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 210, 52, style="F")
    pdf.set_fill_color(*ROJO_UE)
    pdf.rect(0, 52, 210, 4, style="F")

    # Logo
    if LOGO.exists():
        pdf.image(str(LOGO), x=15, y=10, h=28)

    # Título
    pdf.set_text_color(*BLANCO)
    pdf.set_font(pdf.F, "B", 22)
    pdf.set_xy(15, 62)
    pdf.cell(0, 12, "IntApp v2")
    pdf.set_font(pdf.F, "", 13)
    pdf.set_xy(15, 75)
    pdf.cell(0, 8, "Manual explicativo del sistema de evaluación de riesgo de lesión")
    pdf.set_font(pdf.F, "", 9.5)
    pdf.set_text_color(*GRIS_MED)
    pdf.set_xy(15, 86)
    pdf.cell(0, 6, "Herramienta de apoyo a la decisión clínica para el miembro inferior")

    # Bloque de info
    pdf.set_fill_color(*GRIS_CLAR)
    pdf.set_draw_color(*BORDE)
    pdf.set_line_width(0.3)
    pdf.rect(15, 100, 180, 46, style="FD")
    pdf.set_text_color(*GRIS_OSC)
    pdf.set_font(pdf.F, "B", 9)
    pdf.set_xy(20, 105)
    pdf.cell(0, 6, "Proyecto")
    pdf.set_font(pdf.F, "", 9)
    pdf.set_xy(20, 111)
    pdf.cell(0, 5.5, "TFM — Máster en Inteligencia Artificial aplicada al Deporte")
    pdf.set_xy(20, 117)
    pdf.cell(0, 5.5, "Universidad Europea de Madrid")
    pdf.set_xy(20, 123)
    pdf.cell(0, 5.5, f"Autor: Roberto Franco Yagüe  ·  Versión 2.3  ·  {datetime.now().strftime('%B %Y')}")
    pdf.set_xy(20, 133)
    pdf.set_font(pdf.F, "", 8)
    pdf.set_text_color(*GRIS_MED)
    pdf.cell(0, 5, "Este documento describe el funcionamiento completo de la aplicación "
                   "de manera accesible para cualquier lector.")

    # Nota de uso
    pdf.set_xy(15, 155)
    pdf.set_fill_color(232, 236, 252)
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.5)
    pdf.rect(15, 155, 180, 24, style="FD")
    pdf.set_font(pdf.F, "B", 8.5)
    pdf.set_text_color(*AZUL)
    pdf.set_xy(19, 159)
    pdf.cell(0, 5.5, "Aviso importante")
    pdf.set_font(pdf.F, "", 8.5)
    pdf.set_text_color(*GRIS_OSC)
    pdf.set_xy(19, 165)
    pdf.multi_cell(172, 5,
        "IntApp es una herramienta de apoyo a la decisión clínica. El resultado que ofrece "
        "es una estimación probabilística basada en un modelo de aprendizaje automático entrenado "
        "con datos sintéticos. No sustituye en ningún caso el criterio del fisioterapeuta o "
        "del médico responsable del deportista.")

    # ════════════════════════════════════════════════════════════════════════
    # ÍNDICE
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("", "Índice de contenidos")
    secciones_idx = [
        ("1", "¿Qué es IntApp y para qué sirve?"),
        ("2", "Visión general del flujo de la aplicación"),
        ("3", "Paso 1 — Cuestionario del deportista"),
        ("  3.1", "Dolor percibido (Escala NRS)"),
        ("  3.2", "Datos demográficos"),
        ("  3.3", "Nivel de actividad deportiva"),
        ("  3.4", "Historial lesional"),
        ("  3.5", "Hooper Wellbeing Index"),
        ("4", "Paso 2 — Evaluación física"),
        ("  4.1", "Fuerza muscular"),
        ("  4.2", "Movilidad articular"),
        ("  4.3", "Control neuromuscular"),
        ("5", "Cómo procesa los datos el sistema (sin fórmulas complejas)"),
        ("  5.1", "Normalización por peso corporal (N/kg)"),
        ("  5.2", "Ajuste normativo por perfil del deportista"),
        ("  5.3", "Ratios clínicos — H:Q y ADD/ABD"),
        ("  5.4", "Asimetrías bilaterales"),
        ("6", "El modelo de inteligencia artificial"),
        ("7", "Interpretación del resultado"),
        ("  7.1", "Semáforo de riesgo"),
        ("  7.2", "Probabilidades por clase"),
        ("  7.3", "Variables más influyentes"),
        ("  7.4", "Banderas fuera de rango"),
        ("  7.5", "Explicación individual SHAP"),
        ("  7.6", "Informe PDF"),
        ("8", "Limitaciones del sistema"),
    ]
    for num, txt in secciones_idx:
        pdf.set_font(pdf.F, "B" if not num.startswith(" ") else "", 9)
        pdf.set_text_color(*GRIS_OSC if not num.startswith(" ") else GRIS_MED)
        pdf.cell(18, 6, num)
        pdf.set_font(pdf.F, "", 9)
        pdf.set_text_color(*GRIS_OSC)
        pdf.cell(0, 6, txt, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — QUÉ ES INTAPP
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("1", "¿Qué es IntApp y para qué sirve?")

    pdf.parrafo(
        "IntApp (Injury Prevention Tool Application) es una aplicación web desarrollada como "
        "Trabajo de Fin de Máster en la Universidad Europea de Madrid. Su objetivo es ayudar "
        "al fisioterapeuta o preparador físico a identificar, de forma rápida y objetiva, "
        "qué deportistas tienen mayor probabilidad de sufrir una lesión musculoesquelética "
        "en el miembro inferior."
    )
    pdf.parrafo(
        "La herramienta combina información recogida al deportista (cómo se encuentra, "
        "sus datos personales y su historial) con mediciones físicas realizadas por el profesional "
        "(fuerza muscular, movilidad articular y control neuromuscular). Con todo ello, "
        "un modelo de inteligencia artificial (IA) calcula la probabilidad de que el deportista "
        "pertenezca a una de estas tres categorías:"
    )
    pdf.vineta("Riesgo BAJO — puede continuar su programa habitual.", VERDE)
    pdf.vineta("Riesgo MEDIO — se recomienda revisar los factores de riesgo identificados.", AMBAR)
    pdf.vineta("Riesgo ALTO — se recomienda intervención prioritaria.", ROJO)
    pdf.ln(3)
    pdf.caja_aviso(
        "IMPORTANTE: El resultado que ofrece IntApp es una estimación probabilística, no un diagnóstico médico. "
        "El profesional sanitario debe interpretar el resultado en el contexto clínico de cada deportista.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("¿A quién va dirigido?")
    pdf.parrafo(
        "El profesional que usa la aplicación (fisioterapeuta, preparador físico, médico deportivo) "
        "tiene dos roles diferenciados durante la sesión de evaluación:"
    )
    pdf.vineta("Deja el dispositivo al deportista para que complete el cuestionario inicial (Paso 1).")
    pdf.vineta("Toma él mismo las mediciones físicas e introduce los datos en la aplicación (Paso 2).")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — FLUJO GENERAL
    # ════════════════════════════════════════════════════════════════════════
    pdf.seccion("2", "Visión general del flujo de la aplicación")
    pdf.parrafo(
        "La evaluación se realiza en tres etapas secuenciales. El deportista no puede saltar ninguna "
        "de ellas — la aplicación guía el proceso paso a paso:"
    )

    pasos = [
        ("Pantalla de inicio (Splash)",
         "El profesional abre la aplicación y pulsa 'Iniciar evaluación'. Es la pantalla de bienvenida "
         "con el nombre del proyecto y la institución."),
        ("Paso 1 — Cuestionario del deportista",
         "El deportista responde preguntas sobre su dolor actual, sus datos personales, nivel de actividad, "
         "lesiones previas y bienestar general. Cada pregunta incluye instrucciones claras sobre cómo responder. "
         "Al finalizar, pulsa 'Continuar a la evaluación'."),
        ("Paso 2 — Evaluación física",
         "El profesional introduce las mediciones de fuerza, movilidad y control neuromuscular. "
         "Los datos del cuestionario del Paso 1 aparecen en una tarjeta resumen en la parte superior. "
         "Al terminar, pulsa 'Calcular riesgo'."),
        ("Resultado",
         "La IA analiza todos los datos y muestra el nivel de riesgo (semáforo), las probabilidades "
         "por cada categoría, las variables que más han influido en el resultado y las variables "
         "fuera de los rangos de referencia. Se puede descargar un informe en PDF."),
    ]
    for i, (titulo_paso, desc) in enumerate(pasos, 0):
        pdf.set_fill_color(*GRIS_CLAR)
        pdf.set_draw_color(*BORDE)
        pdf.set_line_width(0.3)
        y0 = pdf.get_y()
        # Número de paso
        if i > 0:
            pdf.set_fill_color(*AZUL)
            pdf.set_text_color(*BLANCO)
            pdf.set_font(pdf.F, "B", 10)
            pdf.cell(9, 9, str(i), fill=True, align="C")
        else:
            pdf.set_fill_color(*GRIS_MED)
            pdf.set_text_color(*BLANCO)
            pdf.set_font(pdf.F, "B", 8)
            pdf.cell(9, 9, "0", fill=True, align="C")
        pdf.set_fill_color(*GRIS_CLAR)
        pdf.set_text_color(*AZUL if i > 0 else GRIS_MED)
        pdf.set_font(pdf.F, "B", 9)
        pdf.cell(55, 9, f"  {titulo_paso}", fill=True)
        pdf.set_text_color(*GRIS_OSC)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 64, 9, f"  {desc}", fill=True,
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.ln(2)
    pdf.caja_aviso(
        "Nota sobre el dolor: si el deportista indica un dolor percibido superior a 5 sobre 10, "
        "la aplicación muestra automáticamente un aviso de 'evaluación no concluyente' y recomienda "
        "valoración presencial antes de continuar. El modelo no calcula el riesgo en ese caso.",
        color_fondo=(253, 240, 239), color_borde=ROJO
    )

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — CUESTIONARIO PACIENTE
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("3", "Paso 1 — Cuestionario del deportista")
    pdf.parrafo(
        "El deportista completa este formulario de forma autónoma. Contiene 7 variables agrupadas "
        "en cuatro bloques. El sistema muestra instrucciones junto a cada pregunta para facilitar "
        "una respuesta correcta."
    )

    pdf.subtitulo("3.1  Dolor percibido — Escala NRS (Numeric Rating Scale)")
    pdf.parrafo(
        "Es lo primero que el deportista ve. Se le pide que mueva un deslizador de 0 a 10 según "
        "el dolor que siente en este momento en el miembro inferior:"
    )
    pdf.vineta("0 — Sin ningún dolor.")
    pdf.vineta("1-3 — Dolor leve: molestia presente pero no limita las actividades.")
    pdf.vineta("4-6 — Dolor moderado: limita parcialmente el movimiento o el deporte.")
    pdf.vineta("7-10 — Dolor severo: impide realizar actividades con normalidad.")
    pdf.ln(2)
    pdf.caja_aviso(
        "Si el resultado es mayor de 5, la aplicación bloquea el cálculo automático y recomienda "
        "valoración presencial. Un dolor agudo activo hace que los resultados de las pruebas físicas "
        "no sean representativos del estado real del deportista.",
        color_fondo=(253, 240, 239), color_borde=ROJO
    )

    pdf.subtitulo("3.2  Datos demográficos")
    pdf.parrafo("Se recogen tres datos básicos del deportista:")
    filas_dem = [
        ("Edad", "Años cumplidos. El sistema tiene tablas de referencia distintas para tres grupos: "
                 "18-35 años, 36-50 años y 51-65 años. Lo que es normal en un deportista joven no "
                 "lo es necesariamente en uno de 55 años."),
        ("Género", "Masculino o Femenino. Los valores de referencia de fuerza muscular difieren "
                   "significativamente entre géneros según la literatura científica."),
        ("Peso corporal (kg)", "Necesario para calcular la fuerza relativa (N/kg). "
                               "Ver apartado 5.1 para más detalle."),
    ]
    for col1, col2 in filas_dem:
        pdf.fila_tabla(col1, col2, GRIS_CLAR)
        pdf.fila_tabla("", "", BLANCO)

    pdf.subtitulo("3.3  Nivel de actividad deportiva")
    pdf.parrafo(
        "El deportista elige la opción que mejor describe su práctica habitual. "
        "Este dato es crucial porque el sistema ajusta los umbrales de referencia de la "
        "fuerza muscular según el nivel de exigencia del deportista:"
    )
    niveles = [
        ("Sedentario", "Menos de 150 min/semana sin pauta estructurada.", "Factor 0.85"),
        ("Recreacional", "150-300 min/semana, práctica habitual sin competición.", "Factor 1.00 (referencia)"),
        ("Activo", "Más de 300 min/semana o competición amateur federada.", "Factor 1.15"),
        ("Elite", "Deporte de alto rendimiento o competición profesional.", "Factor 1.30"),
    ]
    for nivel, desc, factor in niveles:
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*AZUL)
        pdf.cell(30, 6, nivel)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        pdf.cell(110, 6, desc)
        pdf.set_font(pdf.F, "", 8)
        pdf.set_text_color(*GRIS_MED)
        pdf.cell(0, 6, factor, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.caja_aviso(
        "Ejemplo: un umbral de cuádriceps de 4.0 N/kg para un hombre de 25 años recreacional "
        "sube a 5.2 N/kg si ese mismo hombre es elite. La misma medición de 4.5 N/kg sería "
        "aceptable en uno y deficitaria en el otro.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("3.4  Historial lesional")
    pdf.parrafo(
        "El deportista indica cuántas lesiones musculoesqueléticas ha sufrido en los últimos "
        "12 meses que hayan requerido al menos 3 días de baja deportiva (esguinces, roturas "
        "musculares, tendinopatías, etc.). La escala es numérica: 0, 1, 2, 3 o más."
    )
    pdf.parrafo(
        "Este dato tiene un peso significativo en el modelo (es la 4.ª variable más importante "
        "de las 56 del sistema). Un historial previo de lesiones es uno de los predictores más "
        "consistentes en la literatura científica de prevención de lesiones deportivas."
    )

    pdf.subtitulo("3.5  Hooper Wellbeing Index")
    pdf.parrafo(
        "El Hooper Wellbeing Index (HWI) es un cuestionario validado científicamente que mide "
        "el estado de recuperación del deportista. Se compone de 4 preguntas, cada una puntuada "
        "del 1 al 7. La puntuación total oscila entre 4 (estado óptimo) y 28 (estado muy deteriorado):"
    )
    preguntas_hooper = [
        ("Calidad del sueño", "1 = muy buena, sin interrupciones · 7 = muy mala, casi sin dormir"),
        ("Nivel de estrés", "1 = muy relajado, sin preocupaciones · 7 = muy estresado"),
        ("Fatiga general", "1 = totalmente descansado · 7 = agotado, sin energía"),
        ("Dolor muscular", "1 = sin dolor · 7 = dolor intenso que limita el movimiento"),
    ]
    for preg, ayuda in preguntas_hooper:
        pdf.vineta(f"{preg}: {ayuda}")
    pdf.ln(2)
    pdf.parrafo(
        "Interpretación de la puntuación total: ≤12 = estado óptimo (verde); "
        "13-18 = estado moderado, revisar recuperación (amarillo); "
        ">18 = sobrecarga o fatiga acumulada, precaución (rojo)."
    )

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4 — EVALUACIÓN FÍSICA
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("4", "Paso 2 — Evaluación física")
    pdf.parrafo(
        "El profesional realiza los tests físicos al deportista e introduce los resultados "
        "en la aplicación. Las mediciones se organizan en tres pestañas (bloques). "
        "Para cada variable, la aplicación muestra un número editable y una barra deslizante "
        "sincronizados entre sí. Además, un botón 'Protocolo' junto a cada test despliega "
        "los pasos de ejecución para garantizar la consistencia de la medición."
    )
    pdf.parrafo(
        "En la parte superior de la pantalla aparece una tarjeta de resumen con los datos "
        "del cuestionario del Paso 1 (edad, género, peso, nivel de actividad, NRS, lesiones previas) "
        "para que el profesional pueda verificarlos antes de continuar."
    )

    pdf.subtitulo("4.1  Fuerza muscular (dinamómetro manual)")
    pdf.parrafo(
        "Se miden 5 grupos musculares, en ambos lados del cuerpo (derecho e izquierdo), "
        "con un dinamómetro de mano (HHD). Los valores se introducen en Newtons (N). "
        "El sistema los convierte automáticamente a N/kg (fuerza relativa al peso corporal) "
        "y a un índice normalizado respecto al perfil del deportista:"
    )
    grupos_fuerza = [
        ("Cuádriceps", "Extensión de rodilla isométrica a 90° de flexión. Principal estabilizador anterior de la rodilla."),
        ("Isquiotibiales", "Flexión de rodilla isométrica. Protegen el ligamento cruzado anterior durante la desaceleración."),
        ("Glúteo medio", "Abducción de cadera. Controla el valgo de rodilla y la estabilidad pélvica."),
        ("Rotadores externos de cadera", "Rotación externa isométrica. Asociados al control del valgo dinámico y lesiones de LCA."),
        ("Aductores de cadera", "Aducción isométrica. El ratio con el glúteo medio es indicador de riesgo inguinal."),
    ]
    for grupo, desc in grupos_fuerza:
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        pdf.cell(5, 5.5, "")
        pdf.set_fill_color(*GRIS_CLAR)
        pdf.cell(52, 5.5, grupo, fill=True)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 57, 5.5, desc, fill=True,
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.parrafo(
        "Además de la fuerza de cada músculo, el sistema calcula automáticamente el número de "
        "repeticiones de elevación de talón en el test de tríceps sural (gemelos), que en lugar "
        "de Newtons se mide en repeticiones máximas."
    )

    pdf.subtitulo("4.2  Movilidad articular (goniómetro / inclinómetro)")
    pdf.parrafo("Se evalúan tres tests de movilidad:")
    tests_movil = [
        ("Dorsiflexión de tobillo · WBLT",
         "El deportista apoya la rodilla en la pared (Wall Bear Lunge Test). Se mide la distancia "
         "en cm entre el dedo gordo y la pared. Un valor bajo indica rigidez del tríceps sural "
         "y Aquiles, asociada a tendinopatías y lesiones de tobillo. Se evalúa en ambos lados."),
        ("Test de Thomas",
         "Prueba de extensibilidad del psoas ilíaco y recto femoral. El deportista se tumba "
         "boca arriba y flexiona una rodilla al pecho; el resultado es binario: "
         "negativo (sin acortamiento) o positivo (acortamiento detectado). "
         "Se registra para cada lado."),
        ("Rotación interna de cadera",
         "Goniómetro con el deportista en decúbito prono, rodilla a 90°. Mide el rango "
         "de movimiento en grados. Déficit de rotación interna se asocia con mayor riesgo "
         "de lesión de LCA y cadera. Se evalúa en ambos lados."),
    ]
    for test, desc in tests_movil:
        pdf.vineta(f"{test}: {desc}")
        pdf.ln(1)

    pdf.subtitulo("4.3  Control neuromuscular (tests funcionales)")
    tests_control = [
        ("Y-Balance Test · Score Compuesto (YBT-CS)",
         "El deportista se pone sobre un solo pie y alcanza con el otro hacia tres direcciones: "
         "anterior (A), posteromedial (PM) y posterolateral (PL). La aplicación calcula "
         "automáticamente el Score Compuesto: CS% = (A + PM + PL) / (3 × longitud del miembro) × 100. "
         "Un CS% < 89% se considera factor de riesgo. Se evalúa en ambos lados."),
        ("Single-Leg Squat · Valgo dinámico",
         "El deportista realiza una sentadilla a una pierna. El profesional observa y puntúa "
         "el valgo de rodilla en escala 0-3: 0 = sin valgo, 1 = leve, 2 = moderado, 3 = severo. "
         "El valgo dinámico refleja déficit de control neuromuscular y es predictor de lesión de LCA."),
        ("Single-Leg Hop · Distancia",
         "El deportista salta a una pierna lo más lejos posible y aterriza sobre la misma pierna. "
         "Se mide la distancia en cm. Mide la potencia excéntrica y el control de aterrizaje. "
         "Se calcula el Limb Symmetry Index (LSI) entre ambos lados."),
    ]
    for test, desc in tests_control:
        pdf.vineta(f"{test}: {desc}")
        pdf.ln(1)

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5 — PROCESAMIENTO DE DATOS
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("5", "Cómo procesa los datos el sistema (sin fórmulas complejas)")
    pdf.parrafo(
        "Antes de que el modelo de IA analice los datos, el sistema realiza una serie de "
        "transformaciones automáticas para que la información sea comparable entre deportistas "
        "de distintas características. Este proceso tiene 4 pasos principales:"
    )

    pdf.subtitulo("5.1  Normalización por peso corporal (N/kg)")
    pdf.parrafo(
        "La fuerza muscular bruta medida con el dinamómetro depende del tamaño del deportista. "
        "Una fuerza de 300 N en un deportista de 60 kg es muy diferente a 300 N en uno de 100 kg. "
        "Por eso, el sistema divide cada valor de fuerza entre el peso corporal del deportista, "
        "obteniendo un valor en N/kg (Newtons por kilogramo)."
    )
    pdf.caja_aviso(
        "Ejemplo: Un cuádriceps que genera 280 N en un deportista de 70 kg equivale a 4.0 N/kg. "
        "El mismo dato en un deportista de 100 kg sería 2.8 N/kg — más bajo, aunque la fuerza "
        "absoluta fuera idéntica. Usar N/kg permite comparar a cualquier deportista con las tablas "
        "de referencia de la literatura científica.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("5.2  Ajuste normativo por perfil del deportista")
    pdf.parrafo(
        "Este es el ajuste más importante del sistema. Una vez que se tiene el valor en N/kg, "
        "el sistema calcula cuánto se desvía ese valor respecto a lo que se espera para ese "
        "deportista concreto, teniendo en cuenta su edad, su género y su nivel de actividad. "
        "El resultado es un 'índice de referencia' (ratio normativo):"
    )
    pdf.parrafo("     Índice = valor del deportista (N/kg) ÷ umbral de referencia para su perfil")
    pdf.ln(1)
    pdf.parrafo(
        "Los umbrales de referencia están extraídos de la literatura científica y organizados "
        "en tablas por género (masculino/femenino) y grupo de edad (18-35, 36-50, 51-65 años). "
        "Sobre ese umbral base se aplica un factor de actividad:"
    )
    pdf.vineta("Índice = 1.0 → el deportista está exactamente en su umbral de referencia.")
    pdf.vineta("Índice < 1.0 → déficit (por debajo de lo esperado para su perfil).")
    pdf.vineta("Índice > 1.0 → por encima de la referencia de su grupo.")
    pdf.ln(2)
    pdf.caja_aviso(
        "Ejemplo concreto: 3.0 N/kg en cuádriceps.\n"
        "• Hombre, 25 años, elite → umbral = 5.2 N/kg → índice = 0.58 → DÉFICIT SEVERO.\n"
        "• Mujer, 55 años, sedentaria → umbral = 2.04 N/kg → índice = 1.47 → POR ENCIMA DE REFERENCIA.\n"
        "Gracias a este ajuste, el modelo trata de forma justa a deportistas con perfiles muy distintos.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("5.3  Ratios clínicos — H:Q y ADD/ABD")
    pdf.parrafo(
        "Además de los valores individuales, el sistema calcula dos ratios entre músculos "
        "antagonistas que son predictores clásicos en la literatura de lesiones deportivas:"
    )
    pdf.vineta(
        "Ratio H:Q (Hamstring:Quadriceps): isquiotibiales ÷ cuádriceps. "
        "Un valor menor de 0.60 indica que el cuádriceps domina excesivamente sobre los "
        "isquiotibiales, lo que aumenta el riesgo de lesión de ligamento cruzado anterior (LCA)."
    )
    pdf.vineta(
        "Ratio ADD/ABD (aductores ÷ glúteo medio): "
        "Un valor bajo indica debilidad relativa de los aductores respecto al glúteo medio, "
        "asociada a mayor riesgo de lesión inguinal."
    )
    pdf.parrafo("Ambos ratios se calculan para el lado derecho y el lado izquierdo por separado.")

    pdf.subtitulo("5.4  Asimetrías bilaterales")
    pdf.parrafo(
        "Para cada par de mediciones (lado derecho / lado izquierdo), el sistema calcula "
        "automáticamente el porcentaje de asimetría:"
    )
    pdf.parrafo("     Asimetría (%) = |valor derecho − valor izquierdo| ÷ máximo de ambos × 100")
    pdf.ln(1)
    pdf.parrafo(
        "Una asimetría entre el 10% y el 15% se considera un factor de riesgo según la literatura. "
        "El sistema calcula estas asimetrías para todas las variables bilaterales: fuerza muscular, "
        "movilidad y tests funcionales."
    )
    pdf.caja_aviso(
        "En total, a partir de las 19 variables originales introducidas por el profesional, "
        "el sistema genera 56 features (características) que el modelo de IA analiza: "
        "valores N/kg, índices normativos por perfil, ratios clínicos y asimetrías bilaterales.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 6 — EL MODELO DE IA
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("6", "El modelo de inteligencia artificial")

    pdf.parrafo(
        "IntApp utiliza un modelo de aprendizaje automático denominado Gradient Boosting "
        "(potenciación de gradiente), que es uno de los algoritmos más precisos y robustos "
        "para problemas de clasificación con variables mixtas como las de este sistema."
    )

    pdf.subtitulo("¿Cómo aprende el modelo?")
    pdf.parrafo(
        "El modelo se entrenó con un dataset de 5.000 evaluaciones sintéticas generadas a "
        "partir de distribuciones estadísticas basadas en la literatura clínica. Aunque los datos "
        "son sintéticos, se diseñaron para reproducir fielmente las distribuciones y correlaciones "
        "observadas en deportistas reales. Durante el entrenamiento, el modelo aprendió a asociar "
        "combinaciones de valores (fuerza, movilidad, control, perfil) con el nivel de riesgo."
    )

    pdf.subtitulo("Calibración del umbral de decisión")
    pdf.parrafo(
        "En un modelo clínico, es más grave no detectar a alguien de alto riesgo (falso negativo) "
        "que clasificar erróneamente a alguien de bajo riesgo como medio (falso positivo). "
        "Por eso, el sistema utiliza un umbral de decisión reducido para la clase 'alto': "
        "clasifica a un deportista como 'alto riesgo' si la probabilidad calculada supera el 12%, "
        "en lugar del 50% estándar. Esto tiene un coste:"
    )
    pdf.vineta("Recall clase 'alto' (capacidad de detectar los casos realmente de riesgo): 96.1%.", VERDE)
    pdf.vineta("Falsos negativos (casos de alto riesgo clasificados como bajo): 1.0% (4 de cada 420).", VERDE)
    pdf.vineta("Precio a pagar: la precisión para la clase 'alto' baja del 91% al 82%.", AMBAR)

    pdf.subtitulo("Métricas de rendimiento del modelo (test set, n = 1.000 deportistas)")
    metricas = [
        ("Accuracy global", "86.6%", "El modelo acierta la categoría correcta en el 86.6% de los casos."),
        ("F1-score macro", "0.87", "Media de precisión y recall equilibrada entre las tres clases."),
        ("Recall clase 'alto'", "96.1%", "De cada 100 casos de alto riesgo, el modelo detecta 96."),
        ("Recall clase 'medio'", "65.8%", "La categoría 'medio' es la más difícil de predecir."),
        ("Validación cruzada 5-fold", "0.873 ± 0.013", "El modelo es estable: rendimiento consistente en diferentes subsets."),
        ("AUC-ROC macro", "~0.94", "Excelente capacidad discriminativa entre las tres categorías."),
    ]
    alt = False
    for m, v, e in metricas:
        fondo = GRIS_CLAR if not alt else BLANCO
        pdf.set_fill_color(*fondo)
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        pdf.cell(62, 6.5, m, fill=True)
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*AZUL)
        pdf.cell(25, 6.5, v, fill=True)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 87, 6.5, e, fill=True,
                       new_x="LMARGIN", new_y="NEXT")
        alt = not alt

    pdf.subtitulo("Variables más importantes para el modelo")
    pdf.parrafo(
        "El modelo aprendió que estas son las características más determinantes para predecir "
        "el nivel de riesgo (en orden de importancia):"
    )
    top_vars = [
        ("1", "Fuerza de cuádriceps (bilateral)", "19% del poder predictivo del modelo."),
        ("2", "Fuerza de isquiotibiales (bilateral)", "~12%, segundo grupo más determinante."),
        ("3", "Historial lesional", "5.8% — una lesión previa es señal de riesgo individual."),
        ("4", "Nivel de actividad", "5.4% — ajusta el nivel de exigencia esperado."),
        ("5", "Rotadores externos de cadera (bilateral)", "~8%"),
        ("6", "Single-leg squat valgo dinámico (bilateral)", "~8% — control neuromuscular."),
        ("7", "Glúteo medio (bilateral)", "~7%"),
    ]
    for rank, var, nota in top_vars:
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*AZUL)
        pdf.cell(6, 5.5, rank + ".")
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        pdf.cell(78, 5.5, var)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 84, 5.5, nota,
                       new_x="LMARGIN", new_y="NEXT")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 7 — INTERPRETACIÓN DEL RESULTADO
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("7", "Interpretación del resultado")
    pdf.parrafo(
        "Tras pulsar 'Calcular riesgo', la aplicación muestra el resultado en varios formatos "
        "complementarios. A continuación se explica cada uno:"
    )

    pdf.subtitulo("7.1  Semáforo de riesgo")
    pdf.parrafo("El resultado principal se muestra como un semáforo de tres colores:")
    pdf.caja_resultado("RIESGO BAJO", VERDE, BLANCO,
        "El deportista puede continuar con su programa habitual. No se han detectado factores "
        "de riesgo significativos en el perfil analizado.")
    pdf.ln(1)
    pdf.caja_resultado("RIESGO MEDIO", AMBAR, BLANCO,
        "Se recomienda revisar los factores de riesgo identificados. El profesional debe valorar "
        "si alguna de las banderas detectadas requiere intervención preventiva.")
    pdf.ln(1)
    pdf.caja_resultado("RIESGO ALTO", ROJO, BLANCO,
        "Se recomienda intervención preventiva prioritaria. El deportista no debería incrementar "
        "la carga de entrenamiento sin antes corregir los déficits identificados.")
    pdf.ln(2)

    pdf.subtitulo("7.2  Probabilidades por clase")
    pdf.parrafo(
        "Junto al semáforo aparecen tres tarjetas con las probabilidades calculadas por el modelo "
        "para cada categoría (Bajo / Medio / Alto). Estos porcentajes representan la confianza "
        "del sistema en cada clasificación."
    )
    pdf.caja_aviso(
        "Ejemplo: Bajo 8% / Medio 21% / Alto 71%. El modelo clasifica al deportista como 'Alto riesgo' "
        "con un 71% de confianza. Cuanto más alto el porcentaje de la clase predicha, más confiable "
        "es el resultado. Una distribución muy uniforme (p.ej. 35%/33%/32%) indica incertidumbre.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("7.3  Variables más influyentes")
    pdf.parrafo(
        "Se muestra una tabla con las 10 variables que más han contribuido al aprendizaje del modelo "
        "en general (no específicamente para este deportista). Sirve como referencia para entender "
        "qué factores son más relevantes en la predicción del riesgo."
    )

    pdf.subtitulo("7.4  Banderas fuera de rango de referencia")
    pdf.parrafo(
        "El sistema compara cada valor introducido con los rangos de referencia clínicos publicados "
        "en la literatura. Las variables que quedan fuera de ese rango se muestran como 'banderas' "
        "en color rojo. Si todos los valores están dentro del rango, aparece un mensaje verde."
    )
    pdf.parrafo(
        "Estas banderas son independientes del resultado del modelo — un valor puede estar fuera "
        "del rango de referencia de la población general y, aun así, ser adecuado para el perfil "
        "concreto del deportista (por eso existen los índices normativos del apartado 5.2)."
    )

    pdf.subtitulo("7.5  Explicación individual SHAP")
    pdf.parrafo(
        "SHAP (SHapley Additive exPlanations) es un método matemático que descompone la predicción "
        "del modelo para mostrar exactamente qué variables han empujado el riesgo hacia arriba "
        "y cuáles lo han reducido, específicamente para este deportista en concreto."
    )
    pdf.vineta("Barras rojas: la variable ha aumentado el riesgo predicho para este deportista.")
    pdf.vineta("Barras azules: la variable ha reducido el riesgo predicho.")
    pdf.parrafo(
        "Esta información es útil para el profesional porque identifica cuáles son los factores "
        "más urgentes de intervenir en el caso concreto que tiene delante."
    )
    pdf.caja_aviso(
        "Diferencia clave: las 'variables más influyentes' (apartado 7.3) muestran la importancia "
        "del modelo en general; la explicación SHAP muestra qué factores han determinado el resultado "
        "de este deportista específico. Ambas pueden ser distintas.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    pdf.subtitulo("7.6  Informe en PDF")
    pdf.parrafo(
        "El botón 'Descargar informe (PDF)' genera y descarga automáticamente un informe "
        "estructurado que incluye: el nivel de riesgo, las probabilidades por clase, las banderas "
        "detectadas y los valores introducidos de todas las variables. "
        "El informe lleva fecha y hora de generación y puede guardarse en el historial del deportista."
    )

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 8 — LIMITACIONES
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.seccion("8", "Limitaciones del sistema")

    pdf.parrafo(
        "IntApp es una herramienta de investigación y apoyo a la decisión clínica. "
        "Antes de aplicarla en un contexto real, el profesional debe tener en cuenta "
        "las siguientes limitaciones:"
    )

    limitaciones = [
        ("Datos sintéticos",
         "El modelo se entrenó con 5.000 evaluaciones generadas artificialmente mediante "
         "distribuciones estadísticas basadas en la literatura. Aunque el diseño es riguroso, "
         "los datos sintéticos no capturan toda la variabilidad y ruido de los datos clínicos reales. "
         "El rendimiento del modelo puede diferir cuando se aplica a deportistas reales."),
        ("Rango de edad y población",
         "Las tablas normativas cubren adultos de 18 a 65 años. Los resultados para deportistas "
         "fuera de este rango deben interpretarse con cautela."),
        ("Clase 'medio' difícil de predecir",
         "El recall de la clase 'medio' es del 65.8%, inferior a las otras dos clases. "
         "Un resultado de riesgo medio debe interpretarse con especial atención al perfil "
         "clínico completo del deportista."),
        ("No cubre el miembro superior",
         "IntApp está diseñado exclusivamente para la evaluación del miembro inferior. "
         "No incluye variables de hombro, codo, muñeca ni columna."),
        ("No sustituye la exploración clínica completa",
         "Los tests evaluados son una selección de variables con mayor evidencia en la literatura "
         "de prevención de lesiones del miembro inferior. Una evaluación clínica completa puede "
         "incluir otros factores no contemplados por la herramienta."),
        ("Pendiente de validación externa",
         "El modelo no ha sido validado con datos reales de deportistas. La validación externa "
         "es el paso natural siguiente a este TFM para transferir la herramienta al entorno clínico."),
        ("Ausencia de datos longitudinales",
         "El sistema evalúa el estado del deportista en un momento puntual. No incorpora "
         "seguimiento a lo largo del tiempo ni tendencias de evolución."),
    ]

    alt = False
    for titulo_lim, desc_lim in limitaciones:
        fondo = GRIS_CLAR if not alt else BLANCO
        pdf.set_fill_color(*fondo)
        pdf.set_font(pdf.F, "B", 8.5)
        pdf.set_text_color(*GRIS_OSC)
        x0 = pdf.get_x()
        pdf.cell(5, 6, "", fill=True)
        pdf.cell(60, 6, titulo_lim, fill=True)
        pdf.set_font(pdf.F, "", 8.5)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 65, 6, desc_lim, fill=True,
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        alt = not alt

    pdf.ln(4)
    pdf.caja_aviso(
        "Conclusión: IntApp es una herramienta válida para apoyar la toma de decisiones en "
        "programas de prevención de lesiones en el ámbito del deporte y la fisioterapia. "
        "Su valor clínico real dependerá de su validación con datos reales y de la integración "
        "con el criterio experto del profesional sanitario.",
        color_fondo=(232, 236, 252), color_borde=AZUL
    )

    return pdf


if __name__ == "__main__":
    print("Generando PDF...")
    pdf = build_pdf()
    pdf.output(str(SALIDA))
    print(f"PDF guardado en: {SALIDA}")
