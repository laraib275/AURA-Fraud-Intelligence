from pathlib import Path

DATA_PATH = Path("data/processed")

list(DATA_PATH.glob("*"))

from pathlib import Path

import numpy as np
import pandas as pd

anomaly_df = pd.read_parquet(
    DATA_PATH / "sparkov_anomaly_scores.parquet"
)

features_df = pd.read_parquet(
    DATA_PATH / "sparkov_features.parquet"
)

print("Anomaly dataset shape:", anomaly_df.shape)
print("Features dataset shape:", features_df.shape)

print("Anomaly columns:")
print(anomaly_df.columns.tolist())

print("\nFeature columns:")
print(features_df.columns.tolist())

print(anomaly_df.head())
print(features_df.head())

# Identify the key risk-related columns

risk_columns = [
    col for col in anomaly_df.columns
    if any(keyword in col.lower() for keyword in [
        "anomaly",
        "behaviour",
        "risk",
        "fraud",
        "signal"
    ])
]

print("Risk-related columns:")
for col in risk_columns:
    print("-", col)

# Check whether the two datasets have the same transaction ordering

print(
    "Transaction IDs identical:",
    anomaly_df["trans_num"].equals(features_df["trans_num"])
)

print(
    "Row count identical:",
    len(anomaly_df) == len(features_df)
)

anomaly_df[
    [col for col in anomaly_df.columns
     if "anomaly" in col.lower()]
].head()

# Combine Phase 8 behavioural features with Phase 7 anomaly outputs
# using the transaction identifier rather than row position.

risk_df = features_df.merge(
    anomaly_df[
        [
            "trans_num",
            "anomaly_score",
            "anomaly_flag"
        ]
    ],
    on="trans_num",
    how="inner",
    validate="one_to_one"
)

print("Risk engine dataset shape:", risk_df.shape)

print("\nRisk engine columns:")
print(risk_df.columns.tolist())

behaviour_columns = [
    col for col in risk_df.columns
    if "behaviour" in col.lower()
]

print("Behavioural risk columns:")
for col in behaviour_columns:
    print("-", col)

# Check all columns available in the features dataset

for i, col in enumerate(features_df.columns, start=1):
    print(i, col)

# Check whether any behavioural signal columns are present

signal_columns = [
    col for col in features_df.columns
    if any(x in col.lower() for x in ["signal", "velocity", "novelty", "behaviour"])
]

print("Signal-related columns:")
for col in signal_columns:
    print("-", col)

# Define the core risk-engine inputs

ANOMALY_COLUMNS = [
    "anomaly_score",
    "anomaly_flag"
]

BEHAVIOUR_COLUMNS = [
    "amount_deviation_ratio",
    "transactions_prev_5min",
    "transactions_prev_1h",
    "transactions_prev_24h",
    "is_new_merchant",
    "is_new_category",
    "customer_merchant_distance_km"
]

available_anomaly_columns = [
    col for col in ANOMALY_COLUMNS
    if col in risk_df.columns
]

available_behaviour_columns = [
    col for col in BEHAVIOUR_COLUMNS
    if col in risk_df.columns
]

print("Available anomaly inputs:")
for col in available_anomaly_columns:
    print(" -", col)

print("\nAvailable behavioural inputs:")
for col in available_behaviour_columns:
    print(" -", col)

# Verify that all expected risk-engine inputs are available

missing_anomaly = [
    col for col in ANOMALY_COLUMNS
    if col not in risk_df.columns
]

missing_behaviour = [
    col for col in BEHAVIOUR_COLUMNS
    if col not in risk_df.columns
]

print("Missing anomaly inputs:", missing_anomaly)
print("Missing behavioural inputs:", missing_behaviour)

# ---------------------------------------------------------
# Phase 9 — Corrected Behavioural Risk Component
# ---------------------------------------------------------

# Missing historical information is treated as no observed
# behavioural deviation for the corresponding component.

amount_raw = (
    risk_df["amount_deviation_ratio"]
    .fillna(0)
    .clip(lower=0)
)

velocity_raw = (
    risk_df[
        [
            "transactions_prev_5min",
            "transactions_prev_1h",
            "transactions_prev_24h"
        ]
    ]
    .fillna(0)
    .max(axis=1)
)

novelty_raw = (
    risk_df["is_new_merchant"]
    .fillna(0)
    .astype(float)
    +
    risk_df["is_new_category"]
    .fillna(0)
    .astype(float)
)


# ---------------------------------------------------------
# Percentile normalization
# ---------------------------------------------------------

def percentile_score(series, percentile=0.99):
    upper = series.quantile(percentile)

    if upper <= 0:
        return pd.Series(0.0, index=series.index)

    return (
        series
        .clip(lower=0, upper=upper)
        / upper
        * 100
    )


