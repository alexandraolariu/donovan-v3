import streamlit as st
import pandas as pd
import os

# 1. CONFIGURARE PAGINĂ
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Coloane eliminate pentru performanță și claritate) ---
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "IssuedDate", "ExpiredLapseDate",
    "WaterAccountList", "WRPDescriptionList", "ROPDescription",
    "ROPLocationName", "ROPLocationDescription", "MaxHeightMetre",
    "IsWaterAllocation", "IsDevelopmentAuthorisation", "IsApproval",
    "IsNotice", "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# 2. DESIGN (CSS) - Curat și profesional pentru Iframe
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    #MainMenu, footer, header {visibility: hidden;}
    .detail-card { 
        background-color: white; padding: 25px; border-radius: 15px; 
        border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
        margin-top: 20px;
    }
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. ÎNCĂRCARE DATE (Optimizată cu Parquet și Cache)
@st.cache_data(show_spinner="Loading database...")
def load_data():
    try:
        # Încercăm să citim Parquet (Viteza maximă)
        # Dacă încă nu ai făcut conversia, codul va căuta și CSV-ul vechi ca backup
        if os.path.exists("water-licence.parquet"):
            df = pd.read_parquet("water-licence.parquet")
        else:
            # Backup în caz că ai rămas pe CSV momentan
            df = pd.read_csv("water-licence-attributes.csv", encoding='cp1252', on_bad_lines='skip')

        # Curățare coloane
        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        # Redenumire coloană cheie
        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})

        return df.fillna('N/A')
    except Exception as e:
        st.error(f"Eroare critică la încărcarea datelor: {e}")
        return pd.DataFrame()

# Inițializare date
df = load_data()

# 4. INTERFAȚA DE CĂUTARE
st.title("💧 Water License Search Portal")
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: 
    s_name = st.text_input("👤 Legal Name:", placeholder="Search name...")
with c2: 
    s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")
with c3: 
    s_water = st.text_input("🌊 Water Name/Type:", placeholder="Search water source...")

# Filtrare eficientă
d_show = df.copy()

if s_name:
    # Căutăm coloana care conține 'legal' în nume
    legal_col = next((c for c in df.columns if 'legal' in c.lower()), df.columns[0])
    d_show = d_show[d_show[legal_col].astype(str).str.contains(s_name, case=False, na=False)]

if s_auth:
    d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]

if s_water:
    water_col = next((c for c in df.columns if 'water' in c.lower()), None)
    if water_col:
        d_show = d_show[d_show[water_col].astype(str).str.contains(s_water, case=False, na=False)]

# 5. AFIȘARE REZULTATE (Tabel interactiv)
st.markdown(f"### 📋 Results ({len(d_show)} records found)")
st.info("💡 Click on a row to see full details below.")

# Limităm afișarea inițială pentru viteză dacă nu există căutare activă
final_df = d_show.head(100) if not (s_name or s_auth or s_water) else d_show

if not final_df.empty:
    # Widget-ul nou de tabel cu selecție (disponibil în Streamlit 1.35+)
    selection = st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
else:
    st.warning("No results found for your search criteria.")
    selection = None

# 6. DETALII RÂND SELECTAT
# Verificăm dacă utilizatorul a dat click pe un rând
if selection and selection.get("selection") and len(selection["selection"]["rows"]) > 0:
    selected_index = selection["selection"]["rows"][0]
    row_data = final_df.iloc[selected_index].to_dict()
    
    st.markdown("---")
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.subheader(f"🔍 Detailed View: {row_data.get('Water License', 'N/A')}")
    
    # Organizăm datele în 3 coloane pentru a nu fi o listă lungă și obositoare
    detail_cols = st.columns(3)
    for i, (key, value) in enumerate(row_data.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.code(str(value), language=None) # Folosim st.code pentru a permite copy-paste ușor
            
    # Buton de export pentru rândul curent
    csv_one = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download this record (CSV)",
        data=csv_one,
        file_name=f"license_{row_data.get('Water License', 'info')}.csv",
        mime="text/csv"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# 7. EXPORT REZULTATE FILTRATE (La finalul paginii)
if not d_show.empty:
    st.sidebar.markdown("---")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Download ALL Filtered Results",
        data=full_csv,
        file_name="filtered_water_licenses.csv",
        mime="text/csv"
    )
