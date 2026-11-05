from pathlib import Path
import math

import pandas as pd

from dash import Dash, Input, Output, State, dcc, html, dash_table

from src.etl import preparar_datos
from src.model import entrenar_modelos, predecir_resultados
from src.finance import (
    evaluar_todas_alternativas,
    evaluar_alternativas_multicultivo,
    expandir_configuracion,
    ajustar_prediccion_rtk_isobus,
)
from src.forecast import generar_escenarios_todos_cultivos
from src.graphics import (
    grafico_ranking_van,
    grafico_ranking_payback,
    grafico_beneficio_incremental,
)


# =========================================================
# RUTAS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

RUTA_CONSTANTES = BASE_DIR / "data" / "precios_constantes.xlsx"
RUTA_HISTORICOS = BASE_DIR / "data" / "precios_historicos.xlsx"
RUTA_INVERSIONES = BASE_DIR / "data" / "inversiones_tecnologia.xlsx"


# =========================================================
# DATOS Y MODELOS
# =========================================================

(
    df_constantes,
    df_historicos,
    df_inversiones,
) = preparar_datos(
    RUTA_CONSTANTES,
    RUTA_HISTORICOS,
    RUTA_INVERSIONES,
)

modelos = entrenar_modelos(df_constantes)

ANIO_MAX_HISTORICO = int(df_historicos["Año"].dropna().max())
ANIO_FUTURO_DEFAULT = ANIO_MAX_HISTORICO + 2


# =========================================================
# PARÁMETROS ECONÓMICOS
# =========================================================

def obtener_parametros_constantes(cultivo):
    datos = df_constantes[df_constantes["Cultivo"] == cultivo]

    return {
        "Precio_tonelada_venta": datos["Precio_tonelada_venta"].mean(),
        "Precio_litro_gasoleoB": datos["Precio_litro_gasoleoB"].mean(),
        "Precio_litro_Fitosanitario": datos["Precio_litro_Fitosanitario"].mean(),
        "Precio_unitario_semilla": datos["Precio_unitario_semilla"].mean(),
        "Precio_Abono_kg": datos["Precio_Abono_kg"].mean(),
        "Gastos_fijos_por_ha": datos["Gastos_fijos_por_ha"].mean(),
        "Descuento_humedad_por_t": datos["Descuento_humedad_por_t"].mean(),
    }


def obtener_parametros_historicos(cultivo, anio):
    datos = df_historicos[
        (df_historicos["Cultivo"] == cultivo)
        & (df_historicos["Año"] == anio)
    ]

    if datos.empty:
        raise ValueError(f"No existen datos de {cultivo} para el año {anio}.")

    return {
        "Precio_tonelada_venta": datos["Precio_tonelada_venta"].mean(),
        "Precio_litro_gasoleoB": datos["Precio_litro_gasoleoB"].mean(),
        "Precio_litro_Fitosanitario": datos["Precio_litro_Fitosanitario"].mean(),
        "Precio_unitario_semilla": datos["Precio_unitario_semilla"].mean(),
        "Precio_Abono_kg": datos["Precio_Abono_kg"].mean(),
        "Gastos_fijos_por_ha": datos["Gastos_fijos_por_ha"].mean(),
        "Descuento_humedad_por_t": datos["Descuento_humedad_por_t"].mean(),
    }


# =========================================================
# PRESENTACIÓN
# =========================================================

def nombre_tecnologia(texto):
    if not isinstance(texto, str):
        return texto

    reemplazos = {
        "RTK_ISOBUS": "RTK + ISOBUS",
        "Siembra_variable": "Siembra variable",
        "Abono_variable": "Abono variable",
        "Corte_tramos": "Corte de tramos",
    }

    partes = [parte.strip() for parte in texto.split(",")]
    return " + ".join(
        reemplazos.get(parte, parte.replace("_", " "))
        for parte in partes
    )


def crear_configuracion_actual(tecnologias_seleccionadas):
    tecnologias_seleccionadas = tecnologias_seleccionadas or []

    configuracion = {
        "RTK_ISOBUS": int("RTK_ISOBUS" in tecnologias_seleccionadas),
        "Siembra_variable": int("Siembra_variable" in tecnologias_seleccionadas),
        "Abono_variable": int("Abono_variable" in tecnologias_seleccionadas),
        "Corte_tramos": int("Corte_tramos" in tecnologias_seleccionadas),
    }

    if (
        configuracion["Siembra_variable"]
        or configuracion["Abono_variable"]
        or configuracion["Corte_tramos"]
    ):
        configuracion["RTK_ISOBUS"] = 1

    return configuracion


