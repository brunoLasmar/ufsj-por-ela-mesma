from dash import Dash, html
import dash_bootstrap_components as dbc

from pages.visao_geral import layout as visao_geral_layout

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "Modelagem de Tópicos UFSJ"
server = app.server

app.layout = html.Div(
    [
        visao_geral_layout,
    ],
    style={"margin": 0, "padding": 0, "backgroundColor": "#f3f5f8"},
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
