"""
variables.py — Definición central de las variables de entrada de IntApp.

Versión 2.2 alineada con el Protocolo de Scoring Clínico v2.2.

Estructura del fichero
----------------------
1. Constantes globales del protocolo: factores de actividad, grupos de edad,
   tablas de umbrales por género y edad para cada variable de fuerza, y
   umbrales del ACWR estratificados por nivel de actividad.

2. Diccionarios por bloque (FUERZA, MOVILIDAD, CONTROL, CONTEXTO) con la
   metadata de cada variable. Las medidas en Newtons se almacenan en N
   (lectura directa del dinamómetro). La normalización a N/kg se realiza
   en `preprocesador.py` y en la función `generar_label` de `generador_datos.py`,
   usando el peso corporal del propio sujeto.

3. Expansión bilateral: las variables marcadas con `bilateral=True` se
   duplican en `_der` y `_izq`. Las variables binarias bilaterales (Thomas)
   también se expanden.

4. Constantes derivadas: VARIABLES (expandido), VARIABLES_ORIGINALES,
   listas de columnas por bloque y total.

Campos por variable
-------------------
- nombre_display:          str        Etiqueta legible para la UI.
- bloque:                  str        "fuerza" | "movilidad" | "control" | "contexto".
- unidad:                  str        Unidad de medida.
- bilateral:               bool       Si se mide en der e izq por separado.
- rango_normal:            tuple      Rango clínicamente aceptable (referencia visual).
- rango_sintetico:         tuple      Rango usado por el generador de datos sintéticos.
- tipo:                    str        "continua" | "ordinal" | "categorica" | "binaria".
- peso_scoring:            int        Peso de la variable en el score ponderado (1-5).
                                      0 = no entra en el score (variables de contexto puro).
                                      Los pesos reflejan el tamaño del efecto en la literatura
                                      de prevención de lesiones (5 = evidencia muy fuerte /
                                      OR > 4; 3 = moderada / OR 2-4; 1-2 = débil / OR < 2).
- aplica_zona_gris:        bool       Si la regla acepta zona gris (±10% del umbral).
- umbral_riesgo_base:      dict|None  Tabla de umbrales por género y grupo de edad
                                      en N/kg, para variables de fuerza estratificadas.
                                      None para variables con umbral universal.
- descripcion:             str        Descripción clínica + referencia bibliográfica.

Cambios v1 → v2.2
-----------------
ELIMINADAS:  triple_hop, rotacion_externa_cadera (movilidad), flexoextension_rodilla,
             ybalance_anterior, ybalance_posteromedial, ybalance_posterolateral,
             thomas_test_iliopsoas + thomas_test_recto_femoral (continuas separadas).
AÑADIDAS:    rotadores_externos_cadera (fuerza, bilateral),
             y_balance_cs (control, bilateral, % longitud miembro),
             thomas_test (movilidad, bilateral, binaria fusionada),
             nivel_actividad (contexto, categórica).
ELIMINADAS v2.3: acwr, pss4, horas_sueno (sustituidas funcionalmente por hooper_index).
ELIMINADAS también: gluteo_mayor, flexores_cadera (fuerza),
             extensibilidad_isquiotibial, extension_primer_dedo (movilidad).
ESTRATIFICACIÓN: cada variable de fuerza incorpora `umbral_riesgo_base` con la
             tabla del protocolo v2.1.
ZONAS GRISES: flag `aplica_zona_gris` para uso en generar_label() del v2.2.

Total de variables originales: 19.  # v2.3: eliminadas acwr, pss4, horas_sueno
"""

# =============================================================================
# CONSTANTES GLOBALES DEL PROTOCOLO v2.2
# =============================================================================

# Factor multiplicador del umbral según el nivel de actividad del sujeto.
# El umbral efectivo de cualquier variable estratificada se calcula como:
#     umbral_efectivo = umbral_base × FACTOR_ACTIVIDAD[nivel]
# Justificación clínica: protocolo v2.1, sección 2.2.
FACTORES_ACTIVIDAD: dict[str, float] = {
    "sedentario":   0.85,
    "recreacional": 1.00,   # nivel de referencia
    "activo":       1.15,
    "elite":        1.30,
}

# Grupos de edad usados en la tabla base de umbrales de fuerza.
# Se aplica el grupo correspondiente; no hay interpolación entre grupos.
GRUPOS_EDAD: list[tuple[int, int]] = [
    (18, 35),
    (36, 50),
    (51, 65),
]


def grupo_edad_clave(edad: float | int) -> str:
    """
    Devuelve la clave del grupo de edad ('18_35', '36_50', '51_65')
    para usar como índice en las tablas `umbral_riesgo_base`.

    Para edades fuera del rango 18-65 se asigna al grupo más cercano.
    """
    if edad < 36:
        return "18_35"
    elif edad < 51:
        return "36_50"
    else:
        return "51_65"


# Umbrales del score ponderado total (protocolo v2.1, sección 1.2).
# El score puede elevar la categoría asignada por reglas, pero nunca reducirla.
# Calibrados para que con la población sintética v2.2 (n=500, semilla=42) la
# distribución resultante sea aproximadamente 50/30/20 (bajo/medio/alto).
SCORE_UMBRAL_ALTO:  int = 26   # ≥ 26 → riesgo alto  (recalibrado v2.3: historial 3→5, y_balance 3→4, rotadores 2→3)
SCORE_UMBRAL_MEDIO: int = 18   # ≥ 18 (y < 26) → riesgo medio si reglas dieron bajo


# Anchura relativa de la zona gris alrededor del umbral efectivo (v2.2 sección 1.1).
# El score acumula peso × ZONA_GRIS_PUNTUACION_PARCIAL cuando el valor cae
# dentro de la franja (umbral × (1-margen), umbral × (1+margen)).
ZONA_GRIS_MARGEN:              float = 0.10
ZONA_GRIS_PUNTUACION_PARCIAL:  float = 0.5


