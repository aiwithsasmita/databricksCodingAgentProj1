# G2211 Provider Profiling & Concentration Risk Dashboard

## Build Guide for Databricks Agent

---

## 1. Project Context

### What is G2211?

HCPCS Code **G2211** is a Medicare add-on code (cannot be billed standalone) recognizing "visit complexity inherent to evaluation and management (E/M) services that serve as the continuing focal point for all needed health care services." It became payable **January 1, 2024**.

### Why This Dashboard?

Medicare and Medicaid spend for G2211-associated claims is running approximately **50% higher** than baseline E/M claims. This dashboard enables actuarial teams to:

- Profile which providers are driving G2211 volume and spend
- Detect geographic concentration of G2211 billing
- Flag outlier providers with abnormally high attachment rates (audit risk)
- Compare Medicare vs Medicaid denial rates and payment differences
- Track the utilization ramp-up trajectory over time for forecasting

### Payer Scope

**Medicare (Fee-for-Service) and Medicaid only** — no commercial or Medicare Advantage in this build.

---

## 2. Required Data Schema

### 2.1 Source Table: `claims`

This is the primary claims-level table. Each row is one claim line.

| Column | Type | Description | Example |
|---|---|---|---|
| `claim_id` | STRING | Unique claim identifier | `CLM00012345` |
| `provider_npi` | STRING | 10-digit National Provider Identifier | `1234567890` |
| `provider_specialty` | STRING | Provider specialty/taxonomy description | `Family Medicine` |
| `provider_state` | STRING | 2-letter state code where provider practices | `CA` |
| `provider_zip` | STRING | Provider 5-digit ZIP code | `90210` |
| `patient_state` | STRING | 2-letter state code of patient residence | `CA` |
| `patient_zip` | STRING | Patient 5-digit ZIP code | `90211` |
| `payer_type` | STRING | Payer category — values: `Medicare`, `Medicaid` | `Medicare` |
| `cpt_code` | STRING | CPT/HCPCS code billed on this line | `99214` |
| `modifier` | STRING | Modifier(s) applied, e.g., `25`, blank if none | `25` |
| `is_g2211` | BOOLEAN | Whether this claim line is for G2211 specifically | `true` |
| `dx_primary` | STRING | Primary ICD-10 diagnosis code | `E11.9` |
| `date_of_service` | DATE | Date the service was rendered | `2024-06-15` |
| `allowed_amount` | DOUBLE | Total allowed amount for this claim line | `145.00` |
| `paid_amount` | DOUBLE | Amount actually paid by the payer | `138.75` |
| `denied` | BOOLEAN | Whether the claim was denied | `false` |
| `denial_reason` | STRING | Denial reason code (null if not denied) | `CO-4` |

### 2.2 Derived Columns (Compute in Databricks)

Add these computed columns to your DataFrame or create a view:

```sql
-- Add these derived columns
SELECT *,
  YEAR(date_of_service) AS service_year,
  DATE_FORMAT(date_of_service, 'yyyy-MM') AS service_month,
  CASE WHEN cpt_code IN ('99202','99203','99204','99205',
                          '99211','99212','99213','99214','99215')
       THEN true ELSE false END AS is_eligible_em,
  CASE WHEN cpt_code = 'G2211' THEN true ELSE false END AS is_g2211_line
FROM claims
WHERE payer_type IN ('Medicare', 'Medicaid')
```

### 2.3 Provider-Level Aggregation Table

Build this aggregation for the scatter plot and Pareto chart:

```sql
CREATE OR REPLACE VIEW provider_g2211_summary AS
SELECT
  provider_npi,
  provider_specialty,
  provider_state,
  provider_zip,
  COUNT(*) AS total_em_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) AS g2211_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) / COUNT(*) AS g2211_attachment_rate,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN allowed_amount ELSE 0 END) AS g2211_total_spend,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN allowed_amount ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 AND NOT denied THEN 1 ELSE 0 END), 0) AS g2211_avg_payment,
  SUM(CASE WHEN is_g2211 AND denied THEN 1 ELSE 0 END) AS g2211_denied_count,
  SUM(CASE WHEN is_g2211 AND denied THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END), 0) AS g2211_denial_rate
FROM claims
WHERE is_eligible_em = true
GROUP BY provider_npi, provider_specialty, provider_state, provider_zip
```

