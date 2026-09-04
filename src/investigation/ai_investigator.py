class AIInvestigator:
    """
    AURA AI Investigator.

    Generates an evidence-based investigation report using:
    1. Deterministic investigation results
    2. Retrieved fraud knowledge from RAG
    3. Groq LLM analysis

    The LLM is instructed to use only the supplied evidence
    and retrieved knowledge and not invent transaction facts.
    """

    def generate_report(
        self,
        investigation,
        rag_context=None,
        llm=None,
    ):

        if not investigation:
            return {
                "error": "No investigation data supplied."
            }

        if "error" in investigation:
            return investigation

        # ---------------------------------------------------------
        # BASIC INVESTIGATION DATA
        # ---------------------------------------------------------

        transaction_id = investigation.get(
            "transaction_id"
        )

        amount = investigation.get(
            "amount"
        )

        fraud_probability = investigation.get(
            "fraud_probability"
        )

        risk_score = investigation.get(
            "risk_score"
        )

        risk_band = investigation.get(
            "risk_band",
            "UNKNOWN"
        )

        investigation_flag = investigation.get(
            "investigation_flag"
        )

        recommended_action = investigation.get(
            "recommended_action",
            "REVIEW"
        )

        reasons = investigation.get(
            "investigation_reasons",
            []
        )

        shap_factors = investigation.get(
            "top_risk_factors",
            []
        )

        graph_analysis = investigation.get(
            "graph_analysis",
            {}
        )

        # ---------------------------------------------------------
        # DETERMINISTIC REPORT
        # ---------------------------------------------------------

        if risk_band == "CRITICAL":

            summary = (
                f"Transaction {transaction_id} has been classified "
                f"as CRITICAL with an AURA risk score of "
                f"{risk_score}. The available evidence indicates "
                f"that this transaction requires immediate "
                f"investigation."
            )

        elif risk_band == "HIGH":

            summary = (
                f"Transaction {transaction_id} has been classified "
                f"as HIGH risk with an AURA risk score of "
                f"{risk_score}. The transaction should be "
                f"escalated for investigation."
            )

        elif risk_band == "MEDIUM":

            summary = (
                f"Transaction {transaction_id} has been classified "
                f"as MEDIUM risk with an AURA risk score of "
                f"{risk_score}. The transaction should be reviewed "
                f"through the appropriate investigation queue."
            )

        elif risk_band == "LOW":

            summary = (
                f"Transaction {transaction_id} has been classified "
                f"as LOW risk with an AURA risk score of "
                f"{risk_score}. No immediate investigation is "
                f"indicated by the current evidence."
            )

        else:

            summary = (
                f"Transaction {transaction_id} has an AURA risk "
                f"score of {risk_score}, but the risk band is "
                f"currently {risk_band}."
            )

        # ---------------------------------------------------------
        # RISK INTERPRETATION
        # ---------------------------------------------------------

        risk_interpretation = []

        if investigation_flag:

            risk_interpretation.append(
                "The AURA risk engine has flagged this transaction "
                "for investigation."
            )

        else:

            risk_interpretation.append(
                "The AURA risk engine has not flagged this "
                "transaction for investigation."
            )

        if fraud_probability is not None:

            probability_percent = (
                float(fraud_probability) * 100
            )

            risk_interpretation.append(
                f"The machine-learning fraud probability is "
                f"{probability_percent:.2f}%."
            )

        if amount is not None:

            risk_interpretation.append(
                f"The transaction amount is {amount}."
            )

        # ---------------------------------------------------------
        # EVIDENCE
        # ---------------------------------------------------------

        evidence = []

        for reason in reasons:

            evidence.append({
                "type": "investigation_reason",
                "description": str(reason),
            })

        # ---------------------------------------------------------
        # SHAP EVIDENCE
        # ---------------------------------------------------------

        shap_evidence = []

        for factor in shap_factors:

            feature = factor.get("feature")
            value = factor.get("value")
            shap_value = factor.get("shap_value")

            shap_evidence.append({
                "feature": feature,
                "value": value,
                "shap_value": shap_value,
            })

        # ---------------------------------------------------------
        # GRAPH EVIDENCE
        # ---------------------------------------------------------

        graph_summary = {
            "available": bool(graph_analysis),
            "data": graph_analysis,
        }

        # ---------------------------------------------------------
        # INVESTIGATOR CONCLUSION
        # ---------------------------------------------------------

        if risk_band == "CRITICAL":

            conclusion = (
                "Investigators should prioritize this transaction "
                "for immediate review. The conclusion is based on "
                "the AURA risk classification and the available "
                "transaction, behavioural, anomaly, explainability, "
                "and graph evidence."
            )

        elif risk_band == "HIGH":

            conclusion = (
                "Investigators should review and escalate this "
                "transaction according to the applicable fraud "
                "investigation procedure."
            )

        elif risk_band == "MEDIUM":

            conclusion = (
                "The transaction should be reviewed for additional "
                "evidence before determining whether escalation "
                "is required."
            )

        else:

            conclusion = (
                "The currently available evidence does not indicate "
                "a need for immediate investigation."
            )

        # ---------------------------------------------------------
        # BASE REPORT
        # ---------------------------------------------------------

        report = {
            "transaction_id": transaction_id,
            "executive_summary": summary,
            "risk_interpretation": risk_interpretation,
            "evidence": evidence,
            "top_risk_factors": shap_evidence,
            "graph_analysis": graph_summary,
            "recommended_action": recommended_action,
            "investigator_conclusion": conclusion,
        }

        # ---------------------------------------------------------
        # GROQ AI ANALYSIS
        # ---------------------------------------------------------

        if llm is not None:

            system_prompt = """
You are AURA, an AI fraud investigation assistant.

Your job is to analyze an already-generated fraud investigation.

IMPORTANT RULES:

1. Do not invent transaction facts.
2. Do not change the supplied risk score.
3. Do not change the supplied fraud probability.
4. Do not change the supplied risk band.
5. Treat the deterministic investigation as the primary evidence.
6. Use the retrieved knowledge only to explain fraud patterns,
   investigative context, and possible interpretation.
7. Clearly distinguish evidence from interpretation.
8. If the evidence is insufficient, say so.
9. Do not claim that a transaction is fraudulent merely because
   it has a high risk score.
10. Produce professional language suitable for a fraud analyst.
11. The overall AURA risk score and graph risk score are separate metrics.
12. NEVER describe the overall AURA risk score as the graph risk score.
13. When discussing graph analysis, use only the explicitly supplied GRAPH RISK SCORE and GRAPH RISK BAND.
14. When discussing overall transaction risk, use the AURA RISK SCORE and AURA RISK BAND.
15. If graph evidence is available, clearly distinguish graph risk from the final AURA risk assessment.

Return a concise investigation analysis containing:

- AI assessment
- Key fraud indicators
- Evidence interpretation
- Investigation considerations
- Recommended next steps
"""
        graph_data = investigation.get("graph_analysis", {})

        graph_risk_score = graph_data.get(
            "graph_risk_score"
        )

        graph_risk_band = graph_data.get(
            "graph_risk_band",
            "UNKNOWN"
        )
        user_prompt = f"""
EXPLICIT RISK METRICS
=====================
AURA RISK SCORE: {risk_score}
AURA RISK BAND: {risk_band}
GRAPH RISK SCORE: {graph_risk_score}
GRAPH RISK BAND: {graph_risk_band}
TRANSACTION INVESTIGATION
=========================

{investigation}

RETRIEVED FRAUD KNOWLEDGE
=========================

{rag_context}

DETERMINISTIC INVESTIGATION REPORT
==================================

{report}

Analyze the investigation using the supplied evidence.
"""
        try:

            ai_analysis = llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            report["ai_analysis"] = ai_analysis

        except Exception as exc:

            report["ai_analysis_error"] = str(exc)

        return report