# =============================================================================
# BLOQUE A: FUERZA (N) — Medidas bilaterales con dinamómetro manual
# =============================================================================
# Las mediciones se almacenan en N (lectura del HHD). Los umbrales del protocolo
# están en N/kg; la conversión se hace dividiendo por el peso corporal del sujeto
# en el momento de aplicar la regla. La tabla `umbral_riesgo_base` recoge los
# valores del protocolo v2.1, sección 2.1 (nivel recreacional como referencia).

VARIABLES_FUERZA = {
    "cuadriceps": {
        "nombre_display": "Cuádriceps isométrico",
        "bloque": "fuerza",
        "unidad": "N",
        "bilateral": True,
        "rango_normal": (130, 420),
        "rango_sintetico": (80, 600),
        "tipo": "continua",
        "peso_scoring": 3,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            # Umbrales en N/kg a nivel recreacional (referencia, factor × 1.00).
            # Fuentes: Andrews et al. (1996) y Bohannon (1997) para adultos activos;
            # Owoeye et al. (2024) aporta medias HHD en deportistas universitarios:
            #   Fútbol ♂ 18-24 a: 5.48 N/kg | Baloncesto ♂ 18-24 a: 4.89 N/kg
            #   Baloncesto ♀ 18-24 a: 4.21 N/kg | Fútbol/balonmano ♀ élite: 3.35-3.50 N/kg
            # Los umbrales recreacionales representan aproximadamente el percentil 25
            # de adultos activos no universitarios (inferior a las medias de élite).
            # Factor élite (× 1.30): M_18_35 → 5.2 N/kg ≈ media fútbol universitario.
            "M_18_35": 4.0, "M_36_50": 3.5, "M_51_65": 3.0,
            "F_18_35": 3.2, "F_36_50": 2.8, "F_51_65": 2.4,
            "lsi_min": 0.90,
        },
        "descripcion": (
            "Fuerza isométrica máxima de cuádriceps medida con dinamómetro manual "
            "en sedestación, cadera 90°, rodilla 60° de flexión. "
            "Valores normativos HHD en deportistas universitarios (Owoeye et al., 2024): "
            "fútbol ♂ 5.48 N/kg (IC95%: 4.96-6.00), baloncesto ♂ 4.89 N/kg (4.44-5.33), "
            "baloncesto ♀ 4.21 N/kg (3.54-4.87); primer estudio con HHD de bajo coste "
            "en deportistas. Valores de referencia para adultos activos no atletas: "
            "Andrews et al. (1996) Phys Ther 76:248-259; Bohannon (1997) Arch Phys Med "
            "Rehabil 78:26-32. Valores normativos para mujeres élite (fútbol/balonmano): "
            "3.35-3.50 N/kg (JSCR, 2018, PMC6092090). "
            "Referencia HHD: Owoeye et al. (2024) Int J Exerc Sci 17(4):768-778."
        ),
        "protocolo": (
            "📍 Posición: deportista sentado, cadera 90°, rodilla 60° de flexión.\n"
            "🔧 HHD: cara anterior del tobillo, 2 cm proximal al maléolo medial.\n"
            "🗣 Instrucción: «Empuja hacia adelante tan fuerte como puedas».\n"
            "🔁 3 contracciones isométricas × 5 s; 30 s de descanso entre intentos.\n"
            "📝 Registrar el valor máximo de los 3 intentos (N).\n"
            "⚠ Estabilizar la pelvis con correa o la mano libre del evaluador."
        ),
    },
    "isquiotibiales": {
        "nombre_display": "Isquiotibiales isométrico",
        "bloque": "fuerza",
        "unidad": "N",
        "bilateral": True,
        "rango_normal": (80, 270),
        "rango_sintetico": (50, 400),
        "tipo": "continua",
        "peso_scoring": 3,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            # Umbrales en N/kg a nivel recreacional (referencia, factor × 1.00).
            # Valores normativos HHD (Owoeye et al., 2024):
            #   Fútbol ♂ 18-24 a: media 3.29 N/kg (IC95%: 2.90-3.64)
            #   Baloncesto ♂ 18-24 a: media 2.97 N/kg (2.72-3.21)
            #   Baloncesto ♀ 18-24 a: media 2.48 N/kg (2.15-2.80)
            # Ratio H:Q en HHD isométrico: PRECAUCIÓN DE SENSIBILIDAD.
            # Owoeye (2024) encontró H:Q < 0.60 en el 37% (fútbol) y 44%
            # (baloncesto) de deportistas universitarios SANOS. El umbral 0.60
            # procede de isocinético (Croisier 2008) y puede ser demasiado
            # sensible en isométrico, generando falsos positivos.
            # El lsi_min para isquiotibiales sigue la misma lógica que cuádriceps.
            "M_18_35": 2.5, "M_36_50": 2.2, "M_51_65": 1.8,
            "F_18_35": 2.1, "F_36_50": 1.8, "F_51_65": 1.5,
            "lsi_min": 0.90,
        },
        "descripcion": (
            "Fuerza isométrica máxima de isquiotibiales en decúbito prono, "
            "rodilla 90° de flexión. Valores normativos HHD (Owoeye et al., 2024): "
            "fútbol ♂ media 3.29 N/kg, baloncesto ♂ 2.97 N/kg, baloncesto ♀ 2.48 N/kg. "
            "El ratio H:Q (calculado en preprocesador) predice lesión de isquiotibiales "
            "con umbral < 0.60 (Croisier et al., 2008). LIMITACIÓN: dicho umbral fue "
            "establecido en dinamometría isocinética a 60°/s; en HHD isométrico, Owoeye "
            "(2024) observó H:Q < 0.60 en el 37-44% de deportistas universitarios sanos, "
            "lo que implica alta tasa de falsos positivos con este umbral en isométrico. "
            "Declarar como limitación del protocolo en el TFM. "
            "Referencias: Croisier et al. (2008) Am J Sports Med 36(8):1469-1475; "
            "Owoeye et al. (2024) Int J Exerc Sci 17(4):768-778."
        ),
        "protocolo": (
            "📍 Posición: deportista en decúbito prono, rodilla 90° de flexión.\n"
            "🔧 HHD: cara posterior del tobillo, 2 cm proximal al maléolo lateral.\n"
            "🗣 Instrucción: «Tira del talón hacia el glúteo tan fuerte como puedas».\n"
            "🔁 3 contracciones isométricas × 5 s; 30 s de descanso entre intentos.\n"
            "📝 Registrar el valor máximo de los 3 intentos (N).\n"
            "⚠ Estabilizar el muslo con la mano libre del evaluador."
        ),
    },
    "gluteo_medio": {
        "nombre_display": "Glúteo medio / abductores cadera",
        "bloque": "fuerza",
        "unidad": "N",
        "bilateral": True,
        "rango_normal": (50, 170),
        "rango_sintetico": (40, 320),
        "tipo": "continua",
        "peso_scoring": 3,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            # Umbrales en N/kg a nivel recreacional (referencia, factor × 1.00).
            # NOTA: la literatura normativa reporta valores en Nm/kg (torque),
            # no en N/kg (fuerza). La conversión depende del brazo de momento
            # (posición del HHD respecto al trocánter), lo que introduce incertidumbre.
            # Valores de referencia en Nm/kg (Thorborg et al., 2016, n=deportistas jóvenes):
            #   Voleibol ♂: 1.28 Nm/kg | Voleibol ♀: 1.13 Nm/kg
            #   Grupo 15-19 años (mixto): 1.41 Nm/kg
            # Corredores adultos excéntrico (PMC3924610):
            #   ♂: 1.62 Nm/kg | ♀: 1.41 Nm/kg
            # Los umbrales en N/kg son estimados; pendiente de validación con
            # datos HHD isométrico específicos en N/kg por grupo edad/sexo.
            "M_18_35": 1.5,  "M_36_50": 1.3,  "M_51_65": 1.1,
            "F_18_35": 1.2,  "F_36_50": 1.05, "F_51_65": 0.9,
            "lsi_min": 0.85,
        },
        "descripcion": (
            "Fuerza isométrica de abductores de cadera en decúbito lateral. "
            "Su debilidad se asocia a valgo dinámico de rodilla y dolor patelofemoral. "
            "Valores normativos en Nm/kg (Thorborg et al., 2016): voleibol ♂ 1.28 Nm/kg, "
            "voleibol ♀ 1.13 Nm/kg (grupo 15-19 años); corredores novatos ♂ 1.62 Nm/kg "
            "y ♀ 1.41 Nm/kg (excéntrico, PMC3924610). Los umbrales en N/kg del protocolo "
            "son estimaciones; la literatura normativa usa Nm/kg, lo que introduce "
            "incertidumbre en la comparación directa — declarar como limitación. "
            "Referencias: Powers (2010) JOSPT 40(2):42-51; "
            "Thorborg et al. (2016) Phys Ther Sport 22:1-6 (PubMed 27428529)."
        ),
        "protocolo": (
            "📍 Posición: decúbito lateral, miembro a testar arriba, cadera en neutro (0° abducción).\n"
            "🔧 HHD: cara lateral del muslo, 5 cm proximal al cóndilo femoral lateral.\n"
            "🗣 Instrucción: «Separa la pierna hacia arriba sin rotar la cadera ni la pelvis».\n"
            "🔁 3 contracciones isométricas × 5 s; 30 s de descanso entre intentos.\n"
            "📝 Registrar el valor máximo de los 3 intentos (N).\n"
            "⚠ Estabilizar la pelvis con la mano libre; el evaluador se coloca detrás del deportista."
        ),
    },
    "rotadores_externos_cadera": {
        "nombre_display": "Rotadores externos de cadera",
        "bloque": "fuerza",
        "unidad": "N",
        "bilateral": True,
        "rango_normal": (30, 130),
        "rango_sintetico": (25, 230),
        "tipo": "continua",
        "peso_scoring": 3,   # elevado 2→3: Hollman (2009) umbral HHD directo; Ireland (2003) OR 3.1 ACL
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            # Umbrales en N/kg a nivel recreacional (referencia, factor × 1.00).
            # Hollman et al. (2009, JOSPT) establecieron directamente en HHD isométrico:
            #   Riesgo ACL si < 1.0 N/kg ♂ y < 0.8 N/kg ♀ (protocolo decúbito prono).
            # Valores normativos de deportistas universitarios en Nm/kg (PMC6442714):
            #   Fútbol ♂ dominante: 0.46 Nm/kg | Baloncesto ♂: 0.35 Nm/kg
            #   Voleibol ♀: 0.29 Nm/kg
            # Ireland et al. (2003): riesgo ACL si fuerza < 20.3% del peso corporal
            #   ≈ 0.203 × 9.81 ≈ 2.0 N/kg; diferencia con Hollman posiblemente
            #   atribuible a distintos protocolos de medición — usar Hollman como
            #   referencia primaria al compartir instrumento (HHD) y protocolo.
            "M_18_35": 1.0,  "M_36_50": 0.85, "M_51_65": 0.7,
            "F_18_35": 0.8,  "F_36_50": 0.7,  "F_51_65": 0.55,
            "lsi_min": 0.85,
        },
        "descripcion": (
            "Fuerza isométrica de rotadores externos de cadera en decúbito prono, "
            "rodilla a 90°. Variable nueva en v2.0: complementa al glúteo medio "
            "cubriendo el plano transversal de la cadera. La debilidad se asocia "
            "al valgo dinámico en mujeres con lesión de LCA (OR 3.1, Ireland 2003). "
            "Umbrales directamente establecidos en HHD isométrico por Hollman et al. "
            "(2009): < 1.0 N/kg ♂ y < 0.8 N/kg ♀ como umbral de riesgo ACL. "
            "Valores normativos en Nm/kg de deportistas de equipo (PMC6442714, 2019): "
            "fútbol ♂ 0.46 Nm/kg (dominant), baloncesto ♂ 0.35 Nm/kg, voleibol ♀ "
            "0.29 Nm/kg — no directamente comparables con N/kg sin conocer el "
            "brazo de momento. "
            "Referencias: Ireland et al. (2003) JOSPT 33(11):671-676; "
            "Hollman et al. (2009) JOSPT 39(9):641-648; PMC6442714 (2019)."
        ),
        "protocolo": (
            "📍 Posición: decúbito prono, rodilla 90° de flexión. Pelvis neutra sobre la camilla.\n"
            "🔧 HHD: cara lateral del tobillo (resistencia a la rotación externa del pie).\n"
            "🗣 Instrucción: «Gira el pie hacia fuera empujando contra mi mano, máxima fuerza».\n"
            "🔁 3 contracciones isométricas × 5 s; 30 s de descanso entre intentos.\n"
            "📝 Registrar el valor máximo de los 3 intentos (N).\n"
            "⚠ Estabilizar la pelvis con la mano libre; no permitir rotación de cadera ni compensación lumbar."
        ),
    },
    "aductores_cadera": {
        "nombre_display": "Aductores de cadera",
        "bloque": "fuerza",
        "unidad": "N",
        "bilateral": True,
        "rango_normal": (80, 230),
        "rango_sintetico": (50, 340),
        "tipo": "continua",
        "peso_scoring": 2,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            "M_18_35": 2.2,  "M_36_50": 1.9,  "M_51_65": 1.6,
            "F_18_35": 1.8,  "F_36_50": 1.55, "F_51_65": 1.3,
            "ratio_add_abd_min": 0.90,
        },
        "descripcion": (
            "Fuerza isométrica de aductores de cadera. El ratio ADD/ABD "
            "ipsilateral por debajo de 0.90 se asocia a lesión inguinal. "
            "Valores de referencia en fútbol élite (Thorborg et al., 2011): "
            "aducción excéntrica ICC inter-evaluador 0.91 (HHD). "
            "Fútbol femenino adulto (ScienceDirect 2024, n=504 valoraciones): "
            "torque aducción isométrico ~1.85 Nm/kg (élite) y ~2.40 Nm/kg (semiprofesional). "
            "NOTA: datos de aductores en N/kg para adultos recreacionales son escasos "
            "en la literatura — los umbrales del protocolo son estimaciones derivadas "
            "de la evidencia en poblaciones de fútbol. "
            "Referencia: Thorborg et al. (2011) Am J Sports Med 39:2704-2708."
        ),
        "protocolo": (
            "📍 Posición: decúbito supino, caderas y rodillas extendidas, ligeramente separadas.\n"
            "🔧 HHD: cara medial de la rodilla (sobre el cóndilo femoral medial).\n"
            "🗣 Instrucción: «Aprieta la pierna hacia dentro empujando contra mi mano, máxima fuerza».\n"
            "🔁 3 contracciones isométricas × 5 s; 30 s de descanso entre intentos.\n"
            "📝 Registrar el valor máximo de los 3 intentos (N).\n"
            "⚠ Evaluar un miembro cada vez; el evaluador resiste desde el lado contralateral."
        ),
    },
    "triceps_sural": {
        "nombre_display": "Tríceps sural — Heel rise test",
        "bloque": "fuerza",
        "unidad": "repeticiones",
        "bilateral": True,
        "rango_normal": (18, 40),
        "rango_sintetico": (5, 45),
        "tipo": "continua",
        "peso_scoring": 2,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            # Umbrales en repeticiones (no se normalizan por peso corporal).
            # Fuente primaria: Hébert-Losier et al. (2017, Physiotherapy, ICC=0.96):
            #   Mediana general — dominante: 25 rep, no dominante: 24 rep.
            #   Por sexo: ♂ mediana 24 rep, ♀ mediana 21 rep.
            # Los umbrales de tabla reflejan la mediana por sexo como punto de corte
            # y aplican descenso por edad (~12-15% por grupo de edad), coherente
            # con el efecto negativo de la edad sobre la capacidad del tríceps sural
            # confirmado en estudio internacional 2025 (ScienceDirect).
            # LSI corregido de 0.85 a 0.90: el estándar de retorno al deporte
            # para tríceps sural usa 90% de simetría (igual que cuádriceps/isquios).
            # La literatura no avala específicamente el 85% para esta variable.
            "M_18_35": 25, "M_36_50": 22, "M_51_65": 18,
            "F_18_35": 22, "F_36_50": 19, "F_51_65": 15,
            "lsi_min": 0.90,   # corregido 0.85 → 0.90 (evidencia: estándar RTS)
            "_unidad_umbral": "repeticiones",  # marca: no convertir por peso
        },
        "descripcion": (
            "Resistencia del tríceps sural mediante heel rise test single-leg. "
            "Número máximo de repeticiones hasta la fatiga con técnica estandarizada. "
            "Valores normativos (Hébert-Losier et al., 2017, n=adultos, ICC=0.96): "
            "mediana dominante 25 rep (general), ♂ 24 rep, ♀ 21 rep. "
            "La edad, el sexo femenino y el bajo nivel de actividad reducen el "
            "rendimiento (estudio internacional 2025, ScienceDirect). "
            "Ausencia de valores normativos específicos para deportistas en la "
            "literatura actual — declarar como limitación. "
            "LSI mínimo establecido en 0.90 (coherente con retorno al deporte "
            "en otros grupos musculares; el 0.85 previo carecía de referencia directa). "
            "Referencia: Hébert-Losier et al. (2017) Physiotherapy 103(4):364-370 "
            "(PubMed 28886865)."
        ),
        "protocolo": (
            "📍 Posición: de pie, monopodal, mano en la pared para equilibrio mínimo (solo contacto de dedos).\n"
            "🔧 Sin calzado o con zapatilla plana; talón al borde de un escalón (opcional, protocolo estándar).\n"
            "🗣 Instrucción: «Sube y baja el talón al máximo a un ritmo de una repetición cada 2 segundos».\n"
            "🎵 Usar metrónomo a 30 bpm o cuenta verbal del evaluador para mantener el ritmo.\n"
            "🛑 Criterio de parada: no alcanza la dorsiflexión plantar máxima o el talón cae sin control.\n"
            "📝 Registrar el número total de repeticiones completas (N)."
        ),
    },
}


