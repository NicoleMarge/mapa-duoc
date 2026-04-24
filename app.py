import streamlit as st
import json
import os
from streamlit_google_auth import Authenticate

# 1. GENERACIÓN DINÁMICA DEL ARCHIVO DE CREDENCIALES
# Esto evita el FileNotFoundError en Streamlit Cloud al usar los Secrets
creds_dict = {
    "web": {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
    }
}

# Escribimos el archivo temporalmente en el servidor
with open("client_secrets.json", "w") as f:
    json.dump(creds_dict, f)

# 2. CONFIGURACIÓN DE LA AUTENTICACIÓN
# Usamos 'secrets_path' (con s) para la versión 1.1.8 de la librería
auth = Authenticate(
    secrets_path="client_secrets.json", 
    cookie_name="google_auth_cookie",
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1,
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
)

# 3. LÓGICA DE LA APLICACIÓN
# Verificamos si el usuario ya está autenticado
auth.check_authenticity()

if not st.session_state.get('connected', False):
    # Pantalla de Bienvenida y Login
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Bienvenido. Por favor, inicia sesión con tu cuenta institucional.")
    
    # Renderiza el botón azul de Google
    auth.login() 
else:
    # --- ÁREA PRIVADA (Solo visible tras loguearse) ---
    st.sidebar.success(f"Usuario: {st.session_state['user_info'].get('name', 'Usuario')}")
    
    if st.sidebar.button("Cerrar Sesión"):
        auth.logout()
        st.rerun()

    st.title("Buscador de Salas y Dependencias")
    st.write("¡Has ingresado correctamente!")
    
    # Aquí puedes insertar tu lógica de búsqueda de salas o Google Sheets
    # Ejemplo:
    # st.write(f"ID de la planilla: {st.secrets['gsheet_id']}")
