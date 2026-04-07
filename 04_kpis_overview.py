import pandas as pd
import json
import os
from datetime import datetime

os.makedirs("data/json", exist_ok=True)

# ── LOAD CLEAN DATA ───────────────────────────────────────────────
fields   = pd.read_csv("data/clean/fields_overview.csv")
prod     = pd.read_csv("data/clean/production_monthly.csv", parse_dates=["date"])
reserves = pd.read_csv("data/clean/reserves.csv")
inv_y    = pd.read_csv("data/clean/investment_yearly.csv")
inv_e    = pd.read_csv("data/clean/investment_expected.csv")

# ── CONSTANTS ─────────────────────────────────────────────────────
BBL_PER_SM3 = 6.2898

# Detect available years and default year
all_years       = sorted(prod["year"].unique().tolist())
months_per_year = prod.groupby("year")["month"].nunique()
partial_years   = months_per_year[months_per_year < 12].index.tolist()
complete_years  = months_per_year[months_per_year == 12].index.tolist()

PRESENT_YEAR = max(complete_years)
LAST_YEAR    = PRESENT_YEAR - 1

print(f"All years:     {all_years}")
print(f"Partial years: {partial_years}")
print(f"Default year:  {PRESENT_YEAR}")
print(f"Comparing vs:  {LAST_YEAR}")

# Debug status values
print(f"\nStatus values: {fields['status'].unique()}")

# ════════════════════════════════════════════════════════════════
# KPI 1 — ACTIVE FIELDS
# ════════════════════════════════════════════════════════════════
fields["status"] = fields["status"].astype(str)

active_fields       = fields[fields["status"] == "Producing"]
transitional_fields = fields[fields["status"] == "Approved for production"]
inactive_fields     = fields[fields["status"] == "Shut down"]

kpi_active_count       = int(len(active_fields))
kpi_transitional_count = int(len(transitional_fields))
kpi_inactive_count     = int(len(inactive_fields))
kpi_total_count        = int(len(fields))

print(f"\nKPI 1 — Fields:")
print(f"  Active:       {kpi_active_count}")
print(f"  Transitional: {kpi_transitional_count}")
print(f"  Not Active:   {kpi_inactive_count}")

# ════════════════════════════════════════════════════════════════
# KPI 2 — TOTAL OIL PRODUCED (present year) + % vs last year
# ════════════════════════════════════════════════════════════════
oil_present = prod[prod["year"] == PRESENT_YEAR]["oil_mill_sm3"].sum()
oil_last    = prod[prod["year"] == LAST_YEAR]["oil_mill_sm3"].sum()

oil_pct_change = ((oil_present - oil_last) / oil_last * 100) if oil_last > 0 else 0
oil_bbl        = oil_present * BBL_PER_SM3 * 1_000_000  # convertir a bbl totales

kpi_oil_mill_sm3  = round(oil_present, 2)
kpi_oil_bbl       = round(oil_bbl / 1_000_000, 2)  # en millones de bbl
kpi_oil_pct       = round(oil_pct_change, 1)

print(f"\nKPI 2 — Total Oil Produced {PRESENT_YEAR}:")
print(f"  {kpi_oil_mill_sm3} Mill Sm³")
print(f"  {kpi_oil_bbl} Mill bbl")
print(f"  {kpi_oil_pct}% vs {LAST_YEAR}")

# ════════════════════════════════════════════════════════════════
# KPI 3 — REMAINING RESERVES (recoverable OE)
# ════════════════════════════════════════════════════════════════
kpi_remaining_oe     = round(reserves["remaining_oe"].sum(), 2)
kpi_recoverable_oe   = round(reserves["recoverable_oe"].sum(), 2)

print(f"\nKPI 3 — Remaining Reserves:")
print(f"  Remaining OE:   {kpi_remaining_oe} Mill Sm³")
print(f"  Recoverable OE: {kpi_recoverable_oe} Mill Sm³")