# =============================================================================
# BLOQUE B: MOVILIDAD — Medidas bilaterales con umbrales universales
# =============================================================================
# El protocolo v2.2 sección 3 indica que las variables de movilidad NO se
# estratifican por nivel de actividad: sus puntos de corte clínicos son
# independientes del perfil deportivo.

VARIABLES_MOVILIDAD = {
    "dorsiflexion_tobillo": {
        "nombre_display": "Dorsiflexión tobillo — WBLT",
        "bloque": "movilidad",
        "unidad": "cm",
        "bilateral": True,
        "rango_normal": (10, 16),
        "rango_sintetico": (3, 20),
        "tipo": "continua",
        "peso_scoring": 4,   # elevado 3→4: OR 4.6 esguince (Willems 2005); mayor evidencia en movilidad
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            "umbral": 10.0,             # < 10 cm = riesgo
            "asimetria_max": 2.5,       # > 2.5 cm entre miembros = alerta
            "_unidad_umbral": "cm",
        },
        "descripcion": (
            "Dorsiflexión de tobillo medida con Weight Bearing Lunge Test. "
            "Distancia pie-pared con talón apoyado y rodilla tocando la pared. "
            "Equivalencia aproximada: 10 cm ≈ 35° de ángulo tibial. "
            "Referencias: Powden et al. (2015) Int J Sports Phys Ther 10(1):21-27; "
            "JOSPT CPG (2021) 51(4):CPG1-CPG80."
        ),
        "protocolo": (
            "📍 Posición: de pie, pie en paralelo a la pared, dedo gordo a la distancia inicial (10 cm).\n"
            "🔧 Marcar el dedo gordo y la pared con cinta métrica en el suelo.\n"
            "🗣 Instrucción: «Avanza la rodilla hasta tocar la pared sin levantar el talón».\n"
            "📏 Si toca la pared, alejar el pie 0.5 cm y repetir hasta encontrar la distancia máxima.\n"
            "📝 Registrar la distancia máxima dedo-pared con talón en contacto total (cm).\n"
            "⚠ La rodilla debe pasar por encima del segundo dedo; no permitir valgo compensatorio."
        ),
    },
    "thomas_test": {
        "nombre_display": "Thomas test (iliopsoas + recto femoral)",
        "bloque": "movilidad",
        "unidad": "binaria",
        "bilateral": True,
        "rango_normal": (0, 0),         # 0 = negativo (esperado)
        "rango_sintetico": (0, 1),
        "tipo": "binaria",
        "categorias": [0, 1],           # 0 = negativo, 1 = positivo (≥ 1 componente alterado)
        "peso_scoring": 2,
        "aplica_zona_gris": False,      # variable binaria → sin zona gris
        "umbral_riesgo_base": None,     # umbral universal
        "descripcion": (
            "Thomas test fusionado del v2.0: un único registro positivo/negativo "
            "que captura iliopsoas (extensión cadera) y recto femoral (flexión "
            "rodilla > 90°). Positivo si ≥ 1 componente está alterado. "
            "Referencias: Harvey (1998) Physiotherapy 84(2):88-91; "
            "Peeler & Anderson (2008) Clin J Sport Med."
        ),
        "protocolo": (
            "📍 Posición inicial: deportista sentado al borde de la camilla, sujetando ambas rodillas al pecho.\n"
            "▶ Ejecución: acostarse hacia atrás manteniendo ambas rodillas al pecho; luego soltar la pierna a testar.\n"
            "🔍 Valorar componente iliopsoas: ¿el muslo queda por encima del plano de la camilla? → Positivo.\n"
            "🔍 Valorar componente recto femoral: ¿la rodilla no alcanza 90° de flexión? → Positivo.\n"
            "📝 Registrar 1 (positivo) si ≥ 1 componente es positivo; 0 (negativo) si ambos negativos.\n"
            "⚠ La otra pierna permanece en flexión máxima durante toda la prueba para neutralizar la lordosis lumbar."
        ),
    },
    "rotacion_interna_cadera": {
        "nombre_display": "Rotación interna de cadera",
        "bloque": "movilidad",
        "unidad": "°",
        "bilateral": True,
        "rango_normal": (30, 50),
        "rango_sintetico": (10, 60),
        "tipo": "continua",
        "peso_scoring": 2,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            "umbral": 30.0,             # < 30° activa = riesgo
            "asimetria_max": 10.0,
            "_unidad_umbral": "grados",
        },
        "descripcion": (
            "Rotación interna activa de cadera en decúbito prono, rodilla 90°. "
            "Referencia: Reiman et al. (2015) Int J Sports Phys Ther 10(2):170-181."
        ),
        "protocolo": (
            "📍 Posición: decúbito prono, rodilla 90° de flexión, tibia vertical como referencia.\n"
            "🔧 Instrumento: goniómetro universal o inclinómetro digital colocado en la tibia.\n"
            "🗣 Instrucción: «Deja caer el pie hacia fuera tan lejos como puedas, sin mover la pelvis».\n"
            "📏 Medir el ángulo entre la vertical y la tibia en la posición activa máxima.\n"
            "📝 Registrar el rango de rotación interna activa (°); repetir 3 veces y promediar.\n"
            "⚠ Estabilizar la pelvis con la mano libre; detectar y corregir compensación por anteversión pélvica."
        ),
    },
}


