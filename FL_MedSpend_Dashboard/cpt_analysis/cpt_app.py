"""
CPT Cost Driver & Early Warning Dashboard
UnitedHealthcare / Optum branded — 8-tab Dash application.
Demo-ready: no risk_score dependency.
"""

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import base64, pathlib

from .cpt_data_generator import generate_cpt_claims
from .cpt_reference import get_cpt_reference, get_states_reference, CATEGORIES
from .cost_decomposition import (
    uchi_decomposition_by_category, cpt_level_yoy, cost_waterfall,
)
from .early_warning import trend_acceleration, zscore_flags, cusum
from .forecasting import (
    forecast_total_spend, forecast_by_category, scenario_analysis,
)

# ═══════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════
print("Generating CPT claims data …")
DF = generate_cpt_claims()
CPT_REF = get_cpt_reference()
STATES_REF = get_states_reference()
print(f"Ready — {len(DF):,} claim rows (no risk-score computation needed)")

# ── UHC / Optum Color Palette ────────────────────────────────────────
UHC_BLUE       = "#002677"
UHC_BLUE_LT    = "#0065B8"
UHC_BLUE_PALE  = "#E8F0FE"
OPTUM_ORANGE   = "#FF612B"
OPTUM_ORANGE_LT= "#FFA07A"
GRAY_800       = "#1E293B"
GRAY_600       = "#475569"
GRAY_200       = "#E2E8F0"
WHITE          = "#FFFFFF"

CAT_COLORS = {
    "E&M": UHC_BLUE, "Surgery": "#D32F2F", "Radiology": "#7B1FA2",
    "Lab": "#2E7D32", "Medicine": OPTUM_ORANGE, "Anesthesia": UHC_BLUE_LT,
    "DME/Supply": "#6A1B9A", "Behavioral Health": "#E65100",
}

# ── Logo ─────────────────────────────────────────────────────────────
ASSETS = pathlib.Path(__file__).parent / "assets"
LOGO_PATH = ASSETS / "uhc_logo.png"
if LOGO_PATH.exists():
    LOGO_B64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    LOGO_SRC = f"data:image/png;base64,{LOGO_B64}"
else:
    LOGO_SRC = ""

# ═══════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════
app = dash.Dash(
    __name__,
    assets_folder=str(ASSETS),
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="UHC — CPT Cost Driver & Early Warning",
)

CHART = dict(
    paper_bgcolor=WHITE, plot_bgcolor=WHITE,
    font=dict(color=GRAY_800, family="Segoe UI, Inter, sans-serif", size=12),
    margin=dict(l=55, r=30, t=55, b=50),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor=GRAY_200, borderwidth=1),
    xaxis=dict(gridcolor=GRAY_200, linecolor=GRAY_200, zerolinecolor=GRAY_200),
    yaxis=dict(gridcolor=GRAY_200, linecolor=GRAY_200, zerolinecolor=GRAY_200),
    title=dict(font=dict(color=UHC_BLUE, size=15, family="Segoe UI Semibold, sans-serif")),
)

def S(fig):
    fig.update_layout(**CHART)
    return fig

def fmt_d(v):
    if abs(v) >= 1e9: return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6: return f"${v/1e6:.1f}M"
    if abs(v) >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:,.0f}"

def fmt_n(v):
    if abs(v) >= 1e6: return f"{v/1e6:.1f}M"
    if abs(v) >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:,.0f}"

def G(fig):
    return dcc.Graph(figure=fig, animate=True,
                     config={"displayModeBar": True, "displaylogo": False},
                     style={"borderRadius": "10px", "overflow": "hidden"})

def kpi(title, val, sub="", icon="fa-solid fa-dollar-sign", color=UHC_BLUE):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.Div([html.I(className=f"{icon} fa-lg", style={"color": color}),
                   html.Span(title, className="ms-2",
                             style={"fontSize":"0.72rem","textTransform":"uppercase",
                                    "letterSpacing":"0.5px","color":GRAY_600,"fontWeight":600})],
                  className="d-flex align-items-center mb-1"),
        html.H4(val, className="mb-0", style={"fontWeight":800,"color":color}),
        html.Small(sub, style={"color":GRAY_600}) if sub else None,
    ]), style={"borderTop":f"4px solid {color}","borderRadius":"10px","backgroundColor":WHITE},
        className="shadow-sm"),
    xs=12, sm=6, md=4, lg=True, className="mb-2 kpi-animate")

TBL_HEADER = {"backgroundColor":UHC_BLUE,"color":WHITE,"fontWeight":600,"fontSize":"0.78rem","padding":"8px 12px"}
TBL_CELL = {"backgroundColor":WHITE,"color":GRAY_800,"fontSize":"0.75rem","padding":"6px 10px",
            "border":f"1px solid {GRAY_200}"}

# ── Filters ──────────────────────────────────────────────────────────
filter_bar = dbc.Card(dbc.CardBody(dbc.Row([
    dbc.Col([dbc.Label("Year",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-year",options=[{"label":str(y),"value":y} for y in sorted(DF["year"].unique())],
                          value=int(DF["year"].max()),clearable=False)], md=2),
    dbc.Col([dbc.Label("State",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-state",
                          options=[{"label":"All States","value":"ALL"}]+
                                  [{"label":s,"value":s} for s in sorted(DF["state"].unique())],
                          value="ALL",clearable=False)], md=2),
    dbc.Col([dbc.Label("Plan Type",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-plan",
                          options=[{"label":"All Plans","value":"ALL"}]+
                                  [{"label":p,"value":p} for p in ["Medicare","Medicaid","Dual"]],
                          value="ALL",clearable=False)], md=2),
    dbc.Col([dbc.Label("Category",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-cat",
                          options=[{"label":"All Categories","value":"ALL"}]+
                                  [{"label":c,"value":c} for c in sorted(DF["category"].unique())],
                          value="ALL",clearable=False)], md=3),
    dbc.Col([dbc.Label("Quarter",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-qtr",
                          options=[{"label":"All","value":"ALL"}]+
                                  [{"label":q,"value":q} for q in ["Q1","Q2","Q3","Q4"]],
                          value="ALL",clearable=False)], md=1),
    dbc.Col([dbc.Label("Base Year",className="small mb-1",style={"fontWeight":600,"color":UHC_BLUE}),
             dcc.Dropdown(id="f-base",options=[{"label":"2023","value":2023},{"label":"2024","value":2024}],
                          value=2024,clearable=False)], md=2),
], className="g-2")), className="mb-3 shadow-sm filter-bar", style={"borderRadius":"10px"})

