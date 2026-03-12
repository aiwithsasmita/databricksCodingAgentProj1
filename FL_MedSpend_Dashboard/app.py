import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from data_generator import (
    generate_claims_data,
    generate_prediction_data,
    get_summary_kpis,
    CLINICAL_CLUSTERS,
    FLORIDA_REGIONS,
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
DF = generate_claims_data()
PRED_DF = generate_prediction_data(DF)
KPIS = get_summary_kpis(DF)

CLUSTER_COLORS = {k: v["color"] for k, v in CLINICAL_CLUSTERS.items()}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SLATE, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="FL Med Spend — Actuarial Dashboard",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_dollar(v):
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    if v >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def fmt_number(v):
    if v >= 1e6:
        return f"{v / 1e6:.1f}M"
    if v >= 1e3:
        return f"{v / 1e3:.0f}K"
    return f"{v:,.0f}"


def kpi_card(title, value, subtitle="", icon="fa-solid fa-dollar-sign", color="#00d2ff"):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.I(className=f"{icon} fa-lg", style={"color": color}),
                    html.Span(title, className="ms-2",
                              style={"fontSize": "0.78rem", "textTransform": "uppercase",
                                     "letterSpacing": "1px", "opacity": 0.7}),
                ], className="d-flex align-items-center mb-2"),
                html.H3(value, className="mb-0", style={"fontWeight": 700, "color": color}),
                html.Small(subtitle, style={"opacity": 0.6}) if subtitle else None,
            ]),
            className="shadow-sm",
            style={"borderTop": f"3px solid {color}", "borderRadius": "10px"},
        ),
        xs=12, sm=6, md=4, lg=True, className="mb-3",
    )


CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cfd8e3", family="Inter, Segoe UI, sans-serif"),
    margin=dict(l=50, r=30, t=50, b=50),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
)


def styled_fig(fig):
    fig.update_layout(**CHART_LAYOUT)
    return fig

