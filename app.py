import streamlit as st
import json
import os
from streamlit_google_auth import Authenticate

# 1. CREAR EL ARCHIVO DE SECRETOS AL VUELO
# Esto soluciona el FileNotFoundError
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

# Escribimos el archivo en el sistema temporal de Streamlit
with open("client_secrets.json", "w") as f:
    json.dump(creds_dict, f)

# 2. CONFIGURAR LA AUTENTICACIÓN
auth = Authenticate(
    secret_path="client_secrets.json", 
    cookie_name="google_auth_cookie",
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1,
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
)

# 3. LÓGICA DE LOGIN
auth.check_authenticity()

if not st.session_state.get('connected', False):
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Bienvenido. Por favor, inicia sesión con tu cuenta institucional.")
    auth.login() # Esto renderiza el botón azul
else:
    # AQUÍ VA EL RESTO DE TU CÓDIGO (El buscador de salas, etc.)
    st.success(f"Bienvenido, {st.session_state['user_info']['name']}")
    if st.button("Cerrar Sesión"):
        auth.logout()
