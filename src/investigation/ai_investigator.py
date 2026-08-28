class AIInvestigator:
    """
    AURA AI Investigator.

    Converts the structured investigation output produced by
    InvestigationEngine into a human-readable investigation report.

    This first version is deterministic and evidence-based.
    It does not invent information that is not present in the
    investigation result.
    """

    def generate_report(self, investigation):

        if not investigation:
            return {
                "error": "No investigation data supplied."
            }

        if "error" in investigation:
            return investigation

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
        # BUILD SUMMARY
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

            feature = factor.get(
                "feature"
            )

            value = factor.get(
                "value"
            )

            shap_value = factor.get(
                "shap_value"
            )

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
        # FINAL REPORT
        # ---------------------------------------------------------

        return {
            "transaction_id": transaction_id,

            "executive_summary": summary,

            "risk_interpretation": risk_interpretation,

            "evidence": evidence,

            "top_risk_factors": shap_evidence,

            "graph_analysis": graph_summary,

            "recommended_action": recommended_action,

            "investigator_conclusion": conclusion,
        }