import pandas as pd
import json
import os
from datetime import datetime

os.makedirs("data/json", exist_ok=True)

# ── LOAD CLEAN DATA ───────────────────────────────────────────────
reserves = pd.read_csv("data/clean/reserves.csv", parse_dates=["date_estimate"])
fields   = pd.read_csv("data/clean/fields_overview.csv")
prod     = pd.read_csv("data/clean/production_monthly.csv", parse_dates=["date"])

# ── CONSTANTS ─────────────────────────────────────────────────────
BBL_PER_SM3 = 6.2898
PROD_YEAR   = 2025

# ── DATA AS OF ────────────────────────────────────────────────────
last_estimate = reserves["date_estimate"].max()
data_as_of    = last_estimate.strftime("%B %Y") if pd.notna(last_estimate) else "N/A"
print(f"Reserves data as of: {data_as_of}")

# ── JOIN RESERVES + FIELDS (for hc_type) ─────────────────────────
fields["hc_type"]    = fields["hc_type"].astype(str)
fields["field_name"] = fields["field_name"].astype(str)
reserves["field_name"] = reserves["field_name"].astype(str)

df = reserves.merge(
    fields[["field_name", "hc_type"]],
    on="field_name",
    how="left"
)
df["hc_type"] = df["hc_type"].fillna("UNKNOWN")

# ════════════════════════════════════════════════════════════════
# KPI 1 — RECOVERABLE OE
# ════════════════════════════════════════════════════════════════
kpi_recoverable_oe      = round(reserves["recoverable_oe"].sum(), 2)
kpi_recoverable_oe_bbl  = round(kpi_recoverable_oe * BBL_PER_SM3, 2)
print(f"\nKPI 1 — Recoverable OE: {kpi_recoverable_oe} Mill Sm³ | {kpi_recoverable_oe_bbl} Mill bbl")

# ════════════════════════════════════════════════════════════════
# KPI 2 — REMAINING OE
# ════════════════════════════════════════════════════════════════
kpi_remaining_oe     = round(reserves["remaining_oe"].sum(), 2)
kpi_remaining_oe_bbl = round(kpi_remaining_oe * BBL_PER_SM3, 2)
print(f"KPI 2 — Remaining OE:   {kpi_remaining_oe} Mill Sm³ | {kpi_remaining_oe_bbl} Mill bbl")

# ════════════════════════════════════════════════════════════════
# KPI 3 — PRODUCED TO DATE
# ════════════════════════════════════════════════════════════════
kpi_produced_to_date     = round(kpi_recoverable_oe - kpi_remaining_oe, 2)
kpi_produced_to_date_bbl = round(kpi_produced_to_date * BBL_PER_SM3, 2)
print(f"KPI 3 — Produced to date: {kpi_produced_to_date} Mill Sm³ | {kpi_produced_to_date_bbl} Mill bbl")

# ════════════════════════════════════════════════════════════════
# KPI 4 — R/P NORWAY TOTAL
# ════════════════════════════════════════════════════════════════
annual_prod_oe = prod[prod["year"] == PROD_YEAR]["oe_mill_sm3"].sum()

rp_total = round(kpi_remaining_oe / annual_prod_oe, 1) if annual_prod_oe > 0 else None

print(f"\nKPI 4 — R/P Norway total:")
print(f"  Remaining OE:       {kpi_remaining_oe} Mill Sm³")
print(f"  Annual prod {PROD_YEAR}:  {round(annual_prod_oe, 2)} Mill Sm³")
print(f"  R/P ratio:          {rp_total} years")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 1 — RESERVE LIFE BY FIELD (Top 15 by R/P)
# ════════════════════════════════════════════════════════════════
# Annual production 2025 by field
prod_2025 = (
    prod[prod["year"] == PROD_YEAR]
    .groupby("field_name")["oe_mill_sm3"]
    .sum()
    .reset_index()
)
prod_2025.columns = ["field_name", "annual_oe"]

# Join reserves with production
rp_df = reserves[["field_name", "remaining_oe"]].merge(
    prod_2025, on="field_name", how="left"
)
rp_df["annual_oe"] = rp_df["annual_oe"].fillna(0)

# Calculate R/P per field
def calc_rp(row):
    if row["remaining_oe"] <= 0:
        return "Depleted"
    if row["annual_oe"] <= 0:
        return "Not yet producing"
    rp = round(row["remaining_oe"] / row["annual_oe"], 1)
    return 50.0 if rp > 50 else rp