def formato_euros(valor):
    if pd.isna(valor):
        return "-"
    return f"{valor:,.0f} €".replace(",", ".")


def formato_payback(valor, vida_util):
    if pd.isna(valor):
        return "-"
    if valor == float("inf"):
        return "No recuperable"
    if valor > vida_util:
        return "No recuperable en la vida útil"
    return f"{valor:.2f} años"


def formato_porcentaje(valor):
    if pd.isna(valor):
        return "-"
    return f"{valor:.1f} %"


def formato_numero_euros_tabla(valor):
    if pd.isna(valor):
        return "-"
    return f"{valor:,.0f} €".replace(",", ".")


def formato_porcentaje_tabla(valor):
    if pd.isna(valor):
        return "-"
    return f"{valor:.2f} %"


def formato_payback_tabla(valor, vida_util):
    if pd.isna(valor):
        return "-"
    if valor == float("inf"):
        return "No recuperable"
    if valor > vida_util:
        return "No recuperable en la vida útil"
    return f"{valor:.2f}"


def formato_superficie_minima(valor):
    if pd.isna(valor):
        return "-"
    if valor == float("inf"):
        return "No rentable"
    if valor <= 0:
        return "0 ha"
    return f"{math.ceil(valor)} ha"


# =========================================================
# COMPARACIÓN TÉCNICA
# =========================================================

NOMBRES_INDICADORES = {
    "Rend_t_ha": "Rendimiento",
    "Productividad_ha_h": "Productividad",
    "Consumo_L_ha": "Consumo de combustible",
    "Fitosanitarios_ha": "Fitosanitarios",
    "Semillas_ha": "Semillas",
    "Abono_ha": "Abono",
    "Pasadas_ha": "Pasadas",
}

UNIDADES_INDICADORES = {
    "Rend_t_ha": "t/ha",
    "Productividad_ha_h": "ha/h",
    "Consumo_L_ha": "L/ha",
    "Fitosanitarios_ha": "L/ha",
    "Semillas_ha": "unidades/ha",
    "Abono_ha": "kg/ha",
    "Pasadas_ha": "pasadas/ha",
}


def formatear_valor_tecnico(variable, valor):
    if pd.isna(valor):
        return "-"
    if variable == "Semillas_ha":
        return f"{valor:,.0f}".replace(",", ".")
    return f"{valor:.2f}"


def crear_comparacion_tecnica_cultivo(
    cultivo,
    configuracion_actual,
    configuracion_recomendada,
):
    actual_modelo = expandir_configuracion(configuracion_actual)
    recomendada_modelo = expandir_configuracion(configuracion_recomendada)

    pred_actual = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **actual_modelo,
    )

    pred_recomendada = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **recomendada_modelo,
    )

    pred_recomendada = ajustar_prediccion_rtk_isobus(
        pred_actual=pred_actual,
        pred_objetivo=pred_recomendada,
        configuracion_objetivo=configuracion_recomendada,
    )

    filas = []
    orden_variables = [
        "Rend_t_ha",
        "Productividad_ha_h",
        "Consumo_L_ha",
        "Fitosanitarios_ha",
        "Semillas_ha",
        "Abono_ha",
        "Pasadas_ha",
    ]

    for variable in orden_variables:
        actual = pred_actual[variable]
        recomendada = pred_recomendada[variable]
        diferencia = recomendada - actual

        if variable == "Semillas_ha":
            variacion = f"{diferencia:+,.0f}".replace(",", ".")
        else:
            variacion = f"{diferencia:+.2f}"

        filas.append(
            {
                "Indicador": NOMBRES_INDICADORES[variable],
                "Unidad": UNIDADES_INDICADORES[variable],
                "Actual": formatear_valor_tecnico(variable, actual),
                "Recomendada": formatear_valor_tecnico(variable, recomendada),
                "Variacion": variacion,
            }
        )

    return filas


def crear_comparacion_tecnica_multi(
    explotacion,
    configuracion_actual,
    configuracion_recomendada,
):
    filas = []
    nombres_cultivos = {
        "Maiz": "Maíz",
        "Arroz": "Arroz",
        "Tomates": "Tomate",
    }

    for cultivo in explotacion:
        comparacion = crear_comparacion_tecnica_cultivo(
            cultivo=cultivo,
            configuracion_actual=configuracion_actual,
            configuracion_recomendada=configuracion_recomendada,
        )

        for fila in comparacion:
            fila = fila.copy()
            fila["Cultivo"] = nombres_cultivos[cultivo]
            filas.append(fila)

    return filas