risk_df["amount_risk"] = percentile_score(amount_raw)

risk_df["velocity_risk"] = percentile_score(velocity_raw)

risk_df["novelty_risk"] = percentile_score(novelty_raw)


# ---------------------------------------------------------
# Combined behavioural risk score
# ---------------------------------------------------------

risk_df["behavioural_risk_score"] = (
    risk_df["amount_risk"]
    + risk_df["velocity_risk"]
    + risk_df["novelty_risk"]
) / 3

risk_df["behavioural_risk_score"] = (
    risk_df["behavioural_risk_score"]
    .clip(0, 100)
)


print("Behavioural risk component created successfully.")

print(
    risk_df[
        [
            "amount_risk",
            "velocity_risk",
            "novelty_risk",
            "behavioural_risk_score"
        ]
    ].describe()
)

print("\nMissing values:")
print(
    risk_df[
        [
            "amount_risk",
            "velocity_risk",
            "novelty_risk",
            "behavioural_risk_score"
        ]
    ].isna().sum()
)

risk_df[
    [
        "trans_num",
        "amount_risk",
        "velocity_risk",
        "novelty_risk",
        "behavioural_risk_score",
        "is_fraud"
    ]
].head(20)

# ---------------------------------------------------------
# Anomaly Risk Component
# ---------------------------------------------------------
# Convert anomaly_score into a 0–100 risk scale.
# Higher anomaly_score = higher anomaly risk.

anomaly_min = risk_df["anomaly_score"].min()
anomaly_max = risk_df["anomaly_score"].max()

if anomaly_max == anomaly_min:
    risk_df["anomaly_risk"] = 0.0
else:
    risk_df["anomaly_risk"] = (
        (risk_df["anomaly_score"] - anomaly_min)
        / (anomaly_max - anomaly_min)
        * 100
    )

risk_df["anomaly_risk"] = (
    risk_df["anomaly_risk"]
    .clip(0, 100)
)

print("Anomaly risk created successfully.")

print(
    risk_df[
        [
            "anomaly_score",
            "anomaly_flag",
            "anomaly_risk"
        ]
    ].describe()
)

print("\nCorrelation with fraud:")
print(
    risk_df[
        ["anomaly_risk", "is_fraud"]
    ].corr(numeric_only=True)
)

risk_df[
    [
        "trans_num",
        "anomaly_score",
        "anomaly_flag",
        "anomaly_risk",
        "amount_risk",
        "velocity_risk",
        "novelty_risk",
        "behavioural_risk_score",
        "is_fraud"
    ]
].head(20)

# Combine behavioural and anomaly risk into a final risk score.

risk_df["final_risk_score"] = (
    0.60 * risk_df["behavioural_risk_score"]
    + 0.40 * risk_df["anomaly_risk"]
)

# Ensure the final score remains within 0–100
risk_df["final_risk_score"] = risk_df["final_risk_score"].clip(0, 100)

print("Final risk score created successfully.")

print(
    risk_df["final_risk_score"].describe()
)

# ---------------------------------------------------------
# Risk Band Assignment
# ---------------------------------------------------------

def assign_risk_band(score):
    if score < 30:
        return "Low"
    elif score < 60:
        return "Medium"
    elif score < 80:
        return "High"
    else:
        return "Critical"


risk_df["risk_band"] = (
    risk_df["final_risk_score"]
    .apply(assign_risk_band)
)

# Preserve the intended severity order
risk_band_order = [
    "Low",
    "Medium",
    "High",
    "Critical"
]

risk_df["risk_band"] = pd.Categorical(
    risk_df["risk_band"],
    categories=risk_band_order,
    ordered=True
)

print("Risk bands created successfully.")

print(
    risk_df["risk_band"]
    .value_counts()
    .sort_index()
)

# Flag transactions requiring investigation.

risk_df["investigation_flag"] = (
    (risk_df["final_risk_score"] >= 60)
    | (risk_df["anomaly_flag"] == 1)
)

print("Investigation flags created successfully.")

print(
    risk_df["investigation_flag"].value_counts()
)

risk_df[
    [
        "trans_num",
        "anomaly_score",
        "anomaly_flag",
        "anomaly_risk",
        "amount_risk",
        "velocity_risk",
        "novelty_risk",
        "behavioural_risk_score",
        "final_risk_score",
        "risk_band",
        "investigation_flag",
        "is_fraud"
    ]
].head(20)

# Compare fraud rate across risk bands.

risk_band_summary = (
    risk_df
    .groupby("risk_band", observed=True)
    .agg(
        transactions=("trans_num", "count"),
        fraud_cases=("is_fraud", "sum"),
        avg_risk_score=("final_risk_score", "mean")
    )
    .reset_index()
)

risk_band_summary["fraud_rate"] = (
    risk_band_summary["fraud_cases"]
    / risk_band_summary["transactions"]
)

risk_band_summary

# Examine the relationship between final risk score and fraud.

print("Final risk score distribution:")
print(risk_df["final_risk_score"].describe())

print("\nFraud rate by score ranges:")

risk_score_bins = pd.cut(
    risk_df["final_risk_score"],
    bins=[0, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    include_lowest=True
)

score_summary = (
    risk_df
    .groupby(risk_score_bins, observed=True)
    .agg(
        transactions=("trans_num", "count"),
        fraud_cases=("is_fraud", "sum"),
        avg_risk_score=("final_risk_score", "mean")
    )
    .reset_index()
)

score_summary["fraud_rate"] = (
    score_summary["fraud_cases"]
    / score_summary["transactions"]
)

score_summary

# Check whether higher behavioural risk actually corresponds to higher fraud.

behaviour_summary = (
    risk_df
    .groupby(
        pd.qcut(
            risk_df["behavioural_risk_score"],
            q=10,
            duplicates="drop"
        ),
        observed=True
    )
    .agg(
        transactions=("trans_num", "count"),
        fraud_cases=("is_fraud", "sum"),
        avg_behavioural_risk=("behavioural_risk_score", "mean")
    )
    .reset_index()
)

behaviour_summary["fraud_rate"] = (
    behaviour_summary["fraud_cases"]
    / behaviour_summary["transactions"]
)

behaviour_summary

# Check anomaly risk versus fraud.

anomaly_summary = (
    risk_df
    .groupby(
        pd.qcut(
            risk_df["anomaly_risk"],
            q=10,
            duplicates="drop"
        ),
        observed=True
    )
    .agg(
        transactions=("trans_num", "count"),
        fraud_cases=("is_fraud", "sum"),
        avg_anomaly_risk=("anomaly_risk", "mean")
    )
    .reset_index()
)

anomaly_summary["fraud_rate"] = (
    anomaly_summary["fraud_cases"]
    / anomaly_summary["transactions"]
)

anomaly_summary

risk_df[["anomaly_score", "anomaly_risk", "is_fraud"]].corr(numeric_only=True)

risk_df.groupby(
    pd.qcut(risk_df["anomaly_risk"], 10, duplicates="drop"),
    observed=True
)["is_fraud"].mean()

risk_df.groupby(
    pd.qcut(risk_df["behavioural_risk_score"], 10, duplicates="drop"),
    observed=True
)["is_fraud"].mean()

# ---------------------------------------------------------
# Final Risk Engine Validation
# ---------------------------------------------------------

validation_summary = pd.DataFrame({
    "metric": [
        "Total transactions",
        "Total fraud cases",
        "Overall fraud rate",
        "Low-risk fraud rate",
        "Medium-risk fraud rate",
        "High-risk fraud rate",
        "Critical-risk fraud rate",
        "Investigation rate"
    ],
    "value": [
        len(risk_df),
        risk_df["is_fraud"].sum(),
        risk_df["is_fraud"].mean(),
        risk_df.loc[
            risk_df["risk_band"] == "Low", "is_fraud"
        ].mean(),
        risk_df.loc[
            risk_df["risk_band"] == "Medium", "is_fraud"
        ].mean(),
        risk_df.loc[
            risk_df["risk_band"] == "High", "is_fraud"
        ].mean(),
        risk_df.loc[
            risk_df["risk_band"] == "Critical", "is_fraud"
        ].mean(),
        risk_df["investigation_flag"].mean()
    ]
})

validation_summary

# Final risk-engine output
final_risk_df = risk_df[
    [
        "trans_num",
        "amount_risk",
        "velocity_risk",
        "novelty_risk",
        "behavioural_risk_score",
        "anomaly_score",
        "anomaly_risk",
        "final_risk_score",
        "risk_band",
        "investigation_flag",
        "is_fraud"
    ]
].copy()

print("Final risk-engine dataset:")
print(final_risk_df.head())

print("\nFinal columns:")
print(final_risk_df.columns.tolist())

print("\nRisk-band distribution:")
print(final_risk_df["risk_band"].value_counts())

# Save final risk-engine output for downstream use

OUTPUT_PATH = DATA_PATH / "sparkov_risk_engine.parquet"

final_risk_df.to_parquet(
    OUTPUT_PATH,
    index=False
)

print(f"\nRisk-engine output saved to: {OUTPUT_PATH}")