# ════════════════════════════════════════════════════════════════
# KPI 4 — INVESTMENT
# ════════════════════════════════════════════════════════════════
# Last year with actual investment data (non-zero)
inv_real_years = inv_y[inv_y["investment_mill_nok"] > 0]["year"]
INV_YEAR       = int(inv_real_years.max())
INV_LAST_YEAR  = INV_YEAR - 1

inv_present = inv_y[inv_y["year"] == INV_YEAR]["investment_mill_nok"].sum()
inv_last    = inv_y[inv_y["year"] == INV_LAST_YEAR]["investment_mill_nok"].sum()

inv_pct_change  = ((inv_present - inv_last) / inv_last * 100) if inv_last > 0 else 0
kpi_inv_present = round(float(inv_present), 2)
kpi_inv_pct     = round(inv_pct_change, 1)
kpi_inv_available    = (INV_YEAR == PRESENT_YEAR) 

print(f"\nKPI 4 — Investment {INV_YEAR}:")
print(f"  {kpi_inv_present} Mill NOK")
print(f"  {kpi_inv_pct}% vs {INV_LAST_YEAR}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 1 — OIL PRODUCTION MONTHLY (all years)
# ════════════════════════════════════════════════════════════════
# Last 12 months for default view
last_12 = prod.sort_values("date").drop_duplicates(subset=["year","month"])
last_12 = last_12.tail(12)

chart_production_monthly = {
    "labels": last_12["date"].dt.strftime("%b %Y").tolist(),
    "oil":    last_12["oil_mill_sm3"].round(3).tolist(),
    "gas":    last_12["gas_mill_sm3"].round(3).tolist(),
    "ngl":    last_12["ngl_mill_sm3"].round(3).tolist(),
}

# All months by year — GROUPED by month (sum all fields)
monthly_by_year = {}
for year in prod["year"].unique():
    yr_data = (
        prod[prod["year"] == year]
        .groupby("month")
        .agg(
            oil=("oil_mill_sm3", "sum"),
            gas=("gas_mill_sm3", "sum"),
            ngl=("ngl_mill_sm3", "sum")
        )
        .reset_index()
        .sort_values("month")
    )
    # Create date label
    yr_data["label"] = yr_data["month"].apply(
        lambda m: pd.Timestamp(year=int(year), month=int(m), day=1).strftime("%b %Y")
    )
    monthly_by_year[int(year)] = {
    "labels": yr_data["label"].tolist(),
    "oil":    yr_data["oil"].round(3).tolist(),
    "gas":    (yr_data["gas"] / 1000).round(3).tolist(),  # ← Bill Sm³
    "ngl":    yr_data["ngl"].round(3).tolist(),
    }

# ════════════════════════════════════════════════════════════════
# GRAPHIC 2 — INVESTMENT YEARLY (historical + expected)
# ════════════════════════════════════════════════════════════════
inv_hist = inv_y.groupby("year")["investment_mill_nok"].sum().reset_index()
inv_hist.columns = ["year", "investment"]

# ← añade este filtro
inv_hist = inv_hist[inv_hist["investment"] > 0]

inv_exp = inv_e.groupby("fix_year")["investment_expected_mill_nok"].sum().reset_index()
inv_exp.columns = ["year", "investment_expected"]

chart_investment_yearly = {
    "historical": {
        "years":  inv_hist["year"].tolist(),
        "values": inv_hist["investment"].tolist()
    },
    "expected": {
        "years":  inv_exp["year"].tolist(),
        "values": inv_exp["investment_expected"].tolist()
    }
}

print(f"\nGraphic 2 — Investment historical years: {inv_hist['year'].min()} → {inv_hist['year'].max()}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 3 — FIELDS BY HC TYPE
# ════════════════════════════════════════════════════════════════
fields["hc_type"] = fields["hc_type"].astype(str)

oil_types = ["OIL", "OIL/GAS", "OIL/CONDENSATE"]
gas_types = ["GAS", "GAS/CONDENSATE"]

hc_oil = int(fields[fields["hc_type"].isin(oil_types)]["hc_type"].count())
hc_gas = int(fields[fields["hc_type"].isin(gas_types)]["hc_type"].count())

chart_hc_type = {
    "labels": ["Oil", "Gas"],
    "values": [hc_oil, hc_gas]
}

print(f"\nGraphic 3 — HC Type:")
print(f"  Oil (OIL + OIL/GAS + OIL/CONDENSATE): {hc_oil}")
print(f"  Gas (GAS + GAS/CONDENSATE):            {hc_gas}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 4 — MAP: ACTIVE FIELDS BY SEA AREA
# ════════════════════════════════════════════════════════════════
map_data = (
    active_fields.groupby("main_area")
    .agg(count=("field_name", "count"))
    .reset_index()
    .sort_values("count", ascending=False)
)

chart_map = {
    "areas": map_data["main_area"].tolist(),
    "counts": map_data["count"].tolist()
}

print(f"\nGraphic 4 — Active fields by sea area:")
for area, count in zip(chart_map["areas"], chart_map["counts"]):
    print(f"  {area}: {count}")

# ════════════════════════════════════════════════════════════════
# EXPORT JSON
# ════════════════════════════════════════════════════════════════
# ── ANNUAL PRODUCTION ─────────────────────────────────────────
annual_prod = (
    prod.groupby("year")
    .agg(
        oil=("oil_mill_sm3", "sum"),
        gas=("gas_mill_sm3", "sum"),
        ngl=("ngl_mill_sm3", "sum"),
        oe =("oe_mill_sm3",  "sum")
    )
    .reset_index()
)

annual_data = {}
for _, row in annual_prod.iterrows():
    y = int(row["year"])
    prev_row = annual_prod[annual_prod["year"] == y - 1]
    prev_oil = float(prev_row["oil"].values[0]) if len(prev_row) > 0 else 0
    pct = round((row["oil"] - prev_oil) / prev_oil * 100, 1) if prev_oil > 0 else 0
    annual_data[y] = {
        "oil_mill_sm3": round(float(row["oil"]), 2),
        "gas_mill_sm3": round(float(row["gas"]), 2),
        "ngl_mill_sm3": round(float(row["ngl"]), 2),
        "oe_mill_sm3":  round(float(row["oe"]),  2),
        "oil_mill_bbl": round(float(row["oil"]) * BBL_PER_SM3, 2),
        "pct_vs_prev":  pct,
        "prev_year":    y - 1
    }

print(f"\nAnnual production: {min(annual_data.keys())} → {max(annual_data.keys())}")

overview = {
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "present_year": int(PRESENT_YEAR),
    "annual_production": annual_data,
    "kpis": {
        "active_fields": {
            "count": kpi_active_count,
            "transitional": kpi_transitional_count,
            "inactive":    kpi_inactive_count,
            "total": kpi_total_count
        },
        "total_oil_produced": {
            "mill_sm3": kpi_oil_mill_sm3,
            "mill_bbl": kpi_oil_bbl,
            "pct_vs_last_year": kpi_oil_pct,
            "year": int(PRESENT_YEAR)
        },
        "remaining_reserves": {
            "remaining_oe_mill_sm3": kpi_remaining_oe,
            "recoverable_oe_mill_sm3": kpi_recoverable_oe
        },
        "investment": {
            "mill_nok": kpi_inv_present,
            "pct_vs_last_year": kpi_inv_pct,
            "last_reported_year": INV_YEAR,
            "data_available": kpi_inv_available
        }
    },
    "charts": {
        "production_monthly": chart_production_monthly,
        "monthly_by_year":    monthly_by_year, 
        "investment_yearly":  chart_investment_yearly,
        "hc_type":            chart_hc_type,
        "map":                chart_map
    }
}



with open("data/json/overview.json", "w") as f:
    json.dump(overview, f, indent=2)

print(f"\n✓ overview.json exportado en data/json/")
print(f"--- KPIs Overview completo: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")