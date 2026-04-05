import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
BG = "#0B1020"
BG_ALT = "#0D1326"
CARD = "#131C31"
CARD_H = "#182240"
BORDER = "#1E2A45"
BORDER_L = "#253255"
TEXT = "#FFFFFF"
TEXT2 = "#94A3B8"
TEXT3 = "#64748B"
PURPLE = "#8B5CF6"
BLUE = "#3B82F6"
CYAN = "#06B6D4"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"

SHADOW = "0 4px 24px rgba(0,0,0,.35), 0 1px 4px rgba(0,0,0,.25)"
SHADOW_SM = "0 2px 12px rgba(0,0,0,.25)"
GLOW_P = f"0 0 20px {PURPLE}22, 0 4px 24px rgba(0,0,0,.35)"

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
*,*::before,*::after{{box-sizing:border-box;}}
html,body,.stApp{{background:{BG}!important;color:{TEXT};font-family:'Inter',system-ui,sans-serif!important;-webkit-font-smoothing:antialiased;}}
header[data-testid="stHeader"]{{background:{BG}!important;border-bottom:1px solid {BORDER};}}
.block-container{{padding:1.2rem 2rem 2rem 2rem!important;max-width:1400px;}}
div[data-testid="stToolbar"]{{display:none;}}
section[data-testid="stSidebar"]{{background:linear-gradient(180deg,{BG_ALT} 0%,#0A0F1E 100%)!important;border-right:1px solid {BORDER}!important;width:320px!important;}}
section[data-testid="stSidebar"] .block-container{{padding:1rem 1.2rem!important;}}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] .stMarkdown{{color:{TEXT2}!important;font-size:.82rem!important;font-family:'Inter',sans-serif!important;}}
section[data-testid="stSidebar"] .stNumberInput label,section[data-testid="stSidebar"] .stSlider label,section[data-testid="stSidebar"] .stSelectbox label,section[data-testid="stSidebar"] .stToggle label{{color:{TEXT2}!important;font-size:.78rem!important;letter-spacing:.02em;}}
section[data-testid="stSidebar"] input{{background:{CARD}!important;border:1px solid {BORDER}!important;color:{TEXT}!important;border-radius:8px!important;font-size:.85rem!important;}}
section[data-testid="stSidebar"] .stSlider > div > div > div{{background:{BORDER}!important;}}
section[data-testid="stSidebar"] .stSlider [role="slider"]{{background:{PURPLE}!important;}}
section[data-testid="stSidebar"] hr{{border-color:{BORDER}!important;margin:.6rem 0!important;}}
div[data-testid="stMetric"]{{display:none;}}
.stTabs{{margin-top:.2rem;}}
.stTabs [data-baseweb="tab-list"]{{gap:0;border-bottom:1px solid {BORDER};background:transparent;padding:0 .5rem;}}
.stTabs [data-baseweb="tab"]{{color:{TEXT3}!important;background:transparent!important;border:none!important;padding:.65rem 1.3rem!important;font-size:.82rem!important;font-weight:500;letter-spacing:.02em;border-radius:10px 10px 0 0!important;transition:all .2s ease;font-family:'Inter',sans-serif!important;}}
.stTabs [data-baseweb="tab"]:hover{{color:{TEXT2}!important;background:{CARD}55!important;}}
.stTabs [aria-selected="true"]{{color:{PURPLE}!important;background:{CARD}!important;border-bottom:2px solid {PURPLE}!important;font-weight:600;}}
.stTabs [data-baseweb="tab-highlight"]{{display:none;}}
.stTabs [data-baseweb="tab-border"]{{display:none;}}
.js-plotly-plot,.plotly{{background:transparent!important;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:{BG};}}
::-webkit-scrollbar-thumb{{background:{BORDER_L};border-radius:3px;}}
div[data-testid="column"] > div{{padding:0 .3rem;}}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPONENT LIBRARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def gbp(v):
    sign = "-" if v < 0 else ""
    return f"{sign}£{abs(v):,.0f}"


def pct_fmt(v):
    return f"{v:.1f}%"


def kpi(label, value, color=PURPLE, icon="", sub=""):
    sub_html = f'<div style="color:{TEXT3};font-size:.7rem;margin-top:.15rem;">{sub}</div>' if sub else ""
    icon_html = f'<span style="font-size:.95rem;margin-right:.25rem;">{icon}</span>' if icon else ""
    return f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:14px;padding:1.1rem 1.2rem;box-shadow:{SHADOW_SM};position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{color}88,transparent);"></div>
    <div style="color:{TEXT2};font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;font-weight:500;margin-bottom:.35rem;">{icon_html}{label}</div>
    <div style="font-size:1.45rem;font-weight:800;color:{color};letter-spacing:-.02em;line-height:1.15;">{value}</div>{sub_html}</div>"""


def kpi_small(label, value, color=TEXT):
    return f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:.75rem .9rem;text-align:center;">
    <div style="color:{TEXT3};font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;font-weight:500;">{label}</div>
    <div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:.2rem;">{value}</div></div>"""


def card_open(title="", subtitle=""):
    sub = f'<span style="color:{TEXT3};font-size:.72rem;font-weight:400;margin-left:.5rem;">{subtitle}</span>' if subtitle else ""
    h = f'<div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.7rem;letter-spacing:-.01em;">{title}{sub}</div>' if title else ""
    return f'<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{SHADOW};margin-bottom:.8rem;">{h}'


def card_close():
    return "</div>"


def section_header(title, icon=""):
    icon_html = f'<span style="margin-right:.4rem;">{icon}</span>' if icon else ""
    return f'<div style="display:flex;align-items:center;margin:1.8rem 0 1rem 0;padding-bottom:.55rem;border-bottom:1px solid {BORDER};"><div style="font-size:1.1rem;font-weight:700;color:{TEXT};letter-spacing:-.01em;">{icon_html}{title}</div></div>'


def sidebar_label(label, color=PURPLE):
    return f'<div style="color:{color};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;margin:.8rem 0 .35rem 0;padding-bottom:.25rem;border-bottom:1px solid {BORDER};">{label}</div>'


def row_item(label, value, color=TEXT, bold=False):
    fw = "700" if bold else "500"
    return f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem 0;border-bottom:1px solid {BORDER}08;"><span style="color:{TEXT2};font-size:.84rem;">{label}</span><span style="color:{color};font-weight:{fw};font-size:.9rem;">{value}</span></div>'


def progress_bar_html(pct_val, color_from=PURPLE, color_to=CYAN, height=8):
    w = max(0, min(100, pct_val))
    return f'<div style="background:{BORDER};border-radius:{height}px;height:{height}px;width:100%;margin-top:.3rem;overflow:hidden;"><div style="width:{w}%;height:100%;border-radius:{height}px;background:linear-gradient(90deg,{color_from},{color_to});transition:width .6s ease;"></div></div>'


def spacer(h="1rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAFE LAYOUT BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def make_layout(overrides=None):
    """Build a Plotly layout dict from PL_BASE with safe overrides."""
    base = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color=TEXT2, size=11, family="Inter, sans-serif"),
        "margin": dict(l=15, r=15, t=25, b=15),
        "legend": dict(font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
        "hoverlabel": dict(bgcolor=CARD, bordercolor=BORDER, font=dict(color=TEXT, size=12, family="Inter")),
    }
    if overrides:
        base.update(overrides)
    return base


GRID_AXIS = {"gridcolor": BORDER, "gridwidth": 1, "griddash": "dot", "zeroline": False}
CLEAN_AXIS = {"showgrid": False, "zeroline": False}
PLT_CFG = {"displayModeBar": False}

CLR_BASE = BLUE
CLR_AGG = PURPLE
CLR_CON = CYAN

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

LBL_CASH = "Cash Savings"
LBL_STOCK = "Stocks and Shares"
LBL_PENSION = "Pension"
LBL_HOUSE = "House Equity"


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
        t = amt * rate
        income_tax += t
        if amt > 0:
            band_breakdown.append({"band_width": amt, "rate": rate, "tax": t})
        remaining -= amt
        if remaining <= 0:
            break
    ni = 0.0
    if gross > 12_570:
        ni += max(0, min(gross, 50_270) - 12_570) * 0.08
    if gross > 50_270:
        ni += (gross - 50_270) * 0.02
    total_ded = income_tax + ni
    net_annual = gross - total_ded
    eff = (total_ded / gross * 100) if gross > 0 else 0
    return {"gross": gross, "personal_allowance": pa, "taxable_income": taxable,
            "income_tax": income_tax, "ni": ni, "total_deductions": total_ded,
            "net_annual": net_annual, "net_monthly": net_annual / 12,
            "effective_rate": eff, "band_breakdown": band_breakdown}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def forecast_wealth(s_liquid, s_invested, s_pension, m_invest, m_pension, m_surplus,
                    exp_ret, infl, prop_val, prop_gr, mort, years, emp_pension_yr=0):
    rows = []
    liquid, invested, pension, prop, mo = s_liquid, s_invested, s_pension, prop_val, mort
    for y in range(0, years + 1):
        eq = max(0, prop - mo)
        nw = liquid + invested + pension + eq
        rf = 1 / ((1 + infl / 100) ** y) if y > 0 else 1
        rows.append({"year": y, "liquid": liquid, "invested": invested, "pension": pension,
                      "house_equity": eq, "net_worth": nw, "net_worth_real": nw * rf})
        if y < years:
            invested *= (1 + exp_ret / 100)
            pension *= (1 + exp_ret / 100)
            prop *= (1 + prop_gr / 100)
            mo *= 0.97
            invested += m_invest * 12
            pension += m_pension * 12 + emp_pension_yr
            liquid += m_surplus * 12
    return pd.DataFrame(rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown(f"""<div style="text-align:center;padding:1rem 0 .6rem 0;">
    <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-.03em;">◈ WealthView</div>
    <div style="color:{TEXT3};font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;margin-top:.2rem;">Personal Finance Dashboard</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(sidebar_label("Reporting Period", PURPLE), unsafe_allow_html=True)
    now = datetime.now()
    rp1, rp2 = st.columns(2)
    with rp1:
        sel_month = st.selectbox("Month", MONTHS, index=now.month - 1)
    with rp2:
        sel_year = st.selectbox("Year", list(range(2020, now.year + 2)), index=min(now.year - 2020, now.year + 1 - 2020))
    period_key = f"{sel_year}-{MONTHS.index(sel_month)+1:02d}"
    period_label = f"{sel_month} {sel_year}"
    existing = st.session_state.snapshots.get(period_key, {})

    st.markdown("---")
    st.markdown(sidebar_label("Assets", GREEN), unsafe_allow_html=True)
    cash = st.number_input("Cash Savings (£)", 0, 10_000_000, int(existing.get("cash", 25_000)), 1_000)
    investments = st.number_input("Stocks and Shares (£)", 0, 50_000_000, int(existing.get("investments", 85_000)), 1_000)
    pension_val = st.number_input("Pension (£)", 0, 50_000_000, int(existing.get("pension", 42_000)), 1_000)
    property_val = st.number_input("Property Value (£)", 0, 50_000_000, int(existing.get("property", 350_000)), 5_000)

    st.markdown(sidebar_label("Liabilities", RED), unsafe_allow_html=True)
    mortgage = st.number_input("Mortgage Balance (£)", 0, 50_000_000, int(existing.get("mortgage", 220_000)), 5_000)

    st.markdown("---")
    st.markdown(sidebar_label("Income", BLUE), unsafe_allow_html=True)
    gross_salary = st.number_input("Gross Salary (£/yr)", 0, 5_000_000, int(existing.get("gross_salary", 65_000)), 1_000)
    annual_bonus = st.number_input("Annual Bonus (£)", 0, 2_000_000, int(existing.get("annual_bonus", 5_000)), 500)
    scotland_tax = st.toggle("Scottish Tax Bands", value=existing.get("scotland_tax", False))
    pension_contrib_pct = st.slider("Pension Contribution %", 0.0, 30.0, float(existing.get("pension_contrib_pct", 5.0)), 0.5)

    st.markdown("---")
    st.markdown(sidebar_label("Spending & Saving", AMBER), unsafe_allow_html=True)
    monthly_expenses = st.number_input("Monthly Expenses (£)", 0, 100_000, int(existing.get("monthly_expenses", 2_800)), 100)
    monthly_invest = st.number_input("Monthly Investment (£)", 0, 50_000, int(existing.get("monthly_invest", 500)), 50)

    st.markdown("---")
    st.markdown(sidebar_label("Forecast Assumptions", CYAN), unsafe_allow_html=True)
    current_age = st.number_input("Current Age", 18, 80, int(existing.get("current_age", 32)))
    retirement_age = st.number_input("Retirement Age", 30, 90, int(existing.get("retirement_age", 60)))
    target_wealth = st.number_input("Target Wealth (£)", 0, 100_000_000, int(existing.get("target_wealth", 1_000_000)), 50_000)
    expected_return = st.slider("Expected Return %", 0.0, 15.0, float(existing.get("expected_return", 7.0)), 0.5)
    inflation = st.slider("Inflation %", 0.0, 10.0, float(existing.get("inflation", 2.5)), 0.1)
    property_growth = st.slider("Property Growth %", 0.0, 10.0, float(existing.get("property_growth", 3.5)), 0.5)

    st.markdown("---")
    st.markdown(f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:12px;padding:.8rem 1rem;margin-bottom:.6rem;text-align:center;">
    <div style="color:{TEXT3};font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.2rem;">Reporting Period</div>
    <div style="color:{PURPLE};font-weight:700;font-size:1rem;">{period_label}</div></div>""", unsafe_allow_html=True)

    if st.button("Save Snapshot", type="primary", use_container_width=True):
        house_eq = max(0, property_val - mortgage)
        nw = cash + investments + pension_val + house_eq
        sd = {"cash": cash, "investments": investments, "pension": pension_val,
              "property": property_val, "mortgage": mortgage,
              "gross_salary": gross_salary, "annual_bonus": annual_bonus,
              "scotland_tax": scotland_tax, "pension_contrib_pct": pension_contrib_pct,
              "monthly_expenses": monthly_expenses, "monthly_invest": monthly_invest,
              "current_age": current_age, "retirement_age": retirement_age,
              "target_wealth": target_wealth, "expected_return": expected_return,
              "inflation": inflation, "property_growth": property_growth,
              "saved_at": datetime.now().isoformat(),
              "net_worth": nw, "house_equity": house_eq}
        st.session_state.snapshots[period_key] = sd
        save_snapshots(st.session_state.snapshots)
        st.session_state.snapshot_saved_flag = True
        st.rerun()

    if st.session_state.snapshot_saved_flag:
        st.markdown(f'<div style="background:{GREEN}18;border:1px solid {GREEN}44;border-radius:8px;padding:.5rem .7rem;text-align:center;margin-top:.3rem;"><span style="color:{GREEN};font-size:.8rem;font-weight:600;">Snapshot saved for {period_label}</span></div>', unsafe_allow_html=True)
        st.session_state.snapshot_saved_flag = False

    sc = len(st.session_state.snapshots)
    if sc > 0:
        st.markdown(f'<div style="color:{TEXT3};font-size:.72rem;text-align:center;margin-top:.4rem;">{sc} snapshot{"s" if sc != 1 else ""} saved</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_history_df(snaps):
    if not snaps:
        return pd.DataFrame()
    rows = []
    for pk, sd in sorted(snaps.items()):
        try:
            parts = pk.split("-")
            yr, mo = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            continue
        he = sd.get("house_equity", max(0, sd.get("property", 0) - sd.get("mortgage", 0)))
        rows.append({"period_key": pk, "date": datetime(yr, mo, 1),
                      "label": f"{MONTHS[mo - 1][:3]} {yr}",
                      "cash": sd.get("cash", 0),
                      "investments": sd.get("investments", 0),
                      "pension": sd.get("pension", 0),
                      "house_equity": he,
                      "net_worth": sd.get("net_worth", 0),
                      "property": sd.get("property", 0),
                      "mortgage": sd.get("mortgage", 0)})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df["nw_change"] = df["net_worth"].diff()
    df["nw_change_pct"] = df["net_worth"].pct_change() * 100
    return df


history_df = build_history_df(st.session_state.snapshots)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALCULATIONS
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
house_equity = max(0, property_val - mortgage)
net_worth = cash + investments + pension_val + house_equity
years_to_retire = max(1, retirement_age - current_age)

df_base = forecast_wealth(cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
                          expected_return, inflation, property_val, property_growth, mortgage,
                          years_to_retire, employer_pension_annual)
df_con = forecast_wealth(cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
                         max(0, expected_return - 2), inflation, property_val, property_growth, mortgage,
                         years_to_retire, employer_pension_annual)
df_agg = forecast_wealth(cash, investments, pension_val, monthly_invest, monthly_pension_contrib, surplus,
                         expected_return + 2, inflation, property_val, property_growth, mortgage,
                         years_to_retire, employer_pension_annual)

f10 = df_base.loc[df_base["year"] == min(10, years_to_retire), "net_worth"].values
forecast_10y_val = f10[0] if len(f10) > 0 else net_worth
goal_progress = min(100, net_worth / target_wealth * 100) if target_wealth > 0 else 0
goal_gap = max(0, target_wealth - net_worth)

if years_to_retire > 0 and expected_return > 0:
    r_m = expected_return / 100 / 12
    n = years_to_retire * 12
    fv_cur = net_worth * ((1 + r_m) ** n)
    shortfall = max(0, target_wealth - fv_cur)
    required_monthly = shortfall * r_m / (((1 + r_m) ** n) - 1) if (shortfall > 0 and r_m > 0) else 0
else:
    required_monthly = 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""<div style="display:flex;align-items:baseline;gap:.8rem;margin-bottom:.1rem;">
<span style="font-size:1.9rem;font-weight:900;letter-spacing:-.03em;background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">◈ WealthView</span>
<span style="color:{TEXT3};font-size:.78rem;letter-spacing:.04em;">Personal Wealth Management & Forecast</span></div>""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GETTING STARTED EXPANDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.expander("Getting Started — How to Use This Dashboard", expanded=False):
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:14px;padding:1.2rem 1.4rem;">
<div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.8rem;">Quick Start Guide</div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{PURPLE}22;border:1px solid {PURPLE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{PURPLE};">1</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Select a Reporting Period</div>
<div style="color:{TEXT2};font-size:.8rem;">Choose the month and year in the sidebar that your figures relate to.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{BLUE}22;border:1px solid {BLUE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{BLUE};">2</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Enter Your Figures</div>
<div style="color:{TEXT2};font-size:.8rem;">Fill in: <b>Cash Savings</b>, <b>Stocks and Shares</b>, <b>Pension</b>, <b>Property Value</b>, and <b>Mortgage</b>.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{CYAN}22;border:1px solid {CYAN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{CYAN};">3</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Click Save Snapshot</div>
<div style="color:{TEXT2};font-size:.8rem;">This stores your figures for that period. Saving again for the same month updates it.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{GREEN}22;border:1px solid {GREEN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{GREEN};">4</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">View Your Net Worth Over Time</div>
<div style="color:{TEXT2};font-size:.8rem;">The History tab shows charts and tables built from your saved snapshots.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;">
<div style="min-width:32px;height:32px;border-radius:8px;background:{AMBER}22;border:1px solid {AMBER}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{AMBER};">5</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Explore Deeper Analysis</div>
<div style="color:{TEXT2};font-size:.8rem;">Use Forecast, Goals, Cash Flow, and Salary Calculator tabs for planning.</div></div></div>

<div style="margin-top:.8rem;padding:.6rem .8rem;background:{PURPLE}10;border:1px solid {PURPLE}22;border-radius:10px;">
<div style="color:{TEXT2};font-size:.78rem;line-height:1.55;">
This dashboard works best when you save snapshots regularly. Monthly snapshots reveal trends and momentum over time. The app is designed for manual tracking and personal financial planning.</div></div>
</div>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab_overview, tab_history, tab_portfolio, tab_forecast, tab_goals, tab_assumptions, tab_cashflow, tab_salary = st.tabs(
    ["Overview", "History", "Portfolio", "Forecast", "Goals", "Assumptions", "Cash Flow", "Salary Calculator"]
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_overview:
    st.markdown(f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:12px;padding:.65rem 1.2rem;margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:.6rem;"><span style="color:{PURPLE};font-size:.85rem;">◈</span><span style="color:{TEXT2};font-size:.78rem;">Current Snapshot</span><span style="color:{TEXT};font-weight:700;font-size:.92rem;">{period_label}</span></div>
    <div style="color:{TEXT3};font-size:.72rem;">{len(st.session_state.snapshots)} snapshot{"s" if len(st.session_state.snapshots) != 1 else ""} saved</div></div>""", unsafe_allow_html=True)

    st.markdown(section_header("Financial Snapshot", "◈"), unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Net Worth", gbp(net_worth), PURPLE, "◈"), unsafe_allow_html=True)
    c2.markdown(kpi(LBL_CASH, gbp(cash), CYAN, "◇"), unsafe_allow_html=True)
    c3.markdown(kpi(LBL_STOCK, gbp(investments), BLUE, "△"), unsafe_allow_html=True)
    c4.markdown(kpi(LBL_PENSION, gbp(pension_val), GREEN, "◎"), unsafe_allow_html=True)
    spacer(".6rem")
    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(kpi(LBL_HOUSE, gbp(house_equity), AMBER, "⬡"), unsafe_allow_html=True)
    c6.markdown(kpi("Mortgage", gbp(-mortgage), RED, "▽"), unsafe_allow_html=True)
    c7.markdown(kpi("Monthly Surplus", gbp(surplus), CYAN if surplus >= 0 else RED, "↗" if surplus >= 0 else "↘"), unsafe_allow_html=True)
    c8.markdown(kpi("Savings Rate", pct_fmt(savings_rate), PURPLE, "◉"), unsafe_allow_html=True)

    spacer("1.2rem")
    st.markdown(section_header("Wealth Composition"), unsafe_allow_html=True)
    col_d, col_b = st.columns([1, 1.1])

    with col_d:
        st.markdown(card_open("Net Worth Allocation"), unsafe_allow_html=True)
        labels = [LBL_CASH, LBL_STOCK, LBL_PENSION, LBL_HOUSE]
        values = [cash, investments, pension_val, house_equity]
        colors = [CYAN, BLUE, GREEN, AMBER]
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62,
                               marker=dict(colors=colors, line=dict(color=BG, width=2)),
                               textinfo="label+percent", textfont=dict(size=11, color=TEXT, family="Inter"),
                               hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
                               direction="clockwise", sort=False))
        fig.update_layout(**make_layout({"height": 370, "showlegend": False}))
        fig.add_annotation(text=f"<b>{gbp(net_worth)}</b>", x=0.5, y=0.54,
                           font=dict(size=19, color=TEXT, family="Inter"), showarrow=False)
        fig.add_annotation(text="NET WORTH", x=0.5, y=0.43,
                           font=dict(size=8.5, color=TEXT3, family="Inter"), showarrow=False)
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with col_b:
        st.markdown(card_open("Asset & Liability Breakdown"), unsafe_allow_html=True)
        cats = [LBL_CASH, LBL_STOCK, LBL_PENSION, LBL_HOUSE, "Mortgage"]
        vals = [cash, investments, pension_val, house_equity, -mortgage]
        clrs = [CYAN, BLUE, GREEN, AMBER, RED]
        fig = go.Figure(go.Bar(x=vals, y=cats, orientation="h",
                               marker=dict(color=clrs, cornerradius=6),
                               text=[gbp(v) for v in vals], textposition="auto",
                               textfont=dict(color=TEXT, size=11, family="Inter"),
                               hovertemplate="<b>%{y}</b>: £%{x:,.0f}<extra></extra>"))
        fig.update_layout(**make_layout({
            "height": 370,
            "yaxis": {**CLEAN_AXIS, "autorange": "reversed", "tickfont": dict(color=TEXT2, size=11)},
            "xaxis": {**CLEAN_AXIS, "zeroline": True, "zerolinecolor": BORDER_L, "zerolinewidth": 1},
        }))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    st.markdown(f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{GLOW_P};text-align:center;margin-top:.4rem;">
    <div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:500;">10-Year Projected Net Worth</div>
    <div style="font-size:2.2rem;font-weight:900;letter-spacing:-.03em;margin-top:.3rem;background:linear-gradient(135deg,{PURPLE},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{gbp(forecast_10y_val)}</div></div>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_history:
    st.markdown(section_header("Snapshot History", "◷"), unsafe_allow_html=True)
    if history_df.empty:
        st.markdown(f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:2.5rem 2rem;box-shadow:{SHADOW};text-align:center;">
        <div style="font-size:2rem;margin-bottom:.6rem;">◈</div>
        <div style="color:{TEXT};font-size:1.05rem;font-weight:600;margin-bottom:.4rem;">No snapshots yet</div>
        <div style="color:{TEXT3};font-size:.82rem;line-height:1.6;max-width:420px;margin:0 auto;">Select a reporting period, enter your figures, and click <span style="color:{PURPLE};font-weight:600;">Save Snapshot</span> to start tracking.</div></div>""", unsafe_allow_html=True)
    else:
        if len(history_df) >= 2:
            latest = history_df.iloc[-1]
            prev = history_df.iloc[-2]
            change = latest["net_worth"] - prev["net_worth"]
            change_pct = (change / prev["net_worth"] * 100) if prev["net_worth"] != 0 else 0
            cc = GREEN if change >= 0 else RED
            ci = "↗" if change >= 0 else "↘"
            c1, c2, c3 = st.columns(3)
            c1.markdown(kpi("Latest Net Worth", gbp(latest["net_worth"]), PURPLE, "◈", sub=latest["label"]), unsafe_allow_html=True)
            c2.markdown(kpi("Month-on-Month Change", gbp(change), cc, ci), unsafe_allow_html=True)
            c3.markdown(kpi("Growth Rate", pct_fmt(change_pct), cc, ci), unsafe_allow_html=True)
            spacer("1rem")

        # Net worth line chart
        st.markdown(card_open("Net Worth Over Time"), unsafe_allow_html=True)
        view_mode = st.radio("View", ["Monthly", "Yearly"], horizontal=True, label_visibility="collapsed")
        if view_mode == "Yearly" and len(history_df) > 0:
            yearly = history_df.copy()
            yearly["year"] = yearly["date"].dt.year
            yearly = yearly.groupby("year").last().reset_index()
            cx, cy_vals = yearly["year"].astype(str), yearly["net_worth"]
        else:
            cx, cy_vals = history_df["label"], history_df["net_worth"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cx, y=cy_vals, mode="lines+markers",
                                 line=dict(color=PURPLE, width=3),
                                 marker=dict(size=8, color=PURPLE, line=dict(color=BG, width=2)),
                                 hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>"))
        fig.update_layout(**make_layout({"height": 380, "showlegend": False, "xaxis": GRID_AXIS, "yaxis": GRID_AXIS}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

        # Stacked bar breakdown
        if len(history_df) >= 2:
            spacer(".5rem")
            st.markdown(card_open("Asset Breakdown Over Time"), unsafe_allow_html=True)
            fig2 = go.Figure()
            for col_name, lbl, clr in [("cash", LBL_CASH, CYAN), ("investments", LBL_STOCK, BLUE),
                                        ("pension", LBL_PENSION, GREEN), ("house_equity", LBL_HOUSE, AMBER)]:
                fig2.add_trace(go.Bar(x=history_df["label"], y=history_df[col_name], name=lbl,
                                      marker=dict(color=clr, cornerradius=4),
                                      hovertemplate=f"<b>{lbl}</b><br>" + "%{x}: £%{y:,.0f}<extra></extra>"))
            fig2.update_layout(**make_layout({
                "height": 350,
                "barmode": "stack",
                "legend": dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                               font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
                "xaxis": GRID_AXIS,
                "yaxis": GRID_AXIS,
            }))
            st.plotly_chart(fig2, use_container_width=True, config=PLT_CFG)
            st.markdown(card_close(), unsafe_allow_html=True)

        # Growth table
        spacer(".5rem")
        st.markdown(card_open("Month-to-Month Growth"), unsafe_allow_html=True)
        th = f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:.82rem;"><thead><tr style="border-bottom:2px solid {BORDER};"><th style="text-align:left;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Period</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Net Worth</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Change</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT2};font-weight:600;">Growth</th></tr></thead><tbody>'
        for _, row in history_df.iterrows():
            chg = row.get("nw_change", None)
            if pd.isna(chg) or chg is None:
                cs, ps, cc2 = "—", "—", TEXT3
            else:
                cc2 = GREEN if chg >= 0 else RED
                cs = gbp(chg)
                ps = pct_fmt(row["nw_change_pct"])
            th += f'<tr style="border-bottom:1px solid {BORDER};"><td style="padding:.45rem .6rem;color:{TEXT};">{row["label"]}</td><td style="padding:.45rem .6rem;color:{TEXT};text-align:right;font-weight:600;">{gbp(row["net_worth"])}</td><td style="padding:.45rem .6rem;color:{cc2};text-align:right;">{cs}</td><td style="padding:.45rem .6rem;color:{cc2};text-align:right;">{ps}</td></tr>'
        th += "</tbody></table></div>"
        st.markdown(th, unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

        # Manage snapshots
        spacer(".5rem")
        st.markdown(card_open("Manage Snapshots"), unsafe_allow_html=True)
        del_keys = sorted(st.session_state.snapshots.keys())
        del_labels = [f"{MONTHS[int(k.split('-')[1]) - 1]} {k.split('-')[0]}" for k in del_keys]
        if del_labels:
            dc1, dc2 = st.columns([2, 1])
            with dc1:
                del_choice = st.selectbox("Select snapshot to remove", del_labels, label_visibility="collapsed")
            with dc2:
                if st.button("Delete Snapshot", type="secondary", use_container_width=True):
                    idx = del_labels.index(del_choice)
                    del st.session_state.snapshots[del_keys[idx]]
                    save_snapshots(st.session_state.snapshots)
                    st.rerun()
        st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_portfolio:
    st.markdown(section_header("Portfolio Overview", "△"), unsafe_allow_html=True)
    total_portfolio = investments + pension_val
    annual_growth_est = total_portfolio * expected_return / 100

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Total Portfolio", gbp(total_portfolio), PURPLE, "◈"), unsafe_allow_html=True)
    c2.markdown(kpi(LBL_STOCK, gbp(investments), BLUE, "△"), unsafe_allow_html=True)
    c3.markdown(kpi(LBL_PENSION, gbp(pension_val), GREEN, "◎"), unsafe_allow_html=True)
    c4.markdown(kpi("Est. Annual Growth", gbp(annual_growth_est), CYAN, "↗", sub=f"at {pct_fmt(expected_return)} return"), unsafe_allow_html=True)

    spacer("1rem")
    cl, cr = st.columns(2)
    with cl:
        st.markdown(card_open("Portfolio Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(labels=[LBL_STOCK, LBL_PENSION], values=[investments, pension_val],
                               hole=0.6, marker=dict(colors=[BLUE, GREEN], line=dict(color=BG, width=2)),
                               textinfo="label+percent", textfont=dict(size=12, color=TEXT, family="Inter"),
                               hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>"))
        fig.update_layout(**make_layout({"height": 320, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with cr:
        st.markdown(card_open("Annual Contributions"), unsafe_allow_html=True)
        fig = go.Figure(go.Bar(x=["Investment", "Pension (you)", "Pension (employer)"],
                               y=[monthly_invest * 12, employee_pension_annual, employer_pension_annual],
                               marker=dict(color=[BLUE, GREEN, CYAN], cornerradius=8),
                               text=[gbp(monthly_invest * 12), gbp(employee_pension_annual), gbp(employer_pension_annual)],
                               textposition="auto", textfont=dict(color=TEXT, size=12, family="Inter"),
                               hovertemplate="<b>%{x}</b><br>£%{y:,.0f}/yr<extra></extra>"))
        fig.update_layout(**make_layout({"height": 320, "xaxis": CLEAN_AXIS, "yaxis": CLEAN_AXIS}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_forecast:
    st.markdown(section_header("Wealth Projection", "⟩"), unsafe_allow_html=True)
    milestones = sorted(set([m for m in [1, 5, 10, years_to_retire] if m <= years_to_retire]))
    cols = st.columns(len(milestones))
    for i, m in enumerate(milestones):
        r = df_base.loc[df_base["year"] == m]
        v = r["net_worth"].values[0] if len(r) > 0 else net_worth
        lb = f"Year {m}" if m != years_to_retire else f"Retirement ({m}yr)"
        cols[i].markdown(kpi_small(lb, gbp(v), PURPLE), unsafe_allow_html=True)
    spacer("1rem")

    # Scenario chart
    st.markdown(card_open("Scenario Analysis", "Conservative · Base · Aggressive"), unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_con["year"], y=df_con["net_worth"],
                             name=f"Conservative ({pct_fmt(max(0, expected_return - 2))})",
                             line=dict(color=CLR_CON, width=2.5, dash="dot"),
                             hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Conservative</extra>"))
    fig.add_trace(go.Scatter(x=df_base["year"], y=df_base["net_worth"],
                             name=f"Base ({pct_fmt(expected_return)})",
                             line=dict(color=CLR_BASE, width=3.5),
                             hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Base</extra>"))
    fig.add_trace(go.Scatter(x=df_agg["year"], y=df_agg["net_worth"],
                             name=f"Aggressive ({pct_fmt(expected_return + 2)})",
                             line=dict(color=CLR_AGG, width=2.5, dash="dot"),
                             hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Aggressive</extra>"))
    fig.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=1.5,
                  annotation_text=f"  Target: {gbp(target_wealth)}", annotation_font=dict(color=GREEN, size=11),
                  annotation_position="top left")
    fig.update_layout(**make_layout({
        "height": 440,
        "legend": dict(orientation="h", y=-0.1, x=0.5, xanchor="center",
                       font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
        "xaxis": {**GRID_AXIS, "title": "Years", "titlefont": dict(color=TEXT3, size=11)},
        "yaxis": {**GRID_AXIS, "title": "Net Worth (£)", "titlefont": dict(color=TEXT3, size=11)},
    }))
    st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
    st.markdown(card_close(), unsafe_allow_html=True)

    spacer(".5rem")
    cl, cr = st.columns(2)
    with cl:
        st.markdown(card_open("Nominal vs Real (Inflation-Adjusted)"), unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_base["year"], y=df_base["net_worth"], name="Nominal",
                                  line=dict(color=BLUE, width=2.5),
                                  hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Nominal</extra>"))
        fig2.add_trace(go.Scatter(x=df_base["year"], y=df_base["net_worth_real"], name="Real",
                                  line=dict(color=CYAN, width=2.5),
                                  hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Real</extra>"))
        fig2.update_layout(**make_layout({
            "height": 310,
            "legend": dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                           font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
            "xaxis": GRID_AXIS, "yaxis": GRID_AXIS,
        }))
        st.plotly_chart(fig2, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with cr:
        st.markdown(card_open("Retirement Scenario Comparison"), unsafe_allow_html=True)
        rv = [df_con.iloc[-1]["net_worth"], df_base.iloc[-1]["net_worth"], df_agg.iloc[-1]["net_worth"]]
        fig3 = go.Figure(go.Bar(x=["Conservative", "Base", "Aggressive"], y=rv,
                                marker=dict(color=[CLR_CON, CLR_BASE, CLR_AGG], cornerradius=8),
                                text=[gbp(v) for v in rv], textposition="auto",
                                textfont=dict(color=TEXT, size=13, family="Inter"),
                                hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>"))
        fig3.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=1.5)
        fig3.update_layout(**make_layout({"height": 310, "xaxis": CLEAN_AXIS, "yaxis": CLEAN_AXIS}))
        st.plotly_chart(fig3, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_goals:
    st.markdown(section_header("Goal Tracking", "◎"), unsafe_allow_html=True)
    cl, cr = st.columns(2)
    with cl:
        st.markdown(card_open("Wealth Target Progress"), unsafe_allow_html=True)
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.3rem;">
        <span style="color:{TEXT2};font-size:.82rem;">Progress toward target</span>
        <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{PURPLE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{pct_fmt(goal_progress)}</span></div>
        {progress_bar_html(goal_progress, PURPLE, CYAN, 10)}
        <div style="display:flex;justify-content:space-between;margin-top:1rem;">
        <div><div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Current</div><div style="color:{TEXT};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(net_worth)}</div></div>
        <div style="text-align:right;"><div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Target</div><div style="color:{GREEN};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(target_wealth)}</div></div></div>""", unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    with cr:
        st.markdown(card_open("Gap Analysis"), unsafe_allow_html=True)
        total_saving_now = monthly_invest + monthly_pension_contrib + max(0, surplus)
        for lb, vl, cl2, bd in [("Remaining Gap", gbp(goal_gap), RED, True),
                                 ("Years to Retirement", str(years_to_retire), TEXT, False),
                                 ("Required Monthly Saving", f"{gbp(required_monthly)}/mo", AMBER, True),
                                 ("Current Monthly Saving", f"{gbp(total_saving_now)}/mo", GREEN, False)]:
            st.markdown(row_item(lb, vl, cl2, bd), unsafe_allow_html=True)
        on_track = total_saving_now >= required_monthly
        sc2 = GREEN if on_track else AMBER
        st2 = "On Track" if on_track else "Below Target"
        si2 = "✓" if on_track else "!"
        st.markdown(f'<div style="margin-top:.8rem;padding:.6rem .8rem;background:{sc2}15;border:1px solid {sc2}33;border-radius:10px;display:flex;align-items:center;gap:.5rem;"><span style="background:{sc2};color:{BG};font-weight:800;font-size:.75rem;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;">{si2}</span><span style="color:{sc2};font-weight:600;font-size:.85rem;">{st2}</span></div>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    spacer(".5rem")
    st.markdown(card_open("Projected Goal Achievement"), unsafe_allow_html=True)
    fig_g = go.Figure()
    fig_g.add_trace(go.Scatter(x=df_base["year"], y=df_base["net_worth"], name="Projected",
                               line=dict(color=BLUE, width=3),
                               hovertemplate="Year %{x}<br>£%{y:,.0f}<extra></extra>"))
    fig_g.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=2,
                    annotation_text=f"  Target: {gbp(target_wealth)}",
                    annotation_font=dict(color=GREEN, size=11), annotation_position="top left")
    crossing = df_base[df_base["net_worth"] >= target_wealth]
    if len(crossing) > 0:
        cy = int(crossing.iloc[0]["year"])
        fig_g.add_vline(x=cy, line_dash="dot", line_color=GREEN, line_width=1.5,
                        annotation_text=f"  Year {cy} (age {current_age + cy})",
                        annotation_font=dict(color=GREEN, size=11))
    fig_g.update_layout(**make_layout({
        "height": 360, "showlegend": False,
        "xaxis": {**GRID_AXIS, "title": "Years"}, "yaxis": GRID_AXIS,
    }))
    st.plotly_chart(fig_g, use_container_width=True, config=PLT_CFG)
    st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSUMPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_assumptions:
    region = "Scotland" if scotland_tax else "England / Wales / NI"
    st.markdown(section_header("Model Assumptions", "⚙"), unsafe_allow_html=True)
    st.markdown(card_open("Parameters"), unsafe_allow_html=True)
    for lb, vl, desc, clr in [
        ("Expected Investment Return", pct_fmt(expected_return), "Annual nominal return on invested assets & pension", BLUE),
        ("Inflation Rate", pct_fmt(inflation), "Used to calculate real (inflation-adjusted) values", CYAN),
        ("Property Growth Rate", pct_fmt(property_growth), "Annual property price appreciation", AMBER),
        ("Employer Pension Match", "3.0%", "Assumed employer pension contribution rate", GREEN),
        ("Mortgage Paydown", "~3%/yr", "Simplified annual principal reduction", TEXT2),
        ("CPI (current)", "3.0%", "Current headline CPI estimate", CYAN),
        ("Forecast Inflation (medium-term)", "2.3%", "BoE medium-term forecast", CYAN),
        ("Forecast Inflation (long-term)", "2.0%", "BoE long-term target", CYAN),
        ("NI Rates", "8% / 2%", "Employee NI: 8% (£12,570–£50,270), 2% above", AMBER),
        ("Tax Region", region, "Selected tax jurisdiction", PURPLE),
    ]:
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid {BORDER};"><div><div style="color:{TEXT};font-size:.88rem;font-weight:500;">{lb}</div><div style="color:{TEXT3};font-size:.72rem;margin-top:.1rem;">{desc}</div></div><span style="color:{clr};font-weight:700;font-size:.95rem;white-space:nowrap;margin-left:1rem;">{vl}</span></div>', unsafe_allow_html=True)
    st.markdown(card_close(), unsafe_allow_html=True)
    spacer(".5rem")
    st.markdown(f'<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{SHADOW_SM};"><div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.5rem;">Disclaimer</div><div style="color:{TEXT3};font-size:.78rem;line-height:1.65;">This dashboard is for illustrative and educational purposes only. It does not constitute financial advice. Tax calculations are approximate and based on 2024-25 UK rates. Forecasts use simplified compound-growth models and do not account for market volatility, sequence-of-returns risk, or changes in tax legislation. Always consult a qualified financial adviser for personal financial decisions.</div></div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CASH FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_cashflow:
    st.markdown(section_header("Monthly Cash Flow", "↔"), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_small("Net Income", gbp(net_monthly), GREEN), unsafe_allow_html=True)
    c2.markdown(kpi_small("Total Outflows", gbp(monthly_expenses + monthly_invest + monthly_pension_contrib), AMBER), unsafe_allow_html=True)
    c3.markdown(kpi_small("Savings Rate", pct_fmt(savings_rate), PURPLE), unsafe_allow_html=True)
    spacer(".8rem")
    cl, cr = st.columns(2)
    with cl:
        st.markdown(card_open("Cash Flow Statement"), unsafe_allow_html=True)
        for lb, vl, clr, bd in [
            ("Gross Monthly Income", total_gross / 12, TEXT, False),
            ("Tax & NI", -tax["total_deductions"] / 12, RED, False),
            ("Pension (employee)", -monthly_pension_contrib, AMBER, False),
            ("Net Monthly Income", net_monthly, GREEN, True),
        ]:
            st.markdown(row_item(lb, gbp(vl), clr, bd), unsafe_allow_html=True)
        st.markdown(f'<div style="height:.25rem;border-bottom:1px dashed {BORDER};margin:.15rem 0;"></div>', unsafe_allow_html=True)
        for lb, vl, clr, bd in [
            ("Expenses", -monthly_expenses, RED, False),
            ("Investment Contribution", -monthly_invest, BLUE, False),
            ("Surplus / Deficit", surplus, CYAN if surplus >= 0 else RED, True),
        ]:
            st.markdown(row_item(lb, gbp(vl), clr, bd), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    with cr:
        st.markdown(card_open("Monthly Outflow Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Expenses", "Investment", "Pension", "Surplus"],
            values=[monthly_expenses, monthly_invest, monthly_pension_contrib, max(0, surplus)],
            hole=0.58, marker=dict(colors=[RED, BLUE, GREEN, CYAN], line=dict(color=BG, width=2)),
            textinfo="label+percent", textfont=dict(size=11, color=TEXT, family="Inter"),
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}/mo<extra></extra>"))
        fig.update_layout(**make_layout({"height": 350, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SALARY CALCULATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_salary:
    st.markdown(f"""<div style="display:flex;align-items:baseline;gap:.6rem;margin:1rem 0 .5rem 0;">
    <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{PURPLE},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">UK Salary Calculator</span>
    <span style="color:{TEXT3};font-size:.75rem;">{"Scotland" if scotland_tax else "England / Wales / NI"} · 2024-25 rates</span></div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="color:{TEXT3};font-size:.8rem;margin-bottom:1rem;">A standalone take-home pay calculator. Adjust gross salary, bonus, and pension contribution in the sidebar.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Gross Income", gbp(total_gross), TEXT, ""), unsafe_allow_html=True)
    c2.markdown(kpi("Take Home (Annual)", gbp(tax["net_annual"]), GREEN, ""), unsafe_allow_html=True)
    c3.markdown(kpi("Take Home (Monthly)", gbp(tax["net_monthly"]), GREEN, ""), unsafe_allow_html=True)
    c4.markdown(kpi("Effective Tax Rate", pct_fmt(tax["effective_rate"]), PURPLE, ""), unsafe_allow_html=True)

    spacer("1rem")
    cl, cr = st.columns([1.15, 0.85])

    with cl:
        st.markdown(card_open("Income Statement"), unsafe_allow_html=True)
        for lb, vl, clr, bd in [
            ("Gross Income (salary + bonus)", total_gross, TEXT, False),
            ("Pension Contribution (employee)", -employee_pension_annual, AMBER, False),
            ("Taxable Income", tax["taxable_income"], TEXT, True),
            ("Personal Allowance", tax["personal_allowance"], TEXT2, False),
            ("Income Tax", -tax["income_tax"], RED, False),
            ("National Insurance", -tax["ni"], RED, False),
            ("Total Deductions", -tax["total_deductions"], RED, True),
            ("Net Annual Income", tax["net_annual"], GREEN, True),
            ("Net Monthly Income", tax["net_monthly"], GREEN, True),
        ]:
            st.markdown(row_item(lb, gbp(vl), clr, bd), unsafe_allow_html=True)
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.7rem 0 .2rem 0;margin-top:.3rem;"><span style="color:{PURPLE};font-weight:700;font-size:.9rem;">Effective Tax Rate</span><span style="font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,{PURPLE},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{pct_fmt(tax["effective_rate"])}</span></div>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    with cr:
        st.markdown(card_open("Tax Composition"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(labels=["Income Tax", "National Insurance", "Net Pay"],
                               values=[tax["income_tax"], tax["ni"], tax["net_annual"]],
                               hole=0.58, marker=dict(colors=[RED, AMBER, GREEN], line=dict(color=BG, width=2)),
                               textinfo="label+percent", textfont=dict(size=10.5, color=TEXT, family="Inter"),
                               hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>"))
        fig.update_layout(**make_layout({"height": 280, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

        st.markdown(card_open("Tax Band Detail"), unsafe_allow_html=True)
        if tax["band_breakdown"]:
            for b in tax["band_breakdown"]:
                st.markdown(row_item(f"{pct_fmt(b['rate'] * 100)} on {gbp(b['band_width'])}", gbp(b['tax']), RED), unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:{TEXT3};font-size:.82rem;">No tax bands applicable</span>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spacer("2rem")
st.markdown(f'<div style="text-align:center;padding:1rem 0;border-top:1px solid {BORDER};"><span style="color:{TEXT3};font-size:.7rem;letter-spacing:.06em;">◈ WEALTHVIEW · PERSONAL FINANCE DASHBOARD · FOR ILLUSTRATIVE PURPOSES ONLY</span></div>', unsafe_allow_html=True)
