import streamlit as st
import pandas as pd
import os
import json
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC")

# --- 2. ARCHIVO DE CREDENCIALES ---
creds_path = "client_secrets.json"
creds_data = {
    "web": {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
    }
}

with open(creds_path, "w") as f:
    json.dump(creds_data, f)

# --- 3. INICIALIZACIÓN ---
# Usamos los argumentos posicionales que ya vimos que funcionan
auth = Authenticate(
    creds_path,
    st.secrets["google_oauth"]["cookie_key"],
    "duoc_auth_cookie",
    st.secrets["google_oauth"]["redirect_uri"]
)

# --- 4. LÓGICA DE LOGIN (CORREGIDA) ---
# En lugar de check_authenticity(), usamos la lógica directa de la librería
if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Bienvenido. Para acceder al buscador, inicia sesión con tu cuenta institucional.")
    
    # Intentar capturar el login
    auth.login()
    
    # Si después de login el estado cambia, recargamos
    if st.session_state.get('connected'):
        st.rerun()
    st.stop()

# --- 5. VALIDACIÓN DE DOMINIO @DUOCUC.CL ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error(f"🚫 Acceso denegado: {user_email} no es institucional.")
        if st.button("Cerrar sesión"):
            auth.logout()
            st.rerun()
        st.stop()

# --- 6. BUSCADOR (ÁREA PRIVADA) ---
st.title("🔍 Buscador de Salas y Dependencias")

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# Interfaz de búsqueda
col1, col2 = st.columns([6, 4])
with col1:
    search_query = st.text_input("Ingresa sala o nombre:", placeholder="Ej: 412, Biblioteca...")

if search_query and not df.empty:
    query = search_query.strip().lower()
    # Buscamos en cualquier columna que contenga el texto
    resultado = df[df.apply(lambda row: query in str(row.values).lower(), axis=1)]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        st.success(f"✅ **Resultado**: {res.get('nombre', 'Sala')} (Piso {res.get('piso', '-')})")
        st.write(f"📍 Edificio: {res.get('edificio', '-')}")
    else:
        st.warning("No se encontraron coincidencias.")

# Botón para salir
if st.sidebar.button("Cerrar Sesión"):
    auth.logout()
    st.rerun()
