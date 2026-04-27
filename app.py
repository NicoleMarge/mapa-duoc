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
    
    /* Estilo para etiquetas de categorías (Salas, Baños, etc.) */
    .categoria-tag {
        display: inline-block;
        padding: 5px 12px;
        margin: 5px;
        border-radius: 20px;
        background-color: #f0f2f6;
        color: #333;
        font-weight: bold;
        font-size: 14px;
        border: 1px solid #ddd;
    }
    
    .success-text { 
        color: #155724; 
        background-color: #d4edda; 
        border: 1px solid #c3e6cb; 
        padding: 10px; 
        border-radius: 5px; 
        font-weight: bold; 
        margin-bottom: 15px;
    }
    .info-label { font-weight: bold; color: #555; }
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

# Traductor de nombres para archivos JPG
def normalizar_edificio(nombre):
    nombre = str(nombre).upper()
    if 'EDIFICIO I' in nombre and 'II' not in nombre: return "edificio1"
    if 'EDIFICIO II' in nombre: return "edificio2"
    if 'EDIFICIO III' in nombre: return "edificio3"
    return nombre.lower().replace(" ", "")

# ==========================================
# 3. BUSCADOR Y NAVEGACIÓN
# ==========================================
col_nav, col_bus = st.columns([6, 4])

with col_nav:
    seleccion_mapa = st.radio("Navegación:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], horizontal=True, label_visibility="collapsed")

with col_bus:
    query = st.text_input("Buscador:", placeholder="Busca tu sala o dependencia...", label_visibility="collapsed")

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN
# ==========================================
if query and not df.empty:
    q = query.strip().lower()
    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        edificio_nom = str(res.get('edificio', 'Edificio 1'))
        
        st.markdown(f'<div class="success-text">✅ Ubicación encontrada en el **{edificio_nom}**</div>', unsafe_allow_html=True)

        col_info, col_mapa = st.columns([4, 6])

        with col_info:
            st.subheader("Información del recinto")
            st.write(f"**Sala:** {str(res.get('sala', 'N/A')).upper()}")
            st.write(f"**Nombre:** {res.get('nombre', 'N/A')}")
            st.write(f"**Piso:** {res.get('piso', 'N/A')}")
            
            st.markdown("---")
            # --- NUEVA SECCIÓN DE CATEGORÍAS SOLICITADAS ---
            st.write("**Dependencias cercanas:**")
            st.markdown("""
                <span class="categoria-tag">📖 Salas</span>
                <span class="categoria-tag">🚻 Baños</span>
                <span class="categoria-tag">🎓 CASE</span>
                <span class="categoria-tag">💡 Punto Estudiantil</span>
                <span class="categoria-tag">📚 Biblioteca</span>
            """, unsafe_allow_html=True)

        with col_mapa:
            archivo = normalizar_edificio(edificio_nom)
            ruta = f"imagenes/{archivo}.jpg"
            if os.path.exists(ruta):
                st.image(ruta, use_container_width=True)
            else:
                st.warning(f"Mostrando mapa base... ({archivo}.jpg)")

    else:
        st.warning(f"No se encontró información para '{query}'")

else:
    # Vista General de Inicio o Edificios seleccionados
    col_vacia, col_mapa_gen, col_vacia2 = st.columns([1, 8, 1])
    with col_mapa_gen:
        if seleccion_mapa == "Inicio":
            st.markdown("<h3 style='text-align: center;'>Plano General de Sedes</h3>", unsafe_allow_html=True)
            img = "imagenes/general.jpg"
        else:
            archivo_sel = normalizar_edificio(seleccion_mapa)
            st.markdown(f"<h3 style='text-align: center;'>Plano {seleccion_mapa}</h3>", unsafe_allow_html=True)
            img = f"imagenes/{archivo_sel}.jpg"
        
        if os.path.exists(img):
            st.image(img, use_container_width=True)
            # También mostramos las categorías en la vista general para que el usuario sepa qué buscar
            st.markdown("<br><p style='text-align: center; color: gray;'>Categorías disponibles:</p>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center;'>"
                        "<span class='categoria-tag'>📖 Salas</span>"
                        "<span class='categoria-tag'>🚻 Baños</span>"
                        "<span class='categoria-tag'>🎓 CASE</span>"
                        "<span class='categoria-tag'>💡 Punto Estudiantil</span>"
                        "<span class='categoria-tag'>📚 Biblioteca</span>"
                        "</div>", unsafe_allow_html=True)
