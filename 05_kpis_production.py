import pandas as pd
import json
import os
from datetime import datetime

os.makedirs("data/json", exist_ok=True)

# ── LOAD CLEAN DATA ───────────────────────────────────────────────
prod   = pd.read_csv("data/clean/production_monthly.csv", parse_dates=["date"])
fields = pd.read_csv("data/clean/fields_overview.csv")

# ── CONSTANTS ─────────────────────────────────────────────────────
BBL_PER_SM3 = 6.2898

# Last month available
last_row        = prod.sort_values("date").iloc[-1]
LAST_MONTH      = int(last_row["month"])
LAST_MONTH_YEAR = int(last_row["year"])

# Previous month
prev_month      = LAST_MONTH - 1 if LAST_MONTH > 1 else 12
prev_month_year = LAST_MONTH_YEAR if LAST_MONTH > 1 else LAST_MONTH_YEAR - 1

prev_month_data = prod[
    (prod["month"] == prev_month) &
    (prod["year"]  == prev_month_year)
]

oe_prev  = prev_month_data["oe_mill_sm3"].sum()
oil_prev = prev_month_data["oil_mill_sm3"].sum()
gas_prev = prev_month_data["gas_mill_sm3"].sum()

# Same month last year
same_month_last_year = prod[
    (prod["month"] == LAST_MONTH) &
    (prod["year"]  == LAST_MONTH_YEAR - 1)
]

print(f"Last month available: {LAST_MONTH}/{LAST_MONTH_YEAR}")
print(f"Comparing MoM vs:     {prev_month}/{prev_month_year}")
print(f"Comparing YoY vs:     {LAST_MONTH}/{LAST_MONTH_YEAR - 1}")

# ── HELPER: % change ─────────────────────────────────────────────
def pct_change(current, previous):
    if previous and previous != 0:
        return round((current - previous) / abs(previous) * 100, 1)
    return 0.0

# ── LAST MONTH TOTALS ─────────────────────────────────────────────
last_month_data = prod[
    (prod["month"] == LAST_MONTH) &
    (prod["year"]  == LAST_MONTH_YEAR)
]

oe_current  = last_month_data["oe_mill_sm3"].sum()
oil_current = last_month_data["oil_mill_sm3"].sum()
gas_current = last_month_data["gas_mill_sm3"].sum()
ngl_current = last_month_data["ngl_mill_sm3"].sum()

oe_yoy = same_month_last_year["oe_mill_sm3"].sum() if len(same_month_last_year) > 0 else 0

# ════════════════════════════════════════════════════════════════
# KPI 1 — OE TOTAL (last month) MoM
# ════════════════════════════════════════════════════════════════
kpi_oe_mill_sm3 = round(oe_current, 3)
kpi_oe_mill_bbl = round(oe_current * BBL_PER_SM3, 3)
kpi_oe_mom      = pct_change(oe_current, oe_prev)

print(f"\nKPI 1 — OE Total {LAST_MONTH}/{LAST_MONTH_YEAR}:")
print(f"  {kpi_oe_mill_sm3} Mill Sm³")
print(f"  {kpi_oe_mill_bbl} Mill bbl")
print(f"  {kpi_oe_mom}% MoM")

# ════════════════════════════════════════════════════════════════
# KPI 2 — TOTAL MONTHLY OIL MoM
# ════════════════════════════════════════════════════════════════
kpi_oil_mill_sm3 = round(oil_current, 3)
kpi_oil_mill_bbl = round(oil_current * BBL_PER_SM3, 3)
kpi_oil_mom      = pct_change(oil_current, oil_prev)

print(f"\nKPI 2 — Oil {LAST_MONTH}/{LAST_MONTH_YEAR}:")
print(f"  {kpi_oil_mill_sm3} Mill Sm³")
print(f"  {kpi_oil_mill_bbl} Mill bbl")
print(f"  {kpi_oil_mom}% MoM")

# ════════════════════════════════════════════════════════════════
# KPI 3 — TOTAL MONTHLY GAS MoM
# ════════════════════════════════════════════════════════════════
kpi_gas_mill_sm3 = round(gas_current, 3)
kpi_gas_mom      = pct_change(gas_current, gas_prev)

print(f"\nKPI 3 — Gas {LAST_MONTH}/{LAST_MONTH_YEAR}:")
print(f"  {kpi_gas_mill_sm3} Mill Sm³")
print(f"  {kpi_gas_mom}% MoM")

# ════════════════════════════════════════════════════════════════
# KPI 4 — OE TOTAL YoY
# ════════════════════════════════════════════════════════════════
kpi_oe_yoy = pct_change(oe_current, oe_yoy)

print(f"\nKPI 4 — OE YoY:")
print(f"  {kpi_oe_yoy}% vs {LAST_MONTH}/{LAST_MONTH_YEAR - 1}")

# ════════════════════════════════════════════════════════════════
# KPI 5 — TOP #1 #2 #3 FIELDS BY OE (last month)
# ════════════════════════════════════════════════════════════════
top_fields = (
    last_month_data.groupby("field_name")["oe_mill_sm3"]
    .sum()
    .sort_values(ascending=False)
    .head(3)
    .reset_index()
)

kpi_top1_name = top_fields.iloc[0]["field_name"] if len(top_fields) > 0 else "N/A"
kpi_top2_name = top_fields.iloc[1]["field_name"] if len(top_fields) > 1 else "N/A"
kpi_top3_name = top_fields.iloc[2]["field_name"] if len(top_fields) > 2 else "N/A"
kpi_top1_oe   = round(top_fields.iloc[0]["oe_mill_sm3"], 3) if len(top_fields) > 0 else 0