# =========================================================
# APP
# =========================================================

app = Dash(__name__)
server = app.server
app.title = "AgroInvest"

ESTILO_TARJETA = {
    "padding": "20px",
    "border": "1px solid #dddddd",
    "borderRadius": "12px",
    "backgroundColor": "#ffffff",
    "minHeight": "125px",
}

ESTILO_INPUT = {
    "width": "100%",
    "height": "38px",
}


# =========================================================
# LAYOUT
# =========================================================

app.layout = html.Div(
    style={
        "maxWidth": "1400px",
        "margin": "0 auto",
        "padding": "28px",
        "fontFamily": "Arial, sans-serif",
    },
    children=[
        html.H1("AgroInvest", style={"marginBottom": "4px", "fontSize": "38px"}),
        html.P(
            "Análisis y recomendación de inversiones en tecnologías de Agricultura 4.0.",
            style={"fontSize": "18px", "marginTop": "0", "marginBottom": "25px"},
        ),
        html.Hr(),

        # 1. EXPLOTACIÓN
        html.H2("1. Configuración de la explotación"),
        html.Label("Tipo de explotación", style={"fontWeight": "bold"}),
        dcc.RadioItems(
            id="tipo-explotacion",
            options=[
                {"label": " Un cultivo", "value": "mono"},
                {"label": " Varios cultivos", "value": "multi"},
            ],
            value="mono",
            inline=True,
            labelStyle={"marginRight": "25px"},
            style={"marginTop": "8px", "marginBottom": "20px"},
        ),

        html.Div(
            id="bloque-monocultivo",
            children=[
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr",
                        "gap": "22px",
                    },
                    children=[
                        html.Div(
                            [
                                html.Label("Cultivo"),
                                dcc.Dropdown(
                                    id="cultivo",
                                    options=[
                                        {"label": "Maíz", "value": "Maiz"},
                                        {"label": "Arroz", "value": "Arroz"},
                                        {"label": "Tomate", "value": "Tomates"},
                                    ],
                                    value="Maiz",
                                    clearable=False,
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Superficie (ha)"),
                                dcc.Input(
                                    id="superficie",
                                    type="number",
                                    value=100,
                                    min=1,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                            ]
                        ),
                    ],
                )
            ],
        ),

        html.Div(
            id="bloque-multicultivo",
            children=[
                html.P(
                    "Introduce la superficie dedicada a cada cultivo. "
                    "Utiliza 0 ha para los cultivos que no estén presentes."
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(3, 1fr)",
                        "gap": "22px",
                    },
                    children=[
                        html.Div(
                            [
                                html.Label("Maíz (ha)"),
                                dcc.Input(
                                    id="superficie-maiz",
                                    type="number",
                                    value=60,
                                    min=0,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Arroz (ha)"),
                                dcc.Input(
                                    id="superficie-arroz",
                                    type="number",
                                    value=30,
                                    min=0,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Tomate (ha)"),
                                dcc.Input(
                                    id="superficie-tomates",
                                    type="number",
                                    value=10,
                                    min=0,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                            ]
                        ),
                    ],
                ),
            ],
        ),

        html.Br(),
        html.Label("Escenario económico"),
        dcc.Dropdown(
            id="escenario",
            options=[
                {"label": "Precios constantes", "value": "constantes"},
                {"label": "Precios históricos", "value": "historicos"},
                {"label": "Personalizado", "value": "personalizado"},
                {"label": "Previsión futura", "value": "futuro"},
            ],
            value="constantes",
            clearable=False,
        ),
        html.Br(),

        html.Label("Tecnologías instaladas actualmente", style={"fontWeight": "bold"}),
        dcc.Checklist(
            id="tecnologias-actuales",
            options=[
                {"label": " RTK + ISOBUS", "value": "RTK_ISOBUS"},
                {"label": " Siembra variable", "value": "Siembra_variable"},
                {"label": " Abono variable", "value": "Abono_variable"},
                {"label": " Corte de tramos", "value": "Corte_tramos"},
            ],
            value=[],
            labelStyle={"display": "block", "marginBottom": "9px"},
            style={"marginTop": "12px"},
        ),
        html.P(
            "GPS se considera la tecnología base. RTK + ISOBUS es requisito previo "
            "para las tecnologías avanzadas.",
            style={"fontSize": "13px", "marginTop": "18px"},
        ),

        html.Hr(),

        # 2. CONDICIONES ECONÓMICAS
        html.H2("2. Condiciones económicas"),
        html.Div(
            id="bloque-historico",
            children=[
                html.Label("Año histórico"),
                dcc.Dropdown(id="anio-historico", clearable=False),
            ],
        ),

        html.Div(
            id="bloque-personalizado",
            children=[
                html.H4("Parámetros personalizados"),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(3, 1fr)",
                        "gap": "15px",
                    },
                    children=[
                        dcc.Input(id="precio-venta", type="number", placeholder="Precio venta €/t"),
                        dcc.Input(id="precio-gasoil", type="number", placeholder="Gasóleo €/L"),
                        dcc.Input(id="precio-fitosanitario", type="number", placeholder="Fitosanitario €/L"),
                        dcc.Input(id="precio-semilla", type="number", placeholder="Precio unitario semilla"),
                        dcc.Input(id="precio-abono", type="number", placeholder="Abono €/kg"),
                        dcc.Input(id="gastos-fijos", type="number", placeholder="Gastos fijos €/ha"),
                        dcc.Input(id="descuento-humedad", type="number", placeholder="Descuento humedad €/t"),
                    ],
                ),
            ],
        ),

        html.Div(
            id="bloque-futuro",
            children=[
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 2fr",
                        "gap": "25px",
                        "alignItems": "end",
                    },
                    children=[
                        html.Div(
                            [
                                html.Label("Año objetivo"),
                                dcc.Input(
                                    id="anio-futuro",
                                    type="number",
                                    value=ANIO_FUTURO_DEFAULT,
                                    min=ANIO_MAX_HISTORICO + 1,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Escenario futuro"),
                                dcc.RadioItems(
                                    id="escenario-futuro",
                                    options=[
                                        {"label": " Conservador", "value": "Conservador"},
                                        {"label": " Central", "value": "Central"},
                                        {"label": " Alcista", "value": "Alcista"},
                                    ],
                                    value="Central",
                                    inline=True,
                                    labelStyle={"marginRight": "25px"},
                                    style={"marginTop": "10px"},
                                ),
                            ]
                        ),
                    ],
                ),
                html.P(
                    "La previsión se obtiene a partir de las tendencias históricas de los "
                    "parámetros económicos. Debe interpretarse como un escenario orientativo "
                    "y no como una predicción garantizada.",
                    style={"fontSize": "13px", "marginTop": "15px"},
                ),
            ],
        ),

        html.Details(
            open=False,
            style={"marginTop": "18px", "marginBottom": "20px"},
            children=[
                html.Summary(
                    "Parámetros financieros",
                    style={
                        "fontWeight": "bold",
                        "fontSize": "16px",
                        "cursor": "pointer",
                        "marginBottom": "15px",
                    },
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr",
                        "gap": "25px",
                        "maxWidth": "700px",
                        "paddingTop": "10px",
                    },
                    children=[
                        html.Div(
                            [
                                html.Label("Vida útil (años)"),
                                dcc.Input(
                                    id="vida-util",
                                    type="number",
                                    value=15,
                                    min=1,
                                    max=50,
                                    step=1,
                                    style=ESTILO_INPUT,
                                ),
                                html.P(
                                    "Horizonte durante el que se evalúan los beneficios de la inversión.",
                                    style={"fontSize": "12px", "marginTop": "5px"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Tasa de descuento (%)"),
                                dcc.Input(
                                    id="tasa-descuento",
                                    type="number",
                                    value=5,
                                    min=0,
                                    max=100,
                                    step=0.5,
                                    style=ESTILO_INPUT,
                                ),
                                html.P(
                                    "Tasa utilizada para actualizar los flujos futuros al valor presente.",
                                    style={"fontSize": "12px", "marginTop": "5px"},
                                ),
                            ]
                        ),
                    ],
                ),
                html.P(
                    "Valores base utilizados por AgroInvest: 15 años de vida útil y 5 % de tasa de descuento.",
                    style={"fontSize": "12px", "fontStyle": "italic"},
                ),
            ],
        ),

        html.Br(),
        html.Button(
            "Analizar inversiones",
            id="boton-analizar",
            n_clicks=0,
            style={
                "padding": "13px 26px",
                "fontSize": "16px",
                "cursor": "pointer",
                "borderRadius": "6px",
            },
        ),

        html.Hr(),

        # 3. RECOMENDACIÓN ECONÓMICA
        html.H2("3. Recomendación económica"),
        html.Div(id="mensaje-error"),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1.7fr 1fr 1fr 1fr 1fr",
                "gap": "15px",
                "marginBottom": "20px",
            },
            children=[
                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4("Mejor inversión"),
                        html.Div(
                            id="kpi-tecnologias",
                            style={
                                "fontSize": "18px",
                                "fontWeight": "bold",
                                "lineHeight": "1.4",
                            },
                        ),
                    ],
                ),
                html.Div(style=ESTILO_TARJETA, children=[html.H4("Inversión"), html.H3(id="kpi-inversion")]),
                html.Div(style=ESTILO_TARJETA, children=[html.H4("VAN"), html.H3(id="kpi-van")]),
                html.Div(style=ESTILO_TARJETA, children=[html.H4("Payback"), html.H3(id="kpi-payback")]),
                html.Div(style=ESTILO_TARJETA, children=[html.H4("ROI"), html.H3(id="kpi-roi")]),
            ],
        ),
        html.Div(
            id="texto-recomendacion",
            style={
                "padding": "16px 18px",
                "marginBottom": "25px",
                "borderLeft": "4px solid #555",
                "backgroundColor": "#f7f7f7",
                "fontSize": "16px",
                "lineHeight": "1.5",
            },
        ),
        dash_table.DataTable(
            id="tabla-ranking",
            page_size=8,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "whiteSpace": "normal",
                "height": "auto",
                "fontFamily": "Arial",
                "fontSize": "14px",
            },
            style_header={"fontWeight": "bold", "backgroundColor": "#f5f5f5"},
        ),
        html.Br(),
        dcc.Graph(id="grafico-van"),
        dcc.Graph(id="grafico-payback"),
        dcc.Graph(id="grafico-beneficio"),
        html.Hr(),

        # 4. IMPACTO TÉCNICO
        html.H2("4. Impacto técnico estimado"),
        html.P(
            "Comparación entre los resultados técnicos estimados para la situación actual "
            "y la alternativa recomendada. Estas estimaciones proceden de los modelos "
            "predictivos y deben interpretarse como apoyo a la decisión, no como efectos "
            "causales garantizados."
        ),
        dash_table.DataTable(
            id="tabla-tecnica",
            style_table={"overflowX": "auto", "marginBottom": "30px"},
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "whiteSpace": "normal",
                "height": "auto",
                "fontFamily": "Arial",
                "fontSize": "14px",
            },
            style_header={"fontWeight": "bold", "backgroundColor": "#f5f5f5"},
        ),
    ],
)


