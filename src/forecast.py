import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression


VARIABLES_PRECIOS = [
    "Precio_tonelada_venta",
    "Precio_litro_gasoleoB",
    "Precio_litro_Fitosanitario",
    "Precio_unitario_semilla",
    "Precio_Abono_kg",
    "Gastos_fijos_por_ha"
]


def evaluar_tendencia_variable(
    df,
    cultivo,
    variable
):
    """
    Calcula el R² de una tendencia lineal temporal
    para una variable económica concreta.
    """

    datos = (
        df[df["Cultivo"] == cultivo]
        .groupby("Año")[variable]
        .mean()
        .reset_index()
        .sort_values("Año")
    )

    X = datos[["Año"]]
    y = datos[variable]

    modelo = LinearRegression()

    modelo.fit(
        X,
        y
    )

    r2 = modelo.score(
        X,
        y
    )

    return r2


def proyectar_variable_hibrida(
    df,
    cultivo,
    variable,
    anio_objetivo,
    n_ultimos=3
):
    """
    Proyecta una variable económica utilizando
    un método diferente según la estabilidad
    de su tendencia histórica.

    R² >= 0.70:
        tendencia lineal

    0.40 <= R² < 0.70:
        combinación de tendencia lineal
        y media reciente

    R² < 0.40:
        media de los últimos años
    """

    datos = (
        df[df["Cultivo"] == cultivo]
        .groupby("Año")[variable]
        .mean()
        .reset_index()
        .sort_values("Año")
    )

    X = datos[["Año"]]
    y = datos[variable]

    modelo = LinearRegression()

    modelo.fit(
        X,
        y
    )

    r2 = modelo.score(
        X,
        y
    )

    prediccion_lineal = modelo.predict(
        pd.DataFrame({
            "Año": [anio_objetivo]
        })
    )[0]

    # ----------------------------------
    # Tendencia clara
    # ----------------------------------

    if r2 >= 0.70:

        prediccion = prediccion_lineal

        metodo = "Tendencia lineal"

    # ----------------------------------
    # Tendencia moderada
    # ----------------------------------

    elif r2 >= 0.40:

        media_reciente = (
            datos
            .tail(n_ultimos)[variable]
            .mean()
        )

        prediccion = (
            0.5 * prediccion_lineal
            + 0.5 * media_reciente
        )

        metodo = "Tendencia suavizada"

    # ----------------------------------
    # Tendencia débil
    # ----------------------------------

    else:

        prediccion = (
            datos
            .tail(n_ultimos)[variable]
            .mean()
        )

        metodo = "Media últimos años"

    return {
        "Prediccion":
            prediccion,

        "R2":
            r2,

        "Metodo":
            metodo
    }


def proyectar_parametros_hibridos(
    df,
    cultivo,
    anio_objetivo
):
    """
    Proyecta todos los parámetros económicos
    utilizados por AgroInvest.
    """

    resultados = {}

    for variable in VARIABLES_PRECIOS:

        resultados[variable] = (
            proyectar_variable_hibrida(
                df=df,
                cultivo=cultivo,
                variable=variable,
                anio_objetivo=anio_objetivo
            )
        )

    return resultados


def crear_escenarios_futuros(
    parametros_centrales,
    variacion=0.10
):
    """
    Genera tres escenarios futuros:

    - Conservador
    - Central
    - Alcista

    El escenario conservador reduce el precio
    de venta y aumenta los costes.

    El escenario alcista aumenta el precio
    de venta y reduce los costes.
    """

    escenario_central = (
        parametros_centrales.copy()
    )

    escenario_conservador = (
        parametros_centrales.copy()
    )

    escenario_alcista = (
        parametros_centrales.copy()
    )

    # ----------------------------------
    # Precio de venta
    # ----------------------------------

    escenario_conservador[
        "Precio_tonelada_venta"
    ] *= (1 - variacion)

    escenario_alcista[
        "Precio_tonelada_venta"
    ] *= (1 + variacion)

    # ----------------------------------
    # Costes
    # ----------------------------------

    variables_coste = [
        "Precio_litro_gasoleoB",
        "Precio_litro_Fitosanitario",
        "Precio_unitario_semilla",
        "Precio_Abono_kg",
        "Gastos_fijos_por_ha"
    ]

    for variable in variables_coste:

        escenario_conservador[
            variable
        ] *= (1 + variacion)

        escenario_alcista[
            variable
        ] *= (1 - variacion)

    return {
        "Conservador":
            escenario_conservador,

        "Central":
            escenario_central,

        "Alcista":
            escenario_alcista
    }


def obtener_descuento_humedad_medio(
    df,
    cultivo
):
    """
    Devuelve el descuento medio por humedad
    del cultivo.

    En cultivos donde no aplica, devuelve NaN.
    """

    valores = df[
        df["Cultivo"] == cultivo
    ]["Descuento_humedad_por_t"]

    if valores.notna().sum() == 0:
        return np.nan

    return valores.mean()


def generar_escenarios_futuros_cultivo(
    df,
    cultivo,
    anio_objetivo,
    variacion=0.10
):
    """
    Genera los escenarios conservador, central
    y alcista para un cultivo concreto.
    """

    proyecciones = (
        proyectar_parametros_hibridos(
            df=df,
            cultivo=cultivo,
            anio_objetivo=anio_objetivo
        )
    )

    parametros_centrales = {
        variable:
            resultado["Prediccion"]

        for variable, resultado
        in proyecciones.items()
    }

    escenarios = (
        crear_escenarios_futuros(
            parametros_centrales,
            variacion=variacion
        )
    )

    descuento_humedad = (
        obtener_descuento_humedad_medio(
            df,
            cultivo
        )
    )

    for escenario in escenarios.values():

        escenario[
            "Descuento_humedad_por_t"
        ] = descuento_humedad

    return escenarios


def generar_escenarios_todos_cultivos(
    df,
    anio_objetivo,
    variacion=0.10
):
    """
    Genera los tres escenarios futuros
    para maíz, arroz y tomate.
    """

    cultivos = [
        "Maiz",
        "Arroz",
        "Tomates"
    ]

    escenarios_por_cultivo = {}

    for cultivo in cultivos:

        escenarios_por_cultivo[
            cultivo
        ] = (
            generar_escenarios_futuros_cultivo(
                df=df,
                cultivo=cultivo,
                anio_objetivo=anio_objetivo,
                variacion=variacion
            )
        )

    return escenarios_por_cultivo
