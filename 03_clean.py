import pandas as pd
import os
import logging
from datetime import datetime

# ── SETUP ─────────────────────────────────────────────────────────
os.makedirs("data/clean", exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ════════════════════════════════════════════════════════════════
# 1. FIELDS OVERVIEW
# ════════════════════════════════════════════════════════════════
print("\n── FIELDS OVERVIEW ──")
df = pd.read_csv("data/raw/fields_overview.csv", low_memory=False)

cols = [
    "fldName", "fldCurrentActivitySatus", "fldHcType",
    "fldMainArea", "fldNpdidField", "fldFactPageUrl"
]
df = df[cols]
df.columns = ["field_name", "status", "hc_type", "main_area", "npdid", "fact_url"]

# Nulls — rellenar, no eliminar
df["main_area"] = df["main_area"].fillna("UNKNOWN")
df["hc_type"]   = df["hc_type"].fillna("UNKNOWN")
df["status"]    = df["status"].fillna("UNKNOWN")

print(f"  Nulls restantes:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
df.to_csv("data/clean/fields_overview.csv", index=False)
print(f"  ✓ {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"fields_overview: {len(df)} filas")

# ════════════════════════════════════════════════════════════════
# 2. PRODUCTION MONTHLY
# ════════════════════════════════════════════════════════════════
print("\n── PRODUCTION MONTHLY ──")
df = pd.read_csv("data/raw/production_monthly.csv", low_memory=False)

cols = [
    "prfInformationCarrier", "prfYear", "prfMonth",
    "prfPrdOilNetMillSm3", "prfPrdGasNetBillSm3", "prfPrdNGLNetMillSm3",
    "prfPrdOeNetMillSm3", "prfPrdProducedWaterInFieldMillSm3",
    "prfNpdidInformationCarrier"
]
df = df[cols]
df.columns = [
    "field_name", "year", "month",
    "oil_mill_sm3", "gas_bill_sm3", "ngl_mill_sm3",
    "oe_mill_sm3", "water_mill_sm3", "npdid"
]

# Fecha real
df["date"] = pd.to_datetime(
    df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2),
    format="%Y-%m"
)

# Ya estaba limpio — confirmamos
print(f"  Nulls: {df.isnull().sum().sum()} (esperado: 0)")
df["gas_mill_sm3"] = (df["gas_bill_sm3"] * 1000).round(3)
df.to_csv("data/clean/production_monthly.csv", index=False)
print(f"  ✓ {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"production_monthly: {len(df)} filas")

# ════════════════════════════════════════════════════════════════
# 3. RESERVES
# ════════════════════════════════════════════════════════════════
print("\n── RESERVES ──")
df = pd.read_csv("data/raw/reserves.csv", low_memory=False)

cols = [
    "fldName", "fldVersion",
    "fldRecoverableOil", "fldRecoverableGas", "fldRecoverableNGL", "fldRecoverableOE",
    "fldRemainingOil", "fldRemainingGas", "fldRemainingNGL", "fldRemainingOE",
    "fldDateOffResEstDisplay", "fldNpdidField"
]
df = df[cols]
df.columns = [
    "field_name", "version",
    "recoverable_oil", "recoverable_gas", "recoverable_ngl", "recoverable_oe",
    "remaining_oil", "remaining_gas", "remaining_ngl", "remaining_oe",
    "date_estimate", "npdid"
]

# Versión más reciente por campo
df = df.sort_values("version", ascending=False)
df = df.drop_duplicates(subset="field_name", keep="first")

# Eliminar las 2 filas sin remaining_oe (dato crítico)
antes = len(df)
df = df.dropna(subset=["remaining_oe"])
print(f"  Filas eliminadas por remaining_oe null: {antes - len(df)}")

df["date_estimate"] = pd.to_datetime(df["date_estimate"], format="%d.%m.%Y", errors="coerce")

print(f"  Nulls restantes:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
df.to_csv("data/clean/reserves.csv", index=False)
print(f"  ✓ {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"reserves: {len(df)} filas")

# ════════════════════════════════════════════════════════════════
# 4. INVESTMENT YEARLY
# ════════════════════════════════════════════════════════════════
print("\n── INVESTMENT YEARLY ──")
df = pd.read_csv("data/raw/investment_yearly.csv", low_memory=False)

cols = [
    "prfInformationCarrier", "prfYear",
    "prfInvestmentsMillNOK", "prfNpdidInformationCarrier"
]
df = df[cols]
df.columns = ["field_name", "year", "investment_mill_nok", "npdid"]

print(f"  Nulls: {df.isnull().sum().sum()} (esperado: 0)")
df.to_csv("data/clean/investment_yearly.csv", index=False)
print(f"  ✓ {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"investment_yearly: {len(df)} filas")

# ════════════════════════════════════════════════════════════════
# 5. INVESTMENT EXPECTED
# ════════════════════════════════════════════════════════════════
print("\n── INVESTMENT EXPECTED ──")
df = pd.read_csv("data/raw/investment_expected.csv", low_memory=False)

cols = [
    "fldName", "fldInvestmentExpected",
    "fldInvExpFixYear", "fldNpdidField"
]
df = df[cols]
df.columns = ["field_name", "investment_expected_mill_nok", "fix_year", "npdid"]

print(f"  Nulls: {df.isnull().sum().sum()} (esperado: 0)")
df.to_csv("data/clean/investment_expected.csv", index=False)
print(f"  ✓ {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"investment_expected: {len(df)} filas")

# ════════════════════════════════════════════════════════════════
# 6. WELLBORE
# ════════════════════════════════════════════════════════════════
print("\n── WELLBORE ──")
df = pd.read_csv("data/raw/wellbore.csv", low_memory=False)

cols = [
    "wlbWellboreName", "wlbWellType", "wlbPurpose", "wlbStatus", "wlbContent",
    "wlbEntryDate", "wlbCompletionDate", "wlbField", "wlbMainArea",
    "wlbTotalDepth", "wlbDrillingOperator",
    "wlbNsDecDeg", "wlbEwDecDeg",
    "wlbNpdidWellbore", "fldNpdidField"
]
df = df[cols]
df.columns = [
    "wellbore_name", "well_type", "purpose", "status", "content",
    "entry_date", "completion_date", "field", "main_area",
    "total_depth", "drilling_operator",
    "lat", "lon",
    "npdid_wellbore", "npdid_field"
]

# Nulls — rellenar con UNKNOWN en categóricas
df["content"]  = df["content"].fillna("UNKNOWN")
df["status"]   = df["status"].fillna("UNKNOWN")
df["purpose"]  = df["purpose"].fillna("UNKNOWN")
df["field"]    = df["field"].fillna("UNKNOWN")
df["main_area"]= df["main_area"].fillna("UNKNOWN")

# Fechas
df["entry_date"]      = pd.to_datetime(df["entry_date"], format="%d.%m.%Y", errors="coerce")
df["completion_date"] = pd.to_datetime(df["completion_date"], format="%d.%m.%Y", errors="coerce")
df["entry_year"]      = df["entry_date"].dt.year

# Coordenadas por campo
field_coords = df.dropna(subset=["lat", "lon"]).query("field != 'UNKNOWN'").groupby("field").agg(
    lat=("lat", "mean"),
    lon=("lon", "mean")
).reset_index()
field_coords.to_csv("data/clean/field_coords.csv", index=False)
print(f"  ✓ field_coords: {len(field_coords)} campos con coordenadas")

print(f"  Nulls restantes:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
df.to_csv("data/clean/wellbore.csv", index=False)
print(f"  ✓ wellbore: {len(df)} filas | {len(df.columns)} columnas")
logging.info(f"wellbore: {len(df)} filas")

print(f"\n--- Limpieza completa: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
print("Archivos en data/clean/")