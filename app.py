import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import re
import html
import io
import math
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
TEXT3 = "#E2E8F0"
PURPLE = "#8B5CF6"
BLUE = "#3B82F6"
CYAN = "#06B6D4"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
YELLOW = "#FFD60A"
DEEP_YELLOW = "#E8A308"
SLIDER_CLR = "#E8A308"
SLIDER_CLR2 = "#D4920A"
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
# PERSISTENCE (Google Sheets + JSON fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SNAPSHOT_FILE = "wealthview_snapshots.json"
SETTINGS_FILE = "wealthview_settings.json"

# ── Google Sheets connection ──
def _get_gsheet():
    """Return (spreadsheet, True) if Google Sheets is configured, else (None, False)."""
    try:
        if "gcp_service_account" not in st.secrets:
            return None, False
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        gc = gspread.authorize(creds)
        sheet_url = st.secrets.get("sheets", {}).get("spreadsheet_url", "")
        if sheet_url:
            sh = gc.open_by_url(sheet_url)
        else:
            sheet_name = st.secrets.get("sheets", {}).get("spreadsheet_name", "WealthView Data")
            try:
                sh = gc.open(sheet_name)
            except gspread.SpreadsheetNotFound:
                sh = gc.create(sheet_name)
                sh.share(None, perm_type="anyone", role="writer")
        return sh, True
    except Exception:
        return None, False

@st.cache_resource(ttl=300)
def _get_gsheet_cached():
    return _get_gsheet()

def _ensure_worksheet(sh, title, headers):
    """Get or create a worksheet with the given headers."""
    try:
        ws = sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=500, cols=len(headers))
        ws.update("A1", [headers])
    return ws

# ── Snapshot persistence ──
def load_snapshots():
    sh, ok = _get_gsheet_cached()
    if ok and sh:
        try:
            ws = _ensure_worksheet(sh, "Snapshots", [
                "period_key", "cash", "investments", "crypto", "pension",
                "real_estate_equity", "net_worth", "saved_at"
            ])
            rows = ws.get_all_records()
            data = {}
            for row in rows:
                pk = str(row.get("period_key", ""))
                if pk:
                    data[pk] = {
                        "cash": int(row.get("cash", 0)),
                        "investments": int(row.get("investments", 0)),
                        "crypto": int(row.get("crypto", 0)),
                        "pension": int(row.get("pension", 0)),
                        "real_estate_equity": int(row.get("real_estate_equity", 0)),
                        "net_worth": int(row.get("net_worth", 0)),
                        "saved_at": str(row.get("saved_at", "")),
                    }
            return data
        except Exception:
            pass
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
    sh, ok = _get_gsheet_cached()
    if ok and sh:
        try:
            ws = _ensure_worksheet(sh, "Snapshots", [
                "period_key", "cash", "investments", "crypto", "pension",
                "real_estate_equity", "net_worth", "saved_at"
            ])
            rows = [["period_key", "cash", "investments", "crypto", "pension",
                     "real_estate_equity", "net_worth", "saved_at"]]
            for pk in sorted(data.keys()):
                sd = data[pk]
                rows.append([
                    pk,
                    sd.get("cash", 0),
                    sd.get("investments", 0),
                    sd.get("crypto", 0),
                    sd.get("pension", 0),
                    sd.get("real_estate_equity", 0),
                    sd.get("net_worth", 0),
                    sd.get("saved_at", ""),
                ])
            ws.clear()
            ws.update("A1", rows)
        except Exception:
            pass

# ── Settings persistence ──
def load_settings():
    sh, ok = _get_gsheet_cached()
    if ok and sh:
        try:
            ws = _ensure_worksheet(sh, "Settings", ["key", "value"])
            rows = ws.get_all_records()
            settings = {}
            for row in rows:
                k = str(row.get("key", ""))
                v = row.get("value", "")
                if k:
                    try:
                        settings[k] = json.loads(str(v))
                    except (json.JSONDecodeError, TypeError):
                        settings[k] = v
            return settings if settings else None
        except Exception:
            pass
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

def save_settings(settings_dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_dict, f, indent=2)
    sh, ok = _get_gsheet_cached()
    if ok and sh:
        try:
            ws = _ensure_worksheet(sh, "Settings", ["key", "value"])
            rows = [["key", "value"]]
            for k, v in settings_dict.items():
                rows.append([k, json.dumps(v)])
            ws.clear()
            ws.update("A1", rows)
        except Exception:
            pass

def _check_gsheets_status():
    sh, ok = _get_gsheet_cached()
    return ok

GSHEETS_CONNECTED = _check_gsheets_status()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION STATE & DEFAULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_SETTINGS = {
    "gross_salary": 180_000,
    "annual_bonus": 0,
    "scotland_tax": False,
    "pension_contrib_pct": 3.0,
    "employer_pension_contrib_pct": 3.0,
    "monthly_invest_cash": 500,
    "monthly_invest_stocks": 1_500,
    "monthly_expenses": 0,
    "current_age": 35,
    "retirement_age": 50,
    "target_wealth": 2_000_000,
    "cash_interest_rate": 4.5,
    "expected_return": 12.0,
    "inflation": 2.5,
    "property_growth": 3.5,
    "selected_scenario": "Base",
    "bonus_month": "March",
    "rental_income": 0,
    "dividends_income": 0,
    "side_income": 0,
    "expense_housing": 0,
    "expense_transport": 0,
    "expense_food": 0,
    "expense_subscriptions": 0,
    "expense_discretionary": 0,
    "expense_other": 0,
}

# Load persisted settings on first run
if "_settings_loaded" not in st.session_state:
    _persisted = load_settings()
    if _persisted:
        for k, v in _persisted.items():
            if k == "custom_goals":
                st.session_state.custom_goals = v
            elif k == "target_alloc":
                st.session_state.target_alloc = v
            elif k in DEFAULT_SETTINGS:
                st.session_state[k] = v
    st.session_state._settings_loaded = True

if "custom_goals" not in st.session_state:
    st.session_state.custom_goals = [
        {"name": "Financial Freedom", "target": 2_000_000, "target_age": 50},
    ]

if "target_alloc" not in st.session_state:
    st.session_state.target_alloc = {"cash": 15, "stocks": 45, "crypto": 5, "pension": 25, "real_estate": 10}

# Initialize all default settings
for key, value in DEFAULT_SETTINGS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Migration: add new employer_pension_contrib_pct if not present
if "employer_pension_contrib_pct" not in st.session_state:
    st.session_state.employer_pension_contrib_pct = 3.0

# Load snapshots
snapshots = load_snapshots()

def _persist_all_settings():
    """Persist all relevant settings to file and Google Sheets."""
    settings_to_save = {k: st.session_state[k] for k in DEFAULT_SETTINGS.keys()}
    settings_to_save["custom_goals"] = st.session_state.custom_goals
    settings_to_save["target_alloc"] = st.session_state.target_alloc
    save_settings(settings_to_save)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def gbp(v):
    """Format value as GBP."""
    return f"£{v:,.0f}" if v >= 0 else f"-£{abs(v):,.0f}"

def pct_fmt(v):
    """Format value as percentage."""
    return f"{v:.1f}%"

def parse_money_input(value, default=0):
    """Parse money input, removing £ and commas."""
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).replace("£", "").replace(",", "").strip()
    try:
        return int(float(s))
    except ValueError:
        return default

def money_text_input(label, value, key, help_text=None):
    """Text input for money with formatted value."""
    return st.text_input(
        label,
        value=gbp(int(value)),
        key=key,
        help=help_text
    )

