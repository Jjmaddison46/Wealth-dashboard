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
TEXT2 = "#E0E7F1"
TEXT3 = "#F0F3F8"
PURPLE = "#8B5CF6"
BLUE = "#3B82F6"
CYAN = "#06B6D4"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
YELLOW = "#FFD60A"
DEEP_YELLOW = "#E8A308"
# Unified accent for sliders & interactive controls
SLIDER_CLR = "#E8A308"
SLIDER_CLR2 = "#D4950A"
WHITE = "#FFFFFF"
BLACK = "#000000"
SHADOW = "0 4px 24px rgba(0,0,0,.35), 0 1px 4px rgba(0,0,0,.25)"
SHADOW_SM = "0 2px 12px rgba(0,0,0,.25)"
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
LBL_CASH = "Cash Savings"
LBL_STOCK = "Stocks & Shares"
LBL_CRYPTO = "Crypto"
LBL_PENSION = "Pension"
LBL_RE = "Property Equity"
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
if "snapshots" not in st.session_state:
    st.session_state.snapshots = load_snapshots()
if "snapshot_saved_flag" not in st.session_state:
    st.session_state.snapshot_saved_flag = False
MILESTONES = [
    (100_000, "£100K", PURPLE),
    (250_000, "£250K", BLUE),
    (500_000, "£500K", CYAN),
    (1_000_000, "£1M", GREEN),
    (2_000_000, "£2M", AMBER),
    (5_000_000, "£5M", CYAN),
]
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
    "pension_growth_rate": 5.0,
    "property_growth": 3.5,
    "selected_scenario": "Base",
    "bonus_month": "March",
    "rental_income": 0,
    "dividends_income": 0,
    "side_income": 0,
    "expense_housing": 0,
    "expense_utilities": 0,
    "expense_transport": 0,
    "expense_food": 0,
    "expense_dining": 0,
    "expense_shopping": 0,
    "expense_entertainment": 0,
    "expense_subscriptions": 0,
    "expense_discretionary": 0,
    "expense_holidays": 0,
    "expense_other": 0,
}
# Load persisted settings (from Google Sheets or JSON) on first run
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
for key, value in DEFAULT_SETTINGS.items():
    if key not in st.session_state:
        st.session_state[key] = value
# Backwards compat: migrate old monthly_invest to split
if "monthly_invest" in st.session_state and "monthly_invest_cash" not in st.session_state:
    old_val = st.session_state.monthly_invest
    st.session_state.monthly_invest_cash = 500
    st.session_state.monthly_invest_stocks = max(0, old_val - 500)
if "cash_interest_rate" not in st.session_state:
    st.session_state.cash_interest_rate = 4.5
# Migration: if employer_pension_contrib_pct not present, default to 3%
if "employer_pension_contrib_pct" not in st.session_state:
    st.session_state.employer_pension_contrib_pct = 3.0
def _persist_all_settings():
    """Save all current settings to persistent storage."""
    settings = {}
    for k in DEFAULT_SETTINGS:
        if k in st.session_state:
            settings[k] = st.session_state[k]
    if "custom_goals" in st.session_state:
        settings["custom_goals"] = st.session_state.custom_goals
    if "target_alloc" in st.session_state:
        settings["target_alloc"] = st.session_state.target_alloc
    save_settings(settings)
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
    background: {CARD} !important;
    color: {TEXT} !important;
    border-radius: 10px !important;
    border: 1px solid {BORDER_L} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{
    color: {TEXT} !important;
    fill: {TEXT2} !important;
}}
/* Fix selectbox cursor/caret line */
[data-baseweb="select"] input {{
    color: transparent !important;
    text-shadow: 0 0 0 {TEXT} !important;
    caret-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}}
