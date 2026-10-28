"""Dashboard. Run (second terminal):  streamlit run app.py"""
import requests, pandas as pd, streamlit as st
API = "http://127.0.0.1:8000"
st.set_page_config(page_title="CampusEco", layout="wide")
st.title("CampusEco: campus energy waste analyser")
st.caption("Demo uses SIMULATED data. The pipeline works on any CSV with columns: timestamp, building, kwh.")

with st.sidebar:
    f = st.file_uploader("Upload CSV", type="csv")
    if f and st.button("Analyse uploaded file"):
        r = requests.post(f"{API}/upload", files={"file": (f.name, f.getvalue())}); st.success(r.json())
    st.subheader("Assumptions (editable)")
    tariff = st.slider("Tariff (₹/kWh)", 4.0, 15.0, 8.0, 0.5)
    ef = st.slider("Emission factor (kg CO₂/kWh)", 0.4, 1.2, 0.82, 0.01)
    save = st.slider("Share of waste we can remove", 0.3, 1.0, 0.7, 0.05)

try:
    ts = requests.get(f"{API}/timeseries").json()
    an = requests.get(f"{API}/analyze").json()
    rc = requests.get(f"{API}/recommendations", params={"tariff": tariff, "ef": ef, "save": save}).json()
except Exception as e:
    st.error(f"Backend not reachable or no data: {e}"); st.stop()

t = rc["total"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Energy saved", f"{t['kwh']} kWh"); c2.metric("Money saved", f"₹{t['inr']:,}")
c3.metric("CO₂ avoided", f"{t['co2_kg']} kg"); c4.metric("Per year (projected)", f"₹{t['inr_per_year']:,}")

st.subheader("Daily consumption by building")
st.line_chart(pd.DataFrame(ts["series"], index=ts["dates"]))
st.subheader("Building summary")
st.dataframe(pd.DataFrame(an["summary"]), use_container_width=True)
st.subheader("Recommendations (ranked by savings)")
st.dataframe(pd.DataFrame(rc["recommendations"]), use_container_width=True)
st.subheader("Biggest spikes")
st.dataframe(pd.DataFrame(an["top_spikes"]), use_container_width=True)