# =============================================================================
# BLOQUE C: CONTROL NEUROMUSCULAR Y EQUILIBRIO — Medidas bilaterales
# =============================================================================

VARIABLES_CONTROL = {
    "y_balance_cs": {
        "nombre_display": "Y-Balance Composite Score",
        "bloque": "control",
        "unidad": "% longitud miembro",
        "bilateral": True,
        "rango_normal": (90, 110),
        "rango_sintetico": (60, 120),
        "tipo": "continua",
        "peso_scoring": 4,   # elevado 3→4: Plisky (2006) OR 6.5 en mujeres; predictor independiente robusto
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            "umbral_M": 89.0,           # < 89% longitud miembro en hombres
            "umbral_F": 94.0,           # < 94% longitud miembro en mujeres
            "asimetria_anterior_max": 4.0,  # cm
            "_unidad_umbral": "porcentaje",
        },
        "descripcion": (
            "Y-Balance Composite Score: (Anterior + Posteromedial + Posterolateral) "
            "/ (3 × longitud miembro EIAS-maléolo medial) × 100. "
            "Reemplaza a las 3 direcciones del v1.0: indicador único normalizado "
            "que mantiene el poder discriminativo sin redundancia. "
            "Referencias: Plisky et al. (2006) JOSPT 36(12):911-919; "
            "Butler et al. (2013) Scand J Med Sci Sports 23(4):225-232."
        ),
        "protocolo": (
            "📏 Paso 1 — Medir longitud del miembro: EIAS → maléolo medial con cinta métrica (cm).\n"
            "📍 Posición: monopodal en el centro del kit Y-Balance (o cinta en el suelo en 3 ángulos).\n"
            "▶ Realizar 3 intentos en cada dirección (Anterior, Posteromedial, Posterolateral).\n"
            "🗣 Instrucción: «Empuja la cinta/caja lo más lejos posible sin apoyar el pie libre».\n"
            "📝 Anotar la mejor distancia de cada dirección (cm).\n"
            "🧮 CS = [(A + PM + PL) / (3 × longitud miembro)] × 100. Introducir el CS resultante (%).\n"
            "⚠ El pie de apoyo no debe moverse; invalidar el intento si el deportista lo desplaza."
        ),
    },
    "single_leg_squat_valgo": {
        "nombre_display": "Single-leg squat — valgo dinámico",
        "bloque": "control",
        "unidad": "puntuación 0-3",
        "bilateral": True,
        "rango_normal": (0, 1),
        "rango_sintetico": (0, 3),
        "tipo": "ordinal",
        "categorias": [0, 1, 2, 3],
        "peso_scoring": 3,
        "aplica_zona_gris": False,      # escala visual ordinal → sin zona gris
        "umbral_riesgo_base": {
            "umbral": 2,                # ≥ 2 = rodilla medial al 1er dedo
            "_unidad_umbral": "puntuacion",
        },
        "descripcion": (
            "Valgo dinámico de rodilla durante single-leg squat (5 repeticiones, "
            "puntuación modal). Escala: 0 = rodilla sobre 2.º dedo; 1 = sobre "
            "1.er dedo (leve); 2 = medial al 1.er dedo (moderado, umbral riesgo); "
            "3 = medial al borde interno del pie (severo). "
            "Referencias: Crossley et al. (2011) Br J Sports Med 45(1):30-35; "
            "Ugalde et al. (2015) JOSPT."
        ),
        "protocolo": (
            "📍 Posición: de pie, monopodal, manos en las caderas, mirada al frente.\n"
            "▶ Ejecución: 5 sentadillas monopodales hasta ~60° de flexión de rodilla, ritmo natural.\n"
            "👁 Observar desde el plano frontal: posición de la rodilla respecto al dedo gordo.\n"
            "📊 Escala de valoración:\n"
            "   0 = rodilla alineada sobre el 2.º dedo → sin valgo\n"
            "   1 = rodilla sobre el 1.er dedo → valgo leve\n"
            "   2 = rodilla medial al 1.er dedo → valgo moderado (umbral de riesgo)\n"
            "   3 = rodilla medial al borde interno del pie → valgo severo\n"
            "📝 Registrar la puntuación modal (la más frecuente en las 5 repeticiones)."
        ),
    },
    "single_leg_hop": {
        "nombre_display": "Single-leg hop for distance",
        "bloque": "control",
        "unidad": "cm",
        "bilateral": True,
        "rango_normal": (110, 220),
        "rango_sintetico": (50, 240),
        "tipo": "continua",
        "peso_scoring": 3,
        "aplica_zona_gris": True,
        "umbral_riesgo_base": {
            "lsi_min": 0.90,
            "lsi_critico": 0.80,        # LSI < 80% combinado con LSI cuádriceps < 80% = riesgo alto
            "_unidad_umbral": "lsi",
        },
        "descripcion": (
            "Distancia máxima en salto monopodal con caída controlada. "
            "Se evalúa como Limb Symmetry Index (lado lesionado / lado sano). "
            "Referencia: Noyes et al. (1991) Am J Sports Med 19(5):513-518."
        ),
        "protocolo": (
            "📍 Posición: de pie, monopodal, detrás de la línea de salida marcada en el suelo.\n"
            "▶ Ejecución: salto horizontal máximo; caída controlada sobre el mismo pie (≥ 2 s estable).\n"
            "📏 Medir desde la línea de salida hasta el punto de contacto del talón (cm).\n"
            "🔁 3 intentos válidos por lado; invalidar si el deportista pierde el equilibrio al caer.\n"
            "📝 Registrar la mejor distancia de los 3 intentos (cm).\n"
            "⚠ No se permite impulso con la pierna libre; brazos pueden usarse para el swing."
        ),
    },
}