### 2.4 State-Level Aggregation Table

Build this for the geographic heatmap:

```sql
CREATE OR REPLACE VIEW state_g2211_summary AS
SELECT
  provider_state AS state,
  COUNT(*) AS total_em_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) AS g2211_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) / COUNT(*) AS attachment_rate,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN allowed_amount ELSE 0 END) AS g2211_total_spend,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN allowed_amount ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 AND NOT denied THEN 1 ELSE 0 END), 0) AS avg_g2211_payment,
  SUM(CASE WHEN is_g2211 AND denied THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END), 0) AS denial_rate
FROM claims
WHERE is_eligible_em = true
GROUP BY provider_state
```

### 2.5 Monthly Trend Table

Build this for the time trend chart:

```sql
CREATE OR REPLACE VIEW monthly_g2211_trend AS
SELECT
  service_month,
  CASE
    WHEN provider_specialty IN ('Family Medicine','Internal Medicine')
      THEN 'Primary Care'
    WHEN provider_specialty IN ('Cardiology','Endocrinology','Pulmonology',
         'Neurology','Rheumatology','Gastroenterology','Nephrology')
      THEN 'Medical Subspecialty'
    ELSE 'Surgical / Other'
  END AS specialty_group,
  payer_type,
  COUNT(*) AS total_em_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) AS g2211_claims,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) / COUNT(*) AS attachment_rate
FROM claims
WHERE is_eligible_em = true
GROUP BY service_month, specialty_group, payer_type
ORDER BY service_month
```

### 2.6 Specialty x State Heatmap Table

```sql
CREATE OR REPLACE VIEW specialty_state_heatmap AS
SELECT
  provider_specialty,
  provider_state,
  COUNT(*) AS total_em,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) AS g2211_count,
  SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END) / COUNT(*) AS attachment_rate
FROM claims
WHERE is_eligible_em = true
GROUP BY provider_specialty, provider_state
HAVING COUNT(*) >= 10  -- minimum volume threshold to avoid noise
ORDER BY provider_specialty, provider_state
```

### 2.7 Payer Denial Comparison Table

```sql
CREATE OR REPLACE VIEW payer_denial_summary AS
SELECT
  payer_type,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN 1 ELSE 0 END) AS paid_claims,
  SUM(CASE WHEN is_g2211 AND denied THEN 1 ELSE 0 END) AS denied_claims,
  SUM(CASE WHEN is_g2211 AND NOT denied THEN allowed_amount ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 AND NOT denied THEN 1 ELSE 0 END), 0) AS avg_paid_amount,
  SUM(CASE WHEN is_g2211 AND denied THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN is_g2211 THEN 1 ELSE 0 END), 0) AS denial_rate
FROM claims
WHERE is_eligible_em = true
GROUP BY payer_type
```

---

## 3. Dashboard Layout

### 3.1 Overall Structure

The dashboard has a **7-panel layout** organized in 4 rows:

```
+-------------------------------------------------------------+
| HEADER: Title + Filters (State, Specialty, Payer, Year)      |
+-------------------------------------------------------------+
| KPI 1  | KPI 2   | KPI 3   | KPI 4  | KPI 5    | KPI 6     |
+-------------------------------------------------------------+
| US Map Choropleth (60%)     | Pareto Chart (40%)             |
+-------------------------------------------------------------+
| Scatter Plot (50%)          | Specialty x State Heatmap (50%)|
+-------------------------------------------------------------+
| Payer Denial Bars (40%)     | Monthly Trend Lines (60%)      |
+-------------------------------------------------------------+
```

### 3.2 Theme & Colors

Use a **white / blue / orange** theme throughout:

| Token | Hex | Usage |
|---|---|---|
| Background | `#f1f5f9` | Page background |
| Card | `#ffffff` | Panel/card backgrounds |
| Border | `#e2e8f0` | Card borders, grid lines |
| Blue (primary) | `#2563eb` | Medicare, primary data bars, map |
| Blue Light | `#dbeafe` | Hover states, focus rings |
| Orange (secondary) | `#f97316` | Medicaid, cumulative lines, accents |
| Green | `#16a34a` | Positive indicators, paid claims |
| Red | `#dc2626` | Negative indicators, denied claims, outliers |
| Amber | `#d97706` | Warning indicators |
| Text | `#0f172a` | Primary text |
| Muted | `#64748b` | Secondary text, axis labels |
| Light | `#94a3b8` | Tertiary text, tick labels |

