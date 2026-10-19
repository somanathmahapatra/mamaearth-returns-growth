
import json
import os
from pathlib import Path

from google.genai import Client, types


# Locate the files relative to this Python script.
BASE_DIR = Path(__file__).resolve().parent
FINDINGS_PATH = BASE_DIR / "findings.json"
OUTPUT_PATH = BASE_DIR / "sample_output.txt"

MODEL_NAME = "gemini-3.8-flash"


def format_inr(value):
    """Format a numeric value as Indian rupees."""
    return f"₹{float(value):,.2f}"


def format_month(month):
    """Convert YYYY-MM into a readable month and year."""
    from datetime import datetime

    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def prepare_findings(findings):
    """Map the existing analysis JSON to the required business findings."""

    payment_rates = findings.get("payment_return_rates", [])

    if isinstance(payment_rates, list):
        payment_rates = {
            item["payment_method"]: round(item["return_rate_pct"], 1)
            for item in payment_rates
        }

    highest_risk = findings["highest_risk_segment"]

    peak_month = findings.get("true_peak_month", {})
    if not peak_month:
        peak_month = {
            "month": findings["corrected_peak_month"],
            "revenue_inr": findings["corrected_peak_revenue"],
        }

    all_months = {
        item["month"]: item["revenue"]
        for item in findings.get("monthly_revenue_all_orders", [])
    }

    corrected_months = {
        item["month"]: item["revenue"]
        for item in findings.get("monthly_revenue_corrected", [])
    }

    january = "2026-01"

    return {
        "cleaned_total_revenue_inr": findings.get(
            "cleaned_total_revenue_inr",
            findings["cleaned_revenue"],
        ),
        "raw_total_revenue_inr": findings.get(
            "raw_total_revenue_inr",
            findings["raw_sql_revenue_reference"],
        ),
        "duplicate_reconciliation_delta_inr": findings.get(
            "duplicate_reconciliation_delta_inr",
            findings["duplicate_revenue_removed"],
        ),
        "return_rate_by_payment": payment_rates,
        "highest_risk_segment": {
            "payment_method": highest_risk["payment_method"],
            "city_tier": highest_risk["city_tier"],
            "return_rate_pct": round(highest_risk["return_rate_pct"], 1),
        },
        "true_peak_month": {
            "month": peak_month["month"],
            "revenue_inr": peak_month["revenue_inr"],
        },
        "outlier_inflated_month": {
            "month": january,
            "apparent_revenue_inr": all_months.get(january),
            "corrected_revenue_inr": corrected_months.get(january),
        },
    }


def generate_offline_narrative(findings):
    """Generate a deterministic narrative without any API or network access."""

    data = prepare_findings(findings)

    rates = data["return_rate_by_payment"]
    risk = data["highest_risk_segment"]
    peak = data["true_peak_month"]
    january = data["outlier_inflated_month"]

    return f"""Situation

The cleaned order dataset contains {findings['cleaned_order_count']} orders, with cleaned revenue of {format_inr(data['cleaned_total_revenue_inr'])}. The payment-method return rates are COD at {rates['COD']:.1f}%, UPI at {rates['UPI']:.1f}%, and CARD at {rates['CARD']:.1f}%. The corrected monthly revenue series identifies {format_month(peak['month'])} as the peak month, with revenue of {format_inr(peak['revenue_inr'])}.

Complication

The raw SQL revenue reference is {format_inr(data['raw_total_revenue_inr'])}, while cleaned revenue is {format_inr(data['cleaned_total_revenue_inr'])}. The reconciliation difference is {format_inr(data['duplicate_reconciliation_delta_inr'])}, attributed to the duplicate orders removed during cleaning. The highest-risk segment is {risk['payment_method']} in city tier {risk['city_tier']}, with a return rate of {risk['return_rate_pct']:.1f}%. January's apparent revenue of {format_inr(january['apparent_revenue_inr'])} is inflated by the flagged bulk orders; corrected January revenue is {format_inr(january['corrected_revenue_inr'])}.

Resolution

Prioritize investigation of COD orders in tier {risk['city_tier']} cities, starting with return reasons, delivery confirmation, and customer feedback. Monitor return rates separately by payment method and city tier, and evaluate any operational changes against subsequent results. Use the duplicate-reconciled revenue and outlier-corrected monthly series for financial reporting. Review the January bulk orders separately rather than treating their apparent revenue as normal demand. Validate the impact of these actions using the same cleaned definitions and metrics in future reporting.
"""


def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a Situation–Complication–Resolution narrative.

    Returns a dictionary containing the narrative and generation source.
    Uses a deterministic offline fallback if the API key is absent
    or the Gemini request fails.
    """

    system_instruction = """
You are a senior data analyst writing for Mamaearth's regional operations
and finance heads.

Write a concise, actionable business narrative using exactly three labeled
sections: Situation, Complication, and Resolution.

Use only the supplied findings. Every number in the narrative must come
from the supplied findings and retain its supplied value; do not invent
statistics, dates, percentages, financial values, or causal claims.
Clearly distinguish observed facts from recommendations.
Explain the business significance and recommend practical next steps.
"""

    # Build the prompt from the supplied findings, not hardcoded figures.
    user_prompt = (
        "Write the business narrative using these verified findings:\n\n"
        + json.dumps(prepare_findings(findings), indent=2)
    )

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "narrative": generate_offline_narrative(findings),
            "source": "offline_fallback",
            "error": "GEMINI_API_KEY is not configured.",
        }

    try:
        client = Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000),
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # A factual report should be reproducible, not creative.
                temperature=0.0,
                max_output_tokens=500,
            ),
        )

        narrative = response.text

        if not narrative or not narrative.strip():
            raise ValueError("Gemini returned an empty narrative.")

        return {
            "narrative": narrative.strip(),
            "source": "gemini",
            "error": None,
        }

    except Exception as exc:
        # Preserve pipeline functionality if the API is unavailable.
        return {
            "narrative": generate_offline_narrative(findings),
            "source": "offline_fallback",
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    """Load findings, generate the narrative, and save the output."""

    with FINDINGS_PATH.open("r", encoding="utf-8") as file:
        findings = json.load(file)

    result = generate_scr_narrative(findings)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        file.write(result["narrative"] + "\n")

    print("Narrative saved to:", OUTPUT_PATH)
    print("Generation source:", result["source"])

    if result["error"]:
        print("Fallback reason:", result["error"])

    print("\n" + result["narrative"])


if __name__ == "__main__":
    main()
