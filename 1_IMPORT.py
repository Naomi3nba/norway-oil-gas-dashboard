#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
import os
import logging
from datetime import datetime


# In[2]:


os.makedirs("logs", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# In[3]:


# ── FUENTES DE DATOS ─────────────────────────────────────────────
SOURCES = {
    "wellbore": "https://factpages.sodir.no/public?/Factpages/external/tableview/wellbore_all_long&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",

    "fields_overview": "https://factpages.sodir.no/public?/Factpages/external/tableview/field&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",

    "production_monthly": "https://factpages.sodir.no/public?/Factpages/external/tableview/field_production_monthly&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",

    "reserves": "https://factpages.sodir.no/public?/Factpages/external/tableview/field_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",

    "investment_yearly": "https://factpages.sodir.no/public?/Factpages/external/tableview/field_investment_yearly&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",

    "investment_expected": "https://factpages.sodir.no/public?/Factpages/external/tableview/field_investment_expected&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false",
}


# In[4]:


# ── FUNCIÓN DE DESCARGA ───────────────────────────────────────────
def download_source(name, url):
    try:
        logging.info(f"Descargando: {name}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # error si status != 200

        df = pd.read_csv(url, low_memory=False)

        path = f"data/raw/{name}.csv"
        df.to_csv(path, index=False)

        logging.info(f"✓ {name} — {len(df)} filas guardadas en {path}")
        print(f"✓ {name}: {len(df)} filas")

    except Exception as e:
        logging.error(f"✗ Error en {name}: {e}")
        print(f"✗ Error en {name}: {e}")


# In[5]:


# ── EJECUTAR ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n--- Inicio descarga: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n")

    for name, url in SOURCES.items():
        download_source(name, url)

    print(f"\n--- Descarga completa ---")
    print(f"Archivos guardados en: data/raw/")


# In[ ]:




