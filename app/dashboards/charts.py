import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = {
    "blue": "#2563eb",
    "cyan": "#06b6d4",
    "night": "#101828",
    "green": "#12b76a",
    "orange": "#f79009",
    "red": "#f04438",
}


def inventory_bar(df: pd.DataFrame):
    """Render detected inventory by object type."""
    if df.empty:
        return go.Figure()
    fig = px.bar(
        df,
        x="object_type",
        y="detected_count",
        text="detected_count",
        title="Inventaire detecte",
        color="detected_count",
        color_continuous_scale=["#dbeafe", PALETTE["blue"]],
    )
    fig.update_layout(height=360, margin=dict(t=55, b=20, l=20, r=20), coloraxis_showscale=False)
    return fig


def anomalies_pie(df: pd.DataFrame):
    """Render anomaly distribution."""
    if df.empty:
        return go.Figure()
    fig = px.pie(df, names="anomaly_type", title="Repartition des anomalies", hole=0.55)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=360, margin=dict(t=55, b=20, l=20, r=20))
    return fig


def score_gauge(score: float):
    """Render the classroom health gauge."""
    color = PALETTE["green"] if score >= 80 else PALETTE["orange"] if score >= 60 else PALETTE["red"]
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Classroom Health Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 60], "color": "#fee4e2"},
                    {"range": [60, 80], "color": "#fef0c7"},
                    {"range": [80, 100], "color": "#dcfae6"},
                ],
            },
        )
    )
    fig.update_layout(height=330, margin=dict(t=42, b=10, l=20, r=20))
    return fig


def history_line(df: pd.DataFrame):
    """Render historical score evolution."""
    if df.empty:
        return go.Figure()
    fig = px.line(df, x="date", y="classroom_health_score", color="room_id", title="Evolution historique du score")
    fig.update_layout(height=330, margin=dict(t=55, b=20, l=20, r=20))
    return fig


def data_quality_bar(df: pd.DataFrame):
    """Render the available quality score columns."""
    if df.empty:
        return go.Figure()
    metrics = [c for c in ["score", "avg_detection_confidence", "inventory_compliance", "equipment_availability", "occupancy_consistency"] if c in df]
    values = []
    for col in metrics:
        value = float(df[col].iloc[0])
        values.append(value * 100 if value <= 1 and col != "score" else value)
    plot_df = pd.DataFrame({"metric": metrics, "score": values})
    fig = px.bar(plot_df, x="metric", y="score", range_y=[0, 100], title="Scores Data Quality", color_discrete_sequence=[PALETTE["green"]])
    fig.update_layout(height=340, margin=dict(t=55, b=20, l=20, r=20))
    return fig
