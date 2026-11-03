import numpy as np
import numpy_financial as npf
import pandas as pd

from itertools import product

from src.model import predecir_resultados


COSTES_TECNOLOGIA = {
    "RTK_ISOBUS": 9500,
    "Siembra_variable": 35000,
    "Abono_variable": 25000,
    "Corte_tramos": 62000
}


TECNOLOGIAS_EVALUABLES = [
    "RTK_ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos"
]


def expandir_configuracion(configuracion):
    """
    Convierte la configuración utilizada por la app
    al formato esperado por el modelo predictivo.
    """

    return {
        "RTK": configuracion["RTK_ISOBUS"],
        "ISOBUS": configuracion["RTK_ISOBUS"],
        "Siembra_variable": configuracion["Siembra_variable"],
        "Abono_variable": configuracion["Abono_variable"],
        "Corte_tramos": configuracion["Corte_tramos"]
    }


def calcular_resultado_economico(
    cultivo,
    superficie,
    predicciones,
    parametros
):
    """
    Convierte las predicciones técnicas en resultados
    económicos por hectárea y totales.
    """

    precio_venta = parametros["Precio_tonelada_venta"]
    precio_gasoil = parametros["Precio_litro_gasoleoB"]
    precio_fitosanitario = parametros["Precio_litro_Fitosanitario"]
    precio_semilla = parametros["Precio_unitario_semilla"]
    precio_abono = parametros["Precio_Abono_kg"]
    gastos_fijos = parametros["Gastos_fijos_por_ha"]
    descuento_humedad = parametros["Descuento_humedad_por_t"]

    rendimiento = predicciones["Rend_t_ha"]
    consumo = predicciones["Consumo_L_ha"]
    fitosanitarios = predicciones["Fitosanitarios_ha"]
    semillas = predicciones["Semillas_ha"]
    abono = predicciones["Abono_ha"]
    pasadas = predicciones["Pasadas_ha"]

    ingreso_bruto_ha = (
        rendimiento * precio_venta
    )

    coste_gasoil_ha = (
        consumo
        * precio_gasoil
        * pasadas
    )

    coste_fitosanitarios_ha = (
        fitosanitarios
        * precio_fitosanitario
    )

    coste_semillas_ha = (
        semillas
        * precio_semilla
    )

    coste_abono_ha = (
        abono
        * precio_abono
    )

    if pd.isna(descuento_humedad):
        coste_secado_ha = 0
    else:
        coste_secado_ha = (
            -descuento_humedad
            * rendimiento
        )

    coste_total_ha = (
        coste_gasoil_ha
        + coste_fitosanitarios_ha
        + coste_semillas_ha
        + coste_abono_ha
        + gastos_fijos
        + coste_secado_ha
    )

    beneficio_ha = (
        ingreso_bruto_ha
        - coste_total_ha
    )

    beneficio_total = (
        beneficio_ha * superficie
    )

    return {
        "Ingreso_bruto_ha": ingreso_bruto_ha,
        "Coste_gasoil_ha": coste_gasoil_ha,
        "Coste_fitosanitarios_ha": coste_fitosanitarios_ha,
        "Coste_semillas_ha": coste_semillas_ha,
        "Coste_abono_ha": coste_abono_ha,
        "Coste_secado_ha": coste_secado_ha,
        "Gastos_fijos_ha": gastos_fijos,
        "Coste_total_ha": coste_total_ha,
        "Beneficio_por_ha": beneficio_ha,
        "Beneficio_total": beneficio_total
    }


def calcular_inversion_configuracion(
    configuracion_actual,
    configuracion_objetivo
):
    """
    Calcula la inversión necesaria para pasar
    de la configuración actual a la objetivo.
    """

    inversion_total = 0
    tecnologias_nuevas = []

    for tecnologia in COSTES_TECNOLOGIA:

        actual = configuracion_actual[tecnologia]
        objetivo = configuracion_objetivo[tecnologia]

        if actual == 0 and objetivo == 1:

            inversion_total += (
                COSTES_TECNOLOGIA[tecnologia]
            )

            tecnologias_nuevas.append(
                tecnologia
            )

    return inversion_total, tecnologias_nuevas


def calcular_roi(
    beneficio_anual,
    inversion
):
    """
    Calcula el ROI anual.
    """

    if inversion == 0:
        return np.nan

    return (
        beneficio_anual / inversion
    ) * 100


def calcular_payback(
    beneficio_anual,
    inversion
):
    """
    Calcula el periodo de recuperación
    de la inversión en años.
    """

    if beneficio_anual <= 0:
        return np.inf

    return (
        inversion / beneficio_anual
    )


def calcular_van(
    inversion,
    beneficio_anual,
    vida_util=15,
    tasa_descuento=0.05
):
    """
    Calcula el Valor Actual Neto.
    """

    flujos = (
        [-inversion]
        + [beneficio_anual] * vida_util
    )

    return npf.npv(
        tasa_descuento,
        flujos
    )


