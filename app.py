import streamlit as st
import pandas as pd
import os
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC", page_icon="📍")

# --- 2. INICIALIZACIÓN DE AUTENTICACIÓN (SOLUCIÓN AL TYPEERROR) ---
# Pasamos los valores directamente en orden para evitar conflictos de nombres de argumentos
auth = Authenticate(
    st.secrets["google_oauth"]["client_id"],
    st.secrets["google_oauth"]["client_secret"],
    st.secrets["google_oauth"]["redirect_uri"],
    'duoc_auth_cookie', # cookie_name
    st.secrets["google_oauth"]["cookie_key"], # key
    1 # cookie_expiry_days
)

# Verificar si el usuario ya está autenticado
auth.check_authenticity()

if not st.session_state.get('connected'):
    # PANTALLA DE ACCESO
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Bienvenido. Para acceder, por favor inicia sesión con tu cuenta institucional de Google.")
    
    # Este botón abrirá la ventana oficial de Google para pedir usuario y contraseña
    auth.login()
    st.stop()

# --- 3. FILTRO DE SEGURIDAD @DUOCUC.CL ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email', '').lower()
    if not user_email.endswith('@duocuc.cl'):
        st.error(f"🚫 Acceso denegado. El correo {user_email} no pertenece a la institución.")
        if st.button("Cerrar Sesión e intentar con cuenta Duoc"):
            auth.logout()
            st.rerun()
        st.stop()
else:
    st.error("No se pudo recuperar la información del perfil.")
    st.stop()

# --- 4. DISEÑO Y BUSCADOR (ÁREA PRIVADA) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    .stTitle { color: #003366; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.title("🔍 Buscador de Salas y Dependencias")
with col_t2:
    st.write(f"👤 {user_email.split('@')[0]}")
    if st.button("Cerrar Sesión"):
        auth.logout()
        st.rerun()

# --- 5. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error("Error al conectar con la base de datos de salas.")
        return pd.DataFrame()

df = cargar_datos()

# --- 6. INTERFAZ DE BÚSQUEDA ---
st.markdown('---')
col_nav, col_busq = st.columns([4, 6])

with col_nav:
    seleccion = st.radio("Ver Edificios:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True)

with col_busq:
    search_query = st.text_input("Busca una sala o lugar:", placeholder="Ej: 412, Auditorio...")

img_path = None

if search_query and not df.empty:
    query = search_query.strip().upper()
    # Filtrar en las columnas del Excel
    resultado = df[
        df['sala'].astype(str).str.upper().str.contains(query, na=False) | 
        df['nombre'].astype(str).str.upper().str.contains(query, na=False)
    ]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        st.success(f"✅ **Sala {res['sala']}**: {res['nombre']}")
        st.info(f"📍 {res['edificio']} | Piso {res['piso']}")
        
        # Lógica de imágenes
        ed_val = str(res['edificio']).upper()
        num = "1"
        if any(x in ed_val for x in ["3", "III"]): num = "3"
        elif any(x in ed_val for x in ["2", "II"]): num = "2"
        img_path = os.path.join("imagenes", f"edificio{num}.jpg")
    else:
        st.warning("No se encontraron resultados.")
        img_path = os.path.join("imagenes", "general.jpg")
else:
    if seleccion == "Inicio":
        img_path = os.path.join("imagenes", "general.jpg")
    else:
        num_sel = seleccion.split()[-1]
        img_path = os.path.join("imagenes", f"edificio{num_sel}.jpg")

# --- 7. RENDERIZADO DEL MAPA ---
if img_path:
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.error(f"Archivo de imagen no encontrado: {img_path}")
