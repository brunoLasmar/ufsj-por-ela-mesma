from __future__ import annotations

import json
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

PRIMARY = "#7a1113"
TEXT_STRONG = "#0f172a"
TEXT_MUTED = "#64748b"
SURFACE = "#ffffff"
BORDER = "#dfe6ee"

CARD_STYLE = {
    "border": f"1px solid {BORDER}",
    "borderRadius": "16px",
    "boxShadow": "0 8px 24px rgba(15, 23, 42, 0.06)",
    "backgroundColor": SURFACE,
}

SECTION_TITLE_STYLE = {
    "color": PRIMARY,
    "fontWeight": "700",
    "letterSpacing": "0.01em",
    "marginBottom": "14px",
}

TABLE_STYLE_CELL = {
    "backgroundColor": SURFACE,
    "color": "#1f2937",
    "padding": "12px",
    "textAlign": "left",
    "whiteSpace": "normal",
    "height": "auto",
    "fontSize": "15px",
    "lineHeight": "1.5",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": PRIMARY,
    "color": "white",
    "fontWeight": "bold",
    "textAlign": "center",
    "fontSize": "15px",
    "padding": "12px",
    "border": "none",
}

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "clean"
TOPICS_PATH = DATA_DIR / "info_topicos.json"
TIMELINE_PATH = DATA_DIR / "topicos_tempo.json"
DOCUMENTS_PATH = DATA_DIR / "info_documentos.json"
MODEL_TOPICS_PATH = DATA_DIR / "modelo_topicos_ufsj" / "topics.json"


def _fmt_int(value: int | float) -> str:
    return f"{int(value or 0):,}".replace(",", ".")


def _empty_figure(message: str, title: str, height: int = 460):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.5, xanchor="center"),
        height=height,
        margin=dict(l=30, r=20, t=70, b=40),
        font=dict(family="Arial", size=13, color="#333"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return fig


def _load_json(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_topics_df() -> pd.DataFrame:
    raw = _load_json(TOPICS_PATH)
    df = pd.DataFrame(raw)
    if df.empty:
        return pd.DataFrame(columns=["Topic", "Count", "Name", "Representation", "TopicLabel", "Words"])

    df["Topic"] = df["Topic"].astype(str)
    df["Count"] = pd.to_numeric(df["Count"], errors="coerce").fillna(0).astype(int)
    df["Representation"] = df["Representation"].apply(lambda values: values if isinstance(values, list) else [])
    df["TopicLabel"] = df["Topic"].apply(lambda topic: "Sem cluster" if topic == "-1" else f"Tópico {topic}")
    df["Words"] = df["Representation"].apply(lambda values: ", ".join(str(word) for word in values[:10]))
    return df.sort_values("Count", ascending=False).reset_index(drop=True)


def _load_timeline_df() -> pd.DataFrame:
    raw = _load_json(TIMELINE_PATH)
    df = pd.DataFrame(raw)
    if df.empty:
        return pd.DataFrame(columns=["Topic", "Frequency", "date"])

    df["Topic"] = df["Topic"].astype(str)
    df["Frequency"] = pd.to_numeric(df["Frequency"], errors="coerce").fillna(0).astype(int)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms", errors="coerce")
    df = df.dropna(subset=["Timestamp"]).copy()
    df["date"] = df["Timestamp"].dt.to_period("M").dt.to_timestamp()
    return df.groupby(["date", "Topic"], as_index=False)["Frequency"].sum()


def _load_document_count() -> int:
    raw = _load_json(DOCUMENTS_PATH)
    if isinstance(raw, list):
        return len(raw)
    return 0


def _load_topic_representations() -> dict[str, list[tuple[str, float]]]:
    raw = _load_json(MODEL_TOPICS_PATH)
    if not isinstance(raw, dict):
        return {}

    topic_representations = raw.get("topic_representations", {})
    result: dict[str, list[tuple[str, float]]] = {}
    for topic_id, pairs in topic_representations.items():
        parsed: list[tuple[str, float]] = []
        if isinstance(pairs, list):
            for item in pairs:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    parsed.append((str(item[0]), float(item[1])))
        result[str(topic_id)] = parsed
    return result


def _kpi_card(title: str, value: str, subtitle: str | None = None, color: str = PRIMARY):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    style={
                        "fontSize": "0.88rem",
                        "color": "#64748b",
                        "fontWeight": 700,
                        "letterSpacing": "0.01em",
                        "textAlign": "center",
                        "marginBottom": "10px",
                    },
                ),
                html.Div(
                    value,
                    style={
                        "fontSize": "2.05rem",
                        "fontWeight": 800,
                        "color": color,
                        "lineHeight": "1.1",
                        "textAlign": "center",
                    },
                ),
                html.Div(
                    subtitle or "",
                    style={
                        "fontSize": "0.84rem",
                        "color": "#475569",
                        "fontWeight": 500,
                        "textAlign": "center",
                        "marginTop": "8px",
                    },
                ),
            ],
            style={
                "minHeight": "132px",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
            },
        ),
        style={
            "backgroundColor": "#ffffff",
            "border": f"1px solid {BORDER}",
            "borderRadius": "16px",
            "boxShadow": "0 8px 20px rgba(15, 23, 42, 0.06)",
        },
        className="h-100",
    )


