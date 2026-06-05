# 🏠 Residential Market Insights

> An interactive Python dashboard for exploring U.S. housing market trends — built with Shiny, Plotly, and Pandas across 73 months of real Realtor.com data.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Shiny](https://img.shields.io/badge/Shiny-for_Python-E69F00?style=flat)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?style=flat&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?style=flat&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-27AE60?style=flat)

---

## 📌 What this project does

Residential Market Insights is a **browser-based analytics dashboard** that makes 6 years of U.S. housing data explorable without writing a single query. Select any state (or the national view), adjust the date range, and instantly see:

- How median list prices have trended in your geography
- Whether home inventory is growing or contracting month-over-month
- How new listing volumes have shifted over time
- Year-over-year price change as a headline KPI

It turns raw Realtor.com metro-level CSV data into decision-ready insight — the core job of any data analyst.

---

## 🖥️ Dashboard preview

[![Demo Video](assets/thum.png)](https://github.com/Syed-Abdul-Rehman-Nasir/Housing-Market-Analysis-Dashboard/issues/1#issue-4596141390)
---

## ✨ Key features

| Feature | Detail |
|---|---|
| **4 KPI cards** | Median list price, MoM inventory change, YoY price change — updated live on filter |
| **4 interactive charts** | Plotly line charts with crosshair hover, zoom, and pan |
| **52 geographies** | All 50 states + DC + national United States view |
| **73 months of data** | April 2018 → April 2024 (month-end, smoothed) |
| **Filtered data tables** | DataGrids that respect both state and date selection |
| **ETL pipeline** | `etl.py` rebuilds processed CSVs from raw Metro files — no app code changes needed |
| **Dynamic date bounds** | Slider min/max derived from CSV at startup — no hard-coded dates |

---

## 🛠️ Tech stack

```
Python 3.9+
├── shiny          — Shiny for Python (Express API) — reactive UI + server in one file
├── pandas         — ETL transforms, CSV I/O, date filtering, aggregation
├── plotly         — Interactive line charts (Plotly Express)
├── shinywidgets   — Embeds Plotly figures inside Shiny render outputs
├── shinyswatch    — Dark Bootstrap theme for polished UI
└── faicons        — Font Awesome SVG icons for KPI cards
```

---

## 📊 Data source

Raw data: **[Realtor.com Research](https://www.realtor.com/research/)** — metro monthly files, `uc_sfrcondo_sm` slice  
(U.S. combined · single-family + condo · smoothed monthly series)

The ETL pipeline (`etl.py`) aggregates ~925 metro rows per file into **52 state/national series** using unweighted metro means. Three processed CSVs power the app at runtime:

| File | Metric |
|---|---|
| `list_price.csv` | Median list price (USD) |
| `for_sale.csv` | Active home inventory (count) |
| `listings.csv` | New listings (count) |

---

## 🚀 Quickstart

```bash
# 1. Clone and enter the project
git clone https://github.com/Syed-Abdul-Rehman-Nasir/housing-market-analysis-dashboard.git
cd housing-market-analysis-dashboard

# 2. Create and activate a virtual environment
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r Requirements.txt
shiny run app.py
```


Open **`http://127.0.0.1:3838`** in your browser.


---

## 🔄 Refreshing the data (ETL)

To rebuild processed CSVs from updated Realtor.com Metro files:

```bash
python etl.py
```

Place updated `Metro_*.csv` files in the project root before running. The app reads min/max dates dynamically — no code changes needed after ETL.

| Raw input | Processed output |
|---|---|
| `Metro_new_listings_uc_sfrcondo_sm_month.csv` | `listings.csv` |
| `Metro_mlp_uc_sfrcondo_sm_month.csv` | `list_price.csv` |
| `Metro_invt_fs_uc_sfrcondo_sm_month.csv` | `for_sale.csv` |

---

## 📁 Project structure

```
housing-market-analysis-dashboard/
│
├── app.py                  # Main dashboard — Shiny Express (UI + server in one file)
├── etl.py                  # ETL pipeline — Metro CSVs → processed CSVs
├── state_choices.py        # State dropdown list (52 entries)
│
├── list_price.csv          # Runtime data: median list price
├── for_sale.csv            # Runtime data: home inventory
├── listings.csv            # Runtime data: new listings
│
├── Metro_*_month.csv       # Raw Realtor.com source files (ETL input only)
│
├── Requirements.txt        # Python dependencies
├── README.md               # This file
└── documentation.md        # Full technical handoff — architecture, reactivity, deployment
```

---

## 🏗️ Architecture overview

```
Browser (Plotly.js + Bootstrap UI)
        ▲
        │  WebSocket (reactive updates)
        ▼
Shiny Server — app.py
  ├── @reactive.calc  →  loads CSVs once, caches per session
  ├── @reactive.calc  →  applies date filter downstream
  └── @render.*       →  KPI cards, Plotly figures, DataGrids
        ▲
        │  read on startup / invalidation
        ▼
CSV files  (list_price.csv · for_sale.csv · listings.csv)
        ▲
        │  optional refresh
        ▼
etl.py  ←  Metro_*.csv  (raw Realtor.com)
```

Key design decision: CSVs are read **once per session** and cached reactively. Date and state filters are applied to in-memory DataFrames — not re-read from disk on every slider movement.

---

## ⚠️ Known limitations

- **Unweighted state aggregates** — ETL averages metros within a state; not population-weighted.
- **Static dataset** — App does not fetch live data; refresh requires new Metro files + `etl.py`.
- **No authentication** — Designed for local or trusted-network use; add platform-level auth for public deployment.

---

## 📄 License

Application source code is provided for educational and portfolio use. **Realtor.com research data** is subject to [Realtor.com's terms of use](https://www.realtor.com/research/) — obtain permission before redistribution or commercial publication of derived datasets.

---

