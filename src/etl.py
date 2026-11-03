import pandas as pd


COLUMNAS_TECNOLOGIA = [
    "GPS",
    "RTK",
    "ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos"
]


def cargar_datos(
    ruta_constantes,
    ruta_historicos,
    ruta_inversiones
):
    """
    Carga los tres ficheros principales de AgroInvest.
    """

    df_constantes = pd.read_excel(ruta_constantes)
    df_historicos = pd.read_excel(ruta_historicos)
    df_inversiones = pd.read_excel(ruta_inversiones)

    return (
        df_constantes,
        df_historicos,
        df_inversiones
    )


def limpiar_datos(df):
    """
    Realiza una limpieza básica del dataset.
    """

    df = df.copy()

    df.columns = df.columns.str.strip()

    df["Parcela"] = (
        df["Parcela"]
        .astype(str)
        .str.strip()
    )

    df["Cultivo"] = (
        df["Cultivo"]
        .astype(str)
        .str.strip()
    )

    return df


def crear_iit(df):
    """
    Calcula el Índice de Intensidad Tecnológica (IIT)
    como suma de las tecnologías instaladas.
    """

    df = df.copy()

    df["IIT"] = (
        df[COLUMNAS_TECNOLOGIA]
        .sum(axis=1)
    )

    return df


def crear_precio_unitario_semilla(df):
    """
    Calcula el precio unitario de la semilla
    a partir del coste por hectárea y la cantidad utilizada.
    """

    df = df.copy()

    df["Precio_unitario_semilla"] = (
        df["Precio_Semillas_ha"]
        / df["Semillas_ha"]
    )

    return df


def preparar_datos(
    ruta_constantes,
    ruta_historicos,
    ruta_inversiones
):
    """
    Carga, limpia y prepara todos los datos
    necesarios para AgroInvest.
    """

    (
        df_constantes,
        df_historicos,
        df_inversiones
    ) = cargar_datos(
        ruta_constantes,
        ruta_historicos,
        ruta_inversiones
    )

    # Limpieza
    df_constantes = limpiar_datos(
        df_constantes
    )

    df_historicos = limpiar_datos(
        df_historicos
    )

    # IIT
    df_constantes = crear_iit(
        df_constantes
    )

    df_historicos = crear_iit(
        df_historicos
    )

    # Precio unitario de semilla
    df_constantes = crear_precio_unitario_semilla(
        df_constantes
    )

    df_historicos = crear_precio_unitario_semilla(
        df_historicos
    )

    return (
        df_constantes,
        df_historicos,
        df_inversiones
    )