# ── Tabs ─────────────────────────────────────────────────────────────
ts = {"padding":"8px 18px","fontWeight":500,"fontSize":"0.82rem","color":GRAY_600,
      "backgroundColor":"#F1F5F9","border":f"1px solid {GRAY_200}"}
tss = {**ts,"borderTop":f"4px solid {UHC_BLUE}","fontWeight":700,"color":UHC_BLUE,
       "backgroundColor":WHITE}
tabs = dcc.Tabs(id="tabs", value="exec", children=[
    dcc.Tab(label="Command Center",value="exec",style=ts,selected_style=tss),
    dcc.Tab(label="CPT Cost Drivers",value="cpt",style=ts,selected_style=tss),
    dcc.Tab(label="Utilization & Intensity",value="util",style=ts,selected_style=tss),
    dcc.Tab(label="Geographic Pressure",value="geo",style=ts,selected_style=tss),
    dcc.Tab(label="Medicare vs Medicaid",value="plan",style=ts,selected_style=tss),
    dcc.Tab(label="Early Warning Signals",value="warn",style=ts,selected_style=tss),
    dcc.Tab(label="Forecast & Scenarios",value="forecast",style=ts,selected_style=tss),
    dcc.Tab(label="Actuarial Actions",value="action",style=ts,selected_style=tss),
], className="mb-3")

# ── Layout ───────────────────────────────────────────────────────────
app.layout = dbc.Container([
    html.Div([
        html.Div([
            html.Img(src=LOGO_SRC, style={"height":"48px","marginRight":"20px"}) if LOGO_SRC else
            html.I(className="fa-solid fa-shield-heart fa-2x me-3", style={"color":WHITE}),
            html.Div([
                html.H3("CPT Cost Driver & Early Warning System", className="mb-0",
                         style={"fontWeight":800,"letterSpacing":"-0.3px","color":WHITE}),
                html.P("Actuarial Analytics  |  UCHI Decomposition  |  10 States  |  Medicare · Medicaid · Dual",
                       className="mb-0", style={"opacity":0.85,"fontSize":"0.82rem","color":"#B8D4FF"}),
            ]),
        ], className="d-flex align-items-center"),
        html.Div([
            html.Span("Powered by ", style={"color":"#B8D4FF","fontSize":"0.75rem"}),
            html.Span("Optum", style={"color":OPTUM_ORANGE,"fontWeight":700,"fontSize":"0.82rem"}),
            html.Span(" Analytics", style={"color":"#B8D4FF","fontSize":"0.75rem"}),
        ], style={"textAlign":"right"}),
    ], className="uhc-header d-flex justify-content-between align-items-center"),
    html.Div(id="kpi-row"),
    filter_bar, tabs, html.Div(id="tab-content"),
], fluid=True, className="px-3", style={"backgroundColor":"#F4F6F9"})


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════
def filt(df, year, state, plan, cat, qtr):
    o = df[df["year"]==year]
    if state!="ALL": o = o[o["state"]==state]
    if plan!="ALL": o = o[o["plan_type"]==plan]
    if cat!="ALL": o = o[o["category"]==cat]
    if qtr!="ALL": o = o[o["quarter"]==qtr]
    return o


# ═══════════════════════════════════════════════════════════════════════
# KPI ROW  (6 cards, no risk score)
# ═══════════════════════════════════════════════════════════════════════
@callback(Output("kpi-row","children"),
          Input("f-year","value"), Input("f-state","value"),
          Input("f-plan","value"), Input("f-cat","value"), Input("f-qtr","value"))
def update_kpis(year, state, plan, cat, qtr):
    fd = filt(DF, year, state, plan, cat, qtr)
    prev = filt(DF, year-1, state, plan, cat, qtr)
    total = fd["allowed_amount"].sum()
    prev_total = prev["allowed_amount"].sum()
    yoy = (total/prev_total-1)*100 if prev_total>0 else 0
    pmpm = total / max(1, fd["member_months"].sum()) * fd["month"].nunique()
    util = fd["utilization_per_1000"].mean()
    uc_curr = fd["unit_cost"].mean()
    uc_prev = prev["unit_cost"].mean() if len(prev)>0 else uc_curr
    uc_yoy = (uc_curr/uc_prev-1)*100 if uc_prev>0 else 0
    total_claims = fd["total_units"].sum()

    return dbc.Row([
        kpi("Total Allowed", fmt_d(total), f"YoY: {yoy:+.1f}%", "fa-solid fa-sack-dollar", UHC_BLUE),
        kpi("Avg PMPM", fmt_d(pmpm), "Per Member Per Month", "fa-solid fa-user-dollar", UHC_BLUE_LT),
        kpi("Util/1000", f"{util:.1f}", "Services per 1K members", "fa-solid fa-chart-line", OPTUM_ORANGE),
        kpi("Avg Unit Cost", fmt_d(uc_curr), "Per service", "fa-solid fa-tag", "#2E7D32"),
        kpi("Total Services", fmt_n(total_claims), "Claim line volume", "fa-solid fa-file-medical", "#7B1FA2"),
        kpi("Unit Cost Trend", f"{uc_yoy:+.1f}%", "YoY price pressure", "fa-solid fa-arrow-trend-up",
            OPTUM_ORANGE if uc_yoy>0 else UHC_BLUE_LT),
    ], className="g-2 mb-3")


