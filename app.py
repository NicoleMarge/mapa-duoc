import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA (ESTILO VISUAL)
# ==========================================
st.set_page_config(page_title="Mapa Duoc UC", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stTitle { 
        font-size: 35px !important; 
        font-weight: bold; 
        padding-bottom: 20px; 
    }
    div[data-testid="stRadio"] > label {
        color: #555;
        font-weight: bold;
    }
    div[data-testid="stTextInput"] {
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .info-recinto-title { font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px;}
    .big-font { font-size: 24px !important; font-weight: bold; margin-bottom: 15px;}
    .info-label { font-weight: bold; color: #555; margin-right: 5px; }
    .success-text { color: #155724; background-color: #d4edda; border-color: #c3e6cb; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 15px;}
    </style>
    """, unsafe_allow_html=True)

st.title("Mapa Duoc UC")

# ==========================================
# 2. CONEXIÓN SEGURA A GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=86400)
def cargar_datos_seguros():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Base de Datos Salas Duoc").sheet1
        data = sheet.get_all_records()
        
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"❌ Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

df = cargar_datos_seguros()

# Función para normalizar nombres de edificios (Convierte Romano a Número)
def normalizar_nombre_edificio(nombre):
    nombre = str(nombre).upper()
    if 'EDIFICIO I' in nombre and 'II' not in nombre: return "edificio1"
    if 'EDIFICIO II' in nombre: return "edificio2"
    if 'EDIFICIO III' in nombre: return "edificio3"
    # Si ya viene como número o texto simple:
    return nombre.lower().replace(" ", "")

# ==========================================
# 3. INTERFAZ SUPERIOR: NAVEGACIÓN Y BÚSQUEDA
# ==========================================
col_nav, col_bus = st.columns([6, 4])

with col_nav:
    seleccion_mapa = st.radio(
        "Navegación:",
        ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"],
        horizontal=True,
        label_visibility="collapsed"
    )

with col_bus:
    query = st.text_input(
        "Buscador de salas:", 
        placeholder="Busca tu sala (ej: 412)...",
        label_visibility="collapsed"
    )

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN
# ==========================================
img_to_show = None

if query and not df.empty:
    q = query.strip().lower()
    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        sala_id = str(res.get('sala', 'N/A')).upper()
        nombre_sala = res.get('nombre', 'Sala de clases')
        edificio_nom = str(res.get('edificio', 'Edificio 1'))
        piso_num = res.get('piso', 'N/A')
        
        st.markdown(f'<div class="success-text">✅ {sala_id} - {nombre_sala} encontrada en el **{edificio_nom}**, Piso {piso_num}</div>', unsafe_allow_html=True)

        col_info, col_mapa = st.columns([4, 6])

        with col_info:
            st.markdown('<p class="info-recinto-title">Información seleccionada</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="big-font">{sala_id} - {nombre_sala}</p>', unsafe_allow_html=True)
            st.markdown(f'<p><span class="info-label">🏢 Edificio:</span> {edificio_nom}</p>', unsafe_allow_html=True)
            st.markdown(f'<p><span class="info-label">📍 Piso:</span> {piso_num}</p>', unsafe_allow_html=True)
            
            tipo_recinto = res.get('tipo', '-')
            st.markdown(f'<p><span class="info-label">🏷️ Tipo:</span> {tipo_recinto}</p>', unsafe_allow_html=True)
            st.markdown("---")
            descripcion = res.get('descripcion', '-')
            st.markdown(f'<span class="info-label">📝 Descripción:</span><br>{descripcion}', unsafe_allow_html=True)

        with col_mapa:
            # USAMOS LA FUNCIÓN DE NORMALIZACIÓN AQUÍ
            nombre_archivo = normalizar_nombre_edificio(edificio_nom)
            img_to_show = f"imagenes/{nombre_archivo}.jpg"
            
            if os.path.exists(img_to_show):
                st.image(img_to_show, use_container_width=True)
            else:
                st.error(f"Archivo no encontrado: {img_to_show}")

    else:
        st.warning(f"No se encontraron resultados para '{query}'")

else:
    col_vacia_izq, col_mapa_gen, col_vacia_der = st.columns([1, 8, 1])

    with col_mapa_gen:
        if seleccion_mapa == "Inicio":
            st.markdown("<h3 style='text-align: center;'>Plano General de Sedes</h3>", unsafe_allow_html=True)
            img_to_show = "imagenes/general.jpg"
        else:
            nombre_archivo_sel = normalizar_nombre_edificio(seleccion_mapa)
            st.markdown(f"<h3 style='text-align: center;'>Plano {seleccion_mapa}</h3>", unsafe_allow_html=True)
            img_to_show = f"imagenes/{nombre_archivo_sel}.jpg"
        
        if img_to_show and os.path.exists(img_to_show):
            st.image(img_to_show, use_container_width=True)
        elif img_to_show:
             st.info(f"Imagen {img_to_show} no encontrada en el repositorio.")