# ---------------------------------------------------------------------------
# KPI Row
# ---------------------------------------------------------------------------
kpi_row = dbc.Row([
    kpi_card("Total Paid (2025)", fmt_dollar(KPIS["total_paid"]),
             f"YoY: {KPIS['yoy_change']:+.1f}%", "fa-solid fa-sack-dollar", "#00d2ff"),
    kpi_card("Avg PMPM", fmt_dollar(KPIS["avg_pmpm"]),
             "Per Member Per Month", "fa-solid fa-user-dollar", "#36d399"),
    kpi_card("Members (monthly avg)", fmt_number(KPIS["total_members"]),
             "Unique members", "fa-solid fa-users", "#f59e0b"),
    kpi_card("Total Claims", fmt_number(KPIS["total_claims"]),
             "2025 claim volume", "fa-solid fa-file-medical", "#a78bfa"),
    kpi_card("High-Cost Claimants", fmt_number(KPIS["high_cost_claimants"]),
             "Stop-loss eligible", "fa-solid fa-triangle-exclamation", "#fb7185"),
    kpi_card("Avg Risk Score", f"{KPIS['avg_risk_score']:.2f}",
             "HCC-equivalent", "fa-solid fa-shield-heart", "#38bdf8"),
], className="g-3 mb-4")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
filter_bar = dbc.Card(
    dbc.CardBody(
        dbc.Row([
            dbc.Col([
                dbc.Label("Year", className="small mb-1"),
                dcc.Dropdown(
                    id="filter-year",
                    options=[{"label": str(y), "value": y} for y in sorted(DF["year"].unique())],
                    value=DF["year"].max(),
                    clearable=False,
                    className="dash-bootstrap",
                ),
            ], md=2),
            dbc.Col([
                dbc.Label("Region", className="small mb-1"),
                dcc.Dropdown(
                    id="filter-region",
                    options=[{"label": "All Regions", "value": "ALL"}]
                        + [{"label": r, "value": r} for r in sorted(DF["region"].unique())],
                    value="ALL",
                    clearable=False,
                ),
            ], md=2),
            dbc.Col([
                dbc.Label("Clinical Cluster", className="small mb-1"),
                dcc.Dropdown(
                    id="filter-cluster",
                    options=[{"label": "All Clusters", "value": "ALL"}]
                        + [{"label": c, "value": c} for c in sorted(DF["clinical_cluster"].unique())],
                    value="ALL",
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("Provider Type", className="small mb-1"),
                dcc.Dropdown(
                    id="filter-ptype",
                    options=[{"label": "All Types", "value": "ALL"}]
                        + [{"label": t, "value": t} for t in sorted(DF["provider_type"].unique())],
                    value="ALL",
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("Quarter", className="small mb-1"),
                dcc.Dropdown(
                    id="filter-quarter",
                    options=[{"label": "All Quarters", "value": "ALL"}] +
                            [{"label": q, "value": q} for q in ["Q1", "Q2", "Q3", "Q4"]],
                    value="ALL",
                    clearable=False,
                ),
            ], md=2),
        ], className="g-2"),
    ),
    className="mb-4 shadow-sm",
    style={"borderRadius": "10px"},
)

# ---------------------------------------------------------------------------
# Tab definitions
# ---------------------------------------------------------------------------
tab_style = {"padding": "8px 20px", "fontWeight": 500, "fontSize": "0.88rem"}
tab_selected_style = {**tab_style, "borderTop": "3px solid #00d2ff", "fontWeight": 700}

tabs = dcc.Tabs(
    id="main-tabs",
    value="overview",
    children=[
        dcc.Tab(label="Overview", value="overview", style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="Provider Analysis", value="provider", style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="Clinical Clusters", value="clusters", style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="Trend & Forecast", value="trend", style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="Utilization & Risk", value="utilization", style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="PMPM Deep Dive", value="pmpm", style=tab_style, selected_style=tab_selected_style),
    ],
    className="mb-4",
)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app.layout = dbc.Container([
    # Header
    html.Div([
        html.Div([
            html.I(className="fa-solid fa-heartbeat fa-2x me-3", style={"color": "#00d2ff"}),
            html.Div([
                html.H2("Florida Medical Spend Dashboard", className="mb-0",
                         style={"fontWeight": 800, "letterSpacing": "-0.5px"}),
                html.P("Actuarial & Economic Predictive Analytics  |  425-Field Claims Intelligence",
                       className="mb-0", style={"opacity": 0.6, "fontSize": "0.85rem"}),
            ]),
        ], className="d-flex align-items-center"),
    ], className="py-3 mb-3", style={"borderBottom": "1px solid rgba(255,255,255,0.08)"}),

    kpi_row,
    filter_bar,
    tabs,
    html.Div(id="tab-content"),
], fluid=True, className="px-4")


# ---------------------------------------------------------------------------
# Filter helper
# ---------------------------------------------------------------------------
def apply_filters(df, year, region, cluster, ptype, quarter):
    out = df[df["year"] == year]
    if region != "ALL":
        out = out[out["region"] == region]
    if cluster != "ALL":
        out = out[out["clinical_cluster"] == cluster]
    if ptype != "ALL":
        out = out[out["provider_type"] == ptype]
    if quarter != "ALL":
        out = out[out["quarter"] == quarter]
    return out


# ===================================================================
# CHART BUILDERS
# ===================================================================

def build_overview(fdf):
    # -- Monthly spend trend --
    monthly = fdf.groupby("month")["total_paid"].sum().reset_index()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["total_paid"],
        mode="lines+markers", fill="tozeroy",
        line=dict(color="#00d2ff", width=2.5),
        marker=dict(size=5),
        fillcolor="rgba(0,210,255,0.08)",
    ))
    fig_trend.update_layout(title="Monthly Total Paid Trend", yaxis_title="Total Paid ($)",
                            xaxis_title="", height=350)
    styled_fig(fig_trend)

    # -- Cluster donut --
    cluster_spend = fdf.groupby("clinical_cluster")["total_paid"].sum().reset_index()
    cluster_spend = cluster_spend.sort_values("total_paid", ascending=False)
    fig_donut = go.Figure(go.Pie(
        labels=cluster_spend["clinical_cluster"],
        values=cluster_spend["total_paid"],
        hole=0.55,
        marker=dict(colors=[CLUSTER_COLORS.get(c, "#888") for c in cluster_spend["clinical_cluster"]]),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig_donut.update_layout(title="Spend by Clinical Cluster", height=400, showlegend=False)
    styled_fig(fig_donut)

    # -- Region bar --
    region_spend = fdf.groupby("region")["total_paid"].sum().reset_index().sort_values("total_paid")
    fig_region = go.Figure(go.Bar(
        y=region_spend["region"], x=region_spend["total_paid"],
        orientation="h",
        marker=dict(color=region_spend["total_paid"],
                    colorscale=[[0, "#1a1a2e"], [0.5, "#00d2ff"], [1, "#36d399"]]),
        text=[fmt_dollar(v) for v in region_spend["total_paid"]],
        textposition="auto",
    ))
    fig_region.update_layout(title="Total Paid by Region", xaxis_title="Total Paid ($)", height=350)
    styled_fig(fig_region)

    # -- Provider type bar --
    ptype_spend = fdf.groupby("provider_type")["total_paid"].sum().reset_index().sort_values("total_paid")
    fig_ptype = go.Figure(go.Bar(
        y=ptype_spend["provider_type"], x=ptype_spend["total_paid"],
        orientation="h",
        marker=dict(color=["#a78bfa", "#f59e0b", "#fb7185", "#36d399"][:len(ptype_spend)]),
        text=[fmt_dollar(v) for v in ptype_spend["total_paid"]],
        textposition="auto",
    ))
    fig_ptype.update_layout(title="Spend by Provider Type", xaxis_title="Total Paid ($)", height=300)
    styled_fig(fig_ptype)

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_trend), lg=7),
            dbc.Col(dcc.Graph(figure=fig_donut), lg=5),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_region), lg=6),
            dbc.Col(dcc.Graph(figure=fig_ptype), lg=6),
        ]),
    ])