# =============================================================================
# BLOQUE D: CONTEXTO — Variables del sujeto y de carga
# =============================================================================
# Incluye demográficas (edad, género, peso), nivel de actividad para
# estratificación, historial, NRS, ACWR e índice de estrés.

VARIABLES_CONTEXTO = {
    "edad": {
        "nombre_display": "Edad",
        "bloque": "contexto",
        "unidad": "años",
        "bilateral": False,
        "rango_normal": (18, 65),
        "rango_sintetico": (18, 65),
        "tipo": "continua",
        "peso_scoring": 0,              # variable demográfica, no entra en score
        "aplica_zona_gris": False,
        "umbral_riesgo_base": None,
        "descripcion": (
            "Edad del deportista en años. Se usa para seleccionar el grupo de edad "
            "(18-35 / 36-50 / 51-65) en la tabla base de umbrales de fuerza. "
            "Población diana: 18-65 años (protocolo v2.2 sección 1)."
        ),
    },
    "genero": {
        "nombre_display": "Género",
        "bloque": "contexto",
        "unidad": "categoría",
        "bilateral": False,
        "categorias": ["masculino", "femenino"],
        "tipo": "categorica",
        "peso_scoring": 0,
        "aplica_zona_gris": False,
        "umbral_riesgo_base": None,
        "descripcion": (
            "Género del deportista. Determina la columna de la tabla base de "
            "umbrales de fuerza (M/F). Las diferencias biomecánicas entre géneros "
            "afectan al riesgo de lesión (mayor valgo dinámico en mujeres, "
            "Ireland et al. 2003)."
        ),
    },
    "peso_corporal": {
        "nombre_display": "Peso corporal",
        "bloque": "contexto",
        "unidad": "kg",
        "bilateral": False,
        "rango_normal": (45, 110),
        "rango_sintetico": (45, 120),
        "tipo": "continua",
        "peso_scoring": 0,
        "aplica_zona_gris": False,
        "umbral_riesgo_base": None,
        "descripcion": (
            "Peso corporal en kg. Se usa para normalizar las mediciones de fuerza "
            "(N → N/kg) en el momento de aplicar los umbrales del scoring."
        ),
    },
    "nivel_actividad": {
        "nombre_display": "Nivel de actividad deportiva",
        "bloque": "contexto",
        "unidad": "categoría",
        "bilateral": False,
        "categorias": ["sedentario", "recreacional", "activo", "elite"],
        "tipo": "categorica",
        "peso_scoring": 0,
        "aplica_zona_gris": False,
        "umbral_riesgo_base": None,
        "descripcion": (
            "Nivel de actividad del sujeto, usado como factor multiplicador "
            "del umbral base de fuerza (× 0.85, × 1.00, × 1.15, × 1.30). "
            "Definiciones operativas (min/semana de actividad moderada): "
            "sedentario < 150; recreacional 150-300; activo > 300 con "
            "entrenamiento estructurado; élite ≥ 6 sesiones/semana con "
            "competición federada (protocolo v2.3 sección 2.2)."
        ),
    },
    "historial_lesional": {
        "nombre_display": "Historial lesional estructurado (0-10)",
        "bloque": "contexto",
        "unidad": "puntuación 0-10",
        "bilateral": False,
        "rango_normal": (0, 4),
        "rango_sintetico": (0, 10),
        "tipo": "ordinal",
        "peso_scoring": 5,   # elevado 3→5: predictor #1 en la literatura (Bahr 2005; Hägglund 2006 OR 3-6×)
        "aplica_zona_gris": False,
        "umbral_riesgo_base": {
            "umbral_medio": 5,          # ≥ 5 = ≥ 2 lesiones MMII con baja > 7d en últimos 12 meses
            "umbral_alto": 7,           # combinado con déficit de fuerza activa A3
            "_unidad_umbral": "puntuacion",
        },
        "descripcion": (
            "Puntuación compuesta del historial de lesiones. Cálculo orientativo: "
            "0 = sin lesiones; 1-3 = 1 lesión leve sin baja; 4-6 = 1-2 lesiones "
            "con baja > 7 días en últimos 12 meses; 7-10 = ≥ 2 lesiones graves "
            "o recurrentes en la misma articulación. "
            "Referencia: Hägglund et al. (2006) Br J Sports Med 40(11):916-919."
        ),
        "protocolo": (
            "🗣 Preguntar: «¿Has tenido lesiones en el miembro inferior en los últimos 12 meses?»\n"
            "📊 Guía de puntuación:\n"
            "   0 = sin lesiones en los últimos 12 meses\n"
            "   1-3 = 1 lesión leve sin baja laboral/deportiva\n"
            "   4-6 = 1-2 lesiones con baja > 7 días (esguince grado II-III, rotura muscular, etc.)\n"
            "   7-10 = ≥ 2 lesiones graves o lesión recurrente en la misma articulación\n"
            "📝 Considerar: LCA, rotura muscular, esguince grado II-III, fractura de estrés.\n"
            "⚠ Centrar la anamnesis en lesiones que requirieron baja de actividad deportiva."
        ),
    },
    "dolor_percibido_nrs": {
        "nombre_display": "Dolor percibido — NRS (0-10)",
        "bloque": "contexto",
        "unidad": "puntuación 0-10",
        "bilateral": False,
        "rango_normal": (0, 3),
        "rango_sintetico": (0, 10),
        "tipo": "ordinal",
        "peso_scoring": 3,
        "aplica_zona_gris": False,
        "umbral_riesgo_base": {
            "umbral_no_concluyente": 5,  # > 5 → evaluación no concluyente (v2.1 C3)
            "_unidad_umbral": "puntuacion",
        },
        "descripcion": (
            "Numeric Rating Scale del dolor durante o tras la evaluación. "
            "IMPORTANTE (v2.1 corrección C3): NRS > 5 NO clasifica directamente "
            "como riesgo alto. Activa la categoría 'EVALUACIÓN NO CONCLUYENTE' "
            "porque la fuerza no se puede medir con dolor agudo. Reprogramar "
            "tras NRS ≤ 3. Referencia: Farrar et al. (2001) Pain 94(2):149-158."
        ),
        "protocolo": (
            "🗣 Instrucción estándar: «En una escala del 0 al 10, donde 0 es sin dolor y "
            "10 es el peor dolor imaginable, ¿cómo valorarías tu dolor AHORA MISMO?»\n"
            "📍 Referir el dolor a la extremidad o región que se va a evaluar.\n"
            "📝 Registrar el valor declarado por el deportista sin interpretación del evaluador.\n"
            "🛑 NRS > 5 → interrumpir la evaluación. Caso no concluyente: reprogramar cuando NRS ≤ 3."
        ),
    },
    "hooper_index": {
        "nombre_display": "Hooper Index — Bienestar deportivo",
        "bloque": "contexto",
        "unidad": "puntuación 4-28",
        "bilateral": False,
        "rango_normal": (4, 17),
        "rango_sintetico": (4, 28),
        "tipo": "continua",
        "peso_scoring": 3,   # elevado 2→3 v2.3: único indicador de sueño/estrés/fatiga/recuperación
        "aplica_zona_gris": False,
        "umbral_riesgo_base": {
            "umbral": 22,
            "_unidad_umbral": "puntuacion",
        },
        "descripcion": (
            "Hooper Index: cuestionario de bienestar de 4 ítems (fatiga, estrés, "
            "dolor muscular/DOMS, calidad del sueño), cada uno valorado de 1 "
            "(muy muy bajo/bueno) a 7 (muy muy alto/malo). Rango total 4-28. "
            "Puntuación ≥ 22 indica recuperación insuficiente y se asocia a mayor "
            "riesgo de lesión por sobreentrenamiento. Validado en élite como "
            "marcador de sobreentrenamiento y estado de recuperación. "
            "Referencias: Hooper & Mackinnon (1995) Sports Med 20(5):321-327; "
            "Rushall (1990) Int J Sport Psychol."
        ),
        "protocolo": (
            "📋 Administrar ANTES de la sesión (primera cosa de la mañana si es posible).\n"
            "📝 4 ítems, escala 1 (muy muy bajo/bueno) a 7 (muy muy alto/malo):\n"
            "   1. Fatiga: «¿Cómo describes tu nivel de fatiga?» (1=muy muy bajo, 7=muy muy alto)\n"
            "   2. Estrés: «¿Cómo describes tu nivel de estrés?» (1=muy muy bajo, 7=muy muy alto)\n"
            "   3. Dolor muscular (DOMS): «¿Cómo describes tu dolor muscular?» (1=muy muy bajo, 7=muy muy alto)\n"
            "   4. Calidad del sueño: «¿Cómo describes tu calidad de sueño?» (1=muy muy buena, 7=muy muy mala)\n"
            "🧮 Suma de los 4 ítems: 4-28. Introducir el total.\n"
            "🛑 Puntuación ≥ 22 = recuperación insuficiente; anotar en el informe."
        ),
    },
}


