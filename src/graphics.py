import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


VERDE_OSCURO = "#244C2B"
VERDE_MEDIO = "#4F7F3F"
VERDE_CLARO = "#8FB573"
VERDE_SUAVE = "#DCE9D4"
DORADO = "#C89535"
MARRON = "#8A6542"
AZUL_TECNO = "#4E7C8A"
FONDO_GRAFICO = "#F7FAF5"

PALETA_AGRO = [
    VERDE_OSCURO,
    VERDE_MEDIO,
    VERDE_CLARO,
    DORADO,
    MARRON,
    AZUL_TECNO,
]


def _nombre_tecnologia(texto):
    """
    Convierte nombres internos en etiquetas legibles.
    """

    if not isinstance(texto, str):
        return texto

    reemplazos = {
        "RTK_ISOBUS": "RTK + ISOBUS",
        "Siembra_variable": "Siembra variable",
        "Abono_variable": "Abono variable",
        "Corte_tramos": "Corte de tramos",
    }

    partes = [
        parte.strip()
        for parte in texto.split(",")
    ]

    partes_limpias = [
        reemplazos.get(
            parte,
            parte.replace("_", " ")
        )
        for parte in partes
    ]

    return " + ".join(partes_limpias)


def _preparar_tabla(tabla):

    datos = tabla.copy()

    datos["Tecnologias_legibles"] = (
        datos["Tecnologias_nuevas"]
        .apply(_nombre_tecnologia)
    )

    return datos


def _estilo_comun(fig):

    fig.update_layout(
        template="plotly_white",
        height=390,
        margin={
            "l": 310,
            "r": 40,
            "t": 65,
            "b": 55,
        },
        title={
            "x": 0.02,
            "font": {
                "size": 20,
                "color": VERDE_OSCURO,
            },
        },
        font={
            "size": 13,
            "color": "#26352A",
        },
        paper_bgcolor="#FFFFFF",
        plot_bgcolor=FONDO_GRAFICO,
    )

    fig.update_xaxes(
        gridcolor="#DCE5D7",
        linecolor="#AEBFA7",
        zerolinecolor="#7C9475",
    )
    fig.update_yaxes(
        gridcolor="#E6EDE2",
        linecolor="#AEBFA7",
    )

    return fig


def grafico_ranking_van(
    tabla,
    top_n=8,
):

    datos = _preparar_tabla(tabla)

    datos = (
        datos
        .sort_values(
            "VAN",
            ascending=False,
        )
        .head(top_n)
    )

    fig = px.bar(
        datos,
        x="VAN",
        y="Tecnologias_legibles",
        orientation="h",
        title="Ranking de alternativas por VAN",
        labels={
            "VAN": "VAN (€)",
            "Tecnologias_legibles": "",
        },
        color_discrete_sequence=[VERDE_MEDIO],
        hover_data={
            "Inversion": ":,.0f",
            "ROI": ":.2f",
            "Payback": ":.2f",
            "TIR": ":.2f",
            "Tecnologias_legibles": False,
        },
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total ascending",
        },
    )

    fig.update_xaxes(
        zeroline=True,
        zerolinewidth=2,
    )

    return _estilo_comun(fig)