def _build_topics_bar_chart(df: pd.DataFrame, top_n: int = 8):
    if df is None or df.empty:
        return _empty_figure("Sem dados de tópicos para exibir.", "Tópicos mais frequentes")

    filtered = df[df["Topic"] != "-1"].copy().sort_values("Count", ascending=False).head(top_n)
    if filtered.empty:
        return _empty_figure("Sem tópicos válidos para exibir.", "Tópicos mais frequentes")

    fig = px.bar(
        filtered,
        x="TopicLabel",
        y="Count",
        text="Count",
        template="plotly_white",
        color_discrete_sequence=[PRIMARY],
        title="Tópicos mais frequentes",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=500,
        margin=dict(l=30, r=20, t=70, b=90),
        xaxis_title="Tópico",
        yaxis_title="Frequência",
        title=dict(x=0.5, xanchor="center"),
        font=dict(family="Arial", size=13, color="#333"),
    )
    fig.update_xaxes(tickangle=-30, automargin=True)
    return fig


def _build_time_chart(df: pd.DataFrame):
    if df is None or df.empty:
        return _empty_figure("Sem dados temporais para exibir.", "Evolução dos tópicos ao longo do tempo")

    topics_to_plot = (
        df.groupby("Topic", as_index=False)["Frequency"].sum().sort_values("Frequency", ascending=False).head(6)["Topic"].tolist()
    )
    filtered = df[df["Topic"].isin(topics_to_plot)].copy()
    filtered["TopicLabel"] = filtered["Topic"].apply(lambda topic: "Sem cluster" if topic == "-1" else f"Tópico {topic}")

    if filtered.empty:
        return _empty_figure("Sem dados temporais para exibir.", "Evolução dos tópicos ao longo do tempo")

    fig = px.line(
        filtered,
        x="date",
        y="Frequency",
        color="TopicLabel",
        markers=True,
        template="plotly_white",
        title="Evolução dos tópicos ao longo do tempo",
    )
    fig.update_layout(
        height=500,
        margin=dict(l=40, r=20, t=70, b=50),
        xaxis_title="Período",
        yaxis_title="Frequência",
        legend_title_text="Tópico",
        title=dict(x=0.5, xanchor="center"),
    )
    return fig


def _build_topic_words_chart(topic_id: str | None, topic_representations: dict[str, list[tuple[str, float]]]):
    if not topic_id:
        return _empty_figure("Selecione um tópico.", "Palavras mais representativas")

    pairs = topic_representations.get(str(topic_id), [])
    if not pairs:
        return _empty_figure("Sem palavras representativas para o tópico selecionado.", f"Palavras do tópico {topic_id}")

    df = pd.DataFrame(pairs, columns=["word", "score"])
    df = df.sort_values("score", ascending=False).head(10)

    fig = px.bar(
        df,
        x="score",
        y="word",
        orientation="h",
        text="score",
        template="plotly_white",
        color_discrete_sequence=[PRIMARY],
        title=f"Palavras mais representativas — Tópico {topic_id}",
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=max(420, 32 * len(df) + 120),
        margin=dict(l=180, r=40, t=70, b=40),
        xaxis_title="Peso",
        yaxis_title="",
        title=dict(x=0.5, xanchor="center"),
    )
    return fig


TOPICS_DF = _load_topics_df()
TIMELINE_DF = _load_timeline_df()
TOPIC_REPRESENTATIONS = _load_topic_representations()
VALID_TOPICS = TOPICS_DF[TOPICS_DF["Topic"] != "-1"].copy()
DEFAULT_TOPIC = VALID_TOPICS["Topic"].iloc[0] if not VALID_TOPICS.empty else "0"
TOPIC_TABLE_DATA = (
    VALID_TOPICS[["Topic", "Count", "Words"]].rename(columns={"Topic": "topic", "Count": "count", "Words": "words"}).head(12).to_dict("records")
)


layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Voltar",
                                href="/",
                                style={
                                    "backgroundColor": "#ffffff",
                                    "color": "primary",
                                    "border": f"1px solid {BORDER}",
                                    "fontWeight": "700",
                                    "padding": "10px 18px",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(15, 23, 42, 0.06)",
                                },
                                className="mb-0",
                            ),
                            width="auto",
                        )
                    ],
                    className="g-0 align-items-center mb-3",
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H1(
                                "Visão Geral da Modelagem de Tópicos",
                                style={
                                    "color": TEXT_STRONG,
                                    "fontWeight": 800,
                                    "fontSize": "2.2rem",
                                    "marginBottom": "10px",
                                    "lineHeight": "1.2",
                                },
                            ),
                            html.P(
                                "Resumo dos tópicos extraídos do conjunto de dados em data/clean, sem análise de sentimento.",
                                style={
                                    "fontSize": "1rem",
                                    "color": TEXT_MUTED,
                                    "lineHeight": "1.55",
                                    "marginBottom": "0",
                                    "maxWidth": "760px",
                                },
                            ),
                        ]
                    ),
                    style={**CARD_STYLE, "marginBottom": "14px", "padding": "6px 8px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            _kpi_card(
                                "Tópicos modelados",
                                _fmt_int(len(VALID_TOPICS)),
                                subtitle="Tópicos principais (sem outlier)",
                                color="#111827",
                            ),
                            md=4,
                            className="mb-3",
                        ),
                        dbc.Col(
                            _kpi_card(
                                "Documentos analisados",
                                _fmt_int(_load_document_count()),
                                subtitle="Registros em data/clean",
                                color="#111827",
                            ),
                            md=4,
                            className="mb-3",
                        ),
                        dbc.Col(
                            _kpi_card(
                                "Menções totais",
                                _fmt_int(int(TOPICS_DF["Count"].sum())),
                                subtitle="Frequência acumulada dos tópicos",
                                color="#111827",
                            ),
                            md=4,
                            className="mb-3",
                        ),
                    ],
                    className="g-3 mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H4("Tópicos mais frequentes", style=SECTION_TITLE_STYLE),
                                        dcc.Graph(
                                            figure=_build_topics_bar_chart(TOPICS_DF),
                                            config={"displayModeBar": False},
                                            style={"height": "500px"},
                                        ),
                                    ]
                                ),
                                style=CARD_STYLE,
                                className="h-100",
                            ),
                            lg=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H4("Evolução dos tópicos ao longo do tempo", style=SECTION_TITLE_STYLE),
                                        dcc.Graph(
                                            figure=_build_time_chart(TIMELINE_DF),
                                            config={"displayModeBar": False},
                                            style={"height": "500px"},
                                        ),
                                    ]
                                ),
                                style=CARD_STYLE,
                                className="h-100",
                            ),
                            lg=6,
                        ),
                    ],
                    className="g-3 mb-3",
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Exploração por tópico", style=SECTION_TITLE_STYLE),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Selecione um tópico", className="topic-filter-label"),
                                            dcc.Dropdown(
                                                id="topic-selector",
                                                options=[{"label": f"{row['Topic']} — {row['TopicLabel']}", "value": row["Topic"]} for _, row in VALID_TOPICS[["Topic", "TopicLabel"]].iterrows()],
                                                value=DEFAULT_TOPIC,
                                                clearable=False,
                                                style={"fontSize": "14px"},
                                            ),
                                        ],
                                        md=4,
                                    )
                                ],
                                className="mb-3",
                            ),
                            dcc.Graph(
                                id="topic-words-figure",
                                figure=_build_topic_words_chart(DEFAULT_TOPIC, TOPIC_REPRESENTATIONS),
                                config={"displayModeBar": False},
                                style={"height": "420px"},
                            ),
                        ]
                    ),
                    style={**CARD_STYLE, "marginBottom": "14px"},
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Resumo dos principais tópicos", style=SECTION_TITLE_STYLE),
                            html.P(
                                "A tabela mostra os tópicos com maior frequência e suas palavras-chave principais.",
                                style={"color": TEXT_MUTED, "marginBottom": "10px"},
                            ),
                            dash_table.DataTable(
                                columns=[
                                    {"name": "Tópico", "id": "topic"},
                                    {"name": "Frequência", "id": "count"},
                                    {"name": "Palavras-chave", "id": "words"},
                                ],
                                data=TOPIC_TABLE_DATA,
                                style_table={
                                    "overflowX": "auto",
                                    "borderRadius": "12px",
                                    "overflow": "hidden",
                                },
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                                page_size=10,
                            ),
                        ]
                    ),
                    style={**CARD_STYLE, "marginBottom": "8px"},
                ),
            ],
            fluid=True,
            style={
                "padding": "20px 28px 28px 28px",
                "backgroundColor": "#f3f5f8",
            },
        )
    ],
    style={
        "backgroundColor": "#f3f5f8",
        "minHeight": "100vh",
        "margin": "0",
        "padding": "0",
    },
)


@callback(Output("topic-words-figure", "figure"), Input("topic-selector", "value"))
def update_topic_words(selected_topic: str | None):
    if selected_topic is None:
        selected_topic = DEFAULT_TOPIC
    return _build_topic_words_chart(selected_topic, TOPIC_REPRESENTATIONS)
