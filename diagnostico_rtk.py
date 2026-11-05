from pathlib import Path

import pandas as pd

from src.etl import preparar_datos
from src.model import (
    entrenar_modelos,
    predecir_resultados
)
from src.finance import (
    expandir_configuracion,
    calcular_resultado_economico
)


# =========================================================
# 1. RUTAS
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
# 2. CARGA DE DATOS
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
# 3. ENTRENAR MODELOS
# =========================================================

modelos = entrenar_modelos(
    df_constantes
)


# =========================================================
# 4. CONFIGURACIONES A COMPARAR
# =========================================================

configuraciones = {

    "BASE / GPS": {
        "RTK_ISOBUS": 0,
        "Siembra_variable": 0,
        "Abono_variable": 0,
        "Corte_tramos": 0
    },

    "RTK + ISOBUS": {
        "RTK_ISOBUS": 1,
        "Siembra_variable": 0,
        "Abono_variable": 0,
        "Corte_tramos": 0
    },

    "PAQUETE COMPLETO": {
        "RTK_ISOBUS": 1,
        "Siembra_variable": 1,
        "Abono_variable": 1,
        "Corte_tramos": 1
    }
}


# =========================================================
# 5. PARÁMETROS ECONÓMICOS DE MAÍZ
# =========================================================

datos_maiz = df_constantes[
    df_constantes["Cultivo"] == "Maiz"
]


parametros_maiz = {

    "Precio_tonelada_venta":
        datos_maiz[
            "Precio_tonelada_venta"
        ].mean(),

    "Precio_litro_gasoleoB":
        datos_maiz[
            "Precio_litro_gasoleoB"
        ].mean(),

    "Precio_litro_Fitosanitario":
        datos_maiz[
            "Precio_litro_Fitosanitario"
        ].mean(),

    "Precio_unitario_semilla":
        datos_maiz[
            "Precio_unitario_semilla"
        ].mean(),

    "Precio_Abono_kg":
        datos_maiz[
            "Precio_Abono_kg"
        ].mean(),

    "Gastos_fijos_por_ha":
        datos_maiz[
            "Gastos_fijos_por_ha"
        ].mean(),

    "Descuento_humedad_por_t":
        datos_maiz[
            "Descuento_humedad_por_t"
        ].mean()
}


# =========================================================
# 6. PREDICCIONES TÉCNICAS EN MAÍZ
# =========================================================

resultados_tecnicos = []


for nombre, configuracion in configuraciones.items():

    configuracion_modelo = (
        expandir_configuracion(
            configuracion
        )
    )

    predicciones = (
        predecir_resultados(
            cultivo="Maiz",
            modelos=modelos,
            **configuracion_modelo
        )
    )

    resultados_tecnicos.append({

        "Configuracion":
            nombre,

        "Rend_t_ha":
            predicciones[
                "Rend_t_ha"
            ],

        "Productividad_ha_h":
            predicciones[
                "Productividad_ha_h"
            ],

        "Consumo_L_ha":
            predicciones[
                "Consumo_L_ha"
            ],

        "Fitosanitarios_ha":
            predicciones[
                "Fitosanitarios_ha"
            ],

        "Semillas_ha":
            predicciones[
                "Semillas_ha"
            ],

        "Abono_ha":
            predicciones[
                "Abono_ha"
            ],

        "Pasadas_ha":
            predicciones[
                "Pasadas_ha"
            ]
    })


tabla_tecnica = (
    pd.DataFrame(
        resultados_tecnicos
    )
    .set_index(
        "Configuracion"
    )
)


print(
    "\n"
    + "=" * 90
)

print(
    "PREDICCIONES TÉCNICAS EN MAÍZ"
)

print(
    "=" * 90
)

print(
    tabla_tecnica.round(2).to_string()
)


# =========================================================
# 7. RESULTADOS ECONÓMICOS EN MAÍZ
# =========================================================

resultados_economicos = []


for nombre, configuracion in configuraciones.items():

    configuracion_modelo = (
        expandir_configuracion(
            configuracion
        )
    )

    predicciones = (
        predecir_resultados(
            cultivo="Maiz",
            modelos=modelos,
            **configuracion_modelo
        )
    )

    economia = (
        calcular_resultado_economico(
            cultivo="Maiz",
            superficie=100,
            predicciones=predicciones,
            parametros=parametros_maiz
        )
    )

    resultados_economicos.append({

        "Configuracion":
            nombre,

        "Ingreso_bruto_ha":
            economia[
                "Ingreso_bruto_ha"
            ],

        "Coste_gasoil_ha":
            economia[
                "Coste_gasoil_ha"
            ],

        "Coste_fitosanitarios_ha":
            economia[
                "Coste_fitosanitarios_ha"
            ],

        "Coste_semillas_ha":
            economia[
                "Coste_semillas_ha"
            ],

        "Coste_abono_ha":
            economia[
                "Coste_abono_ha"
            ],

        "Coste_secado_ha":
            economia[
                "Coste_secado_ha"
            ],

        "Coste_total_ha":
            economia[
                "Coste_total_ha"
            ],

        "Beneficio_por_ha":
            economia[
                "Beneficio_por_ha"
            ]
    })