# ═══════════════════════════════════════════════════════════════════════
# TAB BUILDERS
# ═══════════════════════════════════════════════════════════════════════

# ── Tab 1: Command Center (Top 20 CPTs + sparklines) ─────────────────
def build_exec(fd, base_year):
    curr_year = int(fd["year"].max())
    yoy = cpt_level_yoy(DF, base_year, curr_year)

    top20 = fd.groupby(["cpt_code","cpt_description","category"]).agg(
        total_allowed=("allowed_amount","sum"),
        total_units=("total_units","sum"),
        mm=("member_months","first"),
    ).reset_index()
    top20["pmpm"] = top20["total_allowed"] / top20["mm"]
    top20 = top20.nlargest(20,"total_allowed")

    top20_yoy = top20.merge(
        yoy[["cpt_code","allowed_change_pct"]].drop_duplicates("cpt_code"),
        on="cpt_code", how="left"
    )
    top20_yoy["allowed_change_pct"] = top20_yoy["allowed_change_pct"].fillna(0).round(1)
    top20_yoy["total_allowed"] = top20_yoy["total_allowed"].apply(fmt_d)
    top20_yoy["pmpm"] = top20_yoy["pmpm"].round(2)

    tbl = dash_table.DataTable(
        columns=[{"name":n,"id":c} for n,c in [
            ("CPT","cpt_code"),("Description","cpt_description"),("Category","category"),
            ("Total Allowed","total_allowed"),("PMPM","pmpm"),("YoY %","allowed_change_pct")]],
        data=top20_yoy.to_dict("records"),
        style_header=TBL_HEADER, style_cell=TBL_CELL,
        style_data_conditional=[
            {"if":{"filter_query":"{allowed_change_pct} > 10","column_id":"allowed_change_pct"},
             "backgroundColor":"#FFF0EB","color":OPTUM_ORANGE,"fontWeight":600},
        ],
        page_size=20, sort_action="native",
    )

    state_monthly = fd.groupby(["month","state"]).agg(
        allowed=("allowed_amount","sum"), mm=("member_months","first")).reset_index()
    state_monthly["pmpm"] = state_monthly["allowed"]/state_monthly["mm"]
    states_list = sorted(fd["state"].unique())[:10]
    fig_spark = make_subplots(rows=2, cols=5, subplot_titles=states_list,
                               vertical_spacing=0.12, horizontal_spacing=0.05)
    for i, st in enumerate(states_list):
        r, c = i//5+1, i%5+1
        sd = state_monthly[state_monthly["state"]==st].sort_values("month")
        fig_spark.add_trace(go.Scatter(x=sd["month"],y=sd["pmpm"],mode="lines",
                                        line=dict(color=UHC_BLUE,width=2),showlegend=False,
                                        fill="tozeroy",fillcolor="rgba(0,38,119,0.06)"), row=r, col=c)
    fig_spark.update_layout(title="PMPM Trend by State", height=340)
    S(fig_spark)
    fig_spark.update_annotations(font_size=9, font_color=UHC_BLUE)

    return html.Div([
        html.H6("Top 20 CPTs by Spend", className="mb-2", style={"fontWeight":700,"color":UHC_BLUE}),
        tbl, html.Br(), G(fig_spark),
    ])


# ── Tab 2: CPT Cost Drivers (unchanged) ──────────────────────────────
def build_cpt(fd, base_year):
    curr_year = int(fd["year"].max())
    yoy = cpt_level_yoy(DF, base_year, curr_year)

    top25 = fd.groupby(["cpt_code","cpt_description","category"])["allowed_amount"].sum().reset_index()
    top25 = top25.nlargest(25,"allowed_amount").sort_values("allowed_amount")
    fig_top = go.Figure(go.Bar(y=top25["cpt_code"]+" "+top25["cpt_description"].str[:30],
                                x=top25["allowed_amount"], orientation="h",
                                marker=dict(color=[CAT_COLORS.get(c,UHC_BLUE) for c in top25["category"]]),
                                text=[fmt_d(v) for v in top25["allowed_amount"]], textposition="auto",
                                textfont=dict(color=GRAY_800,size=10)))
    fig_top.update_layout(title="Top 25 CPTs by Total Allowed", height=600, yaxis=dict(autorange="reversed"))
    S(fig_top)

    fast = yoy[yoy["allowed_b"]>0].nlargest(20,"allowed_change_pct").sort_values("allowed_change_pct")
    fig_fast = go.Figure(go.Bar(y=fast["cpt_code"],x=fast["allowed_change_pct"],orientation="h",
                                 marker=dict(color=np.where(fast["allowed_change_pct"]>0,OPTUM_ORANGE,UHC_BLUE_LT)),
                                 text=[f"{v:+.1f}%" for v in fast["allowed_change_pct"]],textposition="auto"))
    fig_fast.update_layout(title=f"Fastest Growing CPTs ({base_year} -> {curr_year} %)", height=500)
    S(fig_fast)

    wf = cost_waterfall(DF, top_n=12, base_year=base_year, curr_year=curr_year)
    fig_wf = go.Figure(go.Waterfall(x=wf["cpt_code"],y=wf["allowed_change"],
                                      text=[fmt_d(v) for v in wf["allowed_change"]],textposition="outside",
                                      connector=dict(line=dict(color=GRAY_200)),
                                      increasing=dict(marker=dict(color=OPTUM_ORANGE)),
                                      decreasing=dict(marker=dict(color=UHC_BLUE_LT))))
    fig_wf.update_layout(title="Top CPTs Contributing to Cost Increase (Waterfall)", height=380)
    S(fig_wf)

    scatter_data = yoy[(yoy["allowed_b"]>10000)&(yoy["allowed_c"]>10000)].copy()
    scatter_data["category"] = scatter_data["category"].astype(str)
    fig_sc = px.scatter(scatter_data, x="util_change_pct", y="uc_change_pct",
                        size="allowed_c", color="category", hover_name="cpt_code",
                        color_discrete_map=CAT_COLORS,
                        labels={"util_change_pct":"Utilization Change %","uc_change_pct":"Unit Cost Change %"},
                        title="CPT Quadrant: Utilization vs Unit Cost Change", height=450)
    fig_sc.add_hline(y=0,line_dash="dash",line_color=GRAY_200)
    fig_sc.add_vline(x=0,line_dash="dash",line_color=GRAY_200)
    S(fig_sc)

    return html.Div([
        dbc.Row([dbc.Col(G(fig_top),lg=6), dbc.Col(G(fig_fast),lg=6)]),
        dbc.Row([dbc.Col(G(fig_wf),lg=6), dbc.Col(G(fig_sc),lg=6)]),
    ])


