import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Mapa Duoc UC",
    layout="wide",
    page_icon="📍"
)

st.title("📍 Mapa Interactivo Duoc UC - Puente Alto")
st.markdown("---")

# ---------------- CONEXIÓN SEGURA A GOOGLE SHEETS ----------------
@st.cache_data(ttl=86400)
def cargar_datos():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

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

    except Exception as e:
        st.error("❌ Error al conectar con Google Sheets")
        return pd.DataFrame()

df = cargar_datos()

# ---------------- UI PRINCIPAL ----------------
st.header("🔍 Buscador de Salas y Dependencias")

col1, col2 = st.columns([6, 4])

with col1:
    query = st.text_input(
        "Buscar sala o dependencia:",
        placeholder="Ej: 412, Biblioteca, Laboratorio..."
    )

# ---------------- BÚSQUEDA ----------------
if query and not df.empty:
    q = query.strip().lower()

    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]

    if not resultado.empty:
        res = resultado.iloc[0]

        nombre = res.get('nombre', 'Sala')
        piso = res.get('piso', '-')
        edificio = res.get('edificio', '-')

        st.success(f"✅ {nombre} (Piso {piso})")
        st.write(f"📍 Edificio: {edificio}")

        # ---------------- DETALLE ----------------
        st.markdown("### 📋 Información de la sala")
        st.dataframe(res.to_frame().T, use_container_width=True)

    else:
        st.warning("⚠️ No se encontraron resultados")

elif query and df.empty:
    st.error("❌ No hay datos disponibles")

# ---------------- MAPA SIMPLIFICADO ----------------
st.markdown("---")
st.subheader("🗺️ Vista general del campus")

st.info("El mapa muestra únicamente los edificios principales del campus")

map_data = pd.DataFrame({
    "lat": [-33.5985, -33.5987, -33.5989],
    "lon": [-70.5755, -70.5752, -70.5758],
    "name": ["Edificio A", "Edificio B", "Edificio C"]
})

st.map(map_data)

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Sistema institucional - Acceso exclusivo para usuarios autorizados")
