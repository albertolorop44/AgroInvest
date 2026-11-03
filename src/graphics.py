import pandas as pd
import plotly.express as px


def grafico_ranking_van(
    tabla,
    top_n=8
):
    """
    Muestra las alternativas tecnológicas
    ordenadas por VAN.
    """

    datos = (
        tabla
        .sort_values(
            "VAN",
            ascending=False
        )
        .head(top_n)
        .copy()
    )

    fig = px.bar(
        datos,
        x="VAN",
        y="Tecnologias_nuevas",
        orientation="h",
        title="Ranking de alternativas por VAN",
        labels={
            "VAN": "VAN (€)",
            "Tecnologias_nuevas":
                "Tecnologías"
        },
        hover_data=[
            "Inversion",
            "ROI",
            "Payback",
            "TIR"
        ]
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total ascending"
        }
    )

    return fig


def grafico_ranking_payback(
    tabla,
    top_n=8
):
    """
    Muestra las alternativas tecnológicas
    ordenadas por menor Payback.
    """

    datos = tabla.copy()

    datos = datos[
        datos["Payback"].notna()
    ]

    datos = datos[
        datos["Payback"] != float("inf")
    ]

    datos = (
        datos
        .sort_values(
            "Payback",
            ascending=True
        )
        .head(top_n)
    )

    fig = px.bar(
        datos,
        x="Payback",
        y="Tecnologias_nuevas",
        orientation="h",
        title="Ranking de alternativas por Payback",
        labels={
            "Payback":
                "Payback (años)",
            "Tecnologias_nuevas":
                "Tecnologías"
        },
        hover_data=[
            "Inversion",
            "ROI",
            "VAN",
            "TIR"
        ]
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total descending"
        }
    )

    return fig


def grafico_beneficio_incremental(
    tabla,
    top_n=8
):
    """
    Compara el beneficio incremental anual
    generado por cada alternativa.
    """

    datos = (
        tabla
        .sort_values(
            "Beneficio_incremental_anual",
            ascending=False
        )
        .head(top_n)
        .copy()
    )

    fig = px.bar(
        datos,
        x="Tecnologias_nuevas",
        y="Beneficio_incremental_anual",
        title="Beneficio incremental anual por alternativa",
        labels={
            "Tecnologias_nuevas":
                "Tecnologías",
            "Beneficio_incremental_anual":
                "Beneficio incremental anual (€)"
        },
        hover_data=[
            "Inversion",
            "ROI",
            "Payback",
            "VAN",
            "TIR"
        ]
    )

    fig.update_layout(
        xaxis_tickangle=-35
    )

    return fig


def grafico_escenarios_futuros(
    tabla_escenarios,
    variable="Precio_tonelada_venta"
):
    """
    Compara una variable económica entre
    los escenarios conservador, central y alcista.
    """

    datos = (
        tabla_escenarios
        .reset_index()
        .rename(
            columns={
                "index":
                    "Escenario"
            }
        )
    )

    fig = px.bar(
        datos,
        x="Escenario",
        y=variable,
        title=f"Comparación de escenarios: {variable}",
        labels={
            variable: variable.replace(
                "_",
                " "
            )
        }
    )

    return fig
