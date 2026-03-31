import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def log(msg: str):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()

THEME = "plotly_dark"
COLORS = px.colors.qualitative.Vivid


def generate_charts(source, output_dir: str = "charts") -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(source) if isinstance(source, str) else source

    # Skip near-unique columns like IDs
    numeric_cols = [
        c for c in df.select_dtypes(include=np.number).columns
        if df[c].nunique() > 1
    ]
    categorical_cols = [
        c for c in df.select_dtypes(include="object").columns
        if df[c].nunique() < df.shape[0] * 0.5
    ]
    saved_charts = []

    # --- CHART 1: MISSING VALUES ---
    if df.isnull().sum().sum() > 0:
        missing = df.isnull().mean() * 100
        missing = missing[missing > 0].sort_values(ascending=False)
        fig = px.bar(
            x=missing.index,
            y=missing.values,
            labels={"x": "Column", "y": "Missing (%)"},
            title="Missing Values by Column (%)",
            color=missing.values,
            color_continuous_scale="Reds",
            template=THEME
        )
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Missing: %{y:.1f}%<extra></extra>")
        fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
        path = f"{output_dir}/missing_values.html"
        fig.write_html(path)
        saved_charts.append(path)
        log(f"  ✅ Saved: {path}")

    # --- CHART 2: NUMERIC DISTRIBUTIONS (one per column) ---
    for col in numeric_cols[:9]:
        fig = px.histogram(
            df, x=col, nbins=30,
            title=f"Distribution: {col}",
            template=THEME,
            color_discrete_sequence=["#7C6FE0"]
        )
        fig.update_traces(
            hovertemplate=f"<b>{col}</b><br>Value: %{{x}}<br>Count: %{{y}}<extra></extra>"
        )
        fig.update_layout(height=350, bargap=0.05)
        path = f"{output_dir}/dist_{col.replace(' ', '_')}.html"
        fig.write_html(path)
        saved_charts.append(path)
        log(f"  ✅ Saved: {path}")

    # --- CHART 3: CORRELATION HEATMAP ---
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr().round(2)
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.columns.tolist(),
            colorscale="RdBu_r",
            zmid=0,
            text=corr_matrix.values,
            texttemplate="%{text}",
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"
        ))
        fig.update_layout(
            title="Correlation Heatmap",
            template=THEME,
            height=600,
            xaxis=dict(tickangle=-45)
        )
        path = f"{output_dir}/correlation_heatmap.html"
        fig.write_html(path)
        saved_charts.append(path)
        log(f"  ✅ Saved: {path}")

    # --- CHART 4: CATEGORICAL VALUE COUNTS ---
    for col in categorical_cols[:3]:
        counts = df[col].value_counts().head(10)
        fig = px.bar(
            x=counts.index,
            y=counts.values,
            labels={"x": col, "y": "Count"},
            title=f"Value Counts: {col}",
            template=THEME,
            color=counts.index,
            color_discrete_sequence=COLORS
        )
        fig.update_traces(hovertemplate=f"<b>%{{x}}</b><br>Count: %{{y:,}}<extra></extra>")
        fig.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
        path = f"{output_dir}/categorical_{col.replace(' ', '_')}.html"
        fig.write_html(path)
        saved_charts.append(path)
        log(f"  ✅ Saved: {path}")

    log(f"\n📊 {len(saved_charts)} charts generated in '{output_dir}/'")
    return saved_charts