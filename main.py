"""
CampusEco Unified Backend Engine: Energy, Water, Waste, Scorecard & Full CSV Upload Handlers
Run: python3 -m uvicorn main:app --reload
"""
import io, os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CampusEco Multi-Domain Sustainability OS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_STORE = {"energy": None, "water": None, "waste": None, "audit": None}
ACTIVE_METADATA = {
    "energy_source": "Default Baseline Simulation",
    "energy_rows": 2880,
    "water_source": "Default Baseline Simulation",
    "water_rows": 2880,
    "waste_source": "Default Baseline Simulation",
    "waste_rows": 30
}

OPEN_AT_NIGHT = {"Boys Hostel Block A", "Girls Hostel Block B", "Hostel", "Hostel Residential Blocks", "Student Hostels"}
OPEN_ON_WEEKEND = {"Boys Hostel Block A", "Girls Hostel Block B", "Main Cafeteria & Mess", "Indoor Sports Complex", "Canteen", "Hostel Residential Blocks", "Mess & Dining Hall", "Student Hostels"}

# ----------------- LIVE DYNAMIC STATES (WATER & WASTE) -----------------
ACTIVE_WATER_LEAKS = {
    "Hostel Residential Blocks": {
        "zone": "Hostel Residential Blocks",
        "type": "Cistern Flush Valve Leak",
        "flow_lph": 1800.0,
        "reported_at": "Today 08:15 AM",
        "action": "Acoustic detection flagged continuous night baseflow across hostel washrooms."
    }
}
RESOLVED_WATER_LEAKS = []

PROCESSED_WASTE_BATCHES = [
    {
        "id": "BATCH-101",
        "source": "Hostel Mess & Cafeteria",
        "organic_kg": 250.0,
        "processed_at": "Yesterday 07:00 PM",
        "lpg_saved_kg": 10.0,
        "financial_saved_inr": 900,
        "methane_avoided_kg_co2": 130.0
    }
]
ACTIVE_WASTE_ALERTS = []