def calcular_tir(
    inversion,
    beneficio_anual,
    vida_util=15
):
    """
    Calcula la Tasa Interna de Retorno.
    """

    flujos = (
        [-inversion]
        + [beneficio_anual] * vida_util
    )

    tir = npf.irr(flujos)

    if np.isnan(tir):
        return np.nan

    return tir * 100


def comparar_configuraciones(
    cultivo,
    superficie,
    configuracion_actual,
    configuracion_objetivo,
    parametros,
    modelos
):
    """
    Compara económica y técnicamente una
    configuración actual con una objetivo.
    """

    config_actual_modelo = (
        expandir_configuracion(
            configuracion_actual
        )
    )

    config_objetivo_modelo = (
        expandir_configuracion(
            configuracion_objetivo
        )
    )

    pred_actual = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **config_actual_modelo
    )

    eco_actual = calcular_resultado_economico(
        cultivo=cultivo,
        superficie=superficie,
        predicciones=pred_actual,
        parametros=parametros
    )

    pred_objetivo = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **config_objetivo_modelo
    )

    eco_objetivo = calcular_resultado_economico(
        cultivo=cultivo,
        superficie=superficie,
        predicciones=pred_objetivo,
        parametros=parametros
    )

    beneficio_incremental_ha = (
        eco_objetivo["Beneficio_por_ha"]
        - eco_actual["Beneficio_por_ha"]
    )

    beneficio_incremental_anual = (
        beneficio_incremental_ha
        * superficie
    )

    inversion, tecnologias_nuevas = (
        calcular_inversion_configuracion(
            configuracion_actual,
            configuracion_objetivo
        )
    )

    return {
        "Beneficio_actual_ha":
            eco_actual["Beneficio_por_ha"],

        "Beneficio_objetivo_ha":
            eco_objetivo["Beneficio_por_ha"],

        "Beneficio_incremental_ha":
            beneficio_incremental_ha,

        "Beneficio_incremental_anual":
            beneficio_incremental_anual,

        "Inversion":
            inversion,

        "Tecnologias_nuevas":
            tecnologias_nuevas
    }


def evaluar_inversion(
    cultivo,
    superficie,
    configuracion_actual,
    configuracion_objetivo,
    parametros,
    modelos,
    vida_util=15,
    tasa_descuento=0.05
):
    """
    Evalúa completamente una inversión tecnológica.
    """

    resultado = comparar_configuraciones(
        cultivo=cultivo,
        superficie=superficie,
        configuracion_actual=configuracion_actual,
        configuracion_objetivo=configuracion_objetivo,
        parametros=parametros,
        modelos=modelos
    )

    inversion = resultado["Inversion"]

    beneficio_anual = (
        resultado["Beneficio_incremental_anual"]
    )

    resultado["ROI"] = calcular_roi(
        beneficio_anual,
        inversion
    )

    resultado["Payback"] = calcular_payback(
        beneficio_anual,
        inversion
    )

    resultado["VAN"] = calcular_van(
        inversion,
        beneficio_anual,
        vida_util,
        tasa_descuento
    )

    resultado["TIR"] = calcular_tir(
        inversion,
        beneficio_anual,
        vida_util
    )

    return resultado


def generar_configuraciones_objetivo(
    configuracion_actual
):
    """
    Genera todas las configuraciones tecnológicas
    válidas a partir de la situación actual.
    """

    configuraciones = []

    for valores in product(
        [0, 1],
        repeat=len(TECNOLOGIAS_EVALUABLES)
    ):

        configuracion = dict(
            zip(
                TECNOLOGIAS_EVALUABLES,
                valores
            )
        )

        valida = True

        # No eliminar tecnologías existentes
        for tecnologia in TECNOLOGIAS_EVALUABLES:

            if (
                configuracion_actual[tecnologia] == 1
                and configuracion[tecnologia] == 0
            ):
                valida = False
                break

        if not valida:
            continue

        # RTK + ISOBUS es requisito previo
        # para las tecnologías avanzadas
        tecnologias_avanzadas = [
            "Siembra_variable",
            "Abono_variable",
            "Corte_tramos"
        ]

        hay_tecnologia_avanzada = any(
            configuracion[tecnologia] == 1
            for tecnologia
            in tecnologias_avanzadas
        )

        if (
            hay_tecnologia_avanzada
            and configuracion["RTK_ISOBUS"] == 0
        ):
            continue

        # Excluir situación actual
        if (
            configuracion
            == configuracion_actual
        ):
            continue

        configuraciones.append(
            configuracion
        )

    return configuraciones


