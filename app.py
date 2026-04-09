import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import re

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
# CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem; font-weight: 700; color: #1E3A5F;
        text-align: center; padding: 1rem 0;
        border-bottom: 3px solid #FF6B35; margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.4rem; font-weight: 600; color: #2C5F8A;
        margin-top: 1.5rem; margin-bottom: 0.8rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem; border-radius: 12px; color: white;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h3 { font-size: 0.85rem; margin-bottom: 0.3rem; opacity: 0.9; }
    .metric-card h2 { font-size: 1.5rem; margin: 0; font-weight: 700; }
    .savings-positive {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem; border-radius: 10px; color: white; text-align: center;
    }
    .savings-negative {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        padding: 1rem; border-radius: 10px; color: white; text-align: center;
    }
    .info-box {
        background: #e3f2fd; border-left: 4px solid #1976d2;
        padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
    }
    .broker-limit-box {
        background: #f8f9fa; border: 2px solid #dee2e6;
        border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .desp-limit-box {
        background: #fff3e0; border: 2px solid #ffe0b2;
        border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .customs-box {
        background: #f3e5f5; border: 2px solid #ce93d8;
        border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .rule-box {
        background: #fce4ec; border: 2px solid #ef9a9a;
        border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .volume-warning {
        background: #fff3cd; border: 2px solid #ffeaa7;
        border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
        color: #856404;
    }
    .volume-ok {
        background: #d1edff; border: 2px solid #74b9ff;
        border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
        color: #0984e3;
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
# INITIALIZE SESSION STATE FOR RESTRICTION RULES
# ============================================================
if "restriction_rules" not in st.session_state:
    st.session_state.restriction_rules = {
        "jt_rec": {"airports": ["rec"], "brokers": ["phx"]},
        "imile_rec": {"airports": ["rec"], "brokers": ["phx"]},
    }

if "partial_carriers" not in st.session_state:
    st.session_state.partial_carriers = {"jt_rec", "imile_rec"}

# ============================================================
# CONSTANTS
# ============================================================
REQUIRED_DATA_COLUMNS = [
    "aeroporto", "broker", "transportadora_atual", "estado",
    "qtd_pacotes_total", "soma_peso_gramas", "media_frete_tms"
]

REQUIRED_BROKER_COLUMNS = ["aeroporto", "broker", "customs_clearance_value_per_package"]

NUMERIC_DATA_COLUMNS = [
    "qtd_pacotes_total", "soma_peso_gramas", "media_frete_tms"
]


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
    airport_str = str(airport).strip().lower()
    broker_str = str(broker).strip().lower()
    
    if cc_df is None or cc_df.empty:
        return default
    
    mask = (
        cc_df["aeroporto"].str.strip().str.lower() == airport_str
    ) & (
        cc_df["broker"].str.strip().str.lower() == broker_str
    )
    
    result = cc_df.loc[mask, "customs_clearance_value_per_package"]
    if not result.empty:
        return result.values[0]
    return default


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
    """Format value as Brazilian Real"""
    return f"R$ {value:,.2f}"


def metric_card(title, value, icon="📊"):
    """Generate HTML for metric card"""
    return f'<div class="metric-card"><h3>{icon} {title}</h3><h2>{value}</h2></div>'


# ============================================================
# COST CALCULATION FUNCTIONS
# ============================================================
def calculate_current_cost(row, cc_df, anjun_discount, apply_anjun_discount):
    """
    Calculate current (real) cost using TMS freight and customs clearance from broker sheet
    """
    qty = row["qtd_pacotes_total"]
    carrier = str(row.get("transportadora_atual", "")).strip()
    broker = str(row.get("broker", "")).strip()
    airport = str(row.get("aeroporto", "")).strip()
    
    freight_unit = row["media_frete_tms"]
    cc_unit = get_customs_clearance(airport, broker, cc_df)
    
    # Apply Anjun discount
    discount = calculate_anjun_discount(carrier, broker, anjun_discount, apply_anjun_discount)
    cc_unit = max(0, cc_unit - discount)
    
    total_freight = freight_unit * qty
    total_cc = cc_unit * qty
    
    return total_freight, total_cc, cc_unit, freight_unit


def calculate_quotation_cost(row, carrier_key, quotation_columns, cc_df, cc_custom,
                              anjun_discount, apply_anjun_discount, rules):
    """
    Calculate simulated cost using quotation and customs clearance (with custom values if set)
    """
    carrier_lower = str(carrier_key).strip().lower()
    airport = str(row.get("aeroporto", "")).strip()
    broker = str(row.get("broker", "")).strip()
    
    # Check restrictions
    if not is_carrier_allowed(carrier_lower, airport, broker, rules):
        return None
    
    # Get quotation column
    col_name = f"media_cotacao_{carrier_lower}"
    if col_name not in row.index or pd.isna(row[col_name]) or row[col_name] <= 0:
        return None
    
    quotation = row[col_name]
    
    # Get customs clearance (use custom value if available for this broker/airport)
    key = (broker, airport)
    if cc_custom and key in cc_custom:
        cc_unit = cc_custom[key]
    else:
        cc_unit = get_customs_clearance(airport, broker, cc_df)
    
    # Apply Anjun discount for simulated carrier
    discount = calculate_anjun_discount(carrier_key, broker, anjun_discount, apply_anjun_discount)
    cc_unit = max(0, cc_unit - discount)
    
    total_unit_cost = quotation + cc_unit
    
    return total_unit_cost, quotation, cc_unit


def find_best_option(row, quotation_columns, cc_df, cc_custom, anjun_discount, 
                     apply_anjun_discount, rules):
    """
    Compare current real cost vs simulated quotation costs
    Baseline = real CC from broker sheet
    Quotations = custom CC when configured
    """
    carrier_current = str(row.get("transportadora_atual", "")).strip()
    broker = str(row.get("broker", "")).strip()
    airport = str(row.get("aeroporto", "")).strip()
    
    freight_current = row["media_frete_tms"]
    cc_current = get_customs_clearance(airport, broker, cc_df)
    
    # Apply Anjun discount for current carrier
    discount_current = calculate_anjun_discount(carrier_current, broker, anjun_discount, apply_anjun_discount)
    cc_current = max(0, cc_current - discount_current)
    
    cost_current = freight_current + cc_current
    
    best_carrier = carrier_current
    best_freight = freight_current
    best_cc = cc_current
    best_cost = cost_current
    best_source = "TMS"
    
    for col in quotation_columns:
        carrier_key = extract_carrier_name(col)
        result = calculate_quotation_cost(
            row, carrier_key, quotation_columns, cc_df, cc_custom,
            anjun_discount, apply_anjun_discount, rules
        )
        if result is None:
            continue
        cost_u, freight_u, cc_u = result
        if cost_u < best_cost:
            best_cost = cost_u
            best_carrier = carrier_key.capitalize()
            best_freight = freight_u
            best_cc = cc_u
            best_source = "QUOTATION"
    
    return best_carrier, best_freight, best_cc, best_cost, best_source


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 📁 Data Upload")
    uploaded_file = st.file_uploader(
        "Upload your data file (Excel with 'dados' and 'broker' sheets)",
        type=["xlsx", "xls"]
    )
    
    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    
    anjun_discount = st.number_input(
        "Anjun Discount (R$/pkg)", value=0.40, step=0.05, format="%.2f",
        help="Discount applied when both carrier AND broker are Anjun"
    )
    
    apply_anjun_discount = st.checkbox(
        "Apply Anjun Discount in Simulations", value=True,
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
    | media_frete_tms | Avg freight/pkg (TMS) |
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
        "media_cotacao_jt_rec": [0, 0, 0, 5.5, 5.8],
        "media_cotacao_imile_rec": [0, 0, 0, 5.3, 5.6],
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
try:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = [s.lower() for s in excel_file.sheet_names]
    
    # Find sheets
    dados_sheet = None
    broker_sheet = None
    
    for sheet in excel_file.sheet_names:
        if sheet.lower() == "dados":
            dados_sheet = sheet
        elif sheet.lower() == "broker":
            broker_sheet = sheet
    
    if dados_sheet is None:
        st.error("❌ Sheet 'dados' not found in the Excel file.")
        st.stop()
    
    if broker_sheet is None:
        st.error("❌ Sheet 'broker' not found in the Excel file.")
        st.stop()
    
    df_dados_raw = pd.read_excel(uploaded_file, sheet_name=dados_sheet)
    df_broker_raw = pd.read_excel(uploaded_file, sheet_name=broker_sheet)
    
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

# Normalize and map columns
df_dados = map_columns(normalize_columns(df_dados_raw.copy()))
df_broker = map_columns(normalize_columns(df_broker_raw.copy()))

# Validate required columns - dados
missing_dados = [c for c in REQUIRED_DATA_COLUMNS if c not in df_dados.columns]
if missing_dados:
    st.error(f"❌ Missing columns in 'dados' sheet: **{', '.join(missing_dados)}**")
    st.stop()

# Validate required columns - broker
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
    st.warning("⚠️ No quotation columns (media_cotacao_*) found. Optimization features will be limited.")

# Store in session state
if ("df_dados_original" not in st.session_state or 
    "last_file" not in st.session_state or 
    st.session_state.last_file != uploaded_file.name):
    st.session_state.df_dados_original = df_dados.copy()
    st.session_state.df_broker_original = df_broker.copy()
    st.session_state.last_file = uploaded_file.name
    # Clear previous results
    for key in ["df_limits_result", "customs_custom", "df_simulation_result",
                "simulated_cost_total", "current_cost_total_sim", "sim_edits"]:
        if key in st.session_state:
            del st.session_state[key]

df_dados = st.session_state.df_dados_original.copy()
df_broker = st.session_state.df_broker_original.copy()

# ============================================================
# CUSTOMS CLEARANCE CONFIGURATION
# ============================================================
st.markdown('<div class="sub-header">🛃 Customs Clearance Cost by Broker / Airport</div>',
            unsafe_allow_html=True)

st.markdown(
    '<div class="info-box">'
    '<strong>⚠️ Important:</strong> Custom values below affect <strong>ONLY simulations '
    'and optimizations</strong>.<br>'
    'The <strong>current real cost</strong> (Overview tab) always uses the original '
    'values from the broker sheet.<br><br>'
    '<strong>Summary:</strong><br>'
    '• 📊 <strong>Overview</strong> → Original CC from broker sheet (real cost)<br>'
    '• 🏆 <strong>Optimization</strong> → current = real | optimized = custom<br>'
    '• 🔄 <strong>Simulator</strong> → current = real | simulated = custom<br>'
    '• 🎯 <strong>Limits</strong> → reference = real | allocation = custom<br>'
    '• 🗺️ <strong>Strategy</strong> → current = real | optimized = custom'
    '</div>',
    unsafe_allow_html=True
)

# Get unique broker/airport pairs from data
broker_airport_pairs = df_dados.groupby(["broker", "aeroporto"]).agg(
    packages=("qtd_pacotes_total", "sum")
).reset_index()

# Merge with broker sheet to get CC values
broker_airport_pairs = broker_airport_pairs.merge(
    df_broker[["broker", "aeroporto", "customs_clearance_value_per_package"]],
    on=["broker", "aeroporto"],
    how="left"
)
broker_airport_pairs["customs_clearance_value_per_package"] = broker_airport_pairs[
    "customs_clearance_value_per_package"
].fillna(0)

if "customs_custom" not in st.session_state:
    st.session_state.customs_custom = {}

use_custom_cc = st.checkbox(
    "✏️ Customize customs clearance costs (affects only simulations)",
    value=len(st.session_state.customs_custom) > 0,
    key="cb_custom_cc"
)

customs_custom = {}

if use_custom_cc:
    st.markdown("#### Edit Values (affects only simulations):")
    
    n_pairs = len(broker_airport_pairs)
    
    if n_pairs <= 8:
        cols_cc = st.columns(min(n_pairs, 4))
        for i, (idx, row) in enumerate(broker_airport_pairs.iterrows()):
            ci = i % len(cols_cc)
            with cols_cc[ci]:
                broker_name = row["broker"]
                airport_name = row["aeroporto"]
                packages = row["packages"]
                cc_original = row["customs_clearance_value_per_package"]
                
                # Get custom value if exists
                key = (broker_name, airport_name)
                cc_default = st.session_state.customs_custom.get(key, cc_original)
                
                st.markdown(
                    f'<div class="customs-box">'
                    f'<strong>📝 {broker_name}</strong> | <strong>✈️ {airport_name}</strong><br>'
                    f'<small>Volume: {packages:,.0f} pkgs | Original: R$ {cc_original:.4f}</small>'
                    f'</div>', unsafe_allow_html=True
                )
                
                new_cost = st.number_input(
                    f"R$/pkg ({broker_name}|{airport_name})",
                    value=float(cc_default),
                    step=0.05,
                    format="%.4f",
                    key=f"cc_{broker_name}_{airport_name}"
                )
                customs_custom[(broker_name, airport_name)] = new_cost
    else:
        df_cc_edit = broker_airport_pairs.copy()
        for idx, row in df_cc_edit.iterrows():
            key = (row["broker"], row["aeroporto"])
            if key in st.session_state.customs_custom:
                df_cc_edit.loc[idx, "customs_clearance_value_per_package"] = st.session_state.customs_custom[key]
        
        df_cc_edit = df_cc_edit.rename(columns={
            "broker": "Broker", "aeroporto": "Airport",
            "packages": "Packages (vol.)", "customs_clearance_value_per_package": "CC Cost (R$/pkg)"
        })
        
        edited_cc = st.data_editor(
            df_cc_edit, use_container_width=True, num_rows="fixed", key="cc_editor",
            column_config={
                "Broker": st.column_config.TextColumn(disabled=True),
                "Airport": st.column_config.TextColumn(disabled=True),
                "Packages (vol.)": st.column_config.NumberColumn(disabled=True, format="%d"),
                "CC Cost (R$/pkg)": st.column_config.NumberColumn(format="%.4f", min_value=0.0, step=0.05)
            }
        )
        for _, row in edited_cc.iterrows():
            customs_custom[(row["Broker"], row["Airport"])] = row["CC Cost (R$/pkg)"]
    
    st.session_state.customs_custom = customs_custom
    
    if customs_custom:
        st.markdown("##### ✅ Custom Costs (used only in simulations):")
        summary_cc = pd.DataFrame([
            {
                "Broker": k[0], "Airport": k[1],
                "Custom CC": v,
                "Original CC": broker_airport_pairs[
                    (broker_airport_pairs["broker"] == k[0]) & 
                    (broker_airport_pairs["aeroporto"] == k[1])
                ]["customs_clearance_value_per_package"].values[0] if len(broker_airport_pairs[
                    (broker_airport_pairs["broker"] == k[0]) & 
                    (broker_airport_pairs["aeroporto"] == k[1])
                ]) > 0 else 0
            }
            for k, v in customs_custom.items()
        ])
        st.dataframe(
            summary_cc.style.format({"Custom CC": "R$ {:.4f}", "Original CC": "R$ {:.4f}"}),
            use_container_width=True, hide_index=True
        )
else:
    customs_custom = {}
    st.session_state.customs_custom = {}
    st.caption("Using original CC values from broker sheet in all tabs.")

st.markdown("---")

# ============================================================
# RESTRICTION RULES EDITOR
# ============================================================
st.markdown('<div class="sub-header">🚨 Carrier Restriction Rules</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="info-box">'
    'Configure which carriers have geographic/broker restrictions. '
    'Restricted carriers can only be used when specific airport AND broker conditions are met.'
    '</div>', unsafe_allow_html=True
)

with st.expander("✏️ Edit Restriction Rules", expanded=False):
    st.markdown("#### Current Rules")
    
    rules_data = []
    for carrier, rule in st.session_state.restriction_rules.items():
        rules_data.append({
            "Carrier": carrier,
            "Airports (comma-separated)": ", ".join(rule.get("airports", [])),
            "Brokers (comma-separated)": ", ".join(rule.get("brokers", []))
        })
    
    if rules_data:  
        df_rules = pd.DataFrame(rules_data)
        st.dataframe(df_rules, use_container_width=True, hide_index=True)
    else:
        st.info("No restriction rules configured.")
    
    st.markdown("---")
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
        if st.button("➕ Add/Update Rule", key="btn_add_rule"):
            if new_carrier.strip():
                airports_list = [a.strip().lower() for a in new_airports.split(",") if a.strip()]
                brokers_list = [b.strip().lower() for b in new_brokers.split(",") if b.strip()]
                st.session_state.restriction_rules[new_carrier.strip().lower()] = {
                    "airports": airports_list,
                    "brokers": brokers_list
                }
                st.success(f"✅ Rule for '{new_carrier}' saved!")
                st.rerun()
            else:
                st.warning("Please enter a carrier name.")
    
    with col_btn2:
        rule_to_delete = st.selectbox(
            "Select rule to delete",
            [""] + list(st.session_state.restriction_rules.keys()),
            key="rule_delete"
        )
        if st.button("🗑️ Delete Rule", key="btn_delete_rule"):
            if rule_to_delete and rule_to_delete in st.session_state.restriction_rules:
                del st.session_state.restriction_rules[rule_to_delete]
                st.success(f"✅ Rule for '{rule_to_delete}' deleted!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("#### Partial Coverage Carriers")
    st.caption("Carriers with limited geographic coverage (marked with ⚠️)")
    
    partial_str = ", ".join(st.session_state.partial_carriers)
    new_partial = st.text_input("Partial carriers (comma-separated)", value=partial_str)
    
    if st.button("💾 Save Partial Carriers", key="btn_save_partial"):
        st.session_state.partial_carriers = {
            p.strip().lower() for p in new_partial.split(",") if p.strip()
        }
        st.success("✅ Partial carriers updated!")


# Display current rules summary
if st.session_state.restriction_rules:
    st.markdown("#### 📋 Active Rules Summary")
    for carrier, rule in st.session_state.restriction_rules.items():
        airports_str = ", ".join([a.upper() for a in rule.get("airports", [])])
        brokers_str = ", ".join([b.upper() for b in rule.get("brokers", [])])
        st.markdown(
            f'<div class="rule-box">'
            f'<strong>🚚 {carrier.upper()}</strong><br>'
            f'✈️ Airports: <strong>{airports_str or "Any"}</strong> | '
            f'📝 Brokers: <strong>{brokers_str or "Any"}</strong>'
            f'</div>', unsafe_allow_html=True
        )

st.markdown("---")

# ============================================================
# CARRIER COVERAGE ANALYSIS
# ============================================================
st.markdown("### 📡 Carrier Coverage and Rules")

coverage_info = []
all_carriers = set()

# From quotation columns
for col in quotation_columns:
    carrier_name = extract_carrier_name(col)
    all_carriers.add(carrier_name)

# From current carriers in data
for carrier in df_dados["transportadora_atual"].unique():
    all_carriers.add(str(carrier).strip().lower())

for carrier in sorted(all_carriers):
    col_name = f"media_cotacao_{carrier}"
    
    if col_name in df_dados.columns:
        total_rows = len(df_dados)
        with_quotation = (df_dados[col_name] > 0).sum()
        coverage_pct = (with_quotation / total_rows * 100) if total_rows > 0 else 0
        
        if carrier in st.session_state.restriction_rules:
            rule = st.session_state.restriction_rules[carrier]
            mask_rule = (
                df_dados["aeroporto"].str.strip().str.lower().isin(rule["airports"]) &
                df_dados["broker"].str.strip().str.lower().isin(rule["brokers"])
            )
            eligible = mask_rule.sum()
            restriction_txt = f"🔒 Restricted ({eligible} eligible)"
        else:
            eligible = total_rows
            restriction_txt = "✅ No restriction"
        
        partial = "⚠️ Partial" if carrier in st.session_state.partial_carriers else "✅ Complete"
        states_covered = df_dados[df_dados[col_name] > 0]["estado"].nunique()
        
        coverage_info.append({
            "Carrier": carrier.capitalize(),
            "Column": col_name,
            "Rows w/ Quotation": with_quotation,
            "Eligible": eligible,
            "Coverage (%)": round(coverage_pct, 1),
            "States": states_covered,
            "Type": partial,
            "Restriction": restriction_txt
        })
    else:
        # Carrier exists only in transportadora_atual
        current_count = (df_dados["transportadora_atual"].str.strip().str.lower() == carrier).sum()
        if current_count > 0:
            coverage_info.append({
                "Carrier": carrier.capitalize(),
                "Column": "TMS only",
                "Rows w/ Quotation": 0,
                "Eligible": current_count,
                "Coverage (%)": 0,
                "States": df_dados[df_dados["transportadora_atual"].str.strip().str.lower() == carrier]["estado"].nunique(),
                "Type": "✅ Current",
                "Restriction": "N/A"
            })

if coverage_info:
    st.dataframe(pd.DataFrame(coverage_info), use_container_width=True, hide_index=True)

st.markdown(
    '<div class="info-box">'
    '📌 <code>media_frete_tms</code> + CC from broker sheet = REAL cost (baseline)<br>'
    '📌 <code>media_cotacao_*</code> + custom CC = SIMULATED cost (optimization)'
    '</div>', unsafe_allow_html=True
)
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
        'All values below use <strong>CC from the broker sheet</strong> (real cost). '
        'Custom CC settings do <strong>NOT</strong> affect this tab.'
        '</div>', unsafe_allow_html=True
    )
    
    total_packages = df_dados["qtd_pacotes_total"].sum()
    total_weight = df_dados["soma_peso_gramas"].sum()
    
    # Calculate total costs
    total_freight = 0
    total_cc = 0
    for _, row in df_dados.iterrows():
        f, c, _, _ = calculate_current_cost(row, df_broker, anjun_discount, apply_anjun_discount)
        total_freight += f
        total_cc += c
    
    total_cost = total_freight + total_cc
    avg_cost = total_cost / total_packages if total_packages > 0 else 0
    
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        st.markdown(metric_card("Total Packages", f"{total_packages:,.0f}", "📦"), unsafe_allow_html=True)
    with r1c2:
        st.markdown(metric_card("Total Freight (TMS)", fmt_brl(total_freight), "💰"), unsafe_allow_html=True)
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
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🚚 Share by Carrier (Current)")
        share = calculate_share(df_dados)
        if not share.empty:
            fig1 = px.pie(share, values="Packages", names="Carrier",
                          color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            fig1.update_layout(height=400, margin=dict(t=30, b=30))
            st.plotly_chart(fig1, use_container_width=True, key="t1_share")
    
    with col_b:
        st.markdown("#### 💰 Freight Cost by Carrier")
        carrier_costs = []
        for carrier in df_dados["transportadora_atual"].unique():
            df_carrier = df_dados[df_dados["transportadora_atual"] == carrier]
            total_f = 0
            total_p = 0
            for _, row in df_carrier.iterrows():
                f, _, _, _ = calculate_current_cost(row, df_broker, anjun_discount, apply_anjun_discount)
                total_f += f
                total_p += row["qtd_pacotes_total"]
            carrier_costs.append({
                "Carrier": carrier,
                "Freight": total_f,
                "Packages": total_p,
                "Avg Freight": total_f / total_p if total_p > 0 else 0
            })
        
        df_carrier_costs = pd.DataFrame(carrier_costs).sort_values("Freight", ascending=True)
        fig2 = px.bar(df_carrier_costs, x="Freight", y="Carrier", orientation="h",
                      text=df_carrier_costs["Freight"].apply(lambda x: f"R$ {x:,.2f}"),
                      color="Carrier", color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=400, margin=dict(t=30, b=30), showlegend=False, yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True, key="t1_cost")
    
    st.markdown("#### 🗺️ Volume by State")
    vol_state = df_dados.groupby("estado")["qtd_pacotes_total"].sum().reset_index()
    vol_state = vol_state.sort_values("qtd_pacotes_total", ascending=False)
    fig3 = px.bar(vol_state, x="estado", y="qtd_pacotes_total",
                  text=vol_state["qtd_pacotes_total"].apply(lambda x: f"{x:,.0f}"),
                  color="qtd_pacotes_total", color_continuous_scale="Blues")
    fig3.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False,
                       xaxis_title="State", yaxis_title="Packages")
    st.plotly_chart(fig3, use_container_width=True, key="t1_vol_state")
    
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("#### ✈️ Volume by Airport")
        vol_airport = df_dados.groupby("aeroporto")["qtd_pacotes_total"].sum().reset_index()
        fig4 = px.pie(vol_airport, values="qtd_pacotes_total", names="aeroporto",
                      color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
        fig4.update_traces(textposition="inside", textinfo="percent+label")
        fig4.update_layout(height=350, margin=dict(t=30, b=30))
        st.plotly_chart(fig4, use_container_width=True, key="t1_airport")
    
    with col_d:
        st.markdown("#### 📝 Volume by Broker")
        vol_broker = df_dados.groupby("broker")["qtd_pacotes_total"].sum().reset_index()
        fig5 = px.pie(vol_broker, values="qtd_pacotes_total", names="broker",
                      color_discrete_sequence=px.colors.qualitative.Pastel1, hole=0.4)
        fig5.update_traces(textposition="inside", textinfo="percent+label")
        fig5.update_layout(height=350, margin=dict(t=30, b=30))
        st.plotly_chart(fig5, use_container_width=True, key="t1_broker")
    
    st.markdown("#### 🚚 Volume by State and Carrier")
    vol_state_carrier = df_dados.groupby(["estado", "transportadora_atual"])["qtd_pacotes_total"].sum().reset_index()
    fig6 = px.bar(vol_state_carrier, x="estado", y="qtd_pacotes_total", color="transportadora_atual",
                  barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2)
    fig6.update_layout(height=450, margin=dict(t=30, b=30),
                       xaxis_title="State", yaxis_title="Packages", legend_title="Carrier")
    st.plotly_chart(fig6, use_container_width=True, key="t1_stack")

# ============================================================
# TAB 2 — OPTIMIZATION
# ============================================================
with tab2:
    st.markdown('<div class="sub-header">🏆 Optimization: Real Cost vs New Quotations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">'
        f'<strong>Current Cost:</strong> <code>media_frete_tms</code> + CC from broker sheet (REAL)<br>'
        f'<strong>Optimized Cost:</strong> best quotation + custom CC (when configured)<br>'
        f'<strong>Anjun Discount:</strong> R$ {anjun_discount:.2f}/pkg '
        f'({"enabled" if apply_anjun_discount else "disabled"})'
        '</div>', unsafe_allow_html=True
    )
    
    if not quotation_columns:
        st.warning("⚠️ No quotation columns found. Cannot perform optimization.")
    else:
        results = []
        for _, row in df_dados.iterrows():
            # Current real cost
            f_curr, cc_curr, cc_unit, f_unit = calculate_current_cost(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            cost_current_total = f_curr + cc_curr
            cost_current_unit = f_unit + cc_unit
            
            # Best option
            best_carrier, best_freight, best_cc, best_cost_unit, source = find_best_option(
                row, quotation_columns, df_broker, customs_custom,
                anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
            )
            
            qty = row["qtd_pacotes_total"]
            cost_optimized_total = best_cost_unit * qty
            
            results.append({
                "state": row["estado"],
                "airport": row["aeroporto"],
                "broker": row["broker"],
                "current_carrier": row["transportadora_atual"],
                "freight_tms": f_unit,
                "cc_real": cc_unit,
                "cost_unit_current": cost_current_unit,
                "cost_total_current": cost_current_total,
                "best_carrier": best_carrier,
                "source": source,
                "freight_unit_opt": best_freight,
                "cc_opt": best_cc,
                "cost_unit_opt": best_cost_unit,
                "cost_total_opt": cost_optimized_total,
                "savings": cost_current_total - cost_optimized_total,
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
            st.metric("Current Cost (Real)", fmt_brl(total_current))
        with o2:
            st.metric("Optimized Cost", fmt_brl(total_optimized))
        with o3:
            css_class = "savings-positive" if total_savings >= 0 else "savings-negative"
            st.markdown(
                f'<div class="{css_class}"><h3>💰 Potential Savings</h3>'
                f'<h2>{fmt_brl(total_savings)}</h2><p>{savings_pct:.1f}%</p></div>',
                unsafe_allow_html=True
            )
        with o4:
            st.metric("Lines Changed", f"{df_results['changed'].sum()} of {len(df_results)}")
        
        if customs_custom:
            st.markdown(
                '<div class="volume-warning">'
                '⚠️ Custom CC active: optimized cost uses custom values. '
                'Current cost uses real CC from broker sheet.'
                '</div>', unsafe_allow_html=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 💰 Savings by State")
        savings_state = df_results.groupby("state").agg(
            savings=("savings", "sum"),
            cost_current=("cost_total_current", "sum"),
            packages=("packages", "sum")
        ).reset_index()
        savings_state = savings_state.sort_values("savings", ascending=False)
        
        fig_savings = px.bar(savings_state, x="state", y="savings",
                             text=savings_state["savings"].apply(lambda x: f"R$ {x:,.2f}"),
                             color="savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"])
        fig_savings.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False,
                                  xaxis_title="State", yaxis_title="Savings (R$)")
        st.plotly_chart(fig_savings, use_container_width=True, key="t2_savings")
        
        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("#### Current Share (TMS)")
            share_current = df_results.groupby("current_carrier")["packages"].sum().reset_index()
            share_current.columns = ["Carrier", "Packages"]
            share_current["Share (%)"] = (share_current["Packages"] / share_current["Packages"].sum() * 100).round(2)
            
            fig_share_curr = px.pie(share_current, values="Packages", names="Carrier", hole=0.4,
                                    color_discrete_sequence=px.colors.qualitative.Set2)
            fig_share_curr.update_traces(textposition="inside", textinfo="percent+label")
            fig_share_curr.update_layout(height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_share_curr, use_container_width=True, key="t2_share_curr")
        
        with col_f:
            st.markdown("#### Optimized Share")
            share_opt = df_results.groupby("best_carrier")["packages"].sum().reset_index()
            share_opt.columns = ["Carrier", "Packages"]
            share_opt["Share (%)"] = (share_opt["Packages"] / share_opt["Packages"].sum() * 100).round(2)
            
            fig_share_opt = px.pie(share_opt, values="Packages", names="Carrier", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Set2)
            fig_share_opt.update_traces(textposition="inside", textinfo="percent+label")
            fig_share_opt.update_layout(height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_share_opt, use_container_width=True, key="t2_share_opt")
        
        st.markdown("#### 📋 Optimization Table")
        df_display = df_results.copy()
        df_display["changed_txt"] = df_display["changed"].apply(lambda x: "✅" if x else "—")
        
        st.dataframe(
            df_display.drop(columns=["changed"]).rename(columns={
                "state": "State", "airport": "Airport", "broker": "Broker",
                "current_carrier": "Current Carrier", "freight_tms": "Freight TMS",
                "cc_real": "CC Real", "cost_unit_current": "Cost/Pkg Current",
                "cost_total_current": "Total Cost Current", "best_carrier": "Best Carrier",
                "source": "Source", "freight_unit_opt": "Freight Opt.", "cc_opt": "CC Opt.",
                "cost_unit_opt": "Cost/Pkg Opt.", "cost_total_opt": "Total Cost Opt.",
                "savings": "Savings", "packages": "Packages", "changed_txt": "Changed?"
            }).style.format({
                "Freight TMS": "R$ {:.4f}", "CC Real": "R$ {:.4f}", "Cost/Pkg Current": "R$ {:.4f}",
                "Total Cost Current": "R$ {:,.2f}", "Freight Opt.": "R$ {:.4f}", "CC Opt.": "R$ {:.4f}",
                "Cost/Pkg Opt.": "R$ {:.4f}", "Total Cost Opt.": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}", "Packages": "{:,.0f}"
            }), use_container_width=True, height=500
        )

# ============================================================
# TAB 3 — SIMULATOR
# ============================================================
with tab3:
    st.markdown('<div class="sub-header">🔄 Volume Redistribution Simulator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">'
        '<strong>Complete Simulator:</strong><br>'
        '• Current Cost = <code>media_frete_tms</code> + CC from broker sheet (REAL)<br>'
        '• Simulated Cost = new quotation + custom CC (when configured)<br>'
        '• Change Airport, Broker and/or Carrier per line<br>'
        '• Carrier filtered by State coverage + restrictions'
        '</div>', unsafe_allow_html=True
    )
    
    # Build relationship maps
    map_airport_broker = df_dados.groupby("aeroporto")["broker"].apply(
        lambda x: sorted(x.unique().tolist())
    ).to_dict()
    
    map_broker_airport = df_dados.groupby("broker")["aeroporto"].apply(
        lambda x: sorted(x.unique().tolist())
    ).to_dict()
    
    def build_state_coverage_map():
        coverage = {}
        for state in df_dados["estado"].unique():
            df_state = df_dados[df_dados["estado"] == state]
            carriers = set(df_state["transportadora_atual"].str.strip().unique())
            for col in quotation_columns:
                carrier_name = extract_carrier_name(col)
                if (df_state[col] > 0).any():
                    carriers.add(carrier_name.capitalize())
            coverage[state] = sorted(carriers)
        return coverage
    
    map_state_coverage = build_state_coverage_map()
    
    def build_quotation_by_state_map():
        quot_map = {}
        for state in df_dados["estado"].unique():
            df_state = df_dados[df_dados["estado"] == state]
            for col in quotation_columns:
                carrier_key = extract_carrier_name(col)
                vals = df_state[df_state[col] > 0][col]
                if not vals.empty:
                    quot_map[(carrier_key, state)] = round(vals.mean(), 4)
        return quot_map
    
    map_quotation_state = build_quotation_by_state_map()
    
    map_freight_tms_state = df_dados.groupby(
        ["transportadora_atual", "estado"]
    )["media_frete_tms"].mean().round(4).to_dict()
    
    # Filters
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
        # Aggregate data
        agg_cols = {
            "qtd_pacotes_total": "sum",
            "soma_peso_gramas": "sum",
            "media_frete_tms": "mean"
        }
        for col in quotation_columns:
            if col in df_filtered.columns:
                agg_cols[col] = "mean"
        
        df_aggregated = df_filtered.groupby(
            ["aeroporto", "broker", "estado", "transportadora_atual"]
        ).agg(agg_cols).reset_index()
        
        # Reference maps expander
        with st.expander("📋 Relationship Maps", expanded=False):
            cm1, cm2 = st.columns(2)
            with cm1:
                st.markdown("#### ✈️ Airport → Brokers")
                map_ab_data = [
                    {"Airport": a, "Brokers": ", ".join(b)}
                    for a, b in sorted(map_airport_broker.items())
                ]
                st.dataframe(pd.DataFrame(map_ab_data), use_container_width=True, hide_index=True)
            with cm2:
                st.markdown("#### 📝 Broker → Airports")
                map_ba_data = [
                    {"Broker": b, "Airports": ", ".join(a)}
                    for b, a in sorted(map_broker_airport.items())
                ]
                st.dataframe(pd.DataFrame(map_ba_data), use_container_width=True, hide_index=True)
        
        with st.expander("🚚 Coverage by State", expanded=False):
            all_carriers_ref = sorted(set(
                list(df_dados["transportadora_atual"].str.strip().unique()) +
                [extract_carrier_name(c).capitalize() for c in quotation_columns]
            ))
            
            coverage_data = []
            for state in sorted(map_state_coverage.keys()):
                carriers_in_state = map_state_coverage[state]
                row_data = {"State": state, "Count": len(carriers_in_state)}
                for carrier in all_carriers_ref:
                    carrier_lower = carrier.lower().replace(" ", "_")
                    quot = map_quotation_state.get((carrier_lower, state))
                    freight = map_freight_tms_state.get((carrier, state))
                    if carrier in carriers_in_state:
                        if quot:
                            row_data[carrier] = f"✅ R${quot:.2f}"
                        elif freight:
                            row_data[carrier] = f"✅ TMS R${freight:.2f}"
                        else:
                            row_data[carrier] = "✅"
                    else:
                        row_data[carrier] = "❌"
                coverage_data.append(row_data)
            st.dataframe(pd.DataFrame(coverage_data), use_container_width=True, hide_index=True, height=400)
        
        # Cost reference table
        st.markdown("### 💰 Cost Reference (CC = Real from broker sheet)")
        ref_rows = []
        for _, row in df_aggregated.iterrows():
            airport = row["aeroporto"]
            broker = row["broker"]
            state = row["estado"]
            carrier_current = row["transportadora_atual"]
            freight_tms = round(row["media_frete_tms"], 4)
            
            # Real CC
            cc_real = get_customs_clearance(airport, broker, df_broker)
            discount = calculate_anjun_discount(carrier_current, broker, anjun_discount, apply_anjun_discount)
            cc_real = max(0, cc_real - discount)
            cc_real = round(cc_real, 4)
            
            cost_current_unit = round(freight_tms + cc_real, 4)
            
            ref = {
                "✈️Airport": airport, "📝Broker": broker, "🗺️State": state,
                "🚚Carrier": carrier_current, "📦Vol": f"{int(row['qtd_pacotes_total']):,}",
                "💰Freight TMS": f"R${freight_tms:.4f}", "🏛️CC Real": f"R${cc_real:.4f}",
                "💎Cost Current": f"R${cost_current_unit:.4f}"
            }
            
            for col in quotation_columns:
                carrier_key = extract_carrier_name(col)
                carrier_name = carrier_key.capitalize()
                
                if not is_carrier_allowed(carrier_key, airport, broker, st.session_state.restriction_rules):
                    ref[f"Quot.{carrier_name}"] = "🔒"
                elif col in row.index and not pd.isna(row[col]) and row[col] > 0:
                    quot_val = round(row[col], 4)
                    
                    # Get CC for simulation (custom if available)
                    key_cc = (broker, airport)
                    if customs_custom and key_cc in customs_custom:
                        cc_sim = customs_custom[key_cc]
                    else:
                        cc_sim = get_customs_clearance(airport, broker, df_broker)
                    
                    discount_sim = calculate_anjun_discount(carrier_key, broker, anjun_discount, apply_anjun_discount)
                    cc_sim = max(0, cc_sim - discount_sim)
                    
                    cost_sim = round(quot_val + cc_sim, 4)
                    diff = round(cost_current_unit - cost_sim, 4)
                    symbol = "🟢" if diff > 0 else "🔴" if diff < 0 else "⚪"
                    ref[f"Quot.{carrier_name}"] = f"{symbol} R${cost_sim:.4f} ({diff:+.4f})"
                else:
                    ref[f"Quot.{carrier_name}"] = "—"
            
            ref_rows.append(ref)
        
        st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, height=300, hide_index=True)
        
        # Line editor
        st.markdown("---")
        st.markdown("### ✏️ Volume Redistribution")
        st.markdown(
            '<div class="info-box">'
            'Adjust Volume, Airport, Broker and Carrier. '
            'Current cost uses REAL CC; simulated uses custom CC (when configured).'
            '</div>', unsafe_allow_html=True
        )
        
        all_airports = sorted(df_dados["aeroporto"].unique().tolist())
        all_brokers = sorted(df_dados["broker"].unique().tolist())
        all_carriers_edit = sorted(set(
            list(df_dados["transportadora_atual"].str.strip().unique()) +
            [extract_carrier_name(c).capitalize() for c in quotation_columns]
        ))
        
        edit_lines = []
        for idx, row in df_aggregated.iterrows():
            cc_real = get_customs_clearance(row["aeroporto"], row["broker"], df_broker)
            discount = calculate_anjun_discount(
                row["transportadora_atual"], row["broker"], anjun_discount, apply_anjun_discount
            )
            cc_real = max(0, cc_real - discount)
            cc_real = round(cc_real, 4)
            cost_unit = round(row["media_frete_tms"] + cc_real, 4)
            
            edit_lines.append({
                "idx_original": idx,
                "airport_current": row["aeroporto"],
                "broker_current": row["broker"],
                "state": row["estado"],
                "carrier_current": row["transportadora_atual"],
                "vol_current": int(row["qtd_pacotes_total"]),
                "freight_tms": round(row["media_frete_tms"], 4),
                "cc_real": cc_real,
                "cost_unit_current": cost_unit,
            })
        
        if "sim_edits" not in st.session_state:
            st.session_state.sim_edits = {}
        
        sim_key = f"sim_{hash(str(filter_states)+str(filter_airports)+str(filter_brokers)+str(filter_carriers))}"
        if "sim_key" not in st.session_state or st.session_state.sim_key != sim_key:
            st.session_state.sim_edits = {}
            st.session_state.sim_key = sim_key
        
        # Header
        st.markdown(
            '<div style="display:grid; grid-template-columns: 0.5fr 0.7fr 0.7fr 0.4fr 0.5fr 0.5fr 0.6fr 0.7fr 0.7fr 0.5fr; '
            'gap:2px; font-weight:bold; font-size:0.7rem; padding:6px 2px; '
            'background:#f0f2f6; border-radius:8px; margin-bottom:2px; text-align:center;">'
            '<div>✈️Airp</div><div>📝Broker</div><div>🚚Carrier</div><div>🗺️UF</div>'
            '<div>📦Curr</div><div>📦Sim✏️</div><div>✈️Dest✏️</div>'
            '<div>📝Dest✏️</div><div>🚚Dest✏️</div><div>💎Cost</div></div>',
            unsafe_allow_html=True
        )
        
        for i, line in enumerate(edit_lines):
            row_key = f"row_{i}"
            edits = st.session_state.sim_edits.get(row_key, {})
            cols = st.columns([0.5, 0.7, 0.7, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7, 0.5])
            
            with cols[0]:
                st.caption(line["airport_current"])
            with cols[1]:
                st.caption(line["broker_current"])
            with cols[2]:
                st.caption(line["carrier_current"])
            with cols[3]:
                st.caption(line["state"])
            with cols[4]:
                st.caption(f"{line['vol_current']:,}")
            with cols[5]:
                vol_sim = st.number_input(
                    "v", value=int(edits.get("vol", line["vol_current"])),
                    min_value=0, step=1, key=f"vol_{i}", label_visibility="collapsed"
                )
            with cols[6]:
                d_airport = edits.get("airport", line["airport_current"])
                ai = all_airports.index(d_airport) if d_airport in all_airports else 0
                airport_dest = st.selectbox(
                    "a", all_airports, index=ai, key=f"airport_{i}", label_visibility="collapsed"
                )
            with cols[7]:
                brokers_available = map_airport_broker.get(airport_dest, all_brokers)
                if not brokers_available:
                    brokers_available = all_brokers
                d_broker = edits.get("broker", line["broker_current"])
                bi = brokers_available.index(d_broker) if d_broker in brokers_available else 0
                broker_dest = st.selectbox(
                    "b", brokers_available, index=bi, key=f"broker_{i}", label_visibility="collapsed"
                )
            with cols[8]:
                carriers_in_state = map_state_coverage.get(line["state"], all_carriers_edit)
                carriers_allowed = [
                    c for c in carriers_in_state
                    if is_carrier_allowed(c.lower().replace(" ", "_"), airport_dest, broker_dest,
                                          st.session_state.restriction_rules)
                ]
                if not carriers_allowed:
                    carriers_allowed = [line["carrier_current"]]
                d_carrier = edits.get("carrier", line["carrier_current"])
                ti = carriers_allowed.index(d_carrier) if d_carrier in carriers_allowed else 0
                carrier_dest = st.selectbox(
                    "t", carriers_allowed, index=ti, key=f"carrier_{i}", label_visibility="collapsed"
                )
            with cols[9]:
                st.caption(f"R${line['cost_unit_current']:.4f}")
            
            st.session_state.sim_edits[row_key] = {
                "vol": vol_sim, "airport": airport_dest, "broker": broker_dest, "carrier": carrier_dest
            }
        
        # Volume control
        st.markdown("---")
        st.markdown("### 📋 Volume Control")
        
        all_edits_data = []
        for i, line in enumerate(edit_lines):
            ed = st.session_state.sim_edits.get(f"row_{i}", {})
            all_edits_data.append({
                "idx": i,
                "airport_current": line["airport_current"],
                "broker_current": line["broker_current"],
                "state": line["state"],
                "carrier_current": line["carrier_current"],
                "vol_current": line["vol_current"],
                "vol_simulated": ed.get("vol", line["vol_current"]),
                "airport_dest": ed.get("airport", line["airport_current"]),
                "broker_dest": ed.get("broker", line["broker_current"]),
                "carrier_dest": ed.get("carrier", line["carrier_current"]),
                "freight_tms": line["freight_tms"],
                "cc_real": line["cc_real"],
                "cost_unit_current": line["cost_unit_current"],
                "idx_original": line["idx_original"],
            })
        
        df_edits = pd.DataFrame(all_edits_data)
        vol_original_total = df_edits["vol_current"].sum()
        vol_simulated_total = df_edits["vol_simulated"].sum()
        vol_diff = vol_simulated_total - vol_original_total
        
        cv1, cv2, cv3 = st.columns(3)
        with cv1:
            st.markdown("#### 📝 Broker Destination")
            for b in sorted(set(df_edits["broker_current"].tolist() + df_edits["broker_dest"].tolist())):
                va = df_edits[df_edits["broker_current"] == b]["vol_current"].sum()
                vs = df_edits[df_edits["broker_dest"] == b]["vol_simulated"].sum()
                d = vs - va
                if vs == 0 and va == 0:
                    continue
                tag = " 🆕" if va == 0 else ""
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{b}**{tag}: {vs:,.0f}/{va:,.0f} ({d:+,.0f}) {arrow}")
        
        with cv2:
            st.markdown("#### 🚚 Carrier Destination")
            for c in sorted(set(df_edits["carrier_current"].tolist() + df_edits["carrier_dest"].tolist())):
                va = df_edits[df_edits["carrier_current"] == c]["vol_current"].sum()
                vs = df_edits[df_edits["carrier_dest"] == c]["vol_simulated"].sum()
                d = vs - va
                if vs == 0 and va == 0:
                    continue
                tag = " 🆕" if va == 0 else ""
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{c}**{tag}: {vs:,.0f}/{va:,.0f} ({d:+,.0f}) {arrow}")
        
        with cv3:
            st.markdown("#### ✈️ Airport Destination")
            for a in sorted(set(df_edits["airport_current"].tolist() + df_edits["airport_dest"].tolist())):
                va = df_edits[df_edits["airport_current"] == a]["vol_current"].sum()
                vs = df_edits[df_edits["airport_dest"] == a]["vol_simulated"].sum()
                d = vs - va
                if vs == 0 and va == 0:
                    continue
                arrow = "⬆️" if d > 0 else "⬇️" if d < 0 else "✅"
                st.markdown(f"• **{a}**: {vs:,.0f}/{va:,.0f} ({d:+,.0f}) {arrow}")
        
        vol_css = "volume-ok" if vol_diff == 0 else "volume-warning"
        st.markdown(
            f'<div class="{vol_css}">Total Volume: {vol_simulated_total:,.0f} / Original: {vol_original_total:,.0f} '
            f'(difference: {vol_diff:+,.0f})</div>', unsafe_allow_html=True
        )
        
        # Calculate button
        st.markdown("---")
        if st.button("🚀 Calculate Simulation", type="primary", key="btn_calc_sim"):
            errors = []
            for _, re in df_edits.iterrows():
                if re["vol_simulated"] == 0:
                    continue
                carrier_key = str(re["carrier_dest"]).lower().replace(" ", "_")
                if not is_carrier_allowed(carrier_key, re["airport_dest"], re["broker_dest"],
                                          st.session_state.restriction_rules):
                    errors.append(
                        f"🔒 {re['carrier_dest']} blocked at {re['airport_dest']}/{re['broker_dest']}"
                    )
                carriers_in_state = map_state_coverage.get(re["state"], [])
                if re["carrier_dest"] not in carriers_in_state:
                    errors.append(f"❌ {re['carrier_dest']} has no coverage in {re['state']}")
            
            if errors:
                for e in errors:
                    st.error(e)
            else:
                simulation_results = []
                cost_current_total = 0
                cost_simulated_total = 0
                
                for _, re in df_edits.iterrows():
                    vol_sim = int(re["vol_simulated"])
                    if vol_sim == 0:
                        continue
                    
                    row_data = df_aggregated.loc[re["idx_original"]]
                    
                    # Current REAL cost
                    freight_curr = re["freight_tms"]
                    cc_curr = re["cc_real"]
                    cost_unit_curr = re["cost_unit_current"]
                    cost_total_curr = round(cost_unit_curr * vol_sim, 2)
                    
                    changed_airport = re["airport_dest"] != re["airport_current"]
                    changed_broker = re["broker_dest"] != re["broker_current"]
                    changed_carrier = re["carrier_dest"].lower() != re["carrier_current"].lower()
                    changed = changed_airport or changed_broker or changed_carrier
                    
                    changes = []
                    if changed_airport:
                        changes.append("Airport")
                    if changed_broker:
                        changes.append("Broker")
                    if changed_carrier:
                        changes.append("Carrier")
                    changes_desc = ", ".join(changes) if changes else "None"
                    
                    carrier_key = re["carrier_dest"].lower().replace(" ", "_")
                    
                    if not changed:
                        freight_new = freight_curr
                        cc_new = cc_curr
                        cost_unit_new = cost_unit_curr
                        sim_type = "TMS (kept)"
                    else:
                        # New freight
                        freight_new = None
                        if changed_carrier:
                            col_name = f"media_cotacao_{carrier_key}"
                            if col_name in row_data.index and not pd.isna(row_data[col_name]) and row_data[col_name] > 0:
                                freight_new = round(row_data[col_name], 4)
                            
                            if freight_new is None:
                                freight_new = map_quotation_state.get((carrier_key, re["state"]))
                            
                            if freight_new is None:
                                freight_new = map_freight_tms_state.get(
                                    (re["carrier_dest"], re["state"]), freight_curr
                                )
                            sim_type = "QUOTATION"
                        else:
                            freight_new = freight_curr
                            sim_type = "TMS (route changed)"
                        
                        # CC for simulation (custom if available for this broker/airport)
                        key_cc = (re["broker_dest"], re["airport_dest"])
                        if customs_custom and key_cc in customs_custom:
                            cc_new = customs_custom[key_cc]
                        else:
                            cc_new = get_customs_clearance(re["airport_dest"], re["broker_dest"], df_broker)
                        
                        # Apply Anjun discount
                        discount = calculate_anjun_discount(
                            re["carrier_dest"], re["broker_dest"], anjun_discount, apply_anjun_discount
                        )
                        cc_new = max(0, cc_new - discount)
                        cc_new = round(cc_new, 4)
                        cost_unit_new = round(freight_new + cc_new, 4)
                    
                    cost_total_new = round(cost_unit_new * vol_sim, 2)
                    savings = round(cost_total_curr - cost_total_new, 2)
                    cost_current_total += cost_total_curr
                    cost_simulated_total += cost_total_new
                    
                    simulation_results.append({
                        "Airport Curr": re["airport_current"],
                        "Broker Curr": re["broker_current"],
                        "State": re["state"],
                        "Carrier Curr": re["carrier_current"],
                        "Airport Dest": re["airport_dest"],
                        "Broker Dest": re["broker_dest"],
                        "Carrier Dest": re["carrier_dest"],
                        "Changes": changes_desc,
                        "Type": sim_type,
                        "Vol. Curr": int(re["vol_current"]),
                        "Vol. Sim": vol_sim,
                        "Freight TMS": freight_curr,
                        "Freight New": freight_new,
                        "CC Real": cc_curr,
                        "CC Sim": cc_new,
                        "Cost/Pkg Curr": cost_unit_curr,
                        "Cost/Pkg New": cost_unit_new,
                        "Cost Total Curr": cost_total_curr,
                        "Cost Total New": cost_total_new,
                        "Savings": savings,
                    })
                
                df_sim_results = pd.DataFrame(simulation_results)
                if df_sim_results.empty:
                    st.warning("No lines with volume > 0.")
                else:
                    st.session_state.df_simulation_result = df_sim_results
                    st.session_state.simulated_cost_total = cost_simulated_total
                    st.session_state.current_cost_total_sim = cost_current_total
                    st.success("✅ Simulation calculated!")
        
        # Display results
        if "df_simulation_result" in st.session_state and not st.session_state.df_simulation_result.empty:
            df_sim_results = st.session_state.df_simulation_result
            cost_curr = st.session_state.current_cost_total_sim
            cost_sim = st.session_state.simulated_cost_total
            total_savings = cost_curr - cost_sim
            savings_pct = (total_savings / cost_curr * 100) if cost_curr > 0 else 0
            
            st.markdown("---")
            st.markdown("### 📊 Results")
            
            if customs_custom:
                st.markdown(
                    '<div class="volume-warning">'
                    '⚠️ Custom CC active: Current Cost uses REAL CC from broker sheet. '
                    'Simulated Cost uses custom CC.'
                    '</div>', unsafe_allow_html=True
                )
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("📦 Volume", f"{df_sim_results['Vol. Sim'].sum():,.0f}")
            with m2:
                st.metric("💰 Current Cost (Real)", fmt_brl(cost_curr))
            with m3:
                st.metric("💎 Simulated Cost", fmt_brl(cost_sim))
            with m4:
                ec_css = "savings-positive" if total_savings >= 0 else "savings-negative"
                st.markdown(
                    f'<div class="{ec_css}"><h3>💰 Savings</h3>'
                    f'<h2>{fmt_brl(total_savings)}</h2><p>{savings_pct:.1f}%</p></div>',
                    unsafe_allow_html=True
                )
            
            st.markdown("#### 📋 Detail")
            st.dataframe(
                df_sim_results.style.format({
                    "Vol. Curr": "{:,.0f}", "Vol. Sim": "{:,.0f}",
                    "Freight TMS": "R$ {:.4f}", "Freight New": "R$ {:.4f}",
                    "CC Real": "R$ {:.4f}", "CC Sim": "R$ {:.4f}",
                    "Cost/Pkg Curr": "R$ {:.4f}", "Cost/Pkg New": "R$ {:.4f}",
                    "Cost Total Curr": "R$ {:,.2f}", "Cost Total New": "R$ {:,.2f}",
                    "Savings": "R$ {:,.2f}",
                                    }), use_container_width=True, height=400
            )
            
            # Shares
            cg1, cg2 = st.columns(2)
            with cg1:
                st.markdown("##### 🚚 Current Carrier Share")
                share_curr = df_sim_results.groupby("Carrier Curr")["Vol. Curr"].sum().reset_index()
                share_curr.columns = ["Carrier", "Packages"]
                fig_curr = px.pie(share_curr, values="Packages", names="Carrier", hole=0.4,
                                  color_discrete_sequence=px.colors.qualitative.Set2)
                fig_curr.update_traces(textposition="inside", textinfo="percent+label")
                fig_curr.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_curr, use_container_width=True, key="s3_curr")
            
            with cg2:
                st.markdown("##### 🚚 Simulated Carrier Share")
                share_sim = df_sim_results.groupby("Carrier Dest")["Vol. Sim"].sum().reset_index()
                share_sim.columns = ["Carrier", "Packages"]
                fig_sim = px.pie(share_sim, values="Packages", names="Carrier", hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_sim.update_traces(textposition="inside", textinfo="percent+label")
                fig_sim.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_sim, use_container_width=True, key="s3_sim")
            
            st.markdown("#### 📥 Export")
            excel_sim = generate_excel({"Simulation": df_sim_results})
            st.download_button(
                "📥 Excel", data=excel_sim, file_name="simulation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_s3"
            )
        
        st.markdown("---")
        if st.button("🔄 Reset", key="reset_sim"):
            st.session_state.sim_edits = {}
            st.session_state.sim_key = ""
            for k in ["df_simulation_result", "simulated_cost_total", "current_cost_total_sim"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("✅ Reset complete!")
            st.rerun()

# ============================================================
# TAB 4 — LIMITS
# ============================================================
with tab4:
    st.markdown('<div class="sub-header">🎯 Limits - Broker and Carrier</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">'
        'Reference cost (current) = CC REAL from broker sheet.<br>'
        'Simulated allocation = custom CC (when configured).'
        '</div>', unsafe_allow_html=True
    )
    
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
    
    # Build carrier list
    carriers_system = []
    for col in quotation_columns:
        carrier_name = extract_carrier_name(col).capitalize()
        if carrier_name not in carriers_system:
            carriers_system.append(carrier_name)
    
    for carrier in df_dados["transportadora_atual"].unique():
        carrier_clean = str(carrier).strip()
        if carrier_clean not in carriers_system and carrier_clean.capitalize() not in carriers_system:
            carriers_system.append(carrier_clean)
    
    carriers_system = sorted(carriers_system)
    brokers_system = sorted(df_dados["broker"].unique().tolist())
    
    # Current volumes
    vol_by_carrier = df_dados.groupby("transportadora_atual")["qtd_pacotes_total"].sum().to_dict()
    vol_by_carrier_lower = {k.lower(): v for k, v in vol_by_carrier.items()}
    vol_by_broker = df_dados.groupby("broker")["qtd_pacotes_total"].sum().to_dict()
    
    # Broker Limits
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
                f'<small>Current: {vol_broker:,.0f} ({share_broker:.1f}%) | {daily_broker:,.0f}/day</small></div>',
                unsafe_allow_html=True
            )
            
            no_limit_b = st.checkbox("No Limit", True, key=f"broker_no_{broker}")
            if no_limit_b:
                broker_limits[broker.lower()] = None
            else:
                limit_type_b = st.radio(
                    "Mode", ["% Vol", "Pkgs/Day", "Total"],
                    horizontal=True, key=f"broker_type_{broker}"
                )
                if limit_type_b == "% Vol":
                    pct = st.number_input(
                        "Max %", 0.0, 100.0, round(share_broker, 1), 1.0,
                        key=f"broker_pct_{broker}"
                    )
                    broker_limits[broker.lower()] = int(total_packages_all * pct / 100)
                elif limit_type_b == "Pkgs/Day":
                    pkgs_day = st.number_input(
                        "Pkgs/day", 0, value=int(daily_broker), step=100,
                        key=f"broker_day_{broker}"
                    )
                    broker_limits[broker.lower()] = pkgs_day * period_days
                else:
                    broker_limits[broker.lower()] = st.number_input(
                        "Total", 0, total_packages_all, int(vol_broker), 100,
                        key=f"broker_total_{broker}"
                    )
    
    st.markdown("---")
    
    # Carrier Limits
    st.markdown("### 🚚 Limits by Carrier")
    st.caption("⚠️ Partial coverage carriers and those with restrictions are marked")
    carrier_limits = {}
    cols_c = st.columns(min(len(carriers_system), 4))
    
    for i, carrier in enumerate(carriers_system):
        ci = i % len(cols_c)
        with cols_c[ci]:
            vol_carrier = vol_by_carrier_lower.get(carrier.lower(), 0)
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
                f'<small>Current: {vol_carrier:,.0f} ({share_carrier:.1f}%) | {daily_carrier:,.0f}/day</small></div>',
                unsafe_allow_html=True
            )
            
            no_limit_c = st.checkbox("No Limit", True, key=f"carrier_no_{carrier}")
            if no_limit_c:
                carrier_limits[carrier.lower()] = None
            else:
                limit_type_c = st.radio(
                    "Mode", ["% Vol", "Pkgs/Day", "Total"],
                    horizontal=True, key=f"carrier_type_{carrier}"
                )
                if limit_type_c == "% Vol":
                    pct = st.number_input(
                        "Max %", 0.0, 100.0, round(share_carrier, 1), 1.0,
                        key=f"carrier_pct_{carrier}"
                    )
                    carrier_limits[carrier.lower()] = int(total_packages_all * pct / 100)
                elif limit_type_c == "Pkgs/Day":
                    pkgs_day = st.number_input(
                        "Pkgs/day", 0, value=int(daily_carrier), step=100,
                        key=f"carrier_day_{carrier}"
                    )
                    carrier_limits[carrier.lower()] = pkgs_day * period_days
                else:
                    carrier_limits[carrier.lower()] = st.number_input(
                        "Total", 0, total_packages_all, int(vol_carrier), 100,
                        key=f"carrier_total_{carrier}"
                    )
    
    st.markdown("---")
    
    # Execute simulation with limits
    if st.button("🚀 Execute with Limits", type="primary", key="btn_limits"):
        # Aggregate data
        agg_cols = {
            "qtd_pacotes_total": "sum",
            "soma_peso_gramas": "sum",
            "media_frete_tms": "mean"
        }
        for col in quotation_columns:
            if col in df_dados.columns:
                agg_cols[col] = "mean"
        
        df_agg = df_dados.groupby(
            ["estado", "aeroporto", "broker", "transportadora_atual"]
        ).agg(agg_cols).reset_index()
        
        # Build capacity dictionaries
        cap_carrier = {
            c.lower(): (
                carrier_limits.get(c.lower())
                if carrier_limits.get(c.lower()) is not None
                else float("inf")
            )
            for c in carriers_system
        }
        
        cap_broker = {
            b.lower(): (
                broker_limits.get(b.lower())
                if broker_limits.get(b.lower()) is not None
                else float("inf")
            )
            for b in brokers_system
        }
        
        # Build allocation options
        options = []
        for idx, row in df_agg.iterrows():
            broker = str(row.get("broker", "")).strip()
            broker_lower = broker.lower()
            airport = str(row.get("aeroporto", "")).strip()
            carrier_current = str(row.get("transportadora_atual", "")).strip()
            
            # Option 1: Quotations (simulated CC)
            for col in quotation_columns:
                carrier_key = extract_carrier_name(col)
                
                if not is_carrier_allowed(carrier_key, airport, broker, st.session_state.restriction_rules):
                    continue
                
                if col not in row.index or pd.isna(row[col]) or row[col] <= 0:
                    continue
                
                freight_unit = row[col]
                
                # CC for simulation (custom if available for this specific broker/airport)
                key_cc = (broker, airport)
                if customs_custom and key_cc in customs_custom:
                    cc_unit = customs_custom[key_cc]
                else:
                    cc_unit = get_customs_clearance(airport, broker, df_broker)
                
                # Apply Anjun discount
                discount = calculate_anjun_discount(
                    carrier_key, broker, anjun_discount, apply_anjun_discount
                )
                cc_unit = max(0, cc_unit - discount)
                
                options.append({
                    "idx": idx,
                    "state": row["estado"],
                    "airport": airport,
                    "broker": broker,
                    "broker_lower": broker_lower,
                    "carrier_current": carrier_current,
                    "carrier": carrier_key.capitalize(),
                    "carrier_lower": carrier_key.lower(),
                    "freight_unit": freight_unit,
                    "cc": cc_unit,
                    "cost_unit": freight_unit + cc_unit,
                    "qty": row["qtd_pacotes_total"],
                    "type": "QUOTATION"
                })
            
            # Option 2: Keep current carrier (real CC)
            freight_current = row["media_frete_tms"]
            cc_current = get_customs_clearance(airport, broker, df_broker)
            discount_current = calculate_anjun_discount(
                carrier_current, broker, anjun_discount, apply_anjun_discount
            )
            cc_current = max(0, cc_current - discount_current)
            carrier_current_lower = carrier_current.lower().replace(" ", "_")
            
            options.append({
                "idx": idx,
                "state": row["estado"],
                "airport": airport,
                "broker": broker,
                "broker_lower": broker_lower,
                "carrier_current": carrier_current,
                "carrier": carrier_current,
                "carrier_lower": carrier_current_lower,
                "freight_unit": freight_current,
                "cc": cc_current,
                "cost_unit": freight_current + cc_current,
                "qty": row["qtd_pacotes_total"],
                "type": "TMS"
            })
        
        # Sort by unit cost (greedy: lowest first)
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
            
            cap_c_remaining = cap_carrier.get(opt["carrier_lower"], float("inf"))
            cap_b_remaining = cap_broker.get(opt["broker_lower"], float("inf"))
            
            if cap_c_remaining <= 0 or cap_b_remaining <= 0:
                continue
            
            alloc = min(remaining, cap_c_remaining, cap_b_remaining)
            
            if alloc > 0:
                # Reference cost (real from broker sheet)
                freight_ref = df_agg.loc[idx, "media_frete_tms"]
                carrier_current_ref = df_agg.loc[idx, "transportadora_atual"]
                broker_ref = df_agg.loc[idx, "broker"]
                airport_ref = df_agg.loc[idx, "aeroporto"]
                
                cc_ref = get_customs_clearance(airport_ref, broker_ref, df_broker)
                discount_ref = calculate_anjun_discount(
                    carrier_current_ref, broker_ref, anjun_discount, apply_anjun_discount
                )
                cc_ref = max(0, cc_ref - discount_ref)
                cost_unit_ref = freight_ref + cc_ref
                savings = (cost_unit_ref - opt["cost_unit"]) * alloc
                
                allocations.append({
                    "state": opt["state"],
                    "airport": opt["airport"],
                    "broker": opt["broker"],
                    "carrier_current": opt["carrier_current"],
                    "carrier_simulated": opt["carrier"],
                    "type": opt["type"],
                    "freight_unit_sim": round(opt["freight_unit"], 4),
                    "cc_sim": round(opt["cc"], 4),
                    "cost_unit_sim": round(opt["cost_unit"], 4),
                    "freight_unit_ref": round(freight_ref, 4),
                    "cc_real_ref": round(cc_ref, 4),
                    "cost_unit_ref": round(cost_unit_ref, 4),
                    "packages": alloc,
                    "cost_total_sim": round(opt["cost_unit"] * alloc, 2),
                    "cost_total_ref": round(cost_unit_ref * alloc, 2),
                    "savings": round(savings, 2),
                    "changed": opt["carrier"].lower() != opt["carrier_current"].lower()
                })
                
                allocated[idx] += alloc
                cap_carrier[opt["carrier_lower"]] = max(0, cap_c_remaining - alloc)
                cap_broker[opt["broker_lower"]] = max(0, cap_b_remaining - alloc)
        
        df_alloc = pd.DataFrame(allocations)
        if df_alloc.empty:
            st.error("❌ Could not allocate any packages. Limits too restrictive.")
        else:
            st.session_state.df_limits_result = df_alloc
            total_allocated = df_alloc["packages"].sum()
            not_allocated = total_packages_all - total_allocated
            if not_allocated > 0:
                st.warning(
                    f"⚠️ {not_allocated:,.0f} packages not allocated ({not_allocated / total_packages_all * 100:.1f}%) "
                    f"— restrictive limits."
                )
            st.success(
                f"✅ Simulation complete! {total_allocated:,.0f} of {total_packages_all:,.0f} packages allocated "
                f"({total_allocated / total_packages_all * 100:.1f}%)."
            )
    
    # Display results
    if "df_limits_result" in st.session_state and not st.session_state.df_limits_result.empty:
        df_alloc = st.session_state.df_limits_result
        st.markdown("---")
        st.markdown("### 📊 Simulation Results with Limits")
        
        if customs_custom:
            st.markdown(
                '<div class="volume-warning">'
                '⚠️ Custom CC active: Reference Cost uses REAL CC from broker sheet. '
                'Simulated Cost uses custom CC for quotations.'
                '</div>', unsafe_allow_html=True
            )
        
        total_alloc = df_alloc["packages"].sum()
        total_cost_sim = df_alloc["cost_total_sim"].sum()
        total_cost_ref = df_alloc["cost_total_ref"].sum()
        total_savings = df_alloc["savings"].sum()
        savings_pct = (total_savings / total_cost_ref * 100) if total_cost_ref > 0 else 0
        
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.metric("📦 Packages Allocated", f"{total_alloc:,.0f} of {total_packages_all:,.0f}")
        with l2:
            st.metric("💰 Real Cost (ref)", fmt_brl(total_cost_ref))
        with l3:
            st.metric("💎 Simulated Cost", fmt_brl(total_cost_sim))
        with l4:
            css_class = "savings-positive" if total_savings >= 0 else "savings-negative"
            st.markdown(
                f'<div class="{css_class}"><h3>💰 Savings vs Real</h3>'
                f'<h2>{fmt_brl(total_savings)}</h2><p>{savings_pct:.1f}%</p></div>',
                unsafe_allow_html=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Summary by type
        col_tp1, col_tp2 = st.columns(2)
        kept = df_alloc[df_alloc["type"] == "TMS"]
        changed = df_alloc[df_alloc["type"] == "QUOTATION"]
        
        with col_tp1:
            st.markdown(
                f'<div class="volume-ok">'
                f'🔵 <strong>Kept (TMS Real):</strong> {len(kept)} allocations | '
                f'{kept["packages"].sum():,.0f} pkgs | '
                f'Cost: {fmt_brl(kept["cost_total_sim"].sum())}'
                f'</div>', unsafe_allow_html=True
            )
        with col_tp2:
            savings_changed = changed["savings"].sum() if not changed.empty else 0
            st.markdown(
                f'<div class="volume-warning">'
                f'🟡 <strong>Changed (Quotation):</strong> {len(changed)} allocations | '
                f'{changed["packages"].sum():,.0f} pkgs | '
                f'Savings: {fmt_brl(savings_changed)}'
                f'</div>', unsafe_allow_html=True
            )
        
        # Shares
        st.markdown("#### 📊 Share by Carrier")
        col_sh1, col_sh2 = st.columns(2)
        
        with col_sh1:
            st.markdown("##### Current (TMS)")
            share_curr_lim = calculate_share(df_dados)
            if not share_curr_lim.empty:
                fig_curr_lim = px.pie(share_curr_lim, values="Packages", names="Carrier",
                                      color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
                fig_curr_lim.update_traces(textposition="inside", textinfo="percent+label")
                fig_curr_lim.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_curr_lim, use_container_width=True, key="lim_sh_curr")
        
        with col_sh2:
            st.markdown("##### Simulated (with Limits)")
            share_sim_lim = df_alloc.groupby("carrier_simulated")["packages"].sum().reset_index()
            share_sim_lim.columns = ["Carrier", "Packages"]
            total_sim_lim = share_sim_lim["Packages"].sum()
            share_sim_lim["Share (%)"] = (
                share_sim_lim["Packages"] / total_sim_lim * 100
            ).round(2) if total_sim_lim > 0 else 0
            
            fig_sim_lim = px.pie(share_sim_lim, values="Packages", names="Carrier",
                                 color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig_sim_lim.update_traces(textposition="inside", textinfo="percent+label")
            fig_sim_lim.update_layout(height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_sim_lim, use_container_width=True, key="lim_sh_sim")
        
        # Share comparison
        st.markdown("#### 📋 Share Comparison")
        share_curr_dict = {}
        if not share_curr_lim.empty:
            for _, r in share_curr_lim.iterrows():
                share_curr_dict[r["Carrier"]] = r
        
        all_carriers_lim = sorted(set(
            list(share_curr_dict.keys()) + share_sim_lim["Carrier"].tolist()
        ))
        comparison_data = []
        for c in all_carriers_lim:
            p_curr = share_curr_dict[c]["Packages"] if c in share_curr_dict else 0
            s_curr = share_curr_dict[c]["Share (%)"] if c in share_curr_dict else 0
            row_sim = share_sim_lim[share_sim_lim["Carrier"] == c]
            p_sim = row_sim["Packages"].values[0] if not row_sim.empty else 0
            s_sim = row_sim["Share (%)"].values[0] if not row_sim.empty else 0
            comparison_data.append({
                "Carrier": c,
                "Packages Current": p_curr, "Share Current (%)": s_curr,
                "Packages Simulated": p_sim, "Share Simulated (%)": s_sim,
                "Vol. Variation": p_sim - p_curr,
                "Share Variation (pp)": round(s_sim - s_curr, 2)
            })
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(
            df_comparison.style.format({
                "Packages Current": "{:,.0f}", "Share Current (%)": "{:.2f}%",
                "Packages Simulated": "{:,.0f}", "Share Simulated (%)": "{:.2f}%",
                "Vol. Variation": "{:+,.0f}", "Share Variation (pp)": "{:+.2f}pp"
            }), use_container_width=True, hide_index=True
        )
        
        # Savings by state
        st.markdown("#### 💰 Savings by State (vs Real Cost)")
        savings_state_lim = df_alloc.groupby("state").agg(
            packages=("packages", "sum"),
            cost_simulated=("cost_total_sim", "sum"),
            cost_real_ref=("cost_total_ref", "sum"),
            savings=("savings", "sum")
        ).reset_index()
        savings_state_lim["savings_pct"] = (
            savings_state_lim["savings"] / savings_state_lim["cost_real_ref"] * 100
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
        st.markdown("#### 💰 Savings by Broker (vs Real Cost)")
        savings_broker_lim = df_alloc.groupby("broker").agg(
            packages=("packages", "sum"),
            cost_simulated=("cost_total_sim", "sum"),
            cost_real_ref=("cost_total_ref", "sum"),
            savings=("savings", "sum")
        ).reset_index()
        savings_broker_lim["savings_pct"] = (
            savings_broker_lim["savings"] / savings_broker_lim["cost_real_ref"] * 100
        ).round(2)
        savings_broker_lim = savings_broker_lim.sort_values("savings", ascending=False)
        
        st.dataframe(
            savings_broker_lim.rename(columns={
                "broker": "Broker", "packages": "Packages",
                "cost_simulated": "Simulated Cost", "cost_real_ref": "Real Cost (ref)",
                "savings": "Savings", "savings_pct": "Savings (%)"
            }).style.format({
                "Packages": "{:,.0f}", "Simulated Cost": "R$ {:,.2f}",
                "Real Cost (ref)": "R$ {:,.2f}", "Savings": "R$ {:,.2f}",
                "Savings (%)": "{:.2f}%"
            }), use_container_width=True, hide_index=True
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
                        "Carrier": c, "Limit": "No Limit",
                        "Allocated": f"{alloc:,.0f}", "Utilization": "—", "Status": "✅"
                    })
                else:
                    util = (alloc / limit * 100) if limit > 0 else 0
                    status = "🔴" if util >= 95 else "🟡" if util >= 70 else "🟢"
                    util_c_data.append({
                        "Carrier": c, "Limit": f"{limit:,.0f}",
                        "Allocated": f"{alloc:,.0f}", "Utilization": f"{util:.1f}%",
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
                        "Broker": b, "Limit": "No Limit",
                        "Allocated": f"{alloc:,.0f}", "Utilization": "—", "Status": "✅"
                    })
                else:
                    util = (alloc / limit * 100) if limit > 0 else 0
                    status = "🔴" if util >= 95 else "🟡" if util >= 70 else "🟢"
                    util_b_data.append({
                        "Broker": b, "Limit": f"{limit:,.0f}",
                        "Allocated": f"{alloc:,.0f}", "Utilization": f"{util:.1f}%",
                        "Status": status
                    })
            st.dataframe(pd.DataFrame(util_b_data), use_container_width=True, hide_index=True)
        
        # Full detail table
        st.markdown("#### 📋 Full Detail")
        st.dataframe(
            df_alloc.rename(columns={
                "state": "State", "airport": "Airport", "broker": "Broker",
                "carrier_current": "Current Carrier (TMS)", "carrier_simulated": "Simulated Carrier",
                "type": "Source", "freight_unit_sim": "Freight/Pkg Sim",
                "cc_sim": "CC Sim", "cost_unit_sim": "Cost/Pkg Sim",
                "freight_unit_ref": "Freight/Pkg Real", "cc_real_ref": "CC Real",
                "cost_unit_ref": "Cost/Pkg Real", "packages": "Packages",
                "cost_total_sim": "Total Cost Sim", "cost_total_ref": "Total Cost Real",
                "savings": "Savings", "changed": "Changed?"
            }).style.format({
                "Freight/Pkg Sim": "R$ {:.4f}", "CC Sim": "R$ {:.4f}", "Cost/Pkg Sim": "R$ {:.4f}",
                "Freight/Pkg Real": "R$ {:.4f}", "CC Real": "R$ {:.4f}", "Cost/Pkg Real": "R$ {:.4f}",
                "Packages": "{:,.0f}",
                "Total Cost Sim": "R$ {:,.2f}", "Total Cost Real": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}",
            }), use_container_width=True, height=500
        )
        
        # Export
        st.markdown("---")
        st.markdown("#### 📥 Export Simulation with Limits")
        export_data_lim = {
            "Detail": df_alloc,
            "Savings_State": savings_state_lim,
            "Savings_Broker": savings_broker_lim,
            "Share_Comparison": df_comparison,
        }
        excel_lim = generate_excel(export_data_lim)
        st.download_button(
            "📥 Download Results (Excel)", data=excel_lim,
            file_name="simulation_limits.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_limits"
        )

# ============================================================
# TAB 5 — STRATEGY BY STATE
# ============================================================
with tab5:
    st.markdown(
        '<div class="sub-header">🗺️ Strategy by State — Real Cost vs Optimized</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="info-box">'
        '<strong>Current Cost:</strong> <code>media_frete_tms</code> + CC from broker sheet (REAL)<br>'
        '<strong>Optimized Cost:</strong> best quotation + custom CC (when configured)'
        '</div>', unsafe_allow_html=True
    )
    
    if customs_custom:
        st.markdown(
            '<div class="volume-warning">'
            '⚠️ Custom CC active: optimized cost uses custom values. '
            'Current cost always uses real CC from broker sheet.'
            '</div>', unsafe_allow_html=True
        )
    
    if not quotation_columns:
        st.warning("⚠️ No quotation columns found. Strategy analysis requires quotations.")
    else:
        strategy_data = []
        all_states = sorted(df_dados["estado"].unique())
        
        for _, row in df_dados.iterrows():
            # Current REAL cost
            f_curr, cc_curr, cc_unit_curr, f_unit_curr = calculate_current_cost(
                row, df_broker, anjun_discount, apply_anjun_discount
            )
            cost_total_curr = f_curr + cc_curr
            cost_unit_curr = f_unit_curr + cc_unit_curr
            
            # Best option (quotations use simulated CC)
            best_carrier, best_freight, best_cc, best_cost_unit, source = find_best_option(
                row, quotation_columns, df_broker, customs_custom,
                anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
            )
            packages = row["qtd_pacotes_total"]
            cost_total_opt = best_cost_unit * packages
            
            strategy_data.append({
                "State": row["estado"],
                "Broker": row["broker"],
                "Airport": row["aeroporto"],
                "Current Carrier (TMS)": row["transportadora_atual"],
                "Optimized Carrier": best_carrier,
                "Source": source,
                "Packages": packages,
                "Freight TMS": f_unit_curr,
                "CC Real": cc_unit_curr,
                "Cost/Pkg Current (Real)": cost_unit_curr,
                "Freight Opt": best_freight,
                "CC Opt": best_cc,
                "Cost/Pkg Opt": best_cost_unit,
                "Total Cost Current (Real)": cost_total_curr,
                "Total Cost Opt": cost_total_opt,
                "Savings": cost_total_curr - cost_total_opt,
            })
        
        df_strategy = pd.DataFrame(strategy_data)
        
        # Consolidate
        df_consolidated = df_strategy.groupby(["State", "Broker", "Optimized Carrier"]).agg({
            "Packages": "sum",
            "Total Cost Current (Real)": "sum",
            "Total Cost Opt": "sum",
            "Savings": "sum",
            "Airport": lambda x: ", ".join(sorted(set(x))),
            "Current Carrier (TMS)": lambda x: ", ".join(sorted(set(x))),
            "Source": lambda x: ", ".join(sorted(set(x)))
        }).reset_index()
        
        df_consolidated["Cost/Pkg Current"] = (
            df_consolidated["Total Cost Current (Real)"] / df_consolidated["Packages"]
        ).round(4)
        df_consolidated["Cost/Pkg Opt"] = (
            df_consolidated["Total Cost Opt"] / df_consolidated["Packages"]
        ).round(4)
        df_consolidated["Savings (%)"] = (
            df_consolidated["Savings"] / df_consolidated["Total Cost Current (Real)"] * 100
        ).round(2)
        df_consolidated = df_consolidated.sort_values(["State", "Savings"], ascending=[True, False])
        
        # Display options
        st.markdown("#### 📋 Consolidated Strategic Table")
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            show_unit_costs = st.checkbox("Unit costs", True, key="t5_unit")
            show_current_carrier = st.checkbox("Current carrier", True, key="t5_curr")
        with col_sel2:
            show_airports = st.checkbox("Airports", True, key="t5_airports")
            filter_positive = st.checkbox("Only savings > 0", False, key="t5_positive")
        
        df_display = df_consolidated.copy()
        if filter_positive:
            df_display = df_display[df_display["Savings"] > 0]
        
        cols_show = ["State", "Broker", "Optimized Carrier", "Source", "Packages",
                     "Total Cost Current (Real)", "Total Cost Opt", "Savings", "Savings (%)"]
        if show_unit_costs:
            cols_show.extend(["Cost/Pkg Current", "Cost/Pkg Opt"])
        if show_current_carrier:
            cols_show.insert(3, "Current Carrier (TMS)")
        if show_airports:
            cols_show.insert(-4, "Airport")
        
        cols_show = [c for c in cols_show if c in df_display.columns]
        
        st.dataframe(
            df_display[cols_show].style.format({
                "Packages": "{:,.0f}",
                "Cost/Pkg Current": "R$ {:,.4f}", "Cost/Pkg Opt": "R$ {:,.4f}",
                "Total Cost Current (Real)": "R$ {:,.2f}", "Total Cost Opt": "R$ {:,.2f}",
                "Savings": "R$ {:,.2f}", "Savings (%)": "{:.2f}%"
            }), use_container_width=True, height=400
        )
        
        # Total metrics
        total_packages_strat = df_consolidated["Packages"].sum()
        total_current_strat = df_consolidated["Total Cost Current (Real)"].sum()
        total_opt_strat = df_consolidated["Total Cost Opt"].sum()
        total_savings_strat = df_consolidated["Savings"].sum()
        savings_pct_strat = (total_savings_strat / total_current_strat * 100) if total_current_strat > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Packages", f"{total_packages_strat:,.0f}")
        with c2:
            st.metric("Real Cost", fmt_brl(total_current_strat))
        with c3:
            st.metric("Optimized Cost", fmt_brl(total_opt_strat))
        with c4:
            css_class = "savings-positive" if total_savings_strat >= 0 else "savings-negative"
            st.markdown(
                f'<div class="{css_class}"><h3>💰 Total Savings</h3>'
                f'<h2>{fmt_brl(total_savings_strat)}</h2><p>{savings_pct_strat:.1f}%</p></div>',
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        # Summaries
        st.markdown("### 📊 Analysis by Broker and Carrier")
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("#### 📝 By Broker")
            summary_broker = df_consolidated.groupby("Broker").agg({
                "Packages": "sum", "Total Cost Current (Real)": "sum",
                "Total Cost Opt": "sum", "Savings": "sum"
            }).reset_index()
            summary_broker["Sav (%)"] = (
                summary_broker["Savings"] / summary_broker["Total Cost Current (Real)"] * 100
            ).round(2)
            summary_broker = summary_broker.sort_values("Savings", ascending=False)
            st.dataframe(
                summary_broker.style.format({
                    "Packages": "{:,.0f}", "Total Cost Current (Real)": "R$ {:,.2f}",
                    "Total Cost Opt": "R$ {:,.2f}", "Savings": "R$ {:,.2f}", "Sav (%)": "{:.2f}%"
                }), use_container_width=True, hide_index=True
            )
        
        with col_r2:
            st.markdown("#### 🚚 By Optimized Carrier")
            summary_carrier = df_consolidated.groupby("Optimized Carrier").agg({
                "Packages": "sum", "Total Cost Current (Real)": "sum",
                "Total Cost Opt": "sum", "Savings": "sum"
            }).reset_index()
            summary_carrier["Share (%)"] = (
                summary_carrier["Packages"] / summary_carrier["Packages"].sum() * 100
            ).round(2)
            summary_carrier["Cost/Pkg"] = (
                summary_carrier["Total Cost Opt"] / summary_carrier["Packages"]
            ).round(4)
            summary_carrier = summary_carrier.sort_values("Packages", ascending=False)
            st.dataframe(
                summary_carrier.style.format({
                    "Packages": "{:,.0f}", "Total Cost Current (Real)": "R$ {:,.2f}",
                    "Total Cost Opt": "R$ {:,.2f}", "Savings": "R$ {:,.2f}",
                    "Share (%)": "{:.2f}%", "Cost/Pkg": "R$ {:,.4f}"
                }), use_container_width=True, hide_index=True
            )
        
        # Visual shares
        st.markdown("### 📊 Shares: Current vs Optimized")
        cs1, cs2 = st.columns(2)
        with cs1:
            share_curr_strat = calculate_share(df_dados)
            if not share_curr_strat.empty:
                fig5a = px.pie(share_curr_strat, values="Packages", names="Carrier",
                               title="Current (TMS)", hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Set2)
                fig5a.update_traces(textposition="inside", textinfo="percent+label")
                fig5a.update_layout(height=400, margin=dict(t=50, b=30))
                st.plotly_chart(fig5a, use_container_width=True, key="t5_sh_curr")
        with cs2:
            if not summary_carrier.empty:
                fig5b = px.pie(summary_carrier, values="Packages", names="Optimized Carrier",
                               title="Optimized", hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Set2)
                fig5b.update_traces(textposition="inside", textinfo="percent+label")
                fig5b.update_layout(height=400, margin=dict(t=50, b=30))
                st.plotly_chart(fig5b, use_container_width=True, key="t5_sh_opt")
        
        # State analysis
        st.markdown("---")
        st.markdown("### 🔍 Analysis by State")
        filter_states_strat = st.multiselect(
            "Select states:", all_states,
            default=all_states[:3] if len(all_states) >= 3 else all_states,
            key="t5_state_det"
        )
        if filter_states_strat:
            df_filtered_strat = df_consolidated[df_consolidated["State"].isin(filter_states_strat)]
            fig_strat = px.bar(
                df_filtered_strat, x="State", y="Packages", color="Optimized Carrier",
                barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2, text="Packages"
            )
            fig_strat.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
            fig_strat.update_layout(height=450, margin=dict(t=30, b=30))
            st.plotly_chart(fig_strat, use_container_width=True, key="t5_strat_stack")
            
            savings_filtered = df_filtered_strat.groupby("State")["Savings"].sum().reset_index()
            savings_filtered = savings_filtered.sort_values("Savings", ascending=False)
            fig_sav_strat = px.bar(
                savings_filtered, x="State", y="Savings",
                text=savings_filtered["Savings"].apply(lambda x: f"R$ {x:,.0f}"),
                color="Savings", color_continuous_scale=["#ef5350", "#ffee58", "#66bb6a"]
            )
            fig_sav_strat.update_traces(textposition='outside')
            fig_sav_strat.update_layout(height=400, margin=dict(t=30, b=30), coloraxis_showscale=False)
            st.plotly_chart(fig_sav_strat, use_container_width=True, key="t5_sav_strat")
        
        # Export
        st.markdown("---")
        export_data_t5 = {
            "Strategy": df_consolidated,
            "Summary_Broker": summary_broker,
            "Summary_Carrier": summary_carrier
        }
        st.download_button(
            "📥 Download Strategy (Excel)", data=generate_excel(export_data_t5),
            file_name="strategy_by_state.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_t5"
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
        '</div>', unsafe_allow_html=True
    )
    
    state_list = sorted(df_dados["estado"].unique().tolist())
    selected_state = st.selectbox("State", state_list, key="state_analysis")
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
            f, c, _, _ = calculate_current_cost(row, df_broker, anjun_discount, apply_anjun_discount)
            total_freight_state += f
            total_cost_state += f + c
        
        e1, e2, e3, e4 = st.columns(4)
        with e1:
            st.metric("📦 Packages", f"{total_packages_state:,.0f}")
        with e2:
            st.metric("💰 Freight TMS", fmt_brl(total_freight_state))
        with e3:
            st.metric("💎 Total Cost (Real)", fmt_brl(total_cost_state))
        with e4:
            st.metric("⚖️ Weight", f"{total_weight_state / 1000:,.1f} kg")
        
        st.markdown("<br>", unsafe_allow_html=True)
        e6a, e6b = st.columns(2)
        with e6a:
            st.markdown(f"#### Current Share — {selected_state}")
            share_state = calculate_share(df_state)
            if not share_state.empty:
                fig_state = px.pie(share_state, values="Packages", names="Carrier", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Set2)
                fig_state.update_traces(textposition="inside", textinfo="percent+label")
                fig_state.update_layout(height=350, margin=dict(t=30, b=30))
                st.plotly_chart(fig_state, use_container_width=True, key="t6_share")
        
        with e6b:
            st.markdown(f"#### Quotations vs TMS — {selected_state}")
            quotation_data = []
            for _, r in df_state.iterrows():
                cc_real = get_customs_clearance(r["aeroporto"], r["broker"], df_broker)
                discount = calculate_anjun_discount(
                    r["transportadora_atual"], r["broker"], anjun_discount, apply_anjun_discount
                )
                cc_real = max(0, cc_real - discount)
                
                row_data = {
                    "Carrier": r["transportadora_atual"],
                    "Broker": r["broker"],
                    "Airport": r["aeroporto"],
                    "Pkgs": f"{r['qtd_pacotes_total']:,.0f}",
                    "Freight TMS": f"R$ {r['media_frete_tms']:.4f}",
                    "CC Real": f"R$ {cc_real:.4f}",
                }
                
                for col in quotation_columns:
                    carrier_key = extract_carrier_name(col)
                    carrier_name = carrier_key.capitalize()
                    if not is_carrier_allowed(carrier_key, r["aeroporto"], r["broker"],
                                              st.session_state.restriction_rules):
                        row_data[f"Quot.{carrier_name}"] = "🔒"
                    elif col in r.index and not pd.isna(r[col]) and r[col] > 0:
                        diff = r[col] - r['media_frete_tms']
                        symbol = "⬇️" if diff < 0 else "⬆️" if diff > 0 else "="
                        row_data[f"Quot.{carrier_name}"] = f"R$ {r[col]:.4f} {symbol}"
                    else:
                        row_data[f"Quot.{carrier_name}"] = "—"
                quotation_data.append(row_data)
            st.dataframe(pd.DataFrame(quotation_data), use_container_width=True, hide_index=True)
        
        # Cost by carrier
        st.markdown(f"#### Cost by Carrier — {selected_state}")
        carrier_costs_state = []
        for carrier in df_state["transportadora_atual"].unique():
            df_carrier_state = df_state[df_state["transportadora_atual"] == carrier]
            total_f = 0
            total_c = 0
            total_p = 0
            for _, row in df_carrier_state.iterrows():
                f, c, _, _ = calculate_current_cost(row, df_broker, anjun_discount, apply_anjun_discount)
                total_f += f
                total_c += c
                total_p += row["qtd_pacotes_total"]
            carrier_costs_state.append({
                "Carrier": carrier,
                "Packages": total_p,
                "Freight": total_f,
                "CC": total_c,
                "Total": total_f + total_c
            })
        
        df_carrier_costs_state = pd.DataFrame(carrier_costs_state)
        
        fig_cost_state = go.Figure()
        fig_cost_state.add_trace(go.Bar(
            name="Freight TMS", x=df_carrier_costs_state["Carrier"], y=df_carrier_costs_state["Freight"],
            marker_color="#4FC3F7",
            text=df_carrier_costs_state["Freight"].apply(lambda x: f"R$ {x:,.2f}"), textposition="auto"
        ))
        fig_cost_state.add_trace(go.Bar(
            name="CC (Real)", x=df_carrier_costs_state["Carrier"], y=df_carrier_costs_state["CC"],
            marker_color="#FFB74D",
            text=df_carrier_costs_state["CC"].apply(lambda x: f"R$ {x:,.2f}"), textposition="auto"
        ))
        fig_cost_state.update_layout(barmode="stack", height=400, margin=dict(t=30, b=30))
        st.plotly_chart(fig_cost_state, use_container_width=True, key="t6_cost_stack")
        
        # Best option
        if quotation_columns:
            st.markdown(f"#### 🏆 Best Option — {selected_state}")
            best_options = []
            for _, r in df_state.iterrows():
                best_carrier, best_freight, best_cc, best_cost, source = find_best_option(
                    r, quotation_columns, df_broker, customs_custom,
                    anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
                )
                f_curr, cc_curr, cc_unit_curr, f_unit_curr = calculate_current_cost(
                    r, df_broker, anjun_discount, apply_anjun_discount
                )
                cost_curr_total = f_curr + cc_curr
                cost_opt_total = best_cost * r["qtd_pacotes_total"]
                changed = r["transportadora_atual"].strip().lower() != best_carrier.strip().lower()
                
                best_options.append({
                    "Broker": r["broker"],
                    "Airport": r["aeroporto"],
                    "Current Carrier": r["transportadora_atual"],
                    "Freight TMS": f_unit_curr,
                    "CC Real": cc_unit_curr,
                    "Cost/Pkg Current": f_unit_curr + cc_unit_curr,
                    "Best": best_carrier,
                    "Source": source,
                    "Freight Opt": best_freight,
                    "CC Opt": best_cc,
                    "Cost/Pkg Opt": best_cost,
                    "Pkgs": r["qtd_pacotes_total"],
                    "Savings": cost_curr_total - cost_opt_total,
                    "Changed?": "✅" if changed else "—"
                })
            
            st.dataframe(
                pd.DataFrame(best_options).style.format({
                    "Freight TMS": "R$ {:.4f}", "CC Real": "R$ {:.4f}", "Cost/Pkg Current": "R$ {:.4f}",
                    "Freight Opt": "R$ {:.4f}", "CC Opt": "R$ {:.4f}", "Cost/Pkg Opt": "R$ {:.4f}",
                    "Pkgs": "{:,.0f}", "Savings": "R$ {:,.2f}"
                }), use_container_width=True, hide_index=True
            )

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
        '• <code>media_frete_tms</code> = REAL freight cost from current carrier<br>'
        '• <code>media_cotacao_*</code> = new quotations for simulation'
        '</div>', unsafe_allow_html=True
    )
    
    view_mode = st.radio("View:", ["Original Data", "Broker Data", "With Optimization"], horizontal=True, key="sub_t7")
    
    if view_mode == "Original Data":
        st.markdown("#### Data Sheet (dados)")
        st.dataframe(df_dados, use_container_width=True, height=500)
    elif view_mode == "Broker Data":
        st.markdown("#### Broker Sheet (broker)")
        st.dataframe(df_broker, use_container_width=True, height=500)
    else:
        st.markdown("#### Data with Optimization")
        df_with_opt = df_dados.copy()
        
        # Add CC real column
        cc_real_list = []
        cost_current_list = []
        for _, row in df_with_opt.iterrows():
            cc = get_customs_clearance(row["aeroporto"], row["broker"], df_broker)
            discount = calculate_anjun_discount(
                row["transportadora_atual"], row["broker"], anjun_discount, apply_anjun_discount
            )
            cc = max(0, cc - discount)
            cc_real_list.append(round(cc, 4))
            cost_current_list.append(round(row["media_frete_tms"] + cc, 4))
        
        df_with_opt["cc_real"] = cc_real_list
        df_with_opt["cost_current_unit"] = cost_current_list
        
        if quotation_columns:
            best_results = []
            for _, row in df_with_opt.iterrows():
                best_carrier, best_freight, best_cc, best_cost, source = find_best_option(
                    row, quotation_columns, df_broker, customs_custom,
                    anjun_discount, apply_anjun_discount, st.session_state.restriction_rules
                )
                best_results.append({
                    "best_carrier": best_carrier,
                    "freight_opt": round(best_freight, 4),
                    "cc_opt": round(best_cc, 4),
                    "cost_opt_unit": round(best_cost, 4),
                    "source": source
                })
            
            df_best = pd.DataFrame(best_results)
            df_with_opt["best_carrier"] = df_best["best_carrier"]
            df_with_opt["freight_opt"] = df_best["freight_opt"]
            df_with_opt["cc_opt"] = df_best["cc_opt"]
            df_with_opt["cost_opt_unit"] = df_best["cost_opt_unit"]
            df_with_opt["source"] = df_best["source"]
            df_with_opt["savings_unit"] = (df_with_opt["cost_current_unit"] - df_with_opt["cost_opt_unit"]).round(4)
            df_with_opt["savings_total"] = (df_with_opt["savings_unit"] * df_with_opt["qtd_pacotes_total"]).round(2)
        
        st.dataframe(df_with_opt, use_container_width=True, height=500)
    
    st.markdown("---")
    
    # Custom CC vs Real
    if customs_custom:
        st.markdown("#### 🛃 Custom CC vs Real")
        cc_comparison = []
        for key, custom_val in customs_custom.items():
            broker_name, airport_name = key
            real_val = get_customs_clearance(airport_name, broker_name, df_broker)
            cc_comparison.append({
                "Broker": broker_name,
                "Airport": airport_name,
                "Custom CC (Simulations)": custom_val,
                "Real CC (Broker Sheet)": real_val,
                "Difference": round(custom_val - real_val, 4)
            })
        st.dataframe(
            pd.DataFrame(cc_comparison).style.format({
                "Custom CC (Simulations)": "R$ {:.4f}",
                "Real CC (Broker Sheet)": "R$ {:.4f}",
                "Difference": "R$ {:.4f}"
            }), use_container_width=True, hide_index=True
        )
    
    st.markdown("#### 🚨 Active Rules")
    if st.session_state.restriction_rules:
        rules_display = [
            {
                "Carrier": carrier.capitalize(),
                "Airports": ", ".join([a.upper() for a in rule.get("airports", [])]),
                "Brokers": ", ".join([b.upper() for b in rule.get("brokers", [])])
            }
            for carrier, rule in st.session_state.restriction_rules.items()
        ]
        st.dataframe(pd.DataFrame(rules_display), use_container_width=True, hide_index=True)
    else:
        st.info("No restriction rules configured.")
    
    st.markdown("---")
    
    st.markdown("#### Share by State and Carrier")
    share_state_carrier = df_dados.groupby(["estado", "transportadora_atual"]).agg(
        packages=("qtd_pacotes_total", "sum")
    ).reset_index()
    
    total_by_state = df_dados.groupby("estado")["qtd_pacotes_total"].sum().reset_index()
    total_by_state.columns = ["estado", "total_state"]
    share_state_carrier = share_state_carrier.merge(total_by_state, on="estado")
    share_state_carrier["share"] = (share_state_carrier["packages"] / share_state_carrier["total_state"] * 100).round(2)
    
    # Add average freight
    avg_freight = df_dados.groupby(["estado", "transportadora_atual"])["media_frete_tms"].mean().reset_index()
    avg_freight.columns = ["estado", "transportadora_atual", "avg_freight"]
    share_state_carrier = share_state_carrier.merge(avg_freight, on=["estado", "transportadora_atual"])
    share_state_carrier["avg_freight"] = share_state_carrier["avg_freight"].round(4)
    
    st.dataframe(
        share_state_carrier.rename(columns={
            "estado": "State", "transportadora_atual": "Carrier (TMS)",
            "packages": "Packages", "total_state": "State Total",
            "share": "Share (%)", "avg_freight": "Avg Freight"
        }).style.format({
            "Share (%)": "{:.2f}%", "Avg Freight": "R$ {:.4f}",
            "Packages": "{:,.0f}", "State Total": "{:,.0f}"
        }), use_container_width=True, height=500
    )
    
    st.markdown("#### Heatmap - Average Freight TMS")
    pivot_freight = share_state_carrier.pivot_table(
        index="estado", columns="transportadora_atual", values="avg_freight", fill_value=0
    )
    fig_heatmap = px.imshow(pivot_freight, text_auto=".2f", color_continuous_scale="RdYlGn_r", aspect="auto")
    fig_heatmap.update_layout(height=600, margin=dict(t=30, b=30))
    st.plotly_chart(fig_heatmap, use_container_width=True, key="t7_heatmap")
    
    st.markdown("---")
    st.markdown("#### 📥 Export All")
    export_all = {
        "Data_Original": df_dados,
        "Broker_Data": df_broker,
        "Share_Total": calculate_share(df_dados),
        "Share_State_Carrier": share_state_carrier,
    }
    
    if st.session_state.restriction_rules:
        export_all["Rules"] = pd.DataFrame(rules_display)
    
    if customs_custom:
        export_all["CC_Custom_vs_Real"] = pd.DataFrame(cc_comparison)
    
    if "df_limits_result" in st.session_state and not st.session_state.df_limits_result.empty:
        export_all["Sim_Limits"] = st.session_state.df_limits_result
    
    if "df_simulation_result" in st.session_state and not st.session_state.df_simulation_result.empty:
        export_all["Sim_Volume"] = st.session_state.df_simulation_result
    
    excel_all = generate_excel(export_all)
    
    dc1, dc2 = st.columns(2)
    with dc1:
        st.download_button(
            "📥 Complete Excel", data=excel_all,
            file_name="complete_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_t7_xl"
        )
    with dc2:
        st.download_button(
            "📥 Original CSV", data=df_dados.to_csv(index=False).encode("utf-8"),
            file_name="original_data.csv", mime="text/csv",
            key="dl_t7_csv"
        )
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#888;padding:1rem;'>"
        "<small>Logistics Cost Simulator v8.0 — Real CC (baseline) vs Custom CC (simulations) | "
        "Anjun discount applied when carrier AND broker are both Anjun</small>"
        "</div>", unsafe_allow_html=True
    )
