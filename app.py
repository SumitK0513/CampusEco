"""
CampusEco - Unified Sustainability Operating System
Energy | Water Leaks & Live Dispatch | Waste & Biogas Circularity
Run: python3 -m streamlit run app.py
"""
import requests
import pandas as pd
import streamlit as st

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="CampusEco | Unified Campus Sustainability OS",
    page_icon="🌱",
    layout="wide"
)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/natural-food.png", width=64)
    st.title("CampusEco OS")
    st.caption("Multi-Utility Waste Detection Engine")
    st.markdown("---")
    
    st.subheader("Global Policy Assumptions")
    tariff_elec = st.slider("Electricity Tariff (₹/kWh)", 4.0, 16.0, 8.0, 0.5)
    tariff_water = st.slider("Water Tariff (₹/kL)", 15.0, 60.0, 35.0, 2.5)
    co2_factor = st.slider("Grid Emission (kg CO₂/kWh)", 0.5, 1.2, 0.82, 0.02)
    recoverable_ratio = st.slider("Actionable Recovery %", 0.4, 1.0, 0.70, 0.05)
    
    st.markdown("---")
    st.subheader("🚨 Live Demo Controls (For Judges)")
    demo_type = st.radio("Select Domain to Trigger", ["⚡ Energy", "💧 Water", "♻️ Waste"])
    
    if demo_type == "⚡ Energy":
        sim_b = st.selectbox("Building", ["Academic Blocks & Labs", "Central Library", "Student Hostels", "Mess & Dining Hall", "Lab Block"])
        if st.button("⚡ Inject Electricity Surge", use_container_width=True):
            r = requests.post(f"{API}/simulate-anomaly", params={"building": sim_b})
            if r.ok:
                st.toast(f"Spike triggered in {sim_b}!", icon="⚡")
                st.rerun()

    elif demo_type == "💧 Water":
        w_zone = st.selectbox("Zone", ["Academic & Admin Complex", "Hostel Residential Blocks", "Mess & Dining Kitchens", "Campus Grounds & Irrigation"])
        w_flow = st.slider("Leak Flow Rate (L/hr)", 200, 2500, 1200, 100)
        if st.button("🚨 Simulate Water Pipe Burst", use_container_width=True):
            r = requests.post(f"{API}/water/report-leak", params={"zone": w_zone, "flow_lph": w_flow})
            if r.ok:
                st.toast(f"Pipe burst active in {w_zone}!", icon="💧")
                st.rerun()

    else:
        waste_amt = st.number_input("Food Waste Batch (kg)", min_value=50.0, max_value=2000.0, value=300.0, step=50.0)
        if st.button("♻️ Ingest & Process Biogas Batch", use_container_width=True):
            r = requests.post(f"{API}/waste/process-biogas-batch", params={"organic_kg": waste_amt})
            if r.ok:
                st.toast(f"Converted {waste_amt} kg food waste to clean biogas!", icon="🌱")
                st.rerun()

    st.markdown("---")
    st.subheader("📂 Telemetry Data Ingestion")
    
    # 1. Energy Meter CSV
    with st.expander("⚡ Upload Energy Meter CSV", expanded=False):
        energy_file = st.file_uploader("Energy CSV (timestamp, building, kwh)", type=["csv"], key="energy_upload")
        if energy_file and st.button("Ingest Energy Telemetry", use_container_width=True):
            try:
                r = requests.post(f"{API}/energy/upload", files={"file": (energy_file.name, energy_file.getvalue())})
                if not r.ok:
                    r = requests.post(f"{API}/upload", files={"file": (energy_file.name, energy_file.getvalue())})
                if r.ok:
                    res = r.json()
                    st.session_state["energy_msg"] = f"✅ Ingested {res.get('rows', 'all')} rows from {energy_file.name}!"
                    st.session_state.pop("energy_err", None)
                else:
                    st.session_state["energy_err"] = f"❌ Error: {r.text}"
                    st.session_state.pop("energy_msg", None)
            except Exception as e:
                st.session_state["energy_err"] = f"❌ Failed: {e}"
                st.session_state.pop("energy_msg", None)
            st.rerun()
            
    if "energy_msg" in st.session_state:
        st.success(st.session_state["energy_msg"])
    if "energy_err" in st.session_state:
        st.error(st.session_state["energy_err"])

    # 2. Water Telemetry CSV
    with st.expander("💧 Upload Water Telemetry CSV", expanded=False):
        water_file = st.file_uploader("Water CSV (timestamp, zone, liters)", type=["csv"], key="water_upload")
        if water_file and st.button("Ingest Water Telemetry", use_container_width=True):
            try:
                r = requests.post(f"{API}/water/upload", files={"file": (water_file.name, water_file.getvalue())})
                if r.ok:
                    res = r.json()
                    st.session_state["water_msg"] = f"✅ Ingested {res.get('rows', 'all')} rows across {len(res.get('zones', []))} zones!"
                    st.session_state.pop("water_err", None)
                else:
                    st.session_state["water_err"] = f"❌ Error: {r.text}"
                    st.session_state.pop("water_msg", None)
            except Exception as e:
                st.session_state["water_err"] = f"❌ Failed: {e}"
                st.session_state.pop("water_msg", None)
            st.rerun()

    if "water_msg" in st.session_state:
        st.success(st.session_state["water_msg"])
    if "water_err" in st.session_state:
        st.error(st.session_state["water_err"])

    # 3. Waste Audit CSV
    with st.expander("♻️ Upload Waste Audit CSV", expanded=False):
        waste_file = st.file_uploader("Waste CSV (date, organic_kg, recyclable_dry_kg, landfill_inert_kg)", type=["csv"], key="waste_upload")
        if waste_file and st.button("Ingest Waste Audit Data", use_container_width=True):
            try:
                r = requests.post(f"{API}/waste/upload", files={"file": (waste_file.name, waste_file.getvalue())})
                if r.ok:
                    res = r.json()
                    st.session_state["waste_msg"] = f"✅ Ingested {res.get('rows', 'all')} days ({res.get('total_organic_kg', 0):,} kg organic)!"
                    st.session_state.pop("waste_err", None)
                else:
                    st.session_state["waste_err"] = f"❌ Error: {r.text}"
                    st.session_state.pop("waste_msg", None)
            except Exception as e:
                st.session_state["waste_err"] = f"❌ Failed: {e}"
                st.session_state.pop("waste_msg", None)
            st.rerun()

    if "waste_msg" in st.session_state:
        st.success(st.session_state["waste_msg"])
    if "waste_err" in st.session_state:
        st.error(st.session_state["waste_err"])

    # 4. Appliance Audit CSV
    with st.expander("🏢 Upload Appliance Audit CSV", expanded=False):
        audit_file = st.file_uploader("Appliance Audit CSV", type=["csv"], key="audit_upload")
        if audit_file and st.button("Ingest Room Audit", use_container_width=True):
            try:
                r = requests.post(f"{API}/audit/upload", files={"file": (audit_file.name, audit_file.getvalue())})
                if r.ok:
                    res = r.json()
                    st.session_state["audit_msg"] = f"✅ Ingested {res.get('rows', 'all')} appliance rows!"
                    st.session_state.pop("audit_err", None)
                else:
                    st.session_state["audit_err"] = f"❌ Error: {r.text}"
                    st.session_state.pop("audit_msg", None)
            except Exception as e:
                st.session_state["audit_err"] = f"❌ Failed: {e}"
                st.session_state.pop("audit_msg", None)
            st.rerun()

    if "audit_msg" in st.session_state:
        st.success(st.session_state["audit_msg"])
    if "audit_err" in st.session_state:
        st.error(st.session_state["audit_err"])

