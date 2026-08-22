from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class InvestigationEngine:
    """Generate AURA fraud investigation reports for transactions."""

    MODEL_FEATURES = [
        "amt",
        "log_amount",
        "hour",
        "day_of_week",
        "month",
        "day_of_month",
        "is_weekend",
        "customer_prev_count",
        "customer_prev_avg_amount",
        "customer_prev_median_amount",
        "customer_prev_std_amount",
        "amount_deviation_ratio",
        "seconds_since_prev_transaction",
        "transactions_prev_5min",
        "transactions_prev_1h",
        "transactions_prev_24h",
        "merchant_seen_before",
        "is_new_merchant",
        "category_seen_before",
        "is_new_category",
        "customer_merchant_distance_km",
    ]

    FINAL_THRESHOLD = 0.22

    def __init__(self):
        # Project-relative paths
        self.model_path = (
            PROJECT_ROOT
            / "models"
            / "random_forest_final.joblib"
        )

        self.data_path = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / "sparkov_features.parquet"
        )

        # Load model and dataset once
        self.model = joblib.load(self.model_path)
        self.df = pd.read_parquet(self.data_path)

        # Reuse these objects for every investigation
        self.imputer = self.model.named_steps["imputer"]
        self.rf_model = self.model.named_steps["model"]
        self.shap_explainer = shap.TreeExplainer(
            self.rf_model
        )

    def _get_risk_band(self, probability):
        if probability >= 0.50:
            return "HIGH", "ESCALATE FOR INVESTIGATION"

        if probability >= self.FINAL_THRESHOLD:
            return "MEDIUM", "SEND TO REVIEW QUEUE"

        return "LOW", "APPROVE"

    def _generate_reasons(self, row):
        reasons = []

        if (
            pd.notna(row["transactions_prev_1h"])
            and row["transactions_prev_1h"] >= 3
        ):
            reasons.append(
                "High transaction velocity in the previous hour"
            )

        if (
            pd.notna(row["transactions_prev_5min"])
            and row["transactions_prev_5min"] >= 2
        ):
            reasons.append(
                "Multiple transactions within a short time window"
            )

        if (
            pd.notna(row["amount_deviation_ratio"])
            and row["amount_deviation_ratio"] >= 3
        ):
            reasons.append(
                "Transaction amount is substantially above customer history"
            )

        if row["is_new_merchant"] == 1:
            reasons.append(
                "Previously unseen merchant for this customer"
            )

        if row["is_new_category"] == 1:
            reasons.append(
                "Previously unseen transaction category"
            )

        if (
            pd.notna(row["customer_merchant_distance_km"])
            and row["customer_merchant_distance_km"] >= 200
        ):
            reasons.append(
                "Large customer-merchant geographic distance"
            )

        if row["customer_prev_count"] == 0:
            reasons.append(
                "No prior transaction history available"
            )

        if not reasons:
            reasons.append(
                "Model identified an anomalous transaction pattern"
            )

        return reasons

    def _get_shap_factors(self, features):
        features_imputed = self.imputer.transform(features)

        shap_values = np.asarray(
            self.shap_explainer.shap_values(
                features_imputed
            )
        )

        if shap_values.ndim == 3:
            shap_fraud = shap_values[0, :, 1]

        elif shap_values.ndim == 2:
            shap_fraud = shap_values[0]

        else:
            raise ValueError(
                f"Unexpected SHAP shape: {shap_values.shape}"
            )

        explanation = pd.DataFrame({
            "feature": self.MODEL_FEATURES,
            "value": features.iloc[0].values,
            "shap_value": shap_fraud,
        })

        explanation["abs_shap"] = (
            explanation["shap_value"].abs()
        )

        explanation = explanation.sort_values(
            "abs_shap",
            ascending=False,
        )

        return (
            explanation[
                explanation["shap_value"] > 0
            ]
            .head(5)
            .to_dict("records")
        )

    def investigate_transaction(self, transaction_id):
        matches = self.df[
            self.df["trans_num"] == transaction_id
        ]

        if matches.empty:
            return {
                "error": (
                    f"Transaction {transaction_id} not found."
                )
            }

        if len(matches) > 1:
            return {
                "error": (
                    f"Multiple records found for {transaction_id}."
                )
            }

        row = matches.iloc[0]

        features = row[
            self.MODEL_FEATURES
        ].to_frame().T

        fraud_probability = float(
            self.model.predict_proba(features)[0, 1]
        )

        risk_score = round(
            fraud_probability * 100,
            2,
        )

        risk_band, action = self._get_risk_band(
            fraud_probability
        )

        reasons = self._generate_reasons(row)

        shap_factors = self._get_shap_factors(
            features
        )

        return {
            "transaction_id": transaction_id,
            "transaction_time": str(
                row["transaction_time"]
            ),
            "amount": float(row["amt"]),
            "fraud_probability": fraud_probability,
            "risk_score": risk_score,
            "risk_band": risk_band,
            "recommended_action": action,
            "investigation_reasons": reasons,
            "top_risk_factors": shap_factors,
        }