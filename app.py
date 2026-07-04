import streamlit as st
import asyncio
import os
import time
from gtts import gTTS
import pandas as pd
import altair as alt
from PIL import Image

# Import backend modules
from config import settings
from logger import logger
from memory import MemoryService
from orchestrator import AgriculturalOrchestrator
from tools.mcp_clients import MCPClient

# Initialize Orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgriculturalOrchestrator()
    
# Initialize Session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{int(time.time())}"

st.set_page_config(
    page_title="AI Farmer Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Stylesheet
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------------- SIDEBAR PROFILE SECTION -----------------
st.sidebar.markdown("<h2 class='gradient-text'>🌱 Farm Profile</h2>", unsafe_allow_html=True)

# Fetch latest profile or use defaults
profile = MemoryService.get_farmer_profile()

with st.sidebar.form("profile_form"):
    st.markdown("### Profile Details")
    name = st.text_input("Farmer Name", value=profile.get("name", "Arjun Patel"))
    region = st.text_input("Region", value=profile.get("region", "Maharashtra, India"))
    
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitude", value=profile.get("latitude", 19.076), format="%.4f")
    lon = col2.number_input("Longitude", value=profile.get("longitude", 72.877), format="%.4f")
    
    farm_size = st.number_input("Farm Size (Acres)", value=profile.get("farm_size_acres", 5.0), step=0.1)
    crops = st.text_input("Primary Crops (comma separated)", value=", ".join(profile.get("primary_crops", ["Cotton"])))
    
    st.markdown("### Soil Quality (N-P-K)")
    soil_ph = st.slider("Soil pH", min_value=4.0, max_value=9.0, value=profile.get("soil_ph", 6.5), step=0.1)
    soil_n = st.number_input("Nitrogen (mg/kg)", value=profile.get("soil_nitrogen", 45.0), step=1.0)
    soil_p = st.number_input("Phosphorus (mg/kg)", value=profile.get("soil_phosphorus", 18.0), step=1.0)
    soil_k = st.number_input("Potassium (mg/kg)", value=profile.get("soil_potassium", 120.0), step=1.0)
    soil_moisture = st.slider("Soil Moisture (%)", min_value=0, max_value=100, value=int(profile.get("soil_moisture", 30)))
    
    save_profile = st.form_submit_button("Save & Update Profile")
    if save_profile:
        updated_profile = {
            "name": name,
            "region": region,
            "latitude": lat,
            "longitude": lon,
            "farm_size_acres": farm_size,
            "soil_ph": soil_ph,
            "soil_nitrogen": soil_n,
            "soil_phosphorus": soil_p,
            "soil_potassium": soil_k,
            "soil_moisture": soil_moisture,
            "primary_crops": [c.strip() for c in crops.split(",") if c.strip()]
        }
        pid = MemoryService.save_farmer_profile(updated_profile)
        st.sidebar.success(f"Profile updated successfully!")
        st.rerun()

# ----------------- APP HEADER -----------------
st.markdown("<h1 style='text-align: center;' class='gradient-text'>AI Farmer Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8;'>Collaborative Multi-Agent Agricultural Advisory Platform</p>", unsafe_allow_html=True)

# Tabs
tab_dash, tab_chat, tab_vision, tab_map, tab_finance, tab_schemes = st.tabs([
    "📊 Dashboard Overview",
    "💬 Advisory Hub",
    "🔬 Disease Diagnostic Lab",
    "📍 Nearby Resources",
    "📈 ROI Planner",
    "📜 Government Schemes"
])

# ----------------- TAB 1: DASHBOARD OVERVIEW -----------------
with tab_dash:
    st.markdown("<div class='glass-card'><h3>🌾 Soil & Climate Summary</h3></div>", unsafe_allow_html=True)
    
    # Soil metrics layout
    col_n, col_p, col_k, col_ph, col_moist = st.columns(5)
    col_n.metric("Nitrogen (N)", f"{profile.get('soil_nitrogen')} mg/kg", delta="Optimal: 50" if profile.get('soil_nitrogen') >= 45 else "- Low")
    col_p.metric("Phosphorus (P)", f"{profile.get('soil_phosphorus')} mg/kg", delta="Optimal: 20" if profile.get('soil_phosphorus') >= 18 else "- Low")
    col_k.metric("Potassium (K)", f"{profile.get('soil_potassium')} mg/kg", delta="Optimal: 120" if profile.get('soil_potassium') >= 120 else "- Low")
    col_ph.metric("Soil pH", f"{profile.get('soil_ph')}", delta="Neutral" if 6.0 <= profile.get('soil_ph') <= 7.5 else "Acidic/Alkaline")
    col_moist.metric("Soil Moisture", f"{profile.get('soil_moisture')}%", delta="Critical: < 20%")
    
    st.markdown("---")
    
    # Fetch forecast data via MCP
    weather_data = MCPClient.get_weather_data(profile.get("latitude"), profile.get("longitude"))
    
    col_weather, col_market = st.columns(2)
    
    with col_weather:
        st.markdown("<div class='glass-card'><h3>🌤️ 7-Day Weather Outlook</h3></div>", unsafe_allow_html=True)
        curr = weather_data.get("current", {})
        st.write(f"**Current Temperature:** {curr.get('temp')}°C | **Humidity:** {curr.get('humidity')}% | **Condition:** {curr.get('weather', [{}])[0].get('description')}")
        
        # Weather table
        forecast_list = []
        for i, day in enumerate(weather_data.get("daily", [])):
            forecast_list.append({
                "Day": f"Day {i+1}",
                "Temp Max (°C)": day.get("temp", {}).get("max"),
                "Temp Min (°C)": day.get("temp", {}).get("min"),
                "Humidity (%)": day.get("humidity"),
                "Rain Prob (%)": int(day.get("pop", 0) * 100)
            })
        st.dataframe(pd.DataFrame(forecast_list), use_container_width=True)
        
    with col_market:
        st.markdown("<div class='glass-card'><h3>📊 Market Commodity Prices</h3></div>", unsafe_allow_html=True)
        # Fetch crop pricing
        primary_crop = profile.get("primary_crops", ["Wheat"])[0]
        market_data = MCPClient.get_market_prices(primary_crop, profile.get("region"))
        pricing = market_data.get("pricing", {})
        
        st.write(f"**Crop:** {market_data.get('crop')} | **Region:** {market_data.get('region')}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Current Mandi Rate", f"₹{pricing.get('current')} / {market_data.get('unit')}")
        col_m2.metric("Weekly Trend", pricing.get("trend").upper())
        col_m3.metric("Last Week Avg", f"₹{pricing.get('last_week')} / {market_data.get('unit')}")
        
        # Simple line chart comparing prices
        trend_df = pd.DataFrame({
            "Time": ["Last Week", "Current"],
            "Price (INR)": [pricing.get("last_week"), pricing.get("current")]
        })
        chart = alt.Chart(trend_df).encode(
            x='Time',
            y=alt.Y('Price (INR)', scale=alt.Scale(domain=[pricing.get("min") - 100, pricing.get("max") + 100])),
            color=alt.value("#10B981")
        ).properties(height=180)
        st.altair_chart(chart.mark_line(point=True) + chart.mark_area(opacity=0.1), use_container_width=True)

# ----------------- TAB 2: ADVISORY CHAT -----------------
with tab_chat:
    st.markdown("<div class='glass-card'><h3>💬 Consult the Multi-Agent Expert Panel</h3></div>", unsafe_allow_html=True)
    
    # Display message history
    history = MemoryService.get_conversation_history(st.session_state.session_id)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    query = st.chat_input("Ask about seed planning, watering rates, pest sprays, or selling timelines...")
    if query:
        with st.chat_message("user"):
            st.write(query)
            
        with st.chat_message("assistant"):
            progress_status = st.empty()
            
            # Simulated Orchestrator steps
            progress_status.info("Orchestrator: Decomposing query and planning execution graph...")
            time.sleep(1.0)
            progress_status.info("Memory Manager: Pulling historical farmer profile and soil context...")
            time.sleep(1.0)
            progress_status.info("Executing specialized sub-agents in parallel (Crop Planning, Weather, Fertilizer)...")
            
            # Execute pipeline
            result = asyncio.run(st.session_state.orchestrator.execute_plan(
                session_id=st.session_state.session_id,
                farmer_id=profile.get("id", 1),
                query=query
            ))
            
            progress_status.empty()
            
            # Render response
            advisory = result.get("final_advisory")
            st.markdown(advisory)
            
            # Audio Text to Speech player
            try:
                tts = gTTS(text=advisory, lang='en', slow=False)
                tts.save("response.mp3")
                st.audio("response.mp3", format="audio/mp3")
            except Exception as e:
                logger.error(f"TTS compilation failed: {e}")
                
            # Check if PDF compiled and provide download button
            pdf_path = result.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Advisory PDF",
                        data=pdf_file,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )
                    
            # Explainability Expander Trace
            with st.expander("🔍 Trace & Agent Consultation Log (Explainability)"):
                trace = result.get("execution_trace", {})
                st.markdown(f"**Agents Activated:** {', '.join(trace.get('agents_called', []))}")
                
                for agent_name, details in trace.get("agent_details", {}).items():
                    st.markdown(f"<div class='consultation-step'><span class='consultation-step-title'>{agent_name.upper()}</span> (Confidence: {details.get('confidence', 0.0)})</div>", unsafe_allow_html=True)
                    st.write(details.get("content"))
                    st.write(f"*Reasoning:* {', '.join(details.get('reasoning', []))}")
                    st.write(f"*Sources:* {', '.join(details.get('sources', []))}")
                    st.markdown("---")