def build_provider(fdf):
    # -- Top 15 providers by total paid --
    top = fdf.groupby("provider_name").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
        claim_count=("claim_count", "sum"),
        avg_risk=("avg_risk_score", "mean"),
    ).reset_index().nlargest(15, "total_paid")

    fig_top = go.Figure(go.Bar(
        x=top["total_paid"],
        y=top["provider_name"],
        orientation="h",
        marker=dict(
            color=top["total_paid"],
            colorscale=[[0, "#0f3460"], [0.5, "#00d2ff"], [1, "#36d399"]],
        ),
        text=[fmt_dollar(v) for v in top["total_paid"]],
        textposition="auto",
        textfont=dict(size=11),
    ))
    fig_top.update_layout(title="Top 15 Providers by Total Paid", height=550,
                          yaxis=dict(autorange="reversed"), xaxis_title="Total Paid ($)")
    styled_fig(fig_top)

    # -- Provider scatter: spend vs members (bubble=risk) --
    prov_agg = fdf.groupby("provider_name").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
        avg_risk=("avg_risk_score", "mean"),
        provider_type=("provider_type", "first"),
    ).reset_index()
    prov_agg["provider_type"] = prov_agg["provider_type"].astype(str)

    fig_scatter = px.scatter(
        prov_agg, x="member_count", y="total_paid", size="avg_risk",
        color="provider_type", hover_name="provider_name",
        labels={"total_paid": "Total Paid ($)", "member_count": "Total Members",
                "avg_risk": "Avg Risk Score"},
        title="Provider Efficiency: Spend vs Members (bubble = risk score)",
        height=450,
        color_discrete_sequence=["#00d2ff", "#36d399", "#f59e0b", "#fb7185"],
    )
    styled_fig(fig_scatter)

    # -- Provider cluster heatmap --
    prov_cluster = fdf.groupby(["provider_name", "clinical_cluster"])["total_paid"].sum().reset_index()
    top10_providers = fdf.groupby("provider_name")["total_paid"].sum().nlargest(10).index
    prov_cluster_top = prov_cluster[prov_cluster["provider_name"].isin(top10_providers)]
    pivot = prov_cluster_top.pivot_table(index="provider_name", columns="clinical_cluster",
                                         values="total_paid", fill_value=0)

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=[[0, "#0f0f23"], [0.3, "#1a1a4e"], [0.6, "#00d2ff"], [1, "#36d399"]],
        text=[[fmt_dollar(v) for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=9),
    ))
    fig_heat.update_layout(title="Top 10 Providers × Clinical Cluster Heatmap", height=450,
                           xaxis=dict(tickangle=-35))
    styled_fig(fig_heat)

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_top), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_scatter), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_heat))]),
    ])


def build_clusters(fdf):
    # -- Cluster bar chart (sorted) --
    cl = fdf.groupby("clinical_cluster").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
        claim_count=("claim_count", "sum"),
    ).reset_index().sort_values("total_paid", ascending=True)

    fig_bar = go.Figure(go.Bar(
        y=cl["clinical_cluster"], x=cl["total_paid"], orientation="h",
        marker=dict(color=[CLUSTER_COLORS.get(c, "#888") for c in cl["clinical_cluster"]]),
        text=[fmt_dollar(v) for v in cl["total_paid"]],
        textposition="auto",
    ))
    fig_bar.update_layout(title="Total Paid by Clinical Cluster", height=450, xaxis_title="Total Paid ($)")
    styled_fig(fig_bar)

    # -- Cluster treemap --
    fig_tree = px.treemap(
        cl.sort_values("total_paid", ascending=False),
        path=["clinical_cluster"],
        values="total_paid",
        color="total_paid",
        color_continuous_scale=[[0, "#1a1a2e"], [0.5, "#00d2ff"], [1, "#36d399"]],
        title="Cluster Spend Treemap",
        height=400,
    )
    fig_tree.update_traces(textinfo="label+value+percent root",
                           texttemplate="%{label}<br>%{value:$,.0f}<br>%{percentRoot:.1%}")
    styled_fig(fig_tree)

    # -- Cluster monthly trend (stacked area) --
    cl_monthly = fdf.groupby(["month", "clinical_cluster"])["total_paid"].sum().reset_index()
    fig_area = go.Figure()
    for cluster in sorted(CLINICAL_CLUSTERS.keys()):
        cd = cl_monthly[cl_monthly["clinical_cluster"] == cluster]
        fig_area.add_trace(go.Scatter(
            x=cd["month"], y=cd["total_paid"],
            mode="lines", stackgroup="one", name=cluster,
            line=dict(width=0.5, color=CLUSTER_COLORS.get(cluster, "#888")),
        ))
    fig_area.update_layout(title="Monthly Spend by Cluster (Stacked)", height=400,
                           yaxis_title="Total Paid ($)", legend=dict(font=dict(size=10)))
    styled_fig(fig_area)

    # -- Cluster member vs spend scatter --
    cl["clinical_cluster"] = cl["clinical_cluster"].astype(str)
    fig_cs = px.scatter(
        cl, x="member_count", y="total_paid", size="claim_count",
        color="clinical_cluster", hover_name="clinical_cluster",
        color_discrete_map=CLUSTER_COLORS,
        labels={"total_paid": "Total Paid ($)", "member_count": "Members", "claim_count": "Claims"},
        title="Cluster: Members vs Spend (bubble = claim count)",
        height=400,
    )
    styled_fig(fig_cs)

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_bar), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_tree), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_area), lg=7),
                 dbc.Col(dcc.Graph(figure=fig_cs), lg=5)]),
    ])


def build_trend(fdf):
    # -- Actual + forecast --
    monthly_actual = DF.groupby(["month", "clinical_cluster"])["total_paid"].sum().reset_index()
    monthly_total = DF.groupby("month")["total_paid"].sum().reset_index()

    pred_total = PRED_DF.groupby("month").agg(
        predicted_paid=("predicted_paid", "sum"),
        lower_bound=("lower_bound", "sum"),
        upper_bound=("upper_bound", "sum"),
    ).reset_index()

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=monthly_total["month"], y=monthly_total["total_paid"],
        mode="lines+markers", name="Actual", line=dict(color="#00d2ff", width=2.5),
        marker=dict(size=4),
    ))
    fig_fc.add_trace(go.Scatter(
        x=pred_total["month"], y=pred_total["predicted_paid"],
        mode="lines+markers", name="Forecast 2026", line=dict(color="#f59e0b", width=2.5, dash="dash"),
        marker=dict(size=5, symbol="diamond"),
    ))
    fig_fc.add_trace(go.Scatter(
        x=pd.concat([pred_total["month"], pred_total["month"][::-1]]),
        y=pd.concat([pred_total["upper_bound"], pred_total["lower_bound"][::-1]]),
        fill="toself", fillcolor="rgba(245,158,11,0.1)",
        line=dict(width=0), name="Confidence Band", showlegend=True,
    ))
    fig_fc.update_layout(title="Total Paid — Actual vs 2026 Forecast (with Confidence Band)",
                         height=400, yaxis_title="Total Paid ($)")
    styled_fig(fig_fc)

    # -- YoY comparison by cluster --
    yoy = DF.groupby(["year", "clinical_cluster"])["total_paid"].sum().reset_index()
    yoy["clinical_cluster"] = yoy["clinical_cluster"].astype(str)
    yoy["year"] = yoy["year"].astype(str)
    fig_yoy = px.bar(
        yoy, x="clinical_cluster", y="total_paid", color="year",
        barmode="group", title="Year-over-Year Spend by Cluster",
        color_discrete_sequence=["#3b82f6", "#00d2ff", "#36d399"],
        labels={"total_paid": "Total Paid ($)", "clinical_cluster": "Cluster"},
        height=400,
    )
    fig_yoy.update_layout(xaxis_tickangle=-30)
    styled_fig(fig_yoy)

    # -- Quarterly growth rate heatmap --
    qtr = DF.groupby(["year", "quarter", "clinical_cluster"])["total_paid"].sum().reset_index()
    qtr["period"] = qtr["year"].astype(str) + " " + qtr["quarter"]
    pivot_q = qtr.pivot_table(index="clinical_cluster", columns="period", values="total_paid")
    growth = pivot_q.pct_change(axis=1) * 100
    growth = growth.iloc[:, 1:]

    fig_growth = go.Figure(go.Heatmap(
        z=growth.values, x=growth.columns, y=growth.index,
        colorscale=[[0, "#dc2626"], [0.5, "#1a1a2e"], [1, "#36d399"]],
        zmid=0,
        text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in growth.values],
        texttemplate="%{text}", textfont=dict(size=9),
    ))
    fig_growth.update_layout(title="Quarterly Growth Rate by Cluster (%)", height=420,
                             xaxis=dict(tickangle=-45))
    styled_fig(fig_growth)

    # -- Cluster-level forecast lines --
    fig_cl_fc = make_subplots(rows=3, cols=4,
                              subplot_titles=list(CLINICAL_CLUSTERS.keys()),
                              vertical_spacing=0.10, horizontal_spacing=0.06)
    for i, cluster in enumerate(CLINICAL_CLUSTERS.keys()):
        row, col = i // 4 + 1, i % 4 + 1
        cd = monthly_actual[monthly_actual["clinical_cluster"] == cluster]
        fig_cl_fc.add_trace(go.Scatter(
            x=cd["month"], y=cd["total_paid"],
            mode="lines", line=dict(color=CLUSTER_COLORS[cluster], width=1.5),
            showlegend=False,
        ), row=row, col=col)

        pd_c = PRED_DF[PRED_DF["clinical_cluster"] == cluster]
        if len(pd_c) > 0:
            fig_cl_fc.add_trace(go.Scatter(
                x=pd_c["month"], y=pd_c["predicted_paid"],
                mode="lines", line=dict(color="#f59e0b", width=1.5, dash="dot"),
                showlegend=False,
            ), row=row, col=col)

    fig_cl_fc.update_layout(title="Per-Cluster Forecast Sparklines", height=550)
    styled_fig(fig_cl_fc)
    fig_cl_fc.update_annotations(font_size=10)

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_fc))]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_yoy), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_growth), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_cl_fc))]),
    ])


def build_utilization(fdf):
    # -- Admits per 1000 by cluster --
    inpatient = fdf[fdf["bed_count"] > 0]
    admits = inpatient.groupby("clinical_cluster")["admits_per_1000"].mean().reset_index()
    admits = admits.sort_values("admits_per_1000", ascending=True)
    fig_admits = go.Figure(go.Bar(
        y=admits["clinical_cluster"], x=admits["admits_per_1000"], orientation="h",
        marker=dict(color=[CLUSTER_COLORS.get(c, "#888") for c in admits["clinical_cluster"]]),
    ))
    fig_admits.update_layout(title="Avg Admits / 1,000 by Cluster", height=380,
                             xaxis_title="Admits per 1,000")
    styled_fig(fig_admits)

    # -- ER visits per 1000 --
    er = fdf.groupby("clinical_cluster")["er_visits_per_1000"].mean().reset_index()
    er = er.sort_values("er_visits_per_1000", ascending=True)
    fig_er = go.Figure(go.Bar(
        y=er["clinical_cluster"], x=er["er_visits_per_1000"], orientation="h",
        marker=dict(color=[CLUSTER_COLORS.get(c, "#888") for c in er["clinical_cluster"]]),
    ))
    fig_er.update_layout(title="Avg ER Visits / 1,000 by Cluster", height=380,
                         xaxis_title="ER Visits per 1,000")
    styled_fig(fig_er)

    # -- Readmission rate radar --
    readmit = fdf.groupby("clinical_cluster")["readmission_rate"].mean().reset_index()
    readmit = readmit.sort_values("clinical_cluster")
    fig_radar = go.Figure(go.Scatterpolar(
        r=readmit["readmission_rate"] * 100,
        theta=readmit["clinical_cluster"],
        fill="toself",
        fillcolor="rgba(0,210,255,0.15)",
        line=dict(color="#00d2ff", width=2),
        marker=dict(size=6),
    ))
    fig_radar.update_layout(
        title="Readmission Rate by Cluster (%)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#cfd8e3"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#cfd8e3"),
        ),
        height=420,
    )
    styled_fig(fig_radar)

    # -- Risk score distribution --
    fig_risk = go.Figure()
    for cluster in sorted(CLINICAL_CLUSTERS.keys()):
        cd = fdf[fdf["clinical_cluster"] == cluster]
        fig_risk.add_trace(go.Box(
            y=cd["avg_risk_score"], name=cluster[:12],
            marker=dict(color=CLUSTER_COLORS.get(cluster, "#888")),
            line=dict(color=CLUSTER_COLORS.get(cluster, "#888")),
        ))
    fig_risk.update_layout(title="Risk Score Distribution by Cluster", height=400,
                           showlegend=False, yaxis_title="Risk Score")
    styled_fig(fig_risk)

    # -- High-cost claimant analysis --
    hc = fdf.groupby("clinical_cluster").agg(
        high_cost_claimants=("high_cost_claimants", "sum"),
        high_cost_amount=("high_cost_amount", "sum"),
        total_paid=("total_paid", "sum"),
    ).reset_index()
    hc["hc_pct"] = hc["high_cost_amount"] / hc["total_paid"] * 100
    hc = hc.sort_values("hc_pct", ascending=True)

    fig_hc = go.Figure()
    fig_hc.add_trace(go.Bar(
        y=hc["clinical_cluster"], x=hc["hc_pct"], orientation="h",
        marker=dict(color="#fb7185"), name="% High-Cost Spend",
    ))
    fig_hc.update_layout(title="High-Cost Claimant Spend as % of Total", height=380,
                         xaxis_title="% of Total Paid")
    styled_fig(fig_hc)

    # -- ALOS by cluster (hospital only) --
    alos = inpatient.groupby("clinical_cluster")["avg_length_of_stay"].mean().reset_index()
    alos = alos.sort_values("avg_length_of_stay", ascending=True)
    fig_alos = go.Figure(go.Bar(
        y=alos["clinical_cluster"], x=alos["avg_length_of_stay"], orientation="h",
        marker=dict(color=[CLUSTER_COLORS.get(c, "#888") for c in alos["clinical_cluster"]]),
    ))
    fig_alos.update_layout(title="Avg Length of Stay by Cluster (days)", height=380,
                           xaxis_title="Days")
    styled_fig(fig_alos)

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_admits), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_er), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_radar), lg=4),
                 dbc.Col(dcc.Graph(figure=fig_risk), lg=4),
                 dbc.Col(dcc.Graph(figure=fig_hc), lg=4)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_alos))]),
    ])


def build_pmpm(fdf):
    # -- PMPM by cluster --
    pmpm_cl = fdf.groupby("clinical_cluster").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
    ).reset_index()
    pmpm_cl["pmpm"] = pmpm_cl["total_paid"] / pmpm_cl["member_count"]
    pmpm_cl = pmpm_cl.sort_values("pmpm", ascending=True)

    fig_pmpm = go.Figure(go.Bar(
        y=pmpm_cl["clinical_cluster"], x=pmpm_cl["pmpm"], orientation="h",
        marker=dict(color=[CLUSTER_COLORS.get(c, "#888") for c in pmpm_cl["clinical_cluster"]]),
        text=[fmt_dollar(v) for v in pmpm_cl["pmpm"]],
        textposition="auto",
    ))
    fig_pmpm.update_layout(title="PMPM by Clinical Cluster", height=420, xaxis_title="PMPM ($)")
    styled_fig(fig_pmpm)

    # -- PMPM monthly trend --
    pmpm_monthly = fdf.groupby("month").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
    ).reset_index()
    pmpm_monthly["pmpm"] = pmpm_monthly["total_paid"] / pmpm_monthly["member_count"]

    fig_pmpm_trend = go.Figure()
    fig_pmpm_trend.add_trace(go.Scatter(
        x=pmpm_monthly["month"], y=pmpm_monthly["pmpm"],
        mode="lines+markers", fill="tozeroy",
        line=dict(color="#36d399", width=2.5),
        fillcolor="rgba(54,211,153,0.08)",
    ))
    z = np.polyfit(range(len(pmpm_monthly)), pmpm_monthly["pmpm"], 1)
    p = np.poly1d(z)
    fig_pmpm_trend.add_trace(go.Scatter(
        x=pmpm_monthly["month"], y=p(range(len(pmpm_monthly))),
        mode="lines", name="Trend Line",
        line=dict(color="#f59e0b", width=2, dash="dash"),
    ))
    fig_pmpm_trend.update_layout(title="Monthly PMPM Trend with Linear Fit", height=380,
                                  yaxis_title="PMPM ($)")
    styled_fig(fig_pmpm_trend)

    # -- PMPM by provider (top 15) --
    pmpm_prov = fdf.groupby("provider_name").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
    ).reset_index()
    pmpm_prov["pmpm"] = pmpm_prov["total_paid"] / pmpm_prov["member_count"]
    pmpm_prov = pmpm_prov.nlargest(15, "pmpm").sort_values("pmpm", ascending=True)

    fig_prov_pmpm = go.Figure(go.Bar(
        y=pmpm_prov["provider_name"], x=pmpm_prov["pmpm"], orientation="h",
        marker=dict(
            color=pmpm_prov["pmpm"],
            colorscale=[[0, "#0f3460"], [0.5, "#00d2ff"], [1, "#fb7185"]],
        ),
        text=[fmt_dollar(v) for v in pmpm_prov["pmpm"]],
        textposition="auto",
    ))
    fig_prov_pmpm.update_layout(title="PMPM — Top 15 Most Expensive Providers", height=500,
                                 xaxis_title="PMPM ($)")
    styled_fig(fig_prov_pmpm)

    # -- PMPM by region --
    pmpm_reg = fdf.groupby("region").agg(
        total_paid=("total_paid", "sum"),
        member_count=("member_count", "sum"),
    ).reset_index()
    pmpm_reg["pmpm"] = pmpm_reg["total_paid"] / pmpm_reg["member_count"]
    pmpm_reg = pmpm_reg.sort_values("pmpm")

    fig_reg_pmpm = go.Figure(go.Bar(
        y=pmpm_reg["region"], x=pmpm_reg["pmpm"], orientation="h",
        marker=dict(color=["#00d2ff", "#36d399", "#a78bfa", "#f59e0b",
                           "#fb7185", "#38bdf8", "#e879f9"][:len(pmpm_reg)]),
        text=[fmt_dollar(v) for v in pmpm_reg["pmpm"]],
        textposition="auto",
    ))
    fig_reg_pmpm.update_layout(title="PMPM by Florida Region", height=350, xaxis_title="PMPM ($)")
    styled_fig(fig_reg_pmpm)

    # -- Billed vs Allowed vs Paid waterfall --
    totals = fdf[["billed_amount", "allowed_amount", "total_paid", "member_cost_share"]].sum()
    fig_waterfall = go.Figure(go.Waterfall(
        x=["Billed", "Network Discount", "Allowed", "Plan Paid", "Member Cost Share"],
        y=[totals["billed_amount"],
           -(totals["billed_amount"] - totals["allowed_amount"]),
           0,
           totals["total_paid"],
           totals["member_cost_share"]],
        measure=["absolute", "relative", "total", "absolute", "absolute"],
        connector=dict(line=dict(color="rgba(255,255,255,0.1)")),
        decreasing=dict(marker=dict(color="#fb7185")),
        increasing=dict(marker=dict(color="#36d399")),
        totals=dict(marker=dict(color="#00d2ff")),
        text=[fmt_dollar(totals["billed_amount"]),
              fmt_dollar(totals["billed_amount"] - totals["allowed_amount"]),
              fmt_dollar(totals["allowed_amount"]),
              fmt_dollar(totals["total_paid"]),
              fmt_dollar(totals["member_cost_share"])],
        textposition="outside",
    ))
    fig_waterfall.update_layout(title="Billed → Allowed → Paid Waterfall", height=380,
                                 yaxis_title="Amount ($)")
    styled_fig(fig_waterfall)

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_pmpm), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_pmpm_trend), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_prov_pmpm), lg=6),
                 dbc.Col(dcc.Graph(figure=fig_reg_pmpm), lg=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_waterfall))]),
    ])


# ===================================================================
# CALLBACKS
# ===================================================================

@callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
    Input("filter-year", "value"),
    Input("filter-region", "value"),
    Input("filter-cluster", "value"),
    Input("filter-ptype", "value"),
    Input("filter-quarter", "value"),
)
def render_tab(tab, year, region, cluster, ptype, quarter):
    fdf = apply_filters(DF, year, region, cluster, ptype, quarter)
    if fdf.empty:
        return dbc.Alert("No data matches the selected filters.", color="warning", className="mt-4")

    builders = {
        "overview": build_overview,
        "provider": build_provider,
        "clusters": build_clusters,
        "trend": build_trend,
        "utilization": build_utilization,
        "pmpm": build_pmpm,
    }
    return builders.get(tab, build_overview)(fdf)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)
