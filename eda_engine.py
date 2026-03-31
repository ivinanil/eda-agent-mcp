import pandas as pd
import numpy as np


def convert_types(obj):
    """
    Recursively converts numpy int64, float64 etc. to native Python types.
    JSON only understands Python's built-in int, float, str, list, dict —
    not numpy's versions of them, even though they look the same.
    """
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj


def run_eda(source) -> dict:
    if isinstance(source, str):
        try:
            df = pd.read_csv(source)
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV: {e}") from e
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty")
    elif isinstance(source, pd.DataFrame):
        df = source
    else:
        raise TypeError(f"Expected a file path or DataFrame, got {type(source)}")

    if df.empty:
        raise ValueError("Dataset contains no rows")

    # --- 1. SHAPE INFO ---
    shape_info = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict()
    }

    # --- 2. MISSING VALUES ---
    missing = df.isnull().sum()
    missing_info = {
        col: {
            "count": int(missing[col]),
            "percentage": round(missing[col] / len(df) * 100, 2)
        }
        for col in df.columns if missing[col] > 0
    }

    # --- 3. NUMERIC COLUMN STATISTICS ---
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    numeric_stats = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        mean = series.mean()
        std = series.std()
        outliers = int(((series - mean).abs() > 3 * std).sum()) if std > 0 else 0

        numeric_stats[col] = {
            "mean": round(mean, 4),
            "median": round(series.median(), 4),
            "std": round(std, 4),
            "min": round(series.min(), 4),
            "max": round(series.max(), 4),
            "skewness": round(series.skew(), 4),
            "kurtosis": round(series.kurt(), 4),
            "outlier_count": outliers
        }

    # --- 4. CATEGORICAL COLUMN STATISTICS ---
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    categorical_stats = {}

    for col in categorical_cols:
        value_counts = df[col].value_counts()
        categorical_stats[col] = {
            "unique_count": int(df[col].nunique()),
            "top_5_values": value_counts.head(5).to_dict(),
            "high_cardinality": df[col].nunique() > 50
        }

    # --- 5. CORRELATIONS ---
    correlations = []
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                val = corr_matrix.iloc[i, j]
                if pd.notna(val):
                    correlations.append({
                        "col_a": numeric_cols[i],
                        "col_b": numeric_cols[j],
                        "correlation": round(val, 4)
                    })
        correlations = sorted(
            correlations,
            key=lambda x: abs(x["correlation"]),
            reverse=True
        )[:10]

    # --- 6. DUPLICATES ---
    duplicate_count = int(df.duplicated().sum())

    result = {
        "shape": shape_info,
        "missing_values": missing_info,
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "top_correlations": correlations,
        "duplicate_rows": duplicate_count
    }

    return convert_types(result)