# =============================================================================
# CONSTRUCCIÓN DEL DICCIONARIO COMPLETO EXPANDIDO
# =============================================================================

def _expandir_bilaterales(variables_bloque: dict) -> dict:
    """
    Expande las variables bilaterales en dos entradas (_der, _izq).
    Las variables no bilaterales se mantienen tal cual.
    """
    expandidas: dict = {}
    for clave, info in variables_bloque.items():
        if info.get("bilateral", False):
            for lado, sufijo in [("derecha", "_der"), ("izquierda", "_izq")]:
                nueva_clave = clave + sufijo
                nueva_info = info.copy()
                nueva_info["nombre_display"] = f"{info['nombre_display']} ({lado})"
                nueva_info["lado"] = lado
                expandidas[nueva_clave] = nueva_info
        else:
            expandidas[clave] = info.copy()
            expandidas[clave]["lado"] = None
    return expandidas


# Diccionario completo con todas las variables expandidas
VARIABLES: dict = {}
VARIABLES.update(_expandir_bilaterales(VARIABLES_FUERZA))
VARIABLES.update(_expandir_bilaterales(VARIABLES_MOVILIDAD))
VARIABLES.update(_expandir_bilaterales(VARIABLES_CONTROL))
VARIABLES.update(_expandir_bilaterales(VARIABLES_CONTEXTO))