def kpi_html(label, value, color=PURPLE, icon="", sub="", info=""):
    """Render KPI card as HTML."""
    sub_html = f"<div style='font-size:.8rem;color:{TEXT2};margin-top:.25rem;'>{sub}</div>" if sub else ""
    info_html = f"<div style='font-size:.75rem;color:{TEXT3};margin-top:.5rem;line-height:1.4;'>{info}</div>" if info else ""
    icon_div = f"<div style='font-size:1.25rem;'>{icon}</div>" if icon else ""
    info_div = f"<div style='border-top:3px solid {color}44;padding-top:.75rem;margin-top:.75rem;'>{info_html}</div>" if info else ""
    return f"""
    <div style="background:linear-gradient(135deg,{CARD},{CARD_H});border:1px solid {BORDER};border-radius:16px;padding:1.25rem;box-shadow:{SHADOW_SM};min-height:230px;display:flex;flex-direction:column;justify-content:space-between;">
        <div>
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem;">
                {icon_div}
                <div style="font-size:.75rem;color:{TEXT2};text-transform:uppercase;letter-spacing:.06em;font-weight:700;">{label}</div>
            </div>
            <div style="font-size:1.8rem;font-weight:800;color:{color};letter-spacing:-.03em;">{value}</div>
            {sub_html}
        </div>
        {info_div}
    </div>
    """

def kpi_small(label, value, color=TEXT):
    """Render small metric card."""
    return f"""
    <div style="padding:.75rem;background:{CARD}66;border:1px solid {BORDER};border-radius:8px;">
        <div style="font-size:.7rem;color:{TEXT2};text-transform:uppercase;font-weight:700;margin-bottom:.3rem;">{label}</div>
        <div style="font-size:1.2rem;font-weight:800;color:{color};">{value}</div>
    </div>
    """

def card_open(title="", subtitle=""):
    """Start a card section."""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{CARD},{CARD_H});border:1px solid {BORDER};border-radius:16px;padding:1.5rem;box-shadow:{SHADOW_SM};margin-bottom:1.5rem;">
    """, unsafe_allow_html=True)
    if title:
        st.markdown(f"<div style='font-size:1.1rem;font-weight:800;color:{TEXT};margin-bottom:.5rem;'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div style='font-size:.9rem;color:{TEXT2};margin-bottom:1rem;'>{subtitle}</div>", unsafe_allow_html=True)

def card_close():
    """End a card section."""
    st.markdown("</div>", unsafe_allow_html=True)

def section_header(title, icon=""):
    """Render section header."""
    icon_span = f"<span style='font-size:1.25rem;'>{icon}</span>" if icon else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:.5rem;margin-top:1.5rem;margin-bottom:1rem;">
        {icon_span}
        <span style="font-size:1.2rem;font-weight:800;color:{TEXT};">{title}</span>
    </div>
    """, unsafe_allow_html=True)

def sidebar_label(label, color=WHITE):
    """Render sidebar label."""
    st.markdown(f"<div style='font-size:.7rem;color:{color};text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-top:.6rem;margin-bottom:.3rem;'>{label}</div>", unsafe_allow_html=True)

def row_item(label, value, color=TEXT, bold=False):
    """Render a label-value pair."""
    weight = "800" if bold else "600"
    st.markdown(f"<div style='display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid {BORDER}33;'><span style='color:{TEXT2};font-weight:600;'>{label}</span><span style='color:{color};font-weight:{weight};'>{value}</span></div>", unsafe_allow_html=True)

def progress_bar_html(pct_val, color_from=PURPLE, color_to=CYAN, height=8):
    """Render HTML progress bar."""
    clamped = max(0, min(100, pct_val))
    return f"""
    <div style="width:100%;height:{height}px;background:{BORDER};border-radius:{height}px;overflow:hidden;margin:.5rem 0;">
        <div style="width:{clamped}%;height:100%;background:linear-gradient(90deg,{color_from},{color_to});transition:width .3s ease;"></div>
    </div>
    """

def spacer(h="1rem"):
    """Add vertical spacing."""
    st.markdown(f"<div style='height:{h};'></div>", unsafe_allow_html=True)

def get_highest_milestone(nw):
    """Get highest wealth milestone reached."""
    milestones = [
        (10_000, "£10K", BLUE),
        (50_000, "£50K", PURPLE),
        (100_000, "£100K", PURPLE),
        (250_000, "£250K", BLUE),
        (500_000, "£500K", CYAN),
        (1_000_000, "£1M", GREEN),
        (2_000_000, "£2M", AMBER),
    ]
    for threshold, label, color in reversed(milestones):
        if nw >= threshold:
            return threshold, label, color
    return None

def generate_insights(net_worth, cash, investments, crypto, pension_val, real_estate_equity,
                      salary, target_wealth, current_age, retirement_age):
    """Generate wealth insights."""
    insights = []

    goal_progress = (net_worth / target_wealth * 100) if target_wealth > 0 else 0

    if goal_progress >= 100:
        insights.append((GREEN, "★", f"Target wealth achieved! {goal_progress:.0f}% of goal."))
    elif goal_progress >= 50:
        insights.append((BLUE, "◎", f"Halfway milestone passed — {goal_progress:.0f}% toward your wealth target."))
    elif goal_progress >= 25:
        insights.append((PURPLE, "◎", f"Early days — {goal_progress:.0f}% toward target. Consistent saving is key."))

    years_remaining = retirement_age - current_age
    if years_remaining > 0:
        annual_needed = (target_wealth - net_worth) / years_remaining
        if annual_needed > 0:
            insights.append((BLUE, "◎", f"Need ~{gbp(annual_needed)} annual growth to hit target by {retirement_age}."))

    cash_ratio = (cash / net_worth * 100) if net_worth > 0 else 0
    if cash_ratio > 50:
        insights.append((AMBER, "⚠", "High cash allocation — consider investing excess."))
    elif cash_ratio < 5 and net_worth > 100_000:
        insights.append((RED, "⚠", "Very low cash reserves — build emergency fund."))

    return insights

def make_layout(overrides=None):
    """Create CSS layout."""
    custom_css = f"""
    <style>
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    body, [data-testid="stAppViewContainer"] {{
        background-color: {BG};
        color: {TEXT};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: {BG_ALT};
    }}
    [data-testid="stForm"] {{
        background-color: {CARD}33;
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1.5rem;
    }}
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {{
        background-color: {CARD}!important;
        color: {TEXT}!important;
        border: 1px solid {BORDER}!important;
        border-radius: 8px!important;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {PURPLE}!important;
        box-shadow: 0 0 0 2px {PURPLE}22!important;
    }}
    .stSelectbox > div > div > select:focus {{
        border-color: {PURPLE}!important;
    }}
    [data-testid="stSlider"] {{
        padding: 1rem 0;
    }}
    [data-testid="stSlider"] > div:first-child {{
        background: linear-gradient(90deg, {SLIDER_CLR} 0%, {SLIDER_CLR2} 100%)!important;
    }}
    [data-testid="stSlider"] input {{
        border: 3px solid {SLIDER_CLR}!important;
        background-color: {WHITE}!important;
        box-shadow: 0 2px 8px rgba(0,0,0,.4)!important;
    }}
    [data-testid="stButton"] > button {{
        background: linear-gradient(135deg, {PURPLE} 0%, {BLUE} 100%)!important;
        border: none!important;
        color: {TEXT}!important;
        font-weight: 700!important;
        border-radius: 8px!important;
        box-shadow: 0 2px 8px {PURPLE}44!important;
        padding: .6rem 1.2rem!important;
        transition: all .2s ease!important;
    }}
    [data-testid="stButton"] > button:hover {{
        transform: translateY(-2px)!important;
        box-shadow: 0 4px 16px {PURPLE}66!important;
    }}
    [data-testid="stTabs"] [role="tab"] {{
        color: {TEXT2}!important;
        font-weight: 600!important;
        border-bottom: 2px solid transparent!important;
        transition: all .2s ease!important;
    }}
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
        color: {TEXT}!important;
        border-bottom: 2px solid {PURPLE}!important;
    }}
    [data-testid="stTabs"] [role="tab"]:hover {{
        color: {TEXT}!important;
        background-color: {PURPLE}11!important;
    }}
    [data-testid="stExpander"] {{
        background-color: {CARD}!important;
        border: 1px solid {BORDER}!important;
        border-radius: 8px!important;
    }}
    [data-testid="stExpander"] [role="button"] {{
        color: {TEXT}!important;
        font-weight: 700!important;
    }}
    .stCheckbox > label {{
        color: {TEXT}!important;
    }}
    .stCheckbox > label > div > input {{
        accent-color: {PURPLE}!important;
    }}
    label {{
        color: {TEXT}!important;
        font-weight: 600!important;
    }}
    </style>
    """
    if overrides:
        custom_css = custom_css.replace("</style>", f"{overrides}</style>")
    st.markdown(custom_css, unsafe_allow_html=True)

