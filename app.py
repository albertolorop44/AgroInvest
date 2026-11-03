from pathlib import Path

import pandas as pd

from dash import (
    Dash,
    Input,
    Output,
    State,
    dcc,
    html,
    dash_table
)

from src.etl import preparar_datos
from src.model import entrenar_modelos
from src.finance import evaluar_todas_alternativas
from src.graphics import (
    grafico_ranking_van,
    grafico_ranking_payback,
    grafico_beneficio_incremental
)


# =========================================================
# RUTAS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

RUTA_CONSTANTES = (
    BASE_DIR
    / "data"
    / "precios_constantes.xlsx"
)

RUTA_HISTORICOS = (
    BASE_DIR
    / "data"
    / "precios_historicos.xlsx"
)

RUTA_INVERSIONES = (
    BASE_DIR
    / "data"
    / "inversiones_tecnologia.xlsx"
)


# =========================================================
# DATOS
# =========================================================

(
    df_constantes,
    df_historicos,
    df_inversiones
) = preparar_datos(
    RUTA_CONSTANTES,
    RUTA_HISTORICOS,
    RUTA_INVERSIONES
)


# =========================================================
# MODELOS
# =========================================================

modelos = entrenar_modelos(
    df_constantes
)


# =========================================================
# PARÁMETROS ECONÓMICOS
# =========================================================

def obtener_parametros_constantes(cultivo):

    datos = df_constantes[
        df_constantes["Cultivo"] == cultivo
    ]

    return {
        "Precio_tonelada_venta":
            datos["Precio_tonelada_venta"].mean(),

        "Precio_litro_gasoleoB":
            datos["Precio_litro_gasoleoB"].mean(),

        "Precio_litro_Fitosanitario":
            datos["Precio_litro_Fitosanitario"].mean(),

        "Precio_unitario_semilla":
            datos["Precio_unitario_semilla"].mean(),

        "Precio_Abono_kg":
            datos["Precio_Abono_kg"].mean(),

        "Gastos_fijos_por_ha":
            datos["Gastos_fijos_por_ha"].mean(),

        "Descuento_humedad_por_t":
            datos["Descuento_humedad_por_t"].mean()
    }


def obtener_parametros_historicos(
    cultivo,
    anio
):

    datos = df_historicos[
        (df_historicos["Cultivo"] == cultivo)
        &
        (df_historicos["Año"] == anio)
    ]

    if datos.empty:
        raise ValueError(
            "No existen datos para ese cultivo y año."
        )

    return {
        "Precio_tonelada_venta":
            datos["Precio_tonelada_venta"].mean(),

        "Precio_litro_gasoleoB":
            datos["Precio_litro_gasoleoB"].mean(),

        "Precio_litro_Fitosanitario":
            datos["Precio_litro_Fitosanitario"].mean(),

        "Precio_unitario_semilla":
            datos["Precio_unitario_semilla"].mean(),

        "Precio_Abono_kg":
            datos["Precio_Abono_kg"].mean(),

        "Gastos_fijos_por_ha":
            datos["Gastos_fijos_por_ha"].mean(),

        "Descuento_humedad_por_t":
            datos["Descuento_humedad_por_t"].mean()
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
        "Corte_tramos": "Corte de tramos"
    }

    partes = [
        parte.strip()
        for parte in texto.split(",")
    ]

    return " + ".join(
        reemplazos.get(
            parte,
            parte.replace("_", " ")
        )
        for parte in partes
    )


