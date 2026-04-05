import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
import json
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(page_title="WealthView", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DESIGN TOKENS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BG        = "#0B1020"
BG_ALT    = "#0D1326"
CARD      = "#131C31"
CARD_H    = "#182240"
BORDER    = "#1E2A45"
BORDER_L  = "#253255"
TEXT      = "#FFFFFF"
TEXT2     = "#94A3B8"
TEXT3     = "#64748B"
PURPLE    = "#8B5CF6"
PURPLE_D  = "#7C3AED"
BLUE      = "#3B82F6"
BLUE_D    = "#2563EB"
CYAN      = "#06B6D4"
CYAN_D    = "#0891B2"
GREEN     = "#10B981"
GREEN_D   = "#059669"
RED       = "#EF4444"
RED_D     = "#DC2626"
AMBER     = "#F59E0B"
PINK      = "#EC4899"

SHADOW    = "0 4px 24px rgba(0,0,0,.35), 0 1px 4px rgba(0,0,0,.25)"
SHADOW_SM = "0 2px 12px rgba(0,0,0,.25)"
GLOW_P    = f"0 0 20px {PURPLE}22, 0 4px 24px rgba(0,0,0,.35)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SNAPSHOT PERSISTENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SNAPSHOT_FILE = "wealthview_snapshots.json"

def load_snapshots():
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_snapshots(data):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if "snapshots" not in st.session_state:
    st.session_state.snapshots = load_snapshots()

if "snapshot_saved_flag" not in st.session_state:
    st.session_state.snapshot_saved_flag = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*, *::before, *::after {{box-sizing:border-box;}}
html, body, .stApp {{
    background:{BG} !important; color:{TEXT};
    font-family:'Inter',system-ui,-apple-system,sans-serif !important;
    -webkit-font-smoothing:antialiased;
}}
header[data-testid="stHeader"] {{background:{BG} !important; border-bottom:1px solid {BORDER};}}
.block-container {{padding:1.2rem 2rem 2rem 2rem !important; max-width:1400px;}}
div[data-testid="stToolbar"] {{display:none;}}

section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,{BG_ALT} 0%,#0A0F1E 100%) !important;
    border-right:1px solid {BORDER} !important; width:320px !important;
}}
section[data-testid="stSidebar"] .block-container {{padding:1rem 1.2rem !important;}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {{
    color:{TEXT2} !important; font-size:.82rem !important; font-family:'Inter',sans-serif !important;
}}
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stToggle label {{
    color:{TEXT2} !important; font-size:.78rem !important; letter-spacing:.02em;
}}
section[data-testid="stSidebar"] input {{
    background:{CARD} !important; border:1px solid {BORDER} !important;
    color:{TEXT} !important; border-radius:8px !important; font-size:.85rem !important;
}}
section[data-testid="stSidebar"] .stSlider > div > div > div {{background:{BORDER} !important;}}
section[data-testid="stSidebar"] .stSlider [role="slider"] {{background:{PURPLE} !important;}}
section[data-testid="stSidebar"] hr {{border-color:{BORDER} !important; margin:.6rem 0 !important;}}

div[data-testid="stMetric"] {{display:none;}}

.stTabs {{margin-top:.2rem;}}
.stTabs [data-baseweb="tab-list"] {{
    gap:0; border-bottom:1px solid {BORDER}; background:transparent; padding:0 .5rem;
}}
.stTabs [data-baseweb="tab"] {{
    color:{TEXT3} !important; background:transparent !important;
    border:none !important; padding:.65rem 1.3rem !important;
    font-size:.82rem !important; font-weight:500; letter-spacing:.02em;
    border-radius:10px 10px 0 0 !important; transition:all .2s ease;
    font-family:'Inter',sans-serif !important;
}}
.stTabs [data-baseweb="tab"]:hover {{color:{TEXT2} !important; background:{CARD}55 !important;}}
.stTabs [aria-selected="true"] {{
    color:{PURPLE} !important; background:{CARD} !important;
    border-bottom:2px solid {PURPLE} !important; font-weight:600;
}}
.stTabs [data-baseweb="tab-highlight"] {{display:none;}}
.stTabs [data-baseweb="tab-border"] {{display:none;}}

.js-plotly-plot, .plotly {{background:transparent !important;}}

::-webkit-scrollbar {{width:6px;height:6px;}}
::-webkit-scrollbar-track {{background:{BG};}}
::-webkit-scrollbar-thumb {{background:{BORDER_L};border-radius:3px;}}
::-webkit-scrollbar-thumb:hover {{background:{TEXT3};}}

section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
    background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:8px !important;
}}
div[data-testid="column"] > div {{padding:0 .3rem;}}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPONENT LIBRARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def gbp(v):
    sign = "-" if v < 0 else ""
    return f"{sign}£{abs(v):,.0f}"

def pct(v):
    return f"{v:.1f}%"

def kpi(label, value, color=PURPLE, icon="", sub=""):
    sub_html = f'<div style="color:{TEXT3};font-size:.7rem;margin-top:.15rem;">{sub}</div>' if sub else ""
    icon_html = f'<span style="font-size:.95rem;margin-right:.25rem;">{icon}</span>' if icon else ""
    return f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:14px;padding:1.1rem 1.2rem;
        box-shadow:{SHADOW_SM};position:relative;overflow:hidden;
    ">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;
            background:linear-gradient(90deg,{color}88,transparent);"></div>
        <div style="color:{TEXT2};font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;font-weight:500;margin-bottom:.35rem;">
            {icon_html}{label}</div>
        <div style="font-size:1.45rem;font-weight:800;color:{color};letter-spacing:-.02em;line-height:1.15;">{value}</div>
        {sub_html}
    </div>"""

def kpi_small(label, value, color=TEXT):
    return f"""
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:.75rem .9rem;text-align:center;">
        <div style="color:{TEXT3};font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;font-weight:500;">{label}</div>
        <div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:.2rem;">{value}</div>
    </div>"""

def card(title="", subtitle=""):
    sub = f'<span style="color:{TEXT3};font-size:.72rem;font-weight:400;margin-left:.5rem;">{subtitle}</span>' if subtitle else ""
    h = f'<div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.7rem;letter-spacing:-.01em;">{title}{sub}</div>' if title else ""
    return f"""<div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;
        box-shadow:{SHADOW};margin-bottom:.8rem;
    ">{h}"""

def card_end():
    return "</div>"

def section_header(title, icon=""):
    icon_html = f'<span style="margin-right:.4rem;">{icon}</span>' if icon else ""
    return f"""
    <div style="display:flex;align-items:center;margin:1.8rem 0 1rem 0;
        padding-bottom:.55rem;border-bottom:1px solid {BORDER};">
        <div style="font-size:1.1rem;font-weight:700;color:{TEXT};letter-spacing:-.01em;">
            {icon_html}{title}</div>
    </div>"""

