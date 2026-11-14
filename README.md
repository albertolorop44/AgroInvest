# AgroInvest

**Aplicación interactiva para el análisis y recomendación de inversiones en tecnologías de Agricultura 4.0**

AgroInvest es una aplicación web desarrollada con Python, Dash y Plotly para apoyar la toma de decisiones de inversión en tecnologías de agricultura de precisión. A partir de datos técnicos, productivos y económicos de explotaciones agrícolas reales, la herramienta compara distintas alternativas tecnológicas y estima su impacto económico y técnico para diferentes tipos de explotación.

## Aplicación desplegada

La aplicación puede utilizarse directamente desde Render:

https://agroinvest-gv3w.onrender.com

> La instancia gratuita de Render puede entrar en reposo tras un periodo de inactividad. La primera carga o algunos cálculos pueden tardar varios segundos.

## Cultivos analizados

AgroInvest trabaja actualmente con tres cultivos:

- Maíz
- Arroz
- Tomate

La aplicación permite analizar un único cultivo o una explotación multicultivo indicando la superficie dedicada a cada uno.

## Tecnologías evaluadas

La aplicación considera GPS/GNSS como tecnología base de la explotación y evalúa inversiones adicionales en:

- RTK + ISOBUS
- Siembra variable
- Abono variable
- Corte automático por tramos

Las tecnologías avanzadas requieren disponer de RTK + ISOBUS. Cuando una tecnología ya está instalada, su coste no vuelve a incluirse en la inversión incremental.

## Funcionalidades principales

AgroInvest permite:

- Configurar explotaciones de un cultivo o multicultivo.
- Introducir la superficie de la explotación.
- Indicar las tecnologías ya instaladas.
- Analizar escenarios de precios constantes.
- Analizar escenarios económicos históricos.
- Introducir parámetros económicos personalizados en monocultivo.
- Generar previsiones futuras con escenarios conservador, central y alcista.
- Definir un presupuesto máximo disponible.
- Modificar la vida útil de la inversión y la tasa de descuento.
- Comparar alternativas mediante VAN, ROI, TIR y Payback.
- Calcular la superficie mínima rentable para alcanzar VAN ≥ 0.
- Generar un ranking de alternativas de inversión.
- Analizar cómo evoluciona el VAN al cambiar la superficie de la explotación.
- Mostrar el beneficio incremental anual de cada alternativa.
- Comparar el impacto técnico estimado de la situación actual frente a la recomendada.
- Generar un resumen final de decisión.
- Mostrar avisos cuando una recomendación se basa en una extrapolación con menor soporte histórico.

## Modelado

Los modelos predictivos se entrenan con `scikit-learn` sobre los datos preparados de la explotación.

Se estiman variables técnicas como:

- Rendimiento (`t/ha`)
- Productividad (`ha/h`)
- Consumo de combustible (`L/ha`)
- Fitosanitarios (`L/ha`)
- Semillas (`unidades/ha`)
- Abono (`kg/ha`)
- Pasadas (`pasadas/ha`)

Para el rendimiento se utilizan variables tecnológicas, cultivo e interacciones cultivo × tecnología. El resto de indicadores se estiman mediante modelos Ridge con preprocesado de variables categóricas y numéricas.

Las predicciones se utilizan posteriormente en el módulo económico para estimar ingresos, costes, beneficio incremental y métricas financieras.

## Evaluación económica

Para cada alternativa tecnológica se calcula la inversión incremental necesaria y el beneficio anual estimado respecto a la situación actual.

Los principales indicadores utilizados son:

- **VAN (Valor Actual Neto):** valor actualizado de los beneficios futuros menos la inversión inicial.
- **ROI:** relación entre el beneficio incremental anual y la inversión.
- **Payback:** años necesarios para recuperar la inversión.
- **TIR:** tasa interna de retorno.
- **Superficie mínima rentable:** superficie necesaria para que el VAN alcance al menos 0 bajo los supuestos seleccionados.

En explotaciones multicultivo, la inversión tecnológica se realiza una única vez y los beneficios incrementales de los cultivos se agregan.

## Escenarios económicos

La aplicación permite trabajar con cuatro tipos de escenario:

### Precios constantes

Utiliza valores medios de los datos preparados como escenario base.

### Precios históricos

Permite seleccionar un año disponible y utilizar los parámetros económicos correspondientes.

### Personalizado

En monocultivo, el usuario puede introducir manualmente precios y costes.

### Previsión futura

Los parámetros económicos futuros se proyectan utilizando tendencias históricas. Según la estabilidad temporal de cada variable, se emplea una tendencia lineal, una tendencia suavizada o la media de los últimos años.

A partir del escenario central se generan:

- **Conservador:** menor precio de venta y mayores costes.
- **Central:** proyección base.
- **Alcista:** mayor precio de venta y menores costes.

