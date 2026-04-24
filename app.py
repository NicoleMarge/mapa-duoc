import streamlit as st
import pandas as pd
import json
from streamlit_google_auth import Authenticate

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Mapa Duoc UC", layout="wide")

# ---------------- CREAR client_secrets.json ----------------
creds = {
    "web": {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]],
    }
}

with open("client_secrets.json", "w") as f:
    json.dump(creds, f)

# ---------------- AUTH ----------------
auth = Authenticate(
    "client_secrets.json",
    st.secrets["google_oauth"]["cookie_key"],
    "duoc_cookie",
    st.secrets["google_oauth"]["redirect_uri"]
)

# ---------------- LOGIN ----------------
if not st.session_state.get("connected"):
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Inicia sesión con tu cuenta institucional (@duocuc.cl)")

    auth.login()

    if st.session_state.get("connected"):
        st.rerun()

    st.stop()

# ---------------- VALIDAR USUARIO ----------------
user_info = st.session_state.get("user_info")

if not user_info:
    st.error("No se pudo obtener la información del usuario")
    st.stop()

email = user_info.get("email", "").lower()

if not email.endswith("@duocuc.cl"):
    st.error(f"🚫 Acceso denegado: {email}")
    if st.button("Cerrar sesión"):
        auth.logout()
        st.rerun()
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.success(f"Conectado como:\n{email}")

if st.sidebar.button("Cerrar sesión"):
    auth.logout()
    st.rerun()

# ---------------- CARGA DE DATOS ----------------
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        sheet_id = st.secrets["gsheet_id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error("Error cargando datos desde Google Sheets")
        return pd.DataFrame()

df = cargar_datos()

# ---------------- UI PRINCIPAL ----------------
st.title("🔍 Buscador de Salas y Dependencias")

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

        # Mostrar más info si existe
        st.markdown("### 📋 Detalle")
        st.dataframe(res.to_frame().T)

    else:
        st.warning("No se encontraron resultados")

elif query and df.empty:
    st.error("No hay datos disponibles para buscar")

# ---------------- INFO FINAL ----------------
st.markdown("---")
st.caption("Sistema interno Duoc UC - Acceso restringido")