[data-baseweb="select"] [role="combobox"] {{
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}}
[data-baseweb="select"] > div::after,
[data-baseweb="select"] > div::before {{
    display: none !important;
}}
/* Also fix main content selectboxes */
[data-baseweb="select"] > div {{
    background: {CARD} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER_L} !important;
    border-radius: 10px !important;
}}
[data-baseweb="select"] span {{
    color: {TEXT} !important;
}}
[data-baseweb="select"] svg {{
    fill: {TEXT2} !important;
}}
[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] input {{
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}}
/* ── SLIDER STYLING — deep yellow/orange accent ── */
.stSlider > div {{
    padding-top: .15rem;
}}
.stSlider [data-baseweb="slider"] {{
    padding-top: .35rem !important;
    padding-bottom: .2rem !important;
}}
.stSlider [data-baseweb="slider"] > div {{
    height: 10px !important;
}}
.stSlider [data-baseweb="slider"] > div > div {{
    border-radius: 999px !important;
}}
/* Background (unfilled) track */
.stSlider [data-baseweb="slider"] > div > div:first-child {{
    background: rgba(232, 163, 8, 0.15) !important;
}}
/* Active (filled) track — deep yellow/orange gradient */
.stSlider [data-baseweb="slider"] > div > div:nth-child(2) {{
    background: linear-gradient(90deg, {SLIDER_CLR2} 0%, {SLIDER_CLR} 100%) !important;
    opacity: 1 !important;
}}
/* Thumb */
.stSlider [role="slider"] {{
    background: #FFFFFF !important;
    border: 3px solid {DEEP_YELLOW} !important;
    box-shadow: 0 0 0 4px rgba(232,163,8,.22), 0 1px 4px rgba(0,0,0,.3) !important;
}}
/* Slider text colors */
.stSlider label,
.stSlider p,
.stSlider span,
.stSlider small {{
    color: #FFFFFF !important;
    font-weight: 700 !important;
    background: transparent !important;
    text-shadow: none !important;
}}
.stSlider [data-testid="stWidgetLabel"] * {{
    color: #FFFFFF !important;
    font-weight: 700 !important;
}}
/* ── UNIFIED BUTTON STYLING — all buttons share same base ── */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {{
    background: linear-gradient(135deg, {BLUE} 0%, {CYAN} 100%) !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: .86rem !important;
    letter-spacing: .02em !important;
    padding: .6rem 1.2rem !important;
    box-shadow: 0 2px 10px rgba(59,130,246,.3), 0 1px 3px rgba(0,0,0,.2) !important;
    transition: all .2s cubic-bezier(.4,0,.2,1) !important;
    cursor: pointer !important;
}}
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {{
    background: linear-gradient(135deg, #5B9BFF 0%, #22D3EE 100%) !important;
    color: {WHITE} !important;
    box-shadow: 0 6px 20px rgba(59,130,246,.4), 0 2px 6px rgba(0,0,0,.25) !important;
    transform: translateY(-2px) !important;
}}
.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.3) !important;
}}
/* ── Download / secondary buttons — subtler style ── */
.stDownloadButton > button {{
    background: {CARD_H} !important;
    border: 1px solid {BORDER_L} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.25) !important;
}}
.stDownloadButton > button:hover {{
    background: {CARD} !important;
    border-color: {BLUE}88 !important;
    box-shadow: 0 4px 14px rgba(59,130,246,.25) !important;
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
    color: {TEXT2} !important;
    background: transparent !important;
    border: none !important;
    padding: .65rem 1.3rem !important;
    font-size: .82rem !important;
    font-weight: 500;
    letter-spacing: .02em;
    border-radius: 10px 10px 0 0 !important;
    transition: all .2s cubic-bezier(.4,0,.2,1);
    font-family: 'Inter', sans-serif !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {WHITE} !important;
    background: rgba(59,130,246,.08) !important;
}}
.stTabs [aria-selected="true"] {{
    color: {WHITE} !important;
    background: linear-gradient(180deg, rgba(59,130,246,.12) 0%, transparent 100%) !important;
    border-bottom: 2px solid {BLUE} !important;
    font-weight: 700;
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}
/* ── EXPANDER — dark themed ── */
.streamlit-expanderHeader {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    color: {TEXT} !important;
    font-weight: 600 !important;
    font-size: .85rem !important;
    transition: all .2s ease !important;
}}
.streamlit-expanderHeader:hover {{
    border-color: {BORDER_L} !important;
    background: {CARD_H} !important;
}}
.streamlit-expanderContent {{
    border: 1px solid {BORDER} !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    background: {BG_ALT} !important;
}}
details[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    background: {CARD} !important;
}}
details[data-testid="stExpander"] summary {{
    color: {TEXT} !important;
    font-weight: 600 !important;
}}
details[data-testid="stExpander"] > div {{
    background: {BG_ALT} !important;
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
::-webkit-scrollbar-thumb:hover {{
    background: {BORDER_L};
}}
/* ── Global transition for all interactive elements ── */
input, select, textarea, button, [role="slider"], [data-baseweb="select"] > div {{
    transition: all .2s cubic-bezier(.4,0,.2,1) !important;
}}
/* ── Inputs focus glow ── */
section[data-testid="stSidebar"] input:focus {{
    border-color: {BORDER_L} !important;
    box-shadow: 0 0 0 3px rgba(37,50,85,.35) !important;
}}
/* ── Radio buttons / toggles styling ── */
.stRadio [role="radiogroup"] label {{
    color: {TEXT2} !important;
    transition: all .15s ease !important;
}}
.stRadio [role="radiogroup"] label:hover {{
    color: {TEXT} !important;
}}
/* ── Main content input labels — ensure high contrast ── */
.stTextInput label,
.stNumberInput label,
.stSelectbox label {{
    color: {WHITE} !important;
    font-weight: 600 !important;
    font-size: .84rem !important;
}}
.stTextInput input {{
    background: {CARD} !important;
    border: 1px solid {BORDER_L} !important;
    color: {TEXT} !important;
    border-radius: 10px !important;
    font-size: .92rem !important;
}}
.stNumberInput input {{
    background: {CARD} !important;
    border: 1px solid {BORDER_L} !important;
    color: {TEXT} !important;
    border-radius: 10px !important;
}}
div[data-testid="column"] > div {{
    padding: 0 .3rem;
}}
/* Force equal-height KPI cards across columns */
div[data-testid="stHorizontalBlock"] {{
    align-items: stretch;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
    display: flex;
    flex-direction: column;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > div > div > div {{
    flex: 1;
}}
.wealthview-header {{
    display:flex;
    align-items:center;
    gap:.75rem;
    margin: .4rem 0 .35rem 0;
    padding-top: .25rem;
    overflow: visible;
}}
.wv-logo {{
    display:inline-flex;
    align-items:center;
    gap:.55rem;
}}
.wv-logo-icon {{
    width:34px;
    height:34px;
    border-radius:9px;
    background:linear-gradient(135deg,{BLUE},{CYAN});
    display:flex;
    align-items:center;
    justify-content:center;
    box-shadow:0 2px 10px rgba(59,130,246,.25);
    flex-shrink:0;
}}
.wv-logo-icon svg {{
    width:18px;
    height:18px;
}}
.wealthview-title {{
    font-size:1.55rem;
    font-weight:800;
    letter-spacing:-.04em;
    color:{TEXT};
    line-height:1.2;
    display:inline-block;
}}
.wealthview-title span {{
    background:linear-gradient(135deg,{BLUE},{CYAN});
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}}
.wealthview-subtitle {{
    color:{TEXT3};
    font-size:.72rem;
    letter-spacing:.06em;
    text-transform:uppercase;
    margin-left:.2rem;
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
/* ── MOBILE RESPONSIVE ── */
@media (max-width: 768px) {{
    .block-container {{
        padding: .8rem .6rem 1.2rem .6rem !important;
    }}
    .wealthview-header {{
        flex-direction: column;
        gap: .2rem;
    }}
    .wealthview-title {{
        font-size: 1.4rem;
    }}
    .wealthview-subtitle {{
        font-size: .68rem;
    }}
    div[data-testid="column"] > div {{
        padding: 0 .1rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: .5rem .6rem !important;
        font-size: .72rem !important;
    }}
}}
@media (max-width: 480px) {{
    .block-container {{
        padding: .5rem .4rem 1rem .4rem !important;
    }}
    .wealthview-title {{
        font-size: 1.15rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: .4rem .4rem !important;
        font-size: .65rem !important;
    }}
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
def kpi_html(label, value, color=BLUE, icon="", sub="", info=""):
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
        f'box-shadow:{SHADOW_SM};position:relative;overflow:hidden;min-height:230px;">'
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
def render_kpi_card(label, value, color=BLUE, icon="", sub="", info=""):
    st.markdown(
        kpi_html(label, value, color=color, icon=icon, sub=sub, info=info),
        unsafe_allow_html=True,
    )
def kpi_small(label, value, color=TEXT):
    return f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:.75rem .9rem;text-align:center;">
    <div style="color:{TEXT2};font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600;">{label}</div>
    <div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:.2rem;">{value}</div></div>"""
def card_open(title="", subtitle=""):
    sub = f'<span style="color:{TEXT2};font-size:.75rem;font-weight:400;margin-left:.5rem;">{subtitle}</span>' if subtitle else ""
    h = f'<div style="color:{TEXT};font-size:.95rem;font-weight:700;margin-bottom:.75rem;letter-spacing:-.01em;">{title}{sub}</div>' if title else ""
    return f'<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.25rem 1.4rem;box-shadow:{SHADOW};margin-bottom:.75rem;">{h}'
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
def progress_bar_html(pct_val, color_from=BLUE, color_to=CYAN, height=8):
    w = max(0, min(100, pct_val))
    return f'<div style="background:{BORDER};border-radius:{height}px;height:{height}px;width:100%;margin-top:.3rem;overflow:hidden;"><div style="width:{w}%;height:100%;border-radius:{height}px;background:linear-gradient(90deg,{color_from},{color_to});transition:width .6s ease;"></div></div>'
def spacer(h="1rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)
def get_highest_milestone(nw):
    reached = None
    for threshold, label, color in MILESTONES:
        if nw >= threshold:
            reached = (threshold, label, color)
    return reached
def generate_insights(net_worth, cash, investments, crypto, pension_val, real_estate_equity,
                      history_df, target_wealth, years_to_retire, monthly_invest, savings_rate,
                      cash_interest_rate, expected_return, largest_asset_label, largest_asset_pct,
                      goal_progress):
    insights = []
    if net_worth > 0:
        cash_pct = cash / net_worth * 100
        if cash_pct > 40:
            insights.append((CYAN, "◇", f"Cash makes up {cash_pct:.0f}% of your net worth. Consider whether some could be deployed into higher-growth assets."))
        elif cash_pct < 5 and net_worth > 50000:
            insights.append((AMBER, "◇", f"Cash is only {cash_pct:.0f}% of your net worth. Ensure you have an adequate emergency fund (3-6 months expenses)."))
    if not history_df.empty and len(history_df) >= 2:
        latest_change_pct = history_df.iloc[-1].get("nw_change_pct", 0)
        if not pd.isna(latest_change_pct):
            if latest_change_pct > 5:
                insights.append((GREEN, "↗", f"Strong month — net worth grew {latest_change_pct:.1f}% since last snapshot."))
            elif latest_change_pct < -3:
                insights.append((RED, "↘", f"Net worth declined {abs(latest_change_pct):.1f}% since last snapshot. Review your spending or market exposure."))
            else:
                insights.append((TEXT2, "→", f"Net worth changed {latest_change_pct:+.1f}% since last snapshot — steady progress."))
    if largest_asset_pct >= 60:
        insights.append((AMBER, "⚖", f"Concentration risk: {largest_asset_label} is {largest_asset_pct:.0f}% of your wealth. Diversification may reduce volatility."))
    if years_to_retire > 0:
        if goal_progress >= 90:
            insights.append((GREEN, "◎", f"You're {goal_progress:.0f}% of the way to your target — nearly there!"))
        elif goal_progress >= 50:
            insights.append((BLUE, "◎", f"Halfway milestone passed — {goal_progress:.0f}% toward your wealth target."))
        elif goal_progress < 20 and net_worth > 0:
            insights.append((PURPLE, "◎", f"Early days — {goal_progress:.0f}% toward target. Consistent saving is key."))
    if savings_rate > 30:
        insights.append((GREEN, "◉", f"Impressive savings rate of {savings_rate:.0f}%. You're building wealth aggressively."))
    elif savings_rate < 10 and savings_rate > 0:
        insights.append((AMBER, "◉", f"Your savings rate is {savings_rate:.0f}%. Even small increases compound significantly over time."))
    return insights[:5]
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
# FORECAST ENGINE (updated: separate cash vs stock growth)
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
    pension_return=None,
):
    rows = []
    cash_value = starting_cash
    invested_value = starting_invested
    pension_value = starting_pension
    real_estate_value = starting_real_estate_equity
    _pension_return = pension_return if pension_return is not None else stock_return
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
            pension_value *= (1 + _pension_return / 100)
            real_estate_value *= (1 + real_estate_growth / 100)
            cash_value += monthly_invest_cash * 12
            invested_value += monthly_invest_stocks * 12
            pension_value += monthly_pension * 12 + employer_pension_annual
    return pd.DataFrame(rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center;padding:1rem 0 .6rem 0;">
            <div style="display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,{BLUE},{CYAN});box-shadow:0 2px 10px rgba(59,130,246,.25);margin-bottom:.45rem;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 17L9 11L13 15L21 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M17 7H21V11" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div style="font-size:1.4rem;font-weight:800;letter-spacing:-.04em;"><span style="background:linear-gradient(135deg,{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Wealth</span><span style="color:{TEXT};">View</span></div>
            <div style="color:{TEXT2};font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;margin-top:.2rem;">Wealth Management</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    now = datetime.now()
    st.markdown("---")
    st.markdown(sidebar_label("Monthly Snapshot Inputs"), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER_L};border-radius:10px;padding:.55rem .75rem;margin-bottom:.6rem;">'
        f'<span style="color:{TEXT2};font-size:.76rem;">Enter the current value of each asset class for the selected month. '
        f'These values are saved as a monthly snapshot to track your wealth over time.</span></div>',
        unsafe_allow_html=True,
    )
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
    draft_cash = money_text_input("Cash Savings (£)", existing_snapshot.get("cash", 25_000), f"cash_snapshot_{period_key}")
    draft_investments = money_text_input("Stocks & Shares (£)", existing_snapshot.get("investments", 85_000), f"investments_snapshot_{period_key}")
    draft_crypto = money_text_input("Crypto (£)", existing_snapshot.get("crypto", 0), f"crypto_snapshot_{period_key}")
    draft_pension_val = money_text_input("Pension (£)", existing_snapshot.get("pension", 42_000), f"pension_snapshot_{period_key}")
    draft_real_estate_equity = money_text_input("Property Equity (£)", existing_snapshot.get("real_estate_equity", 130_000), f"real_estate_equity_snapshot_{period_key}")
    if st.button("Save Monthly Input", use_container_width=True):
        snapshot_data = {
            "cash": draft_cash,
            "investments": draft_investments,
            "crypto": draft_crypto,
            "pension": draft_pension_val,
            "real_estate_equity": draft_real_estate_equity,
            "net_worth": draft_cash + draft_investments + draft_crypto + draft_pension_val + draft_real_estate_equity,
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
    if GSHEETS_CONNECTED:
        st.markdown(
            f'<div style="color:{GREEN};font-size:.68rem;text-align:center;margin-top:.25rem;display:flex;align-items:center;justify-content:center;gap:.3rem;">'
            f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{GREEN};"></span>'
            f'Google Sheets synced</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="color:{TEXT3};font-size:.68rem;text-align:center;margin-top:.25rem;display:flex;align-items:center;justify-content:center;gap:.3rem;">'
            f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{TEXT3};"></span>'
            f'Local storage only</div>',
            unsafe_allow_html=True,
        )
    warnings = []
    if draft_cash == 0 and draft_investments == 0 and draft_crypto == 0 and draft_pension_val == 0 and draft_real_estate_equity == 0:
        warnings.append("All monthly asset values are currently zero.")
    for label, value in [
        (LBL_CASH, draft_cash),
        (LBL_STOCK, draft_investments),
        (LBL_CRYPTO, draft_crypto),
        (LBL_PENSION, draft_pension_val),
        (LBL_RE, draft_real_estate_equity),
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
    st.markdown(sidebar_label("Forecast Assumptions"), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{CYAN}12;border:1px solid {CYAN}33;border-radius:10px;padding:.55rem .75rem;margin-bottom:.6rem;">'
        f'<span style="color:{TEXT2};font-size:.76rem;">These settings control the salary calculator, cash flow analysis, and wealth forecasts. '
        f'They are independent of the monthly snapshot inputs above. Update and click the button below to apply.</span></div>',
        unsafe_allow_html=True,
    )
    with st.form("forecast_assumptions_form", clear_on_submit=False):
        st.markdown(
            f'<div style="color:{TEXT2};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;">Employment Package</div>',
            unsafe_allow_html=True,
        )
        draft_gross_salary = money_text_input("Gross Salary (£/yr)", st.session_state.gross_salary, "gross_salary_input")
        draft_annual_bonus = money_text_input("Annual Bonus (£)", st.session_state.annual_bonus, "annual_bonus_input")
        draft_bonus_month = st.selectbox("Bonus Paid In", MONTHS,
                                          index=MONTHS.index(st.session_state.bonus_month),
                                          key="bonus_month_input",
                                          help="Month your annual bonus is paid — affects cash flow for that month only")
        draft_rental_income = money_text_input("Rental Income (£/yr)", st.session_state.rental_income, "rental_income_input",
                                                help_text="Annual rental income from buy-to-let or other properties")
        draft_dividends_income = money_text_input("Dividends (£/yr)", st.session_state.dividends_income, "dividends_income_input",
                                                    help_text="Annual dividend income from shares")
        draft_side_income = money_text_input("Side Income (£/yr)", st.session_state.side_income, "side_income_input",
                                              help_text="Freelance, consulting, or other annual side income")
        draft_scotland_tax = st.toggle("Scottish Tax Bands", value=st.session_state.scotland_tax)
        st.markdown(
            f'<div style="color:{TEXT2};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Pension Contributions</div>',
            unsafe_allow_html=True,
        )
        draft_pension_contrib_pct = st.slider("Employee Contribution %", 0.0, 30.0, float(st.session_state.pension_contrib_pct), 0.5)
        draft_employer_pension_contrib_pct = st.slider("Employer Contribution %", 0.0, 30.0, float(st.session_state.employer_pension_contrib_pct), 0.5)
        st.markdown(
            f'<div style="color:{TEXT2};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Monthly Investment Contributions</div>',
            unsafe_allow_html=True,
        )
        draft_monthly_invest_cash = money_text_input("Monthly Cash Savings (£)", st.session_state.monthly_invest_cash, "monthly_invest_cash_input",
                                                      help_text="Amount added to cash savings each month")
        draft_monthly_invest_stocks = money_text_input("Monthly Stock Investment (£)", st.session_state.monthly_invest_stocks, "monthly_invest_stocks_input",
                                                        help_text="Amount invested in stocks and shares each month")
        st.markdown(
            f'<div style="color:{TEXT2};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Growth Rate Assumptions</div>',
            unsafe_allow_html=True,
        )
        draft_cash_interest_rate = st.slider("Cash Interest Rate %", 0.0, 10.0, float(st.session_state.cash_interest_rate), 0.1,
                                              help="Annual interest rate on cash savings (e.g. savings account / cash ISA)")
        draft_expected_return = st.slider("Stocks & Shares Return %", 0.0, 15.0, float(st.session_state.expected_return), 0.5,
                                           help="Annual expected return on stocks and crypto")
        draft_pension_growth_rate = st.slider("Pension Growth Rate %", 0.0, 10.0, float(st.session_state.pension_growth_rate), 0.5,
                                               help="Annual expected return on pension investments (often lower risk than stocks)")
        draft_inflation = st.slider("Inflation %", 0.0, 10.0, float(st.session_state.inflation), 0.1)
        draft_property_growth = st.slider("Property Growth %", 0.0, 10.0, float(st.session_state.property_growth), 0.5)
        st.markdown(
            f'<div style="color:{TEXT2};font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .3rem 0;">Planning & Goals</div>',
            unsafe_allow_html=True,
        )
        draft_current_age = st.number_input("Current Age", 18, 80, int(st.session_state.current_age))
        draft_retirement_age = st.number_input("Retirement Age", 30, 90, int(st.session_state.retirement_age))
        draft_target_wealth = money_text_input("Target Wealth (£)", st.session_state.target_wealth, "target_wealth_input")
        forecast_submit = st.form_submit_button("Save Assumptions", use_container_width=True)
    if forecast_submit:
        st.session_state.gross_salary = draft_gross_salary
        st.session_state.annual_bonus = draft_annual_bonus
        st.session_state.bonus_month = draft_bonus_month
        st.session_state.rental_income = draft_rental_income
        st.session_state.dividends_income = draft_dividends_income
        st.session_state.side_income = draft_side_income
        st.session_state.scotland_tax = draft_scotland_tax
        st.session_state.pension_contrib_pct = draft_pension_contrib_pct
        st.session_state.employer_pension_contrib_pct = draft_employer_pension_contrib_pct
        st.session_state.monthly_invest_cash = draft_monthly_invest_cash
        st.session_state.monthly_invest_stocks = draft_monthly_invest_stocks
        st.session_state.cash_interest_rate = draft_cash_interest_rate
        st.session_state.current_age = draft_current_age
        st.session_state.retirement_age = draft_retirement_age
        st.session_state.target_wealth = draft_target_wealth
        st.session_state.expected_return = draft_expected_return
        st.session_state.pension_growth_rate = draft_pension_growth_rate
        st.session_state.inflation = draft_inflation
        st.session_state.property_growth = draft_property_growth
        _persist_all_settings()
        st.rerun()
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESOLVE ACTIVE SNAPSHOT — only saved data drives calculations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_has_saved_snapshots = bool(st.session_state.snapshots)
if _has_saved_snapshots:
    _latest_snap_key = sorted(st.session_state.snapshots.keys())[-1]
    _active_snap = st.session_state.snapshots[_latest_snap_key]
    cash = _active_snap.get("cash", 0)
    investments = _active_snap.get("investments", 0)
    crypto = _active_snap.get("crypto", 0)
    pension_val = _active_snap.get("pension", 0)
    real_estate_equity = _active_snap.get("real_estate_equity", 0)
else:
    # First-use fallback: use draft sidebar values until the user saves
    cash = draft_cash
    investments = draft_investments
    crypto = draft_crypto
    pension_val = draft_pension_val
    real_estate_equity = draft_real_estate_equity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD HISTORY & CURRENT CALCULATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
history_df = build_history_df(st.session_state.snapshots)
gross_salary = st.session_state.gross_salary
annual_bonus = st.session_state.annual_bonus
rental_income = st.session_state.rental_income
dividends_income = st.session_state.dividends_income
side_income = st.session_state.side_income
additional_income = rental_income + dividends_income + side_income
scotland_tax = st.session_state.scotland_tax
pension_contrib_pct = st.session_state.pension_contrib_pct
employer_pension_contrib_pct = st.session_state.employer_pension_contrib_pct
monthly_invest_cash = st.session_state.monthly_invest_cash
monthly_invest_stocks = st.session_state.monthly_invest_stocks
monthly_invest = monthly_invest_cash + monthly_invest_stocks
monthly_expenses = st.session_state.monthly_expenses
current_age = st.session_state.current_age
retirement_age = st.session_state.retirement_age
target_wealth = st.session_state.target_wealth
cash_interest_rate = st.session_state.cash_interest_rate
expected_return = st.session_state.expected_return
pension_growth_rate = st.session_state.pension_growth_rate
inflation = st.session_state.inflation
property_growth = st.session_state.property_growth
selected_scenario = st.session_state.selected_scenario
bonus_month = st.session_state.bonus_month
total_gross = gross_salary + annual_bonus + additional_income
employee_pension_annual = gross_salary * pension_contrib_pct / 100
employer_pension_annual = gross_salary * employer_pension_contrib_pct / 100
taxable_gross = total_gross - employee_pension_annual
tax = calc_uk_tax(taxable_gross, scotland=scotland_tax)
# Base monthly income excludes bonus — bonus hits only in its month
base_monthly_gross = (gross_salary + additional_income) / 12
base_employee_pension_monthly = employee_pension_annual / 12
base_taxable_gross = gross_salary + additional_income - employee_pension_annual
base_tax = calc_uk_tax(base_taxable_gross, scotland=scotland_tax)
net_monthly_ex_bonus = base_tax["net_monthly"]
# Bonus month gets the full net (including bonus)
net_monthly = tax["net_monthly"]
is_bonus_month = (selected_month == bonus_month)
effective_net_monthly = net_monthly if is_bonus_month and annual_bonus > 0 else net_monthly_ex_bonus if annual_bonus > 0 else net_monthly
monthly_pension_contrib = employee_pension_annual / 12
# Use base monthly (excl bonus) for regular cash flow
cashflow_net = net_monthly_ex_bonus if annual_bonus > 0 else net_monthly
surplus = cashflow_net - monthly_expenses - monthly_invest
savings_rate = (monthly_invest / cashflow_net * 100) if cashflow_net > 0 else 0
net_worth = cash + investments + crypto + pension_val + real_estate_equity
years_to_retire = max(1, retirement_age - current_age)
df_con = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest_cash=monthly_invest_cash,
    monthly_invest_stocks=monthly_invest_stocks,
    monthly_pension=monthly_pension_contrib,
    cash_interest_rate=cash_interest_rate,
    stock_return=max(0, expected_return - 2),
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
    pension_return=pension_growth_rate,
)
df_base = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest_cash=monthly_invest_cash,
    monthly_invest_stocks=monthly_invest_stocks,
    monthly_pension=monthly_pension_contrib,
    cash_interest_rate=cash_interest_rate,
    stock_return=expected_return,
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
    pension_return=pension_growth_rate,
)
df_agg = forecast_wealth(
    starting_cash=cash,
    starting_invested=investments + crypto,
    starting_pension=pension_val,
    starting_real_estate_equity=real_estate_equity,
    monthly_invest_cash=monthly_invest_cash,
    monthly_invest_stocks=monthly_invest_stocks,
    monthly_pension=monthly_pension_contrib,
    cash_interest_rate=cash_interest_rate,
    stock_return=expected_return + 2,
    inflation=inflation,
    real_estate_growth=property_growth,
    years=years_to_retire,
    employer_pension_annual=employer_pension_annual,
    pension_return=pension_growth_rate,
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
# Calculate savings streak (consecutive months of net worth growth)
savings_streak = 0
if not history_df.empty and len(history_df) >= 2:
    for i in range(len(history_df) - 1, 0, -1):
        chg = history_df.iloc[i].get("nw_change", 0)
        if pd.notna(chg) and chg > 0:
            savings_streak += 1
        else:
            break
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f"""
    <div class="wealthview-header">
        <div class="wv-logo">
            <div class="wv-logo-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 17L9 11L13 15L21 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M17 7H21V11" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div class="wealthview-title"><span>Wealth</span>View</div>
            </div>
        </div>
        <span class="wealthview-subtitle">Wealth Management</span>
    </div>
    """,
    unsafe_allow_html=True,
)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SNAPSHOT AUTO-REMINDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.snapshots:
    last_snap_key = sorted(st.session_state.snapshots.keys())[-1]
    try:
        ls_year, ls_month = last_snap_key.split("-")
        last_snap_date = datetime(int(ls_year), int(ls_month), 1)
        days_since = (datetime.now() - last_snap_date).days
        if days_since > 35:
            last_snap_label = f"{MONTHS[int(ls_month)-1]} {ls_year}"
            st.markdown(
                f'<div style="background:linear-gradient(135deg,{AMBER}12 0%,{AMBER}06 100%);'
                f'border:1px solid {AMBER}44;border-radius:12px;padding:.7rem 1rem;margin-bottom:.6rem;'
                f'display:flex;align-items:center;gap:.7rem;">'
                f'<span style="font-size:1.2rem;">📅</span>'
                f'<div><span style="color:{AMBER};font-size:.85rem;font-weight:700;">Time for an update!</span>'
                f'<span style="color:{TEXT2};font-size:.82rem;"> Your last snapshot was for '
                f'<b style="color:{WHITE}">{last_snap_label}</b> ({days_since} days ago). '
                f'Head to the sidebar to save this month\'s data.</span></div></div>',
                unsafe_allow_html=True,
            )
    except (ValueError, IndexError):
        pass
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GETTING STARTED (rewritten for clarity)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.expander("Getting Started — How to Use This Dashboard", expanded=False):
    gs_step = (
        '<div style="display:flex;gap:1rem;align-items:flex-start;padding:.75rem 0;'
        f'border-bottom:1px solid {BORDER};">'
        '<div style="min-width:32px;height:32px;border-radius:8px;'
        'background:{bg};border:1px solid {bd};display:flex;align-items:center;'
        'justify-content:center;font-weight:800;font-size:.85rem;color:{c};flex-shrink:0;">{n}</div>'
        '<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">{title}</div>'
        '<div style="color:{TEXT2};font-size:.8rem;line-height:1.6;margin-top:.15rem;">{desc}</div></div></div>'
    )
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:14px;padding:1.2rem 1.4rem;">
<div style="color:{TEXT};font-size:.95rem;font-weight:600;margin-bottom:.6rem;">Quick Start Guide</div>
<div style="display:flex;gap:1rem;align-items:flex-start;padding:.75rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{BLUE}22;border:1px solid {BLUE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{BLUE};flex-shrink:0;">1</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Save Monthly Snapshots</div>
<div style="color:{TEXT2};font-size:.8rem;line-height:1.6;margin-top:.15rem;">Use the <b style="color:{WHITE}">first sidebar section</b> to enter the current value of each asset (Cash, Stocks, Crypto, Pension, Property) for a specific month. Click <b style="color:{WHITE}">Save Monthly Input</b> to record it.</div></div></div>
<div style="display:flex;gap:1rem;align-items:flex-start;padding:.75rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{CYAN}22;border:1px solid {CYAN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{CYAN};flex-shrink:0;">2</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Set Your Assumptions</div>
<div style="color:{TEXT2};font-size:.8rem;line-height:1.6;margin-top:.15rem;">The <b style="color:{WHITE}">second sidebar section</b> controls salary, investment contributions, growth rates, and goals. These drive forecasts and cash flow — update them only when your circumstances change.</div></div></div>
<div style="display:flex;gap:1rem;align-items:flex-start;padding:.75rem 0;border-bottom:1px solid {BORDER};">
<div style="min-width:32px;height:32px;border-radius:8px;background:{GREEN}22;border:1px solid {GREEN}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{GREEN};flex-shrink:0;">3</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Explore the Tabs</div>
<div style="color:{TEXT2};font-size:.8rem;line-height:1.6;margin-top:.15rem;"><b style="color:{WHITE}">Overview</b> and <b style="color:{WHITE}">History</b> track your progress. <b style="color:{WHITE}">Portfolio</b> shows allocation. <b style="color:{WHITE}">Forecast</b> and <b style="color:{WHITE}">Goals</b> help plan ahead. <b style="color:{WHITE}">Cash Flow</b> and <b style="color:{WHITE}">Salary Calculator</b> handle monthly budgeting.</div></div></div>
<div style="display:flex;gap:1rem;align-items:flex-start;padding:.75rem 0;">
<div style="min-width:32px;height:32px;border-radius:8px;background:{BLUE}22;border:1px solid {BLUE}44;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:{BLUE};flex-shrink:0;">4</div>
<div><div style="color:{TEXT};font-weight:600;font-size:.88rem;">Stay Consistent</div>
<div style="color:{TEXT2};font-size:.8rem;line-height:1.6;margin-top:.15rem;">Save snapshots regularly each month to build a rich wealth history. The more data you record, the more powerful your insights and forecasts become.</div></div></div>
</div>
""",
        unsafe_allow_html=True,
    )
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab_overview, tab_history, tab_portfolio, tab_pension, tab_forecast, tab_goals, tab_assumptions, tab_cashflow, tab_salary = st.tabs(
    ["Overview", "History", "Portfolio", "Pension", "Forecast", "Goals", "Assumptions", "Cash Flow", "Salary Calculator"]
)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_overview:
    # ── Milestone celebration banner ──
    milestone = get_highest_milestone(net_worth)
    if milestone:
        ms_threshold, ms_label, ms_color = milestone
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{ms_color}18 0%,{ms_color}08 100%);'
            f'border:1px solid {ms_color}44;border-radius:14px;padding:.85rem 1.2rem;margin-bottom:.8rem;'
            f'display:flex;align-items:center;gap:.8rem;">'
            f'<span style="font-size:1.6rem;">🏆</span>'
            f'<div><span style="color:{ms_color};font-size:.95rem;font-weight:800;">'
            f'Milestone Reached: {ms_label}</span>'
            f'<div style="color:{TEXT2};font-size:.78rem;margin-top:.1rem;">'
            f'Your net worth has crossed the {ms_label} mark. Keep building!</div></div></div>',
            unsafe_allow_html=True,
        )
    badge_a, badge_b, badge_c, badge_d, badge_e = st.columns(5)
    badge_a.markdown(kpi_small("Reporting Period", period_label, PURPLE), unsafe_allow_html=True)
    badge_b.markdown(kpi_small("Latest Saved", latest_saved_period, TEXT), unsafe_allow_html=True)
    badge_c.markdown(kpi_small("Momentum", momentum_label, momentum_color), unsafe_allow_html=True)
    streak_color = GREEN if savings_streak >= 3 else AMBER if savings_streak >= 1 else TEXT3
    streak_text = f"{savings_streak} month{'s' if savings_streak != 1 else ''}" if savings_streak > 0 else "—"
    badge_d.markdown(kpi_small("Growth Streak 🔥", streak_text, streak_color), unsafe_allow_html=True)
    badge_e.markdown(kpi_small("Snapshots", str(len(st.session_state.snapshots)), CYAN), unsafe_allow_html=True)
    st.markdown(section_header("Financial Net Worth Snapshot", "◈"), unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card(
            "Net Worth",
            gbp(net_worth),
            color=PURPLE,
            icon="◈",
            info="Total tracked wealth across all asset classes for this reporting period.",
        )
    with c2:
        render_kpi_card(
            LBL_CASH,
            gbp(cash),
            color=CYAN,
            icon="◇",
            info=f"Cash held in savings or cash ISAs. Growing at {pct_fmt(cash_interest_rate)} per year.",
        )
    with c3:
        render_kpi_card(
            LBL_STOCK,
            gbp(investments),
            color=BLUE,
            icon="△",
            info=f"Current value of stocks & shares ISA/GIA. Expected return: {pct_fmt(expected_return)} p.a.",
        )
    with c4:
        render_kpi_card(
            LBL_CRYPTO,
            gbp(crypto),
            color=AMBER,
            icon="◌",
            info="Current value of cryptocurrency holdings across all wallets and exchanges.",
        )
    with c5:
        render_kpi_card(
            LBL_PENSION,
            gbp(pension_val),
            color=GREEN,
            icon="◎",
            info="Current value of your workplace and personal pension contributions.",
        )
    spacer(".55rem")
    c6, c7, c8, c9 = st.columns(4)
    with c6:
        render_kpi_card(
            LBL_RE,
            gbp(real_estate_equity),
            color=PURPLE,
            icon="⬡",
            info="Tracked property equity value for the current reporting period.",
        )
    with c7:
        render_kpi_card(
            "Monthly Surplus",
            gbp(surplus),
            color=CYAN if surplus >= 0 else RED,
            icon="↗" if surplus >= 0 else "↘",
            info="Monthly income remaining after expenses and investment contributions.",
        )
    with c8:
        render_kpi_card(
            "Savings Rate",
            pct_fmt(savings_rate),
            color=PURPLE,
            icon="◉",
            info="Monthly investment contributions (cash + stocks) as a percentage of net income.",
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
    # ── Intelligent Alerts & Insights Panel ──
    insight_items = generate_insights(
        net_worth, cash, investments, crypto, pension_val, real_estate_equity,
        history_df, target_wealth, years_to_retire, monthly_invest, savings_rate,
        cash_interest_rate, expected_return, largest_asset_label, largest_asset_pct,
        goal_progress,
    )
    if insight_items:
        spacer("1rem")
        st.markdown(section_header("Smart Insights", "💡"), unsafe_allow_html=True)
        st.markdown(card_open("Auto-Generated Observations"), unsafe_allow_html=True)
        for ins_color, ins_icon, ins_text in insight_items:
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:.65rem;padding:.55rem 0;'
                f'border-bottom:1px solid {BORDER};">'
                f'<span style="color:{ins_color};font-size:1rem;min-width:20px;text-align:center;">{ins_icon}</span>'
                f'<span style="color:{TEXT2};font-size:.84rem;line-height:1.55;">{ins_text}</span></div>',
                unsafe_allow_html=True,
            )
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
            # Dynamic labels: large segments get value+%, medium get value only, small get nothing
            texts = []
            sizes = []
            for v, p in zip(values, percentages):
                if v > 0 and p >= 8:
                    texts.append(f"{gbp(v)}<br>{p:.0f}%")
                    sizes.append(11)
                elif v > 0 and p >= 3:
                    texts.append(gbp(v))
                    sizes.append(10)
                else:
                    texts.append("")
                    sizes.append(9)
            fig.add_trace(go.Bar(
                x=display_df["x_label"],
                y=values,
                name=label,
                marker=dict(color=color),
                text=texts,
                textposition="inside",
                textfont=dict(color=TEXT, size=sizes, family="Inter"),
                insidetextanchor="middle",
                constraintext="inside",
                cliponaxis=False,
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
            "height": 520,
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
        # ── Snapshot Comparison Mode ──
        if len(history_df) >= 2:
            spacer("1rem")
            st.markdown(section_header("Snapshot Comparison", "⇆"), unsafe_allow_html=True)
            period_labels = history_df["label"].tolist()
            period_keys = history_df["period_key"].tolist()
            cmp1, cmp2 = st.columns(2)
            with cmp1:
                cmp_idx_a = st.selectbox("Compare Period A", range(len(period_labels)),
                                          format_func=lambda i: period_labels[i],
                                          index=max(0, len(period_labels) - 2), key="cmp_a")
            with cmp2:
                cmp_idx_b = st.selectbox("Compare Period B", range(len(period_labels)),
                                          format_func=lambda i: period_labels[i],
                                          index=len(period_labels) - 1, key="cmp_b")
            row_a = history_df.iloc[cmp_idx_a]
            row_b = history_df.iloc[cmp_idx_b]
            st.markdown(card_open(f"{row_a['label']}  vs  {row_b['label']}"), unsafe_allow_html=True)
            compare_fields = [
                ("Net Worth", "net_worth", PURPLE),
                (LBL_CASH, "cash", CYAN),
                (LBL_STOCK, "investments", BLUE),
                (LBL_CRYPTO, "crypto", AMBER),
                (LBL_PENSION, "pension", GREEN),
                (LBL_RE, "real_estate_equity", PURPLE),
            ]
            cmp_cols = st.columns(3)
            for i, (cmp_label, cmp_field, cmp_color) in enumerate(compare_fields):
                val_a = row_a.get(cmp_field, 0)
                val_b = row_b.get(cmp_field, 0)
                delta = val_b - val_a
                delta_color = GREEN if delta >= 0 else RED
                delta_icon = "↗" if delta >= 0 else "↘"
                with cmp_cols[i % 3]:
                    st.markdown(
                        f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;'
                        f'padding:.7rem .85rem;margin-bottom:.5rem;">'
                        f'<div style="color:{TEXT3};font-size:.65rem;text-transform:uppercase;'
                        f'letter-spacing:.05em;font-weight:500;">{cmp_label}</div>'
                        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:.3rem;">'
                        f'<span style="color:{TEXT2};font-size:.82rem;">{gbp(val_a)}</span>'
                        f'<span style="color:{TEXT};font-size:.78rem;">→</span>'
                        f'<span style="color:{TEXT};font-size:.88rem;font-weight:700;">{gbp(val_b)}</span></div>'
                        f'<div style="color:{delta_color};font-size:.78rem;font-weight:700;margin-top:.2rem;">'
                        f'{delta_icon} {gbp(delta)}</div></div>',
                        unsafe_allow_html=True,
                    )
            st.markdown(card_close(), unsafe_allow_html=True)
    # ── CSV Import for Historical Snapshots ──
    spacer("1rem")
    st.markdown(section_header("Import Snapshots", "📥"), unsafe_allow_html=True)
    with st.expander("Import from CSV", expanded=False):
        st.markdown(
            f'<div style="color:{TEXT2};font-size:.8rem;margin-bottom:.6rem;line-height:1.6;">'
            f'Upload a CSV file with columns: <b style="color:{WHITE}">year, month, cash, investments, crypto, pension, real_estate_equity</b>. '
            f'Values should be numeric. Existing snapshots for the same period will be updated.</div>',
            unsafe_allow_html=True,
        )
        csv_file = st.file_uploader("Choose CSV file", type=["csv"], key="csv_import")
        if csv_file is not None:
            try:
                csv_df = pd.read_csv(csv_file)
                required_cols = {"year", "month", "cash", "investments"}
                if not required_cols.issubset(set(csv_df.columns)):
                    st.error(f"CSV must contain at least these columns: {', '.join(required_cols)}")
                else:
                    st.markdown(f'<div style="color:{TEXT};font-size:.85rem;font-weight:600;margin:.5rem 0;">Preview ({len(csv_df)} rows):</div>', unsafe_allow_html=True)
                    st.dataframe(csv_df.head(12), use_container_width=True)
                    if st.button("Confirm Import", key="csv_confirm"):
                        imported = 0
                        for _, csv_row in csv_df.iterrows():
                            try:
                                yr = int(csv_row["year"])
                                mo = int(csv_row["month"])
                                pk = f"{yr}-{mo:02d}"
                                snap = {
                                    "cash": int(csv_row.get("cash", 0)),
                                    "investments": int(csv_row.get("investments", 0)),
                                    "crypto": int(csv_row.get("crypto", 0)),
                                    "pension": int(csv_row.get("pension", 0)),
                                    "real_estate_equity": int(csv_row.get("real_estate_equity", 0)),
                                }
                                snap["net_worth"] = sum(snap.values())
                                snap["saved_at"] = datetime.now().isoformat()
                                st.session_state.snapshots[pk] = snap
                                imported += 1
                            except (ValueError, KeyError):
                                continue
                        save_snapshots(st.session_state.snapshots)
                        st.success(f"Imported {imported} snapshots successfully.")
                        st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTFOLIO (now includes Cash Savings)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_portfolio:
    st.markdown(section_header("Portfolio Overview", "△"), unsafe_allow_html=True)
    total_portfolio = cash + investments + crypto + pension_val
    annual_growth_est_cash = cash * cash_interest_rate / 100
    annual_growth_est_stocks = (investments + crypto + pension_val) * expected_return / 100
    annual_growth_est = annual_growth_est_cash + annual_growth_est_stocks
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.markdown(kpi_small("Total Portfolio", gbp(total_portfolio), PURPLE), unsafe_allow_html=True)
    p2.markdown(kpi_small(LBL_CASH, gbp(cash), CYAN), unsafe_allow_html=True)
    p3.markdown(kpi_small(LBL_STOCK, gbp(investments), BLUE), unsafe_allow_html=True)
    p4.markdown(kpi_small(LBL_CRYPTO, gbp(crypto), AMBER), unsafe_allow_html=True)
    p5.markdown(kpi_small(LBL_PENSION, gbp(pension_val), GREEN), unsafe_allow_html=True)
    spacer("1rem")
    left, right = st.columns(2)
    with left:
        st.markdown(card_open("Portfolio Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=[LBL_CASH, LBL_STOCK, LBL_CRYPTO, LBL_PENSION],
            values=[cash, investments, crypto, pension_val],
            hole=0.6,
            marker=dict(colors=[CYAN, BLUE, AMBER, GREEN], line=dict(color=BG, width=2)),
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
        equity_ratio = ((investments + crypto) / total_portfolio * 100) if total_portfolio > 0 else 0
        cash_ratio = (cash / total_portfolio * 100) if total_portfolio > 0 else 0
        if equity_ratio < 35:
            risk_label = "Conservative"
            risk_color = CYAN
        elif equity_ratio < 70:
            risk_label = "Balanced"
            risk_color = GREEN
        else:
            risk_label = "Growth"
            risk_color = PURPLE
        st.markdown(row_item("Estimated Annual Growth", gbp(annual_growth_est), CYAN, True), unsafe_allow_html=True)
        st.markdown(row_item("Risk Profile", risk_label, risk_color, True), unsafe_allow_html=True)
        st.markdown(row_item("Cash Allocation", pct_fmt(cash_ratio), CYAN), unsafe_allow_html=True)
        st.markdown(row_item("Cash Interest Rate", pct_fmt(cash_interest_rate), CYAN), unsafe_allow_html=True)
        st.markdown(row_item("Equity Allocation", pct_fmt(equity_ratio), BLUE), unsafe_allow_html=True)
        st.markdown(row_item("Stock Expected Return", pct_fmt(expected_return), BLUE), unsafe_allow_html=True)
        st.markdown(row_item("Largest Concentration", f"{largest_asset_label} ({largest_asset_pct:.0f}%)", TEXT), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)
    # ── Asset Rebalancing Guide ──
    spacer("1rem")
    st.markdown(section_header("Rebalancing Guide", "⚖"), unsafe_allow_html=True)
    with st.expander("Set Your Target Allocation", expanded=False):
        st.markdown(
            f'<div style="color:{TEXT2};font-size:.8rem;margin-bottom:.5rem;line-height:1.5;">'
            f'Define your ideal portfolio split. The guide below will show how your current allocation '
            f'compares and suggest adjustments. Percentages should total 100%.</div>',
            unsafe_allow_html=True,
        )
        ta = st.session_state.target_alloc
        ta_c1, ta_c2, ta_c3, ta_c4, ta_c5 = st.columns(5)
        with ta_c1:
            t_cash = st.number_input("Cash %", 0, 100, int(ta["cash"]), key="ta_cash")
        with ta_c2:
            t_stocks = st.number_input("Stocks %", 0, 100, int(ta["stocks"]), key="ta_stocks")
        with ta_c3:
            t_crypto = st.number_input("Crypto %", 0, 100, int(ta["crypto"]), key="ta_crypto")
        with ta_c4:
            t_pension = st.number_input("Pension %", 0, 100, int(ta["pension"]), key="ta_pension")
        with ta_c5:
            t_re = st.number_input("Property %", 0, 100, int(ta["real_estate"]), key="ta_re")
        ta_total = t_cash + t_stocks + t_crypto + t_pension + t_re
        if ta_total != 100:
            st.markdown(
                f'<div style="color:{RED};font-size:.82rem;font-weight:600;">Total: {ta_total}% — must equal 100%</div>',
                unsafe_allow_html=True,
            )
        if st.button("Save Target Allocation", key="save_ta"):
            st.session_state.target_alloc = {"cash": t_cash, "stocks": t_stocks, "crypto": t_crypto, "pension": t_pension, "real_estate": t_re}
            _persist_all_settings()
            st.rerun()
    if total_portfolio > 0:
        ta = st.session_state.target_alloc
        alloc_data = [
            (LBL_CASH, cash, ta["cash"], CYAN),
            (LBL_STOCK, investments, ta["stocks"], BLUE),
            (LBL_CRYPTO, crypto, ta["crypto"], AMBER),
            (LBL_PENSION, pension_val, ta["pension"], GREEN),
            (LBL_RE, real_estate_equity, ta["real_estate"], PURPLE),
        ]
        total_all = cash + investments + crypto + pension_val + real_estate_equity
        st.markdown(card_open("Actual vs Target Allocation"), unsafe_allow_html=True)
        for a_label, a_val, a_target_pct, a_color in alloc_data:
            actual_pct = (a_val / total_all * 100) if total_all > 0 else 0
            diff_pct = actual_pct - a_target_pct
            diff_val = total_all * diff_pct / 100
            if abs(diff_pct) < 2:
                status = "On target"
                s_color = GREEN
            elif diff_pct > 0:
                status = f"Overweight by {abs(diff_pct):.1f}%"
                s_color = AMBER
            else:
                status = f"Underweight by {abs(diff_pct):.1f}%"
                s_color = RED
            action = ""
            if abs(diff_pct) >= 2:
                verb = "Reduce" if diff_pct > 0 else "Increase"
                action = f" — {verb} by ~{gbp(abs(diff_val))}"
            st.markdown(
                f'<div style="display:flex;align-items:center;padding:.55rem 0;border-bottom:1px solid {BORDER};gap:.8rem;">'
                f'<div style="width:8px;height:8px;border-radius:50%;background:{a_color};flex-shrink:0;"></div>'
                f'<div style="flex:1;"><span style="color:{TEXT};font-size:.85rem;font-weight:600;">{a_label}</span></div>'
                f'<div style="text-align:right;min-width:60px;"><span style="color:{TEXT2};font-size:.82rem;">{actual_pct:.1f}%</span>'
                f'<span style="color:{TEXT3};font-size:.75rem;"> / {a_target_pct}%</span></div>'
                f'<div style="min-width:180px;text-align:right;"><span style="color:{s_color};font-size:.8rem;font-weight:600;">{status}</span>'
                f'<span style="color:{TEXT3};font-size:.75rem;">{action}</span></div></div>',
                unsafe_allow_html=True,
            )
        st.markdown(card_close(), unsafe_allow_html=True)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PENSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_pension:
    st.markdown(section_header("Pension Planning", "◎"), unsafe_allow_html=True)
    total_pension_annual = employee_pension_annual + employer_pension_annual
    # Project pension to retirement
    _pension_forecast_df = forecast_wealth(
        0, 0, pension_val, 0,
        0, 0, employee_pension_annual / 12,
        cash_interest_rate,
        expected_return,
        inflation,
        0, max(years_to_retire, 1),
        employer_pension_annual,
        pension_return=pension_growth_rate,
    )
    projected_pension = _pension_forecast_df.iloc[-1]["pension"] if len(_pension_forecast_df) > 0 else pension_val
    # ── Section A: Summary KPIs ──
    pa1, pa2, pa3 = st.columns(3)
    pa1.markdown(kpi_html("Current Pension Value", gbp(pension_val), PURPLE, "◎",
                          info="Latest recorded pension balance from your most recent snapshot."), unsafe_allow_html=True)
    pa2.markdown(kpi_html("Projected @ Retirement", gbp(projected_pension), GREEN, "⟩",
                          info=f"Estimated pension value at age {retirement_age}, assuming {pct_fmt(pension_growth_rate)} annual growth and current contributions."), unsafe_allow_html=True)
    pa3.markdown(kpi_html("Years to Retirement", str(years_to_retire), AMBER, "◷",
                          info=f"Age {current_age} now, retiring at {retirement_age}."), unsafe_allow_html=True)
    spacer(".5rem")
    pa4, pa5, pa6 = st.columns(3)
    pa4.markdown(kpi_html("Employee Annual", gbp(employee_pension_annual), BLUE, "↗",
                          info=f"{pct_fmt(pension_contrib_pct)} of {gbp(gross_salary)} gross salary. Reduces your taxable income."), unsafe_allow_html=True)
    pa5.markdown(kpi_html("Employer Annual", gbp(employer_pension_annual), CYAN, "↗",
                          info=f"{pct_fmt(employer_pension_contrib_pct)} employer match. Does not reduce your take-home pay."), unsafe_allow_html=True)
    pa6.markdown(kpi_html("Total Annual", gbp(total_pension_annual), GREEN, "◈",
                          info="Combined employee + employer contributions per year."), unsafe_allow_html=True)
    # ── Section B: Pension Growth Chart (nominal + real) ──
    spacer("1rem")
    st.markdown(section_header("Pension Growth Trajectory"), unsafe_allow_html=True)
    st.markdown(card_open(), unsafe_allow_html=True)
    _infl = inflation / 100
    _pension_real = []
    for _, r in _pension_forecast_df.iterrows():
        yr = int(r["year"])
        real_factor = 1 / ((1 + _infl) ** yr) if yr > 0 else 1
        _pension_real.append(r["pension"] * real_factor)
    _pension_forecast_df = _pension_forecast_df.copy()
    _pension_forecast_df["pension_real"] = _pension_real
    fig_pen = go.Figure()
    fig_pen.add_trace(go.Scatter(
        x=_pension_forecast_df["year"], y=_pension_forecast_df["pension"],
        mode="lines+markers", name="Nominal",
        line=dict(color=PURPLE, width=3),
        marker=dict(size=5, color=PURPLE),
        hovertemplate="Year %{x}<br>Nominal: £%{y:,.0f}<extra></extra>",
    ))
    fig_pen.add_trace(go.Scatter(
        x=_pension_forecast_df["year"], y=_pension_forecast_df["pension_real"],
        mode="lines", name="Real (Inflation-Adjusted)",
        line=dict(color=CYAN, width=2, dash="dot"),
        hovertemplate="Year %{x}<br>Real: £%{y:,.0f}<extra></extra>",
    ))
    fig_pen.update_layout(**make_layout({
        "height": 380,
        "xaxis": {**GRID_AXIS, "title": {"text": "Years from Now", "font": dict(color=TEXT3, size=11)}},
        "yaxis": {**GRID_AXIS, "title": {"text": "Pension Value (£)", "font": dict(color=TEXT3, size=11)}},
        "legend": dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
    }))
    st.plotly_chart(fig_pen, use_container_width=True, config=PLT_CFG)
    st.markdown(card_close(), unsafe_allow_html=True)
    # ── Section C: Contribution Breakdown ──
    spacer("1rem")
    st.markdown(section_header("Contribution Breakdown"), unsafe_allow_html=True)
    _emp_monthly = employee_pension_annual / 12
    _empr_monthly = employer_pension_annual / 12
    _total_monthly = _emp_monthly + _empr_monthly
    _total_pct_of_salary = (total_pension_annual / gross_salary * 100) if gross_salary > 0 else 0
    st.markdown(card_open(), unsafe_allow_html=True)
    cb1, cb2, cb3 = st.columns(3)
    cb1.markdown(kpi_small("Employee Monthly", gbp(_emp_monthly), BLUE), unsafe_allow_html=True)
    cb2.markdown(kpi_small("Employer Monthly", gbp(_empr_monthly), CYAN), unsafe_allow_html=True)
    cb3.markdown(kpi_small("Total Monthly", gbp(_total_monthly), GREEN), unsafe_allow_html=True)
    spacer(".4rem")
    cb4, cb5, cb6, cb7 = st.columns(4)
    cb4.markdown(kpi_small("Employee Annual", gbp(employee_pension_annual), BLUE), unsafe_allow_html=True)
    cb5.markdown(kpi_small("Employer Annual", gbp(employer_pension_annual), CYAN), unsafe_allow_html=True)
    cb6.markdown(kpi_small("Total Annual", gbp(total_pension_annual), GREEN), unsafe_allow_html=True)
    cb7.markdown(kpi_small("% of Salary", pct_fmt(_total_pct_of_salary), AMBER), unsafe_allow_html=True)
    st.markdown(card_close(), unsafe_allow_html=True)
    # ── Section D: Retirement Readiness ──
    spacer("1rem")
    st.markdown(section_header("Retirement Readiness"), unsafe_allow_html=True)
    drawdown_4pct = projected_pension * 0.04
    monthly_retirement_income = drawdown_4pct / 12
    if monthly_retirement_income >= 4000:
        _readiness_msg = "Strong retirement foundation"
        _readiness_clr = GREEN
    elif monthly_retirement_income >= 2000:
        _readiness_msg = "Building well — on track for a comfortable retirement"
        _readiness_clr = BLUE
    elif monthly_retirement_income >= 1000:
        _readiness_msg = "Moderate position — consider increasing contributions"
        _readiness_clr = AMBER
    else:
        _readiness_msg = "May require additional pension saving"
        _readiness_clr = RED
    rd1, rd2, rd3 = st.columns(3)
    rd1.markdown(kpi_html("Projected Pot", gbp(projected_pension), PURPLE,
                          info="Estimated pension value at your retirement age."), unsafe_allow_html=True)
    rd2.markdown(kpi_html("Annual Income (4% Rule)", gbp(drawdown_4pct), GREEN,
                          info="Sustainable annual withdrawal using the 4% safe withdrawal rate."), unsafe_allow_html=True)
    rd3.markdown(kpi_html("Monthly Income", gbp(monthly_retirement_income), CYAN,
                          info="Estimated monthly retirement income from pension alone."), unsafe_allow_html=True)
    spacer(".5rem")
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{_readiness_clr}18,{_readiness_clr}08);'
        f'border:1px solid {_readiness_clr}44;border-radius:12px;padding:1rem 1.25rem;'
        f'display:flex;align-items:center;gap:1rem;">'
        f'<div style="width:10px;height:10px;border-radius:50%;background:{_readiness_clr};flex-shrink:0;"></div>'
        f'<div><div style="font-size:.95rem;font-weight:700;color:{_readiness_clr};">{_readiness_msg}</div>'
        f'<div style="font-size:.8rem;color:{TEXT2};margin-top:.2rem;">Based on projected {gbp(monthly_retirement_income)}/month retirement income from the 4% withdrawal rule</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    spacer(".5rem")
    with st.expander("Pension Assumptions & Details", expanded=False):
        st.markdown(row_item("Employee Contribution Rate", pct_fmt(pension_contrib_pct)), unsafe_allow_html=True)
        st.markdown(row_item("Employer Contribution Rate", pct_fmt(employer_pension_contrib_pct)), unsafe_allow_html=True)
        st.markdown(row_item("Gross Salary (basis)", gbp(gross_salary)), unsafe_allow_html=True)
        st.markdown(row_item("Pension Growth Rate", pct_fmt(pension_growth_rate)), unsafe_allow_html=True)
        st.markdown(row_item("Inflation Assumption", pct_fmt(inflation)), unsafe_allow_html=True)
        st.markdown(row_item("Retirement Age", str(retirement_age)), unsafe_allow_html=True)
        st.markdown(row_item("Years to Retirement", str(years_to_retire)), unsafe_allow_html=True)
        spacer(".3rem")
        st.markdown(
            f'<div style="font-size:.78rem;color:{TEXT3};line-height:1.55;">Projections assume contributions and growth rates remain constant. '
            f'The 4% rule is a widely used guideline for sustainable retirement withdrawals, based on historical market returns. '
            f'Actual results will vary. Real values are adjusted for {pct_fmt(inflation)} annual inflation.</div>',
            unsafe_allow_html=True,
        )
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
        f'<div style="background:{AMBER}12;border:1px solid {AMBER}33;border-radius:12px;padding:.7rem .9rem;margin-bottom:.8rem;"><span style="color:{AMBER};font-size:.84rem;font-weight:700;">Nominal forecast:</span> <span style="color:{TEXT2};font-size:.84rem;">Cash grows at {pct_fmt(cash_interest_rate)}, stocks at {pct_fmt(selected_return)}. Charts show projected growth in money terms, not inflation-adjusted.</span></div>',
        unsafe_allow_html=True,
    )
    milestone_years = sorted(set([y for y in [1, 5, 10, years_to_retire] if y <= years_to_retire]))
    milestone_cols = st.columns(len(milestone_years))
    description = f"Cash: {gbp(monthly_invest_cash)}/mo at {pct_fmt(cash_interest_rate)} · Stocks: {gbp(monthly_invest_stocks)}/mo at {pct_fmt(selected_return)}"
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
    # ── Asset Class Breakdown Chart ──
    spacer("1rem")
    st.markdown(card_open("Forecast by Asset Class", f"{scenario_choice} scenario — how each asset grows over time"), unsafe_allow_html=True)
    _fc_view = st.radio("View", ["Stacked Area", "Individual Lines"], horizontal=True, label_visibility="collapsed", key="fc_view")
    if _fc_view == "Stacked Area":
        fig_ac = go.Figure()
        fig_ac.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["cash"],
            name=LBL_CASH, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=CYAN),
            hovertemplate="Year %{x}<br>Cash: £%{y:,.0f}<extra></extra>",
        ))
        fig_ac.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["invested"],
            name=LBL_STOCK, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=BLUE),
            hovertemplate="Year %{x}<br>Stocks: £%{y:,.0f}<extra></extra>",
        ))
        fig_ac.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["pension"],
            name=LBL_PENSION, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=GREEN),
            hovertemplate="Year %{x}<br>Pension: £%{y:,.0f}<extra></extra>",
        ))
        fig_ac.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["real_estate_equity"],
            name=LBL_RE, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=PURPLE),
            hovertemplate="Year %{x}<br>Property: £%{y:,.0f}<extra></extra>",
        ))
    else:
        fig_ac = go.Figure()
        for col, label, color in [
            ("cash", LBL_CASH, CYAN),
            ("invested", LBL_STOCK, BLUE),
            ("pension", LBL_PENSION, GREEN),
            ("real_estate_equity", LBL_RE, PURPLE),
        ]:
            fig_ac.add_trace(go.Scatter(
                x=selected_df["year"], y=selected_df[col],
                name=label, mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=4, color=color),
                hovertemplate=f"Year %{{x}}<br>{label}: £%{{y:,.0f}}<extra></extra>",
            ))
        fig_ac.add_trace(go.Scatter(
            x=selected_df["year"], y=selected_df["net_worth"],
            name="Total Net Worth", mode="lines",
            line=dict(color=WHITE, width=2, dash="dot"),
            hovertemplate="Year %{x}<br>Total: £%{y:,.0f}<extra></extra>",
        ))
    fig_ac.update_layout(**make_layout({
        "height": 420,
        "legend": dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
        "xaxis": {**GRID_AXIS, "title": {"text": "Years", "font": dict(color=TEXT3, size=11)}},
        "yaxis": {**GRID_AXIS, "title": {"text": "Value (£)", "font": dict(color=TEXT3, size=11)}},
    }))
    st.plotly_chart(fig_ac, use_container_width=True, config=PLT_CFG)
    # ── Asset class milestone table ──
    _fc_milestones = sorted(set([y for y in [1, 5, 10, years_to_retire] if y <= years_to_retire]))
    _fc_table = f'<div style="overflow-x:auto;margin-top:.6rem;"><table style="width:100%;border-collapse:collapse;font-size:.82rem;"><thead><tr style="border-bottom:2px solid {BORDER};">'
    _fc_table += f'<th style="text-align:left;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Year</th>'
    _fc_table += f'<th style="text-align:right;padding:.5rem .6rem;color:{CYAN};font-weight:700;">Cash</th>'
    _fc_table += f'<th style="text-align:right;padding:.5rem .6rem;color:{BLUE};font-weight:700;">Stocks</th>'
    _fc_table += f'<th style="text-align:right;padding:.5rem .6rem;color:{GREEN};font-weight:700;">Pension</th>'
    _fc_table += f'<th style="text-align:right;padding:.5rem .6rem;color:{PURPLE};font-weight:700;">Property</th>'
    _fc_table += f'<th style="text-align:right;padding:.5rem .6rem;color:{TEXT};font-weight:700;">Total</th>'
    _fc_table += '</tr></thead><tbody>'
    for yr in _fc_milestones:
        _row = selected_df.loc[selected_df["year"] == yr]
        if len(_row) > 0:
            _r = _row.iloc[0]
            _fc_table += f'<tr style="border-bottom:1px solid {BORDER};">'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{TEXT};font-weight:600;">Year {yr}</td>'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{CYAN};text-align:right;">{gbp(_r["cash"])}</td>'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{BLUE};text-align:right;">{gbp(_r["invested"])}</td>'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{GREEN};text-align:right;">{gbp(_r["pension"])}</td>'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{PURPLE};text-align:right;">{gbp(_r["real_estate_equity"])}</td>'
            _fc_table += f'<td style="padding:.45rem .6rem;color:{TEXT};text-align:right;font-weight:700;">{gbp(_r["net_worth"])}</td>'
            _fc_table += '</tr>'
    _fc_table += '</tbody></table></div>'
    st.markdown(_fc_table, unsafe_allow_html=True)
    st.markdown(card_close(), unsafe_allow_html=True)
    # ── Growth Attribution ──
    spacer(".5rem")
    _fc_final = selected_df.iloc[-1]
    _fc_start_total = net_worth
    _fc_end_total = _fc_final["net_worth"]
    _fc_total_growth = _fc_end_total - _fc_start_total
    _fc_cash_growth = _fc_final["cash"] - cash
    _fc_invest_growth = _fc_final["invested"] - (investments + crypto)
    _fc_pension_growth = _fc_final["pension"] - pension_val
    _fc_re_growth = _fc_final["real_estate_equity"] - real_estate_equity
    ga1, ga2, ga3, ga4 = st.columns(4)
    ga1.markdown(kpi_small("Cash Growth", gbp(_fc_cash_growth), CYAN), unsafe_allow_html=True)
    ga2.markdown(kpi_small("Investment Growth", gbp(_fc_invest_growth), BLUE), unsafe_allow_html=True)
    ga3.markdown(kpi_small("Pension Growth", gbp(_fc_pension_growth), GREEN), unsafe_allow_html=True)
    ga4.markdown(kpi_small("Property Growth", gbp(_fc_re_growth), PURPLE), unsafe_allow_html=True)
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
        st.markdown(f'<div style="margin-top:.8rem;padding:.7rem .9rem;background:{CARD};border:1px solid {BORDER_L};border-radius:10px;color:{TEXT2};font-size:.82rem;line-height:1.55;">{guidance_text}</div>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)
    # ── What-If Scenario Playground ──
    spacer("1rem")
    st.markdown(section_header("What-If Playground", "🔮"), unsafe_allow_html=True)
    with st.expander("Explore temporary what-if adjustments", expanded=False):
        st.markdown(
            f'<div style="color:{TEXT2};font-size:.8rem;margin-bottom:.6rem;line-height:1.5;">'
            f'Adjust these sliders to see a ghost projection on the chart above. '
            f'These changes are <b style="color:{WHITE}">temporary</b> and do not affect your saved settings.</div>',
            unsafe_allow_html=True,
        )
        wi_c1, wi_c2, wi_c3 = st.columns(3)
        with wi_c1:
            wi_invest_boost = st.slider("Monthly Invest Boost (£)", 0, 5000, 0, 100, key="wi_boost")
        with wi_c2:
            wi_return_adj = st.slider("Return Adjustment (%)", -5.0, 5.0, 0.0, 0.5, key="wi_return")
        with wi_c3:
            wi_extra_years = st.slider("Extra Years", 0, 15, 0, 1, key="wi_years")
        if wi_invest_boost > 0 or wi_return_adj != 0.0 or wi_extra_years > 0:
            wi_total_years = years_to_retire + wi_extra_years
            wi_cash_boost = int(wi_invest_boost * 0.25)
            wi_stock_boost = wi_invest_boost - wi_cash_boost
            df_whatif = forecast_wealth(
                starting_cash=cash,
                starting_invested=investments + crypto,
                starting_pension=pension_val,
                starting_real_estate_equity=real_estate_equity,
                monthly_invest_cash=monthly_invest_cash + wi_cash_boost,
                monthly_invest_stocks=monthly_invest_stocks + wi_stock_boost,
                monthly_pension=monthly_pension_contrib,
                cash_interest_rate=cash_interest_rate,
                stock_return=expected_return + wi_return_adj,
                inflation=inflation,
                real_estate_growth=property_growth,
                years=wi_total_years,
                employer_pension_annual=employer_pension_annual,
                pension_return=pension_growth_rate,
            )
            wi_final = df_whatif.iloc[-1]["net_worth"]
            base_final = selected_df.iloc[-1]["net_worth"]
            wi_diff = wi_final - base_final
            st.markdown(card_open("What-If vs Base Projection"), unsafe_allow_html=True)
            fig_wi = go.Figure()
            fig_wi.add_trace(go.Scatter(
                x=selected_df["year"], y=selected_df["net_worth"],
                name=f"Base ({scenario_choice})",
                line=dict(color=BLUE, width=2.5),
                mode="lines",
                hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>Base</extra>",
            ))
            fig_wi.add_trace(go.Scatter(
                x=df_whatif["year"], y=df_whatif["net_worth"],
                name="What-If",
                line=dict(color=AMBER, width=2.5, dash="dash"),
                mode="lines",
                hovertemplate="Year %{x}<br>£%{y:,.0f}<extra>What-If</extra>",
            ))
            fig_wi.add_hline(y=target_wealth, line_dash="dash", line_color=GREEN, line_width=1.5,
                             annotation_text=f"  Target: {gbp(target_wealth)}",
                             annotation_font=dict(color=GREEN, size=11), annotation_position="top left")
            fig_wi.update_layout(**make_layout({
                "height": 380,
                "legend": dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
                "xaxis": {**GRID_AXIS, "title": {"text": "Years", "font": dict(color=TEXT3, size=11)}},
                "yaxis": {**GRID_AXIS, "title": {"text": "Net Worth (£)", "font": dict(color=TEXT3, size=11)}},
            }))
            st.plotly_chart(fig_wi, use_container_width=True, config=PLT_CFG)
            wi_col1, wi_col2 = st.columns(2)
            wi_col1.markdown(kpi_small("What-If Final Value", gbp(wi_final), AMBER), unsafe_allow_html=True)
            diff_color = GREEN if wi_diff >= 0 else RED
            wi_col2.markdown(kpi_small("Difference vs Base", gbp(wi_diff), diff_color), unsafe_allow_html=True)
            st.markdown(card_close(), unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="color:{TEXT3};font-size:.82rem;text-align:center;padding:1rem 0;">'
                f'Move a slider above to see a what-if projection.</div>',
                unsafe_allow_html=True,
            )
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
            <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{pct_fmt(goal_progress)}</span></div>
            {progress_bar_html(goal_progress, BLUE, CYAN, 10)}
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
    # ── Multiple Named Goals ──
    spacer("1rem")
    st.markdown(section_header("Custom Goals", "🎯"), unsafe_allow_html=True)
    goal_colors = [PURPLE, BLUE, CYAN, GREEN]
    for g_idx, goal in enumerate(st.session_state.custom_goals):
        g_name = goal.get("name", f"Goal {g_idx+1}")
        g_target = goal.get("target", 0)
        g_target_age = goal.get("target_age", retirement_age)
        g_progress = min(100, net_worth / g_target * 100) if g_target > 0 else 0
        g_gap = max(0, g_target - net_worth)
        g_years_left = max(0, g_target_age - current_age)
        g_color = goal_colors[g_idx % len(goal_colors)]
        st.markdown(
            f'{card_open(g_name, f"Target: {gbp(g_target)} by age {g_target_age}")}'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.3rem;">'
            f'<span style="color:{TEXT2};font-size:.8rem;">Progress</span>'
            f'<span style="color:{g_color};font-size:1.1rem;font-weight:800;">{pct_fmt(g_progress)}</span></div>'
            f'{progress_bar_html(g_progress, g_color, CYAN, 8)}'
            f'<div style="display:flex;justify-content:space-between;margin-top:.6rem;">'
            f'<span style="color:{TEXT3};font-size:.76rem;">Gap: {gbp(g_gap)}</span>'
            f'<span style="color:{TEXT3};font-size:.76rem;">{g_years_left} years left</span></div>'
            f'{card_close()}',
            unsafe_allow_html=True,
        )
    # Add/Edit goals form
    with st.expander("Add or Edit Custom Goals", expanded=False):
        st.markdown(
            f'<div style="color:{TEXT2};font-size:.8rem;margin-bottom:.5rem;">Define up to 4 named goals with individual targets and timelines.</div>',
            unsafe_allow_html=True,
        )
        num_goals = st.number_input("Number of goals", 1, 4, len(st.session_state.custom_goals), key="num_goals")
        goal_updates = []
        for gi in range(int(num_goals)):
            existing = st.session_state.custom_goals[gi] if gi < len(st.session_state.custom_goals) else {"name": f"Goal {gi+1}", "target": 500_000, "target_age": 55}
            gc1, gc2, gc3 = st.columns([2, 1.5, 1])
            with gc1:
                g_name_input = st.text_input(f"Goal {gi+1} Name", value=existing["name"], key=f"goal_name_{gi}")
            with gc2:
                g_target_input = money_text_input(f"Target (£)", existing["target"], f"goal_target_{gi}")
            with gc3:
                g_age_input = st.number_input(f"By Age", 25, 90, int(existing.get("target_age", 55)), key=f"goal_age_{gi}")
            goal_updates.append({"name": g_name_input, "target": g_target_input, "target_age": g_age_input})
        if st.button("Save Goals", key="save_goals"):
            st.session_state.custom_goals = goal_updates
            _persist_all_settings()
            st.rerun()
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSUMPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_assumptions:
    region = "Scotland" if scotland_tax else "England / Wales / NI"
    st.markdown(section_header("Model Assumptions", "⚙"), unsafe_allow_html=True)
    st.markdown(card_open("Parameters"), unsafe_allow_html=True)
    for label, value, desc, color in [
        ("Cash Interest Rate", pct_fmt(cash_interest_rate), "Annual interest rate applied to cash savings growth", CYAN),
        ("Stocks & Shares Return", pct_fmt(expected_return), "Annual nominal return used for stocks and crypto growth", BLUE),
        ("Pension Growth Rate", pct_fmt(pension_growth_rate), "Annual expected return on pension investments", GREEN),
        ("Inflation Rate", pct_fmt(inflation), "Used to calculate real purchasing-power values", AMBER),
        ("Property Growth", pct_fmt(property_growth), "Annual growth assumption for property equity", PURPLE),
        ("Employee Pension Contribution", pct_fmt(pension_contrib_pct), "Your personal pension contribution rate", BLUE),
        ("Employer Pension Contribution", pct_fmt(employer_pension_contrib_pct), "Your employer's pension contribution rate", CYAN),
        ("Tax Region", region, "Selected tax jurisdiction", AMBER),
        ("Scenario Spread", "±2.0%", "Conservative and aggressive scenarios adjust the stock return ±2% around the base", TEXT),
        ("Monthly Cash Saving", gbp(monthly_invest_cash), "Amount added to cash savings each month", CYAN),
        ("Monthly Stock Investment", gbp(monthly_invest_stocks), "Amount invested in stocks and shares each month", BLUE),
        ("Rental Income", gbp(rental_income) + "/yr", "Annual rental income from properties", AMBER),
        ("Dividends", gbp(dividends_income) + "/yr", "Annual dividend income from shares", BLUE),
        ("Side Income", gbp(side_income) + "/yr", "Freelance or other annual side income", CYAN),
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
    # ── Budget Planner ──
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.3rem 1.5rem;box-shadow:{SHADOW_SM};margin-bottom:1rem;">
        <div style="color:{TEXT};font-size:1.05rem;font-weight:700;margin-bottom:.25rem;">Plan Your Monthly Budget</div>
        <div style="color:{TEXT2};font-size:.82rem;line-height:1.55;">Set your monthly spending across key categories. This feeds directly into your cash flow and savings projections.</div></div>""",
        unsafe_allow_html=True,
    )
    # ── 🏠 Essentials ──
    st.markdown(
        f'<div style="color:{TEXT};font-size:.9rem;font-weight:700;margin:.6rem 0 .4rem 0;padding-bottom:.3rem;border-bottom:1px solid {BORDER};">'
        f'🏠 Essentials</div>',
        unsafe_allow_html=True,
    )
    _ess_c1, _ess_c2 = st.columns(2)
    with _ess_c1:
        exp_housing = money_text_input("🏡 Housing (£/mo)", st.session_state.expense_housing, "exp_housing")
        exp_food = money_text_input("🛒 Food & Groceries (£/mo)", st.session_state.expense_food, "exp_food")
    with _ess_c2:
        exp_utilities = money_text_input("⚡ Utilities (£/mo)", st.session_state.expense_utilities, "exp_utilities")
        exp_transport = money_text_input("🚗 Transport (£/mo)", st.session_state.expense_transport, "exp_transport")
    # ── 📦 Lifestyle ──
    st.markdown(
        f'<div style="color:{TEXT};font-size:.9rem;font-weight:700;margin:.8rem 0 .4rem 0;padding-bottom:.3rem;border-bottom:1px solid {BORDER};">'
        f'📦 Lifestyle</div>',
        unsafe_allow_html=True,
    )
    _lif_c1, _lif_c2 = st.columns(2)
    with _lif_c1:
        exp_dining = money_text_input("🍽 Dining & Eating Out (£/mo)", st.session_state.expense_dining, "exp_dining")
        exp_entertainment = money_text_input("🎬 Entertainment (£/mo)", st.session_state.expense_entertainment, "exp_entertainment")
    with _lif_c2:
        exp_shopping = money_text_input("🛍 Shopping (£/mo)", st.session_state.expense_shopping, "exp_shopping")
        exp_subs = money_text_input("🧾 Subscriptions (£/mo)", st.session_state.expense_subscriptions, "exp_subs")
    # ── ✈️ Future & Flex ──
    st.markdown(
        f'<div style="color:{TEXT};font-size:.9rem;font-weight:700;margin:.8rem 0 .4rem 0;padding-bottom:.3rem;border-bottom:1px solid {BORDER};">'
        f'✈️ Future & Flex</div>',
        unsafe_allow_html=True,
    )
    _fut_c1, _fut_c2 = st.columns(2)
    with _fut_c1:
        exp_holidays = money_text_input("🌴 Holidays & Travel (£/mo)", st.session_state.expense_holidays, "exp_holidays")
    with _fut_c2:
        exp_other = money_text_input("💸 Misc / Other (£/mo)", st.session_state.expense_other, "exp_other")
    # ── Category totals ──
    _total_essentials = exp_housing + exp_utilities + exp_food + exp_transport
    _total_lifestyle = exp_dining + exp_shopping + exp_entertainment + exp_subs
    _total_future = exp_holidays + exp_other
    category_total = _total_essentials + _total_lifestyle + _total_future
    spacer(".6rem")
    _tc1, _tc2, _tc3, _tc4 = st.columns(4)
    _tc1.markdown(kpi_small("🏠 Essentials", gbp(_total_essentials), CYAN), unsafe_allow_html=True)
    _tc2.markdown(kpi_small("📦 Lifestyle", gbp(_total_lifestyle), AMBER), unsafe_allow_html=True)
    _tc3.markdown(kpi_small("✈️ Future & Flex", gbp(_total_future), BLUE), unsafe_allow_html=True)
    _tc4.markdown(kpi_small("Total Expenses", gbp(category_total), RED if category_total > 0 else TEXT), unsafe_allow_html=True)
    # ── Category % split ──
    if category_total > 0:
        _pct_ess = _total_essentials / category_total * 100
        _pct_lif = _total_lifestyle / category_total * 100
        _pct_fut = _total_future / category_total * 100
        st.markdown(
            f'<div style="display:flex;gap:.5rem;margin:.5rem 0 .3rem 0;height:8px;border-radius:4px;overflow:hidden;">'
            f'<div style="flex:{_pct_ess};background:{CYAN};border-radius:4px;" title="Essentials {_pct_ess:.0f}%"></div>'
            f'<div style="flex:{_pct_lif};background:{AMBER};border-radius:4px;" title="Lifestyle {_pct_lif:.0f}%"></div>'
            f'<div style="flex:{_pct_fut};background:{BLUE};border-radius:4px;" title="Future {_pct_fut:.0f}%"></div></div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:.25rem;">'
            f'<span style="color:{CYAN};font-size:.7rem;font-weight:600;">Essentials {_pct_ess:.0f}%</span>'
            f'<span style="color:{AMBER};font-size:.7rem;font-weight:600;">Lifestyle {_pct_lif:.0f}%</span>'
            f'<span style="color:{BLUE};font-size:.7rem;font-weight:600;">Future {_pct_fut:.0f}%</span></div>',
            unsafe_allow_html=True,
        )
    spacer(".6rem")
    if st.button("Update Monthly Budget", key="apply_expenses", use_container_width=True):
        st.session_state.expense_housing = exp_housing
        st.session_state.expense_utilities = exp_utilities
        st.session_state.expense_transport = exp_transport
        st.session_state.expense_food = exp_food
        st.session_state.expense_dining = exp_dining
        st.session_state.expense_shopping = exp_shopping
        st.session_state.expense_entertainment = exp_entertainment
        st.session_state.expense_subscriptions = exp_subs
        st.session_state.expense_holidays = exp_holidays
        st.session_state.expense_other = exp_other
        st.session_state.expense_discretionary = 0  # migrated into sub-categories
        st.session_state.monthly_expenses = category_total
        _persist_all_settings()
        st.rerun()
    spacer("1rem")
    # ── Cash Flow KPIs ──
    if annual_bonus > 0:
        st.markdown(
            f'<div style="background:{AMBER}12;border:1px solid {AMBER}33;border-radius:10px;padding:.6rem .85rem;margin-bottom:.7rem;">'
            f'<span style="color:{AMBER};font-size:.82rem;font-weight:700;">Bonus of {gbp(annual_bonus)}</span>'
            f'<span style="color:{TEXT2};font-size:.82rem;"> is paid in <b style="color:{WHITE}">{bonus_month}</b> only. '
            f'The cash flow below shows your regular monthly income (excluding bonus).</span></div>',
            unsafe_allow_html=True,
        )
    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_small("Net Monthly Income", gbp(cashflow_net), GREEN), unsafe_allow_html=True)
    c2.markdown(kpi_small("Total Outflows", gbp(monthly_expenses + monthly_invest + monthly_pension_contrib), AMBER), unsafe_allow_html=True)
    c3.markdown(kpi_small("Investment Rate", pct_fmt(savings_rate), CYAN), unsafe_allow_html=True)
    spacer(".8rem")
    left, right = st.columns(2)
    with left:
        st.markdown(card_open("Cash Flow Statement", "Regular month (excl. bonus)" if annual_bonus > 0 else ""), unsafe_allow_html=True)
        cf_rows = [
            ("Gross Monthly Salary", gross_salary / 12, TEXT, False),
        ]
        if additional_income > 0:
            cf_rows.append(("Additional Income", additional_income / 12, TEXT, False))
        cf_rows += [
            ("Tax & NI", -base_tax["total_deductions"] / 12 if annual_bonus > 0 else -tax["total_deductions"] / 12, RED, False),
            ("Pension (employee)", -monthly_pension_contrib, AMBER, False),
            ("Net Monthly Income", cashflow_net, GREEN, True),
        ]
        for label, value, color, bold in cf_rows:
            st.markdown(row_item(label, gbp(value), color, bold), unsafe_allow_html=True)
        st.markdown(f'<div style="height:.25rem;border-bottom:1px dashed {BORDER};margin:.15rem 0;"></div>', unsafe_allow_html=True)
        # Show employer pension as informational (not an outflow)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;border-bottom:1px solid {BORDER}08;">'
            f'<span style="color:{TEXT3};font-size:.8rem;font-style:italic;">Employer pension (not an outflow)</span>'
            f'<span style="color:{CYAN};font-weight:500;font-size:.85rem;">+{gbp(employer_pension_annual / 12)}/mo</span></div>',
            unsafe_allow_html=True,
        )
        for label, value, color, bold in [
            ("Expenses", -monthly_expenses, RED, False),
            ("Monthly Cash Saving", -monthly_invest_cash, CYAN, False),
            ("Monthly Stock Investment", -monthly_invest_stocks, BLUE, False),
            ("Monthly Surplus", surplus, CYAN if surplus >= 0 else RED, True),
        ]:
            st.markdown(row_item(label, gbp(value), color, bold), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(card_open("Monthly Outflow Split"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Expenses", "Cash Saving", "Stock Investment", "Pension", "Surplus"],
            values=[monthly_expenses, monthly_invest_cash, monthly_invest_stocks, monthly_pension_contrib, max(0, surplus)],
            hole=0.58,
            marker=dict(colors=[RED, CYAN, BLUE, GREEN, "#475569"], line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}/mo<extra></extra>",
        ))
        fig.update_layout(**make_layout({"height": 350, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)
    # ── Expense Category Breakdown Chart ──
    exp_cats = {
        "🏡 Housing": st.session_state.expense_housing,
        "⚡ Utilities": st.session_state.expense_utilities,
        "🛒 Groceries": st.session_state.expense_food,
        "🚗 Transport": st.session_state.expense_transport,
        "🍽 Dining": st.session_state.expense_dining,
        "🛍 Shopping": st.session_state.expense_shopping,
        "🎬 Entertainment": st.session_state.expense_entertainment,
        "🧾 Subscriptions": st.session_state.expense_subscriptions,
        "🌴 Holidays": st.session_state.expense_holidays,
        "💸 Other": st.session_state.expense_other,
    }
    active_cats = {k: v for k, v in exp_cats.items() if v > 0}
    if active_cats:
        spacer(".6rem")
        st.markdown(card_open("Expense Category Breakdown"), unsafe_allow_html=True)
        _exp_colors = [CYAN, BLUE, GREEN, AMBER, RED, "#F472B6", "#A78BFA", "#FB923C", "#38BDF8", "#94A3B8"]
        fig_exp = go.Figure(go.Pie(
            labels=list(active_cats.keys()),
            values=list(active_cats.values()),
            hole=0.55,
            marker=dict(colors=_exp_colors[:len(active_cats)],
                        line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}/mo<extra></extra>",
        ))
        fig_exp.update_layout(**make_layout({"height": 340, "showlegend": False}))
        fig_exp.add_annotation(text=f"<b>{gbp(sum(active_cats.values()))}</b>", x=0.5, y=0.54,
                               font=dict(size=16, color=TEXT, family="Inter"), showarrow=False)
        fig_exp.add_annotation(text="MONTHLY", x=0.5, y=0.43,
                               font=dict(size=8, color=TEXT3, family="Inter"), showarrow=False)
        st.plotly_chart(fig_exp, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SALARY CALCULATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_salary:
    st.markdown(
        f"""<div style="display:flex;align-items:baseline;gap:.6rem;margin:1rem 0 .5rem 0;">
        <span style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{BLUE},{CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">UK Salary Calculator</span>
        <span style="color:{TEXT2};font-size:.75rem;">{"Scotland" if scotland_tax else "England / Wales / NI"} · current assumptions</span></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div style="color:{TEXT2};font-size:.8rem;margin-bottom:1rem;">A standalone take-home pay tool based on your current employment package assumptions.</div>', unsafe_allow_html=True)
    # ── Personal Allowance notice ──
    _sal_pa = tax["personal_allowance"]
    if total_gross - employee_pension_annual > 100_000:
        _pa_note = f'Your adjusted net income is over the personal allowance threshold of £100,000. Your allowance has been reduced to £{_sal_pa:,.0f} (from the default £12,570).'
        st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER_L};border-radius:12px;padding:.85rem 1.1rem;margin-bottom:1.2rem;color:{TEXT};font-size:.85rem;line-height:1.6;text-align:center;">{_pa_note}</div>', unsafe_allow_html=True)
    # ── Base salary calc (excl bonus) ──
    _sal_base_gross = gross_salary + additional_income
    _sal_base_pension = employee_pension_annual
    _sal_base_taxable_gross = _sal_base_gross - _sal_base_pension
    _sal_base_tax = calc_uk_tax(_sal_base_taxable_gross, scotland=scotland_tax)
    _sal_base_income_tax = _sal_base_tax["income_tax"]
    _sal_base_ni = _sal_base_tax["ni"]
    _sal_base_net = _sal_base_tax["net_annual"]
    # ── Full salary calc (incl bonus — for bonus month) ──
    _sal_full_gross = total_gross
    _sal_full_pension = employee_pension_annual
    _sal_full_taxable_gross = _sal_full_gross - _sal_full_pension
    _sal_full_tax = calc_uk_tax(_sal_full_taxable_gross, scotland=scotland_tax)
    _sal_full_income_tax = _sal_full_tax["income_tax"]
    _sal_full_ni = _sal_full_tax["ni"]
    _sal_full_net = _sal_full_tax["net_annual"]
    # ── Bonus month incremental ──
    _bonus_month_extra_net = _sal_full_net - _sal_base_net if annual_bonus > 0 else 0
    _sal_base_monthly_net = _sal_base_net / 12
    _sal_bonus_month_net = _sal_base_monthly_net + _bonus_month_extra_net if annual_bonus > 0 else _sal_base_monthly_net
    # ── Build salary breakdown table ──
    def _sal_row(label, yearly, is_bold=False, is_green=False, is_red=False):
        monthly = yearly / 12
        weekly = yearly / 52
        daily = yearly / 260
        fw = "700" if is_bold else "500"
        clr = GREEN if is_green else (RED if is_red else TEXT)
        def _fmt(v, show_sign=False):
            sign = "-" if v < 0 else ""
            return f'{sign}£{abs(v):,.2f}'
        return f'''<tr style="border-bottom:1px solid {BORDER};">
            <td style="padding:.65rem .8rem;color:{clr};font-weight:{fw};font-size:.88rem;">{label}</td>
            <td style="padding:.65rem .8rem;color:{clr};font-weight:{fw};font-size:.88rem;text-align:right;">{_fmt(yearly)}</td>
            <td style="padding:.65rem .8rem;color:{clr};font-weight:{fw};font-size:.88rem;text-align:right;">{_fmt(monthly)}</td>
            <td style="padding:.65rem .8rem;color:{clr};font-weight:{fw};font-size:.88rem;text-align:right;">{_fmt(weekly)}</td>
            <td style="padding:.65rem .8rem;color:{clr};font-weight:{fw};font-size:.88rem;text-align:right;">{_fmt(daily)}</td>
        </tr>'''
    # Use base (excl bonus) for the main breakdown table
    _tbl_gross = _sal_base_gross
    _tbl_pension = _sal_base_pension
    _tbl_taxable = _sal_base_taxable_gross
    _tbl_income_tax = _sal_base_income_tax
    _tbl_ni = _sal_base_ni
    _tbl_net = _sal_base_net
    _sal_table = f'''<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {BORDER};border-radius:16px;padding:1.2rem;box-shadow:{SHADOW};margin-bottom:1rem;">
    <div style="font-size:1rem;font-weight:700;color:{TEXT};margin-bottom:.8rem;">{"Base Salary Breakdown (excl. bonus)" if annual_bonus > 0 else "Salary Breakdown"}</div>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
    <thead><tr style="border-bottom:2px solid {BORDER_L};">
        <th style="text-align:left;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;"></th>
        <th style="text-align:right;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Yearly</th>
        <th style="text-align:right;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Monthly</th>
        <th style="text-align:right;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Weekly</th>
        <th style="text-align:right;padding:.6rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Daily</th>
    </tr></thead>
    <tbody>
    {_sal_row("Gross Income", _tbl_gross, is_bold=True)}
    {_sal_row("Pension Deductions", -_tbl_pension)}
    {_sal_row("Taxable Income", _tbl_taxable, is_bold=True)}
    {_sal_row("Income Tax", -_tbl_income_tax, is_red=True)}
    {_sal_row("National Insurance", -_tbl_ni, is_red=True)}
    {_sal_row("Take Home", _tbl_net, is_bold=True, is_green=True)}
    </tbody></table></div></div>'''
    st.markdown(_sal_table, unsafe_allow_html=True)
    # ── Bonus month breakdown (only if bonus > 0) ──
    if annual_bonus > 0:
        _bonus_extra_tax = _sal_full_income_tax - _sal_base_income_tax
        _bonus_extra_ni = _sal_full_ni - _sal_base_ni
        st.markdown(f'''<div style="background:linear-gradient(135deg,{CARD} 0%,{CARD_H} 100%);border:1px solid {AMBER}44;border-radius:16px;padding:1.2rem;box-shadow:{SHADOW};margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.8rem;">
            <span style="font-size:1rem;font-weight:700;color:{AMBER};">Bonus Month ({bonus_month})</span>
            <span style="background:{AMBER}22;color:{AMBER};font-size:.72rem;font-weight:600;padding:.15rem .5rem;border-radius:6px;">+{gbp(annual_bonus)} bonus</span>
        </div>
        <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="border-bottom:2px solid {BORDER_L};">
            <th style="text-align:left;padding:.55rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;"></th>
            <th style="text-align:right;padding:.55rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Regular Month</th>
            <th style="text-align:right;padding:.55rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Bonus Month ({bonus_month})</th>
            <th style="text-align:right;padding:.55rem .8rem;color:{TEXT2};font-weight:600;font-size:.82rem;">Difference</th>
        </tr></thead>
        <tbody>
        <tr style="border-bottom:1px solid {BORDER};">
            <td style="padding:.55rem .8rem;color:{TEXT};font-weight:600;font-size:.86rem;">Gross Pay</td>
            <td style="padding:.55rem .8rem;color:{TEXT};font-size:.86rem;text-align:right;">£{_sal_base_gross/12:,.2f}</td>
            <td style="padding:.55rem .8rem;color:{TEXT};font-size:.86rem;text-align:right;">£{(_sal_base_gross/12 + annual_bonus):,.2f}</td>
            <td style="padding:.55rem .8rem;color:{AMBER};font-weight:600;font-size:.86rem;text-align:right;">+£{annual_bonus:,.2f}</td>
        </tr>
        <tr style="border-bottom:1px solid {BORDER};">
            <td style="padding:.55rem .8rem;color:{TEXT};font-weight:600;font-size:.86rem;">Additional Tax</td>
            <td style="padding:.55rem .8rem;color:{TEXT2};font-size:.86rem;text-align:right;">—</td>
            <td style="padding:.55rem .8rem;color:{RED};font-size:.86rem;text-align:right;">-£{_bonus_extra_tax:,.2f}</td>
            <td style="padding:.55rem .8rem;color:{RED};font-weight:600;font-size:.86rem;text-align:right;">-£{_bonus_extra_tax:,.2f}</td>
        </tr>
        <tr style="border-bottom:1px solid {BORDER};">
            <td style="padding:.55rem .8rem;color:{TEXT};font-weight:600;font-size:.86rem;">Additional NI</td>
            <td style="padding:.55rem .8rem;color:{TEXT2};font-size:.86rem;text-align:right;">—</td>
            <td style="padding:.55rem .8rem;color:{RED};font-size:.86rem;text-align:right;">-£{_bonus_extra_ni:,.2f}</td>
            <td style="padding:.55rem .8rem;color:{RED};font-weight:600;font-size:.86rem;text-align:right;">-£{_bonus_extra_ni:,.2f}</td>
        </tr>
        <tr style="border-bottom:1px solid {BORDER};">
            <td style="padding:.55rem .8rem;color:{GREEN};font-weight:700;font-size:.88rem;">Take Home</td>
            <td style="padding:.55rem .8rem;color:{GREEN};font-weight:700;font-size:.88rem;text-align:right;">£{_sal_base_monthly_net:,.2f}</td>
            <td style="padding:.55rem .8rem;color:{GREEN};font-weight:700;font-size:.88rem;text-align:right;">£{_sal_bonus_month_net:,.2f}</td>
            <td style="padding:.55rem .8rem;color:{GREEN};font-weight:700;font-size:.88rem;text-align:right;">+£{_bonus_month_extra_net:,.2f}</td>
        </tr>
        </tbody></table></div></div>''', unsafe_allow_html=True)
    spacer("1rem")
    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown(card_open("Tax Composition"), unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Income Tax", "National Insurance", "Pension", "Net Pay"],
            values=[_sal_base_income_tax, _sal_base_ni, _sal_base_pension, _sal_base_net],
            hole=0.58,
            marker=dict(colors=[RED, AMBER, BLUE, GREEN], line=dict(color=BG, width=2)),
            textinfo="label+percent+value",
            texttemplate="<b>%{label}</b><br>£%{value:,.0f}",
            textfont=BOLD_WHITE_SM,
            hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<extra></extra>",
        ))
        fig.update_layout(**make_layout({"height": 320, "showlegend": False}))
        st.plotly_chart(fig, use_container_width=True, config=PLT_CFG)
        st.markdown(card_close(), unsafe_allow_html=True)
    with right:
        st.markdown(card_open("Tax Band Detail"), unsafe_allow_html=True)
        if _sal_base_tax["band_breakdown"]:
            for band in _sal_base_tax["band_breakdown"]:
                st.markdown(
                    row_item(f"{pct_fmt(band['rate'] * 100)} on {gbp(band['band_width'])}", gbp(band["tax"]), RED),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(f'<span style="color:{TEXT2};font-size:.82rem;">No tax bands applicable</span>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)
        # KPI summary cards
        st.markdown(card_open("Quick Summary"), unsafe_allow_html=True)
        for _lbl, _val, _clr in [
            ("Effective Tax Rate", pct_fmt(_sal_base_tax["effective_rate"]), PURPLE),
            ("Personal Allowance", gbp(_sal_pa), TEXT),
            ("Monthly Take Home", f'£{_sal_base_monthly_net:,.2f}', GREEN),
        ]:
            st.markdown(row_item(_lbl, _val, _clr), unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPORT REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spacer("1.5rem")
st.markdown(section_header("Export Report", "📄"), unsafe_allow_html=True)
report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
report_lines = [
    "=" * 55,
    "  WEALTHVIEW — WEALTH SUMMARY REPORT",
    f"  Generated: {report_date}",
    "=" * 55,
    "",
    "NET WORTH SNAPSHOT",
    "-" * 40,
    f"  Net Worth:            {gbp(net_worth)}",
    f"  Cash Savings:         {gbp(cash)}",
    f"  Stocks & Shares:      {gbp(investments)}",
    f"  Crypto:               {gbp(crypto)}",
    f"  Pension:              {gbp(pension_val)}",
    f"  Property Equity:      {gbp(real_estate_equity)}",
    "",
    "INCOME & CASH FLOW",
    "-" * 40,
    f"  Gross Annual Income:  {gbp(total_gross)}",
    f"    Salary:             {gbp(gross_salary)}",
    f"    Bonus:              {gbp(annual_bonus)}",
    f"    Additional Income:  {gbp(additional_income)}",
    f"  Net Monthly Income:   {gbp(net_monthly)}",
    f"  Monthly Expenses:     {gbp(monthly_expenses)}",
    f"  Monthly Investing:    {gbp(monthly_invest)}",
    f"  Monthly Surplus:      {gbp(surplus)}",
    f"  Savings Rate:         {pct_fmt(savings_rate)}",
    "",
    "FORECAST SUMMARY",
    "-" * 40,
    f"  Selected Scenario:    {selected_scenario}",
    f"  Cash Interest Rate:   {pct_fmt(cash_interest_rate)}",
    f"  Stock Return:         {pct_fmt(selected_return)}",
    f"  Pension Growth Rate:  {pct_fmt(pension_growth_rate)}",
    f"  Inflation:            {pct_fmt(inflation)}",
    f"  Years to Retirement:  {years_to_retire}",
    f"  10-Year Forecast:     {gbp(forecast_10_year_value)}",
]
if target_years is not None:
    report_lines.append(f"  Years to Target:      {target_years}")
else:
    report_lines.append(f"  Years to Target:      Not reached in forecast period")
report_lines += [
    "",
    "GOAL PROGRESS",
    "-" * 40,
    f"  Target Wealth:        {gbp(target_wealth)}",
    f"  Current Progress:     {pct_fmt(goal_progress)}",
    f"  Remaining Gap:        {gbp(goal_gap)}",
    "",
]
ms = get_highest_milestone(net_worth)
if ms:
    report_lines.append(f"  Highest Milestone:    {ms[1]}")
report_lines += [
    "",
    "=" * 55,
    "  For illustrative purposes only. Not financial advice.",
    "=" * 55,
]
report_text = "\n".join(report_lines)
st.download_button(
    label="Download Wealth Summary Report",
    data=report_text,
    file_name=f"wealthview_report_{datetime.now().strftime('%Y%m%d')}.txt",
    mime="text/plain",
    use_container_width=True,
)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spacer("2rem")
st.markdown(
    f'<div style="text-align:center;padding:1rem 0;border-top:1px solid {BORDER};"><span style="color:{TEXT3};font-size:.7rem;letter-spacing:.06em;">WEALTHVIEW · WEALTH MANAGEMENT · FOR ILLUSTRATIVE PURPOSES ONLY</span></div>',
    unsafe_allow_html=True,
)