# Variables originales sin expandir (útil para la app y para referencia)
VARIABLES_ORIGINALES: dict = {}
VARIABLES_ORIGINALES.update(VARIABLES_FUERZA)
VARIABLES_ORIGINALES.update(VARIABLES_MOVILIDAD)
VARIABLES_ORIGINALES.update(VARIABLES_CONTROL)
VARIABLES_ORIGINALES.update(VARIABLES_CONTEXTO)

# Listas de nombres de columnas por bloque (útil para filtrar y para el preprocesador)
COLUMNAS_FUERZA    = [k for k, v in VARIABLES.items() if v["bloque"] == "fuerza"]
COLUMNAS_MOVILIDAD = [k for k, v in VARIABLES.items() if v["bloque"] == "movilidad"]
COLUMNAS_CONTROL   = [k for k, v in VARIABLES.items() if v["bloque"] == "control"]
COLUMNAS_CONTEXTO  = [k for k, v in VARIABLES.items() if v["bloque"] == "contexto"]

# Total de columnas de entrada (sin la etiqueta riesgo_lesion)
TOTAL_COLUMNAS = len(VARIABLES)


# =============================================================================
# PUNTO DE ENTRADA — verificación rápida
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("variables.py v2.2 — IntApp")
    print("=" * 60)
    print(f"Total de variables originales: {len(VARIABLES_ORIGINALES)}")
    print(f"Total de columnas expandidas:  {TOTAL_COLUMNAS}")
    print(f"  - Fuerza:    {len(COLUMNAS_FUERZA)}")
    print(f"  - Movilidad: {len(COLUMNAS_MOVILIDAD)}")
    print(f"  - Control:   {len(COLUMNAS_CONTROL)}")
    print(f"  - Contexto:  {len(COLUMNAS_CONTEXTO)}")

    # Verificación de coherencia: todas las variables tienen los campos del v2.2
    campos_comunes = [
        "nombre_display", "bloque", "unidad", "bilateral",
        "tipo", "peso_scoring", "aplica_zona_gris",
        "umbral_riesgo_base", "descripcion",
    ]
    print("\nVerificación de campos del v2.2:")
    faltantes = []
    for clave, info in VARIABLES_ORIGINALES.items():
        # Campos comunes a todas
        for campo in campos_comunes:
            if campo not in info:
                faltantes.append(f"  - {clave} → falta '{campo}'")
        # Las categóricas necesitan 'categorias'; las demás 'rango_sintetico'
        if info["tipo"] == "categorica":
            if "categorias" not in info:
                faltantes.append(f"  - {clave} → falta 'categorias'")
        else:
            if "rango_sintetico" not in info:
                faltantes.append(f"  - {clave} → falta 'rango_sintetico'")
    if faltantes:
        print("INCOMPLETO:")
        for f in faltantes:
            print(f)
    else:
        print("  OK: todas las variables tienen los campos requeridos del v2.2.")

    # Resumen del peso total disponible para el score
    peso_total = sum(
        info["peso_scoring"] * (2 if info["bilateral"] else 1)
        for info in VARIABLES_ORIGINALES.values()
    )
    print(f"\nPeso total máximo del score (todas las variables fuera de umbral):")
    print(f"  {peso_total} puntos")
    print(f"  Umbrales del score: ≥ {SCORE_UMBRAL_ALTO} alto, "
          f"≥ {SCORE_UMBRAL_MEDIO} medio.")
