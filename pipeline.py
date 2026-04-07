import subprocess
import sys
import time
import os
from datetime import datetime

os.environ["PYTHONIOENCODING"] = "utf-8"

# ── SCRIPTS EN ORDEN ─────────────────────────────────────────────
PIPELINE = [
    ("1_IMPORT.py",        "Downloading data"),
    ("03_clean.py",           "Cleaning data"),
    ("04_kpis_overview.py",   "KPIs Overview"),
    ("05_kpis_production.py", "KPIs Production"),
    ("06_kpis_reserves.py",   "KPIs Reserves"),
    ("07_kpis_investment.py", "KPIs Investment"),
    ("08_master_json.py",     "Building master.json"),
]

# ── RUN PIPELINE ──────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Norway Oil & Gas — Data Pipeline")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*50}\n")

start_total = time.time()
errors = []

for i, (script, label) in enumerate(PIPELINE, 1):
    print(f"[{i}/{len(PIPELINE)}] {label}...", end=" ", flush=True)
    start = time.time()

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True
    )

    duration = round(time.time() - start, 1)

    if result.returncode == 0:
        print(f"✓ ({duration}s)")
    else:
        print(f"✗ ERROR ({duration}s)")
        print(f"\n--- Error in {script} ---")
        print(result.stderr)
        print("─" * 40)
        errors.append(script)

# ── SUMMARY ───────────────────────────────────────────────────────
total_duration = round(time.time() - start_total, 1)

print(f"\n{'='*50}")
if not errors:
    print(f"  Pipeline completed successfully")
    print(f"  Duration: {total_duration}s")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
else:
    print(f"  Pipeline finished with {len(errors)} error(s):")
    for e in errors:
        print(f"  ✗ {e}")
print(f"{'='*50}\n")