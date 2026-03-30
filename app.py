import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="EDA Agent",
    page_icon="📊",
    layout="wide"
)

# Header
st.markdown("""
    <div style='background: #534AB7; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px;'>
        <h1 style='color: #EEEDFE; margin: 0; font-size: 24px;'>📊 EDA Agent</h1>
        <p style='color: #AFA9EC; margin: 4px 0 0;'>Automated exploratory data analysis powered by Claude AI + MCP</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("", ["Upload & Analyze", "View Report", "View Charts"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### About")
    st.caption("This agent uses Claude AI via MCP to automatically analyze any CSV dataset and generate a professional EDA report.")

# ── PAGE 1: Upload & Analyze ──────────────────────────────
if page == "Upload & Analyze":
    uploaded_file = st.file_uploader(
        "Upload your CSV dataset",
        type=["csv"],
        help="Upload any CSV file to get an automated EDA report"
    )

    if uploaded_file:
        # Save uploaded file to data/ folder
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{uploaded_file.name}"
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Show preview
        df = pd.read_csv(filepath)
        st.markdown("### Dataset Preview")

        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{df.shape[0]:,}")
        col2.metric("Columns", df.shape[1])
        missing_pct = round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 1)
        col3.metric("Missing values", f"{missing_pct}%")
        col4.metric("Duplicate rows", df.duplicated().sum())

        st.dataframe(df.head(10), use_container_width=True)

        st.markdown("---")

        # Run analysis button
        if st.button("Run Full EDA Analysis", type="primary", use_container_width=True):
            with st.status("Running EDA Agent...", expanded=True) as status:

                st.write("Loading dataset and computing statistics...")
                from eda_engine import run_eda
                eda_stats = run_eda(filepath)
                st.write(f"✅ EDA complete — {eda_stats['shape']['rows']:,} rows analyzed")

                st.write("Generating charts...")
                from charts import generate_charts
                chart_paths = generate_charts(filepath)
                st.write(f"✅ {len(chart_paths)} charts generated")

                st.write("Sending to Claude AI for report generation...")
                from agent import generate_report, save_report
                report = generate_report(eda_stats, chart_paths, uploaded_file.name)
                output_path = save_report(report, uploaded_file.name)
                st.write("✅ AI report generated and saved")

                status.update(label="Analysis complete!", state="complete")

            # Store in session state so other pages can access it
            st.session_state["report"] = report
            st.session_state["chart_paths"] = chart_paths
            st.session_state["output_path"] = output_path
            st.session_state["filename"] = uploaded_file.name

            st.success(f"Report saved as: `{output_path}`")
            st.balloons()

    else:
        st.info("Upload a CSV file above to get started.")

# ── PAGE 2: View Report ───────────────────────────────────
elif page == "View Report":
    if "report" not in st.session_state:
        # Try to load the most recent report from disk
        report_files = sorted(
            [f for f in os.listdir(".") if f.startswith("eda_report_") and f.endswith(".md")],
            reverse=True
        )
        if report_files:
            with open(report_files[0], "r", encoding="utf-8") as f:
                st.session_state["report"] = f.read()
                st.session_state["output_path"] = report_files[0]
        else:
            st.warning("No report found. Please run an analysis first.")
            st.stop()

    st.markdown("### AI-Generated EDA Report")

    # Download button
    st.download_button(
        label="Download Report (.md)",
        data=st.session_state["report"],
        file_name=st.session_state.get("output_path", "eda_report.md"),
        mime="text/markdown",
        use_container_width=True
    )

    st.markdown("---")
    st.markdown(st.session_state["report"])

# ── PAGE 3: View Charts ───────────────────────────────────
elif page == "View Charts":
    charts_dir = "charts"

    if not os.path.exists(charts_dir):
        st.warning("No charts found. Please run an analysis first.")
        st.stop()

    chart_files = [
        os.path.join(charts_dir, f)
        for f in os.listdir(charts_dir)
        if f.endswith(".png")
    ]

    if not chart_files:
        st.warning("No charts found. Please run an analysis first.")
        st.stop()

    st.markdown(f"### Generated Charts ({len(chart_files)} total)")

    # Display charts in a 2-column grid
    cols = st.columns(2)
    for i, chart_path in enumerate(sorted(chart_files)):
        chart_name = os.path.basename(chart_path).replace("_", " ").replace(".png", "").title()
        with cols[i % 2]:
            st.markdown(f"**{chart_name}**")
            st.image(chart_path, use_container_width=True)