**Font**: `DM Sans` for UI text, `JetBrains Mono` for numbers/KPIs.

---

## 4. Chart Specifications — Panel by Panel

### 4.1 KPI Scorecard (Row 0)

Six summary cards displayed in a single row.

| KPI | Metric | Formula | Color Accent |
|---|---|---|---|
| Total Claims | Count of all E/M claims in filtered set | `COUNT(*)` | Blue `#2563eb` |
| G2211 Claims | Count of claims where `is_g2211 = true` | `SUM(is_g2211)` | Orange `#f97316` |
| G2211 Spend | Total allowed amount for non-denied G2211 | `SUM(allowed_amount) WHERE is_g2211 AND NOT denied` | Green `#16a34a` |
| Denial Rate | % of G2211 claims denied | `denied_g2211 / total_g2211` | Red `#dc2626` |
| Outlier Providers | Providers with >40% attachment rate and >20 claims | Count from provider summary | Amber `#d97706` |
| Top State | State with most G2211 claims | Max from state summary | Purple `#7c3aed` |

Each card has:
- A 3px colored top border strip
- Label in uppercase `10px` muted text
- Value in `26px` bold monospace
- Subtitle in `11px` with contextual color

**Databricks Python code to compute:**

```python
import pandas as pd

def compute_kpis(df):
    total_claims = len(df)
    g2211_claims = df['is_g2211'].sum()
    attachment_rate = g2211_claims / total_claims if total_claims > 0 else 0
    g2211_spend = df.loc[df['is_g2211'] & ~df['denied'], 'allowed_amount'].sum()
    denied_count = df.loc[df['is_g2211'] & df['denied']].shape[0]
    denial_rate = denied_count / g2211_claims if g2211_claims > 0 else 0

    prov_summary = df.groupby('provider_npi').agg(
        total=('claim_id', 'count'),
        g2211_count=('is_g2211', 'sum')
    )
    prov_summary['rate'] = prov_summary['g2211_count'] / prov_summary['total']
    outlier_count = ((prov_summary['total'] > 20) & (prov_summary['rate'] > 0.4)).sum()

    top_state = (df[df['is_g2211']]
                 .groupby('provider_state')
                 .size()
                 .idxmax())

    return {
        'total_claims': total_claims,
        'g2211_claims': g2211_claims,
        'attachment_rate': attachment_rate,
        'g2211_spend': g2211_spend,
        'denial_rate': denial_rate,
        'denied_count': denied_count,
        'outlier_providers': outlier_count,
        'top_state': top_state
    }
```

---

### 4.2 Geographic Heatmap — US State Choropleth (Row 1, Left)

**Chart Type**: Choropleth map of US states.

**Data Source**: `state_g2211_summary` view.

**Visual Spec**:
- Map projection: **Albers USA** (includes Alaska/Hawaii insets)
- Fill color: Sequential **blue scale** (`d3.interpolateBlues`) mapped to G2211 total spend per state
- States with zero G2211 spend: fill `#f1f5f9` (light gray)
- State borders: `#cbd5e1`, stroke width `0.5px`
- Legend: Horizontal gradient bar at bottom-right showing `$0` to `$max`

**Tooltip on Hover**:
```
State: {state_code}
G2211 Spend: ${total_spend}
G2211 Claims: {count}
Attachment Rate: {rate}%
```

**D3.js Implementation**:
- Load TopoJSON from: `https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json`
- Use `topojson.feature(us, us.objects.states)` to extract state features
- Match states by FIPS code (the `id` field in TopoJSON)
- Use `d3.geoAlbersUsa()` projection, fitted to SVG bounds via `fitSize()`

**State FIPS Code Mapping** (needed to join your data):

| State | FIPS | State | FIPS | State | FIPS | State | FIPS |
|---|---|---|---|---|---|---|---|
| AL | 01 | IL | 17 | MT | 30 | PA | 42 |
| AK | 02 | IN | 18 | NE | 31 | RI | 44 |
| AZ | 04 | IA | 19 | NV | 32 | SC | 45 |
| AR | 05 | KS | 20 | NH | 33 | TN | 47 |
| CA | 06 | KY | 21 | NJ | 34 | TX | 48 |
| CO | 08 | LA | 22 | NM | 35 | UT | 49 |
| CT | 09 | ME | 23 | NY | 36 | VA | 51 |
| FL | 12 | MD | 24 | NC | 37 | WA | 53 |
| GA | 13 | MA | 25 | OH | 39 | WI | 55 |
| HI | 15 | MI | 26 | OK | 40 | WY | 56 |