def generate_seed_data():
    np.random.seed(42)
    dates_hourly = pd.date_range(end=datetime.now(), periods=30 * 24, freq="h")
    dates_daily = pd.date_range(end=datetime.now(), periods=30, freq="D")

    # 1. Energy Data
    energy_rows = []
    for b in ["Library", "Hostel", "Lab Block", "Canteen"]:
        for t in dates_hourly:
            h, wd = t.hour, t.weekday()
            is_wknd = wd >= 5
            base = 6.0
            if b == "Library":
                base = 5.0 + (25.0 if (8 <= h <= 20 and not is_wknd) else 0.0)
                if is_wknd and 9 <= h <= 18:
                    base += 15.0
            elif b == "Hostel":
                base = 12.0 + (15.0 if (18 <= h <= 23 or 5 <= h <= 8) else 0.0)
            elif b == "Lab Block":
                base = 8.0 + (38.0 if (9 <= h <= 17 and not is_wknd) else 0.0)
                if h >= 22 or h <= 5:
                    base += 18.0
            else:
                base = 5.0 + (20.0 if 7 <= h <= 20 else 0.0)

            kwh = max(base * float(np.random.normal(1, 0.05)), 0.5)
            if b == "Lab Block" and t.day == 14 and 12 <= h <= 14:
                kwh *= 2.5
            energy_rows.append({"timestamp": t, "building": b, "kwh": round(kwh, 2)})
    DATA_STORE["energy"] = pd.DataFrame(energy_rows)

    # 2. Water Data
    water_rows = []
    for zone in ["Hostel Residential Blocks", "Academic & Admin Complex", "Mess & Dining Kitchens", "Campus Grounds & Irrigation"]:
        for t in dates_hourly:
            h = t.hour
            if zone == "Hostel Residential Blocks":
                base_flow = 800.0 if (6 <= h <= 9 or 19 <= h <= 22) else 180.0
                base_flow += 120.0
            elif zone == "Academic & Admin Complex":
                base_flow = 500.0 if (9 <= h <= 17) else 30.0
                if t.day == 21 and 2 <= h <= 6:
                    base_flow += 600.0
            elif zone == "Mess & Dining Kitchens":
                base_flow = 650.0 if (7 <= h <= 15 or 18 <= h <= 21) else 40.0
            else:
                base_flow = 400.0 if (5 <= h <= 8) else 10.0
            
            liters = max(base_flow * float(np.random.normal(1, 0.08)), 5.0)
            water_rows.append({"timestamp": t, "zone": zone, "liters": round(liters, 1)})
    DATA_STORE["water"] = pd.DataFrame(water_rows)

    # 3. Waste Data
    waste_rows = []
    for t in dates_daily:
        waste_rows.append({
            "date": t.strftime("%Y-%m-%d"),
            "organic_kg": round(float(np.random.normal(320, 25)), 1),
            "recyclable_dry_kg": round(float(np.random.normal(180, 15)), 1),
            "landfill_inert_kg": round(float(np.random.normal(140, 20)), 1),
            "e_waste_kg": round(float(np.random.choice([0.0, 0.0, 5.0, 12.0, 0.0, 18.0])), 1)
        })
    DATA_STORE["waste"] = pd.DataFrame(waste_rows)

    # 4. Audit Data
    audit_data = [
        {"location": "Classroom 101", "appliance": "Ceiling fan", "count": 6, "watts": 75, "hours_per_day": 8, "idle_hours_per_day": 2},
        {"location": "Classroom 101", "appliance": "LED tube light", "count": 8, "watts": 20, "hours_per_day": 8, "idle_hours_per_day": 2},
        {"location": "Classroom 101", "appliance": "Air conditioner", "count": 1, "watts": 1500, "hours_per_day": 6, "idle_hours_per_day": 2},
        {"location": "Computer Lab 2", "appliance": "Desktop PC", "count": 30, "watts": 180, "hours_per_day": 9, "idle_hours_per_day": 3},
        {"location": "Computer Lab 2", "appliance": "Split AC 2-Ton", "count": 2, "watts": 2200, "hours_per_day": 8, "idle_hours_per_day": 2},
        {"location": "Library Reading Hall", "appliance": "Tube light", "count": 20, "watts": 36, "hours_per_day": 12, "idle_hours_per_day": 3},
        {"location": "Admin Office", "appliance": "Laser Printer", "count": 3, "watts": 450, "hours_per_day": 8, "idle_hours_per_day": 4}
    ]
    DATA_STORE["audit"] = pd.DataFrame(audit_data)

generate_seed_data()

