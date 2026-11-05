import numpy as np
import numpy_financial as npf
import pandas as pd

from itertools import product

from src.model import predecir_resultados


COSTES_TECNOLOGIA = {
    "RTK_ISOBUS": 9500,
    "Siembra_variable": 35000,
    "Abono_variable": 25000,
    "Corte_tramos": 62000,
}

TECNOLOGIAS_EVALUABLES = [
    "RTK_ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos",
]


def expandir_configuracion(configuracion):
    """Convierte la configuración de la app al formato esperado por el modelo."""
    return {
        "RTK": configuracion["RTK_ISOBUS"],
        "ISOBUS": configuracion["RTK_ISOBUS"],
        "Siembra_variable": configuracion["Siembra_variable"],
        "Abono_variable": configuracion["Abono_variable"],
        "Corte_tramos": configuracion["Corte_tramos"],
    }


def ajustar_prediccion_rtk_isobus(pred_actual, pred_objetivo, configuracion_objetivo):
    """
    Aplica un escenario conservador cuando la configuración objetivo es
    exclusivamente RTK + ISOBUS.

    Como no existen observaciones históricas de RTK + ISOBUS aislado, se
    mantienen iguales a la situación actual el rendimiento, fitosanitarios,
    semillas y abono. La mejora procede únicamente de productividad,
    combustible y pasadas.
    """
    es_rtk_isobus_solo = (
        configuracion_objetivo["RTK_ISOBUS"] == 1
        and configuracion_objetivo["Siembra_variable"] == 0
        and configuracion_objetivo["Abono_variable"] == 0
        and configuracion_objetivo["Corte_tramos"] == 0
    )

    if not es_rtk_isobus_solo:
        return pred_objetivo

    pred_ajustada = pred_objetivo.copy()
    for variable in ["Rend_t_ha", "Fitosanitarios_ha", "Semillas_ha", "Abono_ha"]:
        pred_ajustada[variable] = pred_actual[variable]

    return pred_ajustada


def calcular_resultado_economico(cultivo, superficie, predicciones, parametros):
    """Convierte las predicciones técnicas en resultados económicos."""
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

    ingreso_bruto_ha = rendimiento * precio_venta
    coste_gasoil_ha = consumo * precio_gasoil * pasadas
    coste_fitosanitarios_ha = fitosanitarios * precio_fitosanitario
    coste_semillas_ha = semillas * precio_semilla
    coste_abono_ha = abono * precio_abono

    if pd.isna(descuento_humedad):
        coste_secado_ha = 0
    else:
        coste_secado_ha = -descuento_humedad * rendimiento

    coste_total_ha = (
        coste_gasoil_ha
        + coste_fitosanitarios_ha
        + coste_semillas_ha
        + coste_abono_ha
        + gastos_fijos
        + coste_secado_ha
    )

    beneficio_ha = ingreso_bruto_ha - coste_total_ha
    beneficio_total = beneficio_ha * superficie

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
        "Beneficio_total": beneficio_total,
    }


def calcular_inversion_configuracion(configuracion_actual, configuracion_objetivo):
    """Calcula solo la inversión de las tecnologías nuevas."""
    inversion_total = 0
    tecnologias_nuevas = []

    for tecnologia in COSTES_TECNOLOGIA:
        if configuracion_actual[tecnologia] == 0 and configuracion_objetivo[tecnologia] == 1:
            inversion_total += COSTES_TECNOLOGIA[tecnologia]
            tecnologias_nuevas.append(tecnologia)

    return inversion_total, tecnologias_nuevas


def calcular_roi(beneficio_anual, inversion):
    if inversion == 0:
        return np.nan
    return (beneficio_anual / inversion) * 100


def calcular_payback(beneficio_anual, inversion):
    if beneficio_anual <= 0:
        return np.inf
    return inversion / beneficio_anual


def calcular_van(inversion, beneficio_anual, vida_util=15, tasa_descuento=0.05):
    flujos = [-inversion] + [beneficio_anual] * vida_util
    return npf.npv(tasa_descuento, flujos)


def calcular_tir(inversion, beneficio_anual, vida_util=15):
    flujos = [-inversion] + [beneficio_anual] * vida_util
    tir = npf.irr(flujos)
    if np.isnan(tir):
        return np.nan
    return tir * 100


def calcular_factor_actualizacion(vida_util=15, tasa_descuento=0.05):
    """Valor actual de 1 € anual durante toda la vida útil."""
    if vida_util <= 0:
        return 0
    if tasa_descuento == 0:
        return float(vida_util)
    return sum(1 / ((1 + tasa_descuento) ** anio) for anio in range(1, vida_util + 1))