**Databricks Python code**:

```python
import plotly.express as px

def render_geo_heatmap(state_df):
    fig = px.choropleth(
        state_df,
        locations='state',
        locationmode='USA-states',
        color='g2211_total_spend',
        color_continuous_scale='Blues',
        scope='usa',
        hover_data=['g2211_claims', 'attachment_rate', 'avg_g2211_payment'],
        labels={
            'g2211_total_spend': 'G2211 Spend ($)',
            'g2211_claims': 'G2211 Claims',
            'attachment_rate': 'Attach Rate'
        }
    )
    fig.update_layout(
        geo=dict(bgcolor='#f1f5f9', lakecolor='#dbeafe'),
        paper_bgcolor='#ffffff',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig
```

---

### 4.3 Provider Concentration — Pareto Chart (Row 1, Right)

**Chart Type**: Dual-axis bar + line combination chart.

**Data Source**: `provider_g2211_summary` view, top 25 providers by G2211 spend.

**Visual Spec**:
- **Bars** (left Y-axis): G2211 spend per provider, sorted descending, fill `#2563eb` (blue), border-radius `2px`
- **Line** (right Y-axis): Cumulative percentage of total G2211 spend, color `#f97316` (orange), stroke width `2.5px`, dots at each point
- **80% threshold**: Red dashed horizontal line at 80% on the right axis, label "80% threshold" in red
- X-axis: Provider NPI labels, rotated 45 degrees, font size 7px
- Left Y-axis: Dollar amounts (e.g., `$400`, `$800`)
- Right Y-axis: Percentage (e.g., `20%`, `40%`, `60%`, `80%`, `100%`)

**Tooltip on Hover (per bar)**:
```
Provider: {NPI}
G2211 Spend: ${spend}
G2211 Claims: {count}
Cumulative %: {cum_pct}%
```

**Purpose**: Shows whether a small number of providers drive the majority of G2211 spend. If the orange line crosses the 80% mark before 20% of providers, you have high concentration risk.

**Databricks Python code**:

```python
import plotly.graph_objects as go

def render_pareto(provider_df):
    top25 = provider_df.nlargest(25, 'g2211_total_spend').copy()
    total_spend = top25['g2211_total_spend'].sum()
    top25['cum_pct'] = top25['g2211_total_spend'].cumsum() / total_spend

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top25['provider_npi'], y=top25['g2211_total_spend'],
        name='G2211 Spend', marker_color='#2563eb', opacity=0.8,
        yaxis='y'
    ))
    fig.add_trace(go.Scatter(
        x=top25['provider_npi'], y=top25['cum_pct'],
        name='Cumulative %', line=dict(color='#f97316', width=2.5),
        marker=dict(size=5, color='#f97316'), yaxis='y2'
    ))
    fig.add_hline(y=0.8, line_dash='dash', line_color='#dc2626',
                  annotation_text='80% threshold', yref='y2')

    fig.update_layout(
        yaxis=dict(title='G2211 Spend ($)', side='left'),
        yaxis2=dict(title='Cumulative %', overlaying='y', side='right',
                    tickformat='.0%', range=[0, 1.05]),
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        xaxis=dict(tickangle=-45)
    )
    return fig
```

---

### 4.4 Provider Outlier Detection — Scatter Plot (Row 2, Left)

**Chart Type**: Bubble scatter plot.

**Data Source**: `provider_g2211_summary` view — one dot per provider.

**Visual Spec**:
- **X-axis**: Total E/M claim volume per provider (linear scale)
- **Y-axis**: G2211 attachment rate (0% to max, formatted as percentage)
- **Bubble size**: Proportional to G2211 total spend (square-root scale, range 3px–16px radius)
- **Bubble color**: Mapped to provider specialty using a categorical color palette
- **Audit Risk Zone**: Semi-transparent red rectangle above 40% attachment rate, with red dashed line at 40% and label "AUDIT RISK ZONE (>40%)" in red bold text
- Outlier providers (rate > 40%) should have a **red stroke border** (2.5px) around the bubble

