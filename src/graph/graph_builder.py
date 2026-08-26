from pathlib import Path
from typing import Optional

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sparkov_features.parquet"
)


class GraphBuilder:
    """
    Builds transaction relationship data for AURA's graph-analysis layer.

    The first version deliberately uses a lightweight edge representation
    instead of constructing a full in-memory NetworkX graph. This keeps the
    implementation suitable for the 1.29M+ transaction dataset.
    """

    REQUIRED_COLUMNS = {
        "cc_num",
        "trans_num",
        "transaction_time",
        "amt",
    }

    OPTIONAL_COLUMNS = {
        "is_new_merchant",
        "is_new_category",
        "customer_merchant_distance_km",
        "is_fraud",
    }

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else DEFAULT_DATA_PATH

    def load_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load the processed feature dataset.

        Parameters
        ----------
        limit:
            Optional number of rows to load. Useful for testing before
            processing the complete 1.29M+ row dataset.
        """

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Graph data file not found: {self.data_path}"
            )

        if limit is not None:
            df = pd.read_parquet(
                self.data_path,
                engine="pyarrow"
            ).head(limit)
        else:
            df = pd.read_parquet(
                self.data_path,
                engine="pyarrow"
            )

        missing = self.REQUIRED_COLUMNS - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required graph columns: {sorted(missing)}"
            )

        return df

    def build_customer_transaction_edges(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Create customer/card -> transaction relationships.
        """

        edges = df[
            [
                "cc_num",
                "trans_num",
                "transaction_time",
                "amt",
            ]
        ].copy()

        edges = edges.rename(
            columns={
                "cc_num": "customer_id",
                "trans_num": "transaction_id",
            }
        )

        edges["source_type"] = "customer"
        edges["target_type"] = "transaction"
        edges["relationship"] = "made"

        return edges[
            [
                "customer_id",
                "transaction_id",
                "transaction_time",
                "amt",
                "source_type",
                "target_type",
                "relationship",
            ]
        ]

    def build_transaction_features(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Preserve graph-relevant transaction attributes.

        These attributes will later be used by graph analysis and
        investigation logic.
        """

        columns = [
            "trans_num",
            "cc_num",
            "transaction_time",
            "amt",
        ]

        for column in self.OPTIONAL_COLUMNS:
            if column in df.columns:
                columns.append(column)

        return df[columns].copy()

    def build_sample(self, limit: int = 10000) -> dict:
        """
        Build a small graph representation for initial validation.
        """

        df = self.load_data(limit=limit)

        edges = self.build_customer_transaction_edges(df)
        features = self.build_transaction_features(df)

        return {
            "rows_loaded": len(df),
            "edges": edges,
            "transaction_features": features,
        }


if __name__ == "__main__":
    builder = GraphBuilder()

    result = builder.build_sample(limit=10000)

    print("AURA Graph Builder")
    print("=" * 50)
    print(f"Rows loaded: {result['rows_loaded']}")
    print(f"Customer → transaction edges: {len(result['edges'])}")
    print(
        f"Transaction feature rows: "
        f"{len(result['transaction_features'])}"
    )

    print("\nEdge sample:")
    print(result["edges"].head().to_string(index=False))

    print("\nTransaction feature sample:")
    print(
        result["transaction_features"]
        .head()
        .to_string(index=False)
    )