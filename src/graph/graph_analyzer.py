from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_FEATURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sparkov_features.parquet"
)

DEFAULT_RISK_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sparkov_risk_engine.parquet"
)


class GraphAnalyzer:
    """
    Performs the first graph-based fraud analysis layer for AURA.

    The analyzer uses the existing customer -> transaction relationship
    and combines it with the existing risk-engine output.

    This first version focuses on explainable customer-level network
    indicators before introducing more complex graph algorithms.
    """

    def __init__(
        self,
        feature_path: Optional[Path] = None,
        risk_path: Optional[Path] = None,
    ):
        self.feature_path = (
            Path(feature_path)
            if feature_path
            else DEFAULT_FEATURE_PATH
        )

        self.risk_path = (
            Path(risk_path)
            if risk_path
            else DEFAULT_RISK_PATH
        )

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def load_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load feature data and risk-engine output and merge them by
        transaction ID.
        """

        if not self.feature_path.exists():
            raise FileNotFoundError(
                f"Feature dataset not found: {self.feature_path}"
            )

        if not self.risk_path.exists():
            raise FileNotFoundError(
                f"Risk-engine dataset not found: {self.risk_path}"
            )

        feature_df = pd.read_parquet(
            self.feature_path,
            engine="pyarrow",
        )

        risk_df = pd.read_parquet(
            self.risk_path,
            engine="pyarrow",
        )

        # Use a sample during development/testing.
        if limit is not None:
            feature_df = feature_df.head(limit)

            transaction_ids = set(
                feature_df["trans_num"].astype(str)
            )

            risk_df = risk_df[
                risk_df["trans_num"].astype(str).isin(transaction_ids)
            ]

        # Avoid duplicate columns during merge.
        risk_columns = [
            "trans_num",
            "final_risk_score",
            "risk_band",
            "investigation_flag",
            "is_fraud",
        ]

        available_risk_columns = [
            column
            for column in risk_columns
            if column in risk_df.columns
        ]

        risk_df = risk_df[available_risk_columns].copy()

        feature_df["trans_num"] = feature_df["trans_num"].astype(str)
        risk_df["trans_num"] = risk_df["trans_num"].astype(str)

        df = feature_df.merge(
            risk_df,
            on="trans_num",
            how="left",
            suffixes=("", "_risk"),
        )

        return df

    # ------------------------------------------------------------------
    # CUSTOMER GRAPH METRICS
    # ------------------------------------------------------------------

    def calculate_customer_metrics(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate explainable customer-level graph metrics.
        """

        working = df.copy()

        working["cc_num"] = working["cc_num"].astype(str)

        # --------------------------------------------------------------
        # Basic transaction count
        # --------------------------------------------------------------

        customer_metrics = (
            working
            .groupby("cc_num")
            .agg(
                transaction_count=("trans_num", "nunique"),
            )
            .reset_index()
        )

        # --------------------------------------------------------------
        # Unique merchants
        # --------------------------------------------------------------

        merchant_column = None

        possible_merchant_columns = [
            "merchant",
            "merchant_name",
            "merchant_id",
        ]

        for column in possible_merchant_columns:
            if column in working.columns:
                merchant_column = column
                break

        if merchant_column:
            merchant_counts = (
                working
                .groupby("cc_num")[merchant_column]
                .nunique()
                .reset_index(
                    name="unique_merchant_count"
                )
            )

            customer_metrics = customer_metrics.merge(
                merchant_counts,
                on="cc_num",
                how="left",
            )
        else:
            customer_metrics["unique_merchant_count"] = 0

        # --------------------------------------------------------------
        # Fraud-linked transactions
        # --------------------------------------------------------------

        if "is_fraud" in working.columns:

            fraud_counts = (
                working
                .groupby("cc_num")["is_fraud"]
                .sum()
                .reset_index(
                    name="fraud_transaction_count"
                )
            )

            customer_metrics = customer_metrics.merge(
                fraud_counts,
                on="cc_num",
                how="left",
            )

        else:
            customer_metrics["fraud_transaction_count"] = 0

        # --------------------------------------------------------------
        # High-risk transactions
        # --------------------------------------------------------------

        if "final_risk_score" in working.columns:

            high_risk = (
                working
                .assign(
                    high_risk_transaction=(
                        working["final_risk_score"] >= 70
                    ).astype(int)
                )
                .groupby("cc_num")[
                    "high_risk_transaction"
                ]
                .sum()
                .reset_index(
                    name="high_risk_transaction_count"
                )
            )

            customer_metrics = customer_metrics.merge(
                high_risk,
                on="cc_num",
                how="left",
            )

        else:
            customer_metrics[
                "high_risk_transaction_count"
            ] = 0

        # --------------------------------------------------------------
        # Average risk
        # --------------------------------------------------------------

        if "final_risk_score" in working.columns:

            average_risk = (
                working
                .groupby("cc_num")["final_risk_score"]
                .mean()
                .reset_index(
                    name="average_transaction_risk"
                )
            )

            customer_metrics = customer_metrics.merge(
                average_risk,
                on="cc_num",
                how="left",
            )

        else:
            customer_metrics[
                "average_transaction_risk"
            ] = 0

        # --------------------------------------------------------------
        # Maximum risk
        # --------------------------------------------------------------

        if "final_risk_score" in working.columns:

            maximum_risk = (
                working
                .groupby("cc_num")["final_risk_score"]
                .max()
                .reset_index(
                    name="maximum_transaction_risk"
                )
            )

            customer_metrics = customer_metrics.merge(
                maximum_risk,
                on="cc_num",
                how="left",
            )

        else:
            customer_metrics[
                "maximum_transaction_risk"
            ] = 0

        # --------------------------------------------------------------
        # Fraud ratio
        # --------------------------------------------------------------

        customer_metrics["fraud_ratio"] = (
            customer_metrics["fraud_transaction_count"]
            / customer_metrics["transaction_count"].replace(0, 1)
        )

        # --------------------------------------------------------------
        # High-risk ratio
        # --------------------------------------------------------------

        customer_metrics["high_risk_ratio"] = (
            customer_metrics["high_risk_transaction_count"]
            / customer_metrics["transaction_count"].replace(0, 1)
        )

        return customer_metrics

    # ------------------------------------------------------------------
    # GRAPH RISK SCORE
    # ------------------------------------------------------------------

    def calculate_graph_risk(
        self,
        customer_metrics: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate an explainable graph risk score.

        The score combines:
        - fraud ratio
        - high-risk transaction ratio
        - average transaction risk
        - maximum transaction risk
        """

        df = customer_metrics.copy()

        fraud_component = (
            df["fraud_ratio"] * 100
        )

        high_risk_component = (
            df["high_risk_ratio"] * 100
        )

        average_risk_component = (
            df["average_transaction_risk"]
            .fillna(0)
        )

        maximum_risk_component = (
            df["maximum_transaction_risk"]
            .fillna(0)
        )

        df["graph_risk_score"] = (
            0.35 * fraud_component
            + 0.25 * high_risk_component
            + 0.25 * average_risk_component
            + 0.15 * maximum_risk_component
        )

        # Keep score within 0–100.
        df["graph_risk_score"] = (
            df["graph_risk_score"]
            .clip(0, 100)
        )

        # --------------------------------------------------------------
        # Graph risk band
        # --------------------------------------------------------------

        def assign_band(score):

            if score >= 70:
                return "HIGH"

            if score >= 40:
                return "MEDIUM"

            return "LOW"

        df["graph_risk_band"] = (
            df["graph_risk_score"]
            .apply(assign_band)
        )

        return df

    # ------------------------------------------------------------------
    # TRANSACTION-LEVEL GRAPH ENRICHMENT
    # ------------------------------------------------------------------

    def enrich_transactions(
        self,
        df: pd.DataFrame,
        customer_metrics: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Attach customer graph metrics to every transaction.
        """

        enriched = df.copy()

        enriched["cc_num"] = enriched["cc_num"].astype(str)
        customer_metrics["cc_num"] = (
            customer_metrics["cc_num"].astype(str)
        )

        graph_columns = [
            "cc_num",
            "transaction_count",
            "unique_merchant_count",
            "fraud_transaction_count",
            "high_risk_transaction_count",
            "average_transaction_risk",
            "maximum_transaction_risk",
            "fraud_ratio",
            "high_risk_ratio",
            "graph_risk_score",
            "graph_risk_band",
        ]

        available_columns = [
            column
            for column in graph_columns
            if column in customer_metrics.columns
        ]

        enriched = enriched.merge(
            customer_metrics[available_columns],
            on="cc_num",
            how="left",
        )

        return enriched

    # ------------------------------------------------------------------
    # GRAPH REASONS
    # ------------------------------------------------------------------

    def generate_graph_reasons(
        self,
        row: pd.Series,
    ) -> list:
        """
        Generate human-readable graph investigation reasons.
        """

        reasons = []

        if row.get("fraud_transaction_count", 0) > 0:
            reasons.append(
                "Customer is connected to previously identified "
                "fraudulent transaction(s)"
            )

        if row.get("high_risk_transaction_count", 0) > 0:
            reasons.append(
                "Customer is connected to high-risk transaction(s)"
            )

        if row.get("unique_merchant_count", 0) >= 5:
            reasons.append(
                "Customer has transaction relationships with "
                "multiple merchants"
            )

        if row.get("fraud_ratio", 0) >= 0.20:
            reasons.append(
                "Customer has an elevated fraud-linked transaction ratio"
            )

        if row.get("high_risk_ratio", 0) >= 0.30:
            reasons.append(
                "Customer has a high concentration of high-risk transactions"
            )

        if not reasons:
            reasons.append(
                "No significant graph-based risk relationship identified"
            )

        return reasons

    # ------------------------------------------------------------------
    # COMPLETE ANALYSIS
    # ------------------------------------------------------------------

    def analyze(self, limit: Optional[int] = None) -> dict:
        """
        Run the complete graph-analysis pipeline.
        """

        df = self.load_data(limit=limit)

        customer_metrics = self.calculate_customer_metrics(df)

        customer_metrics = self.calculate_graph_risk(
            customer_metrics
        )

        enriched_transactions = self.enrich_transactions(
            df,
            customer_metrics,
        )

        enriched_transactions[
            "graph_reasons"
        ] = enriched_transactions.apply(
            self.generate_graph_reasons,
            axis=1,
        )

        return {
            "rows_analyzed": len(df),
            "customers_analyzed": len(customer_metrics),
            "customer_metrics": customer_metrics,
            "transaction_graph_analysis": enriched_transactions,
        }


# ----------------------------------------------------------------------
# COMMAND-LINE TEST
# ----------------------------------------------------------------------

if __name__ == "__main__":

    analyzer = GraphAnalyzer()

    result = analyzer.analyze(limit=10000)

    print("AURA Graph Analyzer")
    print("=" * 60)

    print(
        f"Transactions analyzed: "
        f"{result['rows_analyzed']}"
    )

    print(
        f"Customers analyzed: "
        f"{result['customers_analyzed']}"
    )

    customer_metrics = result["customer_metrics"]

    print("\nGraph risk distribution:")
    print(
        customer_metrics[
            "graph_risk_band"
        ]
        .value_counts()
        .to_string()
    )

    print("\nCustomer graph metrics sample:")
    print(
        customer_metrics.head(10).to_string(
            index=False
        )
    )

    transactions = result[
        "transaction_graph_analysis"
    ]

    print("\nTransaction graph-analysis sample:")
    print(
        transactions[
            [
                "trans_num",
                "cc_num",
                "graph_risk_score",
                "graph_risk_band",
                "graph_reasons",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    