def crear_configuracion_actual(
    tecnologias_seleccionadas
):

    tecnologias_seleccionadas = (
        tecnologias_seleccionadas or []
    )

    configuracion = {
        "RTK_ISOBUS":
            int(
                "RTK_ISOBUS"
                in tecnologias_seleccionadas
            ),

        "Siembra_variable":
            int(
                "Siembra_variable"
                in tecnologias_seleccionadas
            ),

        "Abono_variable":
            int(
                "Abono_variable"
                in tecnologias_seleccionadas
            ),

        "Corte_tramos":
            int(
                "Corte_tramos"
                in tecnologias_seleccionadas
            )
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

    return (
        f"{valor:,.0f} €"
        .replace(",", ".")
    )


def formato_payback(valor):

    if pd.isna(valor):
        return "-"

    if valor == float("inf"):
        return "No recuperable"

    return f"{valor:.2f} años"


def formato_porcentaje(valor):

    if pd.isna(valor):
        return "-"

    return f"{valor:.1f} %"


def formato_numero_euros_tabla(valor):

    if pd.isna(valor):
        return "-"

    return (
        f"{valor:,.0f} €"
        .replace(",", ".")
    )


def formato_porcentaje_tabla(valor):

    if pd.isna(valor):
        return "-"

    return f"{valor:.2f} %"


def formato_payback_tabla(valor):

    if pd.isna(valor):
        return "-"

    if valor == float("inf"):
        return "No recuperable"

    return f"{valor:.2f}"


# =========================================================
# APP
# =========================================================

app = Dash(__name__)

server = app.server

app.title = "AgroInvest"


# =========================================================
# ESTILOS
# =========================================================

ESTILO_TARJETA = {
    "padding": "20px",
    "border": "1px solid #dddddd",
    "borderRadius": "12px",
    "backgroundColor": "#ffffff",
    "minHeight": "125px"
}


ESTILO_INPUT = {
    "width": "100%",
    "height": "38px"
}


# =========================================================
# LAYOUT
# =========================================================

app.layout = html.Div(

    style={
        "maxWidth": "1400px",
        "margin": "0 auto",
        "padding": "28px",
        "fontFamily": "Arial, sans-serif"
    },

    children=[

        html.H1(
            "AgroInvest",
            style={
                "marginBottom": "4px",
                "fontSize": "38px"
            }
        ),

        html.P(
            "Análisis y recomendación de inversiones "
            "en tecnologías de Agricultura 4.0.",
            style={
                "fontSize": "18px",
                "marginTop": "0",
                "marginBottom": "25px"
            }
        ),

        html.Hr(),

        # =================================================
        # 1. EXPLOTACIÓN
        # =================================================

        html.H2(
            "1. Configuración de la explotación"
        ),

        html.Div(

            style={
                "display": "grid",
                "gridTemplateColumns":
                    "1fr 1fr 1fr",
                "gap": "22px"
            },

            children=[

                html.Div([
                    html.Label(
                        "Cultivo"
                    ),

                    dcc.Dropdown(
                        id="cultivo",
                        options=[
                            {
                                "label": "Maíz",
                                "value": "Maiz"
                            },
                            {
                                "label": "Arroz",
                                "value": "Arroz"
                            },
                            {
                                "label": "Tomate",
                                "value": "Tomates"
                            }
                        ],
                        value="Maiz",
                        clearable=False
                    )
                ]),

                html.Div([
                    html.Label(
                        "Superficie (ha)"
                    ),

                    dcc.Input(
                        id="superficie",
                        type="number",
                        value=100,
                        min=1,
                        step=1,
                        style=ESTILO_INPUT
                    )
                ]),

                html.Div([
                    html.Label(
                        "Escenario económico"
                    ),

                    dcc.Dropdown(
                        id="escenario",

                        options=[
                            {
                                "label":
                                    "Precios constantes",
                                "value":
                                    "constantes"
                            },
                            {
                                "label":
                                    "Precios históricos",
                                "value":
                                    "historicos"
                            },
                            {
                                "label":
                                    "Personalizado",
                                "value":
                                    "personalizado"
                            }
                        ],

                        value="constantes",
                        clearable=False
                    )
                ])
            ]
        ),

        html.Br(),

        html.Label(
            "Tecnologías instaladas actualmente",
            style={
                "fontWeight": "bold"
            }
        ),

        dcc.Checklist(
            id="tecnologias-actuales",

            options=[
                {
                    "label":
                        " RTK + ISOBUS",
                    "value":
                        "RTK_ISOBUS"
                },
                {
                    "label":
                        " Siembra variable",
                    "value":
                        "Siembra_variable"
                },
                {
                    "label":
                        " Abono variable",
                    "value":
                        "Abono_variable"
                },
                {
                    "label":
                        " Corte de tramos",
                    "value":
                        "Corte_tramos"
                }
            ],

            value=[],

            labelStyle={
                "display": "block",
                "marginBottom": "9px"
            },

            style={
                "marginTop": "12px"
            }
        ),

        html.P(
            "GPS se considera la tecnología base. "
            "RTK + ISOBUS es requisito previo para "
            "las tecnologías avanzadas.",
            style={
                "fontSize": "13px",
                "marginTop": "18px"
            }
        ),

        html.Hr(),

        # =================================================
        # 2. ECONOMÍA
        # =================================================

        html.H2(
            "2. Condiciones económicas"
        ),

        html.Div(
            id="bloque-historico",

            children=[
                html.Label(
                    "Año histórico"
                ),

                dcc.Dropdown(
                    id="anio-historico",
                    clearable=False
                )
            ]
        ),

        html.Div(
            id="bloque-personalizado",

            children=[

                html.H4(
                    "Parámetros personalizados"
                ),

                html.Div(

                    style={
                        "display": "grid",
                        "gridTemplateColumns":
                            "repeat(3, 1fr)",
                        "gap": "15px"
                    },

                    children=[

                        dcc.Input(
                            id="precio-venta",
                            type="number",
                            placeholder="Precio venta €/t"
                        ),

                        dcc.Input(
                            id="precio-gasoil",
                            type="number",
                            placeholder="Gasóleo €/L"
                        ),

                        dcc.Input(
                            id="precio-fitosanitario",
                            type="number",
                            placeholder="Fitosanitario €/L"
                        ),

                        dcc.Input(
                            id="precio-semilla",
                            type="number",
                            placeholder="Precio unitario semilla"
                        ),

                        dcc.Input(
                            id="precio-abono",
                            type="number",
                            placeholder="Abono €/kg"
                        ),

                        dcc.Input(
                            id="gastos-fijos",
                            type="number",
                            placeholder="Gastos fijos €/ha"
                        ),

                        dcc.Input(
                            id="descuento-humedad",
                            type="number",
                            placeholder="Descuento humedad €/t"
                        )
                    ]
                )
            ]
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
                "borderRadius": "6px"
            }
        ),

        html.Hr(),

        # =================================================
        # 3. RECOMENDACIÓN
        # =================================================

        html.H2(
            "3. Recomendación"
        ),

        html.Div(
            id="mensaje-error"
        ),

        html.Div(

            style={
                "display": "grid",
                "gridTemplateColumns":
                    "1.7fr 1fr 1fr 1fr 1fr",
                "gap": "15px",
                "marginBottom": "20px"
            },

            children=[

                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4(
                            "Mejor inversión"
                        ),
                        html.Div(
                            id="kpi-tecnologias",
                            style={
                                "fontSize": "18px",
                                "fontWeight": "bold",
                                "lineHeight": "1.4"
                            }
                        )
                    ]
                ),

                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4("Inversión"),
                        html.H3(
                            id="kpi-inversion"
                        )
                    ]
                ),

                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4("VAN"),
                        html.H3(
                            id="kpi-van"
                        )
                    ]
                ),

                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4("Payback"),
                        html.H3(
                            id="kpi-payback"
                        )
                    ]
                ),

                html.Div(
                    style=ESTILO_TARJETA,
                    children=[
                        html.H4("ROI"),
                        html.H3(
                            id="kpi-roi"
                        )
                    ]
                )
            ]
        ),

        # Interpretación automática

        html.Div(
            id="texto-recomendacion",

            style={
                "padding": "16px 18px",
                "marginBottom": "25px",
                "borderLeft": "4px solid #555",
                "backgroundColor": "#f7f7f7",
                "fontSize": "16px",
                "lineHeight": "1.5"
            }
        ),

        # Tabla

        dash_table.DataTable(
            id="tabla-ranking",

            page_size=8,

            style_table={
                "overflowX": "auto",
                "borderRadius": "8px"
            },

            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "whiteSpace": "normal",
                "height": "auto",
                "fontFamily": "Arial",
                "fontSize": "14px"
            },

            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f5f5f5"
            },

            style_data_conditional=[
                {
                    "if": {
                        "column_id": "VAN"
                    },
                    "fontWeight": "500"
                }
            ]
        ),

        html.Br(),

        dcc.Graph(
            id="grafico-van"
        ),

        dcc.Graph(
            id="grafico-payback"
        ),

        dcc.Graph(
            id="grafico-beneficio"
        )
    ]
)


