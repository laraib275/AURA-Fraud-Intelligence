import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="AURA Fraud Intelligence",
    page_icon="🔍",
    layout="wide",
)


# ---------- Styling ----------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 30px;
    }

    .risk-high {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #ff4b4b;
        background: rgba(255, 75, 75, 0.12);
        text-align: center;
    }

    .risk-medium {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #ffa500;
        background: rgba(255, 165, 0, 0.12);
        text-align: center;
    }

    .risk-low {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #21c354;
        background: rgba(33, 195, 84, 0.12);
        text-align: center;
    }

    .factor {
        padding: 10px 12px;
        margin: 6px 0;
        border-radius: 6px;
        background: rgba(128, 128, 128, 0.10);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Header ----------

st.markdown(
    '<div class="main-title">AURA Fraud Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Transaction Investigation'
    '</div>',
    unsafe_allow_html=True,
)


# ---------- Search ----------

st.subheader("Investigate Transaction")

transaction_id = st.text_input(
    "Transaction ID",
    placeholder="Enter transaction ID...",
)


investigate_clicked = st.button(
    "Investigate Transaction",
    type="primary",
)


# ---------- Investigation ----------

if investigate_clicked:

    if not transaction_id.strip():
        st.warning("Please enter a transaction ID.")

    else:

        with st.spinner("Running AURA investigation..."):

            try:

                response = requests.get(
                    f"{API_URL}/investigate/"
                    f"{transaction_id.strip()}",
                    timeout=60,
                )

                if response.status_code == 404:

                    st.error("Transaction not found.")

                elif response.status_code != 200:

                    st.error(
                        f"API returned status "
                        f"{response.status_code}"
                    )

                else:

                    report = response.json()

                    st.success(
                        "Investigation completed."
                    )

                    # ---------- Risk summary ----------

                    st.divider()

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Risk Score",
                            f"{report['risk_score']:.1f}/100",
                        )

                    with col2:
                        st.metric(
                            "Model Fraud Score",
                            f"{report['fraud_probability']:.2%}",
                        )

                    with col3:
                        st.metric(
                            "Risk Band",
                            report["risk_band"],
                        )

                    # ---------- Risk status ----------

                    risk_band = report["risk_band"]

                    if risk_band == "HIGH":

                        st.markdown(
                            """
                            <div class="risk-high">
                                <h3>🔴 HIGH RISK</h3>
                                <p>Immediate investigation recommended.</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    elif risk_band == "MEDIUM":

                        st.markdown(
                            """
                            <div class="risk-medium">
                                <h3>🟠 MEDIUM RISK</h3>
                                <p>Transaction should be reviewed.</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:

                        st.markdown(
                            """
                            <div class="risk-low">
                                <h3>🟢 LOW RISK</h3>
                                <p>No immediate investigation required.</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # ---------- Recommended action ----------

                    st.divider()

                    st.subheader("Recommended Action")

                    st.info(
                        report["recommended_action"]
                    )

                    # ---------- Transaction details ----------

                    st.subheader(
                        "Transaction Details"
                    )

                    detail1, detail2, detail3 = st.columns(3)

                    with detail1:
                        st.write("**Transaction ID**")
                        st.code(
                            report["transaction_id"]
                        )

                    with detail2:
                        st.write("**Transaction Time**")
                        st.write(
                            report["transaction_time"]
                        )

                    with detail3:
                        st.write("**Amount**")
                        st.write(
                            f"{report['amount']:.2f}"
                        )

                    # ---------- Investigation reasons ----------

                    st.divider()

                    st.subheader(
                        "Why Was This Transaction Flagged?"
                    )

                    for reason in report[
                        "investigation_reasons"
                    ]:

                        st.markdown(
                            f"- {reason}"
                        )

                    # ---------- SHAP explanation ----------

                    st.subheader(
                        "Top Model Risk Factors"
                    )

                    for factor in report[
                        "top_risk_factors"
                    ]:

                        feature = factor["feature"]
                        value = factor["value"]
                        shap_value = factor["shap_value"]

                        st.markdown(
                            f"""
                            <div class="factor">
                                <b>{feature}</b><br>
                                Value: {value}<br>
                                Model contribution toward fraud:
                                {shap_value:.4f}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            except requests.exceptions.RequestException:

                st.error(
                    "Could not connect to the AURA API. "
                    "Make sure FastAPI is running."
                )