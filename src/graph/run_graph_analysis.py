from pathlib import Path

from src.graph.graph_analyzer import GraphAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sparkov_graph_analysis.parquet"
)


def main():
    print("Running AURA graph analysis...")

    analyzer = GraphAnalyzer()

    result = analyzer.analyze()

    transactions = result["transaction_graph_analysis"]

    transactions.to_parquet(
        OUTPUT_PATH,
        engine="pyarrow",
        index=False,
    )

    print("=" * 60)
    print("AURA Graph Analysis Complete")
    print("=" * 60)

    print(
        f"Transactions analyzed: "
        f"{result['rows_analyzed']}"
    )

    print(
        f"Customers analyzed: "
        f"{result['customers_analyzed']}"
    )

    print(
        f"Output saved to:\n"
        f"{OUTPUT_PATH}"
    )

    print("\nGraph risk distribution:")

    print(
        transactions["graph_risk_band"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()