import math

import plotly.express as px
import plotly.graph_objects as go


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
        height=390,
        margin={
            "l": 310,
            "r": 40,
            "t": 65,
            "b": 55,
        },
        title={
            "x": 0.02,
        },
        font={
            "size": 13,
        },
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

    datos = (
        datos
        .sort_values(
            "VAN",
            ascending=False,
        )
        .head(top_n)
        .copy()
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

    for _, fila in datos.iterrows():

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
        annotation_text="VAN = 0",
        annotation_position="top left",
    )

    fig.add_vline(
        x=superficie_actual,
        line_dash="dot",
        annotation_text=(
            f"Superficie actual: "
            f"{superficie_actual:g} ha"
        ),
        annotation_position="top",
    )

    fig.update_layout(
        title={
            "text":
                "VAN según superficie de la explotación",
            "x":
                0.02,
        },
        xaxis_title="Superficie (ha)",
        yaxis_title="VAN (€)",
        hovermode="closest",
        height=520,
        margin={
            "l": 80,
            "r": 40,
            "t": 80,
            "b": 65,
        },
        legend={
            "title":
                "Alternativas",
            "orientation":
                "h",
            "yanchor":
                "bottom",
            "y":
                -0.35,
            "xanchor":
                "left",
            "x":
                0,
        },
        font={
            "size": 13,
        },
    )

    fig.update_xaxes(
        range=[
            0,
            superficie_max,
        ],
        rangemode="tozero",
    )

    fig.update_yaxes(
        zeroline=False,
        tickformat=",.0f",
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
    )

    fig.update_layout(
        height=360,
        margin={
            "l": 60,
            "r": 40,
            "t": 65,
            "b": 50,
        },
    )

    return fig
