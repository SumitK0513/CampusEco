# CampusEco

Campus energy waste analyser built for the IEEE 5-Hour Hackathon (Ecotech: Technology for a Greener Future).

CampusEco takes hourly meter data, finds inefficiencies and recommends measurable ways to cut consumption, with savings shown in kWh, rupees and CO2.

## What it does
- Upload a CSV of hourly readings (columns: `timestamp`, `building`, `kwh`).
- Builds a baseline for each building by hour and weekday.
- Flags spikes, after-hours (night) waste and weekend waste.
- Skips buildings that legitimately run at night or on weekends (set in `main.py`: `OPEN_AT_NIGHT`, `OPEN_ON_WEEKEND`).
- Recommends an action per building and estimates the savings.
- Shows everything on a Streamlit dashboard.

## Tech
Python, FastAPI, pandas, Streamlit.

## How to run
1. Install the libraries:
   ```
   python3 -m pip install -r requirements.txt
   ```
2. Start the backend (terminal 1):
   ```
   python3 -m uvicorn main:app --reload
   ```
3. Start the dashboard (terminal 2):
   ```
   python3 -m streamlit run app.py
   ```
4. Open http://localhost:8501

`data.csv` is loaded automatically. To regenerate it, run `python3 gen_data.py`.

## Files
- `main.py`: backend API and analysis engine
- `app.py`: dashboard
- `gen_data.py`: generates simulated demo data
- `data.csv`: simulated hourly data for 4 buildings over 30 days

## Important notes
- The demo data is **simulated**. The pipeline works on any CSV with the columns above.
- Tariff (Rs 8/kWh), emission factor (0.82 kg CO2/kWh) and the share of waste that can be removed (70%) are **editable assumptions**, not official figures. Savings are estimates, not guarantees.

## Roadmap
- Real campus data from an appliance audit
- What-if simulator
- Water and waste modes using the same engine
- Building green-score ranking and downloadable report