**Color Palette for Specialties** (15 specialties):

| Specialty | Color |
|---|---|
| Family Medicine | `#2563eb` |
| Internal Medicine | `#f97316` |
| Cardiology | `#16a34a` |
| Endocrinology | `#dc2626` |
| Pulmonology | `#7c3aed` |
| Neurology | `#0891b2` |
| Rheumatology | `#d97706` |
| Gastroenterology | `#be185d` |
| Nephrology | `#4f46e5` |
| Dermatology | `#059669` |
| Orthopedics | `#e11d48` |
| Urology | `#0284c7` |
| Ophthalmology | `#ca8a04` |
| General Surgery | `#9333ea` |
| Anesthesiology | `#64748b` |

**Tooltip on Hover**:
```
Provider: {NPI} · {Specialty}
State: {state}
Total E/M: {count}
G2211 Claims: {g2211_count}
Attachment Rate: {rate}%
G2211 Spend: ${spend}
[If rate > 40%]: ⚠ OUTLIER FLAG
```

**Databricks Python code**:

```python
import plotly.express as px

def render_outlier_scatter(provider_df):
    fig = px.scatter(
        provider_df,
        x='total_em_claims',
        y='g2211_attachment_rate',
        size='g2211_total_spend',
        color='provider_specialty',
        hover_data=['provider_npi', 'provider_state', 'g2211_claims', 'g2211_denial_rate'],
        labels={
            'total_em_claims': 'Total E/M Volume',
            'g2211_attachment_rate': 'G2211 Attachment Rate',
            'g2211_total_spend': 'G2211 Spend'
        },
        size_max=30
    )
    # Add 40% audit risk zone
    fig.add_hrect(y0=0.4, y1=1.0, fillcolor='#dc2626', opacity=0.06,
                  annotation_text='AUDIT RISK ZONE (>40%)',
                  annotation_position='top right',
                  annotation_font_color='#dc2626')
    fig.add_hline(y=0.4, line_dash='dash', line_color='#dc2626', opacity=0.5)

    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        yaxis=dict(tickformat='.0%')
    )
    return fig
```

---

### 4.5 Specialty x State Heatmap (Row 2, Right)

**Chart Type**: 2D grid heatmap.

**Data Source**: `specialty_state_heatmap` view.

**Visual Spec**:
- **Rows**: Top 10 specialties by volume (Family Medicine, Internal Medicine, Cardiology, Endocrinology, Pulmonology, Neurology, Rheumatology, Gastroenterology, Nephrology, Dermatology)
- **Columns**: Top 12 states by total claims volume
- **Cell color**: Sequential **orange scale** (`d3.interpolateOranges`) mapped to G2211 attachment rate
- **Cell text**: Attachment rate as percentage (e.g., `12.5%`), white text for rates >15%, gray text for rates <=15%
- Empty cells (no data): fill `#f8fafc`
- Cell corner radius: `3px`

**Tooltip on Hover**:
```
{Specialty} — {State}
Attachment Rate: {rate}%
Total E/M: {count}
G2211 Claims: {g2211_count}
```

**Databricks Python code**:

```python
import plotly.express as px

def render_heatmap(heatmap_df, top_specs, top_states):
    pivot = heatmap_df.pivot(
        index='provider_specialty',
        columns='provider_state',
        values='attachment_rate'
    ).fillna(0)
    pivot = pivot.loc[
        [s for s in top_specs if s in pivot.index],
        [s for s in top_states if s in pivot.columns]
    ]

    fig = px.imshow(
        pivot,
        color_continuous_scale='Oranges',
        text_auto='.1%',
        labels=dict(color='Attachment Rate'),
        aspect='auto'
    )
    fig.update_layout(
        paper_bgcolor='#ffffff',
        xaxis_title='State',
        yaxis_title='Specialty'
    )
    return fig
```

---

### 4.6 Payer Denial Analysis — Stacked Bar (Row 3, Left)

**Chart Type**: Grouped bar chart (not stacked — side by side).

**Data Source**: `payer_denial_summary` view.

**Visual Spec**:
- **X-axis**: Two categories — `Medicare`, `Medicaid`
- **Two bars per category**: `Paid Claims` (blue `#2563eb`) and `Denied Claims` (red `#dc2626`)
- Bar border radius: `4px`
- Bar percentage width: `60%` of available space

