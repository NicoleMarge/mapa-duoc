import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import base64
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Mapa Duoc UC", layout="wide", initial_sidebar_state="collapsed")

# Función para convertir la imagen local a Base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

# Intentamos cargar la imagen de la sede para el banner
img_base64 = get_base64_image("imagenes/sede.jpg")
bg_style = f'background-image: url("data:image/jpg;base64,{img_base64}");' if img_base64 else 'background-color: #004680;'

st.markdown(f"""
    <style>
    /* --- ELIMINACIÓN TOTAL DE ELEMENTOS DE STREAMLIT (GITHUB, MANAGE APP, CORONA) --- */
    
    /* Oculta el header superior completo (GitHub, Share, Menú) */
    header[data-testid="stHeader"] {{
        visibility: hidden;
        display: none !important;
    }}

    /* Oculta el botón Manage App, la corona de marca de agua y el footer */
    [data-testid="stAppDeployButton"], 
    .stAppDeployButton, 
    footer, 
    #MainMenu, 
    .viewerBadge_container__1QSob, 
    .viewerBadge_link__1S137,
    div[data-testid="stStatusWidget"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* Ajuste de márgenes para que la app aproveche todo el espacio superior */
    .block-container {{
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 95%;
    }}

    .main {{ background-color: #ffffff; }}
    
    /* --- DISEÑO DEL BANNER PERSONALIZADO --- */
    .header-container {{
        {bg_style}
        background-size: cover;
        background-position: center;
        padding: 50px 20px;
        border-radius: 15px;
        color: white;
        margin-top: 1rem;
        margin-bottom: 25px;
        text-align: left;
        box-shadow: inset 0 0 0 1000px rgba(0,0,0,0.2);
    }}
    
    .header-container h1 {{
        color: white !important;
        font-size: 45px !important;
        font-weight: bold !important;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }}

    /* Botones de categorías */
    div.stButton > button {{
        border-radius: 10px;
        background-color: #f8f9fa;
        color: #333;
        font-weight: 600;
        border: 1px solid #ddd;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
        transition: 0.3s;
    }}
    
    div.stButton > button:hover {{
        border-color: #004680;
        color: #004680;
        transform: translateY(-1px);
    }}

    /* Cuadros de aviso de éxito */
    .success-text {{ 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 12px; 
        border-radius: 10px; 
        font-weight: bold; 
        margin-bottom: 15px;
    }}
    </style>
    
    <div class="header-container">
        <h1>Mapa Duoc UC</h1>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A DATOS (GOOGLE SHEETS)
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
    except Exception:
        return pd.DataFrame()

df = cargar_datos_seguros()

def normalizar_edificio(nombre):
    n = str(nombre).upper().strip()
    if 'III' in n or '3' in n: return "edificio3"
    elif 'II' in n or '2' in n: return "edificio2"
    elif 'I' in n or '1' in n: return "edificio1"
    return "general"

# ==========================================
# 3. INTERFAZ Y ESTADO DE SESIÓN
# ==========================================
if "busqueda_sala" not in st.session_state:
    st.session_state["busqueda_sala"] = ""

def cambiar_busqueda(texto):
    st.session_state["busqueda_sala"] = texto

def limpiar_todo():
    st.session_state["busqueda_sala"] = ""

col_nav, col_bus = st.columns([6, 4])
with col_nav:
    seleccion_mapa = st.radio("Navegación:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], 
                              horizontal=True, label_visibility="collapsed", on_change=limpiar_todo)

with col_bus:
    st.text_input("Buscador:", placeholder="Busca tu sala o lugar...", label_visibility="collapsed", key="busqueda_sala")

# Botones Rápidos (Categorías)
cat_cols = st.columns([1, 1, 1, 1, 1, 4])
with cat_cols[0]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[1]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[2]: st.button("💡 Punto", on_click=cambiar_busqueda, args=("Punto",))
with cat_cols[3]: st.button("📚 Biblio", on_click=cambiar_busqueda, args=("Biblioteca",))
with cat_cols[4]: st.button("☕ Comida", on_click=cambiar_busqueda, args=("Alimentación",))

st.markdown("---")

# ==========================================
# 4. LÓGICA DE BÚSQUEDA Y MAPAS
# ==========================================
query_actual = st.session_state["busqueda_sala"]

if query_actual and not df.empty:
    q = query_actual.strip().lower()
    # Buscamos en todas las columnas
    resultados = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultados.empty:
        if len(resultados) > 1:
            st.markdown(f'<div class="success-text">🔍 Se encontraron {len(resultados)} coincidencias para: {query_actual.upper()}</div>', unsafe_allow_html=True)
            col_tabla, col_mapa = st.columns([5, 5])
            with col_tabla:
                tabla_vista = resultados[['nombre', 'edificio', 'piso']].copy()
                tabla_vista.columns = ['Lugar', 'Edificio', 'Piso']
                st.table(tabla_vista)
            with col_mapa:
                st.image("imagenes/general.jpg", use_container_width=True)
        else:
            res = resultados.iloc[0]
            edificio_val = str(res.get('edificio', ''))
            st.markdown(f'<div class="success-text">✅ Encontrado: {res.get("nombre", "").upper()}</div>', unsafe_allow_html=True)
            col_info, col_mapa = st.columns([4, 6])
            with col_info:
                st.write(f"### Detalle")
                st.write(f"**Lugar:** {res.get('nombre', 'N/A')}")
                st.write(f"**Edificio:** {edificio_val}")
                st.write(f"**Piso:** {res.get('piso', 'N/A')}")
            with col_mapa:
                nombre_archivo = normalizar_edificio(edificio_val)
                st.image(f"imagenes/{nombre_archivo}.jpg", use_container_width=True)
    else:
        st.warning(f"No hay resultados para '{query_actual}'")
else:
    # Si no hay búsqueda, mostramos el mapa según la navegación radial
    archivo_sel = "general" if seleccion_mapa == "Inicio" else normalizar_edificio(seleccion_mapa)
    st.image(f"imagenes/{archivo_sel}.jpg", use_container_width=True)
