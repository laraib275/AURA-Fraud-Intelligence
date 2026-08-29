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

        # ---------------------------------------------------------
        # FILE PATHS
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # LOAD MODEL AND DATA
        # ---------------------------------------------------------

        self.model = joblib.load(self.model_path)

        self.df = pd.read_parquet(
            self.data_path
        )

        self.risk_df = pd.read_parquet(
            self.risk_data_path
        )

        self.graph_df = pd.read_parquet(
            self.graph_data_path
        )

        # ---------------------------------------------------------
        # MODEL COMPONENTS
        # ---------------------------------------------------------

        self.imputer = self.model.named_steps["imputer"]

        self.rf_model = self.model.named_steps["model"]

        self.shap_explainer = shap.TreeExplainer(
            self.rf_model
        )

    # =============================================================
    # JSON SAFE CONVERSION
    # =============================================================

    def _to_python(self, obj):
        """
        Convert NumPy/Pandas objects into JSON-safe Python objects.

        NaN, NaT, positive infinity and negative infinity
        are converted to None so FastAPI can serialize them.
        """

        # Dictionary
        if isinstance(obj, dict):
            return {
                str(key): self._to_python(value)
                for key, value in obj.items()
            }

        # List / tuple
        if isinstance(obj, (list, tuple)):
            return [
                self._to_python(value)
                for value in obj
            ]

        # NumPy array
        if isinstance(obj, np.ndarray):
            return [
                self._to_python(value)
                for value in obj.tolist()
            ]

        # NumPy scalar
        if isinstance(obj, np.generic):
            return self._to_python(
                obj.item()
            )

        # Pandas timestamp
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()

        # Pandas NA / NaT
        if obj is pd.NA or obj is pd.NaT:
            return None

        # Python float
        if isinstance(obj, float):

            if not np.isfinite(obj):
                return None

            return obj

        # Integer / boolean / string / None
        return obj

    # =============================================================
    # INVESTIGATION REASONS
    # =============================================================

    def _generate_reasons(self, row):

        reasons = []

        # High velocity in previous hour
        if (
            pd.notna(row["transactions_prev_1h"])
            and row["transactions_prev_1h"] >= 3
        ):
            reasons.append(
                "High transaction velocity in the previous hour"
            )

        # Multiple transactions in 5 minutes
        if (
            pd.notna(row["transactions_prev_5min"])
            and row["transactions_prev_5min"] >= 2
        ):
            reasons.append(
                "Multiple transactions within a short time window"
            )

        # Large amount deviation
        if (
            pd.notna(row["amount_deviation_ratio"])
            and row["amount_deviation_ratio"] >= 3
        ):
            reasons.append(
                "Transaction amount is substantially above customer history"
            )

        # New merchant
        if (
            pd.notna(row["is_new_merchant"])
            and row["is_new_merchant"] == 1
        ):
            reasons.append(
                "Previously unseen merchant for this customer"
            )

        # New category
        if (
            pd.notna(row["is_new_category"])
            and row["is_new_category"] == 1
        ):
            reasons.append(
                "Previously unseen transaction category"
            )

        # Large geographic distance
        if (
            pd.notna(row["customer_merchant_distance_km"])
            and row["customer_merchant_distance_km"] >= 200
        ):
            reasons.append(
                "Large customer-merchant geographic distance"
            )

        # No transaction history
        if (
            pd.notna(row["customer_prev_count"])
            and row["customer_prev_count"] == 0
        ):
            reasons.append(
                "No prior transaction history available"
            )

        # Default reason
        if not reasons:
            reasons.append(
                "Model identified an anomalous transaction pattern"
            )

        return reasons

    # =============================================================
    # SHAP FACTORS
    # =============================================================

    def _get_shap_factors(self, features):

        features_imputed = self.imputer.transform(
            features
        )

        shap_values = np.asarray(
            self.shap_explainer.shap_values(
                features_imputed
            )
        )

        # ---------------------------------------------------------
        # Handle different SHAP output formats
        # ---------------------------------------------------------

        if shap_values.ndim == 3:

            shap_fraud = shap_values[
                0,
                :,
                1
            ]

        elif shap_values.ndim == 2:

            shap_fraud = shap_values[0]

        else:

            raise ValueError(
                f"Unexpected SHAP shape: {shap_values.shape}"
            )

        # ---------------------------------------------------------
        # Create explanation dataframe
        # ---------------------------------------------------------

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

        # Highest impact first
        explanation = explanation.sort_values(
            "abs_shap",
            ascending=False,
        )

        # Only factors increasing fraud risk
        explanation = explanation[
            explanation["shap_value"] > 0
        ]

        # Top 5
        explanation = explanation.head(5)

        return explanation.to_dict(
            "records"
        )

    # =============================================================
    # GRAPH ANALYSIS
    # =============================================================

    def _get_graph_analysis(self, graph_row):

        graph_analysis = {}

        for column in self.graph_df.columns:

            value = graph_row[column]

            graph_analysis[column] = value

        return graph_analysis

    # =============================================================
    # MAIN INVESTIGATION
    # =============================================================

    def investigate_transaction(
        self,
        transaction_id
    ):

        # ---------------------------------------------------------
        # FIND TRANSACTION
        # ---------------------------------------------------------

        matches = self.df[
            self.df["trans_num"] == transaction_id
        ]

        if matches.empty:

            return {
                "error": (
                    f"Transaction "
                    f"{transaction_id} not found."
                )
            }

        if len(matches) > 1:

            return {
                "error": (
                    f"Multiple records found for "
                    f"{transaction_id}."
                )
            }

        row = matches.iloc[0]

        # ---------------------------------------------------------
        # FIND RISK ENGINE RECORD
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # FIND GRAPH RECORD
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # MODEL FEATURES
        # ---------------------------------------------------------

        features = row[
            self.MODEL_FEATURES
        ].to_frame().T

        # ---------------------------------------------------------
        # FRAUD PROBABILITY
        # ---------------------------------------------------------

        fraud_probability = float(
            self.model.predict_proba(
                features
            )[0, 1]
        )

        # ---------------------------------------------------------
        # RISK ENGINE
        # ---------------------------------------------------------

        risk_score = float(
            risk_row["final_risk_score"]
        )

        risk_band = str(
            risk_row["risk_band"]
        ).upper()

        investigation_flag = bool(
            risk_row["investigation_flag"]
        )

        # ---------------------------------------------------------
        # RECOMMENDED ACTION
        # ---------------------------------------------------------

        if risk_band == "CRITICAL":

            action = (
                "IMMEDIATE INVESTIGATION"
            )

        elif risk_band == "HIGH":

            action = (
                "ESCALATE FOR INVESTIGATION"
            )

        elif risk_band == "MEDIUM":

            action = (
                "SEND TO REVIEW QUEUE"
            )

        else:

            action = "APPROVE"

        # ---------------------------------------------------------
        # INVESTIGATION REASONS
        # ---------------------------------------------------------

        reasons = self._generate_reasons(
            row
        )

        # ---------------------------------------------------------
        # SHAP FACTORS
        # ---------------------------------------------------------

        shap_factors = self._get_shap_factors(
            features
        )

        # ---------------------------------------------------------
        # GRAPH ANALYSIS
        # ---------------------------------------------------------

        graph_analysis = self._get_graph_analysis(
            graph_row
        )

        # ---------------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------------

        response = {

            "transaction_id": transaction_id,

            "transaction_time": str(
                row["transaction_time"]
            ),

            "amount": float(
                row["amt"]
            ),

            # Machine-learning output
            "fraud_probability": (
                fraud_probability
            ),

            # AURA risk engine
            "risk_score": float(
                round(
                    risk_score,
                    2
                )
            ),

            "risk_band": risk_band,

            "investigation_flag": (
                investigation_flag
            ),

            "recommended_action": action,

            # Risk components
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

            # Graph intelligence
            "graph_analysis": graph_analysis,
        }

        # ---------------------------------------------------------
        # MAKE EVERYTHING JSON SAFE
        # ---------------------------------------------------------

        return self._to_python(
            response
        )