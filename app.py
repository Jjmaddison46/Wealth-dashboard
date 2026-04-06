import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import re
import html
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="WealthView",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
TEXT2 = "#C7D2E3"
TEXT3 = "#94A3B8"

PURPLE = "#8B5CF6"
BLUE = "#3B82F6"
CYAN = "#06B6D4"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
YELLOW = "#FFD60A"
WHITE = "#FFFFFF"
BLACK = "#000000"

SHADOW = "0 4px 24px rgba(0,0,0,.35), 0 1px 4px rgba(0,0,0,.25)"
SHADOW_SM = "0 2px 12px rgba(0,0,0,.25)"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

LBL_CASH = "Cash Savings"
LBL_STOCK = "Stock and Shares"
LBL_CRYPTO = "Crypto"
LBL_PENSION = "Pension"
LBL_RE = "Real Estate Equity"

BOLD_WHITE = dict(color=TEXT, size=13, family="Inter, sans-serif")
BOLD_WHITE_SM = dict(color=TEXT, size=11, family="Inter, sans-serif")

GRID_AXIS = {"gridcolor": BORDER, "gridwidth": 1, "zeroline": False}
CLEAN_AXIS = {"showgrid": False, "zeroline": False}
PLT_CFG = {"displayModeBar": False}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PERSISTENCE
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

DEFAULT_SETTINGS = {
    "gross_salary": 180_000,
    "annual_bonus": 0,
    "scotland_tax": False,
    "pension_contrib_pct": 3.0,
    "monthly_invest": 2_000,
    "monthly_expenses": 0,
    "current_age": 35,
    "retirement_age": 50,
    "target_wealth": 2_000_000,
    "expected_return": 12.0,
    "inflation": 2.5,
    "property_growth": 3.5,
    "selected_scenario": "Base",
}

for key, value in DEFAULT_SETTINGS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after {{
    box-sizing: border-box;
}}

html, body, .stApp {{
    background: {BG} !important;
    color: {TEXT};
    font-family: 'Inter', system-ui, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}}

header[data-testid="stHeader"] {{
    background: {BG} !important;
    border-bottom: 1px solid {BORDER};
}}

.block-container {{
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1460px;
}}

div[data-testid="stToolbar"] {{
    display: none;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_ALT} 0%, #0A0F1E 100%) !important;
    border-right: 1px solid {BORDER} !important;
    width: 345px !important;
}}

section[data-testid="stSidebar"] .block-container {{
    padding: 1rem 1.2rem 1.5rem 1.2rem !important;
}}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown {{
    color: {TEXT2} !important;
    font-size: .82rem !important;
    font-family: 'Inter', sans-serif !important;
}}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stToggle label,
section[data-testid="stSidebar"] .stTextInput label {{
    color: {WHITE} !important;
    font-size: .84rem !important;
    font-weight: 700 !important;
    letter-spacing: .01em;
}}

section[data-testid="stSidebar"] input {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 10px !important;
    font-size: .92rem !important;
}}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background: #F8FAFC !important;
    color: {BLACK} !important;
    border-radius: 10px !important;
}}

section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{
    color: {BLACK} !important;
    fill: {BLACK} !important;
}}

section[data-testid="stSidebar"] .stSlider > div {{
    padding-top: .15rem;
}}

section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {{
    padding-top: .35rem !important;
    padding-bottom: .2rem !important;
}}

section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div {{
    height: 10px !important;
}}

section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {{
    border-radius: 999px !important;
}}

section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div:first-child {{
    background: rgba(203, 213, 225, 0.20) !important;
}}

section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div:nth-child(2) {{
    background: linear-gradient(90deg, #FFE347 0%, #FFC300 100%) !important;
    opacity: 1 !important;
}}

section[data-testid="stSidebar"] .stSlider [role="slider"] {{
    background: #FFFFFF !important;
    border: 3px solid #D1D5DB !important;
    box-shadow: 0 0 0 5px rgba(255, 214, 10, 0.22) !important;
}}

section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSlider p,
section[data-testid="stSidebar"] .stSlider span,
section[data-testid="stSidebar"] .stSlider small {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
    background: transparent !important;
    text-shadow: none !important;
}}

section[data-testid="stSidebar"] .stSlider [data-testid="stWidgetLabel"] * {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}

section[data-testid="stSidebar"] .stButton > button {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 1px solid {WHITE} !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    box-shadow: none !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: #F3F4F6 !important;
    color: {BLACK} !important;
    border: 1px solid #F3F4F6 !important;
}}

div[data-testid="stMetric"] {{
    display: none;
}}

.stTabs {{
    margin-top: .25rem;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {BORDER};
    background: transparent;
    padding: 0 .5rem;
}}

.stTabs [data-baseweb="tab"] {{
    color: {TEXT3} !important;
    background: transparent !important;
    border: none !important;
    padding: .65rem 1.3rem !important;
    font-size: .82rem !important;
    font-weight: 500;
    letter-spacing: .02em;
    border-radius: 10px 10px 0 0 !important;
    transition: all .2s ease;
    font-family: 'Inter', sans-serif !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: {TEXT2} !important;
    background: {CARD}55 !important;
}}

.stTabs [aria-selected="true"] {{
    color: {PURPLE} !important;
    background: {CARD} !important;
    border-bottom: 2px solid {PURPLE} !important;
    font-weight: 600;
}}

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

.js-plotly-plot, .plotly {{
    background: transparent !important;
}}

::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}

::-webkit-scrollbar-track {{
    background: {BG};
}}

::-webkit-scrollbar-thumb {{
    background: {BORDER_L};
    border-radius: 3px;
}}

div[data-testid="column"] > div {{
    padding: 0 .3rem;
}}

.wealthview-header {{
    display:flex;
    align-items:baseline;
    gap:.8rem;
    margin: .4rem 0 .35rem 0;
    padding-top: .25rem;
    overflow: visible;
}}

.wealthview-title {{
    font-size:1.95rem;
    font-weight:900;
    letter-spacing:-.03em;
    background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    line-height:1.2;
    display:inline-block;
}}

.wealthview-subtitle {{
    color:{TEXT3};
    font-size:.78rem;
    letter-spacing:.04em;
}}

