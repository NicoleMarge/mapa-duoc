import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Mapa Duoc UC", layout="wide")

st.title("📍 Mapa Institucional Duoc UC")
st.markdown("---")

# ---------------- CONEXIÓN SEGURA ----------------
@st.cache_data(ttl=600)
def cargar_datos():

    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open("Base de Datos Salas Duoc")
    worksheet = sheet.sheet1

    data = worksheet.get_all_records()

    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip().str.lower()

    return df

df = cargar_datos()

# ---------------- BUSCADOR ----------------
st.subheader("🔍 Buscar sala o dependencia")

query = st.text_input(
    "Buscar:",
    placeholder="Ej: 412, Biblioteca..."
)

# ---------------- RESULTADOS ----------------
if query and not df.empty:
    q = query.strip().lower()

    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]

    if not resultado.empty:
        res = resultado.iloc[0]

        st.success(f"✅ {res.get('nombre', 'Sala')}")
        st.write(f"🏢 Edificio: {res.get('edificio', '-')}")
        st.write(f"⬆️ Piso: {res.get('piso', '-')}")

        st.markdown("### 📋 Información")
        st.dataframe(res.to_frame().T, use_container_width=True)

    else:
        st.warning("No se encontraron resultados")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Sistema seguro - datos protegidos")
