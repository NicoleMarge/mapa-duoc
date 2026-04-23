import streamlit as st
import pandas as pd
import os
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE SEGURIDAD (OAuth) ---
# Los datos se extraen de los "Secrets" de Streamlit Cloud por seguridad
auth = Authenticate(
    secret_credentials_path=None,
    cookie_name='duoc_auth_cookie',
    cookie_key=st.secrets["google_oauth"]["cookie_key"],
    client_id=st.secrets["google_oauth"]["client_id"],
    client_secret=st.secrets["google_oauth"]["client_secret"],
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
)

# Revisar si el usuario ya está conectado
auth.check_authenticity()

if not st.session_state.get('connected'):
    st.title("📍 Mapa Institucional Duoc UC")
    st.info("Inicia sesión con tu correo institucional para continuar.")
    auth.login()
    st.stop()

# Validación de dominio de ciberseguridad: solo correos @duocuc.cl
user_email = st.session_state.get('user_info', {}).get('email', '')
if not user_email.endswith('@duocuc.cl'):
    st.error(f"Acceso denegado. El correo {user_email} no tiene permisos.")
    if st.button("Cerrar Sesión"):
        auth.logout()
    st.stop()

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide", page_title="Mapa Duoc UC")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    header {visibility: hidden;}
    .stTitle { font-size: 35px !important; font-weight: bold; padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado con Logout
col_t1, col_t2 = st.columns([9, 1])
with col_t1:
    st.title("Mapa Duoc UC")
with col_t2:
    if st.button("Salir"):
        auth.logout()

# --- 3. CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data
def cargar_datos_gsheets():
    # Debes poner el ID de tu Google Sheet en los Secrets como 'gsheet_url'
    # O reemplazarlo aquí directamente si es público
    try:
        # Formato para leer Google Sheets como CSV directamente
        sheet_id = st.secrets["gsheet_id"] 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error("Error conectando con la base de datos de salas.")
        return pd.DataFrame(columns=['sala', 'edificio', 'piso', 'nombre'])

df = cargar_datos_gsheets()

# --- 4. INTERFAZ: NAVEGACIÓN Y BÚSQUEDA ---
st.markdown('<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d1d1;">', unsafe_allow_html=True)
col_nav, col_busq = st.columns([6, 4])

with col_nav:
    seleccion = st.radio("Selecciona Edificio:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True)

with col_busq:
    search_query = st.text_input("Buscador de salas:", placeholder="Ej: 412 o Sala de Computación...")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# --- 5. LÓGICA DE VISUALIZACIÓN ---
img_path = None

if search_query:
    if not df.empty and 'sala' in df.columns:
        query = search_query.strip().upper()
        resultado = df[
            df['sala'].astype(str).str.upper().str.contains(query, na=False) | 
            df['nombre'].astype(str).str.upper().str.contains(query, na=False)
        ]
        
        if not resultado.empty:
            res = resultado.iloc[0]
            st.success(f"📍 **{res['sala']} - {res['nombre']}**")
            st.info(f"Ubicación: **{res['edificio']}**, Piso: **{res['piso']}**")
            
            ed_str = str(res['edificio']).upper()
            num = "1"
            if "III" in ed_str or "3" in ed_str: num = "3"
            elif "II" in ed_str or "2" in ed_str: num = "2"
            img_path = f"imagenes/edificio{num}.jpg"
        else:
            st.error(f"No se encontró la sala '{search_query}'.")
else:
    if seleccion == "Inicio":
        st.markdown("<h3 style='text-align: center;'>Plano General de Sede</h3>", unsafe_allow_html=True)
        img_path = "imagenes/general.jpg" 
    else:
        num_sel = seleccion.split()[-1]
        st.markdown(f"<h3 style='text-align: center;'>Vista: {seleccion}</h3>", unsafe_allow_html=True)
        img_path = f"imagenes/edificio{num_sel}.jpg"

# --- 6. MOSTRAR IMAGEN ---
if img_path and os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
elif img_path:
    st.warning("Mapa no disponible para esta selección.")