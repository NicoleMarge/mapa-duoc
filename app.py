import streamlit as st
import pandas as pd
import os
import json
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero) ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC")

# --- 2. BYPASS DE SEGURIDAD (Creación de archivo de credenciales) ---
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
    st.error(f"Error creando archivo de seguridad: {e}")

# --- 3. CONFIGURACIÓN DE LA LIBRERÍA ---
# Inicializamos con el archivo recién creado
auth = Authenticate(
    secret_path=creds_path, 
    cookie_name='duoc_auth_cookie',
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1,
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
)

# Verificar estado de conexión
auth.check_authenticity()

if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Bienvenido. Para acceder al buscador de salas, por favor inicia sesión con tu cuenta institucional de Google.")
    
    # Este botón abre la ventana oficial de Google para pedir mail y clave
    auth.login()
    st.stop()

# --- 4. FILTRO DE SEGURIDAD: Solo correos @duocuc.cl ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error(f"Acceso denegado. El correo {user_email} no tiene permisos institucionales.")
        if st.button("Cerrar Sesión e intentar con otra cuenta"):
            auth.logout()
            st.rerun()
        st.stop()
else:
    st.error("No se pudo obtener información del usuario.")
    st.stop()

# --- 5. ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stTitle { font-size: 32px !important; font-weight: bold; color: #003366; }
    div.stButton > button { background-color: #003366; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Barra superior de usuario
col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🔍 Buscador de Salas y Dependencias")
with col_t2:
    st.write(f"👤 {user_email.split('@')[0]}")
    if st.button("Salir de la App"):
        auth.logout()
        st.rerun()

# --- 6. CARGA DE DATOS (Google Sheets) ---
@st.cache_data(ttl=600)
def cargar_datos_gsheets():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        # Formato correcto para exportar CSV desde Google Sheets
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        # Limpieza básica de columnas
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

df = cargar_datos_gsheets()

# --- 7. INTERFAZ DE BÚSQUEDA ---
st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">', unsafe_allow_html=True)
col_nav, col_busq = st.columns([4, 6])

with col_nav:
    seleccion = st.radio("Selecciona Edificio:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True)

with col_busq:
    search_query = st.text_input("¿Qué sala buscas?", placeholder="Ej: 412, Auditorio, Casino...")
st.markdown('</div>', unsafe_allow_html=True)

# --- 8. LÓGICA DE MAPAS Y RESULTADOS ---
img_path = None

if search_query and not df.empty:
    query = search_query.strip().upper()
    # Buscamos en las columnas 'sala' o 'nombre'
    resultado = df[
        df['sala'].astype(str).str.upper().str.contains(query, na=False) | 
        df['nombre'].astype(str).str.upper().str.contains(query, na=False)
    ]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        st.success(f"✅ **Sala {res['sala']}**: {res['nombre']}")
        st.info(f"📍 {res['edificio']} | Piso {res['piso']}")
        
        # Lógica para elegir la imagen según el edificio encontrado
        ed_val = str(res['edificio']).upper()
        num = "1"
        if any(x in ed_val for x in ["3", "III"]): num = "3"
        elif any(x in ed_val for x in ["2", "II"]): num = "2"
        img_path = os.path.join("imagenes", f"edificio{num}.jpg")
    else:
        st.warning(f"No se encontraron resultados para '{search_query}'.")
        img_path = os.path.join("imagenes", "general.jpg")
else:
    # Si no hay búsqueda, mostramos según el radio button
    if seleccion == "Inicio":
        img_path = os.path.join("imagenes", "general.jpg")
    else:
        num_sel = seleccion.split()[-1]
        img_path = os.path.join("imagenes", f"edificio{num_sel}.jpg")

# --- 9. RENDERIZADO DEL MAPA ---
if img_path:
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True, caption=f"Mapa: {os.path.basename(img_path)}")
    else:
        st.error(f"⚠️ No se encontró el archivo de imagen en la ruta: {img_path}")