# ----------------- DATA PROCESSING & VALIDATION -----------------
def process_energy_df(df: pd.DataFrame):
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"timestamp", "building", "kwh"}
    if not need.issubset(df.columns):
        raise HTTPException(400, f"Energy CSV must contain columns: {sorted(need)}. Found: {list(df.columns)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["kwh"] = pd.to_numeric(df["kwh"], errors="coerce")
    df["building"] = df["building"].astype(str).str.strip()
    df = df.dropna(subset=["timestamp", "kwh", "building"])
    if df.empty:
        raise HTTPException(400, "No valid data rows found in uploaded Energy CSV.")
    return df

def process_water_df(df: pd.DataFrame):
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"timestamp", "zone", "liters"}
    if not need.issubset(df.columns):
        raise HTTPException(400, f"Water CSV must contain columns: {sorted(need)}. Found: {list(df.columns)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["liters"] = pd.to_numeric(df["liters"], errors="coerce")
    df["zone"] = df["zone"].astype(str).str.strip()
    df = df.dropna(subset=["timestamp", "liters", "zone"])
    if df.empty:
        raise HTTPException(400, "No valid data rows found in uploaded Water CSV.")
    return df

def process_waste_df(raw_df: pd.DataFrame):
    df = raw_df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Flexible column mapping for organic, recyclable, and landfill streams
    if "organic_wet_kg" in df.columns and "organic_kg" not in df.columns:
        df["organic_kg"] = df["organic_wet_kg"]
    elif "organic" in df.columns and "organic_kg" not in df.columns:
        df["organic_kg"] = df["organic"]
        
    if "recyclable_dry_kg" not in df.columns:
        if "recyclable_kg" in df.columns:
            df["recyclable_dry_kg"] = df["recyclable_kg"]
        elif "dry_kg" in df.columns:
            df["recyclable_dry_kg"] = df["dry_kg"]
            
    if "landfill_inert_kg" not in df.columns:
        if "landfill_kg" in df.columns:
            df["landfill_inert_kg"] = df["landfill_kg"]
        elif "inert_kg" in df.columns:
            df["landfill_inert_kg"] = df["inert_kg"]
            
    if "e_waste_kg" not in df.columns:
        df["e_waste_kg"] = 0.0

    required = {"date", "organic_kg", "recyclable_dry_kg", "landfill_inert_kg"}
    if not required.issubset(df.columns):
        raise HTTPException(400, f"Waste CSV must contain columns: {sorted(required)}. Found: {list(df.columns)}")
        
    df["date"] = df["date"].astype(str).str.strip()
    for col in ["organic_kg", "recyclable_dry_kg", "landfill_inert_kg", "e_waste_kg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["date"])
    if df.empty:
        raise HTTPException(400, "No valid data rows found in uploaded Waste CSV.")
    return df

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "metadata": ACTIVE_METADATA,
        "domains_loaded": {k: (v is not None) for k, v in DATA_STORE.items()}
    }

# ----------------- UPLOAD ENDPOINTS FOR ALL DOMAINS -----------------
@app.post("/energy/upload")
@app.post("/upload")
async def upload_energy(file: UploadFile = File(...)):
    try:
        content = await file.read()
        raw_df = pd.read_csv(io.BytesIO(content))
        cleaned_df = process_energy_df(raw_df)
        DATA_STORE["energy"] = cleaned_df
        ACTIVE_METADATA["energy_source"] = file.filename
        ACTIVE_METADATA["energy_rows"] = len(cleaned_df)
        return {
            "status": "success",
            "source": file.filename,
            "rows": len(cleaned_df),
            "buildings": sorted(cleaned_df["building"].unique().tolist())
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(400, f"Error parsing Energy CSV: {str(e)}")

@app.post("/water/upload")
async def upload_water(file: UploadFile = File(...)):
    try:
        content = await file.read()
        raw_df = pd.read_csv(io.BytesIO(content))
        cleaned_df = process_water_df(raw_df)
        DATA_STORE["water"] = cleaned_df
        ACTIVE_METADATA["water_source"] = file.filename
        ACTIVE_METADATA["water_rows"] = len(cleaned_df)
        
        # Auto-scan Minimum Night Flow (2 AM - 5 AM) for acute leak detection in uploaded data
        df_copy = cleaned_df.copy()
        df_copy["hour"] = df_copy["timestamp"].dt.hour
        night_flow = df_copy[df_copy.hour.between(2, 5)]
        if not night_flow.empty:
            base_leaks = night_flow.groupby("zone")["liters"].median()
            for z, val in base_leaks.items():
                if val > 1000.0 and z not in ACTIVE_WATER_LEAKS:
                    ACTIVE_WATER_LEAKS[z] = {
                        "zone": z,
                        "type": "High Baseline Night Baseflow",
                        "flow_lph": round(float(val), 1),
                        "reported_at": f"Detected in {file.filename}",
                        "action": "Acoustic line leak inspection and isolation valve check recommended."
                    }
                    
        return {
            "status": "success",
            "source": file.filename,
            "rows": len(cleaned_df),
            "zones": sorted(cleaned_df["zone"].unique().tolist())
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(400, f"Error parsing Water CSV: {str(e)}")

@app.post("/waste/upload")
async def upload_waste(file: UploadFile = File(...)):
    try:
        content = await file.read()
        raw_df = pd.read_csv(io.BytesIO(content))
        cleaned_df = process_waste_df(raw_df)
        DATA_STORE["waste"] = cleaned_df
        ACTIVE_METADATA["waste_source"] = file.filename
        ACTIVE_METADATA["waste_rows"] = len(cleaned_df)
        return {
            "status": "success",
            "source": file.filename,
            "rows": len(cleaned_df),
            "total_organic_kg": round(float(cleaned_df["organic_kg"].sum()), 1)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(400, f"Error parsing Waste CSV: {str(e)}")

# ----------------- DYNAMIC SCORECARD -----------------
@app.get("/scorecard")
def campus_scorecard(water_tariff_per_kl: float = 35.0):
    energy_score = 78.0
    active_leak_count = len(ACTIVE_WATER_LEAKS)
    water_score = max(round(92.0 - (active_leak_count * 15.0), 1), 35.0)

    w_df = DATA_STORE["waste"]
    tot_org = float(w_df["organic_kg"].sum()) + sum(b["organic_kg"] for b in PROCESSED_WASTE_BATCHES)
    tot_dry = float(w_df["recyclable_dry_kg"].sum())
    tot_landfill = float(w_df["landfill_inert_kg"].sum()) + sum(a.get("excess_landfill_kg", 0) for a in ACTIVE_WASTE_ALERTS)
    tot_all = tot_org + tot_dry + tot_landfill
    waste_score = round(((tot_org + tot_dry) / tot_all) * 100, 1) if tot_all > 0 else 75.0

    overall = round(energy_score * 0.40 + water_score * 0.30 + waste_score * 0.30, 1)
    
    if overall >= 80:
        band = "Tier-1 Eco Champion (Gold Band)"
    elif overall >= 65:
        band = "Tier-2 Operational (Silver Band)"
    else:
        band = "Tier-3 High Waste Alert (Bronze Band)"

    return {
        "overall_sustainability_score": overall,
        "rating": band,
        "metadata": ACTIVE_METADATA,
        "pillars": {
            "Energy Efficiency": {"score": energy_score, "weight": "40%", "status": "Optimized (MAD Robust Filter)"},
            "Water Infrastructure": {"score": water_score, "weight": "30%", "status": f"{active_leak_count} Active Leak(s) Detected" if active_leak_count > 0 else "All Zones Sealed (Optimal)"},
            "Waste Circularity": {"score": waste_score, "weight": "30%", "status": f"{waste_score}% Landfill Diversion Rate"}
        }
    }

# ----------------- ENERGY ENGINE -----------------
@app.get("/energy/analyze")
def analyze_energy(tariff: float = 8.0, ef: float = 0.82, save: float = 0.70):
    df = DATA_STORE["energy"].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df.timestamp.dt.hour
    df["weekend"] = df.timestamp.dt.weekday >= 5

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

    analyzed = pd.concat(out)
    days = max((analyzed.timestamp.max() - analyzed.timestamp.min()).days, 1)

    action_map = {
        "night_waste": "Automate Smart Timer / Sub-meter shutdown for unoccupied labs & halls.",
        "weekend_waste": "Enforce weekend deep-sleep HVAC schedules.",
        "spike": "Stagger high-load equipment switch-ons & inspect capacitor banks."
    }

    recs = []
    for (b, cat), g in analyzed[analyzed.category != "normal"].groupby(["building", "category"]):
        recoverable_kwh = float(g.excess.sum() * save)
        if recoverable_kwh < 5: continue
        recs.append({
            "building": str(b),
            "issue": str(cat),
            "action": action_map[cat],
            "excess_kwh": round(recoverable_kwh, 1),
            "savings_inr": round(recoverable_kwh * tariff),
            "co2_avoided_kg": round(recoverable_kwh * ef, 1),
            "annual_inr": round(recoverable_kwh * tariff * 365 / days)
        })

    ranking = []
    for b, g in analyzed.groupby("building"):
        tot_b = float(g.kwh.sum())
        exc_b = float(g.excess.sum())
        waste_pct = round((exc_b / tot_b) * 100, 1) if tot_b > 0 else 0.0
        if waste_pct < 5.0:
            badge = "🟢 Grade A (Eco Champion)"
        elif waste_pct < 15.0:
            badge = "🟡 Grade B (Moderate Waste)"
        else:
            badge = "🔴 Grade C (High Waste / Urgent)"
        ranking.append({
            "building": b,
            "total_kwh": round(tot_b, 1),
            "wasted_kwh": round(exc_b, 1),
            "waste_percentage": f"{waste_pct}%",
            "efficiency_grade": badge
        })

    piv = analyzed.groupby([analyzed.timestamp.dt.date.astype(str), "building"])["kwh"].sum().unstack().fillna(0).round(1)

    return {
        "active_source": ACTIVE_METADATA["energy_source"],
        "total_kwh_consumed": round(float(analyzed.kwh.sum()), 1),
        "total_waste_kwh": round(float(analyzed.excess.sum() * save), 1),
        "total_savings_inr": int(sum(r["savings_inr"] for r in recs)),
        "total_co2_kg": round(float(sum(r["co2_avoided_kg"] for r in recs)), 1),
        "annual_projected_inr": int(sum(r["annual_inr"] for r in recs)),
        "recommendations": sorted(recs, key=lambda x: x["savings_inr"], reverse=True),
        "building_rankings": sorted(ranking, key=lambda x: x["wasted_kwh"], reverse=True),
        "timeline_dates": piv.index.tolist(),
        "timeline_series": {col: piv[col].tolist() for col in piv.columns}
    }

@app.post("/simulate-anomaly")
def simulate_anomaly(building: str = "Lab Block"):
    df = DATA_STORE["energy"].copy()
    now_time = datetime.now()
    new_rows = [
        {"timestamp": now_time - timedelta(hours=i), "building": building, "kwh": 98.0 + i*16.0}
        for i in range(3)
    ]
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    DATA_STORE["energy"] = df
    return {"status": "success", "message": f"🚨 Injected simulated load anomaly into {building}!"}

# ----------------- DYNAMIC WATER ENGINE -----------------
@app.get("/water/analyze")
def analyze_water(water_tariff_per_kl: float = 35.0):
    df = DATA_STORE["water"].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    leak_list = []
    tot_monthly_loss_kl = 0.0
    tot_loss_inr = 0.0

    for z, leak_info in ACTIVE_WATER_LEAKS.items():
        flow = leak_info["flow_lph"]
        loss_kl_mo = round((flow * 24 * 30) / 1000.0, 1)
        loss_inr = round(loss_kl_mo * water_tariff_per_kl)
        tot_monthly_loss_kl += loss_kl_mo
        tot_loss_inr += loss_inr
        leak_list.append({
            "zone": z,
            "type": leak_info["type"],
            "flow_lph": flow,
            "loss_kl_per_month": loss_kl_mo,
            "loss_inr_per_month": loss_inr,
            "reported_at": leak_info.get("reported_at", "Active"),
            "action": leak_info["action"],
            "status": "🔴 ACTIVE LEAK"
        })

    total_liters = float(df["liters"].sum())
    piv = df.groupby([df.timestamp.dt.date.astype(str), "zone"])["liters"].sum().unstack().fillna(0).round(1)

    return {
        "active_source": ACTIVE_METADATA["water_source"],
        "total_consumption_kl": round(total_liters / 1000, 1),
        "active_leaks_count": len(ACTIVE_WATER_LEAKS),
        "total_leakage_kl": round(tot_monthly_loss_kl, 1),
        "total_water_loss_inr": int(tot_loss_inr),
        "leak_alerts": leak_list,
        "resolved_leaks": RESOLVED_WATER_LEAKS,
        "timeline_dates": piv.index.tolist(),
        "timeline_series": {col: piv[col].tolist() for col in piv.columns}
    }

@app.post("/water/report-leak")
def report_water_leak(zone: str, leak_type: str = "Pipe Burst / Joint Fracture", flow_lph: float = 750.0):
    ACTIVE_WATER_LEAKS[zone] = {
        "zone": zone,
        "type": leak_type,
        "flow_lph": flow_lph,
        "reported_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "action": f"Emergency isolation valve closed in {zone}; maintenance crew dispatched."
    }
    return {"status": "success", "message": f"🚨 Water leak detected in {zone} ({flow_lph} L/hr)!"}

@app.post("/water/resolve-leak")
def resolve_water_leak(zone: str, water_tariff_per_kl: float = 35.0):
    if zone in ACTIVE_WATER_LEAKS:
        leak = ACTIVE_WATER_LEAKS.pop(zone)
        kl_saved = round((leak["flow_lph"] * 24 * 30) / 1000.0, 1)
        inr_saved = round(kl_saved * water_tariff_per_kl)
        RESOLVED_WATER_LEAKS.append({
            "zone": zone,
            "type": leak["type"],
            "resolved_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "monthly_kl_saved": kl_saved,
            "tariff_saved_inr": inr_saved,
            "status": "🟢 REPAIRED & SEALED"
        })
        return {
            "status": "success", 
            "message": f"✅ Leak in {zone} repaired! Saved {kl_saved} kL/month (₹{inr_saved:,} tariff loss prevented)."
        }
    else:
        raise HTTPException(404, f"No active leak found in zone: {zone}")

# ----------------- DYNAMIC WASTE & CIRCULARITY ENGINE -----------------
@app.get("/waste/analyze")
def analyze_waste():
    df = DATA_STORE["waste"].copy()
    base_organic = float(df["organic_kg"].sum())
    batch_organic = sum(b["organic_kg"] for b in PROCESSED_WASTE_BATCHES)
    tot_organic = base_organic + batch_organic
    
    tot_dry = float(df["recyclable_dry_kg"].sum())
    excess_landfill = sum(a.get("excess_landfill_kg", 0) for a in ACTIVE_WASTE_ALERTS)
    tot_landfill = float(df["landfill_inert_kg"].sum()) + excess_landfill
    tot_ewaste = float(df["e_waste_kg"].sum())
    tot_waste = tot_organic + tot_dry + tot_landfill + tot_ewaste

    diversion_rate = round(((tot_organic + tot_dry) / tot_waste) * 100, 1) if tot_waste > 0 else 75.0
    methane_avoided = round(tot_organic * 0.52, 1)
    biogas_val = round(tot_organic * 0.04 * 90)

    return {
        "active_source": ACTIVE_METADATA["waste_source"],
        "total_waste_kg": round(tot_waste, 1),
        "diversion_rate_pct": diversion_rate,
        "category_breakdown": {
            "Organic Wet (Mess/Canteen)": round(tot_organic, 1),
            "Recyclable Dry (Paper/Plastic)": round(tot_dry, 1),
            "Residual Landfill": round(tot_landfill, 1),
            "E-Waste Managed": round(tot_ewaste, 1)
        },
        "methane_avoided_kg_co2": methane_avoided,
        "biogas_lpg_value_inr": biogas_val,
        "active_alerts": ACTIVE_WASTE_ALERTS,
        "processed_batches": PROCESSED_WASTE_BATCHES,
        "action": "Deploy on-campus 250 kg/day bio-methanation digester to generate cooking gas."
    }

@app.post("/waste/process-biogas-batch")
def process_biogas_batch(source: str = "Hostel Mess Kitchen", organic_kg: float = 300.0):
    lpg_saved = round(organic_kg * 0.04, 1)
    inr_saved = round(lpg_saved * 90)
    co2_saved = round(organic_kg * 0.52, 1)
    batch_id = f"BATCH-{len(PROCESSED_WASTE_BATCHES) + 101}"
    batch = {
        "id": batch_id,
        "source": source,
        "organic_kg": organic_kg,
        "processed_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "lpg_saved_kg": lpg_saved,
        "financial_saved_inr": inr_saved,
        "methane_avoided_kg_co2": co2_saved
    }
    PROCESSED_WASTE_BATCHES.append(batch)
    return {"status": "success", "message": f"♻️ Processed {organic_kg} kg organic waste into biogas! Saved ₹{inr_saved:,} and avoided {co2_saved} kg CO2e."}

@app.post("/waste/report-contamination")
def report_contamination(location: str = "Cafeteria Waste Bin", unsegregated_kg: float = 120.0):
    alert = {
        "id": f"CONTAM-{len(ACTIVE_WASTE_ALERTS) + 1}",
        "location": location,
        "excess_landfill_kg": unsegregated_kg,
        "reported_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "issue": f"{unsegregated_kg} kg of recyclables mixed into municipal landfill bin.",
        "action": "Immediate segregation required by student green audit team."
    }
    ACTIVE_WASTE_ALERTS.append(alert)
    return {"status": "success", "message": f"⚠️ Contamination logged at {location}!"}

@app.post("/waste/resolve-contamination")
def resolve_contamination():
    if ACTIVE_WASTE_ALERTS:
        cleaned = ACTIVE_WASTE_ALERTS.pop(0)
        return {"status": "success", "message": f"✅ Segregated and diverted {cleaned['excess_landfill_kg']} kg back to recycling!"}
    return {"status": "success", "message": "All waste streams already clean."}

# ----------------- APPLIANCE AUDIT -----------------
AUDIT_COLS = ["location", "appliance", "count", "watts", "hours_per_day", "idle_hours_per_day"]

@app.post("/audit/upload")
async def audit_upload(file: UploadFile = File(...)):
    df = pd.read_csv(io.BytesIO(await file.read()))
    df.columns = [c.strip().lower() for c in df.columns]
    miss = [c for c in AUDIT_COLS if c not in df.columns]
    if miss:
        raise HTTPException(400, f"Audit CSV is missing columns: {miss}")
    for c in AUDIT_COLS[2:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=AUDIT_COLS)
    if df.empty:
        raise HTTPException(400, "No valid rows found in audit CSV.")
    DATA_STORE["audit"] = df[AUDIT_COLS].copy()
    return {"status": "success", "rows": len(df), "locations": sorted(df.location.unique().tolist())}

@app.get("/audit")
def get_audit(tariff: float = 8.0, ef: float = 0.82, save: float = 0.70, days: int = 30):
    if DATA_STORE["audit"] is None:
        raise HTTPException(400, "No audit data loaded.")
    d = DATA_STORE["audit"].copy()
    d["daily_kwh"] = d["count"] * d["watts"] * d["hours_per_day"] / 1000.0
    d["idle_kwh_per_day"] = d["count"] * d["watts"] * d["idle_hours_per_day"] / 1000.0
    d["idle_kwh_per_day"] = d[["idle_kwh_per_day", "daily_kwh"]].min(axis=1)

    recs = []
    for r in d[d.idle_kwh_per_day > 0].itertuples():
        kwh = float(r.idle_kwh_per_day * save * days)
        recs.append({
            "id": f"{r.location}|{r.appliance}",
            "location": str(r.location),
            "appliance": str(r.appliance),
            "action": "Switch off or deploy motion sensor timer when room is empty.",
            "idle_hours_per_day": float(r.idle_hours_per_day),
            "saving_kwh": round(kwh, 1),
            "saving_inr": round(kwh * tariff),
            "saving_co2_kg": round(kwh * ef, 1)
        })
    recs.sort(key=lambda x: x["saving_inr"], reverse=True)
    return {
        "period_days": days,
        "appliances": d.round(2).to_dict("records"),
        "recommendations": recs,
        "total_daily_kwh": round(float(d.daily_kwh.sum()), 2)
    }