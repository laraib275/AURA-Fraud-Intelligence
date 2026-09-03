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

        self.risk_data_path = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / "sparkov_risk_engine.parquet"
        )

        self.graph_data_path = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / "sparkov_graph_analysis.parquet"
        )

        # Load model and datasets once
        self.model = joblib.load(self.model_path)
        self.df = pd.read_parquet(self.data_path)
        self.risk_df = pd.read_parquet(self.risk_data_path)
        self.graph_df = pd.read_parquet(self.graph_data_path)

        # Transaction IDs must be compared as strings. The CSV/parquet
        # pipeline can otherwise leave different string/object dtypes.
        self.df["trans_num"] = self.df["trans_num"].astype(str).str.strip()
        self.risk_df["trans_num"] = self.risk_df["trans_num"].astype(str).str.strip()
        self.graph_df["trans_num"] = self.graph_df["trans_num"].astype(str).str.strip()

        # Reuse these objects for every investigation
        self.imputer = self.model.named_steps["imputer"]
        self.rf_model = self.model.named_steps["model"]
        self.shap_explainer = shap.TreeExplainer(self.rf_model)

    def _generate_reasons(self, row, risk_row=None):
        reasons = []

        # Reasons from the final AURA risk-engine components.
        # These are the same components used to create final_risk_score.
        if risk_row is not None:
            if float(risk_row.get("amount_risk", 0)) >= 70:
                reasons.append("High transaction amount risk relative to the observed transaction population")
            if float(risk_row.get("velocity_risk", 0)) >= 70:
                reasons.append("High transaction velocity risk")
            if float(risk_row.get("novelty_risk", 0)) >= 70:
                reasons.append("High transaction novelty risk")
            if float(risk_row.get("anomaly_risk", 0)) >= 70:
                reasons.append("High anomaly risk score")
            if int(risk_row.get("anomaly_flag", 0)) == 1:
                reasons.append("Transaction was flagged by the anomaly detector")

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
            self.shap_explainer.shap_values(features_imputed)
        )

        if shap_values.ndim == 3:
            shap_fraud = shap_values[0, :, 1]

        elif shap_values.ndim == 2:
            shap_fraud = shap_values[0]

        else:
            raise ValueError(
                f"Unexpected SHAP shape: {shap_values.shape}"
            )

        explanation = pd.DataFrame(
            {
                "feature": self.MODEL_FEATURES,
                "value": features.iloc[0].values,
                "shap_value": shap_fraud,
            }
        )

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
        transaction_id = str(transaction_id).strip()

        matches = self.df[
            self.df["trans_num"] == transaction_id
        ]

        risk_matches = self.risk_df[
            self.risk_df["trans_num"] == transaction_id
        ]

        if risk_matches.empty:
            return {
                "error": (
                    f"Risk-engine record for transaction "
                    f"{transaction_id} not found."
                )
            }

        if len(risk_matches) > 1:
            return {
                "error": (
                    f"Multiple risk-engine records found for "
                    f"{transaction_id}."
                )
            }

        risk_row = risk_matches.iloc[0]

        graph_matches = self.graph_df[
            self.graph_df["trans_num"] == transaction_id
        ]

        if graph_matches.empty:
            return {
                "error": (
                    f"Graph-analysis record for transaction "
                    f"{transaction_id} not found."
                )
            }

        if len(graph_matches) > 1:
            return {
                "error": (
                    f"Multiple graph-analysis records found for "
                    f"{transaction_id}."
                )
            }

        graph_row = graph_matches.iloc[0]

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

        risk_score = float(
            risk_row["final_risk_score"]
        )

        risk_band = str(
            risk_row["risk_band"]
        ).upper()

        investigation_flag = bool(
            risk_row["investigation_flag"]
        )

        if risk_band == "CRITICAL":
            action = "IMMEDIATE INVESTIGATION"

        elif risk_band == "HIGH":
            action = "ESCALATE FOR INVESTIGATION"

        elif risk_band == "MEDIUM":
            action = "SEND TO REVIEW QUEUE"

        else:
            action = "APPROVE"

        reasons = self._generate_reasons(row, risk_row)

        shap_factors = self._get_shap_factors(
            features
        )

        return {
            "transaction_id": transaction_id,

            "transaction_time": str(
                row["transaction_time"]
            ),

            "amount": float(row["amt"]),

            # Graph-analysis output
            "graph_risk_score": round(
                float(graph_row["graph_risk_score"]),
                2,
            ),

            "graph_risk_band": str(
                graph_row["graph_risk_band"]
            ).upper(),

            "graph_metrics": {
                "transaction_count": int(
                    graph_row["transaction_count"]
                ),

                "unique_merchant_count": int(
                    graph_row["unique_merchant_count"]
                ),

                "fraud_transaction_count": int(
                    graph_row["fraud_transaction_count"]
                ),

                "high_risk_transaction_count": int(
                    graph_row["high_risk_transaction_count"]
                ),

                "average_transaction_risk": round(
                    float(
                        graph_row["average_transaction_risk"]
                    ),
                    2,
                ),

                "maximum_transaction_risk": round(
                    float(
                        graph_row["maximum_transaction_risk"]
                    ),
                    2,
                ),

                "fraud_ratio": round(
                    float(graph_row["fraud_ratio"]),
                    4,
                ),

                "high_risk_ratio": round(
                    float(graph_row["high_risk_ratio"]),
                    4,
                ),
            },

            "graph_reasons": graph_row["graph_reasons"],

            # Machine-learning model output
            "fraud_probability": fraud_probability,

            # Final AURA risk-engine output
            "risk_score": round(risk_score, 2),
            "risk_band": risk_band,
            "investigation_flag": investigation_flag,
            "recommended_action": action,

            # Risk-engine components
            "amount_risk": float(
                risk_row["amount_risk"]
            ),

            "velocity_risk": float(
                risk_row["velocity_risk"]
            ),

            "novelty_risk": float(
                risk_row["novelty_risk"]
            ),

            "behavioural_risk_score": float(
                risk_row["behavioural_risk_score"]
            ),

            "anomaly_score": float(
                risk_row["anomaly_score"]
            ),

            "anomaly_risk": float(
                risk_row["anomaly_risk"]
            ),

            # Explainability
            "investigation_reasons": reasons,
            "top_risk_factors": shap_factors,
        }