def calcular_superficie_minima_rentable(
    inversion,
    beneficio_incremental_ha,
    vida_util=15,
    tasa_descuento=0.05,
):
    """Calcula la superficie mínima necesaria para que el VAN sea >= 0."""
    if inversion <= 0:
        return 0.0

    if (
        beneficio_incremental_ha is None
        or pd.isna(beneficio_incremental_ha)
        or beneficio_incremental_ha <= 0
    ):
        return np.inf

    factor_actualizacion = calcular_factor_actualizacion(
        vida_util=vida_util,
        tasa_descuento=tasa_descuento,
    )

    if factor_actualizacion <= 0:
        return np.inf

    return inversion / (beneficio_incremental_ha * factor_actualizacion)


def comparar_configuraciones(
    cultivo,
    superficie,
    configuracion_actual,
    configuracion_objetivo,
    parametros,
    modelos,
):
    """Compara económica y técnicamente una configuración actual y una objetivo."""
    config_actual_modelo = expandir_configuracion(configuracion_actual)
    config_objetivo_modelo = expandir_configuracion(configuracion_objetivo)

    pred_actual = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **config_actual_modelo,
    )

    pred_objetivo = predecir_resultados(
        cultivo=cultivo,
        modelos=modelos,
        **config_objetivo_modelo,
    )

    pred_objetivo = ajustar_prediccion_rtk_isobus(
        pred_actual=pred_actual,
        pred_objetivo=pred_objetivo,
        configuracion_objetivo=configuracion_objetivo,
    )

    eco_actual = calcular_resultado_economico(
        cultivo=cultivo,
        superficie=superficie,
        predicciones=pred_actual,
        parametros=parametros,
    )

    eco_objetivo = calcular_resultado_economico(
        cultivo=cultivo,
        superficie=superficie,
        predicciones=pred_objetivo,
        parametros=parametros,
    )

    beneficio_incremental_ha = (
        eco_objetivo["Beneficio_por_ha"] - eco_actual["Beneficio_por_ha"]
    )
    beneficio_incremental_anual = beneficio_incremental_ha * superficie

    inversion, tecnologias_nuevas = calcular_inversion_configuracion(
        configuracion_actual,
        configuracion_objetivo,
    )

    return {
        "Beneficio_actual_ha": eco_actual["Beneficio_por_ha"],
        "Beneficio_objetivo_ha": eco_objetivo["Beneficio_por_ha"],
        "Beneficio_incremental_ha": beneficio_incremental_ha,
        "Beneficio_incremental_anual": beneficio_incremental_anual,
        "Inversion": inversion,
        "Tecnologias_nuevas": tecnologias_nuevas,
    }


def evaluar_inversion(
    cultivo,
    superficie,
    configuracion_actual,
    configuracion_objetivo,
    parametros,
    modelos,
    vida_util=15,
    tasa_descuento=0.05,
):
    resultado = comparar_configuraciones(
        cultivo=cultivo,
        superficie=superficie,
        configuracion_actual=configuracion_actual,
        configuracion_objetivo=configuracion_objetivo,
        parametros=parametros,
        modelos=modelos,
    )

    inversion = resultado["Inversion"]
    beneficio_anual = resultado["Beneficio_incremental_anual"]

    resultado["ROI"] = calcular_roi(beneficio_anual, inversion)
    resultado["Payback"] = calcular_payback(beneficio_anual, inversion)
    resultado["VAN"] = calcular_van(
        inversion,
        beneficio_anual,
        vida_util,
        tasa_descuento,
    )
    resultado["TIR"] = calcular_tir(
        inversion,
        beneficio_anual,
        vida_util,
    )
    resultado["Superficie_minima_rentable"] = calcular_superficie_minima_rentable(
        inversion=inversion,
        beneficio_incremental_ha=resultado["Beneficio_incremental_ha"],
        vida_util=vida_util,
        tasa_descuento=tasa_descuento,
    )

    return resultado


def generar_configuraciones_objetivo(configuracion_actual):
    """Genera todas las configuraciones válidas partiendo de la situación actual."""
    configuraciones = []

    for valores in product([0, 1], repeat=len(TECNOLOGIAS_EVALUABLES)):
        configuracion = dict(zip(TECNOLOGIAS_EVALUABLES, valores))

        # No eliminar tecnologías existentes.
        if any(
            configuracion_actual[tecnologia] == 1
            and configuracion[tecnologia] == 0
            for tecnologia in TECNOLOGIAS_EVALUABLES
        ):
            continue

        # Las tecnologías avanzadas requieren RTK + ISOBUS.
        tecnologias_avanzadas = [
            "Siembra_variable",
            "Abono_variable",
            "Corte_tramos",
        ]
        hay_tecnologia_avanzada = any(
            configuracion[tecnologia] == 1 for tecnologia in tecnologias_avanzadas
        )

        if hay_tecnologia_avanzada and configuracion["RTK_ISOBUS"] == 0:
            continue

        if configuracion == configuracion_actual:
            continue

        configuraciones.append(configuracion)

    return configuraciones