# ----------------- INGESTION CALLS -----------------
try:
    score_data = requests.get(f"{API}/scorecard", params={"water_tariff_per_kl": tariff_water}).json()
    energy_data = requests.get(
        f"{API}/energy/analyze", 
        params={"tariff": tariff_elec, "ef": co2_factor, "save": recoverable_ratio}
    ).json()
    water_data = requests.get(
        f"{API}/water/analyze", 
        params={"water_tariff_per_kl": tariff_water}
    ).json()
    waste_data = requests.get(f"{API}/waste/analyze").json()
    audit_data = requests.get(
        f"{API}/audit",
        params={"tariff": tariff_elec, "ef": co2_factor, "save": recoverable_ratio}
    ).json()
except Exception as e:
    st.error(f"⚠️ Backend is not running! Run `python3 -m uvicorn main:app --reload`. Details: {e}")
    st.stop()

# ----------------- EXECUTIVE HEADER -----------------
st.title("🌱 CampusEco: Unified Sustainability Operating System")
e_src = energy_data.get("active_source", "Active Telemetry")
w_src = water_data.get("active_source", "Active Telemetry")
ws_src = waste_data.get("active_source", "Active Telemetry")
st.caption(f"Active Telemetry ➔ ⚡ Energy: **{e_src}** | 💧 Water: **{w_src}** | ♻️ Waste: **{ws_src}**")

