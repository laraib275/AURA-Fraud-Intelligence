import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AURA · Fraud Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: "Inter", sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 82% 6%, rgba(135,75,255,.22), transparent 25%),
        radial-gradient(circle at 16% 56%, rgba(240,70,165,.09), transparent 25%),
        #080A1A;
    color: #F7F7FF;
}

.block-container { max-width: 1500px; padding: 1.1rem 1.35rem 3rem; }
[data-testid="stHeader"] { background: transparent; }

.rail {
    min-height: 820px; position: relative; padding: 1rem .65rem;
    border-radius: 24px;
    background: linear-gradient(180deg, rgba(22,24,55,.96), rgba(8,10,28,.88));
    border: 1px solid rgba(255,255,255,.07);
    box-shadow: 0 18px 45px rgba(0,0,0,.25);
}
.brand { display:flex; align-items:center; gap:.55rem; color:#fff; font-size:1.05rem; font-weight:800; letter-spacing:.08em; padding:.3rem .45rem 1.5rem; }
.brand-orb { width:15px; height:15px; border-radius:50%; background:radial-gradient(circle at 35% 30%,#fff,#b76cff 42%,#7448ff 78%); box-shadow:0 0 12px #a46dff,0 0 28px rgba(157,101,255,.7); animation:pulse 2.8s ease-in-out infinite; }
@keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.16)} }
.nav { color:#A9AEC7; padding:.78rem .72rem; margin:.3rem 0; border-radius:13px; font-size:.8rem; font-weight:600; }
.nav.active { color:#fff; background:linear-gradient(135deg,rgba(137,82,255,.32),rgba(229,83,175,.14)); border:1px solid rgba(168,126,255,.24); }
.help { position:absolute; left:.75rem; bottom:1rem; color:#777D98; font-size:.7rem; }

.topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; }
.eyebrow { color:#C08BFF; font-size:.68rem; text-transform:uppercase; letter-spacing:.18em; font-weight:800; }
.status { color:#76EDBE; background:rgba(62,219,165,.08); border:1px solid rgba(62,219,165,.22); border-radius:999px; padding:.38rem .72rem; font-size:.7rem; font-weight:700; }
.hero { font-size:3.5rem; line-height:1; letter-spacing:-.055em; font-weight:850; margin-top:.5rem; color:#fff; }
.hero-accent { background:linear-gradient(90deg,#F4F1FF,#B889FF,#F45B99); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.copy { color:#A6ABC3; max-width:650px; font-size:.93rem; line-height:1.65; margin-top:.95rem; }

.scene { position:relative; min-height:300px; overflow:hidden; border-radius:28px; background:radial-gradient(circle at 50% 42%,rgba(137,74,255,.14),transparent 38%),linear-gradient(145deg,rgba(28,30,70,.48),rgba(7,9,24,.08)); }
.orb-wrap { position:absolute; width:240px; height:240px; left:52%; top:48%; transform:translate(-50%,-50%); animation:float 5.5s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translate(-50%,-50%) translateY(0)} 50%{transform:translate(-50%,-50%) translateY(-10px)} }
.orb { position:absolute; inset:30px; border-radius:50%; background:radial-gradient(circle at 29% 24%,rgba(255,255,255,.96),rgba(214,184,255,.65) 8%,rgba(123,60,255,.85) 40%,rgba(42,16,93,.98) 80%); box-shadow:inset -20px -26px 35px rgba(3,3,17,.5),0 0 55px rgba(129,77,255,.7),0 0 125px rgba(224,70,171,.22); overflow:hidden; }
.orb:after { content:""; position:absolute; inset:-20%; background:radial-gradient(circle at 25% 30%,rgba(255,255,255,.16) 0 1.5px,transparent 1.7px),radial-gradient(circle at 70% 60%,rgba(255,255,255,.15) 0 1.2px,transparent 1.4px); background-size:44px 44px,34px 34px; animation:stars 11s linear infinite; }
@keyframes stars { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.ring { position:absolute; border:1.5px solid rgba(211,160,255,.7); border-radius:50%; }
.r1 { inset:14px 0; transform:rotate(-18deg) rotateX(68deg); animation:spin1 9s linear infinite; }
.r2 { inset:6px 20px; border-color:rgba(255,87,175,.7); transform:rotate(26deg) rotateY(67deg); animation:spin2 7s linear infinite reverse; }
@keyframes spin1 { from{transform:rotate(-18deg) rotateX(68deg) rotate(0deg)} to{transform:rotate(-18deg) rotateX(68deg) rotate(360deg)} }
@keyframes spin2 { from{transform:rotate(26deg) rotateY(67deg) rotate(0deg)} to{transform:rotate(26deg) rotateY(67deg) rotate(-360deg)} }
.planet { position:absolute; width:17px; height:17px; border-radius:50%; background:radial-gradient(circle at 35% 30%,#fff,#f16daa 38%,#7444ff 82%); box-shadow:0 0 20px rgba(240,102,180,.72); }
.p1{top:24px;right:38px;animation:drift1 6s ease-in-out infinite}.p2{bottom:36px;left:36px;width:12px;height:12px;animation:drift2 7s ease-in-out infinite}.p3{top:70px;left:18px;width:9px;height:9px;animation:drift3 8s ease-in-out infinite}
@keyframes drift1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(18px,-10px)} }
@keyframes drift2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-11px,8px)} }
@keyframes drift3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(10px,-16px)} }
.gridwave { position:absolute; width:125%; height:160px; left:-12%; bottom:-36px; background:repeating-linear-gradient(90deg,rgba(161,106,255,0) 0 38px,rgba(161,106,255,.18) 39px 40px),repeating-linear-gradient(180deg,rgba(161,106,255,0) 0 20px,rgba(161,106,255,.16) 21px 22px); transform:perspective(420px) rotateX(62deg); mask-image:linear-gradient(to top,black,transparent); opacity:.5; animation:gridmove 9s linear infinite; }
@keyframes gridmove { from{transform:perspective(420px) rotateX(62deg) translateY(0)} to{transform:perspective(420px) rotateX(62deg) translateY(22px)} }

.search-card,.metric,.detail,.reason,.factor { background:linear-gradient(145deg,rgba(27,30,68,.92),rgba(16,18,40,.78)); border:1px solid rgba(255,255,255,.07); box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 16px 34px rgba(0,0,0,.18); backdrop-filter:blur(18px); }
.search-card { padding:1rem 1.05rem; border-radius:18px; margin-top:1.2rem; }
div[data-testid="stTextInput"] label { color:#B9BED2 !important; font-size:.72rem !important; font-weight:700 !important; }
div[data-testid="stTextInput"] input { background:rgba(8,10,25,.72) !important; color:#F8F9FF !important; border:1px solid rgba(154,124,255,.23) !important; border-radius:11px !important; }
div[data-testid="stTextInput"] input:focus { border-color:rgba(194,132,255,.72) !important; box-shadow:0 0 0 3px rgba(145,92,255,.12) !important; }
.stButton > button { background:linear-gradient(135deg,#FF5D9B,#875DFF); color:#fff; border:0; border-radius:11px; font-weight:800; box-shadow:0 10px 26px rgba(155,83,255,.3); }
.stButton > button:hover { color:#fff; transform:translateY(-1px); }

.metric { min-height:145px; padding:1.05rem; border-radius:18px; position:relative; overflow:hidden; }
.label { color:#8D92AD; font-size:.67rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800; }
.value { color:#F8F8FF; font-size:2.3rem; line-height:1; font-weight:850; letter-spacing:-.04em; margin-top:.72rem; }
.note { color:#8B90AB; font-size:.75rem; margin-top:.4rem; }
.iconbox { position:absolute; right:15px; bottom:14px; width:54px; height:54px; display:grid; place-items:center; border-radius:16px; background:radial-gradient(circle at 30% 25%,rgba(255,255,255,.2),rgba(129,82,255,.18) 48%,rgba(255,92,151,.1)); border:1px solid rgba(255,255,255,.08); font-size:1.3rem; }

.risk { margin-top:1rem; padding:1rem 1.08rem; border-radius:17px; background:rgba(26,29,62,.78); border:1px solid rgba(255,255,255,.08); }
.risk.high { border-color:rgba(245,90,135,.24); background:linear-gradient(100deg,rgba(255,76,135,.1),rgba(26,29,62,.78)); }
.risk.medium { border-color:rgba(242,166,89,.24); background:linear-gradient(100deg,rgba(242,166,89,.08),rgba(26,29,62,.78)); }
.risk.low { border-color:rgba(57,212,165,.22); background:linear-gradient(100deg,rgba(57,212,165,.07),rgba(26,29,62,.78)); }
.kicker { color:#8B90AB; font-size:.66rem; text-transform:uppercase; letter-spacing:.12em; font-weight:800; }
.risk-title { color:#F9F9FF; font-size:1.25rem; font-weight:850; margin-top:.25rem; }
.risk-copy { color:#A4A8BF; font-size:.8rem; margin-top:.18rem; }
.action { margin-top:.85rem; padding:.9rem 1rem; border-radius:15px; background:linear-gradient(100deg,rgba(255,78,135,.11),rgba(119,81,255,.10)); border:1px solid rgba(208,126,255,.18); }
.action-label { color:#C28AFF; font-size:.65rem; text-transform:uppercase; letter-spacing:.12em; font-weight:800; }
.action-value { color:#F7F5FF; font-size:1rem; font-weight:800; margin-top:.22rem; }
.section-title { color:#F3F4FC; font-size:1rem; font-weight:800; margin:1.65rem 0 .7rem; }
.section-sub { color:#848AA4; font-size:.74rem; margin-top:-.36rem; margin-bottom:.82rem; }
.detail { min-height:105px; padding:.9rem; border-radius:15px; }
.detail-label { color:#858BA4; font-size:.65rem; text-transform:uppercase; letter-spacing:.10em; font-weight:800; }
.detail-value { color:#F5F5FC; font-size:.86rem; font-weight:650; margin-top:.46rem; word-break:break-word; }
.reason { display:flex; gap:.65rem; padding:.78rem .85rem; margin-bottom:.55rem; border-radius:14px; color:#C5C8DA; font-size:.79rem; }
.reason-dot { width:7px; height:7px; flex:0 0 7px; margin-top:.36rem; border-radius:50%; background:#F35F9E; box-shadow:0 0 11px rgba(243,95,158,.72); }
.factor { padding:.78rem .85rem; margin-bottom:.55rem; border-radius:14px; }
.factor-head { display:flex; justify-content:space-between; gap:.7rem; align-items:center; }
.factor-name { color:#F1F1F9; font-size:.82rem; font-weight:750; }
.factor-score { color:#D19BFF; font-size:.74rem; font-weight:800; }
.factor-meta { color:#858BA5; font-size:.71rem; margin-top:.26rem; }
.bar-bg { height:6px; margin-top:.48rem; border-radius:999px; background:rgba(255,255,255,.055); overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#FF5E92,#895EFF); box-shadow:0 0 14px rgba(154,93,255,.32); }
.footer { margin-top:2.5rem; padding-top:1rem; border-top:1px solid rgba(255,255,255,.07); color:#717792; font-size:.68rem; }
</style>
""", unsafe_allow_html=True)

rail, main = st.columns([0.16, 0.84], gap="large")

with rail:
    st.markdown(
        """
        <div class="rail">
            <div class="brand"><span class="brand-orb"></span>AURA.</div>
            <div class="nav active">⌂ &nbsp;&nbsp; Overview</div>
            <div class="nav">⌕ &nbsp;&nbsp; Investigation</div>
            <div class="nav">▤ &nbsp;&nbsp; Cases</div>
            <div class="nav">◌ &nbsp;&nbsp; Analytics</div>
            <div class="nav">⚙ &nbsp;&nbsp; Settings</div>
            <div class="help">? &nbsp; Help</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with main:
    st.markdown(
        """
        <div class="topbar">
            <div class="eyebrow">Fraud Intelligence Platform</div>
            <div class="status">● &nbsp;Live System</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_left, hero_right = st.columns([0.58, 0.42], gap="large")

    with hero_left:
        st.markdown(
            """
            <div class="hero">
                See the risk.<br>
                <span class="hero-accent">Understand the why.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="copy">
                Investigate suspicious transactions using machine learning,
                explainability, and structured investigation logic.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        transaction_id = st.text_input(
            "Investigate a transaction",
            placeholder="Paste transaction ID...",
        )
        investigate_clicked = st.button("Investigate  →", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with hero_right:
        st.markdown(
            """
            <div class="scene">
                <div class="orb-wrap">
                    <div class="ring r1"></div>
                    <div class="ring r2"></div>
                    <div class="orb"></div>
                    <div class="planet p1"></div>
                    <div class="planet p2"></div>
                    <div class="planet p3"></div>
                </div>
                <div class="gridwave"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if investigate_clicked:
        if not transaction_id.strip():
            st.warning("Please enter a transaction ID before starting the investigation.")
        else:
            with st.spinner("AURA is analysing the transaction..."):
                try:
                    response = requests.get(
                        f"{API_URL}/investigate/{transaction_id.strip()}",
                        timeout=60,
                    )

                    if response.status_code == 404:
                        st.error("Transaction not found.")
                    elif response.status_code != 200:
                        st.error(f"API returned status {response.status_code}")
                    else:
                        report = response.json()
                        st.success("Investigation completed successfully.")

                        c1, c2, c3 = st.columns(3)

                        with c1:
                            st.markdown(
                                f"""
                                <div class="metric">
                                    <div class="label">Risk Score</div>
                                    <div class="value">{report['risk_score']:.0f}<span style="font-size:1rem;color:#858BA4"> /100</span></div>
                                    <div class="note">Maximum risk detected</div>
                                    <div class="iconbox">🛡</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        with c2:
                            st.markdown(
                                f"""
                                <div class="metric">
                                    <div class="label">Model Fraud Score</div>
                                    <div class="value" style="background:linear-gradient(90deg,#B88CFF,#8C6DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{report['fraud_probability']:.0%}</div>
                                    <div class="note">Model output</div>
                                    <div class="iconbox">🧠</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        with c3:
                            st.markdown(
                                f"""
                                <div class="metric">
                                    <div class="label">Risk Band</div>
                                    <div class="value" style="color:#FF6D98">{report['risk_band']}</div>
                                    <div class="note">Current assessment</div>
                                    <div class="iconbox">◒</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        risk_band = report["risk_band"]
                        if risk_band == "HIGH":
                            risk_class = "high"
                            risk_description = "Immediate analyst attention is recommended."
                        elif risk_band == "MEDIUM":
                            risk_class = "medium"
                            risk_description = "This transaction should be reviewed."
                        else:
                            risk_class = "low"
                            risk_description = "No immediate investigation is required."

                        st.markdown(
                            f"""
                            <div class="risk {risk_class}">
                                <div class="kicker">AURA Assessment</div>
                                <div class="risk-title">{risk_band} RISK</div>
                                <div class="risk-copy">{risk_description}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div class="action">
                                <div class="action-label">Recommended Action</div>
                                <div class="action-value">{report['recommended_action']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown('<div class="section-title">Transaction details</div>', unsafe_allow_html=True)
                        d1, d2, d3 = st.columns(3)

                        with d1:
                            st.markdown(
                                f"""<div class="detail"><div class="detail-label">Transaction ID</div><div class="detail-value">{report['transaction_id']}</div></div>""",
                                unsafe_allow_html=True,
                            )
                        with d2:
                            st.markdown(
                                f"""<div class="detail"><div class="detail-label">Transaction Time</div><div class="detail-value">{report['transaction_time']}</div></div>""",
                                unsafe_allow_html=True,
                            )
                        with d3:
                            st.markdown(
                                f"""<div class="detail"><div class="detail-label">Amount</div><div class="detail-value" style="color:#78E8B8">{report['amount']:.2f}</div></div>""",
                                unsafe_allow_html=True,
                            )

                        left, right = st.columns([0.95, 1.05], gap="large")

                        with left:
                            st.markdown(
                                '<div class="section-title">Why was this transaction flagged?</div><div class="section-sub">Investigation signals</div>',
                                unsafe_allow_html=True,
                            )
                            for reason in report.get("investigation_reasons", []):
                                st.markdown(
                                    f"""<div class="reason"><span class="reason-dot"></span><span>{reason}</span></div>""",
                                    unsafe_allow_html=True,
                                )

                        with right:
                            st.markdown(
                                '<div class="section-title">Model explanation</div><div class="section-sub">Top factors contributing to the prediction</div>',
                                unsafe_allow_html=True,
                            )

                            factors = report.get("top_risk_factors", [])
                            max_abs_shap = max((abs(float(f["shap_value"])) for f in factors), default=1.0)

                            for factor in factors:
                                feature = factor["feature"]
                                value = factor["value"]
                                shap_value = float(factor["shap_value"])
                                width = min(100, max(5, int(abs(shap_value) / max_abs_shap * 100)))

                                st.markdown(
                                    f"""
                                    <div class="factor">
                                        <div class="factor-head">
                                            <div class="factor-name">{feature}</div>
                                            <div class="factor-score">+{shap_value:.4f}</div>
                                        </div>
                                        <div class="factor-meta">Observed value: {value}</div>
                                        <div class="bar-bg"><div class="bar-fill" style="width:{width}%"></div></div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                except requests.exceptions.RequestException:
                    st.error("Could not connect to the AURA API. Make sure FastAPI is running.")

    st.markdown(
        """
        <div class="footer">
            AURA Fraud Intelligence · Machine Learning · Explainable AI · Transaction Investigation
        </div>
        """,
        unsafe_allow_html=True,
    )