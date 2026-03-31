# EDA Agent — Automated Data Analysis powered by Claude AI + MCP

An intelligent data analysis agent that takes any CSV dataset and automatically generates a professional Exploratory Data Analysis (EDA) report, complete with visualizations and AI-written insights — in seconds.

Built with the **Model Context Protocol (MCP)**, **Claude AI**, and **Python**, and deployable as a web app via **Streamlit**.

---

## Demo

```bash
python mcp_client.py --file data/Car_Prices_Poland.csv
```

```
MCP server connected
Tools available: ['run_full_eda_pipeline', 'get_quick_stats', 'generate_charts_only']
--- Agent turn 1 --- Claude calling: get_quick_stats
--- Agent turn 2 --- Claude calling: run_full_eda_pipeline
--- Agent turn 3 --- Analysis complete!
Report saved: eda_report_20260330_155519.md
```

Or launch the web app:

```bash
streamlit run app.py
```

---

## What it does

Upload any CSV file and the agent autonomously:

1. Loads and profiles the dataset using pandas
2. Computes statistics — distributions, correlations, missing values, outliers
3. Generates interactive visualizations (heatmaps, histograms, bar charts)
4. Sends everything to Claude AI which writes a structured, insight-driven report
5. Saves the full report as a markdown file ready to share

No manual EDA. No copy-pasting numbers into a report. Just one command.

---

## Why MCP?

Most AI tools receive data passively. With **Model Context Protocol (MCP)**, Claude actively decides which tools to call and in what order — making it a true autonomous agent rather than a simple chatbot.

```
User request
     ↓
Claude (MCP client) ──calls──▶ MCP Server
                                   ├── run_full_eda_pipeline
                                   ├── get_quick_stats
                                   └── generate_charts_only
                                          ↓
                               Results returned to Claude
                                          ↓
                               Claude writes final report
```

Claude orchestrates the entire workflow on its own — deciding when to get quick stats first, when to run the full pipeline, and when the job is done.

---

## Tech stack

| Layer | Technology |
|---|---|
| AI model | Claude claude-sonnet-4-6 (Anthropic) |
| Agent protocol | Model Context Protocol (MCP) |
| Data analysis | pandas, numpy |
| Visualizations | plotly |
| Web interface | Streamlit |
| Language | Python 3.10+ |

---

## Project structure

```
eda-agent-mcp/
├── eda_engine.py       # Pandas EDA logic — stats, correlations, missing values
├── charts.py           # Auto-generates interactive Plotly visualizations
├── agent.py            # Claude API integration + report generation
├── mcp_server.py       # MCP server exposing EDA tools to Claude
├── mcp_client.py       # Agentic loop — Claude calls tools autonomously
├── app.py              # Streamlit web interface
├── data/               # Place your CSV datasets here
├── setup.sh            # First-time setup (Mac/Linux)
├── setup.bat           # First-time setup (Windows)
├── run.sh              # Launch the web app (Mac/Linux)
├── run.bat             # Launch the web app (Windows)
├── requirements.txt
└── README.md
```

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/ivinanil/eda-agent-mcp.git
cd eda-agent-mcp
```

### 2. Run setup

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```
setup.bat
```

This will:
- Create a `.venv` virtual environment
- Install all dependencies
- Create a `.env` placeholder file
- Create the `data/` folder

> Safe to run more than once — skips steps already done.

### 3. Add your API key

Open `.env` and replace the placeholder with your real key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your key from [console.anthropic.com](https://console.anthropic.com).

### 4. Add your dataset

Place any CSV file inside the `data/` folder.

> Files must be inside `data/` and under 100 MB.

---

## Running the project

### Option A — One-click launch (recommended)

**Mac/Linux:** `./run.sh`

**Windows:** `run.bat`

Opens at `http://localhost:8501`. Upload a CSV, click Analyze, watch the report generate live.

### Option B — MCP agent (command line)

```bash
python mcp_client.py --file data/your_file.csv
```

Claude autonomously calls tools and generates the full report.

### Option C — Direct pipeline (fastest)

```bash
python -c "from agent import run_full_pipeline; run_full_pipeline('data/your_file.csv')"
```

---

## Example output

Running on `Car_Prices_Poland.csv` (117,927 rows):

**Charts generated:**
- `charts/missing_values.html` — missing data by column
- `charts/dist_*.html` — numeric column distributions
- `charts/correlation_heatmap.html` — feature correlation matrix
- `charts/categorical_*.html` — top value counts per categorical column

**Report sections:**
1. Dataset overview
2. Data quality assessment
3. Key statistical insights
4. Correlation analysis
5. Categorical variable analysis
6. ML readiness assessment
7. Recommended next steps

---

## MCP tools exposed

| Tool | Description |
|---|---|
| `run_full_eda_pipeline` | Runs the complete pipeline — stats, charts, AI report, saved to file |
| `get_quick_stats` | Returns a fast statistical summary of any CSV |
| `generate_charts_only` | Generates and saves visualizations without a written report |

---

## Requirements

```
anthropic
mcp
pandas
numpy
matplotlib
seaborn
plotly
streamlit
python-dotenv
```

---

## License

MIT License — free to use, modify, and distribute.