def grafico_van_superficie(
    tabla,
    superficie_actual,
    vida_util=15,
    tasa_descuento=0.05,
    top_n=5,
):
    """
    Representa cómo evoluciona el VAN de las mejores
    alternativas al variar la superficie de la explotación.

    En multicultivo, el beneficio incremental por hectárea
    se interpreta manteniendo constante la proporción actual
    entre cultivos.
    """

    datos = _preparar_tabla(tabla)

    datos_ordenados = (
        datos
        .sort_values(
            "VAN",
            ascending=False,
        )
        .copy()
    )

    # Mostramos las mejores alternativas según VAN.
    datos = datos_ordenados.head(top_n).copy()

    # Además, si existe la alternativa RTK + ISOBUS por sí sola
    # y no está ya entre las mejores, la añadimos para poder
    # comparar visualmente su punto de rentabilidad.
    mascara_rtk_isobus = (
        datos_ordenados["Tecnologias_nuevas"]
        .astype(str)
        .str.strip()
        .eq("RTK_ISOBUS")
    )

    if mascara_rtk_isobus.any():

        fila_rtk_isobus = datos_ordenados[
            mascara_rtk_isobus
        ].head(1)

        ya_incluida = (
            datos["Tecnologias_nuevas"]
            .astype(str)
            .str.strip()
            .eq("RTK_ISOBUS")
            .any()
        )

        if not ya_incluida:
            datos = pd.concat(
                [
                    datos,
                    fila_rtk_isobus,
                ],
                ignore_index=True,
            )

    superficie_actual = float(superficie_actual)

    if superficie_actual <= 0:
        raise ValueError(
            "La superficie actual debe ser mayor que 0."
        )

    # Elegimos un rango que permita ver la situación actual
    # y, cuando sea posible, los puntos de VAN = 0.
    superficie_max = max(
        superficie_actual * 2,
        50.0,
    )

    if "Superficie_minima_rentable" in datos.columns:

        superficies_minimas = []

        for valor in datos[
            "Superficie_minima_rentable"
        ]:

            try:
                valor = float(valor)
            except (TypeError, ValueError):
                continue

            if math.isfinite(valor) and valor > 0:
                superficies_minimas.append(valor)

        if superficies_minimas:

            superficie_max = max(
                superficie_max,
                max(superficies_minimas) * 1.20,
            )

    numero_puntos = 61

    superficies = [
        superficie_max
        * i
        / (numero_puntos - 1)
        for i in range(numero_puntos)
    ]

    if tasa_descuento == 0:

        factor_actualizacion = float(
            vida_util
        )

    else:

        factor_actualizacion = sum(
            1
            / (
                (1 + tasa_descuento)
                ** anio
            )
            for anio in range(
                1,
                vida_util + 1,
            )
        )

    fig = go.Figure()

    for indice, (_, fila) in enumerate(datos.iterrows()):

        inversion = float(
            fila["Inversion"]
        )

        beneficio_incremental_anual = float(
            fila[
                "Beneficio_incremental_anual"
            ]
        )

        # Para monocultivo equivale al beneficio incremental/ha.
        # Para multicultivo es el beneficio medio por hectárea
        # manteniendo la proporción actual entre cultivos.
        beneficio_incremental_ha = (
            beneficio_incremental_anual
            / superficie_actual
        )

        valores_van = [
            (
                -inversion
                + (
                    beneficio_incremental_ha
                    * superficie
                    * factor_actualizacion
                )
            )
            for superficie in superficies
        ]

        fig.add_trace(
            go.Scatter(
                x=superficies,
                y=valores_van,
                mode="lines",
                line={
                    "color": PALETA_AGRO[indice % len(PALETA_AGRO)],
                    "width": 3,
                },
                name=fila[
                    "Tecnologias_legibles"
                ],
                hovertemplate=(
                    "<b>%{fullData.name}</b>"
                    "<br>Superficie: %{x:.1f} ha"
                    "<br>VAN: %{y:,.0f} €"
                    "<extra></extra>"
                ),
            )
        )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=VERDE_OSCURO,
        annotation_text="VAN = 0",
        annotation_position="top left",
    )

    fig.add_vline(
        x=superficie_actual,
        line_dash="dot",
        line_color=DORADO,
        annotation_text=(
            f"Superficie actual: "
            f"{superficie_actual:g} ha"
        ),
        annotation_position="top",
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor=FONDO_GRAFICO,
        title={
            "text":
                "VAN según superficie de la explotación",
            "x":
                0.02,
            "font": {
                "size": 20,
                "color": VERDE_OSCURO,
            },
        },
        xaxis_title="Superficie (ha)",
        yaxis_title="VAN (€)",
        hovermode="closest",
        height=620,
        margin={
            "l": 80,
            "r": 40,
            "t": 80,
            "b": 190,
        },
        legend={
            "title":
                "Alternativas",
            "orientation":
                "h",
            "yanchor":
                "top",
            "y":
                -0.28,
            "xanchor":
                "left",
            "x":
                0,
        },
        font={
            "size": 13,
            "color": "#26352A",
        },
    )

    fig.update_xaxes(
        range=[
            0,
            superficie_max,
        ],
        rangemode="tozero",
        title_standoff=14,
        gridcolor="#DCE5D7",
        linecolor="#AEBFA7",
    )

    fig.update_yaxes(
        zeroline=False,
        tickformat=",.0f",
        gridcolor="#DCE5D7",
        linecolor="#AEBFA7",
    )

    return fig


def grafico_ranking_payback(
    tabla,
    top_n=8,
):

    datos = _preparar_tabla(tabla)

    datos = datos[
        datos["Payback"].notna()
    ]

    datos = datos[
        datos["Payback"]
        != float("inf")
    ]

    datos = (
        datos
        .sort_values(
            "Payback",
            ascending=True,
        )
        .head(top_n)
    )

    fig = px.bar(
        datos,
        x="Payback",
        y="Tecnologias_legibles",
        orientation="h",
        title="Ranking de alternativas por Payback",
        labels={
            "Payback":
                "Payback (años)",
            "Tecnologias_legibles":
                "",
        },
        color_discrete_sequence=[VERDE_MEDIO],
        hover_data={
            "Inversion":
                ":,.0f",
            "ROI":
                ":.2f",
            "VAN":
                ":,.0f",
            "TIR":
                ":.2f",
            "Tecnologias_legibles":
                False,
        },
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "array",
            "categoryarray":
                datos[
                    "Tecnologias_legibles"
                ].tolist()[::-1],
        },
    )

    return _estilo_comun(fig)


def grafico_beneficio_incremental(
    tabla,
    top_n=8,
):

    datos = _preparar_tabla(tabla)

    datos = (
        datos
        .sort_values(
            "Beneficio_incremental_anual",
            ascending=False,
        )
        .head(top_n)
    )

    fig = px.bar(
        datos,
        x="Beneficio_incremental_anual",
        y="Tecnologias_legibles",
        orientation="h",
        title="Beneficio incremental anual por alternativa",
        labels={
            "Beneficio_incremental_anual":
                "Beneficio incremental anual (€)",
            "Tecnologias_legibles":
                "",
        },
        color_discrete_sequence=[VERDE_MEDIO],
        hover_data={
            "Inversion":
                ":,.0f",
            "ROI":
                ":.2f",
            "Payback":
                ":.2f",
            "VAN":
                ":,.0f",
            "TIR":
                ":.2f",
            "Tecnologias_legibles":
                False,
        },
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total ascending",
        },
    )

    fig.update_xaxes(
        zeroline=True,
        zerolinewidth=2,
    )

    return _estilo_comun(fig)


def grafico_escenarios_futuros(
    tabla_escenarios,
    variable="Precio_tonelada_venta",
):

    datos = (
        tabla_escenarios
        .reset_index()
        .rename(
            columns={
                "index":
                    "Escenario",
            }
        )
    )

    fig = px.bar(
        datos,
        x="Escenario",
        y=variable,
        title="Comparación de escenarios futuros",
        labels={
            variable:
                variable.replace(
                    "_",
                    " ",
                ),
        },
        color_discrete_sequence=[VERDE_MEDIO],
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor=FONDO_GRAFICO,
        height=360,
        margin={
            "l": 60,
            "r": 40,
            "t": 65,
            "b": 50,
        },
    )

    return fig