# =========================================================
# MOSTRAR CONTROLES ECONÓMICOS
# =========================================================

@app.callback(
    Output(
        "bloque-historico",
        "style"
    ),
    Output(
        "bloque-personalizado",
        "style"
    ),
    Input(
        "escenario",
        "value"
    )
)
def mostrar_controles_escenario(
    escenario
):

    oculto = {
        "display": "none"
    }

    visible = {
        "display": "block",
        "marginBottom": "15px"
    }

    if escenario == "historicos":
        return visible, oculto

    if escenario == "personalizado":
        return oculto, visible

    return oculto, oculto


# =========================================================
# AÑOS HISTÓRICOS
# =========================================================

@app.callback(
    Output(
        "anio-historico",
        "options"
    ),
    Output(
        "anio-historico",
        "value"
    ),
    Input(
        "cultivo",
        "value"
    )
)
def actualizar_anios(cultivo):

    anios = sorted(
        df_historicos[
            df_historicos["Cultivo"]
            == cultivo
        ]["Año"]
        .dropna()
        .unique()
        .tolist()
    )

    opciones = [
        {
            "label": str(anio),
            "value": int(anio)
        }
        for anio in anios
    ]

    valor = (
        int(anios[-1])
        if anios
        else None
    )

    return opciones, valor


