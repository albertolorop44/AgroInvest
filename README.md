# AgroInvest

## Descripción

**AgroInvest** es una aplicación web interactiva orientada al apoyo a la decisión de inversión en tecnologías de Agricultura 4.0. A partir de datos históricos técnicos, productivos y económicos de explotaciones agrícolas reales, la aplicación permitirá comparar el impacto y la viabilidad de seis tecnologías: **GPS, RTK, ISOBUS, siembra variable, abonado variable y corte automático por tramos**.

El proyecto se centrará en tres cultivos: **maíz, arroz y tomate**. El usuario podrá explorar resultados históricos, simular escenarios y comparar alternativas de inversión mediante indicadores técnicos y financieros. Los datos reales de las explotaciones no se publicarán en el repositorio por motivos de confidencialidad.

## Objetivos

- Integrar y preparar con `pandas` los datos históricos técnicos, productivos, tecnológicos y económicos disponibles.
- Analizar el comportamiento de maíz, arroz y tomate en función del nivel y tipo de digitalización.
- Desarrollar modelos predictivos con `scikit-learn` para estimar variables como rendimiento o beneficio por hectárea.
- Evaluar la viabilidad económica de las inversiones mediante ROI, VAN, TIR y Payback.
- Comparar las seis tecnologías y generar recomendaciones según cultivo, superficie, tecnologías existentes y escenario económico.
- Incorporar análisis de sensibilidad para estudiar cómo cambia la recomendación ante variaciones de precios, costes, superficie, vida útil o tasa de descuento.
- Construir visualizaciones interactivas con `Plotly` y una aplicación web con `Dash`.
- Desplegar la aplicación en una URL accesible públicamente.

## Alcance inicial

### Cultivos
- Maíz
- Arroz
- Tomate

### Tecnologías
- GPS / GNSS
- RTK
- ISOBUS
- Siembra variable
- Abonado variable
- Corte automático por tramos

### Indicadores principales
- Rendimiento y productividad
- Consumo e insumos
- Beneficio por hectárea
- ROI
- VAN
- TIR
- Payback

## Plan de trabajo inicial

- [ ] **Primera quincena de octubre:** revisión, anonimización y consolidación de las bases de datos; definición de variables y análisis exploratorio.
- [ ] **Segunda quincena de octubre:** construcción de baseline y modelos predictivos; validación con MAE, RMSE y R².
- [ ] **Primera quincena de noviembre:** desarrollo del motor económico y de recomendación; análisis de sensibilidad y escenarios.
- [ ] **Segunda quincena de noviembre:** desarrollo del dashboard en Dash/Plotly, integración de callbacks y mejora de la experiencia de usuario.
- [ ] **Finales de noviembre:** pruebas, refactorización, documentación, despliegue en Render y preparación de la presentación.

## Tecnologías previstas

- Python
- pandas / NumPy
- scikit-learn
- Plotly
- Dash
- openpyxl
- numpy-financial
- Git / GitHub
- Render

## Privacidad de los datos

Las bases de datos originales proceden de explotaciones agrícolas reales y contienen información privada. Por ello, los ficheros Excel originales no se publicarán en GitHub. El repositorio contendrá el código, la documentación, la descripción de variables y, si fuera necesario, datos de ejemplo anonimizados o sintéticos para facilitar la reproducibilidad de la aplicación.