Estas previsiones deben interpretarse como escenarios orientativos y no como predicciones garantizadas.

## Consideraciones metodológicas

Los resultados de AgroInvest son estimaciones construidas a partir de datos observacionales. La aplicación está diseñada como herramienta de apoyo a la decisión y no permite interpretar las diferencias estimadas como efectos causales garantizados.

Existen además dos consideraciones específicas:

- **RTK + ISOBUS aislado:** al no existir observaciones históricas directas suficientes de esta configuración por sí sola, se utiliza un tratamiento conservador. Se mantienen sin mejora el rendimiento, los fitosanitarios, las semillas y el abono, mientras que se conservan las mejoras estimadas en productividad, consumo de combustible y pasadas.
- **Siembra variable en tomate:** no existen observaciones históricas directas de esta tecnología en tomate dentro de la base utilizada. Cuando una recomendación incluye esta combinación, la aplicación muestra un aviso indicando que la estimación procede de una extrapolación del modelo y presenta mayor incertidumbre.

## Datos

Los datos necesarios para ejecutar la aplicación se encuentran en la carpeta `data/`:

```text
data/
├── precios_constantes.xlsx
├── precios_historicos.xlsx
└── inversiones_tecnologia.xlsx
```

Estos ficheros son los utilizados directamente por AgroInvest para cargar los parámetros, entrenar los modelos y calcular las inversiones.

Los datos originales de trabajo y otras fuentes privadas utilizadas durante el desarrollo no forman parte del repositorio.

## Estructura del proyecto

```text
AgroInvest/
├── app.py
├── requirements.txt
├── render.yaml
├── README.md
├── diagnostico_rtk.py
│
├── assets/
│   ├── style.css
│   ├── cultivo_maiz.png
│   ├── cultivo_arroz.png
│   ├── cultivo_tomate.png
│   ├── tecnologia_rtk.png
│   ├── tecnologia_siembra.png
│   ├── tecnologia_abono.png
│   └── tecnologia_corte.png
│
├── data/
│   ├── precios_constantes.xlsx
│   ├── precios_historicos.xlsx
│   └── inversiones_tecnologia.xlsx
│
├── notebooks/
│   ├── 01_exploracion_datos.ipynb
│   ├── 02_analisis_economico.ipynb
│   ├── 03_modelado.ipynb
│   └── 04_prevision_precios.ipynb
│
└── src/
    ├── etl.py
    ├── model.py
    ├── finance.py
    ├── forecast.py
    └── graphics.py
```

### Módulos principales

- `app.py`: interfaz Dash, callbacks y coordinación general de la aplicación.
- `src/etl.py`: carga, limpieza y preparación de datos.
- `src/model.py`: entrenamiento y predicción de los modelos técnicos.
- `src/finance.py`: evaluación económica, generación de alternativas y métricas financieras.
- `src/forecast.py`: proyección de parámetros económicos y generación de escenarios futuros.
- `src/graphics.py`: visualizaciones Plotly.
- `assets/style.css`: diseño visual de la aplicación.
- `notebooks/`: análisis exploratorio, económico, modelado y previsión de precios.

## Instalación y ejecución local

Clonar el repositorio:

```bash
git clone https://github.com/albertolorop44/AgroInvest.git
cd AgroInvest
```

Crear un entorno virtual es recomendable, aunque no obligatorio:

```bash
python -m venv .venv
```

Activarlo en Linux/macOS:

```bash
source .venv/bin/activate
```

Activarlo en Windows:

```bash
.venv\Scripts\activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:

```bash
python app.py
```

Dash mostrará la dirección local desde la que puede abrirse AgroInvest en el navegador.

## Dependencias principales

- pandas
- NumPy
- scikit-learn
- Plotly
- Dash
- openpyxl
- numpy-financial
- Gunicorn

La lista completa se encuentra en `requirements.txt`.

## Despliegue

La aplicación está desplegada en Render utilizando Gunicorn.

La configuración se encuentra en `render.yaml`:

```yaml
services:
  - type: web
    name: agroinvest
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:server
    healthCheckPath: /
```

Cada actualización enviada a la rama principal puede generar un nuevo despliegue automático en Render.

## Tecnologías utilizadas

- Python
- pandas
- NumPy
- scikit-learn
- Plotly
- Dash
- openpyxl
- numpy-financial
- Gunicorn
- Git y GitHub
- Render
- HTML/CSS a través de componentes Dash

## Estado del proyecto

AgroInvest se encuentra en una versión funcional y desplegada. La aplicación integra la preparación de datos, modelado predictivo, evaluación financiera, escenarios económicos, visualización interactiva y generación de recomendaciones en una única herramienta web.

## Autor

Proyecto desarrollado por **Alberto Loro** en el contexto de la asignatura **Desarrollo de Aplicaciones para la Visualización de Datos**.
