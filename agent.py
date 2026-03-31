from dotenv import load_dotenv
load_dotenv()

import anthropic
import json
import os
from datetime import datetime
import pandas as pd
from eda_engine import run_eda
from charts import generate_charts
import sys

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_FILE_SIZE_MB = 100

def log(msg):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()

client = anthropic.Anthropic()

SYSTEM_PROMPT = """
You are a senior data scientist writing a professional EDA report for a business audience.

You will receive a JSON summary of a dataset's statistics. Your job is to:
1. Interpret the numbers — don't just repeat them, explain what they MEAN
2. Flag potential data quality issues a junior analyst might miss
3. Identify patterns that would affect machine learning model choices
4. Write actionable recommendations, not generic advice

Structure your report with exactly these sections:
## 1. Dataset Overview
## 2. Data Quality Assessment
## 3. Key Statistical Insights
## 4. Correlation Analysis
## 5. Categorical Variable Analysis
## 6. ML Readiness Assessment
## 7. Recommended Next Steps

Rules:
- Reference actual column names and specific numbers from the data
- Use markdown tables where comparisons are clearer in tabular form
- Flag any column with >5% missing values as HIGH PRIORITY
- Flag any correlation above 0.7 as potentially multicollinear
- Be specific — "column X has 23% missing values which will require imputation"
  not "some columns have missing values"
- Keep the tone professional but accessible
"""


def validate_csv_path(csv_path: str, allowed_dir: str = None) -> str:
    """
    Validates that a file path is safe to read:
    - Must exist and be a file
    - Must be within the allowed directory (defaults to project root/data)
    - Must be under the file size limit
    - Must be a .csv file
    """
    if allowed_dir is None:
        allowed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    real_path = os.path.realpath(os.path.abspath(csv_path))
    real_allowed = os.path.realpath(os.path.abspath(allowed_dir))

    if not real_path.startswith(real_allowed + os.sep) and real_path != real_allowed:
        raise ValueError(f"Access denied: file must be inside '{allowed_dir}'")

    if not os.path.isfile(real_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    if not real_path.lower().endswith(".csv"):
        raise ValueError(f"Only .csv files are supported")

    size_mb = os.path.getsize(real_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f} MB (limit: {MAX_FILE_SIZE_MB} MB)")

    return real_path


def generate_report(eda_stats: dict, chart_paths: list, filename: str) -> str:
    chart_refs = ""
    if chart_paths:
        chart_refs = "\n\nThe following charts have been generated and saved:\n"
        for path in chart_paths:
            chart_refs += f"- {os.path.basename(path)}\n"
        chart_refs += "\nEmbed these charts at the appropriate sections using markdown: ![Chart Title](path)"

    user_message = f"""
Please generate a full EDA report for the dataset: '{os.path.basename(filename)}'

Here are the computed statistics:
{json.dumps(eda_stats, indent=2)}
{chart_refs}

Generate the complete report now.
"""

    log("Sending stats to Claude...")
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
    except anthropic.APIConnectionError as e:
        raise RuntimeError(f"Could not connect to Claude API: {e}") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Claude API error {e.status_code}: {e.message}") from e

    if not response.content or not hasattr(response.content[0], "text"):
        raise RuntimeError("Claude returned an empty or unexpected response")

    return response.content[0].text


def save_report(report: str, filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"eda_report_{timestamp}.md"

    header = f"""# EDA Report: {os.path.basename(filename)}
*Generated automatically by EDA Agent on {datetime.now().strftime('%B %d, %Y at %H:%M')}*

---

"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + report)

    log(f"Report saved: {output_path}")
    return output_path


def run_full_pipeline(csv_path: str):
    log(f"\nLoading dataset: {csv_path}")
    validated_path = validate_csv_path(csv_path)

    try:
        df = pd.read_csv(validated_path)
    except pd.errors.ParserError as e:
        raise ValueError(f"Failed to parse CSV file: {e}") from e
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")

    if df.empty:
        raise ValueError("The CSV file contains no data rows")

    log("Running EDA engine...")
    eda_stats = run_eda(df)
    log(f"   -> {eda_stats['shape']['rows']} rows, {eda_stats['shape']['columns']} columns")

    log("Generating charts...")
    chart_paths = generate_charts(df)

    log("Generating AI report...")
    report = generate_report(eda_stats, chart_paths, csv_path)

    log("Saving report...")
    output_path = save_report(report, csv_path)

    return output_path


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/Car_Purchasing_Data.csv"
    run_full_pipeline(csv_path)