rp_df["rp"] = rp_df.apply(calc_rp, axis=1)

# Keep only numeric R/P, sort by highest
rp_numeric = rp_df[rp_df["rp"].apply(lambda x: isinstance(x, float))]
rp_numeric = rp_numeric.sort_values("rp", ascending=False).head(15)

# Fields not yet producing
not_producing = rp_df[rp_df["rp"] == "Not yet producing"]["field_name"].tolist()
depleted      = rp_df[rp_df["rp"] == "Depleted"]["field_name"].tolist()

chart_rp_by_field = {
    "fields":          rp_numeric["field_name"].tolist(),
    "rp_years":        rp_numeric["rp"].tolist(),
    "remaining_oe":    rp_numeric["remaining_oe"].round(2).tolist(),
    "not_producing":   not_producing,
    "depleted":        depleted,
    "data_as_of":      data_as_of,
    "cap_note":        "Fields with R/P > 50 years displayed as 50+"
}

print(f"\nGraphic 1 — Top 15 Reserve Life by Field:")
for _, row in rp_numeric.iterrows():
    print(f"  {row['field_name']}: {row['rp']} years")
print(f"  Not yet producing: {len(not_producing)} fields")
print(f"  Depleted:          {len(depleted)} fields")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 2 — REMAINING OE BY HC TYPE (Oil / Gas / NGL)
# ════════════════════════════════════════════════════════════════
oil_types = ["OIL", "OIL/GAS", "OIL/CONDENSATE"]
gas_types = ["GAS", "GAS/CONDENSATE"]

remaining_oil = round(df[df["hc_type"].isin(oil_types)]["remaining_oil"].sum(), 2)
remaining_gas = round(df[df["hc_type"].isin(gas_types)]["remaining_gas"].sum(), 2)
remaining_ngl = round(df["remaining_ngl"].sum(), 2)

chart_remaining_by_type = {
    "labels": ["Oil", "Gas", "NGL"],
    "values": [remaining_oil, remaining_gas, remaining_ngl],
    "data_as_of": data_as_of
}

print(f"\nGraphic 2 — Remaining by HC Type:")
print(f"  Oil: {remaining_oil} Mill Sm³")
print(f"  Gas: {remaining_gas} Bill Sm³")
print(f"  NGL: {remaining_ngl} Mill Sm³")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 3 — RECOVERABLE / PRODUCED TO DATE / REMAINING
# ════════════════════════════════════════════════════════════════
chart_recovery = {
    "labels": ["Recoverable OE", "Produced to date", "Remaining OE"],
    "values": [kpi_recoverable_oe, kpi_produced_to_date, kpi_remaining_oe],
    "data_as_of": data_as_of
}

print(f"\nGraphic 3 — Recovery overview:")
print(f"  Recoverable:      {kpi_recoverable_oe} Mill Sm³")
print(f"  Produced to date: {kpi_produced_to_date} Mill Sm³")
print(f"  Remaining:        {kpi_remaining_oe} Mill Sm³")

# ════════════════════════════════════════════════════════════════
# EXPORT JSON
# ════════════════════════════════════════════════════════════════
reserves_json = {
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "data_as_of":   data_as_of,
    "kpis": {
        "recoverable_oe": {
            "mill_sm3":   kpi_recoverable_oe,
            "mill_bbl":   kpi_recoverable_oe_bbl,
            "data_as_of": data_as_of
        },
        "remaining_oe": {
            "mill_sm3":   kpi_remaining_oe,
            "mill_bbl":   kpi_remaining_oe_bbl,
            "data_as_of": data_as_of
        },
        "produced_to_date": {
            "mill_sm3":   kpi_produced_to_date,
            "mill_bbl":   kpi_produced_to_date_bbl
        },
        "rp_total": {
            "years":       rp_total,
            "based_on_year": PROD_YEAR,
            "data_as_of":  data_as_of
        }
    },
    "charts": {
        "rp_by_field":        chart_rp_by_field,
        "remaining_by_type":  chart_remaining_by_type,
        "recovery_overview":  chart_recovery
    }
}

with open("data/json/reserves.json", "w") as f:
    json.dump(reserves_json, f, indent=2)

print(f"\n✓ reserves.json exportado en data/json/")
print(f"--- KPIs Reserves completo: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")