from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "analysis" / "output"
VISUALIZATION_DIR = PROJECT_DIR / "visualizations"


def plot_return_rate_by_payment():
    data_path = OUTPUT_DIR / "payment_return_rates.csv"
    df = pd.read_csv(data_path)

    df = df.sort_values("return_rate_pct", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df["payment_method"], df["return_rate_pct"])

    ax.set_title("COD Returns at 44.4% — 3x Card")
    ax.set_xlabel("Payment Method")
    ax.set_ylabel("Return Rate (%)")
    ax.set_ylim(0, max(df["return_rate_pct"]) * 1.25)

    for bar, value in zip(bars, df["return_rate_pct"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}%",
            ha="center",
            va="bottom"
        )

    fig.tight_layout()
    output_path = VISUALIZATION_DIR / "return_rate_by_payment.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def plot_monthly_revenue_trend():
    data_path = OUTPUT_DIR / "monthly_revenue_corrected.csv"
    df = pd.read_csv(data_path)

    df["order_month"] = pd.to_datetime(df["order_month"])
    df = df.sort_values("order_month")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        df["order_month"],
        df["revenue"],
        marker="o",
        linewidth=2
    )

    peak_index = df["revenue"].idxmax()
    peak_month = pd.to_datetime(
    df.loc[peak_index, "order_month"]
).strftime("%B %Y")
    peak_revenue = df.loc[peak_index, "revenue"]

    ax.set_title(
        f"Monthly Revenue Trend (Outlier-Corrected) — "
        f"Peak: {peak_month}"
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    ax.ticklabel_format(style="plain", axis="y")
    ax.grid(True, alpha=0.3)

    ax.annotate(
        f"Peak: ₹{peak_revenue:,.2f}",
        xy=(df.loc[peak_index, "order_month"], peak_revenue),
        xytext=(10, 10),
        textcoords="offset points"
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    output_path = VISUALIZATION_DIR / "monthly_revenue_trend.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def main():
    VISUALIZATION_DIR.mkdir(parents=True, exist_ok=True)

    plot_return_rate_by_payment()
    plot_monthly_revenue_trend()

    print("Visualization generation completed successfully.")


if __name__ == "__main__":
    main()