def years_to_target(df, target):
    """Years until target wealth is reached."""
    for _, row in df.iterrows():
        if row["net_worth"] >= target:
            return row["year"]
    return None

def build_history_df(snaps):
    """Build history dataframe from snapshots."""
    rows = []
    for pk in sorted(snaps.keys()):
        s = snaps[pk]
        rows.append({
            "period": pk,
            "cash": s.get("cash", 0),
            "investments": s.get("investments", 0),
            "crypto": s.get("crypto", 0),
            "pension": s.get("pension", 0),
            "real_estate_equity": s.get("real_estate_equity", 0),
            "net_worth": s.get("net_worth", 0),
            "saved_at": s.get("saved_at", ""),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAX ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_uk_tax(gross, scotland=False):
    """Calculate UK income tax and NI (exact Scottish bands)."""
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
    monthly_invest_cash,
    monthly_invest_stocks,
    monthly_pension,
    cash_interest_rate,
    stock_return,
    inflation,
    real_estate_growth,
    years,
    employer_pension_annual=0,
):
    """Forecast wealth over time."""
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
            cash_value *= (1 + cash_interest_rate / 100)
            invested_value *= (1 + stock_return / 100)
            pension_value *= (1 + stock_return / 100)
            real_estate_value *= (1 + real_estate_growth / 100)
            cash_value += monthly_invest_cash * 12
            invested_value += monthly_invest_stocks * 12
            pension_value += monthly_pension * 12 + employer_pension_annual
    return pd.DataFrame(rows)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown(f"""
    <div style="display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,{PURPLE},{BLUE});box-shadow:0 2px 10px rgba(139,92,246,.25);margin-bottom:.45rem;">
        <div style="font-size:1.2rem;font-weight:900;">◈</div>
    </div>
    <div style="font-size:1.4rem;font-weight:800;letter-spacing:-.04em;"><span style="background:linear-gradient(135deg,{PURPLE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Wealth</span><span style="color:{TEXT};">View</span></div>
    """, unsafe_allow_html=True)

    spacer("0.8rem")

    # SECTION 1: Monthly Snapshot Tracker
    st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;">Monthly Snapshot Tracker</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        reporting_month = st.selectbox("Month", MONTHS, key="reporting_month", label_visibility="collapsed")
    with col2:
        current_year = datetime.now().year
        reporting_year = st.number_input("Year", min_value=2020, max_value=2100, value=current_year, key="reporting_year", label_visibility="collapsed")

    period_key = f"{reporting_year}-{MONTHS.index(reporting_month) + 1:02d}"

    st.markdown(f'<div style="color:{TEXT2};font-size:.8rem;margin-top:.5rem;margin-bottom:.8rem;">Record your wealth snapshot</div>', unsafe_allow_html=True)

    snapshot_cash = st.number_input("Cash Savings", value=snapshots.get(period_key, {}).get("cash", 0), key="snap_cash", min_value=0)
    snapshot_stocks = st.number_input("Stocks", value=snapshots.get(period_key, {}).get("investments", 0), key="snap_stocks", min_value=0)
    snapshot_crypto = st.number_input("Crypto", value=snapshots.get(period_key, {}).get("crypto", 0), key="snap_crypto", min_value=0)
    snapshot_pension = st.number_input("Pension", value=snapshots.get(period_key, {}).get("pension", 0), key="snap_pension", min_value=0)
    snapshot_re = st.number_input("Real Estate Equity", value=snapshots.get(period_key, {}).get("real_estate_equity", 0), key="snap_re", min_value=0)

    if st.button("Save Snapshot", use_container_width=True, key="save_snap"):
        snapshot_nw = snapshot_cash + snapshot_stocks + snapshot_crypto + snapshot_pension + snapshot_re
        snapshots[period_key] = {
            "cash": int(snapshot_cash),
            "investments": int(snapshot_stocks),
            "crypto": int(snapshot_crypto),
            "pension": int(snapshot_pension),
            "real_estate_equity": int(snapshot_re),
            "net_worth": int(snapshot_nw),
            "saved_at": datetime.now().isoformat(),
        }
        save_snapshots(snapshots)
        st.success("Snapshot saved!")

    if GSHEETS_CONNECTED:
        st.markdown(f"<div style='font-size:.75rem;color:{GREEN};text-transform:uppercase;font-weight:700;margin-top:.5rem;'>✓ Google Sheets Connected</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:.75rem;color:{AMBER};text-transform:uppercase;font-weight:700;margin-top:.5rem;'>⚠ Local Storage Only</div>", unsafe_allow_html=True)

    spacer("1rem")

    # SECTION 2: Planning Inputs (in a form)
    st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-top:.6rem;margin-bottom:.3rem;">Planning Inputs</div>', unsafe_allow_html=True)

    with st.form("planning_form", border=False):
        # Employment
        st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;">Employment Package</div>', unsafe_allow_html=True)
        st.session_state.gross_salary = st.number_input("Gross Salary", value=st.session_state.gross_salary, min_value=0, key="ss_salary")
        st.session_state.annual_bonus = st.number_input("Annual Bonus", value=st.session_state.annual_bonus, min_value=0, key="ss_bonus")
        st.session_state.bonus_month = st.selectbox("Bonus Month", MONTHS, index=MONTHS.index(st.session_state.bonus_month), key="ss_bonus_month", label_visibility="collapsed")
        st.session_state.rental_income = st.number_input("Rental/Dividends Income", value=st.session_state.rental_income, min_value=0, key="ss_rental")
        st.session_state.side_income = st.number_input("Side Income", value=st.session_state.side_income, min_value=0, key="ss_side")
        st.session_state.scotland_tax = st.checkbox("Scotland Tax Bands", value=st.session_state.scotland_tax, key="ss_scotland")

        # Pension
        st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Pension Contributions</div>', unsafe_allow_html=True)
        st.session_state.pension_contrib_pct = st.slider("Employee %", 0.0, 20.0, st.session_state.pension_contrib_pct, 0.1, key="ss_pension_emp", label_visibility="collapsed")
        st.session_state.employer_pension_contrib_pct = st.slider("Employer %", 0.0, 20.0, st.session_state.employer_pension_contrib_pct, 0.1, key="ss_pension_emp2", label_visibility="collapsed")

        # Monthly investments
        st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Monthly Investment Contributions</div>', unsafe_allow_html=True)
        st.session_state.monthly_invest_cash = st.number_input("Cash Savings", value=st.session_state.monthly_invest_cash, min_value=0, key="ss_monthly_cash")
        st.session_state.monthly_invest_stocks = st.number_input("Stock Investment", value=st.session_state.monthly_invest_stocks, min_value=0, key="ss_monthly_stocks")

        # Growth assumptions
        st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Growth Rate Assumptions</div>', unsafe_allow_html=True)
        st.session_state.cash_interest_rate = st.slider("Cash Interest %", 0.0, 10.0, st.session_state.cash_interest_rate, 0.1, key="ss_cash_rate", label_visibility="collapsed")
        st.session_state.expected_return = st.slider("Stock Return %", 0.0, 25.0, st.session_state.expected_return, 0.5, key="ss_stock_return", label_visibility="collapsed")
        st.session_state.inflation = st.slider("Inflation %", 0.0, 8.0, st.session_state.inflation, 0.1, key="ss_inflation", label_visibility="collapsed")
        st.session_state.property_growth = st.slider("Property Growth %", 0.0, 10.0, st.session_state.property_growth, 0.1, key="ss_prop_growth", label_visibility="collapsed")

        # Planning & goals
        st.markdown(f'<div style="color:{PURPLE};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Planning & Goals</div>', unsafe_allow_html=True)
        st.session_state.current_age = st.number_input("Current Age", value=st.session_state.current_age, min_value=18, max_value=100, key="ss_age")
        st.session_state.retirement_age = st.number_input("Retirement Age", value=st.session_state.retirement_age, min_value=st.session_state.current_age, max_value=100, key="ss_ret_age")
        st.session_state.target_wealth = st.number_input("Target Wealth", value=st.session_state.target_wealth, min_value=0, key="ss_target")

        if st.form_submit_button("Update Settings", use_container_width=True):
            _persist_all_settings()
            st.success("Settings updated!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN CALCULATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
make_layout()

# Current snapshot (latest or user input)
period_key_latest = max(snapshots.keys()) if snapshots else None
if period_key_latest:
    snap = snapshots[period_key_latest]
    cash = snap.get("cash", 0)
    investments = snap.get("investments", 0)
    crypto = snap.get("crypto", 0)
    pension_val = snap.get("pension", 0)
    real_estate_equity = snap.get("real_estate_equity", 0)
else:
    cash = 50_000
    investments = 100_000
    crypto = 10_000
    pension_val = 150_000
    real_estate_equity = 300_000

net_worth = cash + investments + crypto + pension_val + real_estate_equity
investable_assets = cash + investments + crypto + pension_val

# Salary & tax calculations
gross_salary = st.session_state.gross_salary
annual_bonus = st.session_state.annual_bonus
bonus_month = st.session_state.bonus_month
rental_income = st.session_state.rental_income
side_income = st.session_state.side_income
additional_income = rental_income + st.session_state.dividends_income + side_income
total_gross = gross_salary + annual_bonus + additional_income

employee_pct = st.session_state.pension_contrib_pct
employer_pct = st.session_state.employer_pension_contrib_pct
employee_pension_annual = gross_salary * employee_pct / 100
employer_pension_annual = gross_salary * employer_pct / 100

taxable_gross = total_gross - employee_pension_annual
tax_result = calc_uk_tax(taxable_gross, st.session_state.scotland_tax)
net_annual_post_tax = tax_result["net_annual"]
net_monthly = tax_result["net_monthly"]

# Monthly cash flow (base)
monthly_gross_base = gross_salary / 12
monthly_bonus_amount = annual_bonus / 12
net_monthly_base = net_annual_post_tax / 12

# Bonus month logic
bonus_month_idx = MONTHS.index(bonus_month)
monthly_cash_flow = {}
for i in range(12):
    if i == bonus_month_idx:
        monthly_cash_flow[MONTHS[i]] = net_monthly_base + (annual_bonus / 12)
    else:
        monthly_cash_flow[MONTHS[i]] = net_monthly_base

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tabs = st.tabs([
    "Overview",
    "History",
    "Portfolio",
    "Pension",
    "Forecast",
    "Goals",
    "Cash Flow",
    "Salary Calculator",
    "Assumptions"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[0]:
    milestone = get_highest_milestone(net_worth)
    if milestone:
        threshold, label, color = milestone
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}22,{color}11);border:2px solid {color}44;border-radius:12px;padding:1.5rem;margin-bottom:2rem;text-align:center;">
            <div style="font-size:.8rem;color:{TEXT2};text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-bottom:.5rem;">Milestone Reached</div>
            <div style="font-size:2rem;font-weight:900;color:{color};">{label}</div>
            <div style="font-size:.9rem;color:{TEXT2};margin-top:.5rem;">You've reached {gbp(threshold)} in total wealth!</div>
        </div>
        """, unsafe_allow_html=True)

    # Badge row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_html("Total Assets", gbp(net_worth), PURPLE, "◆"), unsafe_allow_html=True)
    with col2:
        pct_invested = ((investments + crypto + pension_val) / net_worth * 100) if net_worth > 0 else 0
        st.markdown(kpi_html("Growth Assets", f"{pct_invested:.0f}%", BLUE, "↗"), unsafe_allow_html=True)
    with col3:
        pct_cash = (cash / net_worth * 100) if net_worth > 0 else 0
        st.markdown(kpi_html("Liquidity", f"{pct_cash:.0f}%", CYAN, "≈"), unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_html("Pension Value", gbp(pension_val), GREEN, "◎"), unsafe_allow_html=True)

    st.markdown("")

    # Wealth composition chart
    col1, col2 = st.columns([2, 1])
    with col1:
        pie_data = [cash, investments, crypto, pension_val, real_estate_equity]
        pie_labels = [LBL_CASH, LBL_STOCK, LBL_CRYPTO, LBL_PENSION, LBL_RE]
        pie_colors = [BLUE, PURPLE, CYAN, GREEN, AMBER]

        fig = go.Figure(data=[go.Pie(
            labels=pie_labels,
            values=pie_data,
            marker=dict(colors=pie_colors, line=dict(color=CARD, width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=11, family="Inter"),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
        )])
        fig.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD,
            font=BOLD_WHITE_SM,
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)

    with col2:
        st.markdown("<div style='padding:.5rem;'></div>", unsafe_allow_html=True)
        asset_items = [
            (LBL_CASH, cash, BLUE),
            (LBL_STOCK, investments, PURPLE),
            (LBL_CRYPTO, crypto, CYAN),
            (LBL_PENSION, pension_val, GREEN),
            (LBL_RE, real_estate_equity, AMBER),
        ]
        for label, value, color in asset_items:
            pct = (value / net_worth * 100) if net_worth > 0 else 0
            st.markdown(f"<div style='padding:.6rem 0;border-bottom:1px solid {BORDER}33;'><div style='display:flex;justify-content:space-between;align-items:center;'><span style='color:{TEXT2};font-size:.9rem;font-weight:600;'>{label}</span><span style='color:{color};font-weight:800;'>{gbp(value)}</span></div><div style='font-size:.75rem;color:{TEXT3};margin-top:.3rem;'>{pct:.1f}% of total</div></div>", unsafe_allow_html=True)

    st.markdown("")

    # Insights
    with st.expander("Insights & Recommendations", expanded=True):
        insights = generate_insights(net_worth, cash, investments, crypto, pension_val, real_estate_equity,
                                    gross_salary, st.session_state.target_wealth, st.session_state.current_age,
                                    st.session_state.retirement_age)
        if insights:
            for color, icon, text in insights:
                st.markdown(f"<div style='display:flex;gap:.75rem;padding:.75rem;background:{color}11;border-left:3px solid {color};border-radius:4px;margin-bottom:.5rem;'><div style='color:{color};font-size:1rem;flex-shrink:0;'>{icon}</div><div style='color:{TEXT};font-size:.9rem;line-height:1.5;'>{text}</div></div>", unsafe_allow_html=True)
        else:
            st.info("No insights at this time. Update your settings to generate recommendations.")

    with st.expander("Getting Started", expanded=False):
        st.markdown(f"""
        Welcome to **WealthView** — your personal wealth management dashboard.

        1. **Update Your Settings** (Sidebar) — Enter your salary, investment amounts, and goals
        2. **Track Snapshots** (Sidebar) — Record your monthly wealth in the snapshot tracker
        3. **Monitor History** (History Tab) — Watch your wealth grow month by month
        4. **Review Portfolio** (Portfolio Tab) — See your asset allocation and rebalancing suggestions
        5. **Plan Ahead** (Forecast Tab) — Model different scenarios to hit your target wealth
        """)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[1]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Wealth History</div>", unsafe_allow_html=True)

    if snapshots:
        hist_df = build_history_df(snapshots)

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df["period"], y=hist_df["net_worth"],
                                 mode="lines+markers", name="Net Worth",
                                 line=dict(color=PURPLE, width=3),
                                 marker=dict(size=8, color=PURPLE, line=dict(color=TEXT, width=1)),
                                 fill="tozeroy", fillcolor=f"{PURPLE}22",
                                 hovertemplate="<b>%{x}</b><br>" + gbp(0) + ": %{y:,.0f}<extra></extra>"))
        fig.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD,
            xaxis=GRID_AXIS, yaxis=GRID_AXIS,
            font=BOLD_WHITE_SM,
            margin=dict(l=0, r=0, t=0, b=0),
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)

        st.markdown("")

        # Comparison mode
        col1, col2 = st.columns(2)
        with col1:
            compare_from = st.selectbox("Compare From", hist_df["period"].tolist(), key="comp_from")
        with col2:
            compare_to = st.selectbox("Compare To", hist_df["period"].tolist(), key="comp_to", index=len(hist_df) - 1)

        from_idx = hist_df[hist_df["period"] == compare_from].index[0]
        to_idx = hist_df[hist_df["period"] == compare_to].index[0]
        from_row = hist_df.iloc[from_idx]
        to_row = hist_df.iloc[to_idx]

        st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .5rem 0;'>Comparison: {compare_from} → {compare_to}</div>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        comparisons = [
            ("Cash", from_row["cash"], to_row["cash"], col1),
            ("Stocks", from_row["investments"], to_row["investments"], col2),
            ("Crypto", from_row["crypto"], to_row["crypto"], col3),
            ("Pension", from_row["pension"], to_row["pension"], col4),
            ("Real Estate", from_row["real_estate_equity"], to_row["real_estate_equity"], col5),
            ("Net Worth", from_row["net_worth"], to_row["net_worth"], col6),
        ]

        for label, from_val, to_val, col in comparisons:
            change = to_val - from_val
            pct_change = (change / from_val * 100) if from_val > 0 else 0
            color = GREEN if change >= 0 else RED
            with col:
                st.markdown(kpi_small(label, gbp(to_val)), unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:.75rem;color:{color};font-weight:700;margin-top:.3rem;'>{'↑' if change >= 0 else '↓'} {pct_change:.1f}%</div>", unsafe_allow_html=True)

        st.markdown("")

        # Growth table
        st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .5rem 0;'>Growth Table</div>", unsafe_allow_html=True)

        growth_table = hist_df[["period", "cash", "investments", "crypto", "pension", "real_estate_equity", "net_worth"]].copy()
        growth_table["cash"] = growth_table["cash"].apply(gbp)
        growth_table["investments"] = growth_table["investments"].apply(gbp)
        growth_table["crypto"] = growth_table["crypto"].apply(gbp)
        growth_table["pension"] = growth_table["pension"].apply(gbp)
        growth_table["real_estate_equity"] = growth_table["real_estate_equity"].apply(gbp)
        growth_table["net_worth"] = growth_table["net_worth"].apply(gbp)
        growth_table.columns = ["Period", LBL_CASH, LBL_STOCK, LBL_CRYPTO, LBL_PENSION, LBL_RE, "Net Worth"]

        st.dataframe(growth_table, use_container_width=True, hide_index=True)

        # CSV export
        csv_data = hist_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name="wealthview_history.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No snapshots recorded yet. Start by saving a snapshot in the sidebar!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[2]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Portfolio Allocation</div>", unsafe_allow_html=True)

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(kpi_html("Investable Assets", gbp(investable_assets), PURPLE), unsafe_allow_html=True)
    with col2:
        cash_pct = (cash / investable_assets * 100) if investable_assets > 0 else 0
        st.markdown(kpi_html("Cash %", f"{cash_pct:.1f}%", BLUE), unsafe_allow_html=True)
    with col3:
        growth_assets = investments + crypto + pension_val
        growth_pct = (growth_assets / investable_assets * 100) if investable_assets > 0 else 0
        st.markdown(kpi_html("Growth Assets %", f"{growth_pct:.1f}%", CYAN), unsafe_allow_html=True)
    with col4:
        blended_return = (st.session_state.cash_interest_rate * cash_pct / 100 +
                         st.session_state.expected_return * growth_pct / 100)
        st.markdown(kpi_html("Est. Blended Return", f"{blended_return:.2f}%", GREEN), unsafe_allow_html=True)
    with col5:
        largest = max([
            ("Cash", cash),
            ("Stocks", investments),
            ("Crypto", crypto),
            ("Pension", pension_val),
        ], key=lambda x: x[1])
        st.markdown(kpi_html("Largest Allocation", largest[0], AMBER), unsafe_allow_html=True)

    st.markdown("")

    # Asset class table
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Asset Class Detail</div>", unsafe_allow_html=True)

    target_alloc = st.session_state.target_alloc
    asset_classes = [
        ("Cash", cash, target_alloc["cash"]),
        ("Stocks", investments, target_alloc["stocks"]),
        ("Crypto", crypto, target_alloc["crypto"]),
        ("Pension", pension_val, target_alloc["pension"]),
    ]

    table_html = f"<table style='width:100%;border-collapse:collapse;'>"
    table_html += f"<tr style='border-bottom:2px solid {BORDER};'><th style='text-align:left;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Asset Class</th><th style='text-align:right;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Current Value</th><th style='text-align:right;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Current %</th><th style='text-align:right;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Target %</th><th style='text-align:right;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Variance %</th><th style='text-align:left;padding:.75rem;color:{TEXT};font-weight:700;font-size:.85rem;'>Action</th></tr>"

    for asset, value, target_pct in asset_classes:
        current_pct = (value / investable_assets * 100) if investable_assets > 0 else 0
        variance = current_pct - target_pct

        if abs(variance) < 2:
            action = "On target"
            action_color = GREEN
        elif variance > 0:
            action = "Overweight"
            action_color = RED
        else:
            action = "Underweight"
            action_color = AMBER

        suggested_adjustment = (target_pct - current_pct) / 100 * investable_assets

        table_html += f"""
        <tr style='border-bottom:1px solid {BORDER}33;'>
            <td style='padding:.75rem;color:{TEXT};font-weight:600;'>{asset}</td>
            <td style='text-align:right;padding:.75rem;color:{TEXT2};'>{gbp(value)}</td>
            <td style='text-align:right;padding:.75rem;color:{TEXT2};'>{current_pct:.1f}%</td>
            <td style='text-align:right;padding:.75rem;color:{TEXT2};'>{target_pct:.1f}%</td>
            <td style='text-align:right;padding:.75rem;color:{action_color};font-weight:700;'>{variance:+.1f}%</td>
            <td style='padding:.75rem;'><span style='background:{action_color}22;color:{action_color};padding:.4rem .6rem;border-radius:4px;font-size:.8rem;font-weight:700;'>{action}</span></td>
        </tr>
        """

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("")

    # Allocation comparison chart
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<div style='font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:.5rem;'>Current Allocation</div>", unsafe_allow_html=True)
        current_values = [cash, investments, crypto, pension_val]
        current_labels = ["Cash", "Stocks", "Crypto", "Pension"]
        fig1 = go.Figure(data=[go.Pie(
            labels=current_labels,
            values=current_values,
            marker=dict(colors=[BLUE, PURPLE, CYAN, GREEN], line=dict(color=CARD, width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=10),
        )])
        fig1.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font=BOLD_WHITE_SM,
                          margin=dict(l=0, r=0, t=0, b=0), height=250, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True, config=PLT_CFG)

    with col2:
        st.markdown(f"<div style='font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:.5rem;'>Target Allocation</div>", unsafe_allow_html=True)
        target_values = [
            investable_assets * target_alloc["cash"] / 100,
            investable_assets * target_alloc["stocks"] / 100,
            investable_assets * target_alloc["crypto"] / 100,
            investable_assets * target_alloc["pension"] / 100,
        ]
        target_labels = ["Cash", "Stocks", "Crypto", "Pension"]
        fig2 = go.Figure(data=[go.Pie(
            labels=target_labels,
            values=target_values,
            marker=dict(colors=[BLUE, PURPLE, CYAN, GREEN], line=dict(color=CARD, width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=10),
        )])
        fig2.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font=BOLD_WHITE_SM,
                          margin=dict(l=0, r=0, t=0, b=0), height=250, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config=PLT_CFG)

    st.markdown("")

    # Rebalancing guide
    with st.expander("Rebalancing Guide", expanded=False):
        st.markdown(f"""
        **Rebalancing** brings your portfolio back to target allocations.

        Use the variance percentages above to identify overweight and underweight positions:
        - **Underweight**: Consider increasing this allocation
        - **Overweight**: Consider taking profits and rebalancing
        - **On target**: Maintain current allocation

        Review your allocation quarterly and rebalance when variance exceeds ±5%.
        """)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: PENSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[3]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Pension Planning</div>", unsafe_allow_html=True)

    # Summary KPIs
    years_to_retirement = st.session_state.retirement_age - st.session_state.current_age

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(kpi_html("Current Value", gbp(pension_val), PURPLE), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_html("Employee Annual", gbp(employee_pension_annual), BLUE), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_html("Employer Annual", gbp(employer_pension_annual), CYAN), unsafe_allow_html=True)
    with col4:
        total_annual = employee_pension_annual + employer_pension_annual
        st.markdown(kpi_html("Total Annual", gbp(total_annual), GREEN), unsafe_allow_html=True)
    with col5:
        # Project pension forward with stock returns
        pension_at_retirement = forecast_wealth(
            0, 0, pension_val, 0,
            0, 0, employee_pension_annual / 12,
            st.session_state.cash_interest_rate,
            st.session_state.expected_return,
            st.session_state.inflation,
            0, years_to_retirement,
            employer_pension_annual
        )
        projected_pension = pension_at_retirement.iloc[-1]["pension"] if len(pension_at_retirement) > 0 else pension_val
        st.markdown(kpi_html("Projected @ Retirement", gbp(projected_pension), AMBER), unsafe_allow_html=True)
    with col6:
        st.markdown(kpi_html("Years to Retirement", str(years_to_retirement), YELLOW), unsafe_allow_html=True)

    st.markdown("")

    # Pension trajectory chart
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Pension Growth Trajectory</div>", unsafe_allow_html=True)

    trajectory_df = forecast_wealth(
        0, 0, pension_val, 0,
        0, 0, employee_pension_annual / 12,
        st.session_state.cash_interest_rate,
        st.session_state.expected_return,
        st.session_state.inflation,
        0, years_to_retirement,
        employer_pension_annual
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trajectory_df["year"], y=trajectory_df["pension"],
        mode="lines+markers", name="Pension Value",
        line=dict(color=PURPLE, width=3),
        marker=dict(size=6, color=PURPLE),
        fill="tozeroy", fillcolor=f"{PURPLE}22",
        hovertemplate="Year %{x}<br>" + gbp(0) + ": %{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        xaxis=dict(title="Years", **GRID_AXIS),
        yaxis=dict(title="Pension Value", **GRID_AXIS),
        font=BOLD_WHITE_SM, margin=dict(l=50, r=0, t=0, b=50),
        height=300, hovermode="x"
    )
    st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)

    st.markdown("")

    # Contribution breakdown
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Contribution Breakdown</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_small("Employee Monthly", gbp(employee_pension_annual / 12)), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_small("Employer Monthly", gbp(employer_pension_annual / 12)), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_small("Total Monthly", gbp((employee_pension_annual + employer_pension_annual) / 12)), unsafe_allow_html=True)
    with col4:
        pct_of_salary = ((employee_pension_annual + employer_pension_annual) / gross_salary * 100) if gross_salary > 0 else 0
        st.markdown(kpi_small("% of Salary", f"{pct_of_salary:.1f}%"), unsafe_allow_html=True)

    st.markdown("")

    # Retirement readiness
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Retirement Readiness</div>", unsafe_allow_html=True)

    drawdown_4pct = projected_pension * 0.04
    monthly_retirement_income = drawdown_4pct / 12

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_small("Projected Pot", gbp(projected_pension)), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_small("4% Drawdown/Year", gbp(drawdown_4pct)), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_small("Monthly Income", gbp(monthly_retirement_income)), unsafe_allow_html=True)
    with col4:
        readiness_pct = min(100, (projected_pension / st.session_state.target_wealth * 100)) if st.session_state.target_wealth > 0 else 0
        color = GREEN if readiness_pct >= 100 else AMBER if readiness_pct >= 50 else RED
        st.markdown(kpi_small("Target Progress", f"{readiness_pct:.0f}%"), unsafe_allow_html=True)

    st.markdown("")

    with st.expander("Pension Details", expanded=False):
        st.markdown(f"""
        **Your Pension Contributions**

        - **Employee Rate**: {employee_pct}% of {gbp(gross_salary)} = {gbp(employee_pension_annual)}/year
        - **Employer Rate**: {employer_pct}% of {gbp(gross_salary)} = {gbp(employer_pension_annual)}/year
        - **Total Annual**: {gbp(employee_pension_annual + employer_pension_annual)}

        **Projected at Retirement (age {st.session_state.retirement_age})**

        Your pension is projected to reach **{gbp(projected_pension)}** by retirement, assuming:
        - Current contributions continue
        - Average annual return of {st.session_state.expected_return}%

        Using the **4% rule** for sustainable withdrawal:
        - Annual income: {gbp(drawdown_4pct)}
        - Monthly income: {gbp(monthly_retirement_income)}
        """)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: FORECAST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[4]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Wealth Forecast</div>", unsafe_allow_html=True)

    # Scenario selector
    st.session_state.selected_scenario = st.radio(
        "Scenario",
        ["Conservative", "Base", "Aggressive"],
        horizontal=True,
        index=["Conservative", "Base", "Aggressive"].index(st.session_state.selected_scenario)
    )

    if st.session_state.selected_scenario == "Conservative":
        stock_ret = st.session_state.expected_return - 2
    elif st.session_state.selected_scenario == "Aggressive":
        stock_ret = st.session_state.expected_return + 2
    else:
        stock_ret = st.session_state.expected_return

    years_to_forecast = st.session_state.retirement_age - st.session_state.current_age

    forecast_df = forecast_wealth(
        cash, investments, pension_val, real_estate_equity,
        st.session_state.monthly_invest_cash,
        st.session_state.monthly_invest_stocks,
        employee_pension_annual / 12,
        st.session_state.cash_interest_rate,
        stock_ret,
        st.session_state.inflation,
        st.session_state.property_growth,
        years_to_forecast,
        employer_pension_annual
    )

    # Milestone cards
    col1, col2, col3, col4 = st.columns(4)
    milestones_to_show = [100_000, 500_000, 1_000_000, st.session_state.target_wealth]
    colors_milestone = [BLUE, CYAN, GREEN, AMBER]

    for col, target, color in zip([col1, col2, col3, col4], milestones_to_show, colors_milestone):
        with col:
            years = years_to_target(forecast_df, target)
            if years is not None:
                age_at_target = st.session_state.current_age + years
                st.markdown(kpi_html(gbp(target), f"Age {age_at_target}", color), unsafe_allow_html=True)
            else:
                st.markdown(kpi_html(gbp(target), "Not reached", color), unsafe_allow_html=True)

    st.markdown("")

    # Forecast chart
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Wealth Growth ({st.session_state.selected_scenario})</div>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["net_worth"],
                            mode="lines+markers", name="Net Worth",
                            line=dict(color=PURPLE, width=3),
                            marker=dict(size=5), fill="tozeroy", fillcolor=f"{PURPLE}22",
                            hovertemplate="Year %{x}<br>" + gbp(0) + ": %{y:,.0f}<extra></extra>"))
    fig.add_hline(y=st.session_state.target_wealth, line_dash="dash", line_color=AMBER,
                 annotation_text="Target", annotation_position="right")
    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        xaxis=dict(title="Years", **GRID_AXIS),
        yaxis=dict(title="Net Worth", **GRID_AXIS),
        font=BOLD_WHITE_SM, margin=dict(l=50, r=0, t=0, b=50),
        height=350, hovermode="x"
    )
    st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)

    st.markdown("")

    # Nominal vs Real
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<div style='font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:.5rem;'>Nominal (Today's Pounds)</div>", unsafe_allow_html=True)
        fig_nom = go.Figure()
        fig_nom.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["net_worth"],
                                    mode="lines", name="Nominal",
                                    line=dict(color=PURPLE, width=3), fill="tozeroy",
                                    fillcolor=f"{PURPLE}22"))
        fig_nom.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, xaxis=GRID_AXIS,
                             yaxis=GRID_AXIS, font=BOLD_WHITE_SM,
                             margin=dict(l=50, r=0, t=0, b=50), height=300)
        st.plotly_chart(fig_nom, use_container_width=True, config=PLT_CFG)

    with col2:
        st.markdown(f"<div style='font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:.5rem;'>Real (Inflation-Adjusted)</div>", unsafe_allow_html=True)
        fig_real = go.Figure()
        fig_real.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["net_worth_real"],
                                     mode="lines", name="Real",
                                     line=dict(color=CYAN, width=3), fill="tozeroy",
                                     fillcolor=f"{CYAN}22"))
        fig_real.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, xaxis=GRID_AXIS,
                              yaxis=GRID_AXIS, font=BOLD_WHITE_SM,
                              margin=dict(l=50, r=0, t=0, b=50), height=300)
        st.plotly_chart(fig_real, use_container_width=True, config=PLT_CFG)

    st.markdown("")

    # What-If Playground
    with st.expander("What-If Playground", expanded=False):
        st.markdown(f"<div style='font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:1rem;'>Adjust assumptions and see impact on forecast</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            what_if_monthly_invest = st.number_input("Monthly Investment", value=st.session_state.monthly_invest_cash + st.session_state.monthly_invest_stocks, min_value=0, key="what_if_invest")
        with col2:
            what_if_return = st.slider("Stock Return %", 0.0, 25.0, st.session_state.expected_return, 0.5, key="what_if_return")
        with col3:
            what_if_age = st.number_input("Target Retirement Age", value=st.session_state.retirement_age, min_value=st.session_state.current_age, key="what_if_age")

        years_what_if = what_if_age - st.session_state.current_age
        what_if_df = forecast_wealth(
            cash, investments, pension_val, real_estate_equity,
            what_if_monthly_invest / 2, what_if_monthly_invest / 2,
            employee_pension_annual / 12,
            st.session_state.cash_interest_rate,
            what_if_return,
            st.session_state.inflation,
            st.session_state.property_growth,
            years_what_if,
            employer_pension_annual
        )

        fig_what_if = go.Figure()
        fig_what_if.add_trace(go.Scatter(x=what_if_df["year"], y=what_if_df["net_worth"],
                                        mode="lines", name="What-If Scenario",
                                        line=dict(color=BLUE, width=3)))
        fig_what_if.add_hline(y=st.session_state.target_wealth, line_dash="dash", line_color=AMBER)
        fig_what_if.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD,
                                 xaxis=GRID_AXIS, yaxis=GRID_AXIS, font=BOLD_WHITE_SM,
                                 margin=dict(l=50, r=0, t=0, b=50), height=300)
        st.plotly_chart(fig_what_if, use_container_width=True, config=PLT_CFG)

        what_if_final = what_if_df.iloc[-1]["net_worth"] if len(what_if_df) > 0 else 0
        st.markdown(f"**Result**: {gbp(what_if_final)} at age {what_if_age}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[5]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Goals & Milestones</div>", unsafe_allow_html=True)

    if st.session_state.custom_goals:
        for i, goal in enumerate(st.session_state.custom_goals):
            goal_progress = (net_worth / goal["target"] * 100) if goal["target"] > 0 else 0
            years_to_goal = goal["target_age"] - st.session_state.current_age

            color = GREEN if goal_progress >= 100 else BLUE if goal_progress >= 50 else AMBER

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{CARD},{CARD_H});border:1px solid {BORDER};border-radius:12px;padding:1.5rem;margin-bottom:1rem;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:1rem;">
                        <div style="font-size:1.1rem;font-weight:800;color:{TEXT};">{goal['name']}</div>
                        <div style="font-size:.8rem;color:{TEXT2};">Age {goal['target_age']}</div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:.75rem;">
                        <div><span style="color:{TEXT2};font-size:.85rem;">Progress</span><br><span style="color:{color};font-weight:800;font-size:1.3rem;">{goal_progress:.0f}%</span></div>
                        <div><span style="color:{TEXT2};font-size:.85rem;">Target</span><br><span style="color:{TEXT};font-weight:800;font-size:1.3rem;">{gbp(goal['target'])}</span></div>
                        <div><span style="color:{TEXT2};font-size:.85rem;">Current</span><br><span style="color:{TEXT};font-weight:800;font-size:1.3rem;">{gbp(net_worth)}</span></div>
                    </div>
                    {progress_bar_html(goal_progress, color, color)}
                    <div style="font-size:.8rem;color:{TEXT2};margin-top:.75rem;">Gap: {gbp(max(0, goal['target'] - net_worth))}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button(f"Delete", key=f"del_goal_{i}"):
                    st.session_state.custom_goals.pop(i)
                    _persist_all_settings()
                    st.rerun()

    st.markdown("")

    # Add new goal
    with st.expander("Add New Goal", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_goal_name = st.text_input("Goal Name", key="new_goal_name")
        with col2:
            new_goal_target = st.number_input("Target Amount", value=2_000_000, min_value=0, key="new_goal_target")
        with col3:
            new_goal_age = st.number_input("Target Age", value=50, min_value=st.session_state.current_age, key="new_goal_age")

        if st.button("Add Goal"):
            if new_goal_name:
                st.session_state.custom_goals.append({
                    "name": new_goal_name,
                    "target": new_goal_target,
                    "target_age": new_goal_age,
                })
                _persist_all_settings()
                st.success(f"Goal '{new_goal_name}' added!")
            else:
                st.error("Please enter a goal name")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: CASH FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[6]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Monthly Cash Flow Analysis</div>", unsafe_allow_html=True)

    # Summary
    total_monthly_gross = gross_salary / 12 + annual_bonus / 12
    total_expenses = (st.session_state.expense_housing + st.session_state.expense_transport +
                     st.session_state.expense_food + st.session_state.expense_subscriptions +
                     st.session_state.expense_discretionary + st.session_state.expense_other)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_html("Avg Gross Monthly", gbp(total_monthly_gross), PURPLE), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_html("Avg Net Monthly", gbp(net_monthly), BLUE), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_html("Monthly Expenses", gbp(total_expenses), AMBER), unsafe_allow_html=True)
    with col4:
        surplus = net_monthly - total_expenses
        color = GREEN if surplus >= 0 else RED
        st.markdown(kpi_html("Monthly Surplus", gbp(surplus), color), unsafe_allow_html=True)

    st.markdown("")

    # Monthly breakdown table
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Monthly Breakdown by Scenario</div>", unsafe_allow_html=True)

    breakdown_rows = []
    for month in MONTHS:
        monthly_net = monthly_cash_flow.get(month, net_monthly)
        breakdown_rows.append({
            "Month": month,
            "Gross": gbp(monthly_net + tax_result["total_deductions"] / 12),
            "Net": gbp(monthly_net),
            "Expenses": gbp(total_expenses),
            "Surplus": gbp(monthly_net - total_expenses)
        })

    breakdown_df = pd.DataFrame(breakdown_rows)
    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    st.markdown("")

    # Expense breakdown
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Expense Breakdown</div>", unsafe_allow_html=True)

    expenses = [
        ("Housing", st.session_state.expense_housing),
        ("Transport", st.session_state.expense_transport),
        ("Food", st.session_state.expense_food),
        ("Subscriptions", st.session_state.expense_subscriptions),
        ("Discretionary", st.session_state.expense_discretionary),
        ("Other", st.session_state.expense_other),
    ]

    expense_rows = []
    for label, amount in expenses:
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        expense_rows.append({
            "Category": label,
            "Amount": gbp(amount),
            "% of Total": f"{pct:.1f}%"
        })

    expense_df = pd.DataFrame(expense_rows)
    st.dataframe(expense_df, use_container_width=True, hide_index=True)

    if total_expenses > 0:
        fig = go.Figure(data=[go.Pie(
            labels=[e[0] for e in expenses],
            values=[e[1] for e in expenses],
            marker=dict(colors=[BLUE, PURPLE, CYAN, GREEN, AMBER, RED], line=dict(color=CARD, width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=10),
        )])
        fig.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font=BOLD_WHITE_SM,
                         margin=dict(l=0, r=0, t=0, b=0), height=300)
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: SALARY CALCULATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[7]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Salary Calculator</div>", unsafe_allow_html=True)

    # Summary boxes
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(kpi_html("Gross Annual", gbp(gross_salary), PURPLE), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_html("Gross Monthly", gbp(gross_salary / 12), BLUE), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_html("Net Annual", gbp(net_annual_post_tax), CYAN), unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_html("Net Monthly", gbp(net_monthly), GREEN), unsafe_allow_html=True)

    st.markdown("")

    # Tax breakdown
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Tax & National Insurance Breakdown</div>", unsafe_allow_html=True)

    tax_rows = [
        ("Gross Income", gbp(total_gross), TEXT),
        ("Personal Allowance", gbp(-tax_result["personal_allowance"]), TEXT2),
        ("Taxable Income", gbp(tax_result["taxable_income"]), TEXT2),
        ("Income Tax", gbp(-tax_result["income_tax"]), RED),
        ("National Insurance", gbp(-tax_result["ni"]), RED),
        ("Pension Contribution", gbp(-employee_pension_annual), BLUE),
        ("Net Annual (after tax & pension)", gbp(net_annual_post_tax), GREEN),
    ]

    for label, value, color in tax_rows:
        st.markdown(f"<div style='display:flex;justify-content:space-between;padding:.5rem 0;border-bottom:1px solid {BORDER}33;'><span style='color:{TEXT2};font-weight:600;'>{label}</span><span style='color:{color};font-weight:800;'>{value}</span></div>", unsafe_allow_html=True)

    st.markdown("")

    # Yearly/Monthly/Weekly/Daily breakdown (HTML table)
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Income Breakdown</div>", unsafe_allow_html=True)
    def _sal_fmt(v):
        sign = "-" if v < 0 else ""
        return f"{sign}£{abs(v):,.2f}"
    _sal_data = [
        ("Gross Income", total_gross, False, False, False),
        ("Pension Deductions", -employee_pension_annual, False, False, False),
        ("Taxable Income", taxable_gross, True, False, False),
        ("Income Tax", -tax_result["income_tax"], False, True, False),
        ("National Insurance", -tax_result["ni"], False, True, False),
        ("Take Home", net_annual_post_tax, True, False, True),
    ]
    _th = f"<th style='text-align:right;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;'>"
    _tbl = f"<div style='background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.2rem;box-shadow:{SHADOW};margin-bottom:1rem;overflow-x:auto;'>"
    _tbl += f"<table style='width:100%;border-collapse:collapse;'><thead><tr style='border-bottom:2px solid {BORDER_L};'><th style='text-align:left;padding:.6rem .8rem;'></th>{_th}Yearly</th>{_th}Monthly</th>{_th}Weekly</th>{_th}Daily</th></tr></thead><tbody>"
    for lbl, yearly, is_bold, is_red, is_green in _sal_data:
        fw = "700" if is_bold else "500"
        clr = GREEN if is_green else (RED if is_red else TEXT)
        monthly = yearly / 12
        weekly = yearly / 52
        daily = yearly / 260
        _td = f"<td style='padding:.6rem .8rem;color:{clr};font-weight:{fw};font-size:.86rem;text-align:right;'>"
        _tbl += f"<tr style='border-bottom:1px solid {BORDER};'><td style='padding:.6rem .8rem;color:{clr};font-weight:{fw};font-size:.86rem;'>{lbl}</td>{_td}{_sal_fmt(yearly)}</td>{_td}{_sal_fmt(monthly)}</td>{_td}{_sal_fmt(weekly)}</td>{_td}{_sal_fmt(daily)}</td></tr>"
    _tbl += "</tbody></table></div>"
    st.markdown(_tbl, unsafe_allow_html=True)

    st.markdown("")

    # Bonus comparison
    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Bonus Impact by Month</div>", unsafe_allow_html=True)

    bonus_comparison = []
    for month in MONTHS:
        monthly_net = monthly_cash_flow.get(month, net_monthly)
        bonus_comparison.append({
            "Month": month,
            "Net Income": gbp(monthly_net),
            "Bonus?": "Yes" if month == bonus_month else "No"
        })

    bonus_df = pd.DataFrame(bonus_comparison)
    st.dataframe(bonus_df, use_container_width=True, hide_index=True)

    st.markdown("")

    # Personal allowance notice
    if total_gross > 100_000:
        st.warning(f"Personal Allowance Taper: Your gross income exceeds £100k, so your personal allowance is reduced by 50% of the excess (£{total_gross - 100_000:,.0f}). This results in a personal allowance of £{tax_result['personal_allowance']:,.0f}.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: ASSUMPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[8]:
    st.markdown(f"<div style='font-size:1.2rem;font-weight:800;color:{TEXT};margin-bottom:1rem;'>Assumptions & Settings</div>", unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Personal Details</div>", unsafe_allow_html=True)
    row_item("Current Age", str(st.session_state.current_age))
    row_item("Retirement Age", str(st.session_state.retirement_age))
    row_item("Years to Retirement", str(years_to_retirement))

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Employment Income</div>", unsafe_allow_html=True)
    row_item("Gross Salary", gbp(gross_salary))
    row_item("Annual Bonus", gbp(annual_bonus))
    row_item("Bonus Month", bonus_month)
    row_item("Rental/Dividends Income", gbp(rental_income))
    row_item("Side Income", gbp(side_income))
    row_item("Scotland Tax", "Yes" if st.session_state.scotland_tax else "No")

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Pension</div>", unsafe_allow_html=True)
    row_item("Employee Contribution %", f"{employee_pct}%")
    row_item("Employer Contribution %", f"{employer_pct}%")
    row_item("Employee Annual", gbp(employee_pension_annual))
    row_item("Employer Annual", gbp(employer_pension_annual))

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Monthly Investments</div>", unsafe_allow_html=True)
    row_item("Cash Savings", gbp(st.session_state.monthly_invest_cash))
    row_item("Stock Investment", gbp(st.session_state.monthly_invest_stocks))
    row_item("Total Monthly Investment", gbp(st.session_state.monthly_invest_cash + st.session_state.monthly_invest_stocks))

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Growth Assumptions</div>", unsafe_allow_html=True)
    row_item("Cash Interest Rate", f"{st.session_state.cash_interest_rate}%")
    row_item("Stock Expected Return", f"{st.session_state.expected_return}%")
    row_item("Inflation Rate", f"{st.session_state.inflation}%")
    row_item("Property Growth Rate", f"{st.session_state.property_growth}%")

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Financial Goals</div>", unsafe_allow_html=True)
    row_item("Target Wealth", gbp(st.session_state.target_wealth))
    row_item("Current Net Worth", gbp(net_worth))
    row_item("Gap to Target", gbp(max(0, st.session_state.target_wealth - net_worth)))

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1rem 0 .75rem 0;'>Target Allocation</div>", unsafe_allow_html=True)
    for asset, pct in st.session_state.target_alloc.items():
        row_item(asset.capitalize(), f"{pct}%")

st.markdown("")
st.markdown(f"<div style='text-align:center;color:{TEXT3};font-size:.75rem;margin-top:2rem;padding:1rem;border-top:1px solid {BORDER};'>WealthView v1.0 | Data persisted locally and to Google Sheets</div>", unsafe_allow_html=True)
