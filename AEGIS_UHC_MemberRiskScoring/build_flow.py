import xml.etree.ElementTree as ET

OUTPUT = r"D:\AI_Products_Dev\Products\AgenticAIClass_Docs\UHC_MemberRiskScoring_ProjectFlow.drawio"

NAVY     = "#1B3A5C"
MED_BLUE = "#4472C4"
STEEL    = "#2E75B6"
LT_BLUE  = "#D6E4F0"
PALE     = "#EBF1F8"
SLATE    = "#2F5496"
BLACK    = "#000000"
WHITE    = "#FFFFFF"
ACCENT   = "#D26012"

def S(**kw):
    return ";".join(f"{k}={v}" for k, v in kw.items()) + ";"

# ── STYLES ────────────────────────────────────────────────────
TITLE_S = S(text="", html=1, align="center", verticalAlign="middle",
            fontSize=22, fontStyle=1, fontColor=NAVY,
            strokeColor="none", fillColor="none")

SUB_S = S(text="", html=1, align="center", verticalAlign="middle",
          fontSize=11, fontStyle=2, fontColor="#777777",
          strokeColor="none", fillColor="none")

# Source pill — rounded dark navy
SRC = S(rounded=1, whiteSpace="wrap", html=1, fillColor=NAVY,
        fontColor=WHITE, strokeColor=BLACK, fontSize=12,
        fontStyle=0, arcSize=30, shadow=0)

# Process box — medium blue
PROC = S(rounded=1, whiteSpace="wrap", html=1, fillColor=MED_BLUE,
         fontColor=WHITE, strokeColor=SLATE, fontSize=13,
         fontStyle=1, arcSize=16)

# Key box — dark prominent
KEY = S(rounded=1, whiteSpace="wrap", html=1, fillColor=NAVY,
        fontColor=WHITE, strokeColor=BLACK, fontSize=14,
        fontStyle=1, arcSize=16, shadow=1)

# Output box — steel
OUT = S(rounded=1, whiteSpace="wrap", html=1, fillColor=STEEL,
        fontColor=WHITE, strokeColor=NAVY, fontSize=12,
        fontStyle=0, arcSize=16)

# Accent box — the single orange touch
ACC = S(rounded=1, whiteSpace="wrap", html=1, fillColor=ACCENT,
        fontColor=WHITE, strokeColor="#A04E0F", fontSize=13,
        fontStyle=1, arcSize=16)

# Light info box
INFO = S(rounded=1, whiteSpace="wrap", html=1, fillColor=LT_BLUE,
         fontColor=NAVY, strokeColor=STEEL, fontSize=11,
         fontStyle=0, arcSize=16)

# Phase label
PHASE = S(text="", html=1, align="center", verticalAlign="middle",
          fontSize=10, fontStyle=1, fontColor=STEEL,
          strokeColor=STEEL, fillColor=PALE, rounded=1, arcSize=20)

# Arrow — solid dark
ARR = S(edgeStyle="orthogonalEdgeStyle", rounded=1, orthogonalLoop=1,
        jettySize="auto", html=1, strokeColor=NAVY, strokeWidth=2,
        endArrow="blockThin", endFill=1)

# Arrow — dashed light
DARR = S(edgeStyle="orthogonalEdgeStyle", rounded=1, orthogonalLoop=1,
         jettySize="auto", html=1, strokeColor=STEEL, strokeWidth=1,
         dashed=1, endArrow="blockThin", endFill=1)

# Vertical big arrow between phases
BIG_ARR = S(edgeStyle="orthogonalEdgeStyle", rounded=0, orthogonalLoop=1,
            jettySize="auto", html=1, strokeColor=NAVY, strokeWidth=3,
            endArrow="blockThin", endFill=1, endSize=8)

# ── COLLECTOR ─────────────────────────────────────────────────
_n = [1]; cells = []

def nid():
    _n[0] += 1; return str(_n[0])

def box(label, x, y, w, h, style):
    vid = nid()
    cells.append(("v", vid, label, style, x, y, w, h, None, None))
    return vid

def edge(s, t, style=ARR, label=""):
    eid = nid()
    cells.append(("e", eid, label, style, 0, 0, 0, 0, s, t))
    return eid

# ══════════════════════════════════════════════════════════════
#  HIGH-LEVEL PROJECT FLOW
# ══════════════════════════════════════════════════════════════

CX = 700  # center x of the diagram
PW = 1350 # page width

# ── TITLE ──
box("AEGIS  -  Member Risk Scoring", 270, 15, 820, 40, TITLE_S)
box("UHC High-Cost Claimant Prediction  |  End-to-End Project Flow", 300, 52, 760, 22, SUB_S)

# ════════════ PHASE 1: DATA ACQUISITION ════════════
p1 = box("PHASE 1", 30, 100, 80, 28, PHASE)

src_y = 100
sw, sh = 200, 56
gap = 24
sx = 160
s1 = box("Medical Claims<br><i>837P / 837I</i>", sx, src_y, sw, sh, SRC)
sx += sw + gap
s2 = box("Call Center<br><i>IVR / CRM Data</i>", sx, src_y, sw, sh, SRC)
sx += sw + gap
s3 = box("Claim Remittance<br><i>835 / EOB</i>", sx, src_y, sw, sh, SRC)
sx += sw + gap
s4 = box("External Data<br><i>SDOH, SVI, ADI</i>", sx, src_y, sw, sh, SRC)
sx += sw + gap
s5 = box("Enrollment<br><i>834 Eligibility</i>", sx, src_y, sw, sh, SRC)

# ════════════ PHASE 2: DATA INTEGRATION ════════════
p2 = box("PHASE 2", 30, 200, 80, 28, PHASE)

int_y = 198
i1 = box("Data Ingestion<br>&amp; ETL", 240, int_y, 260, 56, PROC)
i2 = box("Data Quality<br>&amp; Validation", 560, int_y, 260, 56, PROC)
i3 = box("Enterprise<br>Data Lake", 880, int_y, 260, 56, KEY)

for s in [s1, s2, s3, s4, s5]:
    edge(s, i1)
edge(i1, i2)
edge(i2, i3)

# ════════════ PHASE 3: FEATURE ENGINEERING ════════════
p3 = box("PHASE 3", 30, 305, 80, 28, PHASE)

fe_y = 300
f1 = box("Member-Month<br>Spine", 200, fe_y, 240, 56, PROC)
f2 = box("Feature<br>Engineering<br><i>85 Features (6 Categories)</i>", 510, fe_y, 280, 60, PROC)
f3 = box("Feature<br>Store", 860, fe_y, 240, 56, KEY)

edge(i3, f1)
edge(f1, f2)
edge(f2, f3)

# ────── feature categories as small tags ──────
ty = 375
tw = 150
tg = 12
tx = 225
t1 = box("Cost History (15)", tx, ty, tw, 28, INFO); tx += tw + tg
t2 = box("Utilization (20)", tx, ty, tw, 28, INFO); tx += tw + tg
t3 = box("Clinical / Dx (20)", tx, ty, tw+10, 28, INFO); tx += tw + 10 + tg
t4 = box("Demographics (15)", tx, ty, tw+10, 28, INFO); tx += tw + 10 + tg
t5 = box("Provider (10) + SDOH (5)", tx, ty, tw+50, 28, INFO)
for t in [t1, t2, t3, t4, t5]:
    edge(f2, t, DARR)

# ════════════ PHASE 4: MODEL DEVELOPMENT ════════════
p4 = box("PHASE 4", 30, 450, 80, 28, PHASE)

ml_y = 445
m1 = box("<b>Stage 1</b><br>XGBoost Classifier<br><i>\"Will member exceed $50K?\"</i>",
         200, ml_y, 340, 68, KEY)
m2 = box("<b>Stage 2</b><br>LightGBM Regression<br><i>\"How much will they cost?\"</i>",
         620, ml_y, 340, 68, KEY)
m3 = box("SHAP<br>Explainability", 1030, ml_y + 4, 200, 58, PROC)

edge(f3, m1)
edge(m1, m2, ARR, "P &gt; 0.30")
edge(m2, m3)

# ════════════ PHASE 5: RISK SCORING ════════════
p5 = box("PHASE 5", 30, 565, 80, 28, PHASE)

rs_y = 560
r1 = box("Risk Scoring<br>Engine", 240, rs_y, 260, 56, PROC)
r2 = box("Risk Tier Assignment<br><b>CRITICAL | HIGH | ELEVATED | WATCH</b>",
         570, rs_y, 380, 56, ACC)
r3 = box("Member Risk<br>Score Table", 1020, rs_y, 220, 56, KEY)

edge(m2, r1)
edge(m3, r2, DARR)
edge(r1, r2)
edge(r2, r3)

# ════════════ PHASE 6: ACTION & DELIVERY ════════════
p6 = box("PHASE 6", 30, 670, 80, 28, PHASE)

act_y = 665
aw, ag = 200, 22
ax = 160
a1 = box("Care<br>Management", ax, act_y, aw, 56, OUT); ax += aw + ag
a2 = box("Actuarial<br>Reserving", ax, act_y, aw, 56, OUT); ax += aw + ag
a3 = box("Stop-Loss<br>Pricing", ax, act_y, aw, 56, OUT); ax += aw + ag
a4 = box("Provider<br>Network Mgmt", ax, act_y, aw, 56, OUT); ax += aw + ag
a5 = box("Executive<br>Dashboard", ax, act_y, aw, 56, OUT)

for a in [a1, a2, a3, a4, a5]:
    edge(r3, a, DARR)

# ── FOOTER ──
box("AEGIS  =  Advanced Early-warning Governance &amp; Intelligence System  |  4-Week MVP Sprint",
    250, 745, 860, 22, SUB_S)

# ══════════════════════════════════════════════════════════════
#  BUILD XML
# ══════════════════════════════════════════════════════════════
root = ET.Element("mxfile", host="app.diagrams.net", type="device")
diag = ET.SubElement(root, "diagram", id="flow",
                     name="AEGIS Member Risk Scoring - Project Flow")
model = ET.SubElement(diag, "mxGraphModel",
    dx="0", dy="0", grid="1", gridSize="10", guides="1",
    tooltips="1", connect="1", arrows="1", fold="1", page="1",
    pageScale="1", pageWidth="1400", pageHeight="800",
    math="0", shadow="0")
r = ET.SubElement(model, "root")
ET.SubElement(r, "mxCell", id="0")
ET.SubElement(r, "mxCell", id="1", parent="0")

for kind, cid, label, style, x, y, w, h, src, tgt in cells:
    a = {"id": cid, "value": label or "", "style": style, "parent": "1"}
    if kind == "v":
        a["vertex"] = "1"
        c = ET.SubElement(r, "mxCell", **a)
        ET.SubElement(c, "mxGeometry", x=str(x), y=str(y),
                      width=str(w), height=str(h), **{"as": "geometry"})
    else:
        a["edge"] = "1"; a["source"] = src; a["target"] = tgt
        c = ET.SubElement(r, "mxCell", **a)
        ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})

tree = ET.ElementTree(root)
ET.indent(tree, space="  ")
tree.write(OUTPUT, xml_declaration=True, encoding="UTF-8")
print(f"[OK] {OUTPUT}")
