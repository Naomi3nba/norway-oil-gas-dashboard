import pandas as pd
import json
import os
from datetime import datetime

os.makedirs("data/json", exist_ok=True)

# ── LOAD CLEAN DATA ───────────────────────────────────────────────
inv_y  = pd.read_csv("data/clean/investment_yearly.csv")
inv_e  = pd.read_csv("data/clean/investment_expected.csv")
fields = pd.read_csv("data/clean/fields_overview.csv")

# ── FILTER REAL DATA (exclude placeholders) ───────────────────────
inv_real = inv_y[inv_y["year"] <= 2024].copy()

# ── CONSTANTS ─────────────────────────────────────────────────────
LAST_YEAR = int(inv_real[inv_real["investment_mill_nok"] > 0]["year"].max())
PREV_YEAR = LAST_YEAR - 1

print(f"Last reported year: {LAST_YEAR}")
print(f"Comparing vs:       {PREV_YEAR}")

# ════════════════════════════════════════════════════════════════
# KPI 1 — TOTAL HISTORICAL INVESTMENT
# ════════════════════════════════════════════════════════════════
kpi_total_historical = round(float(inv_real["investment_mill_nok"].sum()), 2)
kpi_total_historical_bln = round(kpi_total_historical / 1000, 2)

print(f"\nKPI 1 — Total Historical Investment:")
print(f"  {kpi_total_historical:,.0f} Mill NOK")
print(f"  {kpi_total_historical_bln:,.2f} Bln NOK")

# ════════════════════════════════════════════════════════════════
# KPI 2 — INVESTMENT LAST REPORTED YEAR + % vs PREV + % vs PEAK
# ════════════════════════════════════════════════════════════════
inv_by_year = inv_real.groupby("year")["investment_mill_nok"].sum()

inv_last    = float(inv_by_year.get(LAST_YEAR, 0))
inv_prev    = float(inv_by_year.get(PREV_YEAR, 0))

# Peak year
peak_year  = int(inv_by_year.idxmax())
peak_value = float(inv_by_year.max())

pct_vs_prev = round((inv_last - inv_prev) / inv_prev * 100, 1) if inv_prev > 0 else 0
pct_vs_peak = round((inv_last - peak_value) / peak_value * 100, 1) if peak_value > 0 else 0
is_peak     = (LAST_YEAR == peak_year)

kpi_inv_last  = round(inv_last, 2)
kpi_peak_year = peak_year
kpi_peak_value = round(peak_value, 2)

print(f"\nKPI 2 — Investment {LAST_YEAR}:")
print(f"  {kpi_inv_last:,.0f} Mill NOK")
print(f"  {pct_vs_prev:+.1f}% vs {PREV_YEAR}")
print(f"  {pct_vs_peak:+.1f}% vs peak year {peak_year}")
print(f"  Is peak year: {is_peak}")

# KPI 3 — CAPEX EXPECTED 2025
kpi_capex_expected      = round(float(inv_e["investment_expected_mill_nok"].sum()), 2)
kpi_capex_expected_bln  = round(kpi_capex_expected / 1000, 2)
kpi_capex_fields        = int((inv_e["investment_expected_mill_nok"] > 0).sum())

print(f"\nKPI 3 — CAPEX Expected (total remaining):")
print(f"  {kpi_capex_expected:,.0f} Mill NOK")
print(f"  {kpi_capex_expected_bln:,.2f} Bln NOK")
print(f"  {kpi_capex_fields} fields with active investment plans")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 1 — INVESTMENT YEARLY HISTORICAL
# ════════════════════════════════════════════════════════════════
inv_yearly = inv_by_year.reset_index()
inv_yearly.columns = ["year", "investment"]

chart_investment_yearly = {
    "years":  inv_yearly["year"].tolist(),
    "values": inv_yearly["investment"].tolist(),
    "peak_year":  peak_year,
    "peak_value": peak_value
}

print(f"\nGraphic 1 — Investment yearly: {inv_yearly['year'].min()} → {inv_yearly['year'].max()}")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 2 — TOP 7 FIELDS BULLET CHART (cumulative real vs expected)
# ════════════════════════════════════════════════════════════════
# Cumulative real investment by field
cum_real = (
    inv_real.groupby("field_name")["investment_mill_nok"]
    .sum()
    .reset_index()
)
cum_real.columns = ["field_name", "cumulative_real"]

# Expected 2025 by field
expected = inv_e[["field_name", "investment_expected_mill_nok"]].copy()
expected.columns = ["field_name", "expected_2025"]

# Join and get top 7 by cumulative real
bullet = cum_real.merge(expected, on="field_name", how="left")
bullet["expected_2025"] = bullet["expected_2025"].fillna(0)
bullet = bullet.sort_values("cumulative_real", ascending=False).head(7)

chart_bullet = {
    "fields":          bullet["field_name"].tolist(),
    "cumulative_real": bullet["cumulative_real"].tolist(),
    "expected_2025":   bullet["expected_2025"].tolist(),
}

print(f"\nGraphic 2 — Top 7 Fields (cumulative real vs expected 2025):")
for _, row in bullet.iterrows():
    print(f"  {row['field_name']}: Real={row['cumulative_real']:,.0f} | Expected={row['expected_2025']:,.0f} Mill NOK")

# ════════════════════════════════════════════════════════════════
# GRAPHIC 3 — MAP: INVESTMENT BY SEA AREA
# ════════════════════════════════════════════════════════════════
fields["field_name"] = fields["field_name"].astype(str)
fields["main_area"]  = fields["main_area"].astype(str)

inv_area = cum_real.merge(
    fields[["field_name", "main_area"]],
    on="field_name",
    how="left"
)
inv_area["main_area"] = inv_area["main_area"].fillna("UNKNOWN")

area_totals = (
    inv_area.groupby("main_area")["cumulative_real"]
    .sum()
    .reset_index()
    .sort_values("cumulative_real", ascending=False)
)

chart_map_investment = {
    "areas":  area_totals["main_area"].tolist(),
    "values": area_totals["cumulative_real"].tolist()
}

print(f"\nGraphic 3 — Investment by sea area:")
for _, row in area_totals.iterrows():
    print(f"  {row['main_area']}: {row['cumulative_real']:,.0f} Mill NOK")

# ════════════════════════════════════════════════════════════════
# EXPORT JSON
# ════════════════════════════════════════════════════════════════
investment = {
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "last_reported_year": LAST_YEAR,
    "kpis": {
        "total_historical": {
            "mill_nok": kpi_total_historical,
            "bln_nok":  kpi_total_historical_bln,
            "years":    f"1970-{LAST_YEAR}"
        },
        "last_year": {
            "year":          LAST_YEAR,
            "mill_nok":      kpi_inv_last,
            "pct_vs_prev":   pct_vs_prev,
            "prev_year":     PREV_YEAR,
            "pct_vs_peak":   pct_vs_peak,
            "peak_year":     kpi_peak_year,
            "peak_value":    kpi_peak_value,
            "is_peak_year":  is_peak
        },
        "capex_expected": {
            "mill_nok":    kpi_capex_expected,
            "bln_nok":     kpi_capex_expected_bln,
            "active_fields": kpi_capex_fields,
            "fix_year":     2025,
            "note":         "Total remaining investment expected per field"
        }
    },
    "charts": {
        "investment_yearly": chart_investment_yearly,
        "bullet_top7":       chart_bullet,
        "map_investment":    chart_map_investment
    }
}

with open("data/json/investment.json", "w") as f:
    json.dump(investment, f, indent=2)

print(f"\n✓ investment.json exportado en data/json/")
print(f"--- KPIs Investment completo: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")