tot_rupees = energy_data["total_savings_inr"] + water_data["total_water_loss_inr"] + waste_data["biogas_lpg_value_inr"]
tot_co2 = energy_data["total_co2_kg"] + waste_data["methane_avoided_kg_co2"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Campus Eco Score", f"{score_data['overall_sustainability_score']} / 100", score_data["rating"])
k2.metric("Total Monthly Waste (₹)", f"₹{tot_rupees:,}", "Actionable Recoveries")
k3.metric("CO₂e Avoidable", f"{tot_co2:,.1f} kg", "Monthly Mitigation")
k4.metric("Annual ROI Opportunity", f"₹{(energy_data['annual_projected_inr'] + water_data['total_water_loss_inr'] * 12):,}")

st.progress(float(score_data['overall_sustainability_score']) / 100.0)

daily_rupees = int(tot_rupees / 30)
daily_co2 = round(tot_co2 / 30, 1)
st.warning(f"⚠️ **Cost of Inaction:** Every 24 hours without smart automation costs the campus **₹{daily_rupees:,}** in unmetered losses and adds **{daily_co2} kg** of avoidable CO₂ into the environment.")

st.markdown("---")

# ----------------- TABS -----------------
tab_score, tab_energy, tab_water, tab_waste, tab_whatif, tab_report = st.tabs([
    "🌐 Scorecard & Benchmark", 
    "⚡ Energy Inefficiencies", 
    "💧 Water Leaks & Live Dispatch", 
    "♻️ Waste & Biogas Circularity",
    "🎛️ Interactive What-If ROI",
    "📋 Executive Audit Report"
])

# TAB 1: SCORECARD
with tab_score:
    st.subheader("Campus Sustainability Maturity Benchmark")
    st.write("Calculated using weighted multi-criteria decision analysis across all utilities.")
    
    sc_cols = st.columns(3)
    for idx, (pillar, info) in enumerate(score_data["pillars"].items()):
        with sc_cols[idx]:
            st.markdown(f"### {pillar}")
            st.metric("Performance Index", f"{info['score']}%", f"Weight: {info['weight']}")
            st.caption(f"Status: **{info['status']}**")
    
    st.subheader("Cross-Utility Resource Consumption Breakdown")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("⚡ **Building Daily Electricity Trends (kWh)**")
        st.line_chart(pd.DataFrame(energy_data["timeline_series"], index=energy_data["timeline_dates"]))
    with col_b:
        st.write("💧 **Zonal Water Consumption Trends (Liters)**")
        st.line_chart(pd.DataFrame(water_data["timeline_series"], index=water_data["timeline_dates"]))

# TAB 2: ENERGY
with tab_energy:
    st.subheader("⚡ Automated Energy Waste & Anomaly Detection")
    st.caption("Engine: Median Absolute Deviation (MAD) with Dynamic Occupancy-Aware Filters.")
    
    e1, e2, e3 = st.columns(3)
    e1.metric("Gross Consumption", f"{energy_data['total_kwh_consumed']:,} kWh")
    e2.metric("Wasted Energy Flagged", f"{energy_data['total_waste_kwh']:,} kWh", "-70% with Smart Controls")
    e3.metric("Financial Recovery", f"₹{energy_data['total_savings_inr']:,}")

    st.subheader("🏢 Building Efficiency Leaderboard (Green Badges)")
    st.dataframe(pd.DataFrame(energy_data["building_rankings"]), use_container_width=True)

    st.subheader("Ranked Interventions for Energy Conservation")
    recs_df = pd.DataFrame(energy_data["recommendations"])
    if not recs_df.empty:
        st.dataframe(
            recs_df[["building", "issue", "action", "excess_kwh", "savings_inr", "co2_avoided_kg", "annual_inr"]],
            use_container_width=True
        )

# TAB 3: WATER
with tab_water:
    st.subheader("💧 Acoustic Leakage & Minimum Night Flow (MNF) Diagnostics")
    st.caption("Identifies passive losses between 2:00 AM - 5:00 AM and pinpoints acute bursts across campus plumbing.")
    
    w1, w2, w3 = st.columns(3)
    w1.metric("Net Water Dispatched", f"{water_data['total_consumption_kl']:,} kL")
    w2.metric("Night Leakage / Losses", f"{water_data['total_leakage_kl']:,} kL / month", f"{water_data['active_leaks_count']} Active Leaks")
    w3.metric("Current Tariff Fiscal Drain", f"₹{water_data['total_water_loss_inr']:,} / month", f"@ ₹{tariff_water}/kL")

    st.markdown("### 🚨 Active Water Leak Incidents")
    if water_data["leak_alerts"]:
        leak_df = pd.DataFrame(water_data["leak_alerts"])
        st.dataframe(leak_df[["status", "zone", "type", "flow_lph", "loss_kl_per_month", "loss_inr_per_month", "reported_at", "action"]], use_container_width=True)
        
        st.markdown("#### 🔧 Plumber Dispatch & Leak Resolution Console")
        res_col1, res_col2 = st.columns([3, 1])
        with res_col1:
            active_zones = [l["zone"] for l in water_data["leak_alerts"]]
            target_zone = st.selectbox("Select Zone to Repair & Seal Valve", active_zones)
        with res_col2:
            st.write("")
            st.write("")
            if st.button("🛠️ Seal Leak & Recalculate Tariff", use_container_width=True):
                r = requests.post(f"{API}/water/resolve-leak", params={"zone": target_zone, "water_tariff_per_kl": tariff_water})
                if r.ok:
                    res_json = r.json()
                    st.success(res_json["message"])
                    st.rerun()
                else:
                    st.error(r.text)
    else:
        st.success("🎉 All zones are currently sealed! Zero active plumbing leaks detected.")

    if water_data.get("resolved_leaks"):
        st.markdown("### 🟢 Successfully Sealed & Remediated Leaks")
        st.dataframe(pd.DataFrame(water_data["resolved_leaks"]), use_container_width=True)

# TAB 4: WASTE & BIOGAS
with tab_waste:
    st.subheader("♻️ Solid Waste Audit, Biogas Digestion & Landfill Diversion")
    st.caption("Tracks wet organic food conversion to clean biogas, displacement of LPG commercial cylinders, and methane mitigation.")
    
    ws1, ws2, ws3 = st.columns(3)
    ws1.metric("Total Waste Stream", f"{waste_data['total_waste_kg']:,} kg")
    ws2.metric("Landfill Diversion Rate", f"{waste_data['diversion_rate_pct']}%", "Target > 75%")
    ws3.metric("Methane Prevented", f"{waste_data['methane_avoided_kg_co2']:,} kg CO₂e", f"LPG Value: ₹{waste_data['biogas_lpg_value_inr']:,}")

    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.subheader("Waste Fraction Distribution (kg)")
        st.bar_chart(pd.Series(waste_data["category_breakdown"]))
    with col_w2:
        st.subheader("🌱 Circular Bio-Methanation")
        st.info("**Bio-Digester Status:** Active 250 kg/day anaerobic unit. Converts mess organic waste into clean cooking gas and avoids landfill fees.")
        
        st.markdown("#### Log Contamination Event")
        if st.button("⚠️ Log Canteen Plastic Contamination"):
            r = requests.post(f"{API}/waste/report-contamination")
            if r.ok:
                st.toast("Contamination event logged! Diversion dropped.", icon="⚠️")
                st.rerun()
        if st.button("🧹 Clean & Segregate Stream"):
            r = requests.post(f"{API}/waste/resolve-contamination")
            if r.ok:
                st.toast("Waste stream cleaned!", icon="✅")
                st.rerun()

    if waste_data.get("processed_batches"):
        st.subheader("📜 Recent Biogas Processing Logs")
        st.dataframe(pd.DataFrame(waste_data["processed_batches"]), use_container_width=True)

# TAB 5: WHAT-IF
with tab_whatif:
    st.subheader("🎛️ Interactive Decision-Making Sandbox & Appliance Audit")
    st.write("Toggle planned interventions and appliance-level shutdown actions to view live financial and carbon ROI.")
    
    st.markdown("#### 1. Macro Campus Interventions")
    macro_actions = [
        {"name": "Hostel Complex: Rectify continuous plumbing flush leaks in blocks A & B", "kwh": 0, "inr": 6300, "co2": 210},
        {"name": "Cafeteria: Divert 300 kg/day kitchen wet waste to campus bio-digester", "kwh": 0, "inr": 8640, "co2": 1560},
        {"name": "Campus Grounds: Install smart timer on 5HP irrigation pump", "kwh": 450, "inr": 3600, "co2": 369}
    ]
    
    sel_kwh, sel_inr, sel_co2 = 0, 0, 0
    for act in macro_actions:
        if st.checkbox(f"✅ {act['name']} 👉 (Saves: ₹{act['inr']:,} | {act['co2']} kg CO₂)", value=True, key=act['name']):
            sel_kwh += act["kwh"]
            sel_inr += act["inr"]
            sel_co2 += act["co2"]
            
    st.markdown("#### 2. Micro Appliance-Level Interventions (From Audit)")
    for rec in audit_data["recommendations"][:12]:
        label = f"🔌 {rec['location']} - {rec['appliance']}: Save {rec['saving_kwh']} kWh (₹{rec['saving_inr']:,} / mo, {rec['saving_co2_kg']} kg CO₂)"
        if st.checkbox(label, value=True, key=rec["id"]):
            sel_kwh += rec["saving_kwh"]
            sel_inr += rec["saving_inr"]
            sel_co2 += rec["saving_co2_kg"]

    st.markdown("---")
    st.markdown("### 🏆 Combined Realized Impact (Selected Actions)")
    r1, r2, r3 = st.columns(3)
    r1.metric("Electricity Conserved", f"{sel_kwh:,.1f} kWh / month")
    r2.metric("Fiscal Budget Reclaimed", f"₹{int(sel_inr):,} / month")
    r3.metric("Net Carbon Offset", f"{sel_co2:,.1f} kg CO₂e / month")

# TAB 6: EXECUTIVE AUDIT REPORT
with tab_report:
    st.subheader("📋 Campus Sustainability Executive Audit Report")
    st.write("Downloadable official audit briefing for administrative and facility management.")
    
    report_rows = []
    for r in energy_data["recommendations"]:
        report_rows.append({
            "Domain": "Energy (Electricity)",
            "Location": r["building"],
            "Identified Anomaly": r["issue"],
            "Recommended Engineering Action": r["action"],
            "Monthly Recoverable Savings (INR)": r["savings_inr"],
            "Monthly CO2 Avoided (kg)": r["co2_avoided_kg"],
            "Annual Cost Savings (INR)": r["annual_inr"]
        })
    for l in water_data["leak_alerts"]:
        report_rows.append({
            "Domain": "Water Utility",
            "Location": l["zone"],
            "Identified Anomaly": l["type"],
            "Recommended Engineering Action": l["action"],
            "Monthly Recoverable Savings (INR)": l["loss_inr_per_month"],
            "Monthly CO2 Avoided (kg)": 0,
            "Annual Cost Savings (INR)": l["loss_inr_per_month"] * 12
        })
    report_rows.append({
        "Domain": "Solid Waste",
        "Location": "Campus Mess & Canteens",
        "Identified Anomaly": "Landfill Organic Loss",
        "Recommended Engineering Action": waste_data["action"],
        "Monthly Recoverable Savings (INR)": waste_data["biogas_lpg_value_inr"],
        "Monthly CO2 Avoided (kg)": waste_data["methane_avoided_kg_co2"],
        "Annual Cost Savings (INR)": waste_data["biogas_lpg_value_inr"] * 12
    })
    
    df_report = pd.DataFrame(report_rows)
    st.dataframe(df_report, use_container_width=True)
    
    csv_data = df_report.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Official Executive Audit Report (CSV)",
        data=csv_data,
        file_name="CampusEco_Executive_Audit_Report.csv",
        mime="text/csv",
        use_container_width=True
    )