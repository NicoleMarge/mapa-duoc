import streamlit as st
import pandas as pd
import os
import json
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC")

# --- 2. CREACIÓN DEL ARCHIVO JSON (OBLIGATORIO) ---
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

# --- 3. INICIALIZACIÓN SIN NOMBRES DE ARGUMENTOS ---
# Intentamos pasar solo los 4 parámetros básicos en el orden original de la librería
# para evitar que salte el "unexpected keyword argument"
auth = Authenticate(
    creds_path,                               # secret_path
    st.secrets["google_oauth"]["cookie_key"], # cookie_key
    "duoc_auth_cookie",                       # cookie_name
    st.secrets["google_oauth"]["redirect_uri"] # redirect_uri
)

# Lógica de autenticación
auth.check_authenticity()

if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Inicia sesión con tu cuenta @duocuc.cl")
    auth.login()
    st.stop()

# --- 4. VALIDACIÓN DE DOMINIO ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error("Acceso restringido a cuentas Duoc UC.")
        if st.button("Salir"):
            auth.logout()
        st.stop()
else:
    st.stop()

# --- 5. BUSCADOR (ÁREA PRIVADA) ---
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
busqueda = st.text_input("Buscar sala:")

if busqueda and not df.empty:
    res = df[df.apply(lambda row: busqueda.lower() in str(row.values).lower(), axis=1)]
    if not res.empty:
        st.write(res)
    else:
        st.warning("No encontrado.")

if st.button("Cerrar Sesión"):
    auth.logout()
