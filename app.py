import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import re
from functools import lru_cache

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Crossborder Logistics Cost Simulator",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROFESSIONAL CSS STYLING
# ============================================================
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Header styles */
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 4px solid #FF6B35;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 10px;
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2C5F8A;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .metric-card h3 {
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        opacity: 0.9;
        font-weight: 500;
    }
    
    .metric-card h2 {
        font-size: 1.5rem;
        margin: 0;
        font-weight: 700;
    }
    
    /* Savings cards */
    .savings-positive {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    }
    
    .savings-negative {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(235, 51, 73, 0.3);
    }
    
    .savings-neutral {
        background: linear-gradient(135deg, #606c88 0%, #3f4c6b 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid #1976d2;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left: 5px solid #ff9800;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 5px solid #4caf50;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    
    /* Config boxes */
    .broker-limit-box {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease;
    }
    
    .broker-limit-box:hover {
        border-color: #adb5bd;
    }
    
    .desp-limit-box {
        background: #fff8e1;
        border: 2px solid #ffcc80;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .customs-box {
        background: #fce4ec;
        border: 2px solid #f48fb1;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .rule-box {
        background: #ede7f6;
        border: 2px solid #b39ddb;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Volume indicators */
    .volume-warning {
        background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
        border: 2px solid #fbc02d;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #5d4037;
    }
    
    .volume-ok {
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
        border: 2px solid #00acc1;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #006064;
    }
    
    .volume-error {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border: 2px solid #e53935;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #b71c1c;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.85rem !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E3A5F;
        color: white;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Grid header for simulator */
    .sim-header {
        display: grid;
        grid-template-columns: 0.6fr 0.8fr 0.8fr 0.5fr 0.6fr 0.6fr 0.7fr 0.8fr 0.8fr 0.6fr;
        gap: 4px;
        font-weight: 600;
        font-size: 0.75rem;
        padding: 8px 4px;
        background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%);
        border-radius: 8px;
        margin-bottom: 4px;
        text-align: center;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #888;
        padding: 2rem 1rem;
        border-top: 1px solid #e0e0e0;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-header">'
    '🚚 Logistics Cost Simulator - Crossborder + Last Mile'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if "restriction_rules" not in st.session_state:
    st.session_state.restriction_rules = {
        "jt_rec": {"airports": ["rec"], "brokers": ["phx"]},
        "imile_rec": {"airports": ["rec"], "brokers": ["phx"]},
    }

if "partial_carriers" not in st.session_state:
    st.session_state.partial_carriers = {"jt_rec", "imile_rec"}

if "customs_custom" not in st.session_state:
    st.session_state.customs_custom = {}

# ============================================================
# CONSTANTS
# ============================================================
REQUIRED_DATA_COLUMNS = [
    "aeroporto", "broker", "transportadora_atual", "estado",
    "qtd_pacotes_total", "soma_peso_gramas", "media_frete_tms"
]

REQUIRED_BROKER_COLUMNS = ["aeroporto", "broker", "customs_clearance_value_per_package"]

NUMERIC_DATA_COLUMNS = ["qtd_pacotes_total", "soma_peso_gramas", "media_frete_tms"]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def normalize_columns(df):
    """Normalize column names to lowercase with underscores"""
    df.columns = (
        df.columns.str.strip().str.lower()
        .str.replace(" ", "_").str.replace("ç", "c").str.replace("ã", "a")
        .str.replace("é", "e").str.replace("í", "i").str.replace("ó", "o")
        .str.replace("ú", "u").str.replace("â", "a").str.replace("ê", "e")
        .str.replace("ô", "o").str.replace("à", "a")
    )
    return df


def map_columns(df):
    """Map alternative column names to standard names"""
    mapping = {
        "aeroporto": ["aeroporto", "airport", "aero"],
        "broker": ["broker", "despachante"],
        "transportadora_atual": ["transportadora_atual", "transportadora", "carrier", "current_carrier"],
        "estado": ["estado", "uf", "state"],
        "qtd_pacotes_total": ["qtd_pacotes_total", "qtd_pacotes", "pacotes", "packages", "quantity"],
        "soma_peso_gramas": ["soma_peso_gramas", "soma_peso_g", "peso_total", "weight", "total_weight"],
        "media_frete_tms": ["media_frete_tms", "frete_medio", "avg_freight", "freight"],
        "customs_clearance_value_per_package": [
            "customs_clearance_value_per_package", "cc_cpp", "customs_clearance",
            "custo_despacho", "clearance_cost"
        ],
    }
    rename_map = {}
    for standard_col, alternatives in mapping.items():
        for alt in alternatives:
            if alt in df.columns and standard_col not in df.columns:
                rename_map[alt] = standard_col
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def detect_quotation_columns(df):
    """Detect quotation columns (media_cotacao_*)"""
    pattern = re.compile(r'^media_cotacao_')
    return [col for col in df.columns if pattern.match(col)]


def extract_carrier_name(column_name):
    """Extract carrier name from quotation column"""
    return column_name.replace("media_cotacao_", "")


def is_carrier_allowed(carrier_key, airport, broker, rules):
    """Check if carrier is allowed based on restriction rules"""
    carrier_lower = str(carrier_key).strip().lower()
    if carrier_lower not in rules:
        return True
    rule = rules[carrier_lower]
    airport_lower = str(airport).strip().lower()
    broker_lower = str(broker).strip().lower()
    return airport_lower in rule.get("airports", []) and broker_lower in rule.get("brokers", [])


def get_customs_clearance(airport, broker, cc_df, default=0):
    """Get customs clearance cost from broker dataframe"""
    if cc_df is None or cc_df.empty:
        return default
    
    airport_str = str(airport).strip().lower()
    broker_str = str(broker).strip().lower()
    
    mask = (
        cc_df["aeroporto"].str.strip().str.lower() == airport_str
    ) & (
        cc_df["broker"].str.strip().str.lower() == broker_str
    )
    
    result = cc_df.loc[mask, "customs_clearance_value_per_package"]
    if not result.empty:
        return float(result.values[0])
    return default


def get_cc_for_simulation(airport, broker, cc_df, customs_custom):
    """Get CC for simulation - uses custom value if available, otherwise real value"""
    key = (str(broker).strip(), str(airport).strip())
    if customs_custom and key in customs_custom:
        return float(customs_custom[key])
    return get_customs_clearance(airport, broker, cc_df)


def calculate_anjun_discount(carrier, broker, discount_value, apply_discount):
    """Calculate Anjun discount when both carrier and broker are Anjun"""
    if not apply_discount:
        return 0
    carrier_lower = str(carrier).strip().lower()
    broker_lower = str(broker).strip().lower()
    if "anjun" in carrier_lower and "anjun" in broker_lower:
        return discount_value
    return 0


def calculate_share(df, carrier_col="transportadora_atual", qty_col="qtd_pacotes_total"):
    """Calculate market share by carrier"""
    total = df[qty_col].sum()
    if total == 0:
        return pd.DataFrame()
    share = df.groupby(carrier_col)[qty_col].sum().reset_index()
    share.columns = ["Carrier", "Packages"]
    share["Share (%)"] = (share["Packages"] / total * 100).round(2)
    return share.sort_values("Share (%)", ascending=False)


def generate_excel(dataframes_dict):
    """Generate Excel file with multiple sheets"""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buffer.getvalue()


def fmt_brl(value):
    """Format value as Brazilian Real with 2 decimal places"""
    return f"R$ {value:,.2f}"


def metric_card(title, value, icon="📊"):
    """Generate HTML for metric card"""
    return f'<div class="metric-card"><h3>{icon} {title}</h3><h2>{value}</h2></div>'


def savings_card(title, value, percentage=None):
    """Generate HTML for savings card with appropriate styling"""
    css_class = "savings-positive" if value >= 0 else "savings-negative"
    pct_text = f"<p style='margin:0;opacity:0.9;'>{percentage:.1f}%</p>" if percentage is not None else ""
    return f'<div class="{css_class}"><h3 style="margin:0 0 0.3rem 0;font-size:0.85rem;">💰 {title}</h3><h2 style="margin:0;font-size:1.5rem;">{fmt_brl(value)}</h2>{pct_text}</div>'


# ============================================================
# COST CALCULATION FUNCTIONS (CORRECTED)
# ============================================================
def calculate_real_cost_unit(row, cc_df, anjun_discount, apply_anjun_discount):
    """
    Calculate REAL unit cost using TMS freight + CC from broker sheet
    This is the baseline/current cost
    """
    carrier = str(row.get("transportadora_atual", "")).strip()
    broker = str(row.get("broker", "")).strip()
    airport = str(row.get("aeroporto", "")).strip()
    
    freight_unit = float(row["media_frete_tms"])
    cc_unit = get_customs_clearance(airport, broker, cc_df)
    
    # Apply Anjun discount
    discount = calculate_anjun_discount(carrier, broker, anjun_discount, apply_anjun_discount)
    cc_unit = max(0, cc_unit - discount)
    
    return freight_unit, cc_unit, freight_unit + cc_unit


def calculate_simulated_cost_unit(carrier_key, airport, broker, quotation_value, 
                                   cc_df, customs_custom, anjun_discount, apply_anjun_discount):
    """
    Calculate SIMULATED unit cost using quotation + custom CC (or real CC if no custom)
    This is used for optimization and simulation
    """
    # Get CC - custom if available, otherwise real
    cc_unit = get_cc_for_simulation(airport, broker, cc_df, customs_custom)
    
    # Apply Anjun discount
    discount = calculate_anjun_discount(carrier_key, broker, anjun_discount, apply_anjun_discount)
    cc_unit = max(0, cc_unit - discount)
    
    return quotation_value, cc_unit, quotation_value + cc_unit


def find_best_option(row, quotation_columns, cc_df, customs_custom, 
                     anjun_discount, apply_anjun_discount, rules):
    """
    Find the best cost option comparing current vs all available quotations
    Returns: (best_carrier, best_freight, best_cc, best_cost_unit, source)
    """
    carrier_current = str(row.get("transportadora_atual", "")).strip()
    broker = str(row.get("broker", "")).strip()
    airport = str(row.get("aeroporto", "")).strip()
    
    # Calculate current real cost
    freight_curr, cc_curr, cost_curr = calculate_real_cost_unit(
        row, cc_df, anjun_discount, apply_anjun_discount
    )
    
    best_carrier = carrier_current
    best_freight = freight_curr
    best_cc = cc_curr
    best_cost = cost_curr
    best_source = "TMS"
    
    # Check all quotations
    for col in quotation_columns:
        carrier_key = extract_carrier_name(col)
        
        # Check restrictions
        if not is_carrier_allowed(carrier_key, airport, broker, rules):
            continue
        
        # Check if quotation exists and is valid
        if col not in row.index or pd.isna(row[col]) or row[col] <= 0:
            continue
        
        quotation_value = float(row[col])
        
        # Calculate simulated cost
        freight_sim, cc_sim, cost_sim = calculate_simulated_cost_unit(
            carrier_key, airport, broker, quotation_value,
            cc_df, customs_custom, anjun_discount, apply_anjun_discount
        )
        
        if cost_sim < best_cost:
            best_cost = cost_sim
            best_carrier = carrier_key.capitalize()
            best_freight = freight_sim
            best_cc = cc_sim
            best_source = "QUOTATION"
    
    return best_carrier, best_freight, best_cc, best_cost, best_source


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 📁 Data Upload")
    uploaded_file = st.file_uploader(
        "Upload Excel file (sheets: 'dados' and 'broker')",
        type=["xlsx", "xls"]
    )
    
    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    
    anjun_discount = st.number_input(
        "Anjun Discount (R$/pkg)",
        value=0.40,
        step=0.05,
        format="%.2f",
        help="Discount applied when both carrier AND broker are Anjun"
    )
    
    apply_anjun_discount = st.checkbox(
        "Apply Anjun Discount",
        value=True,
        help="When enabled, discount is applied when carrier and broker are both Anjun"
    )
    
    st.markdown("---")
    st.markdown("### 📋 Expected Layout")
    st.markdown("""
    **Sheet 'dados':**
    | Column | Description |
    |--------|-------------|
    | aeroporto | Origin airport |
    | broker | Customs broker |
    | transportadora_atual | Current carrier |
    | estado | State/UF |
    | qtd_pacotes_total | Package quantity |
    | soma_peso_gramas | Total weight (g) |
    | media_frete_tms | Avg freight/pkg |
    | media_cotacao_* | Carrier quotations |
    
    **Sheet 'broker':**
    | Column | Description |
    |--------|-------------|
    | aeroporto | Airport |
    | broker | Broker name |
    | customs_clearance_value_per_package | CC cost/pkg |
    """)

# ============================================================
# NO FILE UPLOADED
# ============================================================
if uploaded_file is None:
    st.info("👈 Upload your data file in the sidebar to begin.")
    
    # Create template
    template_dados = pd.DataFrame({
        "aeroporto": ["GRU", "GRU", "CWB", "REC", "REC"],
        "broker": ["Anjun", "Broker_X", "Anjun", "PHX", "PHX"],
        "transportadora_atual": ["Anjun", "iMile", "JT", "JT", "iMile"],
        "estado": ["SP", "RJ", "PR", "PE", "CE"],
        "qtd_pacotes_total": [1000, 500, 300, 800, 600],
        "soma_peso_gramas": [500000, 250000, 150000, 400000, 300000],
        "media_frete_tms": [5.0, 6.0, 7.0, 6.0, 6.0],
        "media_cotacao_imile": [5.2, 5.8, 7.1, 6.2, 5.9],
        "media_cotacao_jt": [5.5, 6.1, 6.8, 6.5, 6.3],
        "media_cotacao_anjun": [4.8, 5.5, 7.3, 5.8, 6.1],
    })
    
    template_broker = pd.DataFrame({
        "aeroporto": ["GRU", "GRU", "CWB", "REC"],
        "broker": ["Anjun", "Broker_X", "Anjun", "PHX"],
        "customs_clearance_value_per_package": [2.50, 2.50, 2.50, 1.80],
    })
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        template_dados.to_excel(writer, index=False, sheet_name="dados")
        template_broker.to_excel(writer, index=False, sheet_name="broker")
    
    st.download_button(
        "📥 Download Excel Template",
        data=buffer.getvalue(),
        file_name="template_logistics_simulator.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.stop()

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data(file):
    """Load and process data from uploaded file"""
    try:
        excel_file = pd.ExcelFile(file)
        
        dados_sheet = None
        broker_sheet = None
        
        for sheet in excel_file.sheet_names:
            if sheet.lower() == "dados":
                dados_sheet = sheet
            elif sheet.lower() == "broker":
                broker_sheet = sheet
        
        if dados_sheet is None or broker_sheet is None:
            return None, None, "Missing required sheets"
        
        df_dados = pd.read_excel(file, sheet_name=dados_sheet)
        df_broker = pd.read_excel(file, sheet_name=broker_sheet)
        
        df_dados = map_columns(normalize_columns(df_dados))
        df_broker = map_columns(normalize_columns(df_broker))
        
        return df_dados, df_broker, None
    except Exception as e:
        return None, None, str(e)

df_dados, df_broker, error = load_data(uploaded_file)

if error:
    st.error(f"Error loading file: {error}")
    st.stop()

# Validate columns
missing_dados = [c for c in REQUIRED_DATA_COLUMNS if c not in df_dados.columns]
if missing_dados:
    st.error(f"❌ Missing columns in 'dados' sheet: **{', '.join(missing_dados)}**")
    st.stop()

missing_broker = [c for c in REQUIRED_BROKER_COLUMNS if c not in df_broker.columns]
if missing_broker:
    st.error(f"❌ Missing columns in 'broker' sheet: **{', '.join(missing_broker)}**")
    st.stop()

# Convert numeric columns
for col in NUMERIC_DATA_COLUMNS:
    if col in df_dados.columns:
        df_dados[col] = pd.to_numeric(df_dados[col], errors="coerce").fillna(0)

df_broker["customs_clearance_value_per_package"] = pd.to_numeric(
    df_broker["customs_clearance_value_per_package"], errors="coerce"
).fillna(0)

# Detect quotation columns
quotation_columns = detect_quotation_columns(df_dados)
for col in quotation_columns:
    df_dados[col] = pd.to_numeric(df_dados[col], errors="coerce").fillna(0)

if not quotation_columns:
    st.warning("⚠️ No quotation columns (media_cotacao_*) found. Optimization features limited.")

# ============================================================
# CUSTOMS CLEARANCE CONFIGURATION
# ============================================================
st.markdown('<div class="sub-header">🛃 Customs Clearance Configuration</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="info-box">'
    '<strong>⚠️ Important:</strong> Custom CC values affect <strong>ONLY simulations and optimizations</strong>.<br>'
    'The <strong>current/real cost</strong> always uses the original values from the broker sheet.<br><br>'
    '<strong>Summary:</strong><br>'
    '• 📊 <strong>Overview</strong> → Real CC from broker sheet<br>'
    '• 🏆 <strong>Optimization</strong> → Current=Real CC | Optimized=Custom CC<br>'
    '• 🔄 <strong>Simulator</strong> → Current=Real CC | Simulated=Custom CC<br>'
    '• 🎯 <strong>Limits</strong> → Reference=Real CC | Allocated=Custom CC'
    '</div>',
    unsafe_allow_html=True
)

# Get unique broker/airport pairs
broker_airport_pairs = df_dados.groupby(["broker", "aeroporto"]).agg(
    packages=("qtd_pacotes_total", "sum")
).reset_index()

broker_airport_pairs = broker_airport_pairs.merge(
    df_broker[["broker", "aeroporto", "customs_clearance_value_per_package"]],
    on=["broker", "aeroporto"],
    how="left"
)
broker_airport_pairs["customs_clearance_value_per_package"] = broker_airport_pairs[
    "customs_clearance_value_per_package"
].fillna(0)

use_custom_cc = st.checkbox(
    "✏️ Customize customs clearance costs (affects only simulations)",
    value=len(st.session_state.customs_custom) > 0,
    key="cb_custom_cc"
)

customs_custom = {}

if use_custom_cc:
    st.markdown("#### Edit Simulation CC Values:")
    
    n_pairs = len(broker_airport_pairs)
    n_cols = min(n_pairs, 4)
    cols_cc = st.columns(n_cols)
    
    for i, (idx, row) in enumerate(broker_airport_pairs.iterrows()):
        ci = i % n_cols
        with cols_cc[ci]:
            broker_name = row["broker"]
            airport_name = row["aeroporto"]
            packages = row["packages"]
            cc_original = row["customs_clearance_value_per_package"]
            
            key = (broker_name, airport_name)
            cc_default = st.session_state.customs_custom.get(key, cc_original)
            
            st.markdown(
                f'<div class="customs-box">'
                f'<strong>📝 {broker_name}</strong> | <strong>✈️ {airport_name}</strong><br>'
                f'<small>Vol: {packages:,.0f} | Original: R$ {cc_original:.4f}</small>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            new_cost = st.number_input(
                f"CC ({broker_name}|{airport_name})",
                value=float(cc_default),
                step=0.05,
                format="%.4f",
                key=f"cc_{broker_name}_{airport_name}",
                label_visibility="collapsed"
            )
            customs_custom[key] = new_cost
    
    st.session_state.customs_custom = customs_custom
else:
    customs_custom = {}
    st.session_state.customs_custom = {}

st.markdown("---")

# ============================================================
# RESTRICTION RULES EDITOR
# ============================================================
with st.expander("🚨 Carrier Restriction Rules", expanded=False):
    st.markdown(
        '<div class="info-box">'
        'Configure carriers with geographic/broker restrictions. '
        'Restricted carriers can only be used when specific conditions are met.'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Display current rules
    if st.session_state.restriction_rules:
        st.markdown("#### Current Rules")
        rules_data = []
        for carrier, rule in st.session_state.restriction_rules.items():
            rules_data.append({
                "Carrier": carrier,
                "Airports": ", ".join(rule.get("airports", [])),
                "Brokers": ", ".join(rule.get("brokers", []))
            })
        st.dataframe(pd.DataFrame(rules_data), use_container_width=True, hide_index=True)
    
    st.markdown("#### Add/Modify Rule")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        new_carrier = st.text_input("Carrier (lowercase)", placeholder="e.g., jt_rec")
    with col_r2:
        new_airports = st.text_input("Allowed Airports", placeholder="e.g., rec, gru")
    with col_r3:
        new_brokers = st.text_input("Allowed Brokers", placeholder="e.g., phx, anjun")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Add/Update Rule"):
            if new_carrier.strip():
                st.session_state.restriction_rules[new_carrier.strip().lower()] = {
                    "airports": [a.strip().lower() for a in new_airports.split(",") if a.strip()],
                    "brokers": [b.strip().lower() for b in new_brokers.split(",") if b.strip()]
                }
                st.success(f"✅ Rule for '{new_carrier}' saved!")
                st.rerun()
    
    with col_btn2:
        rule_to_delete = st.selectbox(
            "Select rule to delete",
            [""] + list(st.session_state.restriction_rules.keys())
        )
        if st.button("🗑️ Delete Rule"):
            if rule_to_delete in st.session_state.restriction_rules:
                del st.session_state.restriction_rules[rule_to_delete]
                st.success(f"✅ Rule deleted!")
                st.rerun()

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview", "🏆 Optimization", "🔄 Simulator",
    "🎯 Limits", "🗺️ Strategy", "📈 State Detail", "📋 Data"
])

# ============================================================
# TAB 1 — OVERVIEW (REAL COST)
# ============================================================
with tab1:
    st.markdown('<div class="sub-header">📊 Current Overview (Real TMS Cost)</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        'All values use <strong>real CC from the broker sheet</strong>. Custom CC does NOT affect this tab.'
        '</div>',
        unsafe_allow_html=True
    )
    
    total_packages = df_dados["qtd_pacotes_total"].sum()
    total_weight = df_dados["soma_peso_gramas"].sum()
    
    # Calculate total costs
    total_freight = 0
    total_cc = 0
    for _, row in df_dados.iterrows():
        f_unit, cc_unit, _ = calculate_real_cost_unit(row, df_broker, anjun_discount, apply_anjun_discount)
        qty = row["qtd_pacotes_total"]
        total_freight += f_unit * qty
        total_cc += cc_unit * qty
    
    total_cost = total_freight + total_cc
    avg_cost = total_cost / total_packages if total_packages > 0 else 0
    
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        st.markdown(metric_card("Total Packages", f"{total_packages:,.0f}", "📦"), unsafe_allow_html=True)
    with r1c2:
        st.markdown(metric_card("Total Freight", fmt_brl(total_freight), "💰"), unsafe_allow_html=True)
    with r1c3:
        st.markdown(metric_card("Total Cost (F+CC)", fmt_brl(total_cost), "💎"), unsafe_allow_html=True)
    with r1c4:
        st.markdown(metric_card("Avg Cost/Pkg", fmt_brl(avg_cost), "📊"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        st.markdown(metric_card("Total Weight", f"{total_weight / 1000:,.1f} kg", "⚖️"), unsafe_allow_html=True)
    with r2c2:
        st.markdown(metric_card("States", f"{df_dados['estado'].nunique()}", "🗺️"), unsafe_allow_html=True)
    with r2c3:
        st.markdown(metric_card("Carriers", f"{df_dados['transportadora_atual'].nunique()}", "🚚"), unsafe_allow_html=True)
    with r2c4:
        st.markdown(metric_card("Brokers", f"{df_dados['broker'].nunique()}", "📝"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 🚚 Share by Carrier")
        share = calculate_share(df_dados)
        if not share.empty:
            fig1 = px.pie(share, values="Packages", names="Carrier",
                          color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            fig1.update_layout(height=380, margin=dict(t=30, b=30))
            st.plotly_chart(fig1, use_container_width=True, key="t1_share")
    
    with col_b:
        st.markdown("#### 💰 Cost by Carrier")
        carrier_costs = []
        for carrier in df_dados["transportadora_atual"].unique():
            df_carrier = df_dados[df_dados["transportadora_atual"] == carrier]
            total_f = 0
            total_p = 0
            for _, row in df_carrier.iterrows():
                f_unit, cc_unit, _ = calculate_real_cost_unit(row, df_broker, anjun_discount, apply_anjun_discount)
                qty = row["qtd_pacotes_total"]
                total_f += (f_unit + cc_unit) * qty
                total_p += qty
            carrier_costs.append({"Carrier": carrier, "Cost": total_f, "Packages": total_p})
        
        df_carrier_costs = pd.DataFrame(carrier_costs).sort_values("Cost", ascending=True)
        fig2 = px.bar(df_carrier_costs, x="Cost", y="Carrier", orientation="h",
                      text=df_carrier_costs["Cost"].apply(lambda x: f"R$ {x:,.0f}"),
                      color="Carrier", color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=380, margin=dict(t=30, b=30), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, key="t1_cost")
    
    # Volume by state
    st.markdown("#### 🗺️ Volume by State")
    vol_state = df_dados.groupby("estado")["qtd_pacotes_total"].sum().reset_index()
    vol_state = vol_state.sort_values("qtd_pacotes_total", ascending=False)
    fig3 = px.bar(vol_state, x="estado", y="qtd_pacotes_total",
                  text=vol_state["qtd_pacotes_total"].apply(lambda x: f"{x:,.0f}"),
                  color="qtd_pacotes_total", color_continuous_scale="Blues")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False,
                       xaxis_title="State", yaxis_title="Packages")
    st.plotly_chart(fig3, use_container_width=True, key="t1_vol_state")

# ============================================================
# TAB 2 — OPTIMIZATION
# ============================================================
with tab2:
    st.markdown('<div class="sub-header">🏆 Optimization: Real vs Quotations</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        f'<strong>Current Cost:</strong> TMS freight + CC from broker sheet (REAL)<br>'
        f'<strong>Optimized Cost:</strong> Best quotation + custom CC (or real if not set)<br>'
        f'<strong>Anjun Discount:</strong> R$ {anjun_discount:.2f}/pkg '
        f'({"enabled" if apply_anjun_discount else "disabled"})'
        '</div>',
        unsafe_allow_html=True
    )
    
    if not quotation_columns:
        st.warning("⚠️ No quotation columns found. Cannot perform optimization.")
    else:
        results = []
        for _, row in df_dados.iterrows():
            qty = row["qtd_pacotes_total"]
            
            # Current real cost
            f_curr, cc_curr, cost_curr_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            cost_curr_total = cost_curr_unit * qty
            
            # Best option
            best_carrier, best_freight, best_cc, best_cost_unit, source = find_best_option(
                row, quotation_columns, df_broker, customs_custom,
                anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
            )
            cost_opt_total = best_cost_unit * qty
            
            results.append({
                "state": row["estado"],
                "airport": row["aeroporto"],
                "broker": row["broker"],
                "current_carrier": row["transportadora_atual"],
                "freight_tms": round(f_curr, 4),
                "cc_real": round(cc_curr, 4),
                "cost_unit_current": round(cost_curr_unit, 4),
                "cost_total_current": round(cost_curr_total, 2),
                "best_carrier": best_carrier,
                "source": source,
                "freight_opt": round(best_freight, 4),
                "cc_opt": round(best_cc, 4),
                "cost_unit_opt": round(best_cost_unit, 4),
                "cost_total_opt": round(cost_opt_total, 2),
                "savings": round(cost_curr_total - cost_opt_total, 2),
                "packages": qty,
                "changed": str(row["transportadora_atual"]).strip().lower() != str(best_carrier).strip().lower()
            })
        
        df_results = pd.DataFrame(results)
        total_savings = df_results["savings"].sum()
        total_current = df_results["cost_total_current"].sum()
        total_optimized = df_results["cost_total_opt"].sum()
        savings_pct = (total_savings / total_current * 100) if total_current > 0 else 0
        
        o1, o2, o3, o4 = st.columns(4)
        with o1:
            st.metric("📦 Total Packages", f"{df_results['packages'].sum():,.0f}")
        with o2:
            st.metric("💰 Current Cost (Real)", fmt_brl(total_current))
        with o3:
            st.metric("💎 Optimized Cost", fmt_brl(total_optimized))
        with o4:
            st.markdown(savings_card("Potential Savings", total_savings, savings_pct), unsafe_allow_html=True)
        
        if customs_custom:
            st.markdown(
                '<div class="warning-box">'
                '⚠️ Custom CC active: Optimized cost uses custom values. Current cost uses real CC.'
                '</div>',
                unsafe_allow_html=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Savings by state
        st.markdown("#### 💰 Savings by State")
        savings_state = df_results.groupby("state").agg(
            savings=("savings", "sum"),
            packages=("packages", "sum")
        ).reset_index().sort_values("savings", ascending=False)
        
        fig_savings = px.bar(savings_state, x="state", y="savings",
                             text=savings_state["savings"].apply(lambda x: f"R$ {x:,.0f}"),
                             color="savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"])
        fig_savings.update_traces(textposition='outside')
        fig_savings.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False)
        st.plotly_chart(fig_savings, use_container_width=True, key="t2_savings")
        
        # Share comparison
        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("#### Current Share (TMS)")
            share_current = df_results.groupby("current_carrier")["packages"].sum().reset_index()
            share_current.columns = ["Carrier", "Packages"]
            fig_sc = px.pie(share_current, values="Packages", names="Carrier", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            fig_sc.update_traces(textposition="inside", textinfo="percent+label")
            fig_sc.update_layout(height=350)
            st.plotly_chart(fig_sc, use_container_width=True, key="t2_share_curr")
        
        with col_f:
            st.markdown("#### Optimized Share")
            share_opt = df_results.groupby("best_carrier")["packages"].sum().reset_index()
            share_opt.columns = ["Carrier", "Packages"]
            fig_so = px.pie(share_opt, values="Packages", names="Carrier", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            fig_so.update_traces(textposition="inside", textinfo="percent+label")
            fig_so.update_layout(height=350)
            st.plotly_chart(fig_so, use_container_width=True, key="t2_share_opt")
        
        # Detail table
        st.markdown("#### 📋 Optimization Detail")
        df_display = df_results.copy()
        df_display["changed_txt"] = df_display["changed"].apply(lambda x: "✅" if x else "—")
        
        st.dataframe(
            df_display[[
                "state", "airport", "broker", "current_carrier", "freight_tms", "cc_real",
                "cost_unit_current", "cost_total_current", "best_carrier", "source",
                "freight_opt", "cc_opt", "cost_unit_opt", "cost_total_opt", "savings",
                "packages", "changed_txt"
            ]].rename(columns={
                "state": "State", "airport": "Airport", "broker": "Broker",
                "current_carrier": "Current Carrier", "freight_tms": "Freight TMS",
                "cc_real": "CC Real", "cost_unit_current": "Cost/Pkg Curr",
                "cost_total_current": "Total Curr", "best_carrier": "Best Carrier",
                "source": "Source", "freight_opt": "Freight Opt", "cc_opt": "CC Opt",
                "cost_unit_opt": "Cost/Pkg Opt", "cost_total_opt": "Total Opt",
                "savings": "Savings", "packages": "Packages", "changed_txt": "Changed?"
            }).style.format({
                "Freight TMS": "R$ {:.2f}", "CC Real": "R$ {:.2f}", "Cost/Pkg Curr": "R$ {:.2f}",
                "Total Curr": "R$ {:,.2f}", "Freight Opt": "R$ {:.2f}", "CC Opt": "R$ {:.2f}",
                "Cost/Pkg Opt": "R$ {:.2f}", "Total Opt": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}", "Packages": "{:,.0f}"
            }),
            use_container_width=True, height=400
        )
        
        # Export
        excel_opt = generate_excel({"Optimization": df_results, "Savings_by_State": savings_state})
        st.download_button(
            "📥 Download Optimization (Excel)", data=excel_opt,
            file_name="optimization_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_optimization"
        )

# ============================================================
# TAB 3 — SIMULATOR (COMPLETELY REVISED)
# ============================================================
# ============================================================
# TAB 3 — SIMULATOR (CORRIGIDO - MÉDIA PONDERADA)
# ============================================================
with tab3:
    st.markdown('<div class="sub-header">🔄 Volume Redistribution Simulator</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        '<strong>How calculations work:</strong><br>'
        '• <strong>Current Cost (Real):</strong> Uses ORIGINAL volume × (TMS freight + CC from broker sheet)<br>'
        '• <strong>Simulated Cost:</strong> Uses SIMULATED volume × (quotation freight + custom CC)<br>'
        '• <strong>Savings:</strong> Current Cost - Simulated Cost<br><br>'
        '<em>Note: If you redistribute volume between lines, the comparison shows the real savings/cost impact.</em>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Build reference maps
    @st.cache_data
    def build_reference_maps(_df, _quot_cols):
        """Build reference maps for simulation"""
        df = _df.copy()
        
        # State coverage
        state_coverage = {}
        for state in df["estado"].unique():
            df_state = df[df["estado"] == state]
            carriers = set(df_state["transportadora_atual"].str.strip().unique())
            for col in _quot_cols:
                carrier_name = extract_carrier_name(col)
                if (df_state[col] > 0).any():
                    carriers.add(carrier_name.capitalize())
            state_coverage[state] = sorted(carriers)
        
        # Quotation by state (weighted average)
        quotation_map = {}
        for state in df["estado"].unique():
            df_state = df[df["estado"] == state]
            for col in _quot_cols:
                carrier_key = extract_carrier_name(col)
                mask = df_state[col] > 0
                if mask.any():
                    # Weighted average by volume
                    total_vol = df_state.loc[mask, "qtd_pacotes_total"].sum()
                    if total_vol > 0:
                        weighted_sum = (df_state.loc[mask, col] * df_state.loc[mask, "qtd_pacotes_total"]).sum()
                        quotation_map[(carrier_key, state)] = round(weighted_sum / total_vol, 4)
        
        # TMS freight by carrier/state (weighted average)
        freight_tms_map = {}
        for (carrier, state), group in df.groupby(["transportadora_atual", "estado"]):
            total_vol = group["qtd_pacotes_total"].sum()
            if total_vol > 0:
                weighted_sum = (group["media_frete_tms"] * group["qtd_pacotes_total"]).sum()
                freight_tms_map[(carrier, state)] = round(weighted_sum / total_vol, 4)
        
        # Airport-broker relationships
        airport_broker = df.groupby("aeroporto")["broker"].apply(
            lambda x: sorted(x.unique().tolist())
        ).to_dict()
        
        return state_coverage, quotation_map, freight_tms_map, airport_broker
    
    state_coverage, quotation_map, freight_tms_map, airport_broker = build_reference_maps(
        df_dados, quotation_columns
    )
    
    # Filters
    st.markdown("### 🔍 Filters")
    sf1, sf2, sf3, sf4 = st.columns(4)
    with sf1:
        filter_states = st.multiselect(
            "🗺️ States", sorted(df_dados["estado"].unique()),
            default=sorted(df_dados["estado"].unique()), key="sim_states"
        )
    with sf2:
        filter_airports = st.multiselect(
            "✈️ Airports", sorted(df_dados["aeroporto"].unique()),
            default=sorted(df_dados["aeroporto"].unique()), key="sim_airports"
        )
    with sf3:
        filter_brokers = st.multiselect(
            "📝 Brokers", sorted(df_dados["broker"].unique()),
            default=sorted(df_dados["broker"].unique()), key="sim_brokers"
        )
    with sf4:
        filter_carriers = st.multiselect(
            "🚚 Carriers", sorted(df_dados["transportadora_atual"].unique()),
            default=sorted(df_dados["transportadora_atual"].unique()), key="sim_carriers"
        )
    
    df_filtered = df_dados[
        df_dados["estado"].isin(filter_states) &
        df_dados["aeroporto"].isin(filter_airports) &
        df_dados["broker"].isin(filter_brokers) &
        df_dados["transportadora_atual"].isin(filter_carriers)
    ].copy()
    
    if df_filtered.empty:
        st.warning("⚠️ No data for the selected filters.")
    else:
        # ========================================
        # CALCULATE REFERENCE TOTALS (LINE BY LINE - SAME AS OVERVIEW)
        # ========================================
        total_vol_reference = df_filtered["qtd_pacotes_total"].sum()
        total_cost_reference = 0
        
        # Calculate line by line to match Overview exactly
        for _, row in df_filtered.iterrows():
            f_unit, cc_unit, cost_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            total_cost_reference += cost_unit * row["qtd_pacotes_total"]
        
        avg_cost_reference = total_cost_reference / total_vol_reference if total_vol_reference > 0 else 0
        
        # Show reference values
        st.markdown("### 📊 Reference Values (Current Real Cost)")
        ref_col1, ref_col2, ref_col3 = st.columns(3)
        with ref_col1:
            st.metric("📦 Total Volume", f"{total_vol_reference:,.0f}")
        with ref_col2:
            st.metric("💰 Total Current Cost", fmt_brl(total_cost_reference))
        with ref_col3:
            st.metric("📊 Avg Cost/Pkg", fmt_brl(avg_cost_reference))
        
        st.markdown("---")
        
        # ========================================
        # AGGREGATE DATA WITH WEIGHTED AVERAGES
        # ========================================
        def aggregate_with_weighted_avg(df, group_cols, quot_cols):
            """Aggregate data using weighted averages for freight and quotations"""
            results = []
            
            for keys, group in df.groupby(group_cols):
                if not isinstance(keys, tuple):
                    keys = (keys,)
                
                total_vol = group["qtd_pacotes_total"].sum()
                total_weight = group["soma_peso_gramas"].sum()
                
                if total_vol == 0:
                    continue
                
                # Weighted average for freight
                weighted_freight = (group["media_frete_tms"] * group["qtd_pacotes_total"]).sum() / total_vol
                
                row_data = {
                    group_cols[i]: keys[i] for i in range(len(group_cols))
                }
                row_data["qtd_pacotes_total"] = total_vol
                row_data["soma_peso_gramas"] = total_weight
                row_data["media_frete_tms"] = round(weighted_freight, 4)
                
                # Weighted average for each quotation column
                for col in quot_cols:
                    if col in group.columns:
                        mask = group[col] > 0
                        if mask.any():
                            vol_with_quot = group.loc[mask, "qtd_pacotes_total"].sum()
                            if vol_with_quot > 0:
                                weighted_quot = (group.loc[mask, col] * group.loc[mask, "qtd_pacotes_total"]).sum() / vol_with_quot
                                row_data[col] = round(weighted_quot, 4)
                            else:
                                row_data[col] = 0
                        else:
                            row_data[col] = 0
                    else:
                        row_data[col] = 0
                
                results.append(row_data)
            
            return pd.DataFrame(results)
        
        df_agg = aggregate_with_weighted_avg(
            df_filtered, 
            ["aeroporto", "broker", "estado", "transportadora_atual"],
            quotation_columns
        )
        
        # Verify aggregation matches reference
        agg_vol = df_agg["qtd_pacotes_total"].sum()
        agg_cost = 0
        for _, row in df_agg.iterrows():
            f_unit, cc_unit, cost_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            agg_cost += cost_unit * row["qtd_pacotes_total"]
        
        # Show validation
        cost_diff = abs(agg_cost - total_cost_reference)
        if cost_diff > 1:  # More than R$1 difference
            st.markdown(
                f'<div class="warning-box">'
                f'⚠️ <strong>Aggregation validation:</strong> Small rounding difference detected '
                f'(R$ {cost_diff:.2f}). This is normal for weighted averages.'
                f'</div>',
                unsafe_allow_html=True
            )
        
        # Initialize edits
        sim_key = f"sim_{hash(str(filter_states)+str(filter_airports)+str(filter_brokers)+str(filter_carriers))}"
        if "sim_key" not in st.session_state or st.session_state.sim_key != sim_key:
            st.session_state.sim_edits = {}
            st.session_state.sim_key = sim_key
            # Clear previous results
            for k in ["df_simulation_result", "sim_cost_current", "sim_cost_simulated"]:
                if k in st.session_state:
                    del st.session_state[k]
        
        # Build edit lines
        all_airports = sorted(df_dados["aeroporto"].unique().tolist())
        all_brokers = sorted(df_dados["broker"].unique().tolist())
        all_carriers = sorted(set(
            list(df_dados["transportadora_atual"].str.strip().unique()) +
            [extract_carrier_name(c).capitalize() for c in quotation_columns]
        ))
        
        st.markdown("### ✏️ Configure Simulation")
        st.caption("Edit volume and destination for each line. Current Cost uses original volume × real unit cost.")
        
        # Header
        st.markdown(
            '<div style="display:grid; grid-template-columns: 0.5fr 0.7fr 0.7fr 0.4fr 0.5fr 0.5fr 0.6fr 0.7fr 0.7fr 0.5fr; '
            'gap:4px; font-weight:600; font-size:0.72rem; padding:8px 4px; '
            'background:linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%); border-radius:8px; margin-bottom:4px; text-align:center;">'
            '<div>✈️Airp</div><div>📝Broker</div><div>🚚Carrier</div><div>🗺️UF</div>'
            '<div>📦Orig</div><div>📦Sim</div><div>✈️Dest</div>'
            '<div>📝Dest</div><div>🚚Dest</div><div>💎Cost</div></div>',
            unsafe_allow_html=True
        )
        
        edit_lines = []
        for idx, row in df_agg.iterrows():
            # Calculate current real cost using weighted average freight
            f_unit, cc_unit, cost_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            
            edit_lines.append({
                "idx": idx,
                "airport": row["aeroporto"],
                "broker": row["broker"],
                "state": row["estado"],
                "carrier": row["transportadora_atual"],
                "vol_current": int(row["qtd_pacotes_total"]),
                "freight_tms": round(f_unit, 4),
                "cc_real": round(cc_unit, 4),
                "cost_unit_real": round(cost_unit, 4),
                "row_data": row
            })
        
        for i, line in enumerate(edit_lines):
            row_key = f"row_{i}"
            edits = st.session_state.sim_edits.get(row_key, {})
            
            cols = st.columns([0.5, 0.7, 0.7, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7, 0.5])
            
            with cols[0]:
                st.caption(line["airport"])
            with cols[1]:
                st.caption(line["broker"])
            with cols[2]:
                st.caption(line["carrier"])
            with cols[3]:
                st.caption(line["state"])
            with cols[4]:
                st.caption(f"{line['vol_current']:,}")
            with cols[5]:
                vol_sim = st.number_input(
                    "vol", value=int(edits.get("vol", line["vol_current"])),
                    min_value=0, step=100, key=f"vol_{i}", label_visibility="collapsed"
                )
            with cols[6]:
                d_airport = edits.get("airport", line["airport"])
                ai = all_airports.index(d_airport) if d_airport in all_airports else 0
                airport_dest = st.selectbox(
                    "airp", all_airports, index=ai, key=f"airport_{i}", label_visibility="collapsed"
                )
            with cols[7]:
                brokers_avail = airport_broker.get(airport_dest, all_brokers)
                if not brokers_avail:
                    brokers_avail = all_brokers
                d_broker = edits.get("broker", line["broker"])
                bi = brokers_avail.index(d_broker) if d_broker in brokers_avail else 0
                broker_dest = st.selectbox(
                    "brk", brokers_avail, index=bi, key=f"broker_{i}", label_visibility="collapsed"
                )
            with cols[8]:
                carriers_state = state_coverage.get(line["state"], all_carriers)
                carriers_allowed = [
                    c for c in carriers_state
                    if is_carrier_allowed(c.lower().replace(" ", "_"), airport_dest, broker_dest,
                                          st.session_state.restriction_rules)
                ]
                if not carriers_allowed:
                    carriers_allowed = [line["carrier"]]
                d_carrier = edits.get("carrier", line["carrier"])
                ti = carriers_allowed.index(d_carrier) if d_carrier in carriers_allowed else 0
                carrier_dest = st.selectbox(
                    "car", carriers_allowed, index=ti, key=f"carrier_{i}", label_visibility="collapsed"
                )
            with cols[9]:
                st.caption(f"R$ {line['cost_unit_real']:.2f}")
            
            st.session_state.sim_edits[row_key] = {
                "vol": vol_sim, "airport": airport_dest, "broker": broker_dest, "carrier": carrier_dest
            }
        
        # Volume summary
        st.markdown("---")
        st.markdown("### 📊 Volume Summary")
        
        vol_original = sum(l["vol_current"] for l in edit_lines)
        vol_simulated = sum(
            st.session_state.sim_edits.get(f"row_{i}", {}).get("vol", l["vol_current"]) 
            for i, l in enumerate(edit_lines)
        )
        vol_diff = vol_simulated - vol_original
        
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            st.metric("📦 Original Volume", f"{vol_original:,}")
        with vc2:
            st.metric("📦 Simulated Volume", f"{vol_simulated:,}")
        with vc3:
            delta_color = "normal" if vol_diff == 0 else "inverse" if vol_diff < 0 else "off"
            st.metric("📊 Difference", f"{vol_diff:+,}", delta_color=delta_color)
        
        if vol_diff != 0:
            st.markdown(
                f'<div class="volume-warning">'
                f'⚠️ <strong>Volume difference:</strong> {vol_diff:+,} packages. '
                f'Current Cost uses original volumes, Simulated Cost uses edited volumes.'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="volume-ok">'
                f'✅ <strong>Volume balanced:</strong> Total remains {vol_original:,} packages.'
                f'</div>',
                unsafe_allow_html=True
            )
        
        # Redistribution summary
        st.markdown("### 📋 Redistribution Summary")
        col_red1, col_red2, col_red3 = st.columns(3)
        
        carrier_vol_curr = {}
        carrier_vol_sim = {}
        broker_vol_curr = {}
        broker_vol_sim = {}
        airport_vol_curr = {}
        airport_vol_sim = {}
        
        for i, line in enumerate(edit_lines):
            edits = st.session_state.sim_edits.get(f"row_{i}", {})
            vol_curr = line["vol_current"]
            vol_sim = edits.get("vol", line["vol_current"])
            
            carrier_vol_curr[line["carrier"]] = carrier_vol_curr.get(line["carrier"], 0) + vol_curr
            broker_vol_curr[line["broker"]] = broker_vol_curr.get(line["broker"], 0) + vol_curr
            airport_vol_curr[line["airport"]] = airport_vol_curr.get(line["airport"], 0) + vol_curr
            
            carrier_dest = edits.get("carrier", line["carrier"])
            broker_dest = edits.get("broker", line["broker"])
            airport_dest = edits.get("airport", line["airport"])
            
            carrier_vol_sim[carrier_dest] = carrier_vol_sim.get(carrier_dest, 0) + vol_sim
            broker_vol_sim[broker_dest] = broker_vol_sim.get(broker_dest, 0) + vol_sim
            airport_vol_sim[airport_dest] = airport_vol_sim.get(airport_dest, 0) + vol_sim
        
        with col_red1:
            st.markdown("#### 🚚 By Carrier")
            all_carriers_red = sorted(set(list(carrier_vol_curr.keys()) + list(carrier_vol_sim.keys())))
            for c in all_carriers_red:
                vc = carrier_vol_curr.get(c, 0)
                vs = carrier_vol_sim.get(c, 0)
                d = vs - vc
                if vc == 0 and vs == 0:
                    continue
                tag = " 🆕" if vc == 0 else ""
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{c}**{tag}: {vc:,} → {vs:,} ({d:+,}) {arrow}")
        
        with col_red2:
            st.markdown("#### 📝 By Broker")
            all_brokers_red = sorted(set(list(broker_vol_curr.keys()) + list(broker_vol_sim.keys())))
            for b in all_brokers_red:
                vb_c = broker_vol_curr.get(b, 0)
                vb_s = broker_vol_sim.get(b, 0)
                d = vb_s - vb_c
                if vb_c == 0 and vb_s == 0:
                    continue
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{b}**: {vb_c:,} → {vb_s:,} ({d:+,}) {arrow}")
        
        with col_red3:
            st.markdown("#### ✈️ By Airport")
            all_airports_red = sorted(set(list(airport_vol_curr.keys()) + list(airport_vol_sim.keys())))
            for a in all_airports_red:
                va_c = airport_vol_curr.get(a, 0)
                va_s = airport_vol_sim.get(a, 0)
                d = va_s - va_c
                if va_c == 0 and va_s == 0:
                    continue
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{a}**: {va_c:,} → {va_s:,} ({d:+,}) {arrow}")
        
        # Calculate button
        st.markdown("---")
        if st.button("🚀 Calculate Simulation", type="primary", key="btn_calc_sim"):
            simulation_results = []
            total_cost_current = 0
            total_cost_simulated = 0
            errors = []
            
            for i, line in enumerate(edit_lines):
                edits = st.session_state.sim_edits.get(f"row_{i}", {})
                
                vol_current = line["vol_current"]
                vol_sim = int(edits.get("vol", line["vol_current"]))
                
                airport_dest = edits.get("airport", line["airport"])
                broker_dest = edits.get("broker", line["broker"])
                carrier_dest = edits.get("carrier", line["carrier"])
                
                carrier_key = carrier_dest.lower().replace(" ", "_")
                if vol_sim > 0:
                    if not is_carrier_allowed(carrier_key, airport_dest, broker_dest, 
                                              st.session_state.restriction_rules):
                        errors.append(f"🔒 {carrier_dest} blocked at {airport_dest}/{broker_dest}")
                        continue
                    
                    carriers_state = state_coverage.get(line["state"], [])
                    carrier_in_state = (carrier_dest in carriers_state or 
                                       carrier_dest.capitalize() in carriers_state or
                                       carrier_dest.lower() in [c.lower() for c in carriers_state])
                    if not carrier_in_state:
                        errors.append(f"❌ {carrier_dest} has no coverage in {line['state']}")
                        continue
                
                # ========================================
                # CURRENT COST (uses ORIGINAL volume)
                # ========================================
                freight_current = line["freight_tms"]
                cc_current = line["cc_real"]
                cost_unit_current = line["cost_unit_real"]
                cost_total_current_line = round(cost_unit_current * vol_current, 2)
                
                # ========================================
                # SIMULATED COST (uses SIMULATED volume)
                # ========================================
                changed_carrier = carrier_dest.lower() != line["carrier"].lower()
                changed_airport = airport_dest != line["airport"]
                changed_broker = broker_dest != line["broker"]
                changed = changed_carrier or changed_airport or changed_broker
                
                if not changed and vol_sim == vol_current:
                    freight_sim = freight_current
                    cc_sim = cc_current
                    cost_unit_sim = cost_unit_current
                    sim_type = "KEPT"
                else:
                    if changed_carrier:
                        quot_col = f"media_cotacao_{carrier_key}"
                        row_data = line["row_data"]
                        
                        if quot_col in row_data.index and row_data[quot_col] > 0:
                            freight_sim = round(float(row_data[quot_col]), 4)
                        elif (carrier_key, line["state"]) in quotation_map:
                            freight_sim = quotation_map[(carrier_key, line["state"])]
                        elif (carrier_dest, line["state"]) in freight_tms_map:
                            freight_sim = freight_tms_map[(carrier_dest, line["state"])]
                        else:
                            freight_sim = freight_current
                        sim_type = "QUOTATION"
                    else:
                        freight_sim = freight_current
                        sim_type = "ROUTE_CHANGE" if (changed_airport or changed_broker) else "VOLUME_CHANGE"
                    
                    cc_sim = get_cc_for_simulation(airport_dest, broker_dest, df_broker, customs_custom)
                    discount = calculate_anjun_discount(carrier_dest, broker_dest, anjun_discount, apply_anjun_discount)
                    cc_sim = max(0, cc_sim - discount)
                    cc_sim = round(cc_sim, 4)
                    cost_unit_sim = round(freight_sim + cc_sim, 4)
                
                cost_total_sim_line = round(cost_unit_sim * vol_sim, 2)
                
                total_cost_current += cost_total_current_line
                total_cost_simulated += cost_total_sim_line
                
                savings_line = round(cost_total_current_line - cost_total_sim_line, 2)
                
                changes = []
                if changed_airport:
                    changes.append(f"Airport: {line['airport']}→{airport_dest}")
                if changed_broker:
                    changes.append(f"Broker: {line['broker']}→{broker_dest}")
                if changed_carrier:
                    changes.append(f"Carrier: {line['carrier']}→{carrier_dest}")
                if vol_sim != vol_current:
                    changes.append(f"Volume: {vol_current:,}→{vol_sim:,}")
                
                simulation_results.append({
                    "State": line["state"],
                    "Airport Orig": line["airport"],
                    "Broker Orig": line["broker"],
                    "Carrier Orig": line["carrier"],
                    "Airport Dest": airport_dest,
                    "Broker Dest": broker_dest,
                    "Carrier Dest": carrier_dest,
                    "Type": sim_type,
                    "Changes": "; ".join(changes) if changes else "None",
                    "Vol Original": vol_current,
                    "Vol Simulated": vol_sim,
                    "Freight Orig": freight_current,
                    "CC Orig (Real)": cc_current,
                    "Cost/Pkg Orig": cost_unit_current,
                    "Freight Sim": freight_sim,
                    "CC Sim": cc_sim,
                    "Cost/Pkg Sim": cost_unit_sim,
                    "Total Cost Orig": cost_total_current_line,
                    "Total Cost Sim": cost_total_sim_line,
                    "Savings": savings_line
                })
            
            if errors:
                for e in errors:
                    st.error(e)
            
            if simulation_results:
                df_sim = pd.DataFrame(simulation_results)
                st.session_state.df_simulation_result = df_sim
                st.session_state.sim_cost_current = total_cost_current
                st.session_state.sim_cost_simulated = total_cost_simulated
                st.success("✅ Simulation calculated!")
            else:
                st.warning("No valid lines to simulate.")
        
        # Display results
        if "df_simulation_result" in st.session_state and not st.session_state.df_simulation_result.empty:
            df_sim = st.session_state.df_simulation_result
            cost_curr = st.session_state.sim_cost_current
            cost_sim = st.session_state.sim_cost_simulated
            total_savings = cost_curr - cost_sim
            savings_pct = (total_savings / cost_curr * 100) if cost_curr > 0 else 0
            
            st.markdown("---")
            st.markdown("### 📊 Simulation Results")
            
            # Validation
            cost_diff_validation = abs(cost_curr - total_cost_reference)
            validation_status = "✅ Match" if cost_diff_validation < 10 else f"⚠️ Diff: {fmt_brl(cost_diff_validation)}"
            
            st.markdown(
                f'<div class="info-box">'
                f'<strong>📌 Validation:</strong><br>'
                f'• Reference (filtered data): <strong>{fmt_brl(total_cost_reference)}</strong> '
                f'(Avg: <strong>{fmt_brl(avg_cost_reference)}</strong>/pkg)<br>'
                f'• Current Cost (simulation): <strong>{fmt_brl(cost_curr)}</strong> '
                f'(Avg: <strong>{fmt_brl(cost_curr / df_sim["Vol Original"].sum() if df_sim["Vol Original"].sum() > 0 else 0)}</strong>/pkg)<br>'
                f'• Status: <strong>{validation_status}</strong>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            if customs_custom:
                st.markdown(
                    '<div class="warning-box">'
                    '⚠️ <strong>Custom CC active:</strong> Current Cost uses REAL CC. '
                    'Simulated Cost uses custom CC for changed routes.'
                    '</div>',
                    unsafe_allow_html=True
                )
            
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                vol_orig = df_sim["Vol Original"].sum()
                vol_sim_total = df_sim["Vol Simulated"].sum()
                st.metric("📦 Volume", f"{vol_orig:,} → {vol_sim_total:,}")
            with m2:
                avg_curr = cost_curr / vol_orig if vol_orig > 0 else 0
                st.metric("💰 Current Cost", fmt_brl(cost_curr), 
                          delta=f"Avg: {fmt_brl(avg_curr)}/pkg", delta_color="off")
            with m3:
                avg_sim = cost_sim / vol_sim_total if vol_sim_total > 0 else 0
                st.metric("💎 Simulated Cost", fmt_brl(cost_sim),
                          delta=f"Avg: {fmt_brl(avg_sim)}/pkg", delta_color="off")
            with m4:
                st.markdown(savings_card("Savings", total_savings, savings_pct), unsafe_allow_html=True)
            
            # Share comparison
            st.markdown("#### 📊 Share Comparison")
            cg1, cg2 = st.columns(2)
            
            with cg1:
                st.markdown("##### Current Carriers")
                share_curr = df_sim.groupby("Carrier Orig")["Vol Original"].sum().reset_index()
                share_curr.columns = ["Carrier", "Packages"]
                if not share_curr.empty and share_curr["Packages"].sum() > 0:
                    fig_curr = px.pie(share_curr, values="Packages", names="Carrier", hole=0.4,
                                      color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_curr.update_traces(textposition="inside", textinfo="percent+label")
                    fig_curr.update_layout(height=350, margin=dict(t=30, b=30))
                    st.plotly_chart(fig_curr, use_container_width=True, key="sim_share_curr")
            
            with cg2:
                st.markdown("##### Simulated Carriers")
                share_sim = df_sim.groupby("Carrier Dest")["Vol Simulated"].sum().reset_index()
                share_sim.columns = ["Carrier", "Packages"]
                if not share_sim.empty and share_sim["Packages"].sum() > 0:
                    fig_sim = px.pie(share_sim, values="Packages", names="Carrier", hole=0.4,
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_sim.update_traces(textposition="inside", textinfo="percent+label")
                    fig_sim.update_layout(height=350, margin=dict(t=30, b=30))
                    st.plotly_chart(fig_sim, use_container_width=True, key="sim_share_sim")
            
            # Savings by state
            st.markdown("#### 💰 Savings by State")
            savings_by_state = df_sim.groupby("State").agg({
                "Vol Original": "sum",
                "Vol Simulated": "sum",
                "Total Cost Orig": "sum",
                "Total Cost Sim": "sum",
                "Savings": "sum"
            }).reset_index()
            savings_by_state = savings_by_state.sort_values("Savings", ascending=False)
            
            fig_sav = px.bar(savings_by_state, x="State", y="Savings",
                             text=savings_by_state["Savings"].apply(lambda x: f"R$ {x:,.0f}"),
                             color="Savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"])
            fig_sav.update_traces(textposition='outside')
            fig_sav.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False)
            st.plotly_chart(fig_sav, use_container_width=True, key="sim_sav_state")
            
            # Detail table
            st.markdown("#### 📋 Simulation Detail")
            st.dataframe(
                df_sim.style.format({
                    "Vol Original": "{:,}",
                    "Vol Simulated": "{:,}",
                    "Freight Orig": "R$ {:.4f}",
                    "CC Orig (Real)": "R$ {:.4f}",
                    "Cost/Pkg Orig": "R$ {:.4f}",
                    "Freight Sim": "R$ {:.4f}",
                    "CC Sim": "R$ {:.4f}",
                    "Cost/Pkg Sim": "R$ {:.4f}",
                    "Total Cost Orig": "R$ {:,.2f}",
                    "Total Cost Sim": "R$ {:,.2f}",
                    "Savings": "R$ {:,.2f}"
                }),
                use_container_width=True, height=400
            )
            
            # Export
            st.markdown("---")
            excel_sim = generate_excel({
                "Simulation_Detail": df_sim,
                "Savings_by_State": savings_by_state
            })
            st.download_button(
                "📥 Download Simulation (Excel)",
                data=excel_sim,
                file_name="simulation_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_sim"
            )
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Reset Simulation", key="reset_sim"):
            st.session_state.sim_edits = {}
            st.session_state.sim_key = ""
            for k in ["df_simulation_result", "sim_cost_current", "sim_cost_simulated"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


# ============================================================
# TAB 4 — LIMITS (REVISED)
# ============================================================
with tab4:
    st.markdown('<div class="sub-header">🎯 Limits - Broker and Carrier</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        '<strong>How calculations work:</strong><br>'
        '• <strong>Reference Cost:</strong> REAL CC from broker sheet<br>'
        '• <strong>Simulated Allocation:</strong> Custom CC (when configured)<br>'
        '• Algorithm allocates volume to lowest cost options respecting limits'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Period settings
    st.markdown("### 📅 Period")
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        period_days = st.number_input("Days", 1, 365, 30, 1, key="period_days")
    
    total_packages_all = int(df_dados["qtd_pacotes_total"].sum())
    daily_volume = total_packages_all / period_days if period_days > 0 else total_packages_all
    
    with cp2:
        st.markdown(metric_card("Total Volume", f"{total_packages_all:,}", "📦"), unsafe_allow_html=True)
    with cp3:
        st.markdown(metric_card("Volume/Day", f"{daily_volume:,.0f}", "📊"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Build carrier/broker lists
    carriers_system = sorted(set(
        list(df_dados["transportadora_atual"].str.strip().unique()) +
        [extract_carrier_name(c).capitalize() for c in quotation_columns]
    ))
    brokers_system = sorted(df_dados["broker"].unique().tolist())
    
    # Current volumes
    vol_by_carrier = df_dados.groupby("transportadora_atual")["qtd_pacotes_total"].sum().to_dict()
    vol_by_broker = df_dados.groupby("broker")["qtd_pacotes_total"].sum().to_dict()
    
    # Broker limits
    st.markdown("### 📝 Limits by Broker")
    broker_limits = {}
    cols_b = st.columns(min(len(brokers_system), 4))
    
    for i, broker in enumerate(brokers_system):
        ci = i % len(cols_b)
        with cols_b[ci]:
            vol_broker = vol_by_broker.get(broker, 0)
            share_broker = (vol_broker / total_packages_all * 100) if total_packages_all > 0 else 0
            daily_broker = vol_broker / period_days if period_days > 0 else vol_broker
            
            st.markdown(
                f'<div class="desp-limit-box"><strong>📝 {broker}</strong><br>'
                f'<small>Current: {vol_broker:,} ({share_broker:.1f}%)</small></div>',
                unsafe_allow_html=True
            )
            
            no_limit = st.checkbox("No Limit", True, key=f"broker_no_{broker}")
            if no_limit:
                broker_limits[broker.lower()] = None
            else:
                limit_type = st.radio(
                    "Mode", ["% Vol", "Pkgs/Day", "Total"],
                    horizontal=True, key=f"broker_type_{broker}"
                )
                if limit_type == "% Vol":
                    pct = st.number_input("Max %", 0.0, 100.0, round(share_broker, 1), 1.0, 
                                          key=f"broker_pct_{broker}")
                    broker_limits[broker.lower()] = int(total_packages_all * pct / 100)
                elif limit_type == "Pkgs/Day":
                    pkgs = st.number_input("Pkgs/day", 0, value=int(daily_broker), step=100,
                                           key=f"broker_day_{broker}")
                    broker_limits[broker.lower()] = int(pkgs * period_days)
                else:
                    total_lim = st.number_input("Total", 0, total_packages_all, int(vol_broker), 100,
                                                key=f"broker_total_{broker}")
                    broker_limits[broker.lower()] = total_lim
    
    st.markdown("---")
    
    # Carrier limits
    st.markdown("### 🚚 Limits by Carrier")
    carrier_limits = {}
    cols_c = st.columns(min(len(carriers_system), 4))
    
    for i, carrier in enumerate(carriers_system):
        ci = i % len(cols_c)
        with cols_c[ci]:
            vol_carrier = vol_by_carrier.get(carrier, vol_by_carrier.get(carrier.lower(), 0))
            share_carrier = (vol_carrier / total_packages_all * 100) if total_packages_all > 0 else 0
            daily_carrier = vol_carrier / period_days if period_days > 0 else vol_carrier
            
            carrier_key = carrier.lower().replace(" ", "_")
            tags = ""
            if carrier_key in st.session_state.partial_carriers:
                tags += " ⚠️"
            if carrier_key in st.session_state.restriction_rules:
                tags += " 🔒"
            
            st.markdown(
                f'<div class="broker-limit-box"><strong>🚚 {carrier}{tags}</strong><br>'
                f'<small>Current: {vol_carrier:,} ({share_carrier:.1f}%)</small></div>',
                unsafe_allow_html=True
            )
            
            no_limit = st.checkbox("No Limit", True, key=f"carrier_no_{carrier}")
            if no_limit:
                carrier_limits[carrier.lower()] = None
            else:
                limit_type = st.radio(
                    "Mode", ["% Vol", "Pkgs/Day", "Total"],
                    horizontal=True, key=f"carrier_type_{carrier}"
                )
                if limit_type == "% Vol":
                    pct = st.number_input("Max %", 0.0, 100.0, round(share_carrier, 1), 1.0,
                                          key=f"carrier_pct_{carrier}")
                    carrier_limits[carrier.lower()] = int(total_packages_all * pct / 100)
                elif limit_type == "Pkgs/Day":
                    pkgs = st.number_input("Pkgs/day", 0, value=int(daily_carrier), step=100,
                                           key=f"carrier_day_{carrier}")
                    carrier_limits[carrier.lower()] = int(pkgs * period_days)
                else:
                    total_lim = st.number_input("Total", 0, total_packages_all, int(vol_carrier), 100,
                                                key=f"carrier_total_{carrier}")
                    carrier_limits[carrier.lower()] = total_lim
    
    st.markdown("---")
    
    # Execute simulation with limits
    if st.button("🚀 Execute with Limits", type="primary", key="btn_limits"):
        # Aggregate data
        agg_cols = {"qtd_pacotes_total": "sum", "soma_peso_gramas": "sum", "media_frete_tms": "mean"}
        for col in quotation_columns:
            agg_cols[col] = "mean"
        
        df_agg = df_dados.groupby(
            ["estado", "aeroporto", "broker", "transportadora_atual"]
        ).agg(agg_cols).reset_index()
        
        # Build capacity dictionaries
        cap_carrier = {
            c.lower(): carrier_limits.get(c.lower()) if carrier_limits.get(c.lower()) is not None else float("inf")
            for c in carriers_system
        }
        
        cap_broker = {
            b.lower(): broker_limits.get(b.lower()) if broker_limits.get(b.lower()) is not None else float("inf")
            for b in brokers_system
        }
        
        # Build allocation options
        options = []
        for idx, row in df_agg.iterrows():
            broker = str(row["broker"]).strip()
            airport = str(row["aeroporto"]).strip()
            carrier_current = str(row["transportadora_atual"]).strip()
            
            # Calculate real cost for reference
            f_real, cc_real, cost_real = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            
            # Option 1: Keep current carrier (real cost)
            options.append({
                "idx": idx,
                "state": row["estado"],
                "airport": airport,
                "broker": broker,
                "carrier_current": carrier_current,
                "carrier": carrier_current,
                "carrier_lower": carrier_current.lower().replace(" ", "_"),
                "broker_lower": broker.lower(),
                "freight_unit": f_real,
                "cc": cc_real,
                "cost_unit": cost_real,
                "freight_real": f_real,
                "cc_real": cc_real,
                "cost_real": cost_real,
                "qty": row["qtd_pacotes_total"],
                "type": "TMS"
            })
            
            # Option 2: Quotations (simulated cost)
            for col in quotation_columns:
                carrier_key = extract_carrier_name(col)
                
                if not is_carrier_allowed(carrier_key, airport, broker, st.session_state.restriction_rules):
                    continue
                
                if col not in row.index or pd.isna(row[col]) or row[col] <= 0:
                    continue
                
                freight_quot = float(row[col])
                
                # Get CC for simulation
                cc_sim = get_cc_for_simulation(airport, broker, df_broker, customs_custom)
                discount = calculate_anjun_discount(carrier_key, broker, anjun_discount, apply_anjun_discount)
                cc_sim = max(0, cc_sim - discount)
                
                options.append({
                    "idx": idx,
                    "state": row["estado"],
                    "airport": airport,
                    "broker": broker,
                    "carrier_current": carrier_current,
                    "carrier": carrier_key.capitalize(),
                    "carrier_lower": carrier_key.lower(),
                    "broker_lower": broker.lower(),
                    "freight_unit": freight_quot,
                    "cc": cc_sim,
                    "cost_unit": freight_quot + cc_sim,
                    "freight_real": f_real,
                    "cc_real": cc_real,
                    "cost_real": cost_real,
                    "qty": row["qtd_pacotes_total"],
                    "type": "QUOTATION"
                })
        
        # Sort by cost (greedy: lowest first)
        options.sort(key=lambda x: x["cost_unit"])
        
        # Allocate
        vol_per_group = {idx: row["qtd_pacotes_total"] for idx, row in df_agg.iterrows()}
        allocated = {idx: 0 for idx in vol_per_group}
        allocations = []
        
        for opt in options:
            idx = opt["idx"]
            remaining = vol_per_group[idx] - allocated[idx]
            if remaining <= 0:
                continue
            
            cap_c = cap_carrier.get(opt["carrier_lower"], float("inf"))
            cap_b = cap_broker.get(opt["broker_lower"], float("inf"))
            
            if cap_c <= 0 or cap_b <= 0:
                continue
            
            alloc = min(remaining, cap_c, cap_b)
            
            if alloc > 0:
                cost_total_sim = round(opt["cost_unit"] * alloc, 2)
                cost_total_real = round(opt["cost_real"] * alloc, 2)
                savings = round(cost_total_real - cost_total_sim, 2)
                
                allocations.append({
                    "state": opt["state"],
                    "airport": opt["airport"],
                    "broker": opt["broker"],
                    "carrier_current": opt["carrier_current"],
                    "carrier_simulated": opt["carrier"],
                    "type": opt["type"],
                    "freight_sim": round(opt["freight_unit"], 4),
                    "cc_sim": round(opt["cc"], 4),
                    "cost_unit_sim": round(opt["cost_unit"], 4),
                    "freight_real": round(opt["freight_real"], 4),
                    "cc_real": round(opt["cc_real"], 4),
                    "cost_unit_real": round(opt["cost_real"], 4),
                    "packages": alloc,
                    "cost_total_sim": cost_total_sim,
                    "cost_total_real": cost_total_real,
                    "savings": savings,
                    "changed": opt["carrier"].lower() != opt["carrier_current"].lower()
                })
                
                allocated[idx] += alloc
                cap_carrier[opt["carrier_lower"]] = max(0, cap_c - alloc)
                cap_broker[opt["broker_lower"]] = max(0, cap_b - alloc)
        
        df_alloc = pd.DataFrame(allocations)
        
        if df_alloc.empty:
            st.error("❌ Could not allocate any packages. Limits too restrictive.")
        else:
            st.session_state.df_limits_result = df_alloc
            total_allocated = df_alloc["packages"].sum()
            not_allocated = total_packages_all - total_allocated
            
            if not_allocated > 0:
                st.warning(f"⚠️ {not_allocated:,} packages not allocated ({not_allocated / total_packages_all * 100:.1f}%)")
            
            st.success(f"✅ Allocated {total_allocated:,} of {total_packages_all:,} packages")
    
    # Display results
    if "df_limits_result" in st.session_state and not st.session_state.df_limits_result.empty:
        df_alloc = st.session_state.df_limits_result
        
        st.markdown("---")
        st.markdown("### 📊 Results with Limits")
        
        total_alloc = df_alloc["packages"].sum()
        total_cost_sim = df_alloc["cost_total_sim"].sum()
        total_cost_real = df_alloc["cost_total_real"].sum()
        total_savings = df_alloc["savings"].sum()
        savings_pct = (total_savings / total_cost_real * 100) if total_cost_real > 0 else 0
        
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.metric("📦 Allocated", f"{total_alloc:,}")
        with l2:
            st.metric("💰 Real Cost (ref)", fmt_brl(total_cost_real))
        with l3:
            st.metric("💎 Simulated Cost", fmt_brl(total_cost_sim))
        with l4:
            st.markdown(savings_card("Savings", total_savings, savings_pct), unsafe_allow_html=True)
        
        # Share comparison
        st.markdown("#### 📊 Share Comparison")
        col_sh1, col_sh2 = st.columns(2)
        
        with col_sh1:
            st.markdown("##### Current (TMS)")
            share_curr = calculate_share(df_dados)
            if not share_curr.empty:
                fig_curr = px.pie(share_curr, values="Packages", names="Carrier", hole=0.4,
                                  color_discrete_sequence=px.colors.qualitative.Set2)
                fig_curr.update_traces(textposition="inside", textinfo="percent+label")
                fig_curr.update_layout(height=350)
                st.plotly_chart(fig_curr, use_container_width=True, key="lim_sh_curr")
        
        with col_sh2:
            st.markdown("##### Simulated (with Limits)")
            share_sim = df_alloc.groupby("carrier_simulated")["packages"].sum().reset_index()
            share_sim.columns = ["Carrier", "Packages"]
            fig_sim = px.pie(share_sim, values="Packages", names="Carrier", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_sim.update_traces(textposition="inside", textinfo="percent+label")
            fig_sim.update_layout(height=350)
            st.plotly_chart(fig_sim, use_container_width=True, key="lim_sh_sim")
        
        # Share comparison table
        st.markdown("#### 📊 Share Comparison")
        share_curr_dict = {r["Carrier"]: r for _, r in share_curr.iterrows()} if not share_curr.empty else {}
        
        all_carriers_comp = sorted(set(
            list(share_curr_dict.keys()) + share_sim["Carrier"].tolist()
        ))
        
        comparison_data = []
        for c in all_carriers_comp:
            p_curr = share_curr_dict[c]["Packages"] if c in share_curr_dict else 0
            s_curr = (p_curr / total_packages_all * 100) if total_packages_all > 0 else 0
            
            row_sim = share_sim[share_sim["Carrier"] == c]
            p_sim = row_sim["Packages"].values[0] if not row_sim.empty else 0
            s_sim = (p_sim / total_alloc * 100) if total_alloc > 0 else 0
            
            comparison_data.append({
                "Carrier": c,
                "Packages Current": p_curr,
                "Share Current (%)": round(s_curr, 2),
                "Packages Simulated": p_sim,
                "Share Simulated (%)": round(s_sim, 2),
                "Volume Variation": p_sim - p_curr,
                "Share Variation (pp)": round(s_sim - s_curr, 2)
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(
            df_comparison.style.format({
                "Packages Current": "{:,.0f}",
                "Share Current (%)": "{:.2f}%",
                "Packages Simulated": "{:,.0f}",
                "Share Simulated (%)": "{:.2f}%",
                "Volume Variation": "{:+,.0f}",
                "Share Variation (pp)": "{:+.2f}pp"
            }),
            use_container_width=True, hide_index=True
        )
        
        # Savings by state
        st.markdown("#### 💰 Savings by State")
        savings_state_lim = df_alloc.groupby("state").agg(
            packages=("packages", "sum"),
            cost_simulated=("cost_total_sim", "sum"),
            cost_real=("cost_total_real", "sum"),
            savings=("savings", "sum")
        ).reset_index()
        savings_state_lim["savings_pct"] = (
            savings_state_lim["savings"] / savings_state_lim["cost_real"] * 100
        ).round(2)
        savings_state_lim = savings_state_lim.sort_values("savings", ascending=False)
        
        fig_sav_lim = px.bar(
            savings_state_lim, x="state", y="savings",
            text=savings_state_lim["savings"].apply(lambda x: f"R$ {x:,.0f}"),
            color="savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"]
        )
        fig_sav_lim.update_traces(textposition='outside')
        fig_sav_lim.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False,
                                  xaxis_title="State", yaxis_title="Savings (R$)")
        st.plotly_chart(fig_sav_lim, use_container_width=True, key="lim_sav_state")
        
        # Savings by broker
        st.markdown("#### 💰 Savings by Broker")
        savings_broker_lim = df_alloc.groupby("broker").agg(
            packages=("packages", "sum"),
            cost_simulated=("cost_total_sim", "sum"),
            cost_real=("cost_total_real", "sum"),
            savings=("savings", "sum")
        ).reset_index()
        savings_broker_lim["savings_pct"] = (
            savings_broker_lim["savings"] / savings_broker_lim["cost_real"] * 100
        ).round(2)
        savings_broker_lim = savings_broker_lim.sort_values("savings", ascending=False)
        
        st.dataframe(
            savings_broker_lim.rename(columns={
                "broker": "Broker", "packages": "Packages",
                "cost_simulated": "Simulated Cost", "cost_real": "Real Cost",
                "savings": "Savings", "savings_pct": "Savings (%)"
            }).style.format({
                "Packages": "{:,.0f}",
                "Simulated Cost": "R$ {:,.2f}",
                "Real Cost": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}",
                "Savings (%)": "{:.2f}%"
            }),
            use_container_width=True, hide_index=True
        )
        
        # Limit utilization
        st.markdown("#### 📊 Limit Utilization")
        col_util1, col_util2 = st.columns(2)
        
        with col_util1:
            st.markdown("##### 🚚 Carriers")
            util_carrier = df_alloc.groupby("carrier_simulated")["packages"].sum().to_dict()
            util_c_data = []
            for c in carriers_system:
                c_lower = c.lower()
                limit = carrier_limits.get(c_lower)
                alloc = util_carrier.get(c, util_carrier.get(c.capitalize(), 0))
                if limit is None:
                    util_c_data.append({
                        "Carrier": c,
                        "Limit": "No Limit",
                        "Allocated": f"{alloc:,.0f}",
                        "Utilization": "—",
                        "Status": "✅"
                    })
                else:
                    util = (alloc / limit * 100) if limit > 0 else 0
                    status = "🔴" if util >= 95 else "🟡" if util >= 70 else "🟢"
                    util_c_data.append({
                        "Carrier": c,
                        "Limit": f"{limit:,.0f}",
                        "Allocated": f"{alloc:,.0f}",
                        "Utilization": f"{util:.1f}%",
                        "Status": status
                    })
            st.dataframe(pd.DataFrame(util_c_data), use_container_width=True, hide_index=True)
        
        with col_util2:
            st.markdown("##### 📝 Brokers")
            util_broker = df_alloc.groupby("broker")["packages"].sum().to_dict()
            util_b_data = []
            for b in brokers_system:
                b_lower = b.lower()
                limit = broker_limits.get(b_lower)
                alloc = util_broker.get(b, 0)
                if limit is None:
                    util_b_data.append({
                        "Broker": b,
                        "Limit": "No Limit",
                        "Allocated": f"{alloc:,.0f}",
                        "Utilization": "—",
                        "Status": "✅"
                    })
                else:
                    util = (alloc / limit * 100) if limit > 0 else 0
                    status = "🔴" if util >= 95 else "🟡" if util >= 70 else "🟢"
                    util_b_data.append({
                        "Broker": b,
                        "Limit": f"{limit:,.0f}",
                        "Allocated": f"{alloc:,.0f}",
                        "Utilization": f"{util:.1f}%",
                        "Status": status
                    })
            st.dataframe(pd.DataFrame(util_b_data), use_container_width=True, hide_index=True)
        
        # Detail table
        st.markdown("#### 📋 Allocation Detail")
        st.dataframe(
            df_alloc.rename(columns={
                "state": "State", "airport": "Airport", "broker": "Broker",
                "carrier_current": "Current", "carrier_simulated": "Simulated",
                "type": "Type", "freight_sim": "Freight Sim", "cc_sim": "CC Sim",
                "cost_unit_sim": "Cost/Pkg Sim", "freight_real": "Freight Real",
                "cc_real": "CC Real", "cost_unit_real": "Cost/Pkg Real",
                "packages": "Packages", "cost_total_sim": "Total Sim",
                "cost_total_real": "Total Real", "savings": "Savings", "changed": "Changed?"
            }).style.format({
                "Freight Sim": "R$ {:.2f}",
                "CC Sim": "R$ {:.2f}",
                "Cost/Pkg Sim": "R$ {:.2f}",
                "Freight Real": "R$ {:.2f}",
                "CC Real": "R$ {:.2f}",
                "Cost/Pkg Real": "R$ {:.2f}",
                "Packages": "{:,}",
                "Total Sim": "R$ {:,.2f}",
                "Total Real": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}"
            }),
            use_container_width=True, height=400
        )
        
        # Export
        st.markdown("---")
        st.markdown("#### 📥 Export Results")
        export_data_lim = {
            "Allocation_Detail": df_alloc,
            "Savings_by_State": savings_state_lim,
            "Savings_by_Broker": savings_broker_lim,
            "Share_Comparison": df_comparison
        }
        excel_lim = generate_excel(export_data_lim)
        st.download_button(
            "📥 Download Results (Excel)",
            data=excel_lim,
            file_name="limits_simulation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_limits"
        )

# ============================================================
# TAB 5 — STRATEGY BY STATE
# ============================================================
with tab5:
    st.markdown('<div class="sub-header">🗺️ Strategy by State — Real vs Optimized</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        '<strong>Current Cost:</strong> TMS freight + CC from broker sheet (REAL)<br>'
        '<strong>Optimized Cost:</strong> Best quotation + custom CC (when configured)'
        '</div>',
        unsafe_allow_html=True
    )
    
    if customs_custom:
        st.markdown(
            '<div class="warning-box">'
            '⚠️ Custom CC active: optimized cost uses custom values. Current cost uses real CC.'
            '</div>',
            unsafe_allow_html=True
        )
    
    if not quotation_columns:
        st.warning("⚠️ No quotation columns found. Strategy analysis requires quotations.")
    else:
        strategy_data = []
        
        for _, row in df_dados.iterrows():
            qty = row["qtd_pacotes_total"]
            
            # Current real cost
            f_curr, cc_curr, cost_curr_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            cost_curr_total = cost_curr_unit * qty
            
            # Best option
            best_carrier, best_freight, best_cc, best_cost_unit, source = find_best_option(
                row, quotation_columns, df_broker, customs_custom,
                anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
            )
            cost_opt_total = best_cost_unit * qty
            
            strategy_data.append({
                "State": row["estado"],
                "Broker": row["broker"],
                "Airport": row["aeroporto"],
                "Current Carrier": row["transportadora_atual"],
                "Optimized Carrier": best_carrier,
                "Source": source,
                "Packages": qty,
                "Freight TMS": round(f_curr, 4),
                "CC Real": round(cc_curr, 4),
                "Cost/Pkg Current": round(cost_curr_unit, 4),
                "Freight Opt": round(best_freight, 4),
                "CC Opt": round(best_cc, 4),
                "Cost/Pkg Opt": round(best_cost_unit, 4),
                "Total Current": round(cost_curr_total, 2),
                "Total Opt": round(cost_opt_total, 2),
                "Savings": round(cost_curr_total - cost_opt_total, 2)
            })
        
        df_strategy = pd.DataFrame(strategy_data)
        
        # Consolidate by State/Broker/Optimized Carrier
        df_consolidated = df_strategy.groupby(["State", "Broker", "Optimized Carrier"]).agg({
            "Packages": "sum",
            "Total Current": "sum",
            "Total Opt": "sum",
            "Savings": "sum",
            "Airport": lambda x: ", ".join(sorted(set(x))),
            "Current Carrier": lambda x: ", ".join(sorted(set(x))),
            "Source": lambda x: ", ".join(sorted(set(x)))
        }).reset_index()
        
        df_consolidated["Cost/Pkg Current"] = (
            df_consolidated["Total Current"] / df_consolidated["Packages"]
        ).round(4)
        df_consolidated["Cost/Pkg Opt"] = (
            df_consolidated["Total Opt"] / df_consolidated["Packages"]
        ).round(4)
        df_consolidated["Savings (%)"] = (
            df_consolidated["Savings"] / df_consolidated["Total Current"] * 100
        ).round(2)
        df_consolidated = df_consolidated.sort_values(["State", "Savings"], ascending=[True, False])
        
        # Total metrics
        total_packages_strat = df_consolidated["Packages"].sum()
        total_current_strat = df_consolidated["Total Current"].sum()
        total_opt_strat = df_consolidated["Total Opt"].sum()
        total_savings_strat = df_consolidated["Savings"].sum()
        savings_pct_strat = (total_savings_strat / total_current_strat * 100) if total_current_strat > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📦 Packages", f"{total_packages_strat:,.0f}")
        with c2:
            st.metric("💰 Real Cost", fmt_brl(total_current_strat))
        with c3:
            st.metric("💎 Optimized Cost", fmt_brl(total_opt_strat))
        with c4:
            st.markdown(savings_card("Total Savings", total_savings_strat, savings_pct_strat), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display options
        st.markdown("#### 📋 Consolidated Strategic Table")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            show_unit_costs = st.checkbox("Show unit costs", True, key="t5_unit")
            show_current_carrier = st.checkbox("Show current carrier", True, key="t5_curr")
        with col_opt2:
            show_airports = st.checkbox("Show airports", False, key="t5_airports")
            filter_positive = st.checkbox("Only positive savings", False, key="t5_positive")
        
        df_display = df_consolidated.copy()
        if filter_positive:
            df_display = df_display[df_display["Savings"] > 0]
        
        # Build columns to show
        cols_show = ["State", "Broker", "Optimized Carrier", "Source", "Packages",
                     "Total Current", "Total Opt", "Savings", "Savings (%)"]
        if show_unit_costs:
            cols_show.insert(5, "Cost/Pkg Current")
            cols_show.insert(6, "Cost/Pkg Opt")
        if show_current_carrier:
            cols_show.insert(3, "Current Carrier")
        if show_airports:
            cols_show.insert(4, "Airport")
        
        cols_show = [c for c in cols_show if c in df_display.columns]
        
        st.dataframe(
            df_display[cols_show].style.format({
                "Packages": "{:,.0f}",
                "Cost/Pkg Current": "R$ {:.4f}",
                "Cost/Pkg Opt": "R$ {:.4f}",
                "Total Current": "R$ {:,.2f}",
                "Total Opt": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}",
                "Savings (%)": "{:.2f}%"
            }),
            use_container_width=True, height=400
        )
        
        st.markdown("---")
        
        # Summaries
        st.markdown("### 📊 Analysis by Broker and Carrier")
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("#### 📝 Summary by Broker")
            summary_broker = df_consolidated.groupby("Broker").agg({
                "Packages": "sum",
                "Total Current": "sum",
                "Total Opt": "sum",
                "Savings": "sum"
            }).reset_index()
            summary_broker["Savings (%)"] = (
                summary_broker["Savings"] / summary_broker["Total Current"] * 100
            ).round(2)
            summary_broker = summary_broker.sort_values("Savings", ascending=False)
            
            st.dataframe(
                summary_broker.style.format({
                    "Packages": "{:,.0f}",
                    "Total Current": "R$ {:,.2f}",
                    "Total Opt": "R$ {:,.2f}",
                    "Savings": "R$ {:,.2f}",
                    "Savings (%)": "{:.2f}%"
                }),
                use_container_width=True, hide_index=True
            )
        
        with col_r2:
            st.markdown("#### 🚚 Summary by Optimized Carrier")
            summary_carrier = df_consolidated.groupby("Optimized Carrier").agg({
                "Packages": "sum",
                "Total Current": "sum",
                "Total Opt": "sum",
                "Savings": "sum"
            }).reset_index()
            summary_carrier["Share (%)"] = (
                summary_carrier["Packages"] / summary_carrier["Packages"].sum() * 100
            ).round(2)
            summary_carrier["Avg Cost/Pkg"] = (
                summary_carrier["Total Opt"] / summary_carrier["Packages"]
            ).round(4)
            summary_carrier = summary_carrier.sort_values("Packages", ascending=False)
            
            st.dataframe(
                summary_carrier.style.format({
                    "Packages": "{:,.0f}",
                    "Total Current": "R$ {:,.2f}",
                    "Total Opt": "R$ {:,.2f}",
                    "Savings": "R$ {:,.2f}",
                    "Share (%)": "{:.2f}%",
                    "Avg Cost/Pkg": "R$ {:.4f}"
                }),
                use_container_width=True, hide_index=True
            )
        
        # Share charts
        st.markdown("### 📊 Share Comparison: Current vs Optimized")
        cs1, cs2 = st.columns(2)
        
        with cs1:
            st.markdown("#### Current (TMS)")
            share_curr_strat = calculate_share(df_dados)
            if not share_curr_strat.empty:
                fig5a = px.pie(share_curr_strat, values="Packages", names="Carrier",
                               hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig5a.update_traces(textposition="inside", textinfo="percent+label")
                fig5a.update_layout(height=380, margin=dict(t=30, b=30))
                st.plotly_chart(fig5a, use_container_width=True, key="t5_sh_curr")
        
        with cs2:
            st.markdown("#### Optimized")
            if not summary_carrier.empty:
                fig5b = px.pie(summary_carrier, values="Packages", names="Optimized Carrier",
                               hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig5b.update_traces(textposition="inside", textinfo="percent+label")
                fig5b.update_layout(height=380, margin=dict(t=30, b=30))
                st.plotly_chart(fig5b, use_container_width=True, key="t5_sh_opt")
        
        # Savings by state chart
        st.markdown("### 💰 Savings by State")
        savings_state_strat = df_consolidated.groupby("State")["Savings"].sum().reset_index()
        savings_state_strat = savings_state_strat.sort_values("Savings", ascending=False)
        
        fig_sav_strat = px.bar(
            savings_state_strat, x="State", y="Savings",
            text=savings_state_strat["Savings"].apply(lambda x: f"R$ {x:,.0f}"),
            color="Savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"]
        )
        fig_sav_strat.update_traces(textposition='outside')
        fig_sav_strat.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False,
                                    xaxis_title="State", yaxis_title="Savings (R$)")
        st.plotly_chart(fig_sav_strat, use_container_width=True, key="t5_sav_state")
        
        # State analysis
        st.markdown("---")
        st.markdown("### 🔍 Detailed Analysis by State")
        all_states = sorted(df_dados["estado"].unique().tolist())
        filter_states_strat = st.multiselect(
            "Select states for detailed view:",
            all_states,
            default=all_states[:5] if len(all_states) >= 5 else all_states,
            key="t5_state_det"
        )
        
        if filter_states_strat:
            df_filtered_strat = df_consolidated[df_consolidated["State"].isin(filter_states_strat)]
            
            fig_strat = px.bar(
                df_filtered_strat, x="State", y="Packages", color="Optimized Carrier",
                barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2,
                text="Packages"
            )
            fig_strat.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
            fig_strat.update_layout(height=450, margin=dict(t=30, b=30),
                                    xaxis_title="State", yaxis_title="Packages",
                                    legend_title="Optimized Carrier")
            st.plotly_chart(fig_strat, use_container_width=True, key="t5_strat_stack")
        
        # Export
        st.markdown("---")
        st.markdown("#### 📥 Export Strategy")
        export_data_t5 = {
            "Strategy_Consolidated": df_consolidated,
            "Summary_Broker": summary_broker,
            "Summary_Carrier": summary_carrier,
            "Detail": df_strategy
        }
        excel_strat = generate_excel(export_data_t5)
        st.download_button(
            "📥 Download Strategy (Excel)",
            data=excel_strat,
            file_name="strategy_by_state.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_t5"
        )

# ============================================================
# TAB 6 — STATE DETAIL
# ============================================================
with tab6:
    st.markdown('<div class="sub-header">📈 State Analysis</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        'Current Cost = CC REAL from broker sheet. '
        'Best Option = quotation + custom CC (when configured).'
        '</div>',
        unsafe_allow_html=True
    )
    
    state_list = sorted(df_dados["estado"].unique().tolist())
    selected_state = st.selectbox("🗺️ Select State", state_list, key="state_analysis")
    df_state = df_dados[df_dados["estado"] == selected_state].copy()
    
    if df_state.empty:
        st.warning("No data for selected state.")
    else:
        total_packages_state = df_state["qtd_pacotes_total"].sum()
        total_weight_state = df_state["soma_peso_gramas"].sum()
        
        # Calculate total cost for state
        total_cost_state = 0
        total_freight_state = 0
        for _, row in df_state.iterrows():
            f_unit, cc_unit, cost_unit = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            qty = row["qtd_pacotes_total"]
            total_freight_state += f_unit * qty
            total_cost_state += cost_unit * qty
        
        avg_cost_state = total_cost_state / total_packages_state if total_packages_state > 0 else 0
        
        e1, e2, e3, e4 = st.columns(4)
        with e1:
            st.metric("📦 Packages", f"{total_packages_state:,.0f}")
        with e2:
            st.metric("💰 Total Freight", fmt_brl(total_freight_state))
        with e3:
            st.metric("💎 Total Cost", fmt_brl(total_cost_state))
        with e4:
            st.metric("📊 Avg Cost/Pkg", fmt_brl(avg_cost_state))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_6a, col_6b = st.columns(2)
        
        with col_6a:
            st.markdown(f"#### 🚚 Carrier Share — {selected_state}")
            share_state = calculate_share(df_state)
            if not share_state.empty:
                fig_state = px.pie(share_state, values="Packages", names="Carrier", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Set2)
                fig_state.update_traces(textposition="inside", textinfo="percent+label")
                fig_state.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_state, use_container_width=True, key="t6_share")
        
        with col_6b:
            st.markdown(f"#### 📝 Broker Share — {selected_state}")
            share_broker_state = df_state.groupby("broker")["qtd_pacotes_total"].sum().reset_index()
            share_broker_state.columns = ["Broker", "Packages"]
            if not share_broker_state.empty:
                fig_broker = px.pie(share_broker_state, values="Packages", names="Broker", hole=0.4,
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_broker.update_traces(textposition="inside", textinfo="percent+label")
                fig_broker.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_broker, use_container_width=True, key="t6_broker")
        
        # Quotations vs TMS
        st.markdown(f"#### 💰 Quotations vs TMS — {selected_state}")
        quotation_data = []
        for _, r in df_state.iterrows():
            f_unit, cc_unit, cost_unit = calculate_real_cost_unit(
                r, df_broker, anjun_discount, apply_anjun_discount
            )
            
            row_data = {
                "Carrier": r["transportadora_atual"],
                "Broker": r["broker"],
                "Airport": r["aeroporto"],
                "Pkgs": f"{r['qtd_pacotes_total']:,.0f}",
                "Freight TMS": f"R$ {f_unit:.4f}",
                "CC Real": f"R$ {cc_unit:.4f}",
                "Cost/Pkg": f"R$ {cost_unit:.4f}"
            }
            
            for col in quotation_columns:
                carrier_key = extract_carrier_name(col)
                carrier_name = carrier_key.capitalize()
                
                if not is_carrier_allowed(carrier_key, r["aeroporto"], r["broker"],
                                          st.session_state.restriction_rules):
                    row_data[f"Quot.{carrier_name}"] = "🔒"
                elif col in r.index and not pd.isna(r[col]) and r[col] > 0:
                    quot_val = r[col]
                    diff = quot_val - f_unit
                    symbol = "⬇️" if diff < 0 else "⬆️" if diff > 0 else "="
                    row_data[f"Quot.{carrier_name}"] = f"R$ {quot_val:.4f} {symbol}"
                else:
                    row_data[f"Quot.{carrier_name}"] = "—"
            
            quotation_data.append(row_data)
        
        st.dataframe(pd.DataFrame(quotation_data), use_container_width=True, hide_index=True)
        
        # Cost by carrier
        st.markdown(f"#### 💰 Cost by Carrier — {selected_state}")
        carrier_costs_state = []
        for carrier in df_state["transportadora_atual"].unique():
            df_carrier_state = df_state[df_state["transportadora_atual"] == carrier]
            total_f = 0
            total_c = 0
            total_p = 0
            for _, row in df_carrier_state.iterrows():
                f_unit, cc_unit, _ = calculate_real_cost_unit(
                    row, df_broker, anjun_discount, apply_anjun_discount
                )
                qty = row["qtd_pacotes_total"]
                total_f += f_unit * qty
                total_c += cc_unit * qty
                total_p += qty
            carrier_costs_state.append({
                "Carrier": carrier,
                "Packages": total_p,
                "Freight": total_f,
                "CC": total_c,
                "Total": total_f + total_c,
                "Avg Cost/Pkg": (total_f + total_c) / total_p if total_p > 0 else 0
            })
        
        df_carrier_costs_state = pd.DataFrame(carrier_costs_state).sort_values("Total", ascending=False)
        
        fig_cost_state = go.Figure()
        fig_cost_state.add_trace(go.Bar(
            name="Freight TMS",
            x=df_carrier_costs_state["Carrier"],
            y=df_carrier_costs_state["Freight"],
            marker_color="#4FC3F7",
            text=df_carrier_costs_state["Freight"].apply(lambda x: f"R$ {x:,.0f}"),
            textposition="auto"
        ))
        fig_cost_state.add_trace(go.Bar(
            name="CC (Real)",
            x=df_carrier_costs_state["Carrier"],
            y=df_carrier_costs_state["CC"],
            marker_color="#FFB74D",
            text=df_carrier_costs_state["CC"].apply(lambda x: f"R$ {x:,.0f}"),
            textposition="auto"
        ))
        fig_cost_state.update_layout(
            barmode="stack", height=400, margin=dict(t=30, b=30),
            xaxis_title="Carrier", yaxis_title="Cost (R$)"
        )
        st.plotly_chart(fig_cost_state, use_container_width=True, key="t6_cost_stack")
        
        # Best options
        if quotation_columns:
            st.markdown(f"#### 🏆 Best Options — {selected_state}")
            best_options = []
            for _, r in df_state.iterrows():
                f_curr, cc_curr, cost_curr = calculate_real_cost_unit(
                    r, df_broker, anjun_discount, apply_anjun_discount
                )
                
                best_carrier, best_f, best_cc, best_cost, source = find_best_option(
                    r, quotation_columns, df_broker, customs_custom,
                    anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
                )
                
                qty = r["qtd_pacotes_total"]
                cost_curr_total = cost_curr * qty
                cost_opt_total = best_cost * qty
                savings = cost_curr_total - cost_opt_total
                changed = r["transportadora_atual"].strip().lower() != best_carrier.strip().lower()
                
                best_options.append({
                    "Broker": r["broker"],
                    "Airport": r["aeroporto"],
                    "Current Carrier": r["transportadora_atual"],
                    "Freight TMS": f_curr,
                    "CC Real": cc_curr,
                    "Cost/Pkg Current": cost_curr,
                    "Best Carrier": best_carrier,
                    "Source": source,
                    "Freight Opt": best_f,
                    "CC Opt": best_cc,
                    "Cost/Pkg Opt": best_cost,
                    "Packages": qty,
                    "Total Current": cost_curr_total,
                    "Total Opt": cost_opt_total,
                    "Savings": savings,
                    "Changed?": "✅" if changed else "—"
                })
            
            df_best = pd.DataFrame(best_options)
            st.dataframe(
                df_best.style.format({
                    "Freight TMS": "R$ {:.2f}",
                    "CC Real": "R$ {:.2f}",
                    "Cost/Pkg Current": "R$ {:.2f}",
                    "Freight Opt": "R$ {:.2f}",
                    "CC Opt": "R$ {:.2f}",
                    "Cost/Pkg Opt": "R$ {:.2f}",
                    "Packages": "{:,.0f}",
                    "Total Current": "R$ {:,.2f}",
                    "Total Opt": "R$ {:,.2f}",
                    "Savings": "R$ {:,.2f}"
                }),
                use_container_width=True, hide_index=True
            )
            
            # State summary
            total_savings_state = df_best["Savings"].sum()
            total_current_state = df_best["Total Current"].sum()
            savings_pct_state = (total_savings_state / total_current_state * 100) if total_current_state > 0 else 0
            
            st.markdown(f"##### 💰 Total Potential Savings for {selected_state}")
            sav_col1, sav_col2, sav_col3 = st.columns(3)
            with sav_col1:
                st.metric("Current Cost", fmt_brl(total_current_state))
            with sav_col2:
                st.metric("Optimized Cost", fmt_brl(df_best["Total Opt"].sum()))
            with sav_col3:
                st.markdown(savings_card("Savings", total_savings_state, savings_pct_state), unsafe_allow_html=True)

# ============================================================
# TAB 7 — DATA + EXPORT
# ============================================================
with tab7:
    st.markdown('<div class="sub-header">📋 Data and Export</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-box">'
        '<strong>Legend:</strong><br>'
        '• CC from broker sheet = REAL cost (used in Overview and as baseline)<br>'
        '• Custom CC = used ONLY in simulations/optimizations<br>'
        '• <code>media_frete_tms</code> = REAL freight from current carrier<br>'
        '• <code>media_cotacao_*</code> = new quotations for simulation'
        '</div>',
        unsafe_allow_html=True
    )
    
    view_mode = st.radio(
        "View:",
        ["Original Data", "Broker Data", "With Optimization", "Custom CC Summary"],
        horizontal=True,
        key="sub_t7"
    )
    
    if view_mode == "Original Data":
        st.markdown("#### 📊 Data Sheet (dados)")
        st.dataframe(df_dados, use_container_width=True, height=500)
        
    elif view_mode == "Broker Data":
        st.markdown("#### 📝 Broker Sheet (broker)")
        st.dataframe(df_broker, use_container_width=True, height=500)
        
    elif view_mode == "With Optimization":
        st.markdown("#### 🏆 Data with Optimization")
        df_with_opt = df_dados.copy()
        
        # Add calculated columns
        cc_real_list = []
        cost_current_list = []
        best_carrier_list = []
        cost_opt_list = []
        savings_list = []
        source_list = []
        
        for _, row in df_with_opt.iterrows():
            f_curr, cc_curr, cost_curr = calculate_real_cost_unit(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            cc_real_list.append(round(cc_curr, 4))
            cost_current_list.append(round(cost_curr, 4))
            
            if quotation_columns:
                best_carrier, best_f, best_cc, best_cost, source = find_best_option(
                    row, quotation_columns, df_broker, customs_custom,
                    anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
                )
            else:
                best_carrier = row["transportadora_atual"]
                best_cost = cost_curr
                source = "TMS"
            
            best_carrier_list.append(best_carrier)
            cost_opt_list.append(round(best_cost, 4))
            savings_list.append(round(cost_curr - best_cost, 4))
            source_list.append(source)
        
        df_with_opt["cc_real"] = cc_real_list
        df_with_opt["cost_current_unit"] = cost_current_list
        df_with_opt["best_carrier"] = best_carrier_list
        df_with_opt["cost_opt_unit"] = cost_opt_list
        df_with_opt["savings_unit"] = savings_list
        df_with_opt["source"] = source_list
        df_with_opt["savings_total"] = (
            df_with_opt["savings_unit"] * df_with_opt["qtd_pacotes_total"]
        ).round(2)
        
        st.dataframe(df_with_opt, use_container_width=True, height=500)
        
    else:  # Custom CC Summary
        st.markdown("#### 🛃 Custom CC Configuration Summary")
        
        if customs_custom:
            cc_comparison = []
            for key, custom_val in customs_custom.items():
                broker_name, airport_name = key
                real_val = get_customs_clearance(airport_name, broker_name, df_broker)
                diff = custom_val - real_val
                
                # Get volume for this combination
                mask = (df_dados["broker"] == broker_name) & (df_dados["aeroporto"] == airport_name)
                volume = df_dados.loc[mask, "qtd_pacotes_total"].sum()
                impact = diff * volume
                
                cc_comparison.append({
                    "Broker": broker_name,
                    "Airport": airport_name,
                    "Volume": volume,
                    "Real CC (Broker Sheet)": real_val,
                    "Custom CC (Simulation)": custom_val,
                    "Difference": diff,
                    "Total Impact": impact
                })
            
            df_cc_summary = pd.DataFrame(cc_comparison)
            st.dataframe(
                df_cc_summary.style.format({
                    "Volume": "{:,.0f}",
                    "Real CC (Broker Sheet)": "R$ {:.4f}",
                    "Custom CC (Simulation)": "R$ {:.4f}",
                    "Difference": "R$ {:+.4f}",
                    "Total Impact": "R$ {:+,.2f}"
                }),
                use_container_width=True, hide_index=True
            )
            
            # Total impact
            total_impact = df_cc_summary["Total Impact"].sum()
            impact_type = "savings" if total_impact < 0 else "additional cost"
            st.markdown(
                f'<div class="{"success-box" if total_impact < 0 else "warning-box"}">'
                f'<strong>Total Impact:</strong> {fmt_brl(abs(total_impact))} ({impact_type})'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("No custom CC configured. Using real values from broker sheet in all simulations.")
    
    st.markdown("---")
    
    # Restriction rules summary
    st.markdown("#### 🚨 Active Restriction Rules")
    if st.session_state.restriction_rules:
        rules_display = [
            {
                "Carrier": carrier.capitalize(),
                "Allowed Airports": ", ".join([a.upper() for a in rule.get("airports", [])]),
                "Allowed Brokers": ", ".join([b.upper() for b in rule.get("brokers", [])])
            }
            for carrier, rule in st.session_state.restriction_rules.items()
        ]
        st.dataframe(pd.DataFrame(rules_display), use_container_width=True, hide_index=True)
    else:
        st.info("No restriction rules configured.")
    
    st.markdown("---")
    
    # Share by state and carrier
    st.markdown("#### 📊 Share by State and Carrier")
    share_state_carrier = df_dados.groupby(["estado", "transportadora_atual"]).agg(
        packages=("qtd_pacotes_total", "sum")
    ).reset_index()
    
    total_by_state = df_dados.groupby("estado")["qtd_pacotes_total"].sum().reset_index()
    total_by_state.columns = ["estado", "total_state"]
    share_state_carrier = share_state_carrier.merge(total_by_state, on="estado")
    share_state_carrier["share"] = (
        share_state_carrier["packages"] / share_state_carrier["total_state"] * 100
    ).round(2)
    
    # Add average freight
    avg_freight = df_dados.groupby(["estado", "transportadora_atual"])["media_frete_tms"].mean().reset_index()
    avg_freight.columns = ["estado", "transportadora_atual", "avg_freight"]
    share_state_carrier = share_state_carrier.merge(avg_freight, on=["estado", "transportadora_atual"])
    share_state_carrier["avg_freight"] = share_state_carrier["avg_freight"].round(4)
    
    st.dataframe(
        share_state_carrier.rename(columns={
            "estado": "State",
            "transportadora_atual": "Carrier",
            "packages": "Packages",
            "total_state": "State Total",
            "share": "Share (%)",
            "avg_freight": "Avg Freight"
        }).style.format({
            "Share (%)": "{:.2f}%",
            "Avg Freight": "R$ {:.4f}",
            "Packages": "{:,.0f}",
            "State Total": "{:,.0f}"
        }),
        use_container_width=True, height=400
    )
    
    # Heatmap
    st.markdown("#### 🗺️ Heatmap - Average Freight TMS by State and Carrier")
    pivot_freight = share_state_carrier.pivot_table(
        index="estado", columns="transportadora_atual", values="avg_freight", fill_value=0
    )
    
    if not pivot_freight.empty:
        fig_heatmap = px.imshow(
            pivot_freight,
            text_auto=".2f",
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
            labels=dict(x="Carrier", y="State", color="Avg Freight")
        )
        fig_heatmap.update_layout(height=500, margin=dict(t=30, b=30))
        st.plotly_chart(fig_heatmap, use_container_width=True, key="t7_heatmap")
    
    st.markdown("---")
    
    # Export all
    st.markdown("#### 📥 Export All Data")
    export_all = {
        "Data_Original": df_dados,
        "Broker_Data": df_broker,
        "Share_by_Carrier": calculate_share(df_dados),
        "Share_by_State_Carrier": share_state_carrier
    }
    
    if st.session_state.restriction_rules:
        export_all["Restriction_Rules"] = pd.DataFrame(rules_display)
    
    if customs_custom:
        export_all["CC_Custom_vs_Real"] = pd.DataFrame(cc_comparison) if 'cc_comparison' in dir() else pd.DataFrame()
    
    if "df_limits_result" in st.session_state and not st.session_state.df_limits_result.empty:
        export_all["Simulation_Limits"] = st.session_state.df_limits_result
    
    if "df_simulation_result" in st.session_state and not st.session_state.df_simulation_result.empty:
        export_all["Simulation_Volume"] = st.session_state.df_simulation_result
    
    excel_all = generate_excel(export_all)
    
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        st.download_button(
            "📥 Complete Excel",
            data=excel_all,
            file_name="complete_logistics_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_t7_xl"
        )
    with dc2:
        st.download_button(
            "📥 Original CSV",
            data=df_dados.to_csv(index=False).encode("utf-8"),
            file_name="original_data.csv",
            mime="text/csv",
            key="dl_t7_csv"
        )
    with dc3:
        st.download_button(
            "📥 Broker CSV",
            data=df_broker.to_csv(index=False).encode("utf-8"),
            file_name="broker_data.csv",
            mime="text/csv",
            key="dl_t7_broker_csv"
        )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    '<div class="footer">'
    '<p><strong>Logistics Cost Simulator v9.0</strong></p>'
    '<p>Real CC (baseline) vs Custom CC (simulations) | '
    'Anjun discount applied when carrier AND broker are both Anjun</p>'
    '<p style="font-size:0.75rem;color:#aaa;">Built with Streamlit • Data-driven logistics optimization</p>'
    '</div>',
    unsafe_allow_html=True
)