tabla_economica = (
    pd.DataFrame(
        resultados_economicos
    )
    .set_index(
        "Configuracion"
    )
)


print(
    "\n"
    + "=" * 90
)

print(
    "RESULTADOS ECONÓMICOS POR HECTÁREA EN MAÍZ"
)

print(
    "=" * 90
)

print(
    tabla_economica.round(2).to_string()
)


# =========================================================
# 8. DIFERENCIA BASE VS RTK + ISOBUS
# =========================================================

diferencia_tecnica = (
    tabla_tecnica.loc[
        "RTK + ISOBUS"
    ]
    -
    tabla_tecnica.loc[
        "BASE / GPS"
    ]
)


diferencia_beneficio = (
    tabla_economica.loc[
        "RTK + ISOBUS",
        "Beneficio_por_ha"
    ]
    -
    tabla_economica.loc[
        "BASE / GPS",
        "Beneficio_por_ha"
    ]
)


print(
    "\n"
    + "=" * 90
)

print(
    "CAMBIO AL PASAR DE BASE A RTK + ISOBUS"
)

print(
    "=" * 90
)

print(
    diferencia_tecnica
    .round(2)
    .to_string()
)

print(
    "\nCambio de beneficio por ha:"
)

print(
    f"{diferencia_beneficio:.2f} €/ha"
)


# =========================================================
# 9. SOPORTE HISTÓRICO SIMPLE POR CULTIVO
# =========================================================

print(
    "\n"
    + "=" * 90
)

print(
    "SOPORTE HISTÓRICO POR CULTIVO"
)

print(
    "=" * 90
)


for cultivo_diagnostico in [
    "Maiz",
    "Arroz",
    "Tomates"
]:

    print(
        f"\n--- {cultivo_diagnostico} ---"
    )

    for nombre, configuracion in configuraciones.items():

        expandida = (
            expandir_configuracion(
                configuracion
            )
        )

        filtro = (

            (
                df_constantes["Cultivo"]
                == cultivo_diagnostico
            )

            &

            (
                df_constantes["RTK"]
                == expandida["RTK"]
            )

            &

            (
                df_constantes["ISOBUS"]
                == expandida["ISOBUS"]
            )

            &

            (
                df_constantes[
                    "Siembra_variable"
                ]
                ==
                expandida[
                    "Siembra_variable"
                ]
            )

            &

            (
                df_constantes[
                    "Abono_variable"
                ]
                ==
                expandida[
                    "Abono_variable"
                ]
            )

            &

            (
                df_constantes[
                    "Corte_tramos"
                ]
                ==
                expandida[
                    "Corte_tramos"
                ]
            )
        )

        observaciones = int(
            filtro.sum()
        )

        print(
            f"{nombre}: "
            f"{observaciones} observaciones"
        )


# =========================================================
# 10. DISTRIBUCIÓN REAL DE TODAS LAS CONFIGURACIONES
# =========================================================

print(
    "\n"
    + "=" * 100
)

print(
    "DISTRIBUCIÓN REAL DE CONFIGURACIONES TECNOLÓGICAS"
)

print(
    "=" * 100
)


tecnologias = [
    "RTK",
    "ISOBUS",
    "Siembra_variable",
    "Abono_variable",
    "Corte_tramos"
]


for cultivo_diagnostico in [
    "Maiz",
    "Arroz",
    "Tomates"
]:

    print(
        f"\n{'=' * 80}"
    )

    print(
        cultivo_diagnostico.upper()
    )

    print(
        "=" * 80
    )

    df_cultivo = (
        df_constantes[
            df_constantes["Cultivo"]
            == cultivo_diagnostico
        ]
        .copy()
    )

    configuraciones_reales = (
        df_cultivo[
            tecnologias
        ]
        .value_counts(
            dropna=False
        )
        .reset_index(
            name="Observaciones"
        )
        .sort_values(
            "Observaciones",
            ascending=False
        )
    )

    print(
        configuraciones_reales.to_string(
            index=False
        )
    )


# =========================================================
# 11. FIN
# =========================================================

print(
    "\n"
    + "=" * 100
)

print(
    "DIAGNÓSTICO FINALIZADO"
)

print(
    "=" * 100
)
