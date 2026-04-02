import streamlit as st
import pandas as pd
import os

# 1. CONFIGURARE PAGINĂ
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Coloane eliminate pentru viteză) ---
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "IssuedDate", "ExpiredLapseDate",
    "WaterAccountList", "WRPDescriptionList", "ROPDescription",
    "ROPLocationName", "ROPLocationDescription", "MaxHeightMetre",
    "IsWaterAllocation", "IsDevelopmentAuthorisation", "IsApproval",
    "IsNotice", "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# 2. DESIGN (CSS) - Adaptat pentru Iframe
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* Ascundem meniul Streamlit pentru un aspect de portal curat */
    #MainMenu, footer, header {visibility: hidden;}
    
    .detail-card { 
        background-color: white; padding: 25px; border-radius: 15px; 
        border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
        margin-top: 20px;
    }
    /* Stil pentru input-uri mai vizibile */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. ÎNCĂRCARE DATE
@st.cache_data(show_spinner="Loading database...")
def load_data():
    try:
        # Verificăm dacă există varianta rapidă Parquet, altfel folosim CSV
        if os.path.exists("water-licence.parquet"):
            df = pd.read_parquet("water-licence.parquet")
        else:
            df = pd.read_csv("water-licence-attributes.csv", encoding='cp1252', on_bad_lines='skip')

        # Eliminăm coloanele inutile
        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        # Redenumim coloana principală de referință
        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})

        return df.fillna('N/A')
    except Exception as e:
        st.error(f"Eroare la încărcarea datelor: {e}")
        return pd.DataFrame()

df = load_data()

# 4. INTERFAȚA DE CĂUTARE
st.title("💧 Water License Search Portal")
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: 
    s_name = st.text_input("👤 Legal Name:", placeholder="Ex: King...")
with c2: 
    s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")
with c3: 
    s_water = st.text_input("🌊 Water Name/Type:", placeholder="Ex: Mary...")

# Logica de filtrare (AND - trebuie să respecte toate câmpurile completate)
d_show = df.copy()

if s_name:
    # Identificăm coloana de nume (care conține 'legal')
    legal_col = next((c for c in df.columns if 'legal' in c.lower()), df.columns[0])
    d_show = d_show[d_show[legal_col].astype(str).str.contains(s_name, case=False, na=False)]

if s_auth:
    if "Water License" in d_show.columns:
        d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]

if s_water:
    # Identificăm coloana de apă (care conține 'water' în nume)
    water_col = next((c for c in df.columns if 'water' in c.lower()), None)
    if water_col:
        d_show = d_show[d_show[water_col].astype(str).str.contains(s_water, case=False, na=False)]

# 5. AFIȘARE REZULTATE
st.markdown(f"### 📋 Results ({len(d_show)} records found)")

# Dacă nu există căutare, arătăm doar primele 50 de rânduri pentru viteză
final_df = d_show.head(50) if not (s_name or s_auth or s_water) else d_show

if not final_df.empty:
    st.info("💡 Select a row to view full details below.")
    selection = st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
else:
    st.warning("No results found. Try broader search terms.")
    selection = None

# 6. DETALII RÂND SELECTAT
if selection and selection.get("selection") and len(selection["selection"]["rows"]) > 0:
    selected_index = selection["selection"]["rows"][0]
    row_data = final_df.iloc[selected_index].to_dict()
    
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.subheader(f"🔍 Details: {row_data.get('Water License', 'N/A')}")
    
    # Afișăm datele în coloane
    detail_cols = st.columns(3)
    for i, (key, value) in enumerate(row_data.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.info(str(value))
            
    # Export rând selectat
    csv_one = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download this record (CSV)", csv_one, f"license_{selected_index}.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# 7. EXPORT GLOBAL (Aici jos, nu în sidebar)
if not d_show.empty:
    st.markdown("---")
    st.markdown("### 📥 Full Export")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download ALL Filtered Results (CSV)",
        data=full_csv,
        file_name="water_licenses_filtered.csv",
        mime="text/csv"
    )
