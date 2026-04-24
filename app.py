import streamlit as st
import pandas as pd
import os
import json
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC", page_icon="📍")

# --- 2. GENERACIÓN DEL ARCHIVO DE SECRETOS ---
# Muchas versiones de esta librería necesitan leer un archivo físico.
creds_path = "client_secrets.json"
try:
    with open(creds_path, "w") as f:
        json.dump({
            "web": {
                "client_id": st.secrets["google_oauth"]["client_id"],
                "client_secret": st.secrets["google_oauth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
            }
        }, f)
except Exception as e:
    st.error(f"Error técnico: {e}")

# --- 3. INICIALIZACIÓN DE AUTENTICACIÓN ---
# Corregido para versión 1.1.8: Usamos 'secrets_path' (con s)
auth = Authenticate(
    secrets_path=creds_path, 
    cookie_name='duoc_auth_cookie',
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1,
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
)

# Verificar estado de conexión
auth.check_authenticity()

if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Por favor, inicia sesión con tu cuenta institucional de Google.")
    auth.login()
    st.stop()

# --- 4. FILTRO DE SEGURIDAD @DUOCUC.CL ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error(f"Acceso denegado: {user_email} no es un correo institucional.")
        if st.button("Salir"):
            auth.logout()
            st.rerun()
        st.stop()

# --- 5. INTERFAZ Y BUSCADOR ---
st.title("🔍 Buscador de Salas")

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

df = cargar_datos()

# buscador simple
busqueda = st.text_input("Ingresa sala:")
if busqueda and not df.empty:
    # Ajusta 'sala' al nombre exacto de tu columna en el Excel
    res = df[df.apply(lambda row: busqueda.lower() in str(row.values).lower(), axis=1)]
    if not res.empty:
        st.success(f"Encontrado: {res.iloc[0].to_dict()}")
    else:
        st.warning("No hay resultados.")

if st.button("Cerrar Sesión"):
    auth.logout()
    st.rerun()