# =========================================================
# CALLBACK PRINCIPAL
# =========================================================

@app.callback(
    Output(
        "kpi-tecnologias",
        "children"
    ),
    Output(
        "kpi-inversion",
        "children"
    ),
    Output(
        "kpi-van",
        "children"
    ),
    Output(
        "kpi-payback",
        "children"
    ),
    Output(
        "kpi-roi",
        "children"
    ),
    Output(
        "texto-recomendacion",
        "children"
    ),
    Output(
        "tabla-ranking",
        "data"
    ),
    Output(
        "tabla-ranking",
        "columns"
    ),
    Output(
        "grafico-van",
        "figure"
    ),
    Output(
        "grafico-payback",
        "figure"
    ),
    Output(
        "grafico-beneficio",
        "figure"
    ),
    Output(
        "mensaje-error",
        "children"
    ),

    Input(
        "boton-analizar",
        "n_clicks"
    ),

    State(
        "cultivo",
        "value"
    ),
    State(
        "superficie",
        "value"
    ),
    State(
        "escenario",
        "value"
    ),
    State(
        "anio-historico",
        "value"
    ),
    State(
        "tecnologias-actuales",
        "value"
    ),

    State(
        "precio-venta",
        "value"
    ),
    State(
        "precio-gasoil",
        "value"
    ),
    State(
        "precio-fitosanitario",
        "value"
    ),
    State(
        "precio-semilla",
        "value"
    ),
    State(
        "precio-abono",
        "value"
    ),
    State(
        "gastos-fijos",
        "value"
    ),
    State(
        "descuento-humedad",
        "value"
    )
)
def analizar_inversiones(
    n_clicks,
    cultivo,
    superficie,
    escenario,
    anio,
    tecnologias_actuales,
    precio_venta,
    precio_gasoil,
    precio_fitosanitario,
    precio_semilla,
    precio_abono,
    gastos_fijos,
    descuento_humedad
):

    if n_clicks == 0:

        return (
            "-",
            "-",
            "-",
            "-",
            "-",
            "",
            [],
            [],
            {},
            {},
            {},
            ""
        )

    try:

        if (
            superficie is None
            or superficie <= 0
        ):
            raise ValueError(
                "La superficie debe ser mayor que 0."
            )

        configuracion_actual = (
            crear_configuracion_actual(
                tecnologias_actuales
            )
        )

        # =============================================
        # ESCENARIO ECONÓMICO
        # =============================================

        if escenario == "constantes":

            parametros = (
                obtener_parametros_constantes(
                    cultivo
                )
            )

        elif escenario == "historicos":

            parametros = (
                obtener_parametros_historicos(
                    cultivo,
                    anio
                )
            )

        elif escenario == "personalizado":

            valores = [
                precio_venta,
                precio_gasoil,
                precio_fitosanitario,
                precio_semilla,
                precio_abono,
                gastos_fijos
            ]

            if any(
                valor is None
                for valor in valores
            ):
                raise ValueError(
                    "Completa todos los parámetros "
                    "del escenario personalizado."
                )

            parametros = {
                "Precio_tonelada_venta":
                    precio_venta,

                "Precio_litro_gasoleoB":
                    precio_gasoil,

                "Precio_litro_Fitosanitario":
                    precio_fitosanitario,

                "Precio_unitario_semilla":
                    precio_semilla,

                "Precio_Abono_kg":
                    precio_abono,

                "Gastos_fijos_por_ha":
                    gastos_fijos,

                "Descuento_humedad_por_t":
                    descuento_humedad
            }

        else:

            raise ValueError(
                "Escenario económico no válido."
            )

        # =============================================
        # EVALUACIÓN
        # =============================================

        tabla = evaluar_todas_alternativas(
            cultivo=cultivo,
            superficie=superficie,
            configuracion_actual=
                configuracion_actual,
            parametros=parametros,
            modelos=modelos,
            vida_util=15,
            tasa_descuento=0.05
        )

        if tabla.empty:

            raise ValueError(
                "No existen nuevas alternativas "
                "tecnológicas para evaluar."
            )

        ranking = (
            tabla
            .sort_values(
                "VAN",
                ascending=False
            )
            .reset_index(drop=True)
        )

        mejor = ranking.iloc[0]

        # =============================================
        # NOMBRES
        # =============================================

        ranking = ranking.copy()

        ranking["Tecnologias"] = (
            ranking[
                "Tecnologias_nuevas"
            ]
            .apply(
                nombre_tecnologia
            )
        )

        mejor_tecnologia = (
            nombre_tecnologia(
                mejor[
                    "Tecnologias_nuevas"
                ]
            )
        )

        # =============================================
        # INTERPRETACIÓN
        # =============================================

        if mejor["VAN"] > 0:

            texto_recomendacion = (
                f"Para una explotación de "
                f"{superficie:g} ha de "
                f"{cultivo.lower()}, la alternativa "
                f"con mayor VAN es "
                f"{mejor_tecnologia}. "
                f"Requiere una inversión de "
                f"{formato_euros(mejor['Inversion'])}, "
                f"presenta un VAN estimado de "
                f"{formato_euros(mejor['VAN'])} "
                f"y un periodo de recuperación de "
                f"{formato_payback(mejor['Payback'])}. "
                f"El resultado debe interpretarse "
                f"como apoyo a la decisión bajo los "
                f"supuestos económicos seleccionados."
            )

        else:

            texto_recomendacion = (
                "Ninguna de las alternativas evaluadas "
                "presenta un VAN positivo bajo las "
                "condiciones seleccionadas."
            )

        # =============================================
        # TABLA FORMATEADA
        # =============================================

        tabla_mostrar = pd.DataFrame({
            "Tecnologias":
                ranking["Tecnologias"],

            "Inversion":
                ranking["Inversion"]
                .apply(
                    formato_numero_euros_tabla
                ),

            "ROI":
                ranking["ROI"]
                .apply(
                    formato_porcentaje_tabla
                ),

            "Payback":
                ranking["Payback"]
                .apply(
                    formato_payback_tabla
                ),

            "VAN":
                ranking["VAN"]
                .apply(
                    formato_numero_euros_tabla
                ),

            "TIR":
                ranking["TIR"]
                .apply(
                    formato_porcentaje_tabla
                )
        })

        columnas_dash = [
            {
                "name": "Tecnologías",
                "id": "Tecnologias"
            },
            {
                "name": "Inversión",
                "id": "Inversion"
            },
            {
                "name": "ROI",
                "id": "ROI"
            },
            {
                "name": "Payback (años)",
                "id": "Payback"
            },
            {
                "name": "VAN",
                "id": "VAN"
            },
            {
                "name": "TIR",
                "id": "TIR"
            }
        ]

        # =============================================
        # GRÁFICOS
        # =============================================

        fig_van = grafico_ranking_van(
            ranking
        )

        fig_payback = (
            grafico_ranking_payback(
                ranking
            )
        )

        fig_beneficio = (
            grafico_beneficio_incremental(
                ranking
            )
        )

        return (
            mejor_tecnologia,

            formato_euros(
                mejor["Inversion"]
            ),

            formato_euros(
                mejor["VAN"]
            ),

            formato_payback(
                mejor["Payback"]
            ),

            formato_porcentaje(
                mejor["ROI"]
            ),

            texto_recomendacion,

            tabla_mostrar.to_dict(
                "records"
            ),

            columnas_dash,

            fig_van,

            fig_payback,

            fig_beneficio,

            ""
        )

    except Exception as error:

        return (
            "-",
            "-",
            "-",
            "-",
            "-",
            "",
            [],
            [],
            {},
            {},
            {},
            html.Div(
                f"Error: {error}",
                style={
                    "color": "red"
                }
            )
        )


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
