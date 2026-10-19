from pathlib import Path
import json
import sys
import pandas as pd

# Support UTF-8 output in Windows terminals.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Resolve folders from this script's location.
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
ANALYSIS_DIR = PROJECT_DIR / "analysis"
OUTPUT_DIR = ANALYSIS_DIR / "output"
NARRATOR_DIR = PROJECT_DIR / "narrator"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NARRATOR_DIR.mkdir(parents=True, exist_ok=True)

# Reference revenue calculated in Part 1 using the original SQL dataset.
RAW_SQL_REVENUE_REFERENCE = 99860.20


def main():
    # 1. Load untouched source CSV files.
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")

    print("SOURCE DATA")
    print("Customers:", customers.shape)
    print("Products:", products.shape)
    print("Orders:", orders.shape)

    # 2. Standardize payment method labels.
    orders["payment_method"] = (
        orders["payment_method"].astype("string").str.strip().str.upper()
    )

    # 3. Identify and remove duplicate business records.
    duplicate_columns = [
        "customer_id", "product_id", "order_date", "quantity",
        "discount_pct", "payment_method", "rating", "returned"
    ]

    duplicates = orders.loc[
        orders.duplicated(subset=duplicate_columns, keep="first")
    ].copy()

    orders = orders.drop_duplicates(
        subset=duplicate_columns, keep="first"
    ).copy()

    # 4. Impute missing values using the agreed rules.
    missing_before = {
        column: int(orders[column].isna().sum())
        for column in ["discount_pct", "rating"]
    }

    orders["discount_pct"] = orders["discount_pct"].fillna(0)
    median_rating = orders["rating"].median()
    orders["rating"] = orders["rating"].fillna(median_rating)

    # 5. Reconcile orders with product and customer information.
    reconciled = orders.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    reconciled = reconciled.merge(
        customers[["customer_id", "city", "city_tier"]],
        on="customer_id",
        how="left",
        validate="many_to_one"
    )

    if reconciled["price"].isna().any():
        raise ValueError("Some orders do not have a matching product price.")

    if reconciled["city"].isna().any():
        raise ValueError("Some orders do not have matching customer details.")

    reconciled["revenue"] = (
        reconciled["price"]
        * reconciled["quantity"]
        * (1 - reconciled["discount_pct"] / 100)
    )

    # 6. Independently calculate the value of removed duplicate rows.
    removed_rows = duplicates.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    removed_rows["order_value"] = (
        removed_rows["quantity"]
        * removed_rows["price"]
        * (1 - removed_rows["discount_pct"].fillna(0) / 100)
    )

    duplicate_revenue = float(removed_rows["order_value"].sum())
    cleaned_revenue = float(reconciled["revenue"].sum())
    revenue_difference = RAW_SQL_REVENUE_REFERENCE - cleaned_revenue

    # 7. Flag quantity outliers using the IQR rule. Do not delete them.
    q1 = float(reconciled["quantity"].quantile(0.25))
    q3 = float(reconciled["quantity"].quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    reconciled["is_outlier"] = (
        (reconciled["quantity"] < lower_bound)
        | (reconciled["quantity"] > upper_bound)
    )

    outliers = reconciled.loc[
        reconciled["is_outlier"],
        ["order_id", "quantity"]
    ].copy()

    # 8. Return rates by payment method.
    payment_summary = (
        reconciled.groupby("payment_method")
        .agg(
            total_orders=("order_id", "count"),
            returned_orders=("returned", "sum")
        )
        .reset_index()
    )

    payment_summary["return_rate_pct"] = (
        payment_summary["returned_orders"]
        / payment_summary["total_orders"]
        * 100
    )

    payment_summary = payment_summary.sort_values(
        "return_rate_pct", ascending=False
    )

    # 9. Return rates by payment method and city tier.
    segment_summary = (
        reconciled.groupby(["payment_method", "city_tier"])
        .agg(
            total_orders=("order_id", "count"),
            returned_orders=("returned", "sum")
        )
        .reset_index()
    )

    segment_summary["return_rate_pct"] = (
        segment_summary["returned_orders"]
        / segment_summary["total_orders"]
        * 100
    )

    highest_risk_segment = segment_summary.loc[
        segment_summary["return_rate_pct"].idxmax()
    ]

    # 10. Correlation analysis.
    correlation_columns = [
        "rating", "returned", "discount_pct", "quantity"
    ]
    correlation_matrix = reconciled[correlation_columns].corr()

    # 11. Monthly revenue including and excluding flagged outliers.
    dated = reconciled.copy()
    dated["order_date"] = pd.to_datetime(dated["order_date"])
    dated["order_month"] = dated["order_date"].dt.to_period("M").astype(str)

    monthly_all = (
        dated.groupby("order_month", as_index=False)["revenue"]
        .sum()
        .sort_values("order_month")
    )

    corrected = dated.loc[~dated["is_outlier"]].copy()

    monthly_corrected = (
        corrected.groupby("order_month", as_index=False)["revenue"]
        .sum()
        .sort_values("order_month")
    )

    monthly_corrected["previous_month_revenue"] = (
        monthly_corrected["revenue"].shift(1)
    )

    monthly_corrected["revenue_change"] = (
        monthly_corrected["revenue"]
        - monthly_corrected["previous_month_revenue"]
    )

    monthly_corrected["revenue_change_pct"] = (
        monthly_corrected["revenue_change"]
        / monthly_corrected["previous_month_revenue"]
        * 100
    )

    peak = monthly_corrected.loc[monthly_corrected["revenue"].idxmax()]

    changes = monthly_corrected.dropna(subset=["revenue_change"])
    largest_increase = changes.loc[changes["revenue_change"].idxmax()]
    largest_decrease = changes.loc[changes["revenue_change"].idxmin()]

    # 12. Save deterministic output files for downstream scripts.
    reconciled.to_csv(OUTPUT_DIR / "cleaned_orders.csv", index=False)
    outliers.to_csv(OUTPUT_DIR / "quantity_outliers.csv", index=False)
    payment_summary.to_csv(
        OUTPUT_DIR / "payment_return_rates.csv", index=False
    )
    segment_summary.to_csv(
        OUTPUT_DIR / "segment_return_rates.csv", index=False
    )
    monthly_all.to_csv(
        OUTPUT_DIR / "monthly_revenue_all_orders.csv", index=False
    )
    monthly_corrected.to_csv(
        OUTPUT_DIR / "monthly_revenue_corrected.csv", index=False
    )

    # Build a JSON file using ordinary Python data types.
    findings = {
        "raw_sql_revenue_reference": round(RAW_SQL_REVENUE_REFERENCE, 2),
        "cleaned_revenue": round(cleaned_revenue, 2),
        "revenue_difference": round(revenue_difference, 2),
        "duplicate_count": int(len(duplicates)),
        "duplicate_order_ids": duplicates["order_id"].astype(str).tolist(),
        "duplicate_revenue_removed": round(duplicate_revenue, 2),
        "cleaned_order_count": int(len(reconciled)),
        "outlier_count": int(len(outliers)),
        "outliers": [
            {
                "order_id": str(row["order_id"]),
                "quantity": int(row["quantity"])
            }
            for _, row in outliers.iterrows()
        ],
        "median_rating_used": (
            float(median_rating) if pd.notna(median_rating) else None
        ),
        "missing_values_before_imputation": missing_before,
        "payment_return_rates": [
            {
                "payment_method": str(row["payment_method"]),
                "total_orders": int(row["total_orders"]),
                "returned_orders": int(row["returned_orders"]),
                "return_rate_pct": round(float(row["return_rate_pct"]), 3)
            }
            for _, row in payment_summary.iterrows()
        ],
        "highest_risk_segment": {
            "payment_method": str(highest_risk_segment["payment_method"]),
            "city_tier": int(highest_risk_segment["city_tier"]),
            "return_rate_pct": round(
                float(highest_risk_segment["return_rate_pct"]), 3
            )
        },
        "correlations": {
            row: {
                col: round(float(correlation_matrix.loc[row, col]), 6)
                for col in correlation_matrix.columns
            }
            for row in correlation_matrix.index
        },
        "monthly_revenue_all_orders": [
            {
                "month": str(row["order_month"]),
                "revenue": round(float(row["revenue"]), 2)
            }
            for _, row in monthly_all.iterrows()
        ],
        "monthly_revenue_corrected": [
            {
                "month": str(row["order_month"]),
                "revenue": round(float(row["revenue"]), 2),
                "revenue_change": (
                    round(float(row["revenue_change"]), 2)
                    if pd.notna(row["revenue_change"]) else None
                ),
                "revenue_change_pct": (
                    round(float(row["revenue_change_pct"]), 2)
                    if pd.notna(row["revenue_change_pct"]) else None
                )
            }
            for _, row in monthly_corrected.iterrows()
        ],
        "corrected_peak_month": str(peak["order_month"]),
        "corrected_peak_revenue": round(float(peak["revenue"]), 2),
        "largest_monthly_increase": {
            "month": str(largest_increase["order_month"]),
            "amount": round(float(largest_increase["revenue_change"]), 2),
            "pct": round(float(largest_increase["revenue_change_pct"]), 2)
        },
        "largest_monthly_decrease": {
            "month": str(largest_decrease["order_month"]),
            "amount": round(float(largest_decrease["revenue_change"]), 2),
            "pct": round(float(largest_decrease["revenue_change_pct"]), 2)
        }
    }

    findings_path = NARRATOR_DIR / "findings.json"
    with findings_path.open("w", encoding="utf-8") as file:
        json.dump(findings, file, indent=2, sort_keys=True, ensure_ascii=False)
        file.write("\n")

    # Print key results for validation.
    print("\nREPRODUCIBLE ANALYSIS RESULTS")
    print("Duplicate rows removed:", len(duplicates))
    print("Cleaned order count:", len(reconciled))
    print(f"Raw SQL revenue reference: ₹{RAW_SQL_REVENUE_REFERENCE:,.2f}")
    print(f"Cleaned Python revenue: ₹{cleaned_revenue:,.2f}")
    print(f"Removed duplicate revenue: ₹{duplicate_revenue:,.2f}")
    print("Quantity outliers flagged:", len(outliers))
    print("\nReturn rates by payment method:")
    print(payment_summary.round(3).to_string(index=False))
    print("\nHighest-risk segment:")
    print(
        f"{highest_risk_segment['payment_method']} / "
        f"Tier {int(highest_risk_segment['city_tier'])}: "
        f"{highest_risk_segment['return_rate_pct']:.3f}%"
    )
    print(
        f"\nCorrected revenue peak: {peak['order_month']} — "
        f"₹{peak['revenue']:,.2f}"
    )
    print("\nFindings JSON:", findings_path)
    print("Output folder:", OUTPUT_DIR)
    print("Analysis completed successfully.")


if __name__ == "__main__":
    main()