**Legend below chart** showing:
```
Medicare: {denial_rate}% denial · Avg ${avg_paid}/claim
Medicaid: {denial_rate}% denial · Avg ${avg_paid}/claim
```

Color the denial rate tag green if <20%, red if >=20%.

**Expected patterns in real data**:
- Medicare denial rate: ~5-8%
- Medicaid denial rate: ~18-45% (varies dramatically by state)
- Medicare avg G2211 payment: ~$15-$17
- Medicaid avg G2211 payment: ~$10-$14

**Databricks Python code**:

```python
import plotly.graph_objects as go

def render_payer_denial(payer_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=payer_df['payer_type'],
        y=payer_df['paid_claims'],
        name='Paid Claims',
        marker_color='#2563eb'
    ))
    fig.add_trace(go.Bar(
        x=payer_df['payer_type'],
        y=payer_df['denied_claims'],
        name='Denied Claims',
        marker_color='#dc2626'
    ))
    fig.update_layout(
        barmode='group',
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        yaxis=dict(gridcolor='#e2e8f0'),
        legend=dict(orientation='h', y=-0.15)
    )
    return fig
```

---

### 4.7 Monthly Utilization Trend — Multi-Line Chart (Row 3, Right)

**Chart Type**: Multi-series line chart.

**Data Source**: `monthly_g2211_trend` view.

**Visual Spec**:
- **X-axis**: Month (format `YYYY-MM`), from `2024-01` onward
- **Y-axis**: G2211 attachment rate as percentage (e.g., 5%, 10%, 15%)
- **Three lines**, one per specialty group:
  - **Primary Care**: Blue `#2563eb`, solid line, 2.5px width
  - **Medical Subspecialty**: Orange `#f97316`, solid line, 2.5px width
  - **Surgical / Other**: Gray `#64748b`, solid line, 2.5px width
- Curve tension: `0.4` (smooth monotone)
- Point radius: `1.5px`
- Legend at top

**Specialty Group Definitions**:

| Group | Specialties Included |
|---|---|
| Primary Care | Family Medicine, Internal Medicine |
| Medical Subspecialty | Cardiology, Endocrinology, Pulmonology, Neurology, Rheumatology, Gastroenterology, Nephrology |
| Surgical / Other | Dermatology, Orthopedics, Urology, Ophthalmology, General Surgery, Anesthesiology |

**Expected pattern**: S-curve adoption — low in early 2024, rising through 2024-2025, with Primary Care consistently highest. Key inflection points:
- **Jan 2024**: G2211 launch (expect low numbers)
- **Jan 2025**: Modifier 25 expansion (expect acceleration)
- **Jan 2026**: Home visit expansion (expect further acceleration)

**Databricks Python code**:

```python
import plotly.express as px

def render_trend(trend_df):
    fig = px.line(
        trend_df,
        x='service_month',
        y='attachment_rate',
        color='specialty_group',
        color_discrete_map={
            'Primary Care': '#2563eb',
            'Medical Subspecialty': '#f97316',
            'Surgical / Other': '#64748b'
        },
        labels={
            'attachment_rate': 'Attachment Rate %',
            'service_month': 'Month'
        }
    )
    fig.update_traces(line=dict(width=2.5))
    # Add policy date vertical lines
    for dt, label in [('2024-01', 'G2211 Launch'),
                       ('2025-01', 'Mod-25 Expansion'),
                       ('2026-01', 'Home Visit Expansion')]:
        fig.add_vline(x=dt, line_dash='dot', line_color='#94a3b8',
                      annotation_text=label, annotation_position='top')
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        yaxis=dict(tickformat='.1%', gridcolor='#e2e8f0'),
        xaxis=dict(gridcolor='#e2e8f0')
    )
    return fig
```

---

## 5. Interactive Filters

The dashboard must support four global filters that re-render all 7 panels when changed:

| Filter | Options | Default |
|---|---|---|
| State | All States + each distinct state in data | All States |
| Specialty | All Specialties + each distinct specialty | All Specialties |
| Payer | All Payers, Medicare, Medicaid | All Payers |
| Year | All Years, 2024, 2025, 2026 | All Years |

When a filter is applied, re-query all views with a `WHERE` clause or filter the in-memory DataFrame.

---

## 6. Databricks Notebook Structure

Organize the Databricks project as follows:

