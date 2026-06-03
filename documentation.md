# Residential Market Insights — Project Handoff Documentation

**Document version:** 1.0  
**Last updated:** June 3, 2026  
**Project type:** Interactive data dashboard (Python Shiny)  
**Primary audience:** Developers, analysts, and operators taking over maintenance or deployment.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Purpose](#2-business-purpose)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [Repository Structure](#5-repository-structure)
6. [Data Layer](#6-data-layer)
7. [ETL Pipeline](#7-etl-pipeline)
8. [Application Backend (Logic & Reactivity)](#8-application-backend-logic--reactivity)
9. [Frontend & User Interface](#9-frontend--user-interface)
10. [Input → Output Mapping](#10-input--output-mapping)
11. [Configuration & Constants](#11-configuration--constants)
12. [Environment Setup & Running](#12-environment-setup--running)
13. [Deployment Considerations](#13-deployment-considerations)
14. [Maintenance Playbook](#14-maintenance-playbook)
15. [Known Issues & Technical Debt](#15-known-issues--technical-debt)
16. [Troubleshooting](#16-troubleshooting)
17. [Security & Compliance](#17-security--compliance)
18. [Handoff Checklist](#18-handoff-checklist)
19. [Glossary](#19-glossary)
20. [Appendix: Code Reference](#20-appendix-code-reference)

---

## 1. Executive Summary

**Residential Market Insights** is a browser-based dashboard that visualizes U.S. residential housing market trends using monthly statistics derived from **Realtor.com** metro-level data. Users filter by **state** and **date range**, view KPI summary cards, and explore three metrics through interactive **Plotly** charts and tabular data grids.

| Item | Detail |
|------|--------|
| **Entry point** | `app.py` |
| **Run command** | `shiny run app.py` |
| **Framework** | [Shiny for Python](https://shiny.posit.co/py/) — **Express** API |
| **Runtime data** | Three CSV files: `listings.csv`, `list_price.csv`, `for_sale.csv` |
| **Optional data refresh** | `etl.py` rebuilds CSVs from `Metro_*.csv` raw files |
| **Time coverage** | April 2018 — April 2024 (month-end dates) |
| **Authentication** | None (local/demo use) |

There is no separate frontend repository: the UI is declared in Python and rendered by the Shiny server with Bootstrap-based components and client-side Plotly widgets.

---

## 2. Business Purpose

### What problem it solves

Analysts and stakeholders need a quick way to compare housing indicators across U.S. states over time without writing SQL or R/Python scripts for each question.

### What users can do

- See **latest median list price** for a selected geography (state or national).
- See **month-over-month percent change in home inventory** (for-sale count).
- Plot **median list price**, **active inventory**, and **new listings** over time.
- Compare **all states at once** when "United States" is selected on charts (multi-line comparison mode).
- Inspect raw numbers in **table** views (full dataset).

### Metrics exposed

| Dashboard label | Internal file | Realtor.com concept |
|-----------------|---------------|---------------------|
| Median List Price | `list_price.csv` | Metro median list price (`mlp`) |
| Home Inventory | `for_sale.csv` | Inventory for sale (`invt_fs`) |
| New Listings | `listings.csv` | New listings count (`new_listings`) |

All processed values use property type suffix **`uc_sfrcondo_sm`** (U.S. combined, single-family residence + condo, smoothed, monthly) per raw file naming.

---

## 3. Technology Stack

### Core runtime

| Layer | Technology | Role |
|-------|------------|------|
| Language | Python 3.x | Application and ETL |
| Web framework | `shiny` (Express mode) | Server, routing, UI layout, reactivity |
| Data manipulation | `pandas` | CSV I/O, filtering, ETL transforms |
| Charts | `plotly` + `plotly.express` | Interactive line charts |
| Chart bridge | `shinywidgets` | Embeds Plotly in Shiny outputs (`render_plotly`) |
| Icons | `faicons` | Font Awesome SVG icons in UI (`icon_svg`) |

`Requirements.txt` lists only packages used by `app.py` and `etl.py`: `shiny`, `shinyswatch`, `faicons`, `pandas`, `plotly`, and `shinywidgets`.

### What is NOT in the project

- No Node.js / React / Vue separate frontend
- No database (PostgreSQL, SQLite, etc.)
- No REST API layer
- No Docker / Kubernetes manifests
- No automated tests or CI/CD
- No `.gitignore` or version pinning in requirements

---

## 4. System Architecture

### High-level diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Client)                                │
│  • Shiny-rendered HTML (Bootstrap 5 theme via Shiny)                    │
│  • Plotly.js (via shinywidgets) for interactive charts                  │
│  • WebSocket/session to Shiny server for reactive updates               │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHINY SERVER (Python process)                        │
│  app.py                                                                 │
│  ├── UI layer (shiny.express.ui) — declarative layout                   │
│  ├── Inputs: state, date_range                                          │
│  ├── @reactive.calc — data load + date filter                           │
│  └── @render.* — KPI text, Plotly figures, DataGrids                    │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ read at startup / on invalidation
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FILE SYSTEM (same directory as app.py)               │
│  listings.csv | list_price.csv | for_sale.csv  ← runtime                │
│  Metro_*.csv (optional) ← ETL only                                      │
└─────────────────────────────────────────────────────────────────────────┘

Optional offline path:
  Metro_*.csv  ──►  etl.py  ──►  three derived CSVs  ──►  app reads CSVs
```

### Shiny Express vs classic Shiny

This project uses **Shiny Express** (`from shiny.express import input, render, ui`):

- UI and server logic live in **one file** (`app.py`).
- Layout is built with Python `with` context managers (e.g. `with ui.sidebar():`).
- Render functions are nested under UI components via decorators (`@render.ui`, `@render_plotly`).
- No separate `def server(input, output, session)` function.

### Reactivity model

1. **Upstream calcs** (`listings_df`, `list_price_df`, `for_sale_df`) read CSVs once per invalidation cycle and cache results for downstream consumers.
2. **Filtered calcs** (`*_filtered`) depend on `input.date_range()` and upstream loaders.
3. **Render functions** depend on filtered data and/or `input.state()`; Shiny re-executes them when inputs change.

This avoids re-reading disk on every date slider movement while still applying date filters efficiently.

---

## 5. Repository Structure

### Complete file inventory

| File | Size (approx.) | Required at runtime? | Description |
|------|----------------|----------------------|-------------|
| `app.py` | 5.6 KB | **Yes** | Main dashboard application |
| `state_choices.py` | 0.5 KB | **Yes** | State dropdown choices |
| `listings.csv` | 103.5 KB | **Yes** | New listings (processed) |
| `list_price.csv` | 106.7 KB | **Yes** | Median list price (processed) |
| `for_sale.csv` | 103.1 KB | **Yes** | Home inventory (processed) |
| `Requirements.txt` | 0.1 KB | **Yes** (install) | Python dependencies |
| `README.md` | — | No | Quick start (see `documentation.md` for full handoff) |
| `documentation.md` | — | No | This handoff document |
| `etl.py` | 1 KB | No | Rebuilds CSVs from raw Metro files |
| `Metro_new_listings_uc_sfrcondo_sm_month.csv` | 389 KB | No | Raw Realtor.com — new listings |
| `Metro_mlp_uc_sfrcondo_sm_month.csv` | 620 KB | No | Raw Realtor.com — median list price |
| `Metro_invt_fs_uc_sfrcondo_sm_month.csv` | 435 KB | No | Raw Realtor.com — inventory for sale |

**Total project size (with raw Metro files):** ~2.3 MB  
**Minimum deploy bundle (app + 3 CSVs + state_choices + requirements):** ~320 KB + dependencies

### Module dependency graph (Python)

```
app.py
 ├── state_choices.py  (STATE_CHOICES)
 ├── listings.csv
 ├── list_price.csv
 └── for_sale.csv

etl.py  (standalone — not imported by app.py)
 ├── Metro_new_listings_uc_sfrcondo_sm_month.csv  → listings.csv
 ├── Metro_mlp_uc_sfrcondo_sm_month.csv           → list_price.csv
 └── Metro_invt_fs_uc_sfrcondo_sm_month.csv       → for_sale.csv
```

---

## 6. Data Layer

### Processed CSV schema (runtime)

All three application CSVs share an identical schema:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `StateName` | string | Two-letter state code, or `"United States"` for national | `CA`, `United States` |
| `Date` | string (ISO date) | Month-end observation date | `2024-04-30` |
| `Value` | float | Metric value for that state and month | `496057.68` |

**Row count:** 3,723 data rows + 1 header = 3,724 lines per file.

**Entity count:** 51 state-level series + 1 national series = **52** `StateName` values per month.

**Month count:** 73 monthly observations from `2018-04-30` through `2024-04-30`.

**Row ordering:** **Date-major** — for each month, all 52 entities appear, then the next month. Example sequence: all states for `2018-04-30`, then all states for `2018-05-31`, etc. This ordering is relied upon implicitly when KPI functions use `iloc[-1]` and `iloc[-2]` after filtering to a single state.

### Raw Metro CSV schema (ETL input)

| Column index | Name | Description |
|--------------|------|-------------|
| 0 | `RegionID` | Realtor.com region identifier |
| 1 | `SizeRank` | Size rank (0 = country) |
| 2 | `RegionName` | e.g. `"Los Angeles, CA"` or `"United States"` |
| 3 | `RegionType` | `country`, `msa`, etc. |
| 4 | `StateName` | State abbreviation (may be empty for country row) |
| 5+ | Date columns | `YYYY-MM-DD` month-end headers with numeric values |

**Metro file row count:** ~925 metro/regions + header per file (926 lines observed for new listings file).

### Metric semantics and units

| File | Typical magnitude | Unit interpretation |
|------|-------------------|---------------------|
| `list_price.csv` | Hundreds of thousands | U.S. dollars (median list price) |
| `for_sale.csv` | Hundreds to thousands per state | Count of active for-sale inventory (state-level average of metros) |
| `listings.csv` | Hundreds per state | Count of new listings (state-level average of metros) |

**Important:** State-level values in processed CSVs are **unweighted arithmetic means** of all metro rows sharing that `StateName`. They are **not** population-weighted. National `"United States"` row comes from the raw file’s `RegionType == "country"` row, not from averaging states.

### Data provenance

- Source family: **Realtor.com Research** metro monthly datasets (file names embedded in repo).
- Geography: U.S. metropolitan statistical areas (MSAs) aggregated to state + country.
- Frequency: Monthly, month-end dates.
- Property scope: `uc_sfrcondo_sm` (U.S. combined single-family + condo, smoothed).

---

## 7. ETL Pipeline

### Script: `etl.py`

**Purpose:** Transform wide-format Metro CSVs into long-format application CSVs.

**Execution:** Run from project root (paths are relative):

```bash
python etl.py
```

**Working directory requirement:** Current working directory must contain both `etl.py` and `Metro_*.csv` files. Output CSVs are written to the same directory.

### Function: `average_by_state(df)`

| Step | Operation |
|------|-----------|
| 1 | Identify date columns as `df.columns[6:]` (all columns after first six metadata columns) |
| 2 | `groupby("StateName").mean(numeric_only=True)` — average metro values per state |
| 3 | Melt state aggregates to long format: `StateName`, `Date`, `Value` |
| 4 | Extract country row: `df[df["RegionType"] == "country"]` |
| 5 | Label country as `StateName = "United States"` and melt |
| 6 | `pd.concat` state + country series |
| 7 | Filter out rows where `Date == "index"` (artifact guard) |

### ETL file mapping

| Input raw file | Output CSV | Variable in script |
|----------------|------------|-------------------|
| `Metro_new_listings_uc_sfrcondo_sm_month.csv` | `listings.csv` | `listings` |
| `Metro_mlp_uc_sfrcondo_sm_month.csv` | `list_price.csv` | `list_price` |
| `Metro_invt_fs_uc_sfrcondo_sm_month.csv` | `for_sale.csv` | `listings` (variable reused — see technical debt) |

### Post-ETL steps for operators

After running ETL, if the date range in raw data changes:

1. Verify min/max dates in output CSVs.
2. Restart the app (slider min/max are read from `list_price.csv` at startup).
3. Restart the Shiny app.

---

## 8. Application Backend (Logic & Reactivity)

### File: `app.py`

**Base path resolution:**

```python
app_dir = Path(__file__).parent
```

All CSV paths are `app_dir / "<filename>.csv"` so the app works regardless of process working directory as long as files sit beside `app.py`.

### Helper functions

| Function | Parameters | Returns | Behavior |
|----------|------------|---------|----------|
| `string_to_date(date_str)` | ISO date string | `datetime.date` | Parses `%Y-%m-%d` |
| `filter_by_date(df, date_range)` | DataFrame, tuple of two dates | Filtered DataFrame | Sorts range endpoints; keeps rows where `Date` is inclusive between min and max |

### Reactive calculations

| Function | Depends on | Returns |
|----------|------------|---------|
| `listings_df()` | File `listings.csv` | Full DataFrame |
| `list_price_df()` | File `list_price.csv` | Full DataFrame |
| `for_sale_df()` | File `for_sale.csv` | Full DataFrame |
| `listings_filtered()` | `listings_df()`, `input.date_range()` | Date-filtered DataFrame |
| `list_price_filtered()` | `list_price_df()`, `input.date_range()` | Date-filtered DataFrame |
| `for_sale_filtered()` | `for_sale_df()`, `input.date_range()` | Date-filtered DataFrame |

### Render functions (outputs)

| Render function | Decorator | Output type | Data sources |
|-----------------|-----------|-------------|--------------|
| `price()` | `@render.ui` | HTML text (formatted currency) | `list_price_filtered()`, `input.state()`, sorted by `Date` |
| `change()` | `@render.ui` | HTML text (formatted percent) | `for_sale_filtered()`, `input.state()`, sorted by `Date` |
| `yoy_change()` | `@render.ui` | HTML text (formatted percent) | `list_price_yoy()`, `input.state()`, sorted by `Date` |
| `list_price_plot()` | `@render_plotly` | Plotly figure | `list_price_filtered()`, `input.state()` |
| `list_price_table()` | `@render.data_frame` | Shiny DataGrid | `list_price_filtered()`, `StateName == input.state()` |
| `for_sale_plot()` | `@render_plotly` | Plotly figure | `for_sale_filtered()`, `input.state()` |
| `for_sale_table()` | `@render.data_frame` | Shiny DataGrid | `for_sale_filtered()`, `StateName == input.state()` |
| `listings_plot()` | `@render_plotly` | Plotly figure | `listings_filtered()`, `input.state()` |
| `listings_table()` | `@render.data_frame` | Shiny DataGrid | `listings_filtered()`, `StateName == input.state()` |
| `list_price_yoy_plot()` | `@render_plotly` | Plotly figure | `list_price_yoy()`, `input.state()` |
| `list_price_yoy_table()` | `@render.data_frame` | Shiny DataGrid | `list_price_yoy()`, `StateName == input.state()` |

### KPI calculation details

**Latest Median List Price (`price`):**

```python
df = list_price_filtered()
df = df[df["StateName"] == input.state()]
df = df.sort_values("Date")
last_value = df.iloc[-1, -1]  # last row, last column (Value)
return f"${last_value:,.0f}"
```

**Latest Home Inventory Change (`change`):**

```python
df = for_sale_filtered()
df = df[df["StateName"] == input.state()]
last_value = df.iloc[-1, -1]
second_last_value = df.iloc[-2, -1]
percent_change = (last_value - second_last_value) / second_last_value * 100
```

- Uses **last two rows in filtered, state-subset data** as proxy for last two months.
- Valid because data is date-ordered within each state when filtered from date-major CSV.
- Adds explicit `+` prefix only for positive changes.
- **Edge case:** If date range contains fewer than 2 months for a state, `iloc[-2]` will use whatever row exists (may not be meaningful MoM).

### Plot logic (state selection)

```python
if input.state() == "United States":
    df = df[df["StateName"] != "United States"]  # all state lines, no national
else:
    df = df[df["StateName"] == input.state()]      # single state line
```

Plotly: `px.line(df, x="Date", y="Value", color="StateName")` with empty axis titles.

---

## 9. Frontend & User Interface

Shiny generates the frontend; there are no custom HTML/CSS/JS files in the repo. Understanding the UI means understanding Shiny Express components and their default styling (Bootstrap 5–based Shiny theme).

### Page-level options

```python
ui.page_opts(title="Residential Market Insights", id="page")
```

| Setting | Value | Effect |
|---------|-------|--------|
| `title` | `"Residential Market Insights"` | Browser tab title |
| `id` | `"page"` | Root page element ID |

### Layout structure (top to bottom)

```
ui.page_opts
└── ui.sidebar
│     ├── ui.input_select  (id: state)
│     └── ui.input_slider  (id: date_range)
└── ui.layout_column_wrap
│     ├── ui.value_box  → render: price
│     └── ui.value_box  → render: change
└── ui.navset_card_underline  "Median List Price"
│     ├── ui.nav_panel " Plot"  → list_price_plot
│     └── ui.nav_panel " Table" → list_price_table
└── ui.navset_card_underline  "Home Inventory"
│     ├── ui.nav_panel " Plot"  → for_sale_plot
│     └── ui.nav_panel " Table" → for_sale_table
└── ui.navset_card_underline  "New Listings"
      ├── ui.nav_panel " Plot"  → listings_plot
      └── ui.nav_panel " Table" → listings_table
```

### Sidebar components

#### State select (`input.state`)

| Property | Value |
|----------|-------|
| **Input ID** | `state` |
| **Label** | `"Filter by state"` |
| **Control** | Dropdown (`ui.input_select`) |
| **Choices** | `STATE_CHOICES` from `state_choices.py` (52 entries) |
| **Default** | First choice: `"United States"` |

#### Date range slider (`input.date_range`)

| Property | Value |
|----------|-------|
| **Input ID** | `date_range` |
| **Label** | `"Filter by date range"` |
| **Control** | Range slider (`ui.input_slider`) |
| **Min** | `min_date` from `list_price.csv` at startup |
| **Max** | `max_date` from `list_price.csv` at startup |
| **Default** | Full range `[min_date, max_date]` |
| **Value type** | `datetime.date` objects |

### Value boxes (KPI cards)

Three cards in `ui.layout_column_wrap(width="300px", heights_equal="row")`.

| Card title | Icon (`faicons`) | Render | Display format |
|------------|------------------|--------|----------------|
| Latest Median List Price | `dollar-sign` | `price()` | `$XXX,XXX` (no decimals) |
| Latest Home Inventory Change | `house` | `change()` | `+X.XX%` or `-X.XX%` |
| Latest YoY Median List Price Change | `arrow-trend-up` | `yoy_change()` | `+X.X%` or `-X.X%` |

Value boxes use Shiny’s **showcase** slot for the icon and a text label; the numeric output is the child render function return value.

### Navigation card sets (`ui.navset_card_underline`)

Three separate card components, each with:

- **Title:** Section name (metric name)
- **Style:** Underline tab variant inside a card container
- **Tabs:**
  - **Plot** — leading space in label `" Plot"` (preserved in code); icon `chart-line`
  - **Table** — label `" Table"`; icon `table`

### Plot frontend (Plotly via shinywidgets)

- **Library:** Plotly Express line chart
- **Interactivity:** Zoom, pan, hover tooltips (Plotly default)
- **Legend:** One entry per `StateName` when multiple series
- **Axes:** Title text explicitly cleared (`title_text=""`)
- **Updates:** Re-rendered server-side when inputs change; widget sent to browser

### Table frontend (Shiny DataGrid)

- **Component:** `render.DataGrid(...)` inside `@render.data_frame`
- **Behavior:** Sortable, scrollable grid (Shiny default DataGrid features)
- **Scope:** Filtered by sidebar state and date range (same as plots and KPIs)

### Icons reference

All icons from `faicons.icon_svg()`:

| Location | Icon name |
|----------|-----------|
| Median list price KPI | `dollar-sign` |
| Inventory change KPI | `house` |
| Plot tabs (all three sections) | `chart-line` |
| Table tabs (all three sections) | `table` |

### Responsive behavior

- `ui.layout_column_wrap()` wraps KPI cards on smaller viewports.
- Sidebar collapses per Shiny/Bootstrap default (platform and theme dependent).
- No custom media queries or mobile-specific code in repo.

### What the user does not see in repo

- No custom branding/CSS file
- No authentication UI
- No export/download buttons
- No loading spinners or error banners (failures surface as server errors)

---

## 10. Input → Output Mapping

| User control | Affects KPI cards | Affects plots | Affects tables |
|--------------|-------------------|---------------|----------------|
| `state` | Yes — filters to selected `StateName` | Yes — single state or all states (special US logic) | Yes — `StateName == input.state()` |
| `date_range` | Yes — defines “latest” and MoM window | Yes | Yes — via `*_filtered()` |

### State = "United States" behavior matrix

| Output | Behavior |
|--------|----------|
| `price` | National median list price series |
| `change` | National inventory MoM % change |
| `*_plot` | Multi-line chart: **all states**, excludes `"United States"` series |
| `*_table` | Rows for `"United States"` national series only |

### State = specific abbreviation (e.g. `"CA"`)

| Output | Behavior |
|--------|----------|
| `price` | California latest median price in date range |
| `change` | California inventory MoM % in date range |
| `*_plot` | Single line for California |
| `*_table` | Still shows all states and dates |

---

## 11. Configuration & Constants

### `state_choices.py`

- **Export:** `STATE_CHOICES` — Python list of 52 strings
- **First entry:** `"United States"` (default dropdown selection)
- **Remaining:** 50 states + DC (alphabetical by abbreviation in file, not strictly alphabetical for full list — US first then AK…WY)

### Hard-coded dates in `app.py`

| Constant usage | Date |
|----------------|------|
| Slider `min` | 2018-04-30 |
| Slider `max` | 2024-04-30 |
| Slider default start | 2018-04-30 |
| Slider default end | 2024-04-30 |

These must be manually synchronized with CSV content after ETL updates.

### Shiny input IDs (for testing/automation)

| ID | Type |
|----|------|
| `state` | select |
| `date_range` | slider (range) |

---

## 12. Environment Setup & Running

### Prerequisites

- Python 3.9+ recommended (3.12 verified in development environment)
- `pip` package manager
- Network access for initial `pip install`

### Windows (PowerShell)

```powershell
cd "<project-folder>"

# Optional virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r Requirements.txt

# Run application
shiny run app.py
```

### macOS / Linux

```bash
cd "/path/to/<project-folder>"
python3 -m venv .venv
source .venv/bin/activate
pip install -r Requirements.txt
shiny run app.py
```

### Common CLI options

| Command | Purpose |
|---------|---------|
| `shiny run app.py` | Default — local dev server |
| `shiny run app.py --reload` | Auto-restart on file changes |
| `shiny run app.py --host 0.0.0.0 --port 8080` | Listen on all interfaces, custom port |
| `shiny run --help` | Full CLI reference |

### Default URL

Typically **`http://127.0.0.1:3838`** (printed in terminal on startup). Port may vary if 3838 is in use.

### ETL command (optional)

```bash
python etl.py
```

Run after replacing `Metro_*.csv` with updated Realtor.com exports.

---

## 13. Deployment Considerations

### Suitable targets

- **Local / VM:** `shiny run` behind firewall for internal analysts
- **Posit Connect / ShinyApps.io (Python):** Supported in principle — bundle `app.py`, CSVs, `state_choices.py`, and `requirements.txt`
- **Container:** Not pre-configured; would need Dockerfile installing requirements and `CMD ["shiny", "run", "app.py", "--host", "0.0.0.0"]`

### Deployment bundle (minimum)

```
app.py
state_choices.py
listings.csv
list_price.csv
for_sale.csv
Requirements.txt
```

Omit `Metro_*.csv` and `etl.py` if data is pre-built and will not be refreshed on server.

### Process model

- Single Python process per app instance
- In-memory reactive cache after CSV load
- No horizontal scaling story without sticky sessions or externalizing data

### Environment variables

**None** are used in current code. All configuration is in source files.

---

## 14. Maintenance Playbook

### Refresh housing data

1. Obtain updated `Metro_*.csv` files from Realtor.com (matching naming convention or adjust `etl.py` paths).
2. Place files in project root.
3. Run `python etl.py`.
4. Validate row counts (~3723 rows per output) and date range in outputs.
5. Update slider min/max in `app.py` if dates extended.
6. Restart Shiny: `shiny run app.py`.

### Add a new state to dropdown

Only needed if ETL produces a new `StateName` not in `STATE_CHOICES`. Edit `state_choices.py` and restart app.

### Change chart type or styling

Edit `px.line(...)` calls in the three `*_plot()` functions in `app.py`. Consider axis titles for production polish.

### Align tables with filters

Replace `list_price_df()` with filtered/state-subset DataFrames in table render functions (documented improvement in §15).

### Dependency cleanup

Audit and pin versions in `Requirements.txt` if deploying to production.

---

## 15. Known Issues & Technical Debt

| ID | Severity | Issue | Location | Status |
|----|----------|-------|----------|--------|
| TD-5 | Low | State aggregates are unweighted metro means | `etl.py` | Open — document or use population weights |
| TD-7 | Low | KPI shows `N/A` if fewer than two months in range (MoM) | `app.py` `change()` | Open — by design |
| TD-8 | Info | Nav panel labels have leading space (`" Plot"`) | `app.py` | Open — cosmetic |
| TD-9 | Info | No tests, CI, or pinned dependency versions | Project-wide | Open |
| TD-10 | Low | YoY table shows decimal `YoY_Change`; plot uses percent ticks | `app.py` | Open |

---

## 16. Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `ModuleNotFoundError: pandas` / `shiny` | Dependencies not installed | `pip install -r Requirements.txt` in active venv |
| `shiny` not recognized | Shiny not on PATH | `python -m shiny run app.py` |
| Blank or error on KPI | State has no rows in range | Widen date range; verify `StateName` exists in CSV |
| `FileNotFoundError` for CSV | Wrong working directory | Run from folder containing CSVs or rely on `app_dir` (should work if `app.py` path correct) |
| Plot empty for one state | Typo in state or no data | Confirm state code in CSV matches dropdown |
| Port already in use | Another Shiny instance | `shiny run app.py --port 3839` |
| PowerShell venv activate blocked | Execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` or use `.\.venv\Scripts\python.exe -m shiny run app.py` |
| ETL overwrites wrong file | Misread variable reuse | Verify `for_sale.csv` timestamp/size after ETL |

---

## 17. Security & Compliance

| Topic | Status |
|-------|--------|
| Authentication | None — anyone with URL can access |
| Authorization | None |
| Secrets / API keys | None stored |
| External network calls at runtime | None (static CSV only) |
| PII | None in datasets (aggregated housing statistics) |
| Data licensing | Realtor.com data — confirm license terms before public deployment |

**Recommendation for production:** Place behind VPN, reverse proxy auth, or Connect/SSO; do not expose `0.0.0.0` publicly without access controls.

---

## 18. Handoff Checklist

Use this when transferring ownership:

- [ ] Clone/copy project directory with all runtime CSVs
- [ ] Confirm Python version and create `venv`
- [ ] Run `pip install -r Requirements.txt`
- [ ] Verify `shiny run app.py` loads at expected URL
- [ ] Confirm three KPI/plot sections render with default filters
- [ ] Document who owns Realtor.com data refresh cadence
- [ ] Store raw `Metro_*.csv` source and download date
- [ ] Confirm tables update when state and date range change
- [ ] Decide deployment target (local only vs Connect)
- [ ] Add version control (`.gitignore` for `.venv/`, `__pycache__/`) if not present
- [ ] Archive this `documentation.md` with the handoff package

---

## 19. Glossary

| Term | Definition |
|------|------------|
| **Shiny Express** | Single-file declarative Shiny for Python API using `with ui.*` contexts |
| **Reactive calc** | Cached computed value that invalidates when dependencies change |
| **MSA** | Metropolitan Statistical Area |
| **MoM** | Month-over-month change |
| **KPI / Value box** | Summary metric card at top of dashboard |
| **DataGrid** | Shiny’s interactive table component |
| **ETL** | Extract, Transform, Load — `etl.py` pipeline |
| **mlp** | Median list price (Realtor.com metric code in filename) |
| **invt_fs** | Inventory for sale |
| **uc_sfrcondo_sm** | Dataset slice: U.S. combined, SFH+condo, smoothed, monthly |

---

## 20. Appendix: Code Reference

### `app.py` line map

| Lines | Section |
|-------|---------|
| 1–14 | Imports and `app_dir` |
| 17–27 | Helper functions |
| 30–65 | Reactive data loaders and filters |
| 72 | Page options |
| 74–86 | Sidebar inputs |
| 88–110 | KPI value boxes |
| 113–134 | Median List Price card |
| 137–158 | Home Inventory card |
| 161–182 | New Listings card |

### `state_choices.py`

52 entries: `United States` + 50 states + `DC`.

### `Requirements.txt` (full)

```
shiny
shinyswatch
faicons
pandas
plotly
shinywidgets
```

### Related documentation

| File | Role |
|------|------|
| `README.md` | Minimal quick start |
| `documentation.md` | This handoff document (authoritative for operations) |

### External references

- Shiny for Python: https://shiny.posit.co/py/
- Shiny Express: https://shiny.posit.co/py/docs/express.html
- shinywidgets: https://github.com/posit-dev/py-shinywidgets
- Plotly Express: https://plotly.com/python/plotly-express/

---

*End of handoff documentation. For implementation changes, edit `app.py`, `etl.py`, or `state_choices.py` and restart the Shiny server.*