# ----------------- TAB 3: DISEASE DIAGNOSTIC LAB -----------------
with tab_vision:
    st.markdown("<div class='glass-card'><h3>🔬 Leaf Diagnostic Camera (Gemini Vision)</h3></div>", unsafe_allow_html=True)
    st.write("Upload a clear photo of an infected leaf or plant part for visual disease diagnostics and treatment protocols.")
    
    uploaded_file = st.file_uploader("Upload Leaf Photo", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Leaf Image", width=300)
        
        # Save temp image path
        scratch_dir = "scratch"
        if not os.path.exists(scratch_dir):
            os.makedirs(scratch_dir)
            
        temp_img_path = os.path.join(scratch_dir, f"temp_upload_{int(time.time())}.jpg")
        img.convert("RGB").save(temp_img_path)
        
        analyze_btn = st.button("Run Visual Diagnostics Scan")
        if analyze_btn:
            with st.spinner("Analyzing image features using Gemini Vision..."):
                response = asyncio.run(st.session_state.orchestrator.execute_plan(
                    session_id=st.session_state.session_id,
                    farmer_id=profile.get("id", 1),
                    query="Inspect this leaf image for diseases and pest marks.",
                    image_path=temp_img_path
                ))
                
                advisory = response.get("final_advisory")
                st.markdown(advisory)
                
                # Confidence indicator
                trace = response.get("execution_trace", {})
                disease_details = trace.get("agent_details", {}).get("disease", {})
                confidence = disease_details.get("confidence", 0.8)
                st.metric("Diagnostic Confidence Score", f"{int(confidence*100)}%")

# ----------------- TAB 4: NEARBY RESOURCES MAPS -----------------
with tab_map:
    st.markdown("<div class='glass-card'><h3>📍 Nearby Infrastructure & Supplies Tracker</h3></div>", unsafe_allow_html=True)
    
    res_type = st.selectbox(
        "Select Resource Category to Locate",
        ["seed store", "cold storage", "mandi", "equipment rent", "lab"]
    )
    
    if st.button("Locate Resources"):
        with st.spinner(f"Locating local {res_type} units around farm coordinates..."):
            places = MCPClient.search_nearby_resources(profile.get("latitude"), profile.get("longitude"), res_type)
            
            if places:
                # Display Map
                map_data = pd.DataFrame([{
                    "latitude": p["latitude"],
                    "longitude": p["longitude"],
                    "name": p["name"]
                } for p in places])
                # Include farmer farm coordinate
                map_data.loc[len(map_data)] = [profile.get("latitude"), profile.get("longitude"), "My Farm"]
                
                st.map(map_data, use_container_width=True)
                
                # List details
                st.markdown("### Search Results")
                for p in places:
                    st.write(f"🔹 **{p['name']}** | Distance: **{p['distance_km']} km** | Rating: ⭐ {p['rating']} | Phone: {p['phone']}")
            else:
                st.info("No nearby facilities found matching this category.")

# ----------------- TAB 5: FINANCIAL ROI PLANNER -----------------
with tab_finance:
    st.markdown("<div class='glass-card'><h3>📊 Farm Budget & Profitability Forecaster</h3></div>", unsafe_allow_html=True)
    
    crop_name = st.selectbox("Select Crop", profile.get("primary_crops", ["Cotton"]))
    yield_val = st.number_input("Expected Yield per Acre (Quintals)", value=14.5, step=0.5)
    
    # Pre-populate estimated mandi price
    mkt = MCPClient.get_market_prices(crop_name, profile.get("region"))
    current_price = mkt.get("pricing", {}).get("current", 2500)
    
    price_val = st.number_input("Mandi Sale Price (INR per Quintal)", value=float(current_price))
    
    if st.button("Generate ROI Projection Chart"):
        acres = profile.get("farm_size_acres", 5.0)
        total_yield = yield_val * acres
        gross_revenue = total_yield * price_val
        
        # Estimate Cultivation Costs per acre (seeds, fertilizers, labor, rentals)
        seed_cost = 1500 * acres
        fertilizer_cost = 3500 * acres
        labor_cost = 4500 * acres
        machinery_cost = 2500 * acres
        total_cost = seed_cost + fertilizer_cost + labor_cost + machinery_cost
        
        net_profit = gross_revenue - total_cost
        roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0
        
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Estimated Cultivation Cost", f"₹{int(total_cost):,}")
        col_f2.metric("Expected Net Profit", f"₹{int(net_profit):,}", delta=f"ROI: {roi:.1f}%")
        col_f3.metric("Expected Yield (Total)", f"{total_yield:.1f} Quintals")
        
        # Plot costs vs revenue
        fin_df = pd.DataFrame({
            "Category": ["Seeds Cost", "Fertilizer Cost", "Labor Cost", "Equipment Rent", "Net Profit"],
            "Amount (INR)": [seed_cost, fertilizer_cost, labor_cost, machinery_cost, net_profit]
        })
        
        chart = alt.Chart(fin_df).mark_bar().encode(
            x=alt.X('Category', sort=None),
            y='Amount (INR)',
            color=alt.condition(
                alt.datum.Category == 'Net Profit',
                alt.value('#10B981'), # Green for profit
                alt.value('#EF4444')  # Red for costs
            )
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

# ----------------- TAB 6: GOVERNMENT SCHEMES -----------------
with tab_schemes:
    st.markdown("<div class='glass-card'><h3>📜 National & State Farmer Assistance Schemes</h3></div>", unsafe_allow_html=True)
    st.write("Browse active subsidies, soil card initiatives, crop insurance programs, and support campaigns.")
    
    schemes_data = MCPClient.search_web("List major agricultural schemes, crop insurance policies, and fertilizer subsidies in India")
    st.markdown(schemes_data)
