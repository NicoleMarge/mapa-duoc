import streamlit as st
import pandas as pd
import os
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE SEGURIDAD (OAuth) ---
# Extraemos los datos de secrets primero para asegurar que existen y son strings
try:
    client_id = str(st.secrets["google_oauth"]["client_id"])
    client_secret = str(st.secrets["google_oauth"]["client_secret"])
    redirect_uri = str(st.secrets["google_oauth"]["redirect_uri"])
    cookie_key = str(st.secrets["google_oauth"]["cookie_key"])
except KeyError as e:
    st.error(f"Error: No se encontró la llave {e} en los Secrets de Streamlit.")
    st.stop()

# Inicialización de Autenticación
# Nota: Algunos entornos requieren que no se pasen parámetros nulos
auth = Authenticate(
    cookie_name='duoc_auth_cookie',
    cookie_key=cookie_key,
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri
)

# Revisar estado de autenticación
auth.check_authenticity()

if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Bienvenido. Por favor, inicia sesión con tu cuenta institucional.")
    auth.login()
    st.stop()

# Filtro de seguridad: Solo correos @duocuc.cl
user_email = st.session_state.get('user_info', {}).get('email', '').lower()
if not user_email.endswith('@duocuc.cl'):
    st.error(f"Acceso denegado. El correo {user_email} no pertenece a la institución.")
    if st.button("Cerrar Sesión"):
        auth.logout()
    st.stop()

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    header {visibility: hidden;}
    .stTitle { font-size: 32px !important; font-weight: bold; color: #003366; }
    </style>
    """, unsafe_allow_html=True)

# Barra superior
col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("📍 Buscador de Salas")
with col_t2:
    st.write(f"👤 {user_email.split('@')[0]}")
    if st.button("Salir"):
        auth.logout()

# --- 3. CARGA DE DATOS (GOOGLE SHEETS) ---
@st.cache_data(ttl=600)
def cargar_datos_gsheets():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return pd.DataFrame()

df = cargar_datos_gsheets()

# --- 4. INTERFAZ ---
st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">', unsafe_allow_html=True)
col_nav, col_busq = st.columns([5, 5])

with col_nav:
    seleccion = st.radio("Explorar Edificio:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True)

with col_busq:
    search_query = st.text_input("¿Qué sala buscas?", placeholder="Ej: 412 o Auditorio")
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. LÓGICA DE MAPAS ---
img_path = None

if search_query and not df.empty:
    query = search_query.strip().upper()
    resultado = df[
        df['sala'].astype(str).str.upper().str.contains(query, na=False) | 
        df['nombre'].astype(str).str.upper().str.contains(query, na=False)
    ]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        st.success(f"✅ **{res['sala']}**: {res['nombre']}")
        st.info(f"📍 {res['edificio']} | Piso: {res['piso']}")
        
        ed_val = str(res['edificio']).upper()
        num = "1"
        if any(x in ed_val for x in ["3", "III"]): num = "3"
        elif any(x in ed_val for x in ["2", "II"]): num = "2"
        img_path = os.path.join("imagenes", f"edificio{num}.jpg")
    else:
        st.warning(f"No encontramos '{search_query}'.")
else:
    if seleccion == "Inicio":
        img_path = os.path.join("imagenes", "general.jpg")
    else:
        num_sel = seleccion.split()[-1]
        img_path = os.path.join("imagenes", f"edificio{num_sel}.jpg")

# --- 6. RENDERIZADO ---
if img_path:
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.error(f"Falta archivo: {img_path}")
