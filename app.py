import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA (VISUAL)
# ==========================================
st.set_page_config(
    page_title="Mapa Duoc UC", 
    layout="wide", 
    page_icon="📍"
)

# Inyección de CSS para replicar la visual limpia de la referencia
st.markdown("""
    <style>
    /* Fondo blanco y ocultar header por defecto de Streamlit */
    .main { background-color: #ffffff; }
    header {visibility: hidden;}
    
    /* Título principal grande y negrita */
    .stTitle { 
        font-size: 35px !important; 
        font-weight: bold; 
        padding-bottom: 20px; 
        color: #000000;
    }
    
    /* Estilo para los subtítulos de los edificios */
    .titulo-edificio {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
        color: #333333;
    }
    
    /* Contenedor oscuro para la barra de navegación y búsqueda */
    .nav-container {
        background-color: #1e1e1e; 
        padding: 15px; 
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    /* Asegurar que el texto dentro del contenedor oscuro sea legible */
    .nav-container div[data-testid="stRadio"] > label {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Mapa Duoc UC")

# ==========================================
# 2. CONEXIÓN SEGURA A GOOGLE SHEETS
# ==========================================
# Mantenemos tu lógica original para datos privados y seguros
@st.cache_data(ttl=86400)  # Caché de 24 horas para rendimiento
def cargar_datos_seguros():
    try:
        # Permisos necesarios
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Autenticación usando Secrets de Streamlit Cloud (Seguridad ante todo)
        creds = Credentials.from_service_account_info(
            st.secrets["gsheets"],
            scopes=scope
        )

        client = gspread.authorize(creds)

        # Nombre EXACTO del Google Sheet privado
        # Asegúrate de que el JSON de la cuenta de servicio tenga acceso a este sheet
        sheet = client.open("Base de Datos Salas Duoc").sheet1

        data = sheet.get_all_records()

        # Convertir a DataFrame y normalizar columnas a minúsculas
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.lower()

        return df

    except Exception as e:
        # Solo mostrar error si hay problemas de conexión, no si el usuario no busca nada
        st.error(f"❌ Error crítico de seguridad al conectar con la base de datos: {e}")
        return pd.DataFrame()

# Cargar los datos una sola vez
df = cargar_datos_seguros()

# ==========================================
# 3. INTERFAZ SUPERIOR: NAVEGACIÓN Y BÚSQUEDA
# ==========================================
# Creamos el contenedor oscuro para replicar la visual de la referencia
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
col_nav, col_busq = st.columns([6, 4])

with col_nav:
    # Navegación horizontal por botones de radio
    seleccion = st.radio(
        "Ver Edificio:", # Etiqueta oculta pero útil para accesibilidad
        ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], 
        horizontal=True,
        label_visibility="collapsed" # Ocultamos la etiqueta para la visual limpia
    )

with col_busq:
    # Campo de búsqueda de sala
    search_query = st.text_input(
        "Buscador:", # Etiqueta oculta
        placeholder="Busca tu sala (ej: 412)...",
        label_visibility="collapsed"
    )
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---") # Línea divisoria

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN DE MAPAS
# ==========================================
img_path = None

# Prioridad 1: Si el usuario escribe en el buscador
if search_query:
    if not df.empty and 'sala' in df.columns:
        query = search_query.strip().upper()
        # Búsqueda flexible (contiene texto) para coincidir con "PA-412" si escriben "412"
        resultado = df[df['sala'].astype(str).str.upper().str.contains(query, na=False)]
        
        if not resultado.empty:
            res = resultado.iloc[0]
            
            # Obtener datos para el mensaje de éxito
            sala_id = res.get('sala', search_query)
            nombre_sala = res.get('nombre', 'Sala de clases')
            edificio_nom = res.get('edificio', '-')
            piso_num = res.get('piso', '-')

            # Mensaje de éxito visual
            st.success(f"📍 **{sala_id} - {nombre_sala}** encontrada en el **{edificio_nom}**, **Piso {piso_num}**")
            
            # Lógica para identificar qué mapa de edificio mostrar
            ed_str = str(edificio_nom).upper()
            num = "1" # Por defecto
            if "III" in ed_str or "3" in ed_str: num = "3"
            elif "II" in ed_str or "2" in ed_str: num = "2"
            
            # Ruta de la imagen del edificio específico
            img_path = f"imagenes/edificio{num}.jpg"
        else:
            st.error(f"No se encontró la sala '{search_query}' en la base de datos segura.")
    elif df.empty:
        st.warning("La base de datos está vacía o no se pudo cargar.")

# Prioridad 2: Si no hay búsqueda, mostramos según la navegación por botones
else:
    if seleccion == "Inicio":
        st.markdown('<p class="titulo-edificio">Plano General de Sedes</p>', unsafe_allow_html=True)
        img_path = "imagenes/general.jpg" # Mapa con los tres edificios
    else:
        # Extraer el número del edificio (ej: "Edificio 2" -> "2")
        num_sel = seleccion.split()[-1]
        st.markdown(f'<p class="titulo-edificio">{seleccion}</p>', unsafe_allow_html=True)
        img_path = f"imagenes/edificio{num_sel}.jpg" # Mapa del edificio individual

# ==========================================
# 5. MOSTRAR LA IMAGEN DEL MAPA
# ==========================================
# Verificación de ciberseguridad: el archivo debe existir en el repositorio
if img_path:
    if os.path.exists(img_path):
        # use_container_width=True asegura que la imagen se adapte al ancho de la página
        st.image(img_path, use_container_width=True)
    else:
        # Mensaje si falta algún mapa por subir a GitHub
        st.info(f"Falta subir la imagen correspondiente a: {img_path}")
