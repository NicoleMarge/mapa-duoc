import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Mapa Duoc UC", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stTitle { font-size: 35px !important; font-weight: bold; padding-bottom: 20px; }
    
    .categoria-tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 5px 3px;
        border-radius: 15px;
        background-color: #f8f9fa;
        color: #444;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .success-text { 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 10px; 
        border-radius: 5px; 
        font-weight: bold; 
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Mapa Duoc UC")

# ==========================================
# 2. CONEXIÓN A DATOS
# ==========================================
@st.cache_data(ttl=86400)
def cargar_datos_seguros():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Base de Datos Salas Duoc").sheet1
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_datos_seguros()

def normalizar_edificio(nombre):
    nombre = str(nombre).upper()
    if 'EDIFICIO I' in nombre and 'II' not in nombre: return "edificio1"
    if 'EDIFICIO II' in nombre: return "edificio2"
    if 'EDIFICIO III' in nombre: return "edificio3"
    return nombre.lower().replace(" ", "")

# ==========================================
# 3. INTERFAZ SUPERIOR (LÓGICA DE LIMPIEZA)
# ==========================================

# Creamos una función para limpiar el buscador al hacer clic en los edificios
def limpiar_buscador():
    st.session_state["busqueda_sala"] = ""

col_nav, col_bus = st.columns([6, 4])

with col_nav:
    # Si seleccionamos un edificio, se dispara 'limpiar_buscador'
    seleccion_mapa = st.radio(
        "Navegación:", 
        ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], 
        horizontal=True, 
        label_visibility="collapsed",
        on_change=limpiar_buscador
    )

with col_bus:
    # Vinculamos el texto del buscador al session_state
    if "busqueda_sala" not in st.session_state:
        st.session_state["busqueda_sala"] = ""
    
    query = st.text_input(
        "Buscador:", 
        placeholder="Busca tu sala (ej: LC3)...", 
        label_visibility="collapsed",
        key="busqueda_sala"
    )

# --- CATEGORÍAS ---
st.markdown("""
    <div>
        <span class="categoria-tag">📖 Salas</span>
        <span class="categoria-tag">🚻 Baños</span>
        <span class="categoria-tag">🎓 CASE</span>
        <span class="categoria-tag">💡 Punto Estudiantil</span>
        <span class="categoria-tag">📚 Biblioteca</span>
        <span class="categoria-tag">☕ Alimentación</span>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN
# ==========================================

# Solo buscamos sala SI hay algo escrito. Si acabas de cambiar de edificio, query estará vacío.
if query and not df.empty:
    q = query.strip().lower()
    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        edificio_nom = str(res.get('edificio', 'Edificio 1'))
        
        st.markdown(f'<div class="success-text">✅ {res.get("sala", "").upper()} encontrada en el **{edificio_nom}**</div>', unsafe_allow_html=True)

        col_info, col_mapa = st.columns([4, 6])
        with col_info:
            st.markdown("### Información seleccionada")
            st.write(f"**Sala:** {str(res.get('sala', 'N/A')).upper()}")
            st.write(f"**Edificio:** {edificio_nom}")
            st.write(f"**Piso:** {res.get('piso', 'N/A')}")
        
        with col_mapa:
            archivo = normalizar_edificio(edificio_nom)
            ruta = f"imagenes/{archivo}.jpg"
            if os.path.exists(ruta):
                st.image(ruta, use_container_width=True)
            else:
                st.info(f"Cargando mapa... ({archivo}.jpg)")
    else:
        st.warning(f"No se encontró información para '{query}'")

else:
    # Vista por defecto según navegación (Se activa al cambiar de botón)
    if seleccion_mapa == "Inicio":
        st.markdown("<h3 style='text-align: center;'>Plano General de Sedes</h3>", unsafe_allow_html=True)
        img = "imagenes/general.jpg"
    else:
        archivo_sel = normalizar_edificio(seleccion_mapa)
        st.markdown(f"<h3 style='text-align: center;'>{seleccion_mapa}</h3>", unsafe_allow_html=True)
        img = f"imagenes/{archivo_sel}.jpg"
    
    if os.path.exists(img):
        st.image(img, use_container_width=True)
    else:
        st.error(f"No se encontró la imagen: {img}")