print(f"\nKPI 5 — Top Fields OE {LAST_MONTH}/{LAST_MONTH_YEAR}:")
print(f"  #1 {kpi_top1_name}: {kpi_top1_oe} Mill Sm³ OE")
print(f"  #2 {kpi_top2_name}")
print(f"  #3 {kpi_top3_name}")

# ════════════════════════════════════════════════════════════════
# KPI 6 — PRODUCTION MIX TOP #1 FIELD (Oil / Gas / NGL)
# ════════════════════════════════════════════════════════════════
top1_data  = last_month_data[last_month_data["field_name"] == kpi_top1_name]
top1_oil   = top1_data["oil_mill_sm3"].sum()
top1_gas   = top1_data["gas_mill_sm3"].sum()
top1_ngl   = top1_data["ngl_mill_sm3"].sum()
top1_total = top1_oil + top1_gas + top1_ngl

top1_oil_pct = round(top1_oil / top1_total * 100, 1) if top1_total > 0 else 0
top1_gas_pct = round(top1_gas / top1_total * 100, 1) if top1_total > 0 else 0
top1_ngl_pct = round(top1_ngl / top1_total * 100, 1) if top1_total > 0 else 0

dominant = max(
    [("Oil", top1_oil_pct), ("Gas", top1_gas_pct), ("NGL", top1_ngl_pct)],
    key=lambda x: x[1]
)[0]

print(f"\nKPI 6 — Production Mix {kpi_top1_name}:")
print(f"  Oil: {top1_oil_pct}%")
print(f"  Gas: {top1_gas_pct}%")
print(f"  NGL: {top1_ngl_pct}%")
print(f"  Dominant: {dominant}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 1 — TOP 10 FIELDS BY OIL / GAS / NGL (last month)
# ════════════════════════════════════════════════════════════════
top10_fields = (
    last_month_data.groupby("field_name")
    .agg(
        oil=("oil_mill_sm3", "sum"),
        gas=("gas_mill_sm3", "sum"),
        ngl=("ngl_mill_sm3", "sum"),
        oe =("oe_mill_sm3",  "sum")
    )
    .sort_values("oe", ascending=False)
    .head(10)
    .reset_index()
)

chart_top_fields = {
    "fields": top10_fields["field_name"].tolist(),
    "oil":    top10_fields["oil"].round(3).tolist(),
    "gas":    top10_fields["gas"].round(3).tolist(),
    "ngl":    top10_fields["ngl"].round(3).tolist(),
    "oe":     top10_fields["oe"].round(3).tolist(),
}

print(f"\nGraphic 1 — Top 10 Fields {LAST_MONTH}/{LAST_MONTH_YEAR}:")
for _, row in top10_fields.iterrows():
    print(f"  {row['field_name']}: OE={round(row['oe'],3)} Oil={round(row['oil'],3)} Gas={round(row['gas'],3)} NGL={round(row['ngl'],3)}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 2 — OIL / GAS / NGL LAST 12 MONTHS
# ════════════════════════════════════════════════════════════════
last_12 = prod.sort_values("date").drop_duplicates(subset=["year","month"]).tail(12)

chart_production_12m = {
    "labels": last_12["date"].dt.strftime("%b %Y").tolist(),
    "oil":    last_12["oil_mill_sm3"].round(3).tolist(),
    "gas":    last_12["gas_mill_sm3"].round(3).tolist(),
    "ngl":    last_12["ngl_mill_sm3"].round(3).tolist(),
}

print(f"\nGraphic 2 — Last 12 months: {chart_production_12m['labels'][0]} → {chart_production_12m['labels'][-1]}")

# ════════════════════════════════════════════════════════════════
# EXPORT JSON
# ════════════════════════════════════════════════════════════════
production = {
    "last_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
    "last_month":      LAST_MONTH,
    "last_month_year": LAST_MONTH_YEAR,
    "kpis": {
        "oe_total": {
            "mill_sm3": kpi_oe_mill_sm3,
            "mill_bbl": kpi_oe_mill_bbl,
            "mom_pct":  kpi_oe_mom,
            "yoy_pct":  kpi_oe_yoy
        },
        "oil_monthly": {
            "mill_sm3": kpi_oil_mill_sm3,
            "mill_bbl": kpi_oil_mill_bbl,
            "mom_pct":  kpi_oil_mom
        },
        "gas_monthly": {
            "mill_sm3": kpi_gas_mill_sm3,
            "mom_pct":  kpi_gas_mom
        },
        "top_fields": {
            "top1_name": kpi_top1_name,
            "top1_oe":   kpi_top1_oe,
            "top2_name": kpi_top2_name,
            "top3_name": kpi_top3_name
        },
        "production_mix": {
            "field":    kpi_top1_name,
            "oil_pct":  top1_oil_pct,
            "gas_pct":  top1_gas_pct,
            "ngl_pct":  top1_ngl_pct,
            "dominant": dominant
        }
    },
    "charts": {
        "top_fields":      chart_top_fields,
        "production_12m":  chart_production_12m
    }
}

with open("data/json/production.json", "w") as f:
    json.dump(production, f, indent=2)

print(f"\n✓ production.json exportado en data/json/")
print(f"--- KPIs Production completo: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")