import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Mapa Duoc UC", layout="wide")

# ---------------- CONEXIÓN SEGURA ----------------
@st.cache_data(ttl=86400)  # 24 horas
def cargar_datos():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(
            st.secrets["gsheets"],
            scopes=scope
        )

        client = gspread.authorize(creds)

        # Nombre EXACTO del Google Sheet
        sheet = client.open("Base de Datos Salas Duoc").sheet1

        data = sheet.get_all_records()

        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.lower()

        return df

    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df = cargar_datos()

# ---------------- UI ----------------
st.title("📍 Mapa Institucional Duoc UC")

query = st.text_input(
    "Buscar sala o dependencia:",
    placeholder="Ej: 412, Biblioteca, Laboratorio..."
)

# ---------------- BUSCADOR ----------------
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

        st.markdown("### 📋 Información")
        st.dataframe(res.to_frame().T)

    else:
        st.warning("No se encontraron resultados")

elif query and df.empty:
    st.error("No hay datos disponibles")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Mapa Duoc UC - Acceso seguro con Google API")
