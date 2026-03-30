import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Use a clean style that looks professional in reports
plt.style.use("seaborn-v0_8-whitegrid")
COLORS = sns.color_palette("husl", 10)


def generate_charts(filepath: str, output_dir: str = "charts") -> list[str]:
    """
    Generates a set of EDA charts for a CSV file.
    Saves them as PNG files and returns the list of file paths.
    These paths get embedded in the final markdown report.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(filepath)
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    saved_charts = []

    # --- CHART 1: MISSING VALUES HEATMAP ---
    # Shows at a glance which columns have nulls and how many.
    # A fully colored column = no missing data. Gaps = missing.
    if df.isnull().sum().sum() > 0:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(
            df.isnull(),
            cbar=False,
            yticklabels=False,
            cmap="YlOrRd",
            ax=ax
        )
        ax.set_title("Missing Values Heatmap", fontsize=14, pad=12)
        ax.set_xlabel("Columns")
        path = f"{output_dir}/missing_values.png"
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        saved_charts.append(path)
        print(f"  ✅ Saved: {path}")

    # --- CHART 2: NUMERIC DISTRIBUTIONS ---
    # Histograms for every numeric column, shown in a grid.
    # This reveals: is the data normal? Skewed? Bimodal?
    # Knowing the distribution shape is critical before applying ML models.
    if numeric_cols:
        n = len(numeric_cols)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
        axes = np.array(axes).flatten() if n > 1 else [axes]

        for i, col in enumerate(numeric_cols):
            axes[i].hist(
                df[col].dropna(),
                bins=30,
                color=COLORS[i % len(COLORS)],
                edgecolor="white",
                alpha=0.85
            )
            axes[i].set_title(col, fontsize=12)
            axes[i].set_xlabel("Value")
            axes[i].set_ylabel("Frequency")

        # Hide any unused subplots
        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)

        fig.suptitle("Numeric Column Distributions", fontsize=15, y=1.01)
        plt.tight_layout()
        path = f"{output_dir}/distributions.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        saved_charts.append(path)
        print(f"  ✅ Saved: {path}")

    # --- CHART 3: CORRELATION HEATMAP ---
    # The most important chart for ML feature selection.
    # Dark red = strong positive correlation (move together)
    # Dark blue = strong negative correlation (move opposite)
    # Near zero = no relationship
    if len(numeric_cols) > 1:
        fig, ax = plt.subplots(figsize=(8, 6))
        corr_matrix = df[numeric_cols].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # upper triangle mask
        sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            square=True,
            linewidths=0.5,
            ax=ax
        )
        ax.set_title("Correlation Heatmap", fontsize=14, pad=12)
        plt.tight_layout()
        path = f"{output_dir}/correlation_heatmap.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved_charts.append(path)
        print(f"  ✅ Saved: {path}")

    # --- CHART 4: TOP CATEGORICAL VALUE COUNTS ---
    # Bar charts for categorical columns — shows class imbalance.
    # If one category dominates (e.g. 90% "Male"), that affects model fairness.
    for col in categorical_cols[:3]:  # limit to first 3 to avoid too many charts
        fig, ax = plt.subplots(figsize=(8, 4))
        counts = df[col].value_counts().head(10)
        counts.plot(kind="bar", ax=ax, color=COLORS, edgecolor="white")
        ax.set_title(f"Value Counts: {col}", fontsize=13)
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        ax.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        path = f"{output_dir}/categorical_{col.replace(' ', '_')}.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved_charts.append(path)
        print(f"  ✅ Saved: {path}")

    print(f"\n📊 {len(saved_charts)} charts generated in '{output_dir}/'")
    return saved_charts