```
g2211-provider-risk-dashboard/
├── README.md                          # This file
├── notebooks/
│   ├── 01_data_ingestion.py           # Load CSV/Parquet claims data
│   ├── 02_data_preparation.py         # Create derived columns and views
│   ├── 03_kpi_calculations.py         # Compute all KPI metrics
│   ├── 04_chart_geo_heatmap.py        # US state choropleth
│   ├── 05_chart_pareto.py             # Provider Pareto analysis
│   ├── 06_chart_outlier_scatter.py    # Provider outlier detection
│   ├── 07_chart_specialty_heatmap.py  # Specialty x State grid
│   ├── 08_chart_payer_denial.py       # Medicare vs Medicaid denial
│   ├── 09_chart_trend.py             # Monthly utilization trend
│   └── 10_dashboard_assembly.py       # Combine all into dashboard
├── sql/
│   ├── create_views.sql               # All SQL view definitions
│   └── validation_queries.sql         # Data quality checks
├── config/
│   ├── theme.json                     # Color/font theme config
│   └── fips_mapping.csv               # State to FIPS code lookup
├── output/
│   └── g2211_dashboard.html           # Exported HTML dashboard
└── tests/
    └── test_data_quality.py           # Data validation tests
```

---

## 7. GitHub Repository Setup

### 7.1 Create the repo

```bash
gh repo create g2211-provider-risk-dashboard --private --description "G2211 CPT Provider Profiling & Concentration Risk - Actuarial Dashboard" --clone
cd g2211-provider-risk-dashboard
```

### 7.2 Create directory structure

```bash
mkdir -p notebooks sql config output tests
```

### 7.3 Copy reference files

```bash
# Copy the working HTML dashboard as reference
cp /path/to/g2211_provider_risk_dashboard.html output/

# Copy this guide
cp /path/to/G2211_DASHBOARD_BUILD_GUIDE.md README.md
```

### 7.4 Theme config file

Create `config/theme.json`:

```json
{
  "colors": {
    "background": "#f1f5f9",
    "card": "#ffffff",
    "border": "#e2e8f0",
    "primary": "#2563eb",
    "primary_light": "#dbeafe",
    "secondary": "#f97316",
    "secondary_light": "#fff7ed",
    "success": "#16a34a",
    "danger": "#dc2626",
    "warning": "#d97706",
    "text": "#0f172a",
    "muted": "#64748b",
    "light": "#94a3b8"
  },
  "fonts": {
    "body": "DM Sans",
    "mono": "JetBrains Mono"
  },
  "specialty_colors": {
    "Family Medicine": "#2563eb",
    "Internal Medicine": "#f97316",
    "Cardiology": "#16a34a",
    "Endocrinology": "#dc2626",
    "Pulmonology": "#7c3aed",
    "Neurology": "#0891b2",
    "Rheumatology": "#d97706",
    "Gastroenterology": "#be185d",
    "Nephrology": "#4f46e5",
    "Dermatology": "#059669",
    "Orthopedics": "#e11d48",
    "Urology": "#0284c7",
    "Ophthalmology": "#ca8a04",
    "General Surgery": "#9333ea",
    "Anesthesiology": "#64748b"
  },
  "specialty_groups": {
    "Primary Care": ["Family Medicine", "Internal Medicine"],
    "Medical Subspecialty": ["Cardiology", "Endocrinology", "Pulmonology", "Neurology", "Rheumatology", "Gastroenterology", "Nephrology"],
    "Surgical / Other": ["Dermatology", "Orthopedics", "Urology", "Ophthalmology", "General Surgery", "Anesthesiology"]
  },
  "group_colors": {
    "Primary Care": "#2563eb",
    "Medical Subspecialty": "#f97316",
    "Surgical / Other": "#64748b"
  }
}
```

### 7.5 FIPS mapping file

Create `config/fips_mapping.csv`:

