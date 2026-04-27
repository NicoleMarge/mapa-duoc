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

# Intentamos cargar la imagen de la sede
img_base64 = get_base64_image("imagenes/sede.jpg")
bg_style = f'background-image: url("data:image/jpg;base64,{img_base64}");' if img_base64 else 'background-color: #004680;'

st.markdown(f"""
    <style>
    /* 1. OCULTAR ELEMENTOS DE INTERFAZ DE STREAMLIT */
    header[data-testid="stHeader"] {{
        visibility: hidden;
        height: 0%;
    }}
    
    .stAppDeployButton {{
        display: none !important;
    }}

    /* 2. AJUSTE DE MÁRGENES GENERALES */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }}

    .main {{ background-color: #ffffff; }}
    
    /* 3. ENCABEZADO (BANNER) */
    .header-container {{
        {bg_style}
        background-size: cover;
        background-position: center;
        padding: 60px 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 25px;
        text-align: left;
        box-shadow: inset 0 0 0 1000px rgba(0,0,0,0.1);
    }}
    
    .header-container h1 {{
        color: white !important;
        font-size: 50px !important;
        font-weight: bold !important;
        margin: 0;
        text-shadow: 3px 3px 10px rgba(0,0,0,0.8);
    }}

    /* 4. BOTONES DE CATEGORÍAS */
    div.stButton > button {{
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.95);
        color: #1a1a1a;
        font-weight: 700;
        border: 1px solid #e9ecef;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        transition: all 0.3s;
        margin-bottom: 5px;
    }}
    
    div.stButton > button:hover {{
        border-color: #004680;
        color: #004680;
        transform: translateY(-2px);
    }}

    /* 5. CUADROS DE MENSAJES Y RESULTADOS */
    .success-text {{ 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 10px; 
        border-radius: 8px; 
        font-weight: bold; 
        margin-top: 10px;
        margin-bottom: 15px;
    }}
    
    .stRadio > label {{ 
        color: #444 !important; 
        font-weight: bold !important;
    }}
    </style>
    
    <div class="header-container">
        <h1>Mapa Duoc UC</h1>
    </div>
    """, unsafe_allow_html=True)

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
        return pd.DataFrame()

df = cargar_datos_seguros()

def normalizar_edificio(nombre):
    n = str(nombre).upper().strip()
    if 'III' in n or '3' in n: return "edificio3"
    elif 'II' in n or '2' in n: return "edificio2"
    elif 'I' in n or '1' in n: return "edificio1"
    return "general"

# ==========================================
# 3. INTERFAZ SUPERIOR Y ESTADO
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
    st.text_input("Buscador:", placeholder="Busca tu sala...", label_visibility="collapsed", key="busqueda_sala")

# --- CATEGORÍAS ---
cat_cols = st.columns([1, 1, 1.2, 1.2, 1.2, 4])
with cat_cols[0]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[1]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[2]: st.button("💡 Punto Estudiantil", on_click=cambiar_busqueda, args=("PUNTO ESTUDIANTIL",))
with cat_cols[3]: st.button("📚 Biblioteca", on_click=cambiar_busqueda, args=("BIBLIOTECA",))
with cat_cols[4]: st.button("☕ Alimentación", on_click=cambiar_busqueda, args=("ALIMENTACIÓN",))

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN
# ==========================================
query_actual = st.session_state["busqueda_sala"]

if query_actual and not df.empty:
    q = query_actual.strip().lower()
    resultados = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultados.empty:
        if len(resultados) > 1:
            st.markdown(f'<div class="success-text">✅ Se encontraron {len(resultados)} opciones para: **{query_actual.upper()}**</div>', unsafe_allow_html=True)
            col_tabla, col_mapa = st.columns([5, 5])
            with col_tabla:
                st.markdown("### Opciones Disponibles")
                tabla_vista = resultados[['nombre', 'edificio', 'piso']].copy()
                tabla_vista.columns = ['Lugar', 'Edificio', 'Piso']
                st.table(tabla_vista)
            with col_mapa:
                st.image("imagenes/general.jpg", use_container_width=True)
        else:
            res = resultados.iloc[0]
            edificio_valor = str(res.get('edificio', ''))
            st.markdown(f'<div class="success-text">✅ Encontrado: **{res.get("nombre", "").upper()}**</div>', unsafe_allow_html=True)
            col_info, col_mapa = st.columns([4, 6])
            with col_info:
                st.markdown("### Detalles de Ubicación")
                st.write(f"**Nombre:** {res.get('nombre', 'N/A')}")
                st.write(f"**Edificio:** {edificio_valor}")
                st.write(f"**Piso:** {res.get('piso', 'N/A')}")
            with col_mapa:
                nombre_archivo = normalizar_edificio(edificio_valor)
                st.image(f"imagenes/{nombre_archivo}.jpg", use_container_width=True)
    else:
        st.warning(f"No se encontró información para '{query_actual}'")
else:
    archivo_sel = "general" if seleccion_mapa == "Inicio" else normalizar_edificio(seleccion_mapa)
    st.image(f"imagenes/{archivo_sel}.jpg", use_container_width=True)
