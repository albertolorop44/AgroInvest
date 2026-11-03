import plotly.express as px


def _nombre_tecnologia(texto):
    """
    Convierte los nombres internos en etiquetas más legibles.
    """

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

    partes_limpias = [
        reemplazos.get(
            parte,
            parte.replace("_", " ")
        )
        for parte in partes
    ]

    return " + ".join(partes_limpias)


def _preparar_tabla(tabla):
    """
    Crea una copia con nombres de tecnologías legibles.
    """

    datos = tabla.copy()

    datos["Tecnologias_legibles"] = (
        datos["Tecnologias_nuevas"]
        .apply(_nombre_tecnologia)
    )

    return datos


def grafico_ranking_van(
    tabla,
    top_n=8
):
    """
    Ranking de alternativas por VAN.
    """

    datos = _preparar_tabla(tabla)

    datos = (
        datos
        .sort_values(
            "VAN",
            ascending=False
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
            "Tecnologias_legibles": "Tecnologías"
        },
        hover_data={
            "Inversion": ":,.0f",
            "ROI": ":.2f",
            "Payback": ":.2f",
            "TIR": ":.2f",
            "Tecnologias_legibles": False
        }
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total ascending"
        },
        height=460,
        margin={
            "l": 240,
            "r": 40,
            "t": 70,
            "b": 60
        }
    )

    return fig


def grafico_ranking_payback(
    tabla,
    top_n=8
):
    """
    Ranking de alternativas por menor Payback.
    """

    datos = _preparar_tabla(tabla)

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
        y="Tecnologias_legibles",
        orientation="h",
        title="Ranking de alternativas por Payback",
        labels={
            "Payback": "Payback (años)",
            "Tecnologias_legibles": "Tecnologías"
        },
        hover_data={
            "Inversion": ":,.0f",
            "ROI": ":.2f",
            "VAN": ":,.0f",
            "TIR": ":.2f",
            "Tecnologias_legibles": False
        }
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total descending"
        },
        height=460,
        margin={
            "l": 240,
            "r": 40,
            "t": 70,
            "b": 60
        }
    )

    return fig


def grafico_beneficio_incremental(
    tabla,
    top_n=8
):
    """
    Beneficio incremental anual por alternativa.
    """

    datos = _preparar_tabla(tabla)

    datos = (
        datos
        .sort_values(
            "Beneficio_incremental_anual",
            ascending=False
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
                "Tecnologías"
        },
        hover_data={
            "Inversion": ":,.0f",
            "ROI": ":.2f",
            "Payback": ":.2f",
            "VAN": ":,.0f",
            "TIR": ":.2f",
            "Tecnologias_legibles": False
        }
    )

    fig.update_layout(
        yaxis={
            "categoryorder":
                "total ascending"
        },
        height=460,
        margin={
            "l": 240,
            "r": 40,
            "t": 70,
            "b": 60
        }
    )

    return fig


def grafico_escenarios_futuros(
    tabla_escenarios,
    variable="Precio_tonelada_venta"
):
    """
    Compara una variable entre escenarios
    conservador, central y alcista.
    """

    datos = (
        tabla_escenarios
        .reset_index()
        .rename(
            columns={
                "index": "Escenario"
            }
        )
    )

    fig = px.bar(
        datos,
        x="Escenario",
        y=variable,
        title=f"Comparación de escenarios: {variable}",
        labels={
            variable:
                variable.replace("_", " ")
        }
    )

    fig.update_layout(
        height=400,
        margin={
            "l": 60,
            "r": 40,
            "t": 70,
            "b": 60
        }
    )

    return fig