```csv
state,fips,state_name
AL,01,Alabama
AK,02,Alaska
AZ,04,Arizona
AR,05,Arkansas
CA,06,California
CO,08,Colorado
CT,09,Connecticut
DE,10,Delaware
FL,12,Florida
GA,13,Georgia
HI,15,Hawaii
ID,16,Idaho
IL,17,Illinois
IN,18,Indiana
IA,19,Iowa
KS,20,Kansas
KY,21,Kentucky
LA,22,Louisiana
ME,23,Maine
MD,24,Maryland
MA,25,Massachusetts
MI,26,Michigan
MN,27,Minnesota
MS,28,Mississippi
MO,29,Missouri
MT,30,Montana
NE,31,Nebraska
NV,32,Nevada
NH,33,New Hampshire
NJ,34,New Jersey
NM,35,New Mexico
NY,36,New York
NC,37,North Carolina
ND,38,North Dakota
OH,39,Ohio
OK,40,Oklahoma
OR,41,Oregon
PA,42,Pennsylvania
RI,44,Rhode Island
SC,45,South Carolina
SD,46,South Dakota
TN,47,Tennessee
TX,48,Texas
UT,49,Utah
VT,50,Vermont
VA,51,Virginia
WA,53,Washington
WV,54,West Virginia
WI,55,Wisconsin
WY,56,Wyoming
```

### 7.6 Git workflow

```bash
git add .
git commit -m "Initial G2211 provider risk dashboard - data schema, SQL views, chart specs, theme config"
git push -u origin main
```

---

## 8. Data Quality Checks

Run these validation queries before building charts:

```sql
-- 1. Verify G2211 claims exist
SELECT COUNT(*) AS g2211_count FROM claims WHERE cpt_code = 'G2211';
-- Expected: > 0

-- 2. Check payer distribution
SELECT payer_type, COUNT(*) AS cnt
FROM claims GROUP BY payer_type;
-- Expected: Medicare and Medicaid only

-- 3. Verify date range
SELECT MIN(date_of_service) AS min_date, MAX(date_of_service) AS max_date
FROM claims;
-- Expected: starts 2024-01-01

-- 4. Check for orphan G2211 (no matching E/M on same date/provider)
SELECT COUNT(*) FROM claims c1
WHERE c1.cpt_code = 'G2211'
AND NOT EXISTS (
  SELECT 1 FROM claims c2
  WHERE c2.provider_npi = c1.provider_npi
    AND c2.date_of_service = c1.date_of_service
    AND c2.cpt_code IN ('99202','99203','99204','99205',
                         '99211','99212','99213','99214','99215')
);
-- Expected: 0 (G2211 should always pair with an E/M code)

-- 5. Check for unusually high attachment rates by provider
SELECT provider_npi, provider_specialty, provider_state,
       COUNT(*) AS total,
       SUM(CASE WHEN cpt_code = 'G2211' THEN 1 ELSE 0 END) AS g2211,
       SUM(CASE WHEN cpt_code = 'G2211' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct
FROM claims
GROUP BY provider_npi, provider_specialty, provider_state
HAVING COUNT(*) > 50
ORDER BY pct DESC
LIMIT 20;
-- Review: flag providers with > 40% for audit review
```

---

## 9. Key Actuarial Benchmarks

Use these benchmarks from industry research to validate your data:

| Metric | National Benchmark (2024-2025) | Source |
|---|---|---|
| G2211 attachment rate (all specialties) | 5.2% of eligible E/M | ECG Management Consultants |
| % of physicians billing G2211 | 36% | ECG Management Consultants |
| Among billers, avg attachment rate | 14.5% of their E/M volume | ECG Management Consultants |
| Medicare avg G2211 payment | $15.53 (2025 national avg) | CMS Fee Schedule |
| G2211 RVU total | 0.48 (0.33 work + 0.13 PE + 0.02 MP) | CMS |
| Medicare denial rate for G2211 | ~5-8% | Industry reports |
| Medicare Advantage denial rate | ~30-40% | Industry reports |
| Medicaid denial rate (adopting states) | ~15-25% | Estimated |
| Medicaid denial rate (non-adopting states) | ~40-60% | Estimated |
| CMS projected attachment rate | 38-54% | CMS 2024 MPFS |
| Budget neutrality CF impact from G2211 | -2.20% (90% attributable to G2211) | ASA |

**States known to cover G2211 under Medicaid** (reference Medicare fee schedule): CA, NY, MA, WA, IL, PA, NJ, MD, WI, MI. Verify against your actual claims data.

---

## 10. Reference: Working HTML Dashboard

A fully functional single-file HTML dashboard with synthetic demo data is included at:

```
output/g2211_provider_risk_dashboard.html
```

This file uses the exact chart types, color theme, layout, and interaction patterns described in this guide. Open it in any browser to see the target output. The Databricks build should produce charts that match this reference visually.
