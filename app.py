import streamlit as st
import pandas as pd
import os
import json
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero) ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC", page_icon="📍")

# --- 2. GENERACIÓN DEL ARCHIVO DE CREDENCIALES ---
creds_path = "client_secrets.json"
try:
    with open(creds_path, "w") as f:
        json.dump({
            "web": {
                "client_id": st.secrets["google_oauth"]["client_id"],
                "client_secret": st.secrets["google_oauth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
            }
        }, f)
except Exception as e:
    st.error(f"Error técnico de credenciales: {e}")

# --- 3. INICIALIZACIÓN DE AUTENTICACIÓN ---
# Corregido: Usamos 'secret_path' y pasamos los argumentos en el orden exacto de la v1.1.8
auth = Authenticate(
    secret_path=creds_path, 
    cookie_name='duoc_auth_cookie',
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1,
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
)

# Verificar si el usuario ya está logueado
auth.check_authenticity()

if not st.session_state.get('connected'):
    # PANTALLA DE ACCESO (Pública)
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Bienvenido. Para acceder, inicia sesión con tu cuenta institucional de Google.")
    
    # Este botón activará el flujo de Usuario/Contraseña oficial de Google
    auth.login()
    st.stop()

# --- 4. VALIDACIÓN DE DOMINIO @DUOCUC.CL ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error(f"🚫 Acceso denegado. El correo {user_email} no es institucional.")
        if st.button("Intentar con otra cuenta"):
            auth.logout()
            st.rerun()
        st.stop()
else:
    st.error("Error al recuperar perfil de usuario.")
    st.stop()

# --- 5. INTERFAZ DE LA APLICACIÓN (Privada) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    .stTitle { color: #003366; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado
col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🔍 Buscador de Salas")
with col_t2:
    st.write(f"👤 {user_email.split('@')[0]}")
    if st.button("Cerrar Sesión"):
        auth.logout()
        st.rerun()

# --- 6. CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error("Error al conectar con Google Sheets.")
        return pd.DataFrame()

df = cargar_datos()

# --- 7. BUSCADOR Y MAPAS ---
st.markdown('---')
col_nav, col_busq = st.columns([4, 6])

with col_nav:
    seleccion = st.radio("Ver Edificio:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True)

with col_busq:
    search_query = st.text_input("Buscar por sala o nombre:", placeholder="Ej: 412...")

img_path = None

if search_query and not df.empty:
    query = search_query.strip().upper()
    resultado = df[
        df['sala'].astype(str).str.upper().str.contains(query, na=False) | 
        df['nombre'].astype(str).str.upper().str.contains(query, na=False)
    ]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        st.success(f"✅ **Sala {res['sala']}**: {res['nombre']}")
        st.info(f"📍 {res['edificio']} | Piso {res['piso']}")
        
        ed_val = str(res['edificio']).upper()
        num = "1"
        if any(x in ed_val for x in ["3", "III"]): num = "3"
        elif any(x in ed_val for x in ["2", "II"]): num = "2"
        img_path = os.path.join("imagenes", f"edificio{num}.jpg")
    else:
        st.warning("No se encontraron resultados.")
        img_path = os.path.join("imagenes", "general.jpg")
else:
    # Lógica por botones de edificio
    if seleccion == "Inicio":
        img_path = os.path.join("imagenes", "general.jpg")
    else:
        num_sel = seleccion.split()[-1]
        img_path = os.path.join("imagenes", f"edificio{num_sel}.jpg")

# --- 8. MOSTRAR IMAGEN ---
if img_path:
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.error(f"Archivo no encontrado: {img_path}")