# ── Tab 3: Utilization & Intensity (unchanged) ───────────────────────
def build_util(fd, base_year):
    cat_monthly = fd.groupby(["month","category"]).agg(
        units=("total_units","sum"),mm=("member_months","first")).reset_index()
    cat_monthly["util_1k"] = cat_monthly["units"]/cat_monthly["mm"]*1000
    fig_util = go.Figure()
    for cat in sorted(CATEGORIES):
        cd = cat_monthly[cat_monthly["category"]==cat]
        fig_util.add_trace(go.Scatter(x=cd["month"],y=cd["util_1k"],mode="lines",stackgroup="one",
                                       name=cat,line=dict(width=0.5,color=CAT_COLORS.get(cat,UHC_BLUE))))
    fig_util.update_layout(title="Utilization per 1,000 by Category (Stacked)",height=380,yaxis_title="Services/1K")
    S(fig_util)

    rvu_monthly = fd.groupby(["month","category"])["rvu_total"].mean().reset_index()
    fig_int = go.Figure()
    for cat in sorted(CATEGORIES):
        cd = rvu_monthly[rvu_monthly["category"]==cat]
        fig_int.add_trace(go.Scatter(x=cd["month"],y=cd["rvu_total"],mode="lines+markers",
                                      name=cat,line=dict(color=CAT_COLORS.get(cat,UHC_BLUE),width=2),marker=dict(size=3)))
    fig_int.update_layout(title="Intensity Index (Avg RVU) by Category",height=380,yaxis_title="Avg RVU")
    S(fig_int)

    pos_data = fd.groupby(["month","place_of_service"])["allowed_amount"].sum().reset_index()
    pos_colors = {"Office":UHC_BLUE,"Inpatient":OPTUM_ORANGE,"ER":"#D32F2F","ASC":UHC_BLUE_LT,
                  "Telehealth":"#7B1FA2","Other":"#90A4AE"}
    fig_pos = go.Figure()
    for pos in sorted(pos_data["place_of_service"].unique()):
        pd_ = pos_data[pos_data["place_of_service"]==pos]
        fig_pos.add_trace(go.Bar(x=pd_["month"],y=pd_["allowed_amount"],name=pos,
                                  marker=dict(color=pos_colors.get(pos,"#90A4AE"))))
    fig_pos.update_layout(barmode="stack",title="Spend by Place of Service",height=380,yaxis_title="Allowed ($)")
    S(fig_pos)

    curr_year = int(fd["year"].max())
    yoy = cpt_level_yoy(DF, base_year, curr_year)
    movers = yoy.nlargest(10,"util_change_pct")[["cpt_code","description","category","util_b","util_c","util_change_pct","allowed_change_pct"]]
    tbl = dash_table.DataTable(
        columns=[{"name":c,"id":c,"type":"numeric" if "pct" in c or "util" in c else "text",
                  "format":{"specifier":".1f"} if "pct" in c else None} for c in movers.columns],
        data=movers.round(2).to_dict("records"),
        style_header=TBL_HEADER, style_cell=TBL_CELL, page_size=10, sort_action="native",
    )

    return html.Div([
        dbc.Row([dbc.Col(G(fig_util),lg=6), dbc.Col(G(fig_int),lg=6)]),
        dbc.Row([dbc.Col(G(fig_pos),lg=6),
                 dbc.Col([html.H6("Top Code Volume Movers",className="mt-2 mb-2",style={"fontWeight":700,"color":UHC_BLUE}),tbl],lg=6)]),
    ])


