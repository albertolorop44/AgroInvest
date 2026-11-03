import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


OBJETIVOS_GLOBALES = [
    "Productividad_ha_h",
    "Consumo_L_ha",
    "Fitosanitarios_ha",
    "Abono_ha",
    "Pasadas_ha"
]


VARIABLES_GLOBALES = [
    "Cultivo",
    "RTK",
    "ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos"
]


VARIABLES_SEMILLAS = [
    "RTK",
    "ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos"
]


def crear_variables_interaccion(df):
    """
    Crea las variables utilizadas por el modelo
    de rendimiento, incluyendo interacciones
    cultivo x tecnología.
    """

    X = df[
        [
            "RTK",
            "ISOBUS",
            "Siembra_variable",
            "Abono_variable",
            "Corte_tramos"
        ]
    ].copy()

    cultivos = [
        "Maiz",
        "Arroz",
        "Tomates"
    ]

    tecnologias = [
        "RTK",
        "ISOBUS",
        "Siembra_variable",
        "Abono_variable",
        "Corte_tramos"
    ]

    for cultivo in cultivos:

        X[f"Cultivo_{cultivo}"] = (
            df["Cultivo"] == cultivo
        ).astype(int)

    for cultivo in cultivos:

        indicador_cultivo = (
            df["Cultivo"] == cultivo
        ).astype(int)

        for tecnologia in tecnologias:

            X[f"{tecnologia}_{cultivo}"] = (
                df[tecnologia]
                * indicador_cultivo
            )

    return X


def crear_preprocesador_global():
    """
    Crea el preprocesador utilizado por
    los modelos Ridge globales.
    """

    return ColumnTransformer(
        transformers=[
            (
                "categoricas",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                ["Cultivo"]
            ),
            (
                "numericas",
                StandardScaler(),
                [
                    "RTK",
                    "ISOBUS",
                    "Siembra_variable",
                    "Abono_variable",
                    "Corte_tramos"
                ]
            )
        ]
    )


def entrenar_modelos(df):
    """
    Entrena todos los modelos predictivos
    utilizados por AgroInvest.

    Devuelve:
    - modelos globales
    - modelos específicos de semillas
    - modelo de rendimiento
    - columnas del modelo de rendimiento
    """

    # ----------------------------------
    # Modelos globales
    # ----------------------------------

    X_global = df[
        VARIABLES_GLOBALES
    ].copy()

    preprocesador_global = (
        crear_preprocesador_global()
    )

    modelos_globales = {}

    for objetivo in OBJETIVOS_GLOBALES:

        modelo = Pipeline(
            steps=[
                (
                    "preprocesador",
                    clone(
                        preprocesador_global
                    )
                ),
                (
                    "modelo",
                    Ridge(alpha=1.0)
                )
            ]
        )

        modelo.fit(
            X_global,
            df[objetivo]
        )

        modelos_globales[
            objetivo
        ] = modelo

    # ----------------------------------
    # Modelos específicos de semillas
    # ----------------------------------

    modelos_semillas = {}

    for cultivo in [
        "Maiz",
        "Arroz",
        "Tomates"
    ]:

        df_cultivo = df[
            df["Cultivo"] == cultivo
        ].copy()

        X_semillas = df_cultivo[
            VARIABLES_SEMILLAS
        ].copy()

        y_semillas = (
            df_cultivo["Semillas_ha"]
        )

        modelo_semillas = Pipeline(
            steps=[
                (
                    "escalado",
                    StandardScaler()
                ),
                (
                    "modelo",
                    Ridge(alpha=1.0)
                )
            ]
        )

        modelo_semillas.fit(
            X_semillas,
            y_semillas
        )

        modelos_semillas[
            cultivo
        ] = modelo_semillas

    # ----------------------------------
    # Modelo de rendimiento
    # ----------------------------------

    X_rendimiento = (
        crear_variables_interaccion(df)
    )

    modelo_rendimiento = Pipeline(
        steps=[
            (
                "escalado",
                StandardScaler()
            ),
            (
                "modelo",
                Ridge(alpha=1.0)
            )
        ]
    )

    modelo_rendimiento.fit(
        X_rendimiento,
        df["Rend_t_ha"]
    )

    return {
        "modelos_globales":
            modelos_globales,

        "modelos_semillas":
            modelos_semillas,

        "modelo_rendimiento":
            modelo_rendimiento,

        "columnas_rendimiento":
            X_rendimiento.columns
    }


def predecir_resultados(
    cultivo,
    RTK,
    ISOBUS,
    Siembra_variable,
    Abono_variable,
    Corte_tramos,
    modelos
):
    """
    Predice los principales resultados técnicos
    de una configuración tecnológica.
    """

    entrada_global = pd.DataFrame({
        "Cultivo": [cultivo],
        "RTK": [RTK],
        "ISOBUS": [ISOBUS],
        "Siembra_variable": [
            Siembra_variable
        ],
        "Abono_variable": [
            Abono_variable
        ],
        "Corte_tramos": [
            Corte_tramos
        ]
    })

    resultados = {}

    # ----------------------------------
    # Modelos globales
    # ----------------------------------

    for objetivo in OBJETIVOS_GLOBALES:

        resultados[objetivo] = (
            modelos[
                "modelos_globales"
            ][objetivo]
            .predict(
                entrada_global
            )[0]
        )

    # ----------------------------------
    # Semillas
    # ----------------------------------

    entrada_semillas = pd.DataFrame({
        "RTK": [RTK],
        "ISOBUS": [ISOBUS],
        "Siembra_variable": [
            Siembra_variable
        ],
        "Abono_variable": [
            Abono_variable
        ],
        "Corte_tramos": [
            Corte_tramos
        ]
    })

    resultados["Semillas_ha"] = (
        modelos[
            "modelos_semillas"
        ][cultivo]
        .predict(
            entrada_semillas
        )[0]
    )

    # ----------------------------------
    # Rendimiento
    # ----------------------------------

    entrada_rendimiento = (
        crear_variables_interaccion(
            entrada_global
        )
    )

    entrada_rendimiento = (
        entrada_rendimiento[
            modelos[
                "columnas_rendimiento"
            ]
        ]
    )

    resultados["Rend_t_ha"] = (
        modelos[
            "modelo_rendimiento"
        ]
        .predict(
            entrada_rendimiento
        )[0]
    )

    return resultados