.scenario-wrap {{
    background: linear-gradient(135deg, {CARD} 0%, {CARD_H} 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 1rem 1.15rem 1.1rem 1.15rem;
    box-shadow: {SHADOW_SM};
    margin-bottom: .9rem;
}}

.scenario-title {{
    color: {TEXT};
    font-size: .95rem;
    font-weight: 700;
    margin-bottom: .2rem;
}}

.scenario-subtitle {{
    color: {TEXT2};
    font-size: .8rem;
    margin-bottom: .65rem;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def gbp(v):
    sign = "-" if v < 0 else ""
    return f"{sign}£{abs(v):,.0f}"


def pct_fmt(v):
    return f"{v:.1f}%"


def parse_money_input(value, default=0):
    if value is None:
        return default
    cleaned = re.sub(r"[^\d]", "", str(value))
    if cleaned == "":
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return default


def money_text_input(label, value, key, help_text=None):
    formatted_default = f"{int(value):,}" if value is not None else "0"
    raw_value = st.text_input(label, value=formatted_default, key=key, help=help_text)
    return parse_money_input(raw_value, value if value is not None else 0)


def kpi_html(label, value, color=PURPLE, icon="", sub="", info=""):
    sub_html = f'<div style="color:{TEXT3};font-size:.7rem;margin-top:.18rem;">{sub}</div>' if sub else ""
    icon_html = f'<span style="font-size:.95rem;margin-right:.25rem;">{icon}</span>' if icon else ""

    info_html = ""
    if info:
        safe_info = html.escape(info)
        info_html = (
            f'<div style="margin-top:.7rem;padding:.55rem .7rem;'
            f'background:rgba(255,255,255,.04);border:1px solid {BORDER_L};'
            f'border-radius:10px;color:{TEXT2};font-size:.74rem;line-height:1.5;">'
            f'<span style="color:{TEXT};font-weight:700;">What is this?</span><br>{safe_info}</div>'
        )

    return (
        f'<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);'
        f'border:1px solid {BORDER};border-radius:14px;padding:1.05rem 1.2rem;'
        f'box-shadow:{SHADOW_SM};position:relative;overflow:hidden;min-height:156px;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        f'background:linear-gradient(90deg,{color}88,transparent);"></div>'
        f'<div style="color:{TEXT2};font-size:.7rem;text-transform:uppercase;'
        f'letter-spacing:.06em;font-weight:500;margin-bottom:.45rem;">{icon_html}{label}</div>'
        f'<div style="font-size:1.45rem;font-weight:800;color:{color};'
        f'letter-spacing:-.02em;line-height:1.15;">{value}</div>'
        f'{sub_html}'
        f'{info_html}'
        f'</div>'
    )


def render_kpi_card(label, value, color=PURPLE, icon="", sub="", info=""):
    st.markdown(
        kpi_html(label, value, color=color, icon=icon, sub=sub, info=info),
        unsafe_allow_html=True,
    )


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


def sidebar_label(label, color=WHITE):
    return f'<div style="color:{color};font-weight:800;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;margin:.8rem 0 .35rem 0;padding-bottom:.25rem;border-bottom:1px solid {BORDER};">{label}</div>'


def row_item(label, value, color=TEXT, bold=False):
    fw = "700" if bold else "500"
    return f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem 0;border-bottom:1px solid {BORDER}08;"><span style="color:{TEXT2};font-size:.84rem;">{label}</span><span style="color:{color};font-weight:{fw};font-size:.9rem;">{value}</span></div>'


def progress_bar_html(pct_val, color_from=PURPLE, color_to=CYAN, height=8):
    w = max(0, min(100, pct_val))
    return f'<div style="background:{BORDER};border-radius:{height}px;height:{height}px;width:100%;margin-top:.3rem;overflow:hidden;"><div style="width:{w}%;height:100%;border-radius:{height}px;background:linear-gradient(90deg,{color_from},{color_to});transition:width .6s ease;"></div></div>'


def spacer(h="1rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)


def make_layout(overrides=None):
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


def years_to_target(df, target):
    reached = df[df["net_worth"] >= target]
    if len(reached) == 0:
        return None
    return int(reached.iloc[0]["year"])


def build_history_df(snaps):
    if not snaps:
        return pd.DataFrame()

    rows = []
    for pk, sd in sorted(snaps.items()):
        try:
            year, month = pk.split("-")
            year = int(year)
            month = int(month)
        except (ValueError, IndexError):
            continue

        re_val = sd.get("real_estate_equity", 0)
        crypto_val = sd.get("crypto", 0)
        net_worth = sd.get("net_worth", sd.get("cash", 0) + sd.get("investments", 0) + crypto_val + sd.get("pension", 0) + re_val)

        rows.append({
            "period_key": pk,
            "date": datetime(year, month, 1),
            "label": f"{MONTHS[month - 1][:3]} {year}",
            "cash": sd.get("cash", 0),
            "investments": sd.get("investments", 0),
            "crypto": crypto_val,
            "pension": sd.get("pension", 0),
            "real_estate_equity": re_val,
            "net_worth": net_worth,
        })

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    if df.empty:
        return df

    df["nw_change"] = df["net_worth"].diff()
    df["nw_change_pct"] = df["net_worth"].pct_change() * 100
    df["year"] = df["date"].dt.year
    return df

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAX ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_uk_tax(gross, scotland=False):
    personal_allowance = 12_570.0
    if gross > 100_000:
        personal_allowance = max(0, personal_allowance - (gross - 100_000) / 2)
    taxable = max(0, gross - personal_allowance)

    if scotland:
        bands = [
            (2_162, 0.19),
            (10_956, 0.20),
            (29_974, 0.21),
            (82_338, 0.42),
            (float("inf"), 0.45),
        ]
    else:
        bands = [
            (37_700, 0.20),
            (87_440, 0.40),
            (float("inf"), 0.45),
        ]

    income_tax = 0.0
    remaining = taxable
    band_breakdown = []

    for width, rate in bands:
        amount = min(remaining, width)
        tax = amount * rate
        income_tax += tax
        if amount > 0:
            band_breakdown.append({"band_width": amount, "rate": rate, "tax": tax})
        remaining -= amount
        if remaining <= 0:
            break

    ni = 0.0
    if gross > 12_570:
        ni += max(0, min(gross, 50_270) - 12_570) * 0.08
    if gross > 50_270:
        ni += (gross - 50_270) * 0.02

    total_deductions = income_tax + ni
    net_annual = gross - total_deductions
    effective_rate = (total_deductions / gross * 100) if gross > 0 else 0

    return {
        "gross": gross,
        "personal_allowance": personal_allowance,
        "taxable_income": taxable,
        "income_tax": income_tax,
        "ni": ni,
        "total_deductions": total_deductions,
        "net_annual": net_annual,
        "net_monthly": net_annual / 12,
        "effective_rate": effective_rate,
        "band_breakdown": band_breakdown,
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def forecast_wealth(
    starting_cash,
    starting_invested,
    starting_pension,
    starting_real_estate_equity,
    monthly_invest,
    monthly_pension,
    expected_return,
    inflation,
    real_estate_growth,
    years,
    employer_pension_annual=0,
):
    rows = []
    cash_value = starting_cash
    invested_value = starting_invested
    pension_value = starting_pension
    real_estate_value = starting_real_estate_equity

    for year in range(0, years + 1):
        net_worth = cash_value + invested_value + pension_value + real_estate_value
        real_factor = 1 / ((1 + inflation / 100) ** year) if year > 0 else 1

        rows.append({
            "year": year,
            "cash": cash_value,
            "invested": invested_value,
            "pension": pension_value,
            "real_estate_equity": real_estate_value,
            "net_worth": net_worth,
            "net_worth_real": net_worth * real_factor,
        })

        if year < years:
            invested_value *= (1 + expected_return / 100)
            pension_value *= (1 + expected_return / 100)
            real_estate_value *= (1 + real_estate_growth / 100)

            invested_value += monthly_invest * 12
            pension_value += monthly_pension * 12 + employer_pension_annual

    return pd.DataFrame(rows)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center;padding:1rem 0 .6rem 0;">
            <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,{PURPLE},{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-.03em;">◈ WealthView</div>
            <div style="color:{TEXT3};font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;margin-top:.2rem;">Personal Finance Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    now = datetime.now()

    st.markdown("---")
    st.markdown(sidebar_label("Monthly Snapshot Inputs"), unsafe_allow_html=True)
    st.caption("Update these figures each month and save them to build your wealth history over time.")

    col_m, col_y = st.columns(2)
    with col_m:
        selected_month = st.selectbox("Reporting Month", MONTHS, index=now.month - 1)
    with col_y:
        selected_year = st.selectbox("Reporting Year", list(range(2020, now.year + 2)), index=min(now.year - 2020, now.year + 1 - 2020))

    period_key = f"{selected_year}-{MONTHS.index(selected_month)+1:02d}"
    period_label = f"{selected_month} {selected_year}"
    existing_snapshot = st.session_state.snapshots.get(period_key, {})

    if existing_snapshot:
        st.markdown(
            f'<div style="background:{AMBER}12;border:1px solid {AMBER}33;border-radius:10px;padding:.55rem .75rem;margin-bottom:.6rem;"><span style="color:{AMBER};font-size:.78rem;font-weight:700;">Editing existing snapshot for {period_label}</span></div>',
            unsafe_allow_html=True,
        )

    cash = money_text_input("Cash Savings (£)", existing_snapshot.get("cash", 25_000), f"cash_snapshot_{period_key}")
    investments = money_text_input("Stock and Shares (£)", existing_snapshot.get("investments", 85_000), f"investments_snapshot_{period_key}")
    crypto = money_text_input("Crypto (£)", existing_snapshot.get("crypto", 0), f"crypto_snapshot_{period_key}")
    pension_val = money_text_input("Pension (£)", existing_snapshot.get("pension", 42_000), f"pension_snapshot_{period_key}")
    real_estate_equity = money_text_input("Real Estate Equity Value (£)", existing_snapshot.get("real_estate_equity", 130_000), f"real_estate_equity_snapshot_{period_key}")

    if st.button("Save Monthly Input", use_container_width=True):
        snapshot_data = {
            "cash": cash,
            "investments": investments,
            "crypto": crypto,
            "pension": pension_val,
            "real_estate_equity": real_estate_equity,
            "net_worth": cash + investments + crypto + pension_val + real_estate_equity,
            "saved_at": datetime.now().isoformat(),
        }
        if period_key in st.session_state.snapshots:
            merged = st.session_state.snapshots[period_key].copy()
            merged.update(snapshot_data)
            snapshot_data = merged

        st.session_state.snapshots[period_key] = snapshot_data
        save_snapshots(st.session_state.snapshots)
        st.session_state.snapshot_saved_flag = True
        st.rerun()

    if st.session_state.snapshot_saved_flag:
        st.markdown(
            f'<div style="background:{GREEN}18;border:1px solid {GREEN}44;border-radius:8px;padding:.5rem .7rem;text-align:center;margin-top:.45rem;"><span style="color:{GREEN};font-size:.8rem;font-weight:700;">Monthly input saved for {period_label}</span></div>',
            unsafe_allow_html=True,
        )
        st.session_state.snapshot_saved_flag = False

    snapshot_count = len(st.session_state.snapshots)
    if snapshot_count > 0:
        st.markdown(
            f'<div style="color:{TEXT3};font-size:.72rem;text-align:center;margin-top:.4rem;">{snapshot_count} snapshot{"s" if snapshot_count != 1 else ""} saved</div>',
            unsafe_allow_html=True,
        )

    warnings = []
    if cash == 0 and investments == 0 and crypto == 0 and pension_val == 0 and real_estate_equity == 0:
        warnings.append("All monthly asset values are currently zero.")
    for label, value in [
        (LBL_CASH, cash),
        (LBL_STOCK, investments),
        (LBL_CRYPTO, crypto),
        (LBL_PENSION, pension_val),
        (LBL_RE, real_estate_equity),
    ]:
        if value > 50_000_000:
            warnings.append(f"{label} looks unusually high.")

    if warnings:
        for warning in warnings:
            st.markdown(
                f'<div style="background:{RED}12;border:1px solid {RED}33;border-radius:10px;padding:.5rem .7rem;margin-top:.45rem;"><span style="color:{RED};font-size:.78rem;font-weight:600;">{warning}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(sidebar_label("Current Employment Package and Forecasting Assumptions"), unsafe_allow_html=True)
    st.caption("These settings are separate from monthly inputs. Update them and apply when ready.")

    with st.form("forecast_assumptions_form", clear_on_submit=False):
        draft_gross_salary = money_text_input("Gross Salary (£/yr)", st.session_state.gross_salary, "gross_salary_input")
        draft_annual_bonus = money_text_input("Annual Bonus (£)", st.session_state.annual_bonus, "annual_bonus_input")
        draft_scotland_tax = st.toggle("Scottish Tax Bands", value=st.session_state.scotland_tax)
        draft_pension_contrib_pct = st.slider("Pension Contribution %", 0.0, 30.0, float(st.session_state.pension_contrib_pct), 0.5)

        draft_monthly_invest = money_text_input("Monthly Investment (£)", st.session_state.monthly_invest, "monthly_invest_input")
        draft_current_age = st.number_input("Current Age", 18, 80, int(st.session_state.current_age))
        draft_retirement_age = st.number_input("Retirement Age", 30, 90, int(st.session_state.retirement_age))
        draft_target_wealth = money_text_input("Target Wealth (£)", st.session_state.target_wealth, "target_wealth_input")
        draft_expected_return = st.slider("Expected Return %", 0.0, 15.0, float(st.session_state.expected_return), 0.5)
        draft_inflation = st.slider("Inflation %", 0.0, 10.0, float(st.session_state.inflation), 0.1)
        draft_property_growth = st.slider("Yearly Real Estate Growth %", 0.0, 10.0, float(st.session_state.property_growth), 0.5)

        forecast_submit = st.form_submit_button("Update Forecast Assumptions", use_container_width=True)

    if forecast_submit:
        st.session_state.gross_salary = draft_gross_salary
        st.session_state.annual_bonus = draft_annual_bonus
        st.session_state.scotland_tax = draft_scotland_tax
        st.session_state.pension_contrib_pct = draft_pension_contrib_pct
        st.session_state.monthly_invest = draft_monthly_invest
        st.session_state.current_age = draft_current_age
        st.session_state.retirement_age = draft_retirement_age
        st.session_state.target_wealth = draft_target_wealth
        st.session_state.expected_return = draft_expected_return
        st.session_state.inflation = draft_inflation
        st.session_state.property_growth = draft_property_growth
        st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD HISTORY & CURRENT CALCULATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
history_df = build_history_df(st.session_state.snapshots)

gross_salary = st.session_state.gross_salary
annual_bonus = st.session_state.annual_bonus
scotland_tax = st.session_state.scotland_tax
pension_contrib_pct = st.session_state.pension_contrib_pct
monthly_invest = st.session_state.monthly_invest
monthly_expenses = st.session_state.monthly_expenses
current_age = st.session_state.current_age
retirement_age = st.session_state.retirement_age
target_wealth = st.session_state.target_wealth
expected_return = st.session_state.expected_return
inflation = st.session_state.inflation
property_growth = st.session_state.property_growth
selected_scenario = st.session_state.selected_scenario

total_gross = gross_salary + annual_bonus
employee_pension_annual = gross_salary * pension_contrib_pct / 100
employer_pension_annual = gross_salary * 0.03
taxable_gross = total_gross - employee_pension_annual
tax = calc_uk_tax(taxable_gross, scotland=scotland_tax)

net_monthly = tax["net_monthly"]
monthly_pension_contrib = employee_pension_annual / 12
surplus = net_monthly - monthly_expenses - monthly_invest
savings_rate = (monthly_invest / net_monthly * 100) if net_monthly > 0 else 0
net_worth = cash + investments + crypto + pension_val + real_estate_equity
years_to_retire = max(1, retirement_age - current_age)

df_con = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest=monthly_invest,
    monthly_pension=monthly_pension_contrib,
    expected_return=max(0, expected_return - 2),
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
)

df_base = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest=monthly_invest,
    monthly_pension=monthly_pension_contrib,
    expected_return=expected_return,
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
)

df_agg = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest=monthly_invest,
    monthly_pension=monthly_pension_contrib,
    expected_return=expected_return + 2,
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
)

scenario_map = {
    "Conservative": (df_con, max(0, expected_return - 2)),
    "Base": (df_base, expected_return),
    "Aggressive": (df_agg, expected_return + 2),
}

selected_df, selected_return = scenario_map[selected_scenario]
target_years = years_to_target(selected_df, target_wealth)
forecast_10_year = selected_df.loc[selected_df["year"] == min(10, years_to_retire), "net_worth"]
forecast_10_year_value = forecast_10_year.values[0] if len(forecast_10_year) > 0 else net_worth

goal_progress = min(100, net_worth / target_wealth * 100) if target_wealth > 0 else 0
goal_gap = max(0, target_wealth - net_worth)

if years_to_retire > 0 and selected_return > 0:
    r_monthly = selected_return / 100 / 12
    periods = years_to_retire * 12
    future_value_existing = net_worth * ((1 + r_monthly) ** periods)
    shortfall = max(0, target_wealth - future_value_existing)
    required_monthly = shortfall * r_monthly / (((1 + r_monthly) ** periods) - 1) if shortfall > 0 else 0
else:
    required_monthly = 0

asset_values = {
    LBL_CASH: cash,
    LBL_STOCK: investments,
    LBL_CRYPTO: crypto,
    LBL_PENSION: pension_val,
    LBL_RE: real_estate_equity,
}
largest_asset_label = max(asset_values, key=asset_values.get) if asset_values else ""
largest_asset_pct = (asset_values[largest_asset_label] / net_worth * 100) if net_worth > 0 else 0

if not history_df.empty and len(history_df) >= 2:
    latest_change = history_df.iloc[-1]["nw_change"]
    if latest_change > 0:
        momentum_label = "Growing"
        momentum_color = GREEN
    elif latest_change < 0:
        momentum_label = "Declining"
        momentum_color = RED
    else:
        momentum_label = "Stable"
        momentum_color = TEXT2
else:
    momentum_label = "Building history"
    momentum_color = TEXT2

latest_saved_period = history_df.iloc[-1]["label"] if not history_df.empty else "No saved history yet"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f"""
    <div class="wealthview-header">
        <span class="wealthview-title">◈ WealthView</span>
        <span class="wealthview-subtitle">Personal Wealth Management & Forecast</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GETTING STARTED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.expander("Getting Started — How to Use This Dashboard", expanded=False):
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:14px;padding:1.2rem 1.4rem;">
<div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.8rem;">Quick Start Guide</div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{PURPLE}22;border:1px solid {PURPLE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{PURPLE};">1</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Select a Reporting Period</div>
<div style="color:{TEXT2};font-size:.8rem;">Choose the month and year in the sidebar that your figures relate to.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{BLUE}22;border:1px solid {BLUE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{BLUE};">2</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Enter Monthly Asset Inputs</div>
<div style="color:{TEXT2};font-size:.8rem;">Add Cash Savings, Stock and Shares, Crypto, Pension, and Real Estate Equity Value.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{CYAN}22;border:1px solid {CYAN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{CYAN};">3</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Click Save Monthly Input</div>
<div style="color:{TEXT2};font-size:.8rem;">This creates or updates the snapshot for that month and year.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{GREEN}22;border:1px solid {GREEN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{GREEN};">4</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Update Planning Inputs Separately</div>
<div style="color:{TEXT2};font-size:.8rem;">Edit salary, contribution, age, and forecast assumptions, then click <b>Update Forecast Assumptions</b>.</div></div></div>

<div style="display:flex;gap:1rem;align-items:flex-start;padding:.7rem 0;">
<div style="min-width:32px;height:32px;border-radius:8px;background:{AMBER}22;border:1px solid {AMBER}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{AMBER};">5</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Use the Product Views</div>
<div style="color:{TEXT2};font-size:.8rem;">Overview and History show wealth progress. Forecast and Goals support planning. Cash Flow and Salary Calculator help with day-to-day management.</div></div></div>
</div>
""",
        unsafe_allow_html=True,
    )

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
    badge_a, badge_b, badge_c, badge_d = st.columns(4)
    badge_a.markdown(kpi_small("Current Reporting Period", period_label, PURPLE), unsafe_allow_html=True)
    badge_b.markdown(kpi_small("Latest Saved Period", latest_saved_period, TEXT), unsafe_allow_html=True)
    badge_c.markdown(kpi_small("Momentum", momentum_label, momentum_color), unsafe_allow_html=True)
    badge_d.markdown(kpi_small("Saved Snapshots", str(len(st.session_state.snapshots)), CYAN), unsafe_allow_html=True)

    st.markdown(section_header("Financial Net Worth Snapshot", "◈"), unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card(
            "Net Worth",
            gbp(net_worth),
            color=PURPLE,
            icon="◈",
            info="Your total tracked wealth. Calculated as Cash Savings + Stock and Shares + Crypto + Pension + Real Estate Equity.",
        )
    with c2:
        render_kpi_card(
            LBL_CASH,
            gbp(cash),
            color=CYAN,
            icon="◇",
            info="Cash held in savings or cash-based accounts.",
        )
    with c3:
        render_kpi_card(
            LBL_STOCK,
            gbp(investments),
            color=BLUE,
            icon="△",
            info="The current value of your stock and shares investments.",
        )
    with c4:
        render_kpi_card(
            LBL_CRYPTO,
            gbp(crypto),
            color=AMBER,
            icon="◌",
            info="The current value of your crypto holdings.",
        )
    with c5:
        render_kpi_card(
            LBL_PENSION,
            gbp(pension_val),
            color=GREEN,
            icon="◎",
            info="The current value of your pension pot.",
        )

    spacer(".55rem")
    c6, c7, c8, c9 = st.columns(4)
    with c6:
        render_kpi_card(
            LBL_RE,
            gbp(real_estate_equity),
            color=PURPLE,
            icon="⬡",
            info="Your tracked real estate equity value for this reporting period.",
        )
    with c7:
        render_kpi_card(
            "Monthly Surplus",
            gbp(surplus),
            color=CYAN if surplus >= 0 else RED,
            icon="↗" if surplus >= 0 else "↘",
            info="Estimated monthly income left after expenses and monthly investment contributions.",
        )
    with c8:
        render_kpi_card(
            "Savings Rate",
            pct_fmt(savings_rate),
            color=PURPLE,
            icon="◉",
            info="Calculated as your chosen monthly investment contribution divided by your net monthly income.",
        )
    with c9:
        render_kpi_card(
            "10-Year Forecast",
            gbp(forecast_10_year_value),
            color=BLUE,
            icon="⟩",
            info=f"Projected net worth in 10 years under the selected {selected_scenario.lower()} scenario.",
        )

    if largest_asset_pct >= 50:
        st.markdown(
            f'<div style="background:{AMBER}12;border:1px solid {AMBER}33;border-radius:12px;padding:.7rem .9rem;margin-top:.6rem;"><span style="color:{AMBER};font-size:.84rem;font-weight:700;">Allocation Warning:</span> <span style="color:{TEXT2};font-size:.84rem;">{largest_asset_label} makes up {largest_asset_pct:.0f}% of your current net worth.</span></div>',
            unsafe_allow_html=True,
        )

    spacer("1rem")
    st.markdown(section_header("Wealth Composition"), unsafe_allow_html=True)
    left, right = st.columns([1, 1.1])

    with left:
        st.markdown(card_open("Net Worth Allocation"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=[LBL_CASH, LBL_STOCK, LBL_CRYPTO, LBL_PENSION, LBL_RE],
            values=[cash, investments, crypto, pension_val, real_estate_equity],
            hole=0.62,
            marker=dict(colors=[CYAN, BLUE, AMBER, GREEN, PURPLE], line=dict(color=BG, width=2)),
            textinfo="label+percent",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
            direction="clockwise",
            sort=False,
        ))
        fig.update_layout(**make_layout({"height": 360, "showlegend": False}))
        fig.add_annotation(text=f"<b>{gbp(net_worth)}</b>", x=0.5, y=0.54, font=dict(size=19, color=TEXT, family="Inter"), showarrow=False)
        fig.add_annotation(text="NET WORTH", x=0.5, y=0.43, font=dict(size=8.5, color=TEXT3, family="Inter"), showarrow=False)
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Asset Breakdown"), unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=[cash, investments, crypto, pension_val, real_estate_equity],
            y=[LBL_CASH, LBL_STOCK, LBL_CRYPTO, LBL_PENSION, LBL_RE],
            orientation="h",
            marker=dict(color=[CYAN, BLUE, AMBER, GREEN, PURPLE]),
            text=[gbp(v) for v in [cash, investments, crypto, pension_val, real_estate_equity]],
            textposition="inside",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{y}</b>: £%{x:,.0f}<extra></extra>",
        ))
        fig.update_layout(**make_layout({
            "height": 360,
            "yaxis": {**CLEAN_AXIS, "autorange": "reversed", "tickfont": dict(color=TEXT2, size=11)},
            "xaxis": {**CLEAN_AXIS, "zeroline": True, "zerolinecolor": BORDER_L, "zerolinewidth": 1},
        }))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_history:
    st.markdown(section_header("Snapshot History", "◷"), unsafe_allow_html=True)

    if history_df.empty:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:2.5rem 2rem;box-shadow:{SHADOW};text-align:center;">
            <div style="font-size:2rem;margin-bottom:.6rem;">◈</div>
            <div style="color:{TEXT};font-size:1.05rem;font-weight:600;margin-bottom:.4rem;">No snapshots yet</div>
            <div style="color:{TEXT3};font-size:.82rem;line-height:1.6;max-width:420px;margin:0 auto;">Save your first monthly input to begin tracking how your net worth changes over time.</div></div>""",
            unsafe_allow_html=True,
        )
    else:
        if len(history_df) >= 2:
            latest = history_df.iloc[-1]
            previous = history_df.iloc[-2]
            change = latest["net_worth"] - previous["net_worth"]
            change_pct = (change / previous["net_worth"] * 100) if previous["net_worth"] != 0 else 0
            change_color = GREEN if change >= 0 else RED
            change_icon = "↗" if change >= 0 else "↘"

            h1, h2, h3 = st.columns(3)
            h1.markdown(kpi_html("Latest Net Worth", gbp(latest["net_worth"]), PURPLE, "◈", latest["label"]), unsafe_allow_html=True)
            h2.markdown(kpi_html("Month-on-Month Change", gbp(change), change_color, change_icon), unsafe_allow_html=True)
            h3.markdown(kpi_html("Growth Rate", pct_fmt(change_pct), change_color, change_icon), unsafe_allow_html=True)

        spacer(".6rem")
        st.markdown(card_open("Net Worth History", "Stacked assets with total net worth line"), unsafe_allow_html=True)
        view_mode = st.radio("View", ["Monthly", "Yearly"], horizontal=True, label_visibility="collapsed")

        if view_mode == "Yearly":
            display_df = history_df.sort_values("date").groupby("year").tail(1).copy()
            display_df["x_label"] = display_df["year"].astype(str)
        else:
            display_df = history_df.copy()
            display_df["x_label"] = display_df["label"]

        fig = go.Figure()
        totals = display_df["net_worth"].replace(0, 1)

        traces = [
            ("cash", LBL_CASH, CYAN),
            ("investments", LBL_STOCK, BLUE),
            ("crypto", LBL_CRYPTO, AMBER),
            ("pension", LBL_PENSION, GREEN),
            ("real_estate_equity", LBL_RE, PURPLE),
        ]

        for col_name, label, color in traces:
            values = display_df[col_name]
            percentages = (values / totals * 100).fillna(0)
            texts = [
                f"{gbp(v)}<br>{p:.0f}%" if v > 0 and p >= 8 else ""
                for v, p in zip(values, percentages)
            ]
            fig.add_trace(go.Bar(
                x=display_df["x_label"],
                y=values,
                name=label,
                marker=dict(color=color),
                text=texts,
                textposition="inside",
                textfont=dict(color=TEXT, size=10, family="Inter"),
                insidetextanchor="middle",
                hovertemplate=f"<b>{label}</b><br>%{{x}}: £%{{y:,.0f}}<extra></extra>",
            ))

        fig.add_trace(go.Scatter(
            x=display_df["x_label"],
            y=display_df["net_worth"],
            name="Total Net Worth",
            mode="lines+markers+text",
            line=dict(color=WHITE, width=3),
            marker=dict(size=10, color=WHITE, line=dict(color=BG, width=3)),
            text=[gbp(v) for v in display_df["net_worth"]],
            textposition="top center",
            textfont=dict(color=WHITE, size=11, family="Inter"),
            hovertemplate="<b>Total Net Worth</b><br>%{x}: £%{y:,.0f}<extra></extra>",
        ))

        fig.update_layout(**make_layout({
            "height": 470,
            "barmode": "stack",
            "legend": dict(
                orientation="h",
                y=-0.2,
                x=0.5,
                xanchor="center",
                font=dict(size=11, color=TEXT2),
                bgcolor="rgba(0,0,0,0)",
            ),
            "xaxis": GRID_AXIS,
            "yaxis": GRID_AXIS,
        }))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

        spacer(".5rem")
        st.markdown(card_open("Month-to-Month Growth"), unsafe_allow_html=True)
        table_html = f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:.82rem;"><thead><tr style="border-bottom:2px solid {BORDER};"><th style="text-align:left;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Period</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Net Worth</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Change</th><th style="text-align:right;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Growth</th></tr></thead><tbody>'
        for _, row in history_df.iterrows():
            chg = row["nw_change"]
            if pd.isna(chg):
                change_str = "—"
                pct_str = "—"
                change_color = TEXT3
            else:
                change_color = GREEN if chg >= 0 else RED
                change_str = gbp(chg)
                pct_str = pct_fmt(row["nw_change_pct"])
            table_html += f'<tr style="border-bottom:1px solid {BORDER};"><td style="padding:.45rem .6rem;color:{TEXT};font-weight:600;">{row["label"]}</td><td style="padding:.45rem .6rem;color:{TEXT};text-align:right;font-weight:700;">{gbp(row["net_worth"])}</td><td style="padding:.45rem .6rem;color:{change_color};text-align:right;font-weight:700;">{change_str}</td><td style="padding:.45rem .6rem;color:{change_color};text-align:right;font-weight:700;">{pct_str}</td></tr>'
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_portfolio:
    st.markdown(section_header("Portfolio Overview", "△"), unsafe_allow_html=True)
    total_portfolio = investments + crypto + pension_val
    annual_growth_est = total_portfolio * expected_return / 100

    p1, p2, p3, p4 = st.columns(4)
    p1.markdown(kpi_small("Total Portfolio", gbp(total_portfolio), PURPLE), unsafe_allow_html=True)
    p2.markdown(kpi_small(LBL_STOCK, gbp(investments), BLUE), unsafe_allow_html=True)
    p3.markdown(kpi_small(LBL_CRYPTO, gbp(crypto), AMBER), unsafe_allow_html=True)
    p4.markdown(kpi_small(LBL_PENSION, gbp(pension_val), GREEN), unsafe_allow_html=True)

    spacer("1rem")
    left, right = st.columns(2)

    with left:
        st.markdown(card_open("Portfolio Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=[LBL_STOCK, LBL_CRYPTO, LBL_PENSION],
            values=[investments, crypto, pension_val],
            hole=0.6,
            marker=dict(colors=[BLUE, AMBER, GREEN], line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}<br>%{percent}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
        ))
        fig.update_layout(**make_layout({"height": 330, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Portfolio Insights"), unsafe_allow_html=True)
        risk_ratio = ((investments + crypto) / total_portfolio * 100) if total_portfolio > 0 else 0
        if risk_ratio < 35:
            risk_label = "Conservative"
            risk_color = CYAN
        elif risk_ratio < 70:
            risk_label = "Balanced"
            risk_color = GREEN
        else:
            risk_label = "Growth"
            risk_color = PURPLE

        st.markdown(row_item("Estimated Annual Growth", gbp(annual_growth_est), CYAN, True), unsafe_allow_html=True)
        st.markdown(row_item("Risk Profile", risk_label, risk_color, True), unsafe_allow_html=True)
        st.markdown(row_item("Equity Allocation", pct_fmt(risk_ratio), BLUE), unsafe_allow_html=True)
        st.markdown(row_item("Largest Concentration", f"{largest_asset_label} ({largest_asset_pct:.0f}%)", TEXT), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORECAST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_forecast:
    st.markdown(section_header("Wealth Projection", "⟩"), unsafe_allow_html=True)

    st.markdown(
        """
        <div class="scenario-wrap">
            <div class="scenario-title">Forecast Scenario</div>
            <div class="scenario-subtitle">Choose the scenario that should drive the forecast summary cards and target timing.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_choice = st.selectbox(
        "Forecast Scenario",
        ["Conservative", "Base", "Aggressive"],
        index=["Conservative", "Base", "Aggressive"].index(st.session_state.selected_scenario),
        label_visibility="collapsed",
    )

    if scenario_choice != st.session_state.selected_scenario:
        st.session_state.selected_scenario = scenario_choice
        st.rerun()

    selected_df, selected_return = scenario_map[scenario_choice]
    target_years = years_to_target(selected_df, target_wealth)

    st.markdown(
        f'<div style="background:{AMBER}12;border:1px solid {AMBER}33;border-radius:12px;padding:.7rem .9rem;margin-bottom:.8rem;"><span style="color:{AMBER};font-size:.84rem;font-weight:700;">Nominal forecast:</span> <span style="color:{TEXT2};font-size:.84rem;">This chart shows projected growth in money terms and does not reflect inflation-adjusted affordability.</span></div>',
        unsafe_allow_html=True,
    )

    milestone_years = sorted(set([y for y in [1, 5, 10, years_to_retire] if y <= years_to_retire]))
    milestone_cols = st.columns(len(milestone_years))
    description = f"Based on {gbp(monthly_invest)}/mo contributions and {selected_return:.1f}% yearly growth"
    for idx, year in enumerate(milestone_years):
        match = selected_df.loc[selected_df["year"] == year, "net_worth"]
        value = match.values[0] if len(match) > 0 else net_worth
        label = f"Year {year}" if year != years_to_retire else f"Retirement ({year}yr)"
        color = BLUE if scenario_choice == "Base" else (CYAN if scenario_choice == "Conservative" else PURPLE)
        milestone_cols[idx].markdown(kpi_html(label, gbp(value), color, sub=description), unsafe_allow_html=True)

    spacer(".8rem")
    st.markdown(card_open("Scenario Analysis", f"Currently showing: {scenario_choice}"), unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_con["year"], y=df_con["net_worth"],
        name=f"Conservative ({max(0, expected_return - 2):.1f}%)",
        line=dict(color=CYAN, width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=4, color=CYAN),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Conservative</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_base["year"], y=df_base["net_worth"],
        name=f"Base ({expected_return:.1f}%)",
        line=dict(color=BLUE, width=3.5),
        mode="lines+markers",
        marker=dict(size=5, color=BLUE),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Base</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_agg["year"], y=df_agg["net_worth"],
        name=f"Aggressive ({expected_return + 2:.1f}%)",
        line=dict(color=PURPLE, width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=4, color=PURPLE),
        hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Aggressive</extra>",
    ))
    fig.add_hline(
        y=target_wealth,
        line_dash="dash",
        line_color=GREEN,
        line_width=1.5,
        annotation_text=f"  Target: {gbp(target_wealth)}",
        annotation_font=dict(color=GREEN, size=11),
        annotation_position="top left",
    )
    fig.update_layout(**make_layout({
        "height": 440,
        "legend": dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
        "xaxis": {**GRID_AXIS, "title": {"text": "Years", "font": dict(color=TEXT3, size=11)}},
        "yaxis": {**GRID_AXIS, "title": {"text": "Net Worth (£)", "font": dict(color=TEXT3, size=11)}},
    }))
    st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
    st.markdown(card_close(), unsafe_allow_html=True)

    spacer(".5rem")
    left, right = st.columns(2)

    with left:
        st.markdown(card_open("Nominal vs Real (Inflation-Adjusted)"), unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["net_worth"],
            name="Nominal",
            line=dict(color=BLUE, width=2.5),
            mode="lines",
            hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Nominal</extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["net_worth_real"],
            name="Real",
            line=dict(color=CYAN, width=2.5),
            mode="lines",
            hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Real</extra>",
        ))
        fig2.update_layout(**make_layout({
            "height": 320,
            "legend": dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
            "xaxis": GRID_AXIS,
            "yaxis": GRID_AXIS,
        }))
        st.plotly_chart(fig2, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Target Timing & Guidance"), unsafe_allow_html=True)
        if target_years is not None:
            st.markdown(row_item("Selected Scenario", scenario_choice, BLUE, True), unsafe_allow_html=True)
            st.markdown(row_item("Years to Target", str(target_years), GREEN, True), unsafe_allow_html=True)
            st.markdown(row_item("Projected Age", str(current_age + target_years), TEXT, True), unsafe_allow_html=True)
        else:
            st.markdown(row_item("Selected Scenario", scenario_choice, BLUE, True), unsafe_allow_html=True)
            st.markdown(row_item("Years to Target", "Not reached", RED, True), unsafe_allow_html=True)

        guidance_gap = max(0, required_monthly - monthly_invest)
        guidance_text = f"Increase monthly investing by about {gbp(guidance_gap)}/mo to improve your path to target." if guidance_gap > 0 else "Your current monthly investment level is already aligned with this scenario."
        st.markdown(f'<div style="margin-top:.8rem;padding:.7rem .9rem;background:{PURPLE}10;border:1px solid {PURPLE}22;border-radius:10px;color:{TEXT2};font-size:.82rem;line-height:1.55;">{guidance_text}</div>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_goals:
    st.markdown(section_header("Goal Tracking", "◎"), unsafe_allow_html=True)
    left, right = st.columns(2)

    with left:
        st.markdown(card_open("Wealth Target Progress"), unsafe_allow_html=True)
        st.markdown(
            f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.3rem;">
            <span style="color:{TEXT2};font-size:.82rem;">Progress toward target</span>
            <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{PURPLE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{pct_fmt(goal_progress)}</span></div>
            {progress_bar_html(goal_progress, PURPLE, CYAN, 10)}
            <div style="display:flex;justify-content:space-between;margin-top:1rem;">
            <div><div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Current</div><div style="color:{TEXT};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(net_worth)}</div></div>
            <div style="text-align:right;"><div style="color:{TEXT3};font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Target</div><div style="color:{GREEN};font-weight:700;font-size:1.05rem;margin-top:.15rem;">{gbp(target_wealth)}</div></div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Gap Analysis"), unsafe_allow_html=True)
        total_saving_now = monthly_invest + monthly_pension_contrib
        for label, value, color, bold in [
            ("Remaining Gap", gbp(goal_gap), RED, True),
            ("Years to Retirement", str(years_to_retire), TEXT, False),
            ("Required Monthly Investing", f"{gbp(required_monthly)}/mo", AMBER, True),
            ("Current Monthly Investing", f"{gbp(total_saving_now)}/mo", GREEN, False),
        ]:
            st.markdown(row_item(label, value, color, bold), unsafe_allow_html=True)

        on_track = total_saving_now >= required_monthly
        status_color = GREEN if on_track else AMBER
        status_text = "On Track" if on_track else "Below Target"
        status_icon = "✓" if on_track else "!"

        st.markdown(
            f'<div style="margin-top:.8rem;padding:.6rem .8rem;background:{status_color}15;border:1px solid {status_color}33;border-radius:10px;display:flex;align-items:center;gap:.5rem;"><span style="background:{status_color};color:{BG};font-weight:800;font-size:.75rem;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;">{status_icon}</span><span style="color:{status_color};font-weight:600;font-size:.85rem;">{status_text}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSUMPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_assumptions:
    region = "Scotland" if scotland_tax else "England / Wales / NI"
    st.markdown(section_header("Model Assumptions", "⚙"), unsafe_allow_html=True)
    st.markdown(card_open("Parameters"), unsafe_allow_html=True)

    for label, value, desc, color in [
        ("Expected Investment Return", pct_fmt(expected_return), "Annual nominal return used for stock, crypto, and pension growth", BLUE),
        ("Inflation Rate", pct_fmt(inflation), "Used to calculate real purchasing-power values", CYAN),
        ("Yearly Real Estate Growth %", pct_fmt(property_growth), "Annual growth assumption for real estate equity", PURPLE),
        ("Employer Pension Match", "3.0%", "Assumed employer pension contribution rate", GREEN),
        ("Tax Region", region, "Selected tax jurisdiction", AMBER),
        ("Scenario Spread", "±2.0%", "Conservative and aggressive scenarios are built around the base return", TEXT),
    ]:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid {BORDER};"><div><div style="color:{TEXT};font-size:.88rem;font-weight:500;">{label}</div><div style="color:{TEXT3};font-size:.72rem;margin-top:.1rem;">{desc}</div></div><span style="color:{color};font-weight:700;font-size:.95rem;white-space:nowrap;margin-left:1rem;">{value}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(card_close(), unsafe_allow_html=True)
    spacer(".5rem")
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{SHADOW_SM};"><div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.5rem;">Disclaimer</div><div style="color:{TEXT3};font-size:.78rem;line-height:1.65;">This dashboard is for illustrative and educational purposes only. It does not constitute financial advice. Forecasts use simplified compound-growth models. Unallocated surplus cash is not included in projections unless explicitly represented in your saved asset values.</div></div>',
        unsafe_allow_html=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CASH FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_cashflow:
    st.markdown(section_header("Monthly Cash Flow", "↔"), unsafe_allow_html=True)

    cashflow_expenses = money_text_input("Monthly Expenses (£)", st.session_state.monthly_expenses, "monthly_expenses_cashflow")
    if cashflow_expenses != st.session_state.monthly_expenses:
        st.session_state.monthly_expenses = cashflow_expenses
        monthly_expenses = cashflow_expenses
        surplus = net_monthly - monthly_expenses - monthly_invest
        savings_rate = (monthly_invest / net_monthly * 100) if net_monthly > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_small("Net Income", gbp(net_monthly), GREEN), unsafe_allow_html=True)
    c2.markdown(kpi_small("Total Outflows", gbp(monthly_expenses + monthly_invest + monthly_pension_contrib), AMBER), unsafe_allow_html=True)
    c3.markdown(kpi_small("Investment Rate", pct_fmt(savings_rate), PURPLE), unsafe_allow_html=True)

    spacer(".8rem")
    left, right = st.columns(2)

    with left:
        st.markdown(card_open("Cash Flow Statement"), unsafe_allow_html=True)
        for label, value, color, bold in [
            ("Gross Monthly Income", total_gross / 12, TEXT, False),
            ("Tax & NI", -tax["total_deductions"] / 12, RED, False),
            ("Pension (employee)", -monthly_pension_contrib, AMBER, False),
            ("Net Monthly Income", net_monthly, GREEN, True),
        ]:
            st.markdown(row_item(label, gbp(value), color, bold), unsafe_allow_html=True)

        st.markdown(f'<div style="height:.25rem;border-bottom:1px dashed {BORDER};margin:.15rem 0;"></div>', unsafe_allow_html=True)

        for label, value, color, bold in [
            ("Expenses", -monthly_expenses, RED, False),
            ("Monthly Investment", -monthly_invest, BLUE, False),
            ("Monthly Surplus", surplus, CYAN if surplus >= 0 else RED, True),
        ]:
            st.markdown(row_item(label, gbp(value), color, bold), unsafe_allow_html=True)

        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Monthly Outflow Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Expenses", "Monthly Investment", "Pension", "Surplus"],
            values=[monthly_expenses, monthly_invest, monthly_pension_contrib, max(0, surplus)],
            hole=0.58,
            marker=dict(colors=[RED, BLUE, GREEN, CYAN], line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}/mo<extra></extra>",
        ))
        fig.update_layout(**make_layout({"height": 350, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SALARY CALCULATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_salary:
    st.markdown(
        f"""<div style="display:flex;align-items:baseline;gap:.6rem;margin:1rem 0 .5rem 0;">
        <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{PURPLE},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">UK Salary Calculator</span>
        <span style="color:{TEXT3};font-size:.75rem;">{"Scotland" if scotland_tax else "England / Wales / NI"} · current assumptions</span></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div style="color:{TEXT3};font-size:.8rem;margin-bottom:1rem;">A standalone take-home pay tool based on your current employment package assumptions.</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(kpi_html("Gross Income", gbp(total_gross), TEXT), unsafe_allow_html=True)
    s2.markdown(kpi_html("Take Home (Annual)", gbp(tax["net_annual"]), GREEN), unsafe_allow_html=True)
    s3.markdown(kpi_html("Take Home (Monthly)", gbp(tax["net_monthly"]), GREEN), unsafe_allow_html=True)
    s4.markdown(kpi_html("Effective Tax Rate", pct_fmt(tax["effective_rate"]), PURPLE), unsafe_allow_html=True)

    spacer("1rem")
    left, right = st.columns([1.15, 0.85])

    with left:
        st.markdown(card_open("Income Statement"), unsafe_allow_html=True)
        for label, value, color, bold in [
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
            st.markdown(row_item(label, gbp(value), color, bold), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

    with right:
        st.markdown(card_open("Tax Composition"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Income Tax", "National Insurance", "Net Pay"],
            values=[tax["income_tax"], tax["ni"], tax["net_annual"]],
            hole=0.58,
            marker=dict(colors=[RED, AMBER, GREEN], line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
        ))
        fig.update_layout(**make_layout({"height": 280, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)

        st.markdown(card_open("Tax Band Detail"), unsafe_allow_html=True)
        if tax["band_breakdown"]:
            for band in tax["band_breakdown"]:
                st.markdown(
                    row_item(f"{pct_fmt(band['rate'] * 100)} on {gbp(band['band_width'])}", gbp(band["tax"]), RED),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(f'<span style="color:{TEXT3};font-size:.82rem;">No tax bands applicable</span>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spacer("2rem")
st.markdown(
    f'<div style="text-align:center;padding:1rem 0;border-top:1px solid {BORDER};"><span style="color:{TEXT3};font-size:.7rem;letter-spacing:.06em;">◈ WEALTHVIEW · PERSONAL FINANCE DASHBOARD · FOR ILLUSTRATIVE PURPOSES ONLY</span></div>',
    unsafe_allow_html=True,
)
