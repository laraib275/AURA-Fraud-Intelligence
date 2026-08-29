from pathlib import Path

from src.investigation.investigation_engine import InvestigationEngine
from src.rag.retriever import TfidfRetriever
from src.rag.rag_pipeline import RAGPipeline
from src.llm.openai_client import OpenAIClient
from src.investigation.ai_investigator import AIInvestigator


class AIInvestigationPipeline:

    def __init__(self):

        project_root = Path(__file__).resolve().parents[2]

        # ---------------------------------------------------------
        # INVESTIGATION ENGINE
        # ---------------------------------------------------------

        self.investigation_engine = InvestigationEngine()

        # ---------------------------------------------------------
        # RAG
        # ---------------------------------------------------------

        retriever_path = (
            project_root
            / "data"
            / "rag"
            / "tfidf_retriever.pkl"
        )

        self.retriever = TfidfRetriever.load(
            str(retriever_path)
        )

        self.rag = RAGPipeline(
            self.retriever
        )

        # ---------------------------------------------------------
        # GROQ LLM
        # ---------------------------------------------------------

        self.llm = OpenAIClient()

        # ---------------------------------------------------------
        # AI INVESTIGATOR
        # ---------------------------------------------------------

        self.ai_investigator = AIInvestigator()

    def investigate(self, transaction_id):

        # ---------------------------------------------------------
        # STEP 1
        # Deterministic investigation
        # ---------------------------------------------------------

        investigation = (
            self.investigation_engine
            .investigate_transaction(transaction_id)
        )

        if not investigation:
            return {
                "error": "Investigation returned no result."
            }

        if "error" in investigation:
            return investigation

        # ---------------------------------------------------------
        # STEP 2
        # Retrieve relevant knowledge
        # ---------------------------------------------------------

        rag_context = self.rag.build_context(
            investigation,
            top_k=5
        )

        # ---------------------------------------------------------
        # STEP 3
        # Generate AI investigation report
        # ---------------------------------------------------------

        ai_report = self.ai_investigator.generate_report(
            investigation=investigation,
            rag_context=rag_context,
            llm=self.llm
        )

        # ---------------------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------------------

        return {
            "transaction_id": transaction_id,
            "investigation": investigation,
            "rag_context": rag_context,
            "ai_report": ai_report,
        }