def sidebar_section(label, color=PURPLE):
    return f"""<div style="
        color:{color};font-weight:700;font-size:.7rem;text-transform:uppercase;
        letter-spacing:.08em;margin:.8rem 0 .35rem 0;padding-bottom:.25rem;
        border-bottom:1px solid {BORDER};
    ">{label}</div>"""

def row_item(label, value, color=TEXT, bold=False):
    fw = "700" if bold else "500"
    return f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem 0;border-bottom:1px solid {BORDER}08;">
        <span style="color:{TEXT2};font-size:.84rem;">{label}</span>
        <span style="color:{color};font-weight:{fw};font-size:.9rem;">{value}</span>
    </div>"""

def progress_bar(pct_val, color_from=PURPLE, color_to=CYAN, height=8):
    w = max(0, min(100, pct_val))
    return f"""
    <div style="background:{BORDER};border-radius:{height}px;height:{height}px;width:100%;margin-top:.3rem;overflow:hidden;">
        <div style="width:{w}%;height:100%;border-radius:{height}px;
            background:linear-gradient(90deg,{color_from},{color_to});transition:width .6s ease;"></div>
    </div>"""

def spacer(h="1rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)

def axis_opts(*dicts):
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UK TAX ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_uk_tax(gross, scotland=False):
    pa = 12_570.0
    if gross > 100_000:
        pa = max(0, pa - (gross - 100_000) / 2)
    taxable = max(0, gross - pa)
    if scotland:
        bands = [(2_162, 0.19), (10_956, 0.20), (29_974, 0.21), (82_338, 0.42), (float('inf'), 0.45)]
    else:
        bands = [(37_700, 0.20), (87_440, 0.40), (float('inf'), 0.45)]
    income_tax = 0.0
    remaining = taxable
    band_breakdown = []
    for width, rate in bands:
        amt = min(remaining, width)
        tax = amt * rate
        income_tax += tax
        if amt > 0:
            band_breakdown.append({"band_width": amt, "rate": rate, "tax": tax})
        remaining -= amt
        if remaining <= 0:
            break
    ni_lower, ni_upper = 12_570.0, 50_270.0
    ni = 0.0
    if gross > ni_lower:
        ni += max(0, min(gross, ni_upper) - ni_lower) * 0.08
    if gross > ni_upper:
        ni += (gross - ni_upper) * 0.02
    total_deductions = income_tax + ni
    net_annual = gross - total_deductions
    effective_rate = (total_deductions / gross * 100) if gross > 0 else 0
    return {
        "gross": gross, "personal_allowance": pa, "taxable_income": taxable,
        "income_tax": income_tax, "ni": ni, "total_deductions": total_deductions,
        "net_annual": net_annual, "net_monthly": net_annual / 12,
        "effective_rate": effective_rate, "band_breakdown": band_breakdown,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def forecast_wealth(
    starting_liquid, starting_invested, starting_pension,
    monthly_invest, monthly_pension_contrib, monthly_surplus_after_invest,
    expected_return, inflation, property_val, property_growth, mortgage,
    years, pension_contrib_employer_annual=0
):
    rows = []
    liquid = starting_liquid
    invested = starting_invested
    pension = starting_pension
    prop = property_val
    mort = mortgage
    for y in range(0, years + 1):
        equity = max(0, prop - mort)
        nw = liquid + invested + pension + equity
        real_factor = 1 / ((1 + inflation / 100) ** y) if y > 0 else 1
        rows.append({
            "year": y, "liquid": liquid, "invested": invested, "pension": pension,
            "property_equity": equity, "net_worth": nw, "net_worth_real": nw * real_factor,
        })
        if y < years:
            invested *= (1 + expected_return / 100)
            pension *= (1 + expected_return / 100)
            prop *= (1 + property_growth / 100)
            mort *= 0.97
            invested += monthly_invest * 12
            pension += monthly_pension_contrib * 12 + pension_contrib_employer_annual
            liquid += monthly_surplus_after_invest * 12
    return pd.DataFrame(rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLOTLY THEME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT2, size=11, family="Inter, sans-serif"),
    margin=dict(l=15, r=15, t=25, b=15),
    legend=dict(font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER, font=dict(color=TEXT, size=12, family="Inter")),
)
GRID = {"gridcolor": BORDER, "gridwidth": 1, "griddash": "dot", "zeroline": False}
AXIS_CLEAN = {"showgrid": False, "zeroline": False}
CFG = {"displayModeBar": False}

CLR_BASE = BLUE
CLR_AGGRESSIVE = PURPLE
CLR_CONSERVATIVE = CYAN

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0 .6rem 0;">
        <div style="font-size:1.8rem;font-weight:900;
            background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            letter-spacing:-.03em;">◈ WealthView</div>
        <div style="color:{TEXT3};font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;margin-top:.2rem;">
            Personal Finance Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Reporting Period ──
    st.markdown(sidebar_section("Reporting Period", PURPLE), unsafe_allow_html=True)
    now = datetime.now()
    rp_col1, rp_col2 = st.columns(2)
    with rp_col1:
        sel_month = st.selectbox("Month", MONTHS, index=now.month - 1)
    with rp_col2:
        sel_year = st.selectbox("Year", list(range(2020, now.year + 2)), index=min(now.year - 2020, now.year + 1 - 2020))
    period_key = f"{sel_year}-{MONTHS.index(sel_month)+1:02d}"
    period_label = f"{sel_month} {sel_year}"

    # Pre-fill from existing snapshot if it exists
    existing = st.session_state.snapshots.get(period_key, {})

    st.markdown("---")
    st.markdown(sidebar_section("Assets", GREEN), unsafe_allow_html=True)
    cash = st.number_input("Cash & Savings (£)", 0, 10_000_000, int(existing.get("cash", 25_000)), 1_000)
    investments = st.number_input("Investments (£)", 0, 50_000_000, int(existing.get("investments", 85_000)), 1_000)
    pension_val = st.number_input("Pension (£)", 0, 50_000_000, int(existing.get("pension", 42_000)), 1_000)
    property_val = st.number_input("Property Value (£)", 0, 50_000_000, int(existing.get("property", 350_000)), 5_000)

    st.markdown(sidebar_section("Liabilities", RED), unsafe_allow_html=True)
    mortgage = st.number_input("Mortgage Balance (£)", 0, 50_000_000, int(existing.get("mortgage", 220_000)), 5_000)

    st.markdown("---")
    st.markdown(sidebar_section("Income", BLUE), unsafe_allow_html=True)
    gross_salary = st.number_input("Gross Salary (£/yr)", 0, 5_000_000, int(existing.get("gross_salary", 65_000)), 1_000)
    annual_bonus = st.number_input("Annual Bonus (£)", 0, 2_000_000, int(existing.get("annual_bonus", 5_000)), 500)
    scotland_tax = st.toggle("Scottish Tax Bands", value=existing.get("scotland_tax", False))
    pension_contrib_pct = st.slider("Pension Contribution %", 0.0, 30.0, float(existing.get("pension_contrib_pct", 5.0)), 0.5)

    st.markdown("---")
    st.markdown(sidebar_section("Spending & Saving", AMBER), unsafe_allow_html=True)
    monthly_expenses = st.number_input("Monthly Expenses (£)", 0, 100_000, int(existing.get("monthly_expenses", 2_800)), 100)
    monthly_invest = st.number_input("Monthly Investment (£)", 0, 50_000, int(existing.get("monthly_invest", 500)), 50)

    st.markdown("---")
    st.markdown(sidebar_section("Forecast Assumptions", CYAN), unsafe_allow_html=True)
    current_age = st.number_input("Current Age", 18, 80, int(existing.get("current_age", 32)))
    retirement_age = st.number_input("Retirement Age", 30, 90, int(existing.get("retirement_age", 60)))
    target_wealth = st.number_input("Target Wealth (£)", 0, 100_000_000, int(existing.get("target_wealth", 1_000_000)), 50_000)
    expected_return = st.slider("Expected Return %", 0.0, 15.0, float(existing.get("expected_return", 7.0)), 0.5)
    inflation = st.slider("Inflation %", 0.0, 10.0, float(existing.get("inflation", 2.5)), 0.1)
    property_growth = st.slider("Property Growth %", 0.0, 10.0, float(existing.get("property_growth", 3.5)), 0.5)

    # ── Save Snapshot ──
    st.markdown("---")
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:12px;padding:.8rem 1rem;margin-bottom:.6rem;
        text-align:center;
    ">
        <div style="color:{TEXT3};font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.2rem;">
            Reporting Period</div>
        <div style="color:{PURPLE};font-weight:700;font-size:1rem;">{period_label}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Save Snapshot", type="primary", use_container_width=True):
        snapshot_data = {
            "cash": cash, "investments": investments, "pension": pension_val,
            "property": property_val, "mortgage": mortgage,
            "gross_salary": gross_salary, "annual_bonus": annual_bonus,
            "scotland_tax": scotland_tax, "pension_contrib_pct": pension_contrib_pct,
            "monthly_expenses": monthly_expenses, "monthly_invest": monthly_invest,
            "current_age": current_age, "retirement_age": retirement_age,
            "target_wealth": target_wealth, "expected_return": expected_return,
            "inflation": inflation, "property_growth": property_growth,
            "saved_at": datetime.now().isoformat(),
        }
        # Compute derived values to store
        nw = cash + investments + pension_val + max(0, property_val - mortgage)
        snapshot_data["net_worth"] = nw
        snapshot_data["property_equity"] = max(0, property_val - mortgage)
        snapshot_data["liquid"] = cash
        snapshot_data["invested"] = investments

        st.session_state.snapshots[period_key] = snapshot_data
        save_snapshots(st.session_state.snapshots)
        st.session_state.snapshot_saved_flag = True
        st.rerun()

    if st.session_state.snapshot_saved_flag:
        st.markdown(f"""
        <div style="background:{GREEN}18;border:1px solid {GREEN}44;border-radius:8px;
            padding:.5rem .7rem;text-align:center;margin-top:.3rem;">
            <span style="color:{GREEN};font-size:.8rem;font-weight:600;">Snapshot saved for {period_label}</span>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.snapshot_saved_flag = False

    snap_count = len(st.session_state.snapshots)
    if snap_count > 0:
        st.markdown(f'<div style="color:{TEXT3};font-size:.72rem;text-align:center;margin-top:.4rem;">{snap_count} snapshot{"s" if snap_count != 1 else ""} saved</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD SNAPSHOT HISTORY DATAFRAME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_history_df(snapshots):
    if not snapshots:
        return pd.DataFrame()
    rows = []
    for pk, sd in sorted(snapshots.items()):
        try:
            parts = pk.split("-")
            yr, mo = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            continue
        rows.append({
            "period_key": pk,
            "date": datetime(yr, mo, 1),
            "label": f"{MONTHS[mo-1][:3]} {yr}",
            "cash": sd.get("cash", 0),
            "investments": sd.get("investments", 0) if "investments" in sd else sd.get("invested", 0),
            "pension": sd.get("pension", 0),
            "property_equity": sd.get("property_equity", max(0, sd.get("property", 0) - sd.get("mortgage", 0))),
            "net_worth": sd.get("net_worth", 0),
            "property": sd.get("property", 0),
            "mortgage": sd.get("mortgage", 0),
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df["nw_change"] = df["net_worth"].diff()
    df["nw_change_pct"] = df["net_worth"].pct_change() * 100
    return df

history_df = build_history_df(st.session_state.snapshots)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALCULATIONS (current inputs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
total_gross = gross_salary + annual_bonus
employee_pension_annual = gross_salary * pension_contrib_pct / 100
employer_pension_annual = gross_salary * 0.03
taxable_gross = total_gross - employee_pension_annual
tax = calc_uk_tax(taxable_gross, scotland=scotland_tax)
net_monthly = tax["net_monthly"]
monthly_pension_contrib = employee_pension_annual / 12
surplus = net_monthly - monthly_expenses - monthly_invest
savings_rate = ((net_monthly - monthly_expenses) / net_monthly * 100) if net_monthly > 0 else 0
net_worth = cash + investments + pension_val + max(0, property_val - mortgage)
liquid_assets = cash
invested_assets = investments
debt = mortgage
property_equity = max(0, property_val - mortgage)
years_to_retire = max(1, retirement_age - current_age)

df_base = forecast_wealth(
    cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
    expected_return, inflation, property_val, property_growth, mortgage,
    years_to_retire, employer_pension_annual
)
df_conservative = forecast_wealth(
    cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
    max(0, expected_return - 2), inflation, property_val, property_growth, mortgage,
    years_to_retire, employer_pension_annual
)
df_aggressive = forecast_wealth(
    cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
    expected_return + 2, inflation, property_val, property_growth, mortgage,
    years_to_retire, employer_pension_annual
)

forecast_10y = df_base.loc[df_base["year"] == min(10, years_to_retire), "net_worth"].values
forecast_10y_val = forecast_10y[0] if len(forecast_10y) > 0 else net_worth
goal_progress = min(100, net_worth / target_wealth * 100) if target_wealth > 0 else 0
goal_gap = max(0, target_wealth - net_worth)

if years_to_retire > 0 and expected_return > 0:
    r_m = expected_return / 100 / 12
    n = years_to_retire * 12
    fv_current = net_worth * ((1 + r_m) ** n)
    shortfall = max(0, target_wealth - fv_current)
    required_monthly = shortfall * r_m / (((1 + r_m) ** n) - 1) if (shortfall > 0 and r_m > 0) else 0
else:
    required_monthly = 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:.8rem;margin-bottom:.1rem;">
    <span style="font-size:1.9rem;font-weight:900;letter-spacing:-.03em;
        background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">◈ WealthView</span>
    <span style="color:{TEXT3};font-size:.78rem;letter-spacing:.04em;">Personal Wealth Management & Forecast</span>
</div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab_overview, tab_history, tab_salary, tab_cashflow, tab_portfolio, tab_forecast, tab_goals, tab_assumptions, tab_guide = st.tabs(
    ["Overview", "History", "Salary & Tax", "Cash Flow", "Portfolio", "Forecast", "Goals", "Assumptions", "Getting Started"]
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_overview:
    # Reporting period banner
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:12px;padding:.65rem 1.2rem;
        margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;
    ">
        <div style="display:flex;align-items:center;gap:.6rem;">
            <span style="color:{PURPLE};font-size:.85rem;">◈</span>
            <span style="color:{TEXT2};font-size:.78rem;">Current Snapshot</span>
            <span style="color:{TEXT};font-weight:700;font-size:.92rem;">{period_label}</span>
        </div>
        <div style="color:{TEXT3};font-size:.72rem;">{len(st.session_state.snapshots)} snapshot{"s" if len(st.session_state.snapshots) != 1 else ""} saved</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_header("Financial Snapshot", "◈"), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi("Net Worth", gbp(net_worth), PURPLE, "◈"), unsafe_allow_html=True)
    c2.markdown(kpi("Liquid Assets", gbp(liquid_assets), CYAN, "◇"), unsafe_allow_html=True)
    c3.markdown(kpi("Invested Assets", gbp(invested_assets), BLUE, "△"), unsafe_allow_html=True)
    spacer(".6rem")

    c4, c5, c6 = st.columns(3)
    c4.markdown(kpi("Pension", gbp(pension_val), GREEN, "◎"), unsafe_allow_html=True)
    c5.markdown(kpi("Property Equity", gbp(property_equity), AMBER, "⬡"), unsafe_allow_html=True)
    c6.markdown(kpi("Outstanding Debt", gbp(-debt), RED, "▽"), unsafe_allow_html=True)
    spacer(".6rem")

    c7, c8, c9 = st.columns(3)
    c7.markdown(kpi("Net Monthly Income", gbp(net_monthly), GREEN, "→"), unsafe_allow_html=True)
    c8.markdown(kpi("Monthly Surplus", gbp(surplus), CYAN if surplus >= 0 else RED, "↗" if surplus >= 0 else "↘"), unsafe_allow_html=True)
    c9.markdown(kpi("Savings Rate", pct(savings_rate), PURPLE, "◉"), unsafe_allow_html=True)

    spacer("1.2rem")
    st.markdown(section_header("Wealth Composition"), unsafe_allow_html=True)

    col_donut, col_bar = st.columns([1, 1.1])

    with col_donut:
        st.markdown(card("Net Worth Allocation"), unsafe_allow_html=True)
        labels = ["Cash", "Investments", "Pension", "Property Equity"]
        values = [cash, investments, pension_val, property_equity]
        colors = [CYAN, BLUE, GREEN, AMBER]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.62,
            marker=dict(colors=colors, line=dict(color=BG, width=2)),
            textinfo="label+percent", textfont=dict(size=11, color=TEXT, family="Inter"),
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<br>%{percent}<extra></extra>",
            direction="clockwise", sort=False,
        ))
        fig.update_layout(**PL, height=370, showlegend=False)
        fig.add_annotation(text=f"<b>{gbp(net_worth)}</b>", x=0.5, y=0.54,
                           font=dict(size=19, color=TEXT, family="Inter"), showarrow=False)
        fig.add_annotation(text="NET WORTH", x=0.5, y=0.43,
                           font=dict(size=8.5, color=TEXT3, family="Inter"), showarrow=False)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

    with col_bar:
        st.markdown(card("Asset & Liability Breakdown"), unsafe_allow_html=True)
        cats = ["Cash", "Investments", "Pension", "Property Equity", "Mortgage"]
        vals = [cash, investments, pension_val, property_equity, -mortgage]
        clrs = [CYAN, BLUE, GREEN, AMBER, RED]
        fig = go.Figure(go.Bar(
            x=vals, y=cats, orientation="h",
            marker=dict(color=clrs, cornerradius=6, line=dict(width=0)),
            text=[gbp(v) for v in vals], textposition="auto",
            textfont=dict(color=TEXT, size=11, family="Inter"),
            hovertemplate="<b>%{y}</b>: £%{x:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            **PL, height=370,
            yaxis=axis_opts(AXIS_CLEAN, {"autorange": "reversed", "tickfont": dict(color=TEXT2, size=11)}),
            xaxis=axis_opts(AXIS_CLEAN, {"zeroline": True, "zerolinecolor": BORDER_L, "zerolinewidth": 1}),
        )
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

    # 10-year banner
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;
        box-shadow:{GLOW_P};text-align:center;margin-top:.4rem;
    ">
        <div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:500;">
            10-Year Projected Net Worth</div>
        <div style="font-size:2.2rem;font-weight:900;letter-spacing:-.03em;margin-top:.3rem;
            background:linear-gradient(135deg,{PURPLE},{BLUE});
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            {gbp(forecast_10y_val)}</div>
    </div>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_history:
    st.markdown(section_header("Snapshot History", "◷"), unsafe_allow_html=True)

    if history_df.empty:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
            border:1px solid {BORDER};border-radius:16px;padding:2.5rem 2rem;
            box-shadow:{SHADOW};text-align:center;
        ">
            <div style="font-size:2rem;margin-bottom:.6rem;">◈</div>
            <div style="color:{TEXT};font-size:1.05rem;font-weight:600;margin-bottom:.4rem;">No snapshots yet</div>
            <div style="color:{TEXT3};font-size:.82rem;line-height:1.6;max-width:420px;margin:0 auto;">
                Select a reporting period in the sidebar, enter your financial figures,
                and click <span style="color:{PURPLE};font-weight:600;">Save Snapshot</span> to start tracking your wealth over time.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Momentum summary
        if len(history_df) >= 2:
            latest = history_df.iloc[-1]
            prev = history_df.iloc[-2]
            change = latest["net_worth"] - prev["net_worth"]
            change_pct = (change / prev["net_worth"] * 100) if prev["net_worth"] != 0 else 0
            change_color = GREEN if change >= 0 else RED
            change_icon = "↗" if change >= 0 else "↘"

            c1, c2, c3 = st.columns(3)
            c1.markdown(kpi("Latest Net Worth", gbp(latest["net_worth"]), PURPLE, "◈", sub=latest["label"]), unsafe_allow_html=True)
            c2.markdown(kpi("Month-on-Month Change", gbp(change), change_color, change_icon), unsafe_allow_html=True)
            c3.markdown(kpi("Growth Rate", pct(change_pct), change_color, change_icon), unsafe_allow_html=True)
            spacer("1rem")

        # Net worth over time chart
        st.markdown(card("Net Worth Over Time"), unsafe_allow_html=True)

        view_toggle = st.radio("View", ["Monthly", "Yearly"], horizontal=True, label_visibility="collapsed")

        if view_toggle == "Yearly":
            yearly = history_df.copy()
            yearly["year"] = yearly["date"].dt.year
            yearly = yearly.groupby("year").last().reset_index()
            chart_x = yearly["year"].astype(str)
            chart_y = yearly["net_worth"]
            chart_labels = yearly["year"].astype(str)
        else:
            chart_x = history_df["label"]
            chart_y = history_df["net_worth"]
            chart_labels = history_df["label"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_x, y=chart_y, mode="lines+markers",
            line=dict(color=PURPLE, width=3), marker=dict(size=8, color=PURPLE, line=dict(color=BG, width=2)),
            fill="tozeroy", fillcolor=f"{PURPLE}12",
            hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(**PL, height=380, showlegend=False, xaxis=GRID, yaxis=GRID)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

        # Stacked area breakdown
        if len(history_df) >= 2:
            spacer(".5rem")
            st.markdown(card("Asset Breakdown Over Time"), unsafe_allow_html=True)
            fig2 = go.Figure()
            for col_name, color in [("cash", CYAN), ("investments", BLUE), ("pension", GREEN), ("property_equity", AMBER)]:
                fig2.add_trace(go.Scatter(
                    x=history_df["label"], y=history_df[col_name], name=col_name.replace("_", " ").title(),
                    stackgroup="one", line=dict(width=0.5, color=color),
                    fillcolor=f"{color}55",
                    hovertemplate=f"<b>{col_name.replace('_',' ').title()}</b><br>" + "%{x}: £%{y:,.0f}<extra></extra>",
                ))
            fig2.update_layout(**PL, height=350, legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
                               xaxis=GRID, yaxis=GRID)
            st.plotly_chart(fig2, use_container_width=True, config=CFG)
            st.markdown(card_end(), unsafe_allow_html=True)

        # Growth table
        spacer(".5rem")
        st.markdown(card("Month-to-Month Growth"), unsafe_allow_html=True)
        table_html = f"""
        <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:.82rem;">
        <thead>
            <tr style="border-bottom:2px solid {BORDER};">
                <th style="text-align:left;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Period</th>
                <th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Net Worth</th>
                <th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Change</th>
                <th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Growth</th>
            </tr>
        </thead>
        <tbody>"""
        for _, row in history_df.iterrows():
            chg = row.get("nw_change", 0)
            chg_pct = row.get("nw_change_pct", 0)
            if pd.isna(chg):
                chg_str = "—"
                pct_str = "—"
                chg_color = TEXT3
            else:
                chg_color = GREEN if chg >= 0 else RED
                chg_str = gbp(chg)
                pct_str = pct(chg_pct)
            table_html += f"""
            <tr style="border-bottom:1px solid {BORDER};">
                <td style="padding:.45rem .6rem;color:{TEXT};">{row['label']}</td>
                <td style="padding:.45rem .6rem;color:{TEXT};text-align:right;font-weight:600;">{gbp(row['net_worth'])}</td>
                <td style="padding:.45rem .6rem;color:{chg_color};text-align:right;font-weight:500;">{chg_str}</td>
                <td style="padding:.45rem .6rem;color:{chg_color};text-align:right;font-weight:500;">{pct_str}</td>
            </tr>"""
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)

        # Delete snapshot
        spacer(".5rem")
        st.markdown(card("Manage Snapshots"), unsafe_allow_html=True)
        del_options = [f"{MONTHS[int(k.split('-')[1])-1]} {k.split('-')[0]}" for k in sorted(st.session_state.snapshots.keys())]
        del_keys = sorted(st.session_state.snapshots.keys())
        if del_options:
            del_col1, del_col2 = st.columns([2, 1])
            with del_col1:
                del_choice = st.selectbox("Select snapshot to remove", del_options, label_visibility="collapsed")
            with del_col2:
                if st.button("Delete Snapshot", type="secondary", use_container_width=True):
                    idx = del_options.index(del_choice)
                    del st.session_state.snapshots[del_keys[idx]]
                    save_snapshots(st.session_state.snapshots)
                    st.rerun()
        st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SALARY & TAX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_salary:
    region = "Scotland" if scotland_tax else "England / Wales / NI"
    st.markdown(section_header(f"UK Salary Breakdown — {region}", "⚙"), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_small("Gross Income", gbp(total_gross), TEXT), unsafe_allow_html=True)
    c2.markdown(kpi_small("Take Home", gbp(tax["net_annual"]), GREEN), unsafe_allow_html=True)
    c3.markdown(kpi_small("Total Tax & NI", gbp(tax["total_deductions"]), RED), unsafe_allow_html=True)
    c4.markdown(kpi_small("Effective Rate", pct(tax["effective_rate"]), PURPLE), unsafe_allow_html=True)

    spacer(".8rem")
    cl, cr = st.columns([1.15, 0.85])

    with cl:
        st.markdown(card("Income Statement"), unsafe_allow_html=True)
        items = [
            ("Gross Income (salary + bonus)", total_gross, TEXT, False),
            ("Pension Contribution (employee)", -employee_pension_annual, AMBER, False),
            ("Taxable Income", tax["taxable_income"], TEXT, True),
            ("Personal Allowance", tax["personal_allowance"], TEXT2, False),
            ("Income Tax", -tax["income_tax"], RED, False),
            ("National Insurance", -tax["ni"], RED, False),
            ("Total Deductions", -tax["total_deductions"], RED, True),
            ("Net Annual Income", tax["net_annual"], GREEN, True),
            ("Net Monthly Income", tax["net_monthly"], GREEN, True),
        ]
        for label, val, color, bold in items:
            st.markdown(row_item(label, gbp(val), color, bold), unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:.7rem 0 .2rem 0;margin-top:.3rem;">
            <span style="color:{PURPLE};font-weight:700;font-size:.9rem;">Effective Tax Rate</span>
            <span style="font-size:1.2rem;font-weight:800;
                background:linear-gradient(135deg,{PURPLE},{BLUE});
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                {pct(tax['effective_rate'])}</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)

    with cr:
        st.markdown(card("Tax Composition"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Income Tax", "National Insurance", "Net Pay"],
            values=[tax["income_tax"], tax["ni"], tax["net_annual"]],
            hole=0.58, marker=dict(colors=[RED, AMBER, GREEN], line=dict(color=BG, width=2)),
            textinfo="label+percent", textfont=dict(size=10.5, color=TEXT, family="Inter"),
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
        ))
        fig.update_layout(**PL, height=280, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

        st.markdown(card("Tax Band Detail"), unsafe_allow_html=True)
        if tax["band_breakdown"]:
            for b in tax["band_breakdown"]:
                st.markdown(row_item(
                    f"{pct(b['rate']*100)} on {gbp(b['band_width'])}", gbp(b['tax']), RED
                ), unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:{TEXT3};font-size:.82rem;">No tax bands applicable</span>', unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CASH FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_cashflow:
    st.markdown(section_header("Monthly Cash Flow", "↔"), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_small("Net Income", gbp(net_monthly), GREEN), unsafe_allow_html=True)
    c2.markdown(kpi_small("Total Outflows", gbp(monthly_expenses + monthly_invest + monthly_pension_contrib), AMBER), unsafe_allow_html=True)
    c3.markdown(kpi_small("Savings Rate", pct(savings_rate), PURPLE), unsafe_allow_html=True)

    spacer(".8rem")
    cl, cr = st.columns(2)

    with cl:
        st.markdown(card("Cash Flow Statement"), unsafe_allow_html=True)
        cf_items = [
            ("Gross Monthly Income", total_gross / 12, TEXT, False),
            ("Tax & NI", -tax["total_deductions"] / 12, RED, False),
            ("Pension (employee)", -monthly_pension_contrib, AMBER, False),
            ("Net Monthly Income", net_monthly, GREEN, True),
            ("", 0, TEXT, False),
            ("Expenses", -monthly_expenses, RED, False),
            ("Investment Contribution", -monthly_invest, BLUE, False),
            ("Surplus / Deficit", surplus, CYAN if surplus >= 0 else RED, True),
        ]
        for label, val, color, bold in cf_items:
            if label == "":
                st.markdown(f'<div style="height:.25rem;border-bottom:1px dashed {BORDER};margin:.15rem 0;"></div>', unsafe_allow_html=True)
            else:
                st.markdown(row_item(label, gbp(val), color, bold), unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)

    with cr:
        st.markdown(card("Monthly Outflow Split"), unsafe_allow_html=True)
        cf_labels = ["Expenses", "Investment", "Pension", "Surplus"]
        cf_vals = [monthly_expenses, monthly_invest, monthly_pension_contrib, max(0, surplus)]
        cf_colors = [RED, BLUE, GREEN, CYAN]
        fig = go.Figure(go.Pie(
            labels=cf_labels, values=cf_vals, hole=0.58,
            marker=dict(colors=cf_colors, line=dict(color=BG, width=2)),
            textinfo="label+percent", textfont=dict(size=11, color=TEXT, family="Inter"),
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}/mo<extra></extra>",
        ))
        fig.update_layout(**PL, height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_portfolio:
    st.markdown(section_header("Portfolio Overview", "△"), unsafe_allow_html=True)
    total_portfolio = investments + pension_val
    annual_growth_est = total_portfolio * expected_return / 100

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Total Portfolio", gbp(total_portfolio), PURPLE, "◈"), unsafe_allow_html=True)
    c2.markdown(kpi("Investments", gbp(investments), BLUE, "△"), unsafe_allow_html=True)
    c3.markdown(kpi("Pension", gbp(pension_val), GREEN, "◎"), unsafe_allow_html=True)
    c4.markdown(kpi("Est. Annual Growth", gbp(annual_growth_est), CYAN, "↗", sub=f"at {pct(expected_return)} return"), unsafe_allow_html=True)

    spacer("1rem")
    cl, cr = st.columns(2)

    with cl:
        st.markdown(card("Portfolio Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Investments", "Pension"], values=[investments, pension_val],
            hole=0.6, marker=dict(colors=[BLUE, GREEN], line=dict(color=BG, width=2)),
            textinfo="label+percent", textfont=dict(size=12, color=TEXT, family="Inter"),
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
        ))
        fig.update_layout(**PL, height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

    with cr:
        st.markdown(card("Annual Contributions"), unsafe_allow_html=True)
        contrib_labels = ["Investment", "Pension (employee)", "Pension (employer)"]
        contrib_vals = [monthly_invest * 12, employee_pension_annual, employer_pension_annual]
        contrib_colors = [BLUE, GREEN, CYAN]
        fig = go.Figure(go.Bar(
            x=contrib_labels, y=contrib_vals,
            marker=dict(color=contrib_colors, cornerradius=8, line=dict(width=0)),
            text=[gbp(v) for v in contrib_vals], textposition="auto",
            textfont=dict(color=TEXT, size=12, family="Inter"),
            hovertemplate="<b>%{x}</b><br>£%{y:,.0f}/yr<extra></extra>",
        ))
        fig.update_layout(**PL, height=320, xaxis=AXIS_CLEAN, yaxis=AXIS_CLEAN)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_forecast:
    st.markdown(section_header("Wealth Projection", "⟩"), unsafe_allow_html=True)

    milestones = sorted(set([m for m in [1, 5, 10, years_to_retire] if m <= years_to_retire]))
    cols = st.columns(len(milestones))
    for i, m in enumerate(milestones):
        row = df_base.loc[df_base["year"] == m]
        val = row["net_worth"].values[0] if len(row) > 0 else net_worth
        label = f"Year {m}" if m != years_to_retire else f"Retirement ({m}yr)"
        cols[i].markdown(kpi_small(label, gbp(val), PURPLE), unsafe_allow_html=True)

    spacer("1rem")

    st.markdown(card("Scenario Analysis", "Conservative · Base · Aggressive"), unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(df_aggressive["year"]) + list(df_conservative["year"][::-1]),
        y=list(df_aggressive["net_worth"]) + list(df_conservative["net_worth"][::-1]),
        fill="toself", fillcolor=f"{BLUE}10", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df_conservative["year"], y=df_conservative["net_worth"],
        name=f"Conservative ({pct(max(0,expected_return-2))})",
        line=dict(color=CLR_CONSERVATIVE, width=2.5, dash="dot"),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Conservative</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_base["year"], y=df_base["net_worth"],
        name=f"Base ({pct(expected_return)})",
        line=dict(color=CLR_BASE, width=3.5),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Base</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_aggressive["year"], y=df_aggressive["net_worth"],
        name=f"Aggressive ({pct(expected_return+2)})",
        line=dict(color=CLR_AGGRESSIVE, width=2.5, dash="dot"),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Aggressive</extra>",
    ))
    fig.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=1.5,
                  annotation_text=f"  Target: {gbp(target_wealth)}", annotation_font=dict(color=GREEN, size=11),
                  annotation_position="top left")
    fig.update_layout(
        **PL, height=440,
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
        xaxis=axis_opts(GRID, {"title": "Years", "titlefont": dict(color=TEXT3, size=11)}),
        yaxis=axis_opts(GRID, {"title": "Net Worth (£)", "titlefont": dict(color=TEXT3, size=11)}),
    )
    st.plotly_chart(fig, use_container_width=True, config=CFG)
    st.markdown(card_end(), unsafe_allow_html=True)

    spacer(".5rem")
    cl, cr = st.columns(2)

    with cl:
        st.markdown(card("Nominal vs Real (Inflation-Adjusted)"), unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_base["year"], y=df_base["net_worth"], name="Nominal",
            line=dict(color=BLUE, width=2.5), fill="tonexty", fillcolor=f"{BLUE}15",
            hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Nominal</extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=df_base["year"], y=df_base["net_worth_real"], name="Real",
            line=dict(color=CYAN, width=2.5),
            hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Real</extra>",
        ))
        fig2.update_layout(**PL, height=310,
                           legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                           xaxis=GRID, yaxis=GRID)
        st.plotly_chart(fig2, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)

    with cr:
        st.markdown(card("Retirement Scenario Comparison"), unsafe_allow_html=True)
        retire_vals = [
            df_conservative.iloc[-1]["net_worth"],
            df_base.iloc[-1]["net_worth"],
            df_aggressive.iloc[-1]["net_worth"],
        ]
        retire_labels = ["Conservative", "Base", "Aggressive"]
        retire_colors = [CLR_CONSERVATIVE, CLR_BASE, CLR_AGGRESSIVE]
        fig3 = go.Figure(go.Bar(
            x=retire_labels, y=retire_vals,
            marker=dict(color=retire_colors, cornerradius=8, line=dict(width=0)),
            text=[gbp(v) for v in retire_vals], textposition="auto",
            textfont=dict(color=TEXT, size=13, family="Inter"),
            hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>",
        ))
        fig3.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=1.5)
        fig3.update_layout(**PL, height=310, xaxis=AXIS_CLEAN, yaxis=AXIS_CLEAN)
        st.plotly_chart(fig3, use_container_width=True, config=CFG)
        st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_goals:
    st.markdown(section_header("Goal Tracking", "◎"), unsafe_allow_html=True)

    cl, cr = st.columns(2)

    with cl:
        st.markdown(card("Wealth Target Progress"), unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.3rem;">
            <span style="color:{TEXT2};font-size:.82rem;">Progress toward target</span>
            <span style="font-size:1.3rem;font-weight:800;
                background:linear-gradient(135deg,{PURPLE},{CYAN});
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                {pct(goal_progress)}</span>
        </div>
        {progress_bar(goal_progress, PURPLE, CYAN, 10)}
        <div style="display:flex;justify-content:space-between;margin-top:1rem;">
            <div>
                <div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Current</div>
                <div style="color:{TEXT};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(net_worth)}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Target</div>
                <div style="color:{GREEN};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(target_wealth)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)

    with cr:
        st.markdown(card("Gap Analysis"), unsafe_allow_html=True)
        total_saving_now = monthly_invest + monthly_pension_contrib + max(0, surplus)
        gap_items = [
            ("Remaining Gap", gbp(goal_gap), RED, True),
            ("Years to Retirement", str(years_to_retire), TEXT, False),
            ("Required Monthly Saving", f"{gbp(required_monthly)}/mo", AMBER, True),
            ("Current Monthly Saving", f"{gbp(total_saving_now)}/mo", GREEN, False),
        ]
        for label, val, color, bold in gap_items:
            st.markdown(row_item(label, val, color, bold), unsafe_allow_html=True)
        on_track = total_saving_now >= required_monthly
        status_color = GREEN if on_track else AMBER
        status_text = "On Track" if on_track else "Below Target"
        status_icon = "✓" if on_track else "!"
        st.markdown(f"""
        <div style="margin-top:.8rem;padding:.6rem .8rem;background:{status_color}15;border:1px solid {status_color}33;
            border-radius:10px;display:flex;align-items:center;gap:.5rem;">
            <span style="background:{status_color};color:{BG};font-weight:800;font-size:.75rem;
                width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;">
                {status_icon}</span>
            <span style="color:{status_color};font-weight:600;font-size:.85rem;">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(card_end(), unsafe_allow_html=True)

    spacer(".5rem")

    st.markdown(card("Projected Goal Achievement"), unsafe_allow_html=True)
    fig_g = go.Figure()
    fig_g.add_trace(go.Scatter(
        x=df_base["year"], y=df_base["net_worth"], name="Projected",
        line=dict(color=BLUE, width=3), fill="tozeroy", fillcolor=f"{BLUE}12",
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra></extra>",
    ))
    fig_g.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=2,
                    annotation_text=f"  Target: {gbp(target_wealth)}",
                    annotation_font=dict(color=GREEN, size=11), annotation_position="top left")
    crossing = df_base[df_base["net_worth"] >= target_wealth]
    if len(crossing) > 0:
        cy = int(crossing.iloc[0]["year"])
        fig_g.add_vline(x=cy, line_dash="dot", line_color=GREEN, line_width=1.5,
                        annotation_text=f"  Year {cy} (age {current_age + cy})",
                        annotation_font=dict(color=GREEN, size=11))
    fig_g.update_layout(**PL, height=360, showlegend=False,
                        xaxis=axis_opts(GRID, {"title": "Years"}), yaxis=GRID)
    st.plotly_chart(fig_g, use_container_width=True, config=CFG)
    st.markdown(card_end(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSUMPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_assumptions:
    region = "Scotland" if scotland_tax else "England / Wales / NI"
    st.markdown(section_header("Model Assumptions", "⚙"), unsafe_allow_html=True)

    st.markdown(card("Parameters"), unsafe_allow_html=True)
    assumptions = [
        ("Expected Investment Return", pct(expected_return), "Annual nominal return on invested assets & pension", BLUE),
        ("Inflation Rate", pct(inflation), "Used to calculate real (inflation-adjusted) values", CYAN),
        ("Property Growth Rate", pct(property_growth), "Annual property price appreciation", AMBER),
        ("Employer Pension Match", "3.0%", "Assumed employer pension contribution rate", GREEN),
        ("Mortgage Paydown", "~3%/yr", "Simplified annual principal reduction", TEXT2),
        ("CPI (current)", "3.0%", "Current headline CPI estimate", CYAN),
        ("Forecast Inflation (medium-term)", "2.3%", "BoE medium-term forecast", CYAN),
        ("Forecast Inflation (long-term)", "2.0%", "BoE long-term target", CYAN),
        ("NI Rates", "8% / 2%", "Employee NI: 8% (£12,570–£50,270), 2% above", AMBER),
        ("Tax Region", region, "Selected tax jurisdiction", PURPLE),
    ]
    for label, val, desc, color in assumptions:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid {BORDER};">
            <div>
                <div style="color:{TEXT};font-size:.88rem;font-weight:500;">{label}</div>
                <div style="color:{TEXT3};font-size:.72rem;margin-top:.1rem;">{desc}</div>
            </div>
            <span style="color:{color};font-weight:700;font-size:.95rem;white-space:nowrap;margin-left:1rem;">{val}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown(card_end(), unsafe_allow_html=True)

    spacer(".5rem")
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{SHADOW_SM};
    ">
        <div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.5rem;">Disclaimer</div>
        <div style="color:{TEXT3};font-size:.78rem;line-height:1.65;">
        This dashboard is for illustrative and educational purposes only. It does not constitute financial advice.
        Tax calculations are approximate and based on 2024-25 UK rates. Forecasts use simplified compound-growth
        models and do not account for market volatility, sequence-of-returns risk, or changes in tax legislation.
        Always consult a qualified financial adviser for personal financial decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GETTING STARTED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_guide:
    st.markdown(section_header("Getting Started", "◈"), unsafe_allow_html=True)

    def guide_step(num, title, desc, color=PURPLE):
        return f"""
        <div style="
            display:flex;gap:1rem;align-items:flex-start;padding:1rem 0;
            border-bottom:1px solid {BORDER};
        ">
            <div style="
                min-width:36px;height:36px;border-radius:10px;
                background:linear-gradient(135deg,{color}33,{color}11);
                border:1px solid {color}44;
                display:flex;align-items:center;justify-content:center;
                font-weight:800;font-size:.9rem;color:{color};
            ">{num}</div>
            <div>
                <div style="color:{TEXT};font-weight:600;font-size:.92rem;margin-bottom:.2rem;">{title}</div>
                <div style="color:{TEXT2};font-size:.82rem;line-height:1.55;">{desc}</div>
            </div>
        </div>"""

    st.markdown(card("How to Use This Dashboard"), unsafe_allow_html=True)
    st.markdown(f"""
    <div style="color:{TEXT2};font-size:.84rem;line-height:1.6;margin-bottom:.6rem;">
        WealthView helps you track your personal finances over time. Each month, you save a snapshot of your
        financial position. Over time, these snapshots build a picture of your wealth journey.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(guide_step("1", "Select a Reporting Period",
        "In the sidebar, choose the <b>Month</b> and <b>Year</b> your figures relate to. "
        "This is the point in time you are recording.",
        PURPLE), unsafe_allow_html=True)

    st.markdown(guide_step("2", "Enter Your Financial Figures",
        "Fill in the sidebar fields for: <b>Cash & Savings</b>, <b>Investments</b> (stocks & shares), "
        "<b>Pension</b>, <b>Property Value</b>, and <b>Mortgage Balance</b>. "
        "Also enter your income, expenses, and contribution details.",
        BLUE), unsafe_allow_html=True)

    st.markdown(guide_step("3", "Click Save Snapshot",
        "Press the <b>Save Snapshot</b> button at the bottom of the sidebar. "
        "This stores your figures for the selected period. If you update and save again for the same period, "
        "it replaces the previous values.",
        CYAN), unsafe_allow_html=True)

    st.markdown(guide_step("4", "View Your Progress Over Time",
        "Switch to the <b>History</b> tab to see your net worth tracked over time, month-on-month changes, "
        "and a detailed growth table. The more snapshots you save, the richer the picture.",
        GREEN), unsafe_allow_html=True)

    st.markdown(guide_step("5", "Explore Deeper Analysis",
        "Use the other tabs for more insight: <b>Salary & Tax</b> calculates your UK take-home pay, "
        "<b>Cash Flow</b> shows your monthly budget, <b>Portfolio</b> summarises your investments, "
        "<b>Forecast</b> projects your future wealth under different scenarios, "
        "and <b>Goals</b> tracks your progress toward a target.",
        AMBER), unsafe_allow_html=True)

    st.markdown(card_end(), unsafe_allow_html=True)

    spacer(".8rem")

    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);
        border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;
        box-shadow:{SHADOW_SM};
    ">
        <div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.6rem;">Tips for Best Results</div>
        <div style="display:flex;flex-direction:column;gap:.5rem;">
            <div style="display:flex;align-items:center;gap:.6rem;">
                <span style="color:{PURPLE};font-size:.75rem;">◈</span>
                <span style="color:{TEXT2};font-size:.82rem;">Save a snapshot at the same time each month for consistent tracking</span>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;">
                <span style="color:{BLUE};font-size:.75rem;">◈</span>
                <span style="color:{TEXT2};font-size:.82rem;">Monthly snapshots reveal trends, momentum, and seasonal patterns</span>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;">
                <span style="color:{CYAN};font-size:.75rem;">◈</span>
                <span style="color:{TEXT2};font-size:.82rem;">This dashboard is designed for manual tracking and personal financial planning</span>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;">
                <span style="color:{GREEN};font-size:.75rem;">◈</span>
                <span style="color:{TEXT2};font-size:.82rem;">Your data is stored locally in a JSON file alongside the app</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spacer("2rem")
st.markdown(f"""
<div style="text-align:center;padding:1rem 0;border-top:1px solid {BORDER};">
    <span style="color:{TEXT3};font-size:.7rem;letter-spacing:.06em;">
        ◈ WEALTHVIEW · PERSONAL FINANCE DASHBOARD · FOR ILLUSTRATIVE PURPOSES ONLY
    </span>
</div>
""", unsafe_allow_html=True)