def evaluar_todas_alternativas(
    cultivo,
    superficie,
    configuracion_actual,
    parametros,
    modelos,
    vida_util=15,
    tasa_descuento=0.05,
):
    alternativas = generar_configuraciones_objetivo(configuracion_actual)
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
            tasa_descuento=tasa_descuento,
        )

        resultados.append(
            {
                "Configuracion_objetivo": configuracion_objetivo,
                "Tecnologias_nuevas": ", ".join(resultado["Tecnologias_nuevas"]),
                "Inversion": resultado["Inversion"],
                "Beneficio_actual_ha": resultado["Beneficio_actual_ha"],
                "Beneficio_objetivo_ha": resultado["Beneficio_objetivo_ha"],
                "Beneficio_incremental_ha": resultado["Beneficio_incremental_ha"],
                "Beneficio_incremental_anual": resultado["Beneficio_incremental_anual"],
                "ROI": resultado["ROI"],
                "Payback": resultado["Payback"],
                "VAN": resultado["VAN"],
                "TIR": resultado["TIR"],
                "Superficie_minima_rentable": resultado["Superficie_minima_rentable"],
            }
        )

    return pd.DataFrame(resultados)


def comparar_explotacion_multicultivo(
    explotacion,
    configuracion_actual,
    configuracion_objetivo,
    parametros_por_cultivo,
    modelos,
):
    """Compara una inversión común para una explotación con varios cultivos."""
    resultados_cultivos = []
    beneficio_incremental_total = 0

    for cultivo, superficie in explotacion.items():
        parametros = parametros_por_cultivo[cultivo]

        resultado = comparar_configuraciones(
            cultivo=cultivo,
            superficie=superficie,
            configuracion_actual=configuracion_actual,
            configuracion_objetivo=configuracion_objetivo,
            parametros=parametros,
            modelos=modelos,
        )

        beneficio_incremental_total += resultado["Beneficio_incremental_anual"]

        resultados_cultivos.append(
            {
                "Cultivo": cultivo,
                "Superficie": superficie,
                "Beneficio_actual_ha": resultado["Beneficio_actual_ha"],
                "Beneficio_objetivo_ha": resultado["Beneficio_objetivo_ha"],
                "Beneficio_incremental_ha": resultado["Beneficio_incremental_ha"],
                "Beneficio_incremental_total": resultado["Beneficio_incremental_anual"],
            }
        )

    inversion, tecnologias_nuevas = calcular_inversion_configuracion(
        configuracion_actual,
        configuracion_objetivo,
    )

    return (
        pd.DataFrame(resultados_cultivos),
        beneficio_incremental_total,
        inversion,
        tecnologias_nuevas,
    )


def evaluar_alternativas_multicultivo(
    explotacion,
    configuracion_actual,
    parametros_por_cultivo,
    modelos,
    vida_util=15,
    tasa_descuento=0.05,
):
    alternativas = generar_configuraciones_objetivo(configuracion_actual)
    resultados = []
    superficie_total = sum(explotacion.values())

    for configuracion_objetivo in alternativas:
        (
            detalle_cultivos,
            beneficio_incremental_total,
            inversion,
            tecnologias_nuevas,
        ) = comparar_explotacion_multicultivo(
            explotacion=explotacion,
            configuracion_actual=configuracion_actual,
            configuracion_objetivo=configuracion_objetivo,
            parametros_por_cultivo=parametros_por_cultivo,
            modelos=modelos,
        )

        roi = calcular_roi(beneficio_incremental_total, inversion)
        payback = calcular_payback(beneficio_incremental_total, inversion)
        van = calcular_van(
            inversion,
            beneficio_incremental_total,
            vida_util,
            tasa_descuento,
        )
        tir = calcular_tir(
            inversion,
            beneficio_incremental_total,
            vida_util,
        )

        if superficie_total > 0:
            beneficio_incremental_medio_ha = (
                beneficio_incremental_total / superficie_total
            )
        else:
            beneficio_incremental_medio_ha = 0

        superficie_minima_rentable = calcular_superficie_minima_rentable(
            inversion=inversion,
            beneficio_incremental_ha=beneficio_incremental_medio_ha,
            vida_util=vida_util,
            tasa_descuento=tasa_descuento,
        )

        resultados.append(
            {
                "Configuracion_objetivo": configuracion_objetivo,
                "Tecnologias_nuevas": ", ".join(tecnologias_nuevas),
                "Inversion": inversion,
                "Beneficio_incremental_anual": beneficio_incremental_total,
                "ROI": roi,
                "Payback": payback,
                "VAN": van,
                "TIR": tir,
                "Superficie_minima_rentable": superficie_minima_rentable,
            }
        )

    return pd.DataFrame(resultados)
