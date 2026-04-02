import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode

# 1. CONFIGURARE PAGINĂ
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Ce eliminăm) ---
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "IssuedDate", "ExpiredLapseDate",
    "WaterAccountList", "WRPDescriptionList", "ROPDescription",
    "ROPLocationName", "ROPLocationDescription", "MaxHeightMetre",
    "IsWaterAllocation", "IsDevelopmentAuthorisation", "IsApproval",
    "IsNotice", "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# 2. DESIGN (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    #MainMenu, footer, header {visibility: hidden;}
    .detail-card { 
        background-color: white; padding: 25px; border-radius: 12px; 
        border: 2px solid #1E3A8A; box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        margin-top: 20px;
    }
    .instruction-box {
        padding: 10px; border-radius: 5px; background-color: #e7f3ff;
        border-left: 5px solid #1E3A8A; color: #1E3A8A; font-weight: bold;
        margin-bottom: 15px;
    }
    .ag-row:hover { background-color: #e1effe !important; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)


# 3. ÎNCĂRCARE ȘI CURĂȚARE DATE
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("water-licence-attributes.csv", sep=None, engine='python', encoding='cp1252',
                         on_bad_lines='skip')

        # 1. Eliminăm coloanele nedorite
        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        # 2. REDENUMIRE COLOANĂ (AuthorisationReference -> Water License)
        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})

        return df.fillna('N/A').astype(str)
    except:
        return pd.DataFrame()


df = load_data()

# --- INTERFAȚA ---
st.title("💧 Water License Search Portal")

# 4. CĂUTĂRI (Actualizate pentru noul nume)
c1, c2, c3 = st.columns(3)
with c1: s_name = st.text_input("👤 Legal Name:", placeholder="Search name...")
with c2: s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")  # Am schimbat eticheta aici
with c3: s_water = st.text_input("🌊 Water Name/Type:", placeholder="Search water source...")

# Filtrare
d_show = df.copy()

if s_name:
    col = next((c for c in df.columns if 'legal' in c.lower()), df.columns[0])
    d_show = d_show[d_show[col].str.contains(s_name, case=False, na=False)]
if s_auth:
    # Căutăm în coloana redenumită "Water License"
    col = "Water License" if "Water License" in d_show.columns else d_show.columns[0]
    d_show = d_show[d_show[col].str.contains(s_auth, case=False, na=False)]
if s_water:
    target_col = "WaterName/Type" if "WaterName/Type" in df.columns else next(
        (c for c in df.columns if 'water' in c.lower()), None)
    if target_col:
        d_show = d_show[d_show[target_col].str.contains(s_water, case=False, na=False)]

if not (s_name or s_auth or s_water):
    d_show = d_show.head(100)

# 5. TABELUL
if d_show.empty:
    st.warning("⚠️ No results found.")
else:
    st.markdown(
        '<div class="instruction-box">💡 TIP: Click on a row below to see technical details and export records.</div>',
        unsafe_allow_html=True)

    manual_options = {
        "columnDefs": [{"field": i, "headerName": i} for i in d_show.columns],
        "defaultColDef": {"resizable": True, "sortable": True, "filter": True, "minWidth": 200},
        "rowSelection": "single",
        "pagination": True,
        "paginationPageSize": 10
    }

    response = AgGrid(
        d_show,
        gridOptions=manual_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme='alpine',
        height=450,
        fit_columns_on_grid_load=False
    )

    # 6. DETALII POP-UP
    sel = response.get('selected_rows')
    row = None
    if isinstance(sel, pd.DataFrame) and not sel.empty:
        row = sel.iloc[0].to_dict()
    elif isinstance(sel, list) and len(sel) > 0:
        row = sel[0]

    if row:
        st.markdown("---")
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.subheader("📋 Record Details")

        clean_items = {k: v for k, v in row.items() if not str(k).startswith('_')}

        cols = st.columns(3)
        for i, (k, v) in enumerate(clean_items.items()):
            with cols[i % 3]:
                st.markdown(f"**{k}**")
                st.info(str(v))

        csv_single = pd.DataFrame([clean_items]).to_csv(index=False).encode('utf-8')
        st.download_button(f"📥 Export License {row.get('Water License', '')}", csv_single, "license_detail.csv",
                           "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

# 7. EXPORT GLOBAL
if not d_show.empty:
    st.markdown("---")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download All Filtered Results (CSV)", full_csv, "water_licenses.csv", "text/csv")
