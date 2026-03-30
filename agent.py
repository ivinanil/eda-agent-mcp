from dotenv import load_dotenv
load_dotenv()

import anthropic
import json
from datetime import datetime
from eda_engine import run_eda
from charts import generate_charts
import sys

def log(msg):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()

client = anthropic.Anthropic()

# --- THE SYSTEM PROMPT ---
# This is the most important part of Person 2's work.
# It tells Claude exactly what role to play, what sections to produce,
# and how to format the output. Good prompt = good report.
# Think of this like writing a job description for Claude.

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


def generate_report(eda_stats: dict, chart_paths: list, filename: str) -> str:
    """
    Sends EDA stats to Claude and gets back a full markdown report.
    We include chart_paths in the message so Claude knows which
    charts exist and can reference them with proper markdown image tags.
    """

    # Build the chart references section
    # This tells Claude "these charts exist, embed them in the right sections"
    chart_refs = ""
    if chart_paths:
        chart_refs = "\n\nThe following charts have been generated and saved:\n"
        for path in chart_paths:
            chart_refs += f"- {path}\n"
        chart_refs += "\nEmbed these charts at the appropriate sections using markdown: ![Chart Title](path)"

    user_message = f"""
Please generate a full EDA report for the dataset: '{filename}'

Here are the computed statistics:
{json.dumps(eda_stats, indent=2)}
{chart_refs}

Generate the complete report now.
"""

    log("🤖 Sending stats to Claude...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    return response.content[0].text


def save_report(report: str, filename: str) -> str:
    """
    Saves the report as a markdown file with a timestamp.
    The timestamp ensures you don't overwrite previous runs —
    useful when testing on multiple datasets.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"eda_report_{timestamp}.md"

    header = f"""# EDA Report: {filename}
*Generated automatically by EDA Agent on {datetime.now().strftime('%B %d, %Y at %H:%M')}*

---

"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + report)

    log(f"✅ Report saved: {output_path}")
    return output_path


def run_full_pipeline(csv_path: str):
    """
    Orchestrates the full pipeline:
    Step 1 → Run EDA (Person 1's code)
    Step 2 → Generate charts (Person 1's code)
    Step 3 → Send to Claude, get report (Person 2's code)
    Step 4 → Save report to file (Person 2's code)

    This function is what Person 3's MCP server will call.
    """
    log(f"\n📂 Loading dataset: {csv_path}")

    log("📊 Running EDA engine...")
    eda_stats = run_eda(csv_path)
    log(f"   → {eda_stats['shape']['rows']} rows, {eda_stats['shape']['columns']} columns")

    log("🎨 Generating charts...")
    chart_paths = generate_charts(csv_path)

    log("🤖 Generating AI report...")
    report = generate_report(eda_stats, chart_paths, csv_path)

    log("💾 Saving report...")
    output_path = save_report(report, csv_path)

    return output_path


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "Car_Purchasing_Data.csv"
    run_full_pipeline(csv_path)