"""CampusEco backend. Run:  uvicorn main:app --reload"""
import io, os
import numpy as np, pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CampusEco")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DF = None  # holds the uploaded data in memory
# EDITABLE ASSUMPTIONS (show these on screen; verify real values before claiming them)
# OCCUPANCY CONFIG (editable): buildings that legitimately run at night / on weekends are not flagged for that
OPEN_AT_NIGHT = {"Hostel"}
OPEN_ON_WEEKEND = {"Hostel", "Canteen"}
DEFAULTS = {"tariff_inr_per_kwh": 8.0, "emission_kg_per_kwh": 0.82, "saving_fraction": 0.7}

def load(df: pd.DataFrame):
    need = {"timestamp", "building", "kwh"}
    if not need.issubset(df.columns):
        raise HTTPException(400, f"CSV must have columns: {sorted(need)}")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["kwh"] = pd.to_numeric(df["kwh"], errors="coerce")
    df = df.dropna(subset=["timestamp", "kwh"])
    df["hour"] = df.timestamp.dt.hour
    df["weekend"] = df.timestamp.dt.weekday >= 5
    return df

if os.path.exists("data.csv"):
    DF = load(pd.read_csv("data.csv"))

def need_data():
    if DF is None:
        raise HTTPException(400, "No data. POST a CSV to /upload first.")
    return DF

def analyse(df):
    """Tag every hour as: spike / night_waste / weekend_waste / normal, with excess kWh."""
    out = []
    for b, g in df.groupby("building"):
        g = g.copy()
        base = g.groupby(["hour", "weekend"])["kwh"].transform("median")
        mad = (g["kwh"] - base).abs().groupby([g["hour"], g["weekend"]]).transform("median").clip(lower=0.3)
        g["z"] = 0.6745 * (g["kwh"] - base) / mad
        floor = g["kwh"].quantile(0.10)
        g["category"], g["excess"] = "normal", 0.0
        spike = g["z"] > 3.5
        g.loc[spike, "category"] = "spike"
        g.loc[spike, "excess"] = (g["kwh"] - base)[spike]
        night = (b not in OPEN_AT_NIGHT) & (~spike) & ((g["hour"] >= 23) | (g["hour"] <= 5)) & (g["kwh"] > 1.3 * floor)
        g.loc[night, "category"] = "night_waste"
        g.loc[night, "excess"] = (g["kwh"] - 1.3 * floor)[night]
        wk = (b not in OPEN_ON_WEEKEND) & (~spike) & g["weekend"] & g["hour"].between(6, 22) & (g["kwh"] > 1.3 * floor)
        g.loc[wk, "category"] = "weekend_waste"
        g.loc[wk, "excess"] = (g["kwh"] - 1.3 * floor)[wk]
        out.append(g)
    return pd.concat(out)

@app.get("/health")
def health():
    return {"status": "ok", "data_loaded": DF is not None}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global DF
    DF = load(pd.read_csv(io.BytesIO(await file.read())))
    return {"rows": len(DF), "buildings": sorted(DF.building.unique().tolist())}

@app.get("/analyze")
def analyze():
    a = analyse(need_data())
    summary = []
    for b, g in a.groupby("building"):
        summary.append({"building": b, "total_kwh": round(g.kwh.sum(), 1),
                        "avg_kwh_per_hour": round(g.kwh.mean(), 2),
                        "anomaly_hours": int((g.category != "normal").sum()),
                        "excess_kwh": round(g.excess.sum(), 1)})
    top = a[a.category == "spike"].sort_values("excess", ascending=False).head(10)
    anomalies = [{"building": r.building, "timestamp": str(r.timestamp), "kwh": round(r.kwh, 1),
                  "excess_kwh": round(r.excess, 1)} for r in top.itertuples()]
    return {"summary": summary, "top_spikes": anomalies}

@app.get("/timeseries")
def timeseries():
    d = need_data().copy()
    d["date"] = d.timestamp.dt.date.astype(str)
    p = d.pivot_table(index="date", columns="building", values="kwh", aggfunc="sum").round(1)
    return {"dates": p.index.tolist(), "series": {c: p[c].tolist() for c in p.columns}}

ADVICE = {
    "night_waste": "Install timers / auto-shutdown for after-hours loads (AC, lights, lab equipment).",
    "weekend_waste": "Set a weekend schedule: switch off AC and lighting in unused areas.",
    "spike": "Investigate the spike (equipment fault or simultaneous start-up) and stagger heavy loads.",
}

@app.get("/recommendations")
def recommendations(tariff: float = DEFAULTS["tariff_inr_per_kwh"],
                    ef: float = DEFAULTS["emission_kg_per_kwh"],
                    save: float = DEFAULTS["saving_fraction"]):
    a = analyse(need_data())
    days = max((a.timestamp.max() - a.timestamp.min()).days, 1)
    recs = []
    for (b, cat), g in a[a.category != "normal"].groupby(["building", "category"]):
        kwh = g.excess.sum() * save
        if kwh < 5:
            continue
        recs.append({"building": b, "issue": cat, "action": ADVICE[cat],
                     "hours_affected": len(g),
                     "saving_kwh_per_period": round(kwh, 1),
                     "saving_inr_per_period": round(kwh * tariff),
                     "saving_co2_kg_per_period": round(kwh * ef, 1),
                     "saving_inr_per_year": round(kwh * tariff * 365 / days)})
    recs.sort(key=lambda r: r["saving_inr_per_period"], reverse=True)
    tot = {"kwh": round(sum(r["saving_kwh_per_period"] for r in recs), 1),
           "inr": sum(r["saving_inr_per_period"] for r in recs),
           "co2_kg": round(sum(r["saving_co2_kg_per_period"] for r in recs), 1),
           "inr_per_year": sum(r["saving_inr_per_year"] for r in recs)}
    return {"period_days": days,
            "assumptions": {"tariff_inr_per_kwh": tariff, "emission_kg_per_kwh": ef, "saving_fraction": save,
                            "note": "Editable assumptions; savings are estimates, not guarantees."},
            "recommendations": recs, "total": tot}
