"""Punto de entrada de AgroInvest.

El dashboard se desarrollará durante la asignatura. Este archivo deja preparada
la estructura inicial del proyecto sin incluir datos privados.
"""

from dash import Dash, html

app = Dash(__name__)
server = app.server

app.layout = html.Div(
    [
        html.H1("AgroInvest"),
        html.P(
            "Herramienta interactiva para analizar la viabilidad económica "
            "de tecnologías de Agricultura 4.0."
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
