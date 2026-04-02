import streamlit as st
import pandas as pd

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
        background-color: white; padding: 20px; border-radius: 12px; 
        border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. ÎNCĂRCARE DATE
@st.cache_data
def load_data():
    try:
        # Citim datele
        df = pd.read_csv("water-licence-attributes.csv", encoding='cp1252', on_bad_lines='skip')

        # Eliminăm coloanele nedorite
        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})

        return df.fillna('N/A')
    except Exception as e:
        st.error(f"Eroare la date: {e}")
        return pd.DataFrame()

df = load_data()

st.title("💧 Water License Search Portal")

# 4. CĂUTĂRI
c1, c2, c3 = st.columns(3)
with c1: s_name = st.text_input("👤 Legal Name:", placeholder="Search name...")
with c2: s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")
with c3: s_water = st.text_input("🌊 Water Name/Type:", placeholder="Search water source...")

# Filtrare
d_show = df.copy()
if s_name:
    col = next((c for c in df.columns if 'legal' in c.lower()), df.columns[0])
    d_show = d_show[d_show[col].astype(str).str.contains(s_name, case=False, na=False)]
if s_auth:
    d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]
if s_water:
    target_col = next((c for c in df.columns if 'water' in c.lower()), None)
    if target_col:
        d_show = d_show[d_show[target_col].astype(str).str.contains(s_water, case=False, na=False)]

# 5. TABELUL MODERN
st.markdown("### 📋 Results")
st.info("💡 Select a row to view details.")

# Ensure we have data to show
final_df = d_show.head(100) if not (s_name or s_auth or s_water) else d_show

# Use selection only if the dataframe isn't empty
if not final_df.empty:
    selection = st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row" # Changed 'single' to 'single-row' for better compatibility in some versions
    )
else:
    st.warning("No results found.")
    selection = None
    

# 6. DETALII POP-UP (Aici era eroarea roșie - acum e reparată)
if selection and len(selection.get("selection", {}).get("rows", [])) > 0:
    selected_row_index = selection["selection"]["rows"][0]
    row_data = final_df.iloc[selected_row_index].to_dict()
    
    st.markdown("---")
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.subheader(f"🔍 Details for License: {row_data.get('Water License', 'N/A')}")
    
    cols = st.columns(3)
    for i, (k, v) in enumerate(row_data.items()):
        with cols[i % 3]:
            st.write(f"**{k}**")
            st.info(str(v))
            
    # Export pentru rândul selectat
    csv_single = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export this record", csv_single, "license_detail.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# 7. EXPORT GLOBAL
if not d_show.empty:
    st.markdown("---")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Filtered Results (CSV)", full_csv, "water_licenses.csv", "text/csv")
