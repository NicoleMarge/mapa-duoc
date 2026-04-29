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

# Carga de imagen de encabezado
img_base64 = get_base64_image("imagenes/sede.jpg")
bg_style = f'background-image: url("data:image/jpg;base64,{img_base64}");' if img_base64 else 'background-color: #004680;'

st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{ visibility: hidden; height: 0%; }}
    [data-testid="stStatusWidget"], .stAppDeployButton, [data-testid="stAppDeployButton"] {{ display: none !important; }}
    footer {{ display: none !important; }}
    #MainMenu {{visibility: hidden;}}

    .block-container {{ padding-top: 2rem !important; padding-bottom: 1rem !important; }}
    .main {{ background-color: #ffffff; }}
    
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

    div.stButton > button {{
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.95);
        color: #1a1a1a;
        font-weight: 700;
        border: 1px solid #e9ecef;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }}
    
    .success-text {{ 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 10px; 
        border-radius: 8px; 
        font-weight: bold; 
        margin-bottom: 15px;
    }}

    .map-container {{
        border: 2px solid #888;
        border-radius: 4px;
        overflow: hidden;
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
# 3. INTERFAZ SUPERIOR
# ==========================================
if "busqueda_sala" not in st.session_state:
    st.session_state["busqueda_sala"] = ""

def cambiar_busqueda(texto):
    st.session_state["busqueda_sala"] = texto

def limpiar_busqueda():
    st.session_state["busqueda_sala"] = ""

col_nav, col_bus = st.columns([6, 4])
with col_nav:
    seleccion_mapa = st.radio("Navegación:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], 
                              horizontal=True, label_visibility="collapsed", on_change=limpiar_busqueda)

with col_bus:
    st.text_input("Buscador:", placeholder="Busca tu sala...", label_visibility="collapsed", key="busqueda_sala")

# Categorías
cat_cols = st.columns([1, 1, 1.2, 1.2, 1.2, 4])
with cat_cols[0]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[1]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[2]: st.button("💡 Punto Estudiantil", on_click=cambiar_busqueda, args=("PUNTO ESTUDIANTIL",))
with cat_cols[3]: st.button("📚 Biblioteca", on_click=cambiar_busqueda, args=("BIBLIOTECA",))
with cat_cols[4]: st.button("☕ Alimentación", on_click=cambiar_busqueda, args=("ALIMENTACIÓN",))

st.markdown("---")

# ==========================================
# 4. LÓGICA DE FILTRADO UNIFICADA
# ==========================================
query_actual = st.session_state["busqueda_sala"]
resultados = pd.DataFrame()
titulo_filtro = ""

# Prioridad 1: Si hay algo escrito en el buscador o se presionó un botón de categoría
if query_actual and not df.empty:
    q = query_actual.strip().lower()
    resultados = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    titulo_filtro = query_actual.upper()

# Prioridad 2: Si se seleccionó un Edificio en el Radio Button (Círculo Rojo)
elif seleccion_mapa != "Inicio" and not df.empty:
    if "1" in seleccion_mapa: 
        termino = "EDIFICIO I"
    elif "2" in seleccion_mapa: 
        termino = "EDIFICIO II"
    else: 
        termino = "EDIFICIO III"
    
    resultados = df[df['edificio'].astype(str).str.upper().str.contains(termino, na=False)]
    titulo_filtro = termino

# --- RENDERIZADO DE RESULTADOS ---
if not resultados.empty:
    # Banner verde
    st.markdown(f'<div class="success-text">✅ Se encontraron {len(resultados)} opciones para: **{titulo_filtro}**</div>', unsafe_allow_html=True)
    
    # Si hay múltiples resultados o es una vista de edificio completo
    if len(resultados) > 1 or seleccion_mapa != "Inicio":
        col_tabla, col_mapa = st.columns([5, 5])
        with col_tabla:
            st.markdown(f"### Opciones Disponibles para: {titulo_filtro}")
            tabla_vista = resultados[['nombre', 'edificio', 'piso']].copy()
            tabla_vista.columns = ['Lugar', 'Edificio', 'Piso']
            st.table(tabla_vista)
            
        with col_mapa:
            ed_ref = str(resultados.iloc[0].get('edificio', ''))
            nombre_archivo = normalizar_edificio(ed_ref)
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st.image(f"imagenes/{nombre_archivo}.jpg", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    # Si es un resultado único (Búsqueda específica de sala)
    else:
        res = resultados.iloc[0]
        col_info, col_mapa = st.columns([4, 6])
        with col_info:
            st.markdown("### Detalles de Ubicación")
            st.write(f"**Nombre:** {res.get('nombre', 'N/A')}")
            st.write(f"**Edificio:** {res.get('edificio', 'N/A')}")
            st.write(f"**Piso:** {res.get('piso', 'N/A')}")
        with col_mapa:
            nombre_archivo = normalizar_edificio(res.get('edificio', ''))
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st.image(f"imagenes/{nombre_archivo}.jpg", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# CASO: Inicio o sin resultados
else:
    if seleccion_mapa == "Inicio" and not query_actual:
        st.image("imagenes/general.jpg", use_container_width=True)
    elif query_actual:
        st.warning(f"No se encontró información para '{query_actual}'")