def evaluar_todas_alternativas(
    cultivo,
    superficie,
    configuracion_actual,
    parametros,
    modelos,
    vida_util=15,
    tasa_descuento=0.05
):
    """
    Evalúa todas las alternativas válidas
    para un cultivo.
    """

    alternativas = (
        generar_configuraciones_objetivo(
            configuracion_actual
        )
    )

    resultados = []

    for configuracion_objetivo in alternativas:

        resultado = evaluar_inversion(
            cultivo=cultivo,
            superficie=superficie,
            configuracion_actual=configuracion_actual,
            configuracion_objetivo=configuracion_objetivo,
            parametros=parametros,
            modelos=modelos,
            vida_util=vida_util,
            tasa_descuento=tasa_descuento
        )

        resultados.append({
            "Configuracion_objetivo":
                configuracion_objetivo,

            "Tecnologias_nuevas":
                ", ".join(
                    resultado[
                        "Tecnologias_nuevas"
                    ]
                ),

            "Inversion":
                resultado["Inversion"],

            "Beneficio_actual_ha":
                resultado[
                    "Beneficio_actual_ha"
                ],

            "Beneficio_objetivo_ha":
                resultado[
                    "Beneficio_objetivo_ha"
                ],

            "Beneficio_incremental_ha":
                resultado[
                    "Beneficio_incremental_ha"
                ],

            "Beneficio_incremental_anual":
                resultado[
                    "Beneficio_incremental_anual"
                ],

            "ROI":
                resultado["ROI"],

            "Payback":
                resultado["Payback"],

            "VAN":
                resultado["VAN"],

            "TIR":
                resultado["TIR"]
        })

    return pd.DataFrame(resultados)


def comparar_explotacion_multicultivo(
    explotacion,
    configuracion_actual,
    configuracion_objetivo,
    parametros_por_cultivo,
    modelos
):
    """
    Compara una inversión tecnológica para
    una explotación con varios cultivos.
    """

    resultados_cultivos = []

    beneficio_incremental_total = 0

    for cultivo, superficie in (
        explotacion.items()
    ):

        parametros = (
            parametros_por_cultivo[cultivo]
        )

        resultado = comparar_configuraciones(
            cultivo=cultivo,
            superficie=superficie,
            configuracion_actual=configuracion_actual,
            configuracion_objetivo=configuracion_objetivo,
            parametros=parametros,
            modelos=modelos
        )

        beneficio_incremental_total += (
            resultado[
                "Beneficio_incremental_anual"
            ]
        )

        resultados_cultivos.append({
            "Cultivo":
                cultivo,

            "Superficie":
                superficie,

            "Beneficio_actual_ha":
                resultado[
                    "Beneficio_actual_ha"
                ],

            "Beneficio_objetivo_ha":
                resultado[
                    "Beneficio_objetivo_ha"
                ],

            "Beneficio_incremental_ha":
                resultado[
                    "Beneficio_incremental_ha"
                ],

            "Beneficio_incremental_total":
                resultado[
                    "Beneficio_incremental_anual"
                ]
        })

    inversion, tecnologias_nuevas = (
        calcular_inversion_configuracion(
            configuracion_actual,
            configuracion_objetivo
        )
    )

    return (
        pd.DataFrame(
            resultados_cultivos
        ),
        beneficio_incremental_total,
        inversion,
        tecnologias_nuevas
    )


def evaluar_alternativas_multicultivo(
    explotacion,
    configuracion_actual,
    parametros_por_cultivo,
    modelos,
    vida_util=15,
    tasa_descuento=0.05
):
    """
    Evalúa todas las alternativas tecnológicas
    para una explotación multicultivo.
    """

    alternativas = (
        generar_configuraciones_objetivo(
            configuracion_actual
        )
    )

    resultados = []

    for configuracion_objetivo in alternativas:

        (
            detalle_cultivos,
            beneficio_incremental_total,
            inversion,
            tecnologias_nuevas
        ) = comparar_explotacion_multicultivo(
            explotacion=explotacion,
            configuracion_actual=configuracion_actual,
            configuracion_objetivo=configuracion_objetivo,
            parametros_por_cultivo=parametros_por_cultivo,
            modelos=modelos
        )

        roi = calcular_roi(
            beneficio_incremental_total,
            inversion
        )

        payback = calcular_payback(
            beneficio_incremental_total,
            inversion
        )

        van = calcular_van(
            inversion,
            beneficio_incremental_total,
            vida_util,
            tasa_descuento
        )

        tir = calcular_tir(
            inversion,
            beneficio_incremental_total,
            vida_util
        )

        resultados.append({
            "Configuracion_objetivo":
                configuracion_objetivo,

            "Tecnologias_nuevas":
                ", ".join(
                    tecnologias_nuevas
                ),

            "Inversion":
                inversion,

            "Beneficio_incremental_anual":
                beneficio_incremental_total,

            "ROI":
                roi,

            "Payback":
                payback,

            "VAN":
                van,

            "TIR":
                tir
        })

    return pd.DataFrame(resultados)