# =========================================================
# CALLBACKS DE VISIBILIDAD
# =========================================================

@app.callback(
    Output("bloque-monocultivo", "style"),
    Output("bloque-multicultivo", "style"),
    Input("tipo-explotacion", "value"),
)
def mostrar_tipo_explotacion(tipo):
    visible = {"display": "block"}
    oculto = {"display": "none"}
    if tipo == "multi":
        return oculto, visible
    return visible, oculto


@app.callback(
    Output("bloque-historico", "style"),
    Output("bloque-personalizado", "style"),
    Output("bloque-futuro", "style"),
    Input("escenario", "value"),
)
def mostrar_controles_escenario(escenario):
    oculto = {"display": "none"}
    visible = {"display": "block", "marginBottom": "15px"}

    if escenario == "historicos":
        return visible, oculto, oculto
    if escenario == "personalizado":
        return oculto, visible, oculto
    if escenario == "futuro":
        return oculto, oculto, visible
    return oculto, oculto, oculto


@app.callback(
    Output("anio-historico", "options"),
    Output("anio-historico", "value"),
    Input("tipo-explotacion", "value"),
    Input("cultivo", "value"),
)
def actualizar_anios(tipo, cultivo):
    if tipo == "multi":
        conjuntos = []
        for nombre_cultivo in ["Maiz", "Arroz", "Tomates"]:
            anios_cultivo = set(
                df_historicos[df_historicos["Cultivo"] == nombre_cultivo]["Año"]
                .dropna()
                .astype(int)
                .tolist()
            )
            conjuntos.append(anios_cultivo)

        anios = sorted(set.intersection(*conjuntos)) if conjuntos else []
    else:
        anios = sorted(
            df_historicos[df_historicos["Cultivo"] == cultivo]["Año"]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

    opciones = [{"label": str(anio), "value": int(anio)} for anio in anios]
    valor = int(anios[-1]) if anios else None
    return opciones, valor


# =========================================================
# CALLBACK PRINCIPAL
# =========================================================

@app.callback(
    Output("kpi-tecnologias", "children"),
    Output("kpi-inversion", "children"),
    Output("kpi-van", "children"),
    Output("kpi-payback", "children"),
    Output("kpi-roi", "children"),
    Output("texto-recomendacion", "children"),
    Output("tabla-ranking", "data"),
    Output("tabla-ranking", "columns"),
    Output("grafico-van", "figure"),
    Output("grafico-payback", "figure"),
    Output("grafico-beneficio", "figure"),
    Output("tabla-tecnica", "data"),
    Output("tabla-tecnica", "columns"),
    Output("mensaje-error", "children"),
    Input("boton-analizar", "n_clicks"),
    State("tipo-explotacion", "value"),
    State("cultivo", "value"),
    State("superficie", "value"),
    State("superficie-maiz", "value"),
    State("superficie-arroz", "value"),
    State("superficie-tomates", "value"),
    State("escenario", "value"),
    State("anio-historico", "value"),
    State("anio-futuro", "value"),
    State("escenario-futuro", "value"),
    State("tecnologias-actuales", "value"),
    State("precio-venta", "value"),
    State("precio-gasoil", "value"),
    State("precio-fitosanitario", "value"),
    State("precio-semilla", "value"),
    State("precio-abono", "value"),
    State("gastos-fijos", "value"),
    State("descuento-humedad", "value"),
    State("vida-util", "value"),
    State("tasa-descuento", "value"),
)
def analizar_inversiones(
    n_clicks,
    tipo_explotacion,
    cultivo,
    superficie,
    superficie_maiz,
    superficie_arroz,
    superficie_tomates,
    escenario,
    anio,
    anio_futuro,
    escenario_futuro,
    tecnologias_actuales,
    precio_venta,
    precio_gasoil,
    precio_fitosanitario,
    precio_semilla,
    precio_abono,
    gastos_fijos,
    descuento_humedad,
    vida_util,
    tasa_descuento,
):
    if n_clicks == 0:
        return (
            "-", "-", "-", "-", "-", "",
            [], [], {}, {}, {}, [], [], "",
        )

    try:
        if vida_util is None or vida_util <= 0:
            raise ValueError("La vida útil debe ser mayor que 0.")
        if tasa_descuento is None or tasa_descuento < 0:
            raise ValueError("La tasa de descuento no puede ser negativa.")

        vida_util = int(vida_util)
        tasa_descuento_decimal = float(tasa_descuento) / 100
        configuracion_actual = crear_configuracion_actual(tecnologias_actuales)

        escenarios_futuros = None
        if escenario == "futuro":
            if anio_futuro is None:
                raise ValueError("Introduce un año objetivo.")
            if anio_futuro <= ANIO_MAX_HISTORICO:
                raise ValueError(
                    f"El año objetivo debe ser posterior a {ANIO_MAX_HISTORICO}."
                )

            escenarios_futuros = generar_escenarios_todos_cultivos(
                df=df_historicos,
                anio_objetivo=int(anio_futuro),
                variacion=0.10,
            )

        # -------------------------------------------------
        # MONOCULTIVO
        # -------------------------------------------------
        if tipo_explotacion == "mono":
            if superficie is None or superficie <= 0:
                raise ValueError("La superficie debe ser mayor que 0.")

            if escenario == "constantes":
                parametros = obtener_parametros_constantes(cultivo)
                descripcion_escenario = "precios constantes"

            elif escenario == "historicos":
                parametros = obtener_parametros_historicos(cultivo, anio)
                descripcion_escenario = f"precios históricos de {anio}"

            elif escenario == "personalizado":
                valores = [
                    precio_venta,
                    precio_gasoil,
                    precio_fitosanitario,
                    precio_semilla,
                    precio_abono,
                    gastos_fijos,
                ]
                if any(valor is None for valor in valores):
                    raise ValueError(
                        "Completa todos los parámetros del escenario personalizado."
                    )

                parametros = {
                    "Precio_tonelada_venta": precio_venta,
                    "Precio_litro_gasoleoB": precio_gasoil,
                    "Precio_litro_Fitosanitario": precio_fitosanitario,
                    "Precio_unitario_semilla": precio_semilla,
                    "Precio_Abono_kg": precio_abono,
                    "Gastos_fijos_por_ha": gastos_fijos,
                    "Descuento_humedad_por_t": descuento_humedad,
                }
                descripcion_escenario = "parámetros personalizados"

            elif escenario == "futuro":
                parametros = escenarios_futuros[cultivo][escenario_futuro]
                descripcion_escenario = (
                    f"previsión {escenario_futuro.lower()} para {int(anio_futuro)}"
                )
            else:
                raise ValueError("Escenario económico no reconocido.")

            tabla = evaluar_todas_alternativas(
                cultivo=cultivo,
                superficie=superficie,
                configuracion_actual=configuracion_actual,
                parametros=parametros,
                modelos=modelos,
                vida_util=vida_util,
                tasa_descuento=tasa_descuento_decimal,
            )

            nombres_cultivo = {
                "Maiz": "maíz",
                "Arroz": "arroz",
                "Tomates": "tomate",
            }
            descripcion_explotacion = (
                f"{superficie:g} ha de {nombres_cultivo.get(cultivo, cultivo.lower())}"
            )
            explotacion_tecnica = {cultivo: superficie}

        # -------------------------------------------------
        # MULTICULTIVO
        # -------------------------------------------------
        else:
            superficies = {
                "Maiz": superficie_maiz or 0,
                "Arroz": superficie_arroz or 0,
                "Tomates": superficie_tomates or 0,
            }

            explotacion = {
                cultivo_nombre: superficie_cultivo
                for cultivo_nombre, superficie_cultivo in superficies.items()
                if superficie_cultivo > 0
            }

            if not explotacion:
                raise ValueError("Introduce superficie en al menos un cultivo.")

            if escenario == "personalizado":
                raise ValueError(
                    "El escenario personalizado multicultivo requiere parámetros específicos por cultivo."
                )

            parametros_por_cultivo = {}
            for cultivo_nombre in explotacion:
                if escenario == "constantes":
                    parametros_por_cultivo[cultivo_nombre] = obtener_parametros_constantes(
                        cultivo_nombre
                    )
                elif escenario == "historicos":
                    parametros_por_cultivo[cultivo_nombre] = obtener_parametros_historicos(
                        cultivo_nombre,
                        anio,
                    )
                elif escenario == "futuro":
                    parametros_por_cultivo[cultivo_nombre] = escenarios_futuros[
                        cultivo_nombre
                    ][escenario_futuro]
                else:
                    raise ValueError("Escenario económico no reconocido.")

            if escenario == "constantes":
                descripcion_escenario = "precios constantes"
            elif escenario == "historicos":
                descripcion_escenario = f"precios históricos de {anio}"
            else:
                descripcion_escenario = (
                    f"previsión {escenario_futuro.lower()} para {int(anio_futuro)}"
                )

            tabla = evaluar_alternativas_multicultivo(
                explotacion=explotacion,
                configuracion_actual=configuracion_actual,
                parametros_por_cultivo=parametros_por_cultivo,
                modelos=modelos,
                vida_util=vida_util,
                tasa_descuento=tasa_descuento_decimal,
            )

            superficie_total = sum(explotacion.values())
            nombres_visibles = {
                "Maiz": "maíz",
                "Arroz": "arroz",
                "Tomates": "tomate",
            }
            partes = [
                f"{hectareas:g} ha de {nombres_visibles[cultivo_nombre]}"
                for cultivo_nombre, hectareas in explotacion.items()
            ]
            descripcion_explotacion = (
                f"{superficie_total:g} ha distribuidas en " + ", ".join(partes)
            )
            explotacion_tecnica = explotacion

        # -------------------------------------------------
        # RANKING
        # -------------------------------------------------
        if tabla.empty:
            raise ValueError("No existen nuevas alternativas tecnológicas para evaluar.")

        ranking = tabla.sort_values("VAN", ascending=False).reset_index(drop=True).copy()
        ranking["Tecnologias"] = ranking["Tecnologias_nuevas"].apply(nombre_tecnologia)

        mejor = ranking.iloc[0]
        configuracion_recomendada = mejor["Configuracion_objetivo"]
        mejor_tecnologia = mejor["Tecnologias"]
        superficie_minima_mejor = formato_superficie_minima(
            mejor["Superficie_minima_rentable"]
        )

        # -------------------------------------------------
        # TEXTO DE RECOMENDACIÓN
        # -------------------------------------------------
        if mejor["VAN"] > 0:
            texto_recomendacion = (
                f"Para una explotación de {descripcion_explotacion}, bajo el escenario de "
                f"{descripcion_escenario}, la alternativa con mayor VAN es {mejor_tecnologia}. "
                f"Requiere una inversión de {formato_euros(mejor['Inversion'])}, presenta un VAN "
                f"estimado de {formato_euros(mejor['VAN'])} y un periodo de recuperación de "
                f"{formato_payback(mejor['Payback'], vida_util)}. Bajo estos mismos supuestos, "
                f"su superficie mínima estimada para alcanzar VAN ≥ 0 es {superficie_minima_mejor}. "
                f"El análisis utiliza una vida útil de {vida_util} años y una tasa de descuento "
                f"del {tasa_descuento:.1f} %. El resultado debe interpretarse como apoyo a la "
                f"decisión bajo los supuestos seleccionados."
            )
        else:
            texto_recomendacion = (
                f"Bajo el escenario de {descripcion_escenario}, ninguna de las alternativas "
                f"evaluadas presenta un VAN positivo con una vida útil de {vida_util} años y "
                f"una tasa de descuento del {tasa_descuento:.1f} %. La alternativa con mayor VAN "
                f"es {mejor_tecnologia} y su superficie mínima estimada para alcanzar VAN ≥ 0, "
                f"manteniendo estos supuestos, es {superficie_minima_mejor}."
            )

        # -------------------------------------------------
        # TABLA ECONÓMICA
        # -------------------------------------------------
        tabla_mostrar = pd.DataFrame(
            {
                "Tecnologias": ranking["Tecnologias"],
                "Inversion": ranking["Inversion"].apply(formato_numero_euros_tabla),
                "Superficie_minima": ranking["Superficie_minima_rentable"].apply(
                    formato_superficie_minima
                ),
                "ROI": ranking["ROI"].apply(formato_porcentaje_tabla),
                "Payback": ranking["Payback"].apply(
                    lambda x: formato_payback_tabla(x, vida_util)
                ),
                "VAN": ranking["VAN"].apply(formato_numero_euros_tabla),
                "TIR": ranking["TIR"].apply(formato_porcentaje_tabla),
            }
        )

        columnas_dash = [
            {"name": "Tecnologías", "id": "Tecnologias"},
            {"name": "Inversión", "id": "Inversion"},
            {"name": "Superficie mínima rentable", "id": "Superficie_minima"},
            {"name": "ROI", "id": "ROI"},
            {"name": "Payback", "id": "Payback"},
            {"name": "VAN", "id": "VAN"},
            {"name": "TIR", "id": "TIR"},
        ]

        # -------------------------------------------------
        # TABLA TÉCNICA
        # -------------------------------------------------
        if tipo_explotacion == "mono":
            tabla_tecnica = crear_comparacion_tecnica_cultivo(
                cultivo=cultivo,
                configuracion_actual=configuracion_actual,
                configuracion_recomendada=configuracion_recomendada,
            )
            columnas_tecnicas = [
                {"name": "Indicador", "id": "Indicador"},
                {"name": "Unidad", "id": "Unidad"},
                {"name": "Situación actual", "id": "Actual"},
                {"name": "Recomendada", "id": "Recomendada"},
                {"name": "Variación", "id": "Variacion"},
            ]
        else:
            tabla_tecnica = crear_comparacion_tecnica_multi(
                explotacion=explotacion_tecnica,
                configuracion_actual=configuracion_actual,
                configuracion_recomendada=configuracion_recomendada,
            )
            columnas_tecnicas = [
                {"name": "Cultivo", "id": "Cultivo"},
                {"name": "Indicador", "id": "Indicador"},
                {"name": "Unidad", "id": "Unidad"},
                {"name": "Situación actual", "id": "Actual"},
                {"name": "Recomendada", "id": "Recomendada"},
                {"name": "Variación", "id": "Variacion"},
            ]

        # -------------------------------------------------
        # GRÁFICOS
        # -------------------------------------------------
        fig_van = grafico_ranking_van(ranking)
        fig_payback = grafico_ranking_payback(ranking)
        fig_beneficio = grafico_beneficio_incremental(ranking)

        return (
            mejor_tecnologia,
            formato_euros(mejor["Inversion"]),
            formato_euros(mejor["VAN"]),
            formato_payback(mejor["Payback"], vida_util),
            formato_porcentaje(mejor["ROI"]),
            texto_recomendacion,
            tabla_mostrar.to_dict("records"),
            columnas_dash,
            fig_van,
            fig_payback,
            fig_beneficio,
            tabla_tecnica,
            columnas_tecnicas,
            "",
        )

    except Exception as error:
        return (
            "-", "-", "-", "-", "-", "",
            [], [], {}, {}, {}, [], [],
            html.Div(f"Error: {error}", style={"color": "red"}),
        )


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
