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

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

img_base64 = get_base64_image("imagenes/sede.jpg")
bg_style = f'background-image: url("data:image/jpg;base64,{img_base64}");' if img_base64 else 'background-color: #004680;'

st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{ visibility: hidden; height: 0%; }}
    [data-testid="stStatusWidget"], .stAppDeployButton {{ display: none !important; }}
    footer {{ display: none !important; }}
    .main {{ background-color: #ffffff; }}
    
    .header-container {{
        {bg_style}
        background-size: cover;
        background-position: center;
        padding: 60px 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 25px;
        box-shadow: inset 0 0 0 1000px rgba(0,0,0,0.2);
    }}
    
    .header-container h1 {{
        color: white !important;
        font-size: 50px !important;
        font-weight: bold !important;
        margin: 0;
        text-shadow: 3px 3px 10px rgba(0,0,0,0.8);
    }}

    .success-text {{ 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 12px; 
        border-radius: 8px; 
        font-weight: bold; 
        margin-bottom: 20px;
    }}

    /* Estilo para el recuadro de información de la imagen 8 */
    .info-card {{
        border: 2px solid #000000;
        padding: 20px;
        border-radius: 5px;
        background-color: white;
    }}

    div.stButton > button {{
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.95);
        color: #1a1a1a;
        font-weight: 700;
        border: 1px solid #e9ecef;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        width: 100%;
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
    except Exception:
        return pd.DataFrame()

df = cargar_datos_seguros()

def normalizar_edificio(nombre):
    n = str(nombre).upper()
    if 'III' in n or '3' in n: return "edificio3"
    elif 'II' in n or '2' in n: return "edificio2"
    elif 'I' in n or '1' in n: return "edificio1"
    return "general"

# ==========================================
# 3. INTERFAZ
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
    display_text = "" if st.session_state["busqueda_sala"] == "ACCION_ENFERMERIA_ZOCALO" else st.session_state["busqueda_sala"]
    nueva_busqueda = st.text_input("Buscador:", value=display_text, placeholder="Busca tu sala...", label_visibility="collapsed")
    if nueva_busqueda != display_text:
        st.session_state["busqueda_sala"] = nueva_busqueda

cat_cols = st.columns([1, 1, 1.3, 1.2, 1.2, 1.3, 2.7])
with cat_cols[0]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[1]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[2]: st.button("💡 Punto", on_click=cambiar_busqueda, args=("PUNTO ESTUDIANTIL",))
with cat_cols[3]: st.button("📚 Bibliot.", on_click=cambiar_busqueda, args=("BIBLIOTECA",))
with cat_cols[4]: st.button("🍴 Alim.", on_click=cambiar_busqueda, args=("ALIMENTACIÓN",))
with cat_cols[5]: st.button("🏥 Enferm.", on_click=cambiar_busqueda, args=("ACCION_ENFERMERIA_ZOCALO",))

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN (MODIFICADA)
# ==========================================
query_actual = st.session_state["busqueda_sala"]
resultados = pd.DataFrame()
titulo_seccion = ""

if query_actual == "ACCION_ENFERMERIA_ZOCALO":
    resultados = df[
        (df['nombre'].astype(str).str.lower().str.contains("enfermería|enfermeria", na=False)) & 
        (df['piso'].astype(str).str.lower().str.contains("zocalo", na=False))
    ]
    titulo_seccion = "ENFERMERÍA (PISO ZÓCALO)"
elif query_actual:
    q = query_actual.strip().lower()
    resultados = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    titulo_seccion = query_actual.upper()
elif seleccion_mapa != "Inicio":
    termino = "EDIFICIO I" if "1" in seleccion_mapa else "EDIFICIO II" if "2" in seleccion_mapa else "EDIFICIO III"
    resultados = df[df['edificio'].astype(str).str.upper().str.contains(termino, na=False)]
    titulo_seccion = termino

if not resultados.empty:
    st.markdown(f'<div class="success-text">✅ {titulo_seccion}</div>', unsafe_allow_html=True)
    
    # Si hay múltiples resultados (como al filtrar por edificio)
    if len(resultados) > 1 and query_actual != "ACCION_ENFERMERIA_ZOCALO":
        col_tabla, col_mapa = st.columns([5, 5])
        with col_tabla:
            st.markdown("### Opciones Disponibles")
            vista = resultados[['nombre', 'edificio', 'piso']].copy()
            vista.columns = ['Lugar', 'Edificio', 'Piso']
            st.write(vista.reset_index(drop=True).to_html(index=False, escape=False), unsafe_allow_html=True)
        with col_mapa:
            archivo = normalizar_edificio(resultados.iloc[0].get('edificio', ''))
            st.image(f"imagenes/{archivo}.jpg", use_container_width=True)
    
    # Si es un resultado único (como buscar "lc3" o usar el botón Enfermería)
    else:
        res = resultados.iloc[0]
        col_info, col_mapa = st.columns([5, 5])
        
        with col_info:
            # Estructura visual de la imagen de referencia
            st.markdown(f"""
                <div class="info-card">
                    <h3>Información del recinto seleccionado</h3>
                    <br>
                    <h1 style='font-size: 40px;'>{str(res['nombre']).upper()}</h1>
                    <hr>
                    <h2 style='color: #004680;'>{str(res['edificio']).upper()}</h2>
                </div>
            """, unsafe_allow_html=True)
            
        with col_mapa:
            archivo = normalizar_edificio(res['edificio'])
            st.image(f"imagenes/{archivo}.jpg", use_container_width=True)

elif seleccion_mapa == "Inicio":
    st.image("imagenes/general.jpg", use_container_width=True)
