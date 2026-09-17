"""Darukaa.Earth AI Biodiversity Intelligence - Streamlit Frontend Application.

Conforms to Requirements #15 and #16:
- Environmental chat with multi-turn memory
- Structured environmental input form with presets
- Interactive location input
- Environmental metrics dashboard
- Recommendation cards (Why it works, affected metrics, impact, horizon, confidence, evidence)
- Authoritative citation inspector
"""

import streamlit as st
import httpx
import json
from typing import Dict, Any, List

# Streamlit Page Config
st.set_page_config(
    page_title="Darukaa.Earth | AI Biodiversity Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1b5e20;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .badge-high {
        background-color: #c6f6d5;
        color: #22543d;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-medium {
        background-color: #feebc8;
        color: #7b341e;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-low {
        background-color: #fed7d7;
        color: #742a2a;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .rec-card {
        border-left: 4px solid #2e7d32;
        background-color: #ffffff;
        border-top: 1px solid #e0e0e0;
        border-right: 1px solid #e0e0e0;
        border-bottom: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "accumulated_variables" not in st.session_state:
    st.session_state.accumulated_variables = {}
if "last_assessment" not in st.session_state:
    st.session_state.last_assessment = None

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/natural-food.png", width=64)
    st.title("Darukaa.Earth")
    st.caption("AI Environmental Scientist & Biodiversity Intelligence")
    st.markdown("---")

    backend_url = st.text_input("Backend API URL", value="http://localhost:8000")
    
    # Test Backend Connection
    try:
        res = httpx.get(f"{backend_url}/health", timeout=2.0)
        if res.status_code == 200:
            st.success("API Connected (Healthy)")
        else:
            st.warning("Backend degraded")
    except Exception:
        st.error("Backend Unreachable. Start backend service.")

    st.markdown("### Quick Demo Presets")
    preset = st.selectbox(
        "Load Environmental Preset",
        [
            "Select Preset...",
            "Semi-Arid Monoculture Wheat (Low SOC, Low Rain)",
            "Degraded Tropical Pasture (Acidic, Deforestation)",
            "Saline Irrigated Arid Zone (High pH, Heat Stress)",
            "Temperate Diversified Agroforestry"
        ]
    )

    st.markdown("---")
    st.markdown("### Remembered Profile State")
    if st.session_state.accumulated_variables:
        st.json(st.session_state.accumulated_variables)
    else:
        st.info("No variables accumulated yet.")

    if st.button("Clear Session & Reset Memory"):
        st.session_state.conversation_id = None
        st.session_state.chat_messages = []
        st.session_state.accumulated_variables = {}
        st.session_state.last_assessment = None
        st.rerun()

# Title Header
st.markdown('<div class="main-title">🌿 Darukaa.Earth Biodiversity Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Multi-Metric AI Environmental Scientist grounded in FAO, IPCC, UNEP, ISRIC SoilGrids, and GBIF evidence.</div>',
    unsafe_allow_html=True
)

# Tabs
tab_chat, tab_structured, tab_recs, tab_knowledge = st.tabs([
    "💬 Environmental Chat",
    "📊 Structured Input & Dashboard",
    "📜 Recommendations & Evidence",
    "🔍 Knowledge Retrieval Explorer"
])

# Preset values mapping
preset_data = {}
if preset == "Semi-Arid Monoculture Wheat (Low SOC, Low Rain)":
    preset_data = {
        "location": {"latitude": 19.07, "longitude": 73.00, "region_name": "Deccan Plateau Semi-Arid"},
        "soil": {"ph": 6.1, "organic_carbon": 0.3, "moisture": 12.0, "bulk_density": 1.48},
        "climate": {"rainfall": 540.0, "temperature": 29.0},
        "land_use": {"type": "monoculture", "crop": "wheat", "buffer_strip_width_m": 0.0},
        "biodiversity": {"species_richness": 12, "habitat_diversity_index": 0.22}
    }
elif preset == "Degraded Tropical Pasture (Acidic, Deforestation)":
    preset_data = {
        "location": {"latitude": -3.46, "longitude": -62.21, "region_name": "Amazonian Buffer Basin"},
        "soil": {"ph": 4.6, "organic_carbon": 0.8, "moisture": 26.0, "bulk_density": 1.35},
        "climate": {"rainfall": 1850.0, "temperature": 27.5},
        "land_use": {"type": "pasture", "crop": "brachiaria grass", "buffer_strip_width_m": 2.0},
        "biodiversity": {"species_richness": 18, "habitat_diversity_index": 0.30}
    }
elif preset == "Saline Irrigated Arid Zone (High pH, Heat Stress)":
    preset_data = {
        "location": {"latitude": 27.02, "longitude": 71.20, "region_name": "Thar Arid Zone"},
        "soil": {"ph": 8.5, "organic_carbon": 0.25, "moisture": 9.0, "bulk_density": 1.55},
        "climate": {"rainfall": 280.0, "temperature": 34.0},
        "land_use": {"type": "monoculture", "crop": "cotton", "buffer_strip_width_m": 0.0},
        "biodiversity": {"species_richness": 8, "habitat_diversity_index": 0.15}
    }
elif preset == "Temperate Diversified Agroforestry":
    preset_data = {
        "location": {"latitude": 45.42, "longitude": -75.69, "region_name": "St. Lawrence Agroecosystem"},
        "soil": {"ph": 6.8, "organic_carbon": 2.4, "moisture": 24.0, "bulk_density": 1.18},
        "climate": {"rainfall": 920.0, "temperature": 8.5},
        "land_use": {"type": "agroforestry", "crop": "apple orchard with clover alley", "buffer_strip_width_m": 12.0},
        "biodiversity": {"species_richness": 55, "habitat_diversity_index": 0.78}
    }

# TAB 1: ENVIRONMENTAL CHAT
with tab_chat:
    st.markdown("### Conversational Environmental Scientist")
    st.caption("Maintains multi-turn memory and performs progressive slot-filling across turns.")

    # Render previous messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if user_prompt := st.chat_input("Describe your farm, soil, climate, or ask an environmental question..."):
        # Append User Message
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Call Backend
        with st.chat_message("assistant"):
            with st.spinner("Environmental scientist is evaluating variables and literature..."):
                payload = {
                    "message": user_prompt,
                    "conversation_id": st.session_state.conversation_id
                }
                try:
                    res = httpx.post(f"{backend_url}/chat", json=payload, timeout=20.0)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.conversation_id = data["conversation_id"]
                        st.session_state.accumulated_variables = data.get("accumulated_variables", {})
                        
                        reply = data["reply"]
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

                        if data.get("assessment_response"):
                            st.session_state.last_assessment = data["assessment_response"]
                            st.success("Holistic multi-metric assessment generated! View the Dashboard & Recommendations tabs.")
                    else:
                        st.error(f"API Error: {res.text}")
                except Exception as e:
                    st.error(f"Communication error: {e}")

# TAB 2: STRUCTURED INPUT & DASHBOARD
with tab_structured:
    st.markdown("### Structured Environmental Diagnostics")
    st.caption("Input exact field measurements across Soil, Climate, Land-Use, and Biodiversity axes.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🌍 Geographic Location")
        lat = st.number_input("Latitude", value=preset_data.get("location", {}).get("latitude", 19.07), format="%.4f")
        lon = st.number_input("Longitude", value=preset_data.get("location", {}).get("longitude", 73.00), format="%.4f")
        region = st.text_input("Region Name", value=preset_data.get("location", {}).get("region_name", "Semi-Arid Basin"))

        st.markdown("#### 🌾 Land Use & Cover")
        lu_type = st.selectbox(
            "Land Use System",
            ["monoculture", "polyculture", "agroforestry", "fallow", "pasture"],
            index=0 if preset_data.get("land_use", {}).get("type", "monoculture") == "monoculture" else 2
        )
        crop = st.text_input("Primary Crop", value=preset_data.get("land_use", {}).get("crop", "wheat"))
        buffer_w = st.number_input("Buffer Strip Width (m)", value=float(preset_data.get("land_use", {}).get("buffer_strip_width_m", 0.0)), step=1.0)

    with col2:
        st.markdown("#### 🌱 Soil Health Metrics")
        ph = st.slider("Soil pH", min_value=3.5, max_value=10.0, value=float(preset_data.get("soil", {}).get("ph", 6.1)), step=0.1)
        soc = st.number_input("Soil Organic Carbon (SOC %)", value=float(preset_data.get("soil", {}).get("organic_carbon", 0.3)), min_value=0.0, max_value=20.0, step=0.05)
        moist = st.slider("Soil Moisture Content (%)", min_value=0.0, max_value=60.0, value=float(preset_data.get("soil", {}).get("moisture", 12.0)), step=1.0)
        bdod = st.number_input("Bulk Density (g/cm³)", value=float(preset_data.get("soil", {}).get("bulk_density", 1.48)), step=0.02)

    with col3:
        st.markdown("#### 🌦️ Climate & Water")
        rain = st.number_input("Annual Precipitation (mm)", value=float(preset_data.get("climate", {}).get("rainfall", 540.0)), step=10.0)
        temp = st.number_input("Mean Surface Temperature (°C)", value=float(preset_data.get("climate", {}).get("temperature", 29.0)), step=0.5)

        st.markdown("#### 🐝 Biodiversity Indicators")
        richness = st.number_input("Observed Species Richness", value=int(preset_data.get("biodiversity", {}).get("species_richness", 12)), step=1)
        hab_div = st.slider("Habitat Diversity Index (0-1)", min_value=0.0, max_value=1.0, value=float(preset_data.get("biodiversity", {}).get("habitat_diversity_index", 0.22)), step=0.02)

    if st.button("🚀 Run Multi-Metric Scientific Analysis", type="primary", use_container_width=True):
        structured_payload = {
            "location": {"latitude": lat, "longitude": lon, "region_name": region},
            "soil": {"ph": ph, "organic_carbon": soc, "moisture": moist, "bulk_density": bdod},
            "climate": {"rainfall": rain, "temperature": temp},
            "land_use": {"type": lu_type, "crop": crop, "buffer_strip_width_m": buffer_w},
            "biodiversity": {"species_richness": richness, "habitat_diversity_index": hab_div}
        }
        with st.spinner("Executing LangGraph multi-metric reasoning and evidence validation..."):
            try:
                res = httpx.post(f"{backend_url}/analyze", json=structured_payload, timeout=25.0)
                if res.status_code == 200:
                    st.session_state.last_assessment = res.json()
                    st.success("Analysis complete!")
                else:
                    st.error(f"Analysis error: {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # Render Dashboard if assessment exists
    if st.session_state.last_assessment:
        ass = st.session_state.last_assessment
        assessment_meta = ass.get("assessment", {})
        conf_meta = ass.get("confidence", {})

        st.markdown("---")
        st.subheader("📈 Multi-Metric Ecological Dashboard")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            score = assessment_meta.get("ecological_health_score", 65.0)
            color = "green" if score > 70 else ("orange" if score > 45 else "red")
            st.metric("Ecological Health Index", f"{score}/100")
        with d2:
            st.metric("Confidence Level", f"{conf_meta.get('overall_level', 'High')} ({conf_meta.get('overall_score', 0.85)*100:.0f}%)")
        with d3:
            st.metric("Data Completeness", f"{conf_meta.get('data_completeness', 0.8)*100:.0f}%")
        with d4:
            st.metric("Cross-Source Backing", f"{conf_meta.get('multi_source_agreement', 0.8)*100:.0f}%")

        st.markdown(f"**Diagnostic Summary:** {assessment_meta.get('diagnostic_summary')}")
        
        st.markdown("##### 🧬 Compound Risk Pathways (Interacting Triads):")
        for pathway in assessment_meta.get("compound_risks", []):
            st.info(f"⚡ {pathway}")

# TAB 3: RECOMMENDATIONS & EVIDENCE
with tab_recs:
    st.markdown("### Evidence-Backed Scientific Interventions")
    st.caption("Every intervention is grounded in authoritative scientific sources with traceable citations.")

    if not st.session_state.last_assessment:
        st.info("Run an analysis or chat with the assistant to generate recommendations.")
    else:
        ass = st.session_state.last_assessment
        recs = ass.get("recommendations", [])
        
        for idx, r in enumerate(recs, 1):
            conf_class = "badge-high" if r.get("confidence") == "High" else ("badge-medium" if r.get("confidence") == "Medium" else "badge-low")
            
            st.markdown(f"""
            <div class="rec-card">
                <h4>Intervention {idx}: {r.get('recommendation')}</h4>
                <p><b>🔬 Scientific Reasoning:</b> {r.get('scientific_reasoning')}</p>
                <p><b>📊 Impacted Metrics:</b> {', '.join([f'<code>{m}</code>' for m in r.get('impacted_metrics', [])])}</p>
                <p><b>🎯 Expected Impact:</b> {r.get('expected_impact')}</p>
                <p><b>⏳ Time Horizon:</b> {r.get('time_horizon')} | 
                   <b>🛡️ Confidence:</b> <span class="{conf_class}">{r.get('confidence')} ({r.get('confidence_score', 0.8)*100:.0f}%)</span></p>
            </div>
            """, unsafe_allow_html=True)

            # Evidentiary citations accordion
            with st.expander(f"📚 Authoritative Evidence & Citations for Intervention {idx}"):
                for cit in r.get("evidence", []):
                    st.markdown(f"**{cit.get('source_name')}** ({cit.get('organization')}, {cit.get('year')})")
                    st.markdown(f"- *Section/Page:* {cit.get('page')} | *Topic:* {cit.get('topic')}")
                    if cit.get('url'):
                        st.markdown(f"- *Reference Link:* [{cit.get('url')}]({cit.get('url')})")
                    if cit.get('quoted_text'):
                        st.caption(f'"{cit.get("quoted_text")}"')
                    st.markdown("---")

# TAB 4: KNOWLEDGE BASE SEARCH
with tab_knowledge:
    st.markdown("### Scientific Knowledge Base Explorer (Hybrid RAG)")
    st.caption("Search across ingested FAO, IPCC, UNEP, ISRIC SoilGrids, and GBIF documents using dense semantic + sparse BM25 retrieval.")

    search_q = st.text_input("Enter ecological query", value="soil organic carbon water retention microbial biomass semi-arid")
    col_k1, col_k2 = st.columns([1, 4])
    with col_k1:
        top_k = st.slider("Top K", min_value=1, max_value=10, value=4)

    if st.button("Search Scientific Corpus"):
        with st.spinner("Executing hybrid RAG retrieval..."):
            try:
                res = httpx.get(f"{backend_url}/knowledge/search", params={"query": search_q, "top_k": top_k}, timeout=10.0)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Retrieved {data['total_results']} authoritative chunks with citations.")
                    for item in data.get("results", []):
                        with st.container():
                            cit = item.get("citation", {})
                            st.markdown(f"#### 📖 {item.get('title')} (Score: {item.get('score')})")
                            st.markdown(f"**Organization:** {item.get('organization')} | **Year:** {item.get('year')} | **Section:** {item.get('page')}")
                            st.markdown(f"```markdown\n{item.get('content')}\n```")
                            if cit.get("url"):
                                st.markdown(f"[Official Source Link]({cit.get('url')})")
                            st.markdown("---")
                else:
                    st.error(f"Search failed: {res.text}")
            except Exception as e:
                st.error(f"Search request failed: {e}")