# ── Tab 4: Geographic Pressure (unchanged) ───────────────────────────
def build_geo(fd, base_year):
    curr_year = int(fd["year"].max())

    state_agg = fd.groupby("state").agg(allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    state_agg["pmpm"] = state_agg["allowed"]/state_agg["mm"]
    fig_map = go.Figure(go.Choropleth(
        locations=state_agg["state"], locationmode="USA-states", z=state_agg["pmpm"],
        colorscale=[[0,"#E8F0FE"],[0.3,"#90CAF9"],[0.6,UHC_BLUE_LT],[0.85,UHC_BLUE],[1,"#001550"]],
        colorbar=dict(title=dict(text="PMPM ($)",font=dict(color=UHC_BLUE)),tickfont=dict(color=GRAY_800)),
        text=state_agg.apply(lambda r: f"{r['state']}: ${r['pmpm']:.2f}", axis=1),
    ))
    fig_map.update_layout(title=f"Medical Cost Pressure by State ({curr_year})", height=420,
                           geo=dict(scope="usa",bgcolor=WHITE,lakecolor=WHITE,
                                    landcolor="#F4F6F9",showlakes=False,
                                    showframe=False,projection_type="albers usa"))
    S(fig_map)

    st_yoy_curr = fd.groupby("state").agg(allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    st_yoy_prev = filt(DF,base_year,"ALL","ALL","ALL","ALL").groupby("state").agg(
        allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    st_m = st_yoy_prev.merge(st_yoy_curr,on="state",suffixes=("_b","_c"))
    st_m["growth"] = (st_m["allowed_c"]/st_m["mm_c"])/(st_m["allowed_b"]/st_m["mm_b"])*100-100
    st_m = st_m.sort_values("growth")
    fig_rank = go.Figure(go.Bar(y=st_m["state"],x=st_m["growth"],orientation="h",
                                 marker=dict(color=np.where(st_m["growth"]>0,OPTUM_ORANGE,UHC_BLUE_LT)),
                                 text=[f"{v:+.1f}%" for v in st_m["growth"]],textposition="auto"))
    fig_rank.update_layout(title=f"PMPM Growth by State ({base_year} -> {curr_year})",height=380,xaxis_title="Growth %")
    S(fig_rank)

    cross = fd.groupby(["state","category"])["allowed_amount"].sum().reset_index()
    pivot = cross.pivot_table(index="state",columns="category",values="allowed_amount",fill_value=0)
    fig_heat = go.Figure(go.Heatmap(z=pivot.values,x=pivot.columns,y=pivot.index,
                                      colorscale=[[0,"#E8F0FE"],[0.4,"#90CAF9"],[0.7,UHC_BLUE_LT],[1,UHC_BLUE]],
                                      text=[[fmt_d(v) for v in row] for row in pivot.values],
                                      texttemplate="%{text}",textfont=dict(size=9,color=WHITE)))
    fig_heat.update_layout(title="Spend: State x Category",height=400,xaxis=dict(tickangle=-30))
    S(fig_heat)

    return html.Div([
        dbc.Row([dbc.Col(G(fig_map),lg=7), dbc.Col(G(fig_rank),lg=5)]),
        dbc.Row([dbc.Col(G(fig_heat))]),
    ])


# ── Tab 5: Medicare vs Medicaid (unchanged) ──────────────────────────
def build_plan(fd, base_year):
    plan_monthly = DF.groupby(["month","plan_type"]).agg(
        allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    plan_monthly["pmpm"] = plan_monthly["allowed"]/plan_monthly["mm"]
    plan_colors = {"Medicare":UHC_BLUE,"Medicaid":UHC_BLUE_LT,"Dual":OPTUM_ORANGE}
    fig_trend = go.Figure()
    for p in ["Medicare","Medicaid","Dual"]:
        pd_ = plan_monthly[plan_monthly["plan_type"]==p].sort_values("month")
        fig_trend.add_trace(go.Scatter(x=pd_["month"],y=pd_["pmpm"],mode="lines+markers",name=p,
                                        line=dict(color=plan_colors[p],width=2.5),marker=dict(size=4)))
    fig_trend.update_layout(title="PMPM Trend: Medicare vs Medicaid vs Dual",height=380,yaxis_title="PMPM ($)")
    S(fig_trend)

    plan_cpt = fd.groupby(["plan_type","cpt_code","cpt_description","category"])["allowed_amount"].sum().reset_index()
    top_cpts_global = plan_cpt.groupby("cpt_code")["allowed_amount"].sum().nlargest(10).index
    plan_top = plan_cpt[plan_cpt["cpt_code"].isin(top_cpts_global)]
    plan_top["label"] = plan_top["cpt_code"]+" "+plan_top["cpt_description"].str[:25]
    plan_top["plan_type"] = plan_top["plan_type"].astype(str)
    fig_drivers = px.bar(plan_top,x="label",y="allowed_amount",color="plan_type",barmode="group",
                          color_discrete_map=plan_colors,
                          labels={"allowed_amount":"Allowed ($)","label":"CPT"},
                          title="Top 10 CPT Drivers by Plan Type",height=400)
    fig_drivers.update_layout(xaxis_tickangle=-30)
    S(fig_drivers)

    plan_util = fd.groupby(["plan_type","category"]).agg(
        units=("total_units","sum"),mm=("member_months","first")).reset_index()
    plan_util["util_1k"] = plan_util["units"]/plan_util["mm"]*1000
    plan_util["plan_type"] = plan_util["plan_type"].astype(str)
    fig_util = px.bar(plan_util,x="category",y="util_1k",color="plan_type",barmode="group",
                       color_discrete_map=plan_colors,
                       labels={"util_1k":"Utilization/1K","category":"Category"},
                       title="Utilization per 1,000 by Plan Type & Category",height=380)
    S(fig_util)

    plan_uc = fd.groupby(["plan_type","category"]).agg(
        allowed=("allowed_amount","sum"),units=("total_units","sum")).reset_index()
    plan_uc["unit_cost"] = plan_uc["allowed"]/plan_uc["units"].clip(lower=1)
    plan_uc["plan_type"] = plan_uc["plan_type"].astype(str)
    fig_uc = px.bar(plan_uc,x="category",y="unit_cost",color="plan_type",barmode="group",
                     color_discrete_map=plan_colors,
                     labels={"unit_cost":"Avg Unit Cost ($)","category":"Category"},
                     title="Unit Cost by Plan Type & Category",height=380)
    S(fig_uc)

    return html.Div([
        dbc.Row([dbc.Col(G(fig_trend),lg=6), dbc.Col(G(fig_drivers),lg=6)]),
        dbc.Row([dbc.Col(G(fig_util),lg=6), dbc.Col(G(fig_uc),lg=6)]),
    ])


# ── Tab 6: Early Warning (cost-based, no risk score) ─────────────────
def build_warn(fd, base_year):
    # Cost acceleration heatmap: 3-month vs 12-month PMPM growth by category x state
    monthly = DF.groupby(["month","category","state"]).agg(
        allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    monthly["pmpm"] = monthly["allowed"]/monthly["mm"]
    monthly = monthly.sort_values("month")

    last_3 = monthly["month"].unique()[-3:]
    last_12 = monthly["month"].unique()[-12:]
    recent = monthly[monthly["month"].isin(last_3)].groupby(["category","state"])["pmpm"].mean()
    trailing = monthly[monthly["month"].isin(last_12)].groupby(["category","state"])["pmpm"].mean()
    accel = ((recent / trailing - 1) * 100).reset_index(name="accel_pct")

    pivot = accel.pivot_table(index="category",columns="state",values="accel_pct",fill_value=0)
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0,"#E8F5E9"],[0.3,"#FFF8E1"],[0.6,OPTUM_ORANGE_LT],[0.8,OPTUM_ORANGE],[1,"#B71C1C"]],
        text=[[f"{v:+.1f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=10,color=GRAY_800),
        zmid=0,
    ))
    fig_heat.update_layout(title="Cost Acceleration: 3-Month vs 12-Month PMPM Growth (Category x State)",height=400)
    S(fig_heat)

    # Top accelerating CPTs using trend_acceleration from early_warning.py
    accel_rows = []
    cpt_monthly = DF.groupby(["month","cpt_code","cpt_description","category"]).agg(
        allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index()
    cpt_monthly["pmpm"] = cpt_monthly["allowed"]/cpt_monthly["mm"]
    for cpt in cpt_monthly["cpt_code"].unique():
        cd = cpt_monthly[cpt_monthly["cpt_code"]==cpt].sort_values("month")
        if len(cd) < 12:
            continue
        short_s, long_s, is_accel = trend_acceleration(cd["pmpm"])
        if is_accel and short_s > 0:
            accel_rows.append({
                "cpt_code": cpt,
                "description": cd["cpt_description"].iloc[-1],
                "category": cd["category"].iloc[-1],
                "3mo_slope": round(short_s, 4),
                "12mo_slope": round(long_s, 4),
                "current_pmpm": round(float(cd["pmpm"].iloc[-1]), 4),
                "accel_ratio": round(short_s / max(abs(long_s), 1e-9), 1),
            })
    accel_df = pd.DataFrame(accel_rows).sort_values("accel_ratio", ascending=False).head(20)

    tbl = dash_table.DataTable(
        columns=[{"name":n,"id":c} for n,c in [
            ("CPT","cpt_code"),("Description","description"),("Category","category"),
            ("3-Mo Slope","3mo_slope"),("12-Mo Slope","12mo_slope"),
            ("Current PMPM","current_pmpm"),("Acceleration Ratio","accel_ratio")]],
        data=accel_df.to_dict("records"),
        style_header=TBL_HEADER, style_cell=TBL_CELL,
        style_data_conditional=[
            {"if":{"filter_query":"{accel_ratio} > 3","column_id":"accel_ratio"},
             "backgroundColor":"#FFF0EB","color":OPTUM_ORANGE,"fontWeight":600},
        ],
        page_size=20, sort_action="native",
    )

    # Monthly PMPM with anomaly band (+2 sigma)
    total_monthly = DF.groupby("month").agg(
        allowed=("allowed_amount","sum"),mm=("member_months","first")).reset_index().sort_values("month")
    total_monthly["pmpm"] = total_monthly["allowed"]/total_monthly["mm"]
    _, flags = zscore_flags(total_monthly["pmpm"], window=12, threshold=2.0)
    rolling_mean = total_monthly["pmpm"].rolling(12,min_periods=6).mean()
    rolling_std = total_monthly["pmpm"].rolling(12,min_periods=6).std()
    upper_band = rolling_mean + 2 * rolling_std

    fig_anom = go.Figure()
    fig_anom.add_trace(go.Scatter(x=total_monthly["month"],y=total_monthly["pmpm"],
                                   mode="lines+markers",name="PMPM",
                                   line=dict(color=UHC_BLUE,width=2.5),marker=dict(size=4)))
    fig_anom.add_trace(go.Scatter(x=total_monthly["month"],y=upper_band,
                                   mode="lines",name="+2σ Threshold",
                                   line=dict(color=OPTUM_ORANGE,width=2,dash="dash")))
    fig_anom.add_trace(go.Scatter(x=total_monthly["month"],y=rolling_mean,
                                   mode="lines",name="12-Mo Rolling Mean",
                                   line=dict(color=GRAY_600,width=1.5,dash="dot")))
    flagged_months = total_monthly[flags.values]
    if len(flagged_months) > 0:
        fig_anom.add_trace(go.Scatter(x=flagged_months["month"],y=flagged_months["pmpm"],
                                       mode="markers",name="Anomaly",
                                       marker=dict(color=OPTUM_ORANGE,size=12,symbol="diamond",
                                                   line=dict(color="#B71C1C",width=2))))
    fig_anom.update_layout(title="Monthly PMPM with Anomaly Detection (+2σ Band)",height=380,yaxis_title="PMPM ($)")
    S(fig_anom)

    return html.Div([
        dbc.Row([dbc.Col(G(fig_heat),lg=6), dbc.Col(G(fig_anom),lg=6)]),
        html.H6("Top Accelerating CPTs (3-Month vs 12-Month Trend)",className="mt-3 mb-2",
                 style={"fontWeight":700,"color":UHC_BLUE}),
        tbl,
    ])


# ── Tab 7: Forecast & Scenarios (no risk dependency) ─────────────────
def build_forecast(fd, base_year):
    actual_df, forecast_df, rmse = forecast_total_spend(DF)
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(x=actual_df["month"],y=actual_df["pmpm_actual"],mode="lines+markers",
                                 name="Actual",line=dict(color=UHC_BLUE,width=2.5),marker=dict(size=3),
                                 fill="tozeroy",fillcolor="rgba(0,38,119,0.05)"))
    fig_fc.add_trace(go.Scatter(x=forecast_df["month"],y=forecast_df["pmpm_forecast"],mode="lines+markers",
                                 name="Forecast",line=dict(color=OPTUM_ORANGE,width=2.5,dash="dash"),marker=dict(size=5,symbol="diamond")))
    fig_fc.add_trace(go.Scatter(
        x=pd.concat([forecast_df["month"],forecast_df["month"][::-1]]),
        y=pd.concat([forecast_df["upper_95"],forecast_df["lower_95"][::-1]]),
        fill="toself",fillcolor="rgba(255,97,43,0.08)",line=dict(width=0),name="95% CI"))
    fig_fc.add_trace(go.Scatter(
        x=pd.concat([forecast_df["month"],forecast_df["month"][::-1]]),
        y=pd.concat([forecast_df["upper_80"],forecast_df["lower_80"][::-1]]),
        fill="toself",fillcolor="rgba(255,97,43,0.15)",line=dict(width=0),name="80% CI"))
    fig_fc.update_layout(title="Total PMPM - Actual + 6-Month Forecast",height=400,yaxis_title="PMPM ($)")
    S(fig_fc)

    cat_fc = forecast_by_category(DF)
    n_cats = len(cat_fc); cols = 4; rows_n = (n_cats+cols-1)//cols
    fig_cats = make_subplots(rows=rows_n,cols=cols,subplot_titles=list(cat_fc.keys()),
                              vertical_spacing=0.10,horizontal_spacing=0.06)
    for i,(cat,data) in enumerate(cat_fc.items()):
        r,c = i//cols+1, i%cols+1
        fig_cats.add_trace(go.Scatter(x=data["actual_months"],y=data["actual_pmpm"],mode="lines",
                                       line=dict(color=CAT_COLORS.get(cat,UHC_BLUE),width=1.5),showlegend=False),row=r,col=c)
        fig_cats.add_trace(go.Scatter(x=data["forecast_months"],y=data["forecast"],mode="lines",
                                       line=dict(color=OPTUM_ORANGE,width=1.5,dash="dot"),showlegend=False),row=r,col=c)
    fig_cats.update_layout(title="Per-Category Forecast Sparklines",height=450)
    S(fig_cats)
    fig_cats.update_annotations(font_size=9,font_color=UHC_BLUE)

    scenarios = scenario_analysis(DF)
    fig_sc = go.Figure()
    for scn,color,dash_ in [("scenario_baseline",UHC_BLUE,"solid"),
                              ("scenario_adverse",OPTUM_ORANGE,"dash"),
                              ("scenario_favorable",UHC_BLUE_LT,"dash")]:
        fig_sc.add_trace(go.Scatter(x=scenarios["month"],y=scenarios[scn],mode="lines+markers",
                                     name=scn.replace("scenario_","").title(),
                                     line=dict(color=color,width=2.5,dash=dash_),marker=dict(size=4)))
    fig_sc.update_layout(title="Scenario Analysis: Baseline vs Adverse vs Favorable",height=380,yaxis_title="PMPM ($)")
    S(fig_sc)

    # Projected excess from DF only (recent 6mo avg vs prior 6mo avg)
    cpt_monthly = DF.groupby(["month","cpt_code","cpt_description","category"])["allowed_amount"].sum().reset_index()
    cpt_monthly = cpt_monthly.sort_values("month")
    months_all = sorted(cpt_monthly["month"].unique())
    recent_6 = months_all[-6:]
    prior_6 = months_all[-12:-6] if len(months_all)>=12 else months_all[:6]

    recent_avg = cpt_monthly[cpt_monthly["month"].isin(recent_6)].groupby(
        ["cpt_code","cpt_description","category"])["allowed_amount"].mean().reset_index(name="recent_avg")
    prior_avg = cpt_monthly[cpt_monthly["month"].isin(prior_6)].groupby("cpt_code")["allowed_amount"].mean().reset_index(name="prior_avg")
    excess = recent_avg.merge(prior_avg, on="cpt_code")
    excess["monthly_excess"] = (excess["recent_avg"] - excess["prior_avg"]).clip(lower=0)
    excess["excess_6m"] = (excess["monthly_excess"] * 6).round(0)
    excess = excess.nlargest(10, "excess_6m")

    if not excess.empty and excess["excess_6m"].sum() > 0:
        impact_tbl = dash_table.DataTable(
            columns=[{"name":n,"id":c} for n,c in [
                ("CPT","cpt_code"),("Description","cpt_description"),("Category","category"),
                ("Mo. Prior Avg $","prior_avg"),("Mo. Recent Avg $","recent_avg"),
                ("Mo. Excess $","monthly_excess"),("6-Mo Projected Excess $","excess_6m")]],
            data=excess.round(0).to_dict("records"),
            style_header=TBL_HEADER, style_cell=TBL_CELL, page_size=10, sort_action="native",
        )
    else:
        impact_tbl = html.P("No significant excess cost projected.", style={"color":GRAY_600})

    return html.Div([
        dbc.Row([dbc.Col(G(fig_fc))]),
        dbc.Row([dbc.Col(G(fig_cats))]),
        dbc.Row([dbc.Col(G(fig_sc),lg=6),
                 dbc.Col([html.H6("Impact Quantification - 6-Month Projected Excess",className="mb-2",
                                   style={"fontWeight":700,"color":UHC_BLUE}), impact_tbl],lg=6)]),
    ])


# ── Tab 8: Actuarial Actions (benchmark-based, no risk score) ────────
def build_action(fd, base_year):
    curr_year = int(fd["year"].max())
    yoy = cpt_level_yoy(DF, base_year, curr_year)

    # Benchmark deviation table
    bench = yoy[yoy["national_benchmark"].fillna(0)>0].copy()
    bench_above = bench[bench["benchmark_deviation_pct"]>0].nlargest(20,"benchmark_deviation_pct")
    bench_above["savings_opportunity"] = (
        (bench_above["uc_c"] - bench_above["national_benchmark"]) * bench_above["units_c"]
    ).clip(lower=0).round(0)

    tbl_bench = dash_table.DataTable(
        columns=[{"name":n,"id":c} for n,c in [
            ("CPT","cpt_code"),("Description","description"),("Category","category"),
            ("Unit Cost","uc_c"),("CMS Benchmark","national_benchmark"),
            ("Deviation %","benchmark_deviation_pct"),("Volume","units_c"),
            ("Savings Opportunity $","savings_opportunity")]],
        data=bench_above.round(1).to_dict("records"),
        style_header=TBL_HEADER, style_cell={**TBL_CELL,"whiteSpace":"normal"},
        style_data_conditional=[
            {"if":{"filter_query":"{benchmark_deviation_pct} > 30","column_id":"benchmark_deviation_pct"},
             "backgroundColor":"#FFF0EB","color":OPTUM_ORANGE,"fontWeight":600},
        ],
        page_size=20, sort_action="native",
    )

    # Savings opportunity bar chart
    top_savings = bench_above.nlargest(12,"savings_opportunity").sort_values("savings_opportunity")
    fig_sav = go.Figure(go.Bar(
        y=top_savings["cpt_code"],x=top_savings["savings_opportunity"],orientation="h",
        marker=dict(color=UHC_BLUE_LT,line=dict(color=UHC_BLUE,width=1)),
        text=[fmt_d(v) for v in top_savings["savings_opportunity"]],textposition="auto"))
    fig_sav.update_layout(title="Cost Savings Opportunity (Unit Cost Above CMS Benchmark x Volume)",
                           height=400,xaxis_title="Potential Savings ($)")
    S(fig_sav)

    # Benchmark deviation bar chart
    bench_top15 = bench.nlargest(15,"benchmark_deviation_pct").sort_values("benchmark_deviation_pct")
    fig_bench = go.Figure(go.Bar(
        y=bench_top15["cpt_code"],x=bench_top15["benchmark_deviation_pct"],orientation="h",
        marker=dict(color=np.where(bench_top15["benchmark_deviation_pct"]>0,OPTUM_ORANGE,UHC_BLUE_LT)),
        text=[f"{v:+.1f}%" for v in bench_top15["benchmark_deviation_pct"]],textposition="auto"))
    fig_bench.update_layout(title="Unit Cost vs CMS National Benchmark (Top Deviations)",height=400,
                             xaxis_title="Deviation from Benchmark %")
    S(fig_bench)

    # Key takeaways auto-generated
    cat_growth = yoy.groupby("category")["allowed_change_pct"].mean().sort_values(ascending=False)
    top_cat = cat_growth.index[0] if len(cat_growth) > 0 else "N/A"
    top_cat_pct = cat_growth.iloc[0] if len(cat_growth) > 0 else 0

    state_pmpm = fd.groupby("state").agg(a=("allowed_amount","sum"),m=("member_months","first")).reset_index()
    state_pmpm["pmpm"] = state_pmpm["a"]/state_pmpm["m"]
    top_state = state_pmpm.nlargest(1,"pmpm")
    top_state_name = top_state["state"].iloc[0] if len(top_state)>0 else "N/A"
    top_state_pmpm = top_state["pmpm"].iloc[0] if len(top_state)>0 else 0

    top_cpt = yoy.nlargest(1,"allowed_change")
    top_cpt_code = top_cpt["cpt_code"].iloc[0] if len(top_cpt)>0 else "N/A"
    top_cpt_change = top_cpt["allowed_change"].iloc[0] if len(top_cpt)>0 else 0

    total_savings = bench_above["savings_opportunity"].sum()

    takeaways = dbc.Card(dbc.CardBody([
        html.H6("Key Takeaways", style={"fontWeight":700,"color":UHC_BLUE}),
        html.Ul([
            html.Li([html.Strong(f"{top_cat}"), f" is the fastest-growing category at {top_cat_pct:+.1f}% YoY"]),
            html.Li([html.Strong(f"{top_state_name}"), f" has the highest PMPM at ${top_state_pmpm:.2f}"]),
            html.Li([html.Strong(f"CPT {top_cpt_code}"), f" is the largest single cost driver (+{fmt_d(top_cpt_change)})"]),
            html.Li([html.Strong(f"{fmt_d(total_savings)}"), " in potential savings from CMS benchmark alignment across top 20 CPTs"]),
        ], style={"color":GRAY_800,"fontSize":"0.88rem","lineHeight":"1.8"}),
    ]), style={"borderLeft":f"4px solid {OPTUM_ORANGE}","borderRadius":"10px"}, className="shadow-sm mb-3")

    return html.Div([
        takeaways,
        html.H6("CPTs Above CMS Benchmark - Savings Opportunities",className="mb-2",style={"fontWeight":700,"color":UHC_BLUE}),
        tbl_bench, html.Br(),
        dbc.Row([dbc.Col(G(fig_sav),lg=6), dbc.Col(G(fig_bench),lg=6)]),
    ])


# ═══════════════════════════════════════════════════════════════════════
# MAIN CALLBACK
# ═══════════════════════════════════════════════════════════════════════
@callback(Output("tab-content","children"),
          Input("tabs","value"),
          Input("f-year","value"), Input("f-state","value"),
          Input("f-plan","value"), Input("f-cat","value"),
          Input("f-qtr","value"), Input("f-base","value"))
def render(tab, year, state, plan, cat, qtr, base):
    fd = filt(DF, year, state, plan, cat, qtr)
    if fd.empty:
        return dbc.Alert("No data matches the selected filters.",color="warning",className="mt-4")
    builders = {
        "exec":build_exec, "cpt":build_cpt, "util":build_util, "geo":build_geo,
        "plan":build_plan, "warn":build_warn, "forecast":build_forecast, "action":build_action,
    }
    return builders.get(tab, build_exec)(fd, base)


if __name__ == "__main__":
    app.run(debug=True, port=8051)
