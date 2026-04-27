import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA (ESTILO VISUAL)
# ==========================================
st.set_page_config(page_title="Mapa Duoc UC", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizado para replicar tu referencia limpia
st.markdown("""
    <style>
    /* Fondo blanco y tipografía limpia */
    .main { background-color: #ffffff; }
    
    /* Título principal grande */
    .stTitle { 
        font-size: 35px !important; 
        font-weight: bold; 
        padding-bottom: 20px; 
    }
    
    /* Estilo para los botones de navegación */
    div[data-testid="stRadio"] > label {
        color: #555;
        font-weight: bold;
    }
    
    /* Contenedor del buscador */
    div[data-testid="stTextInput"] {
        background-color: #f8f9fa;
        border-radius: 5px;
    }

    /* Estilo tarjeta de información */
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
@st.cache_data(ttl=86400) # Caché de 24 horas (Seguridad y Rendimiento)
def cargar_datos_seguros():
    try:
        # Permisos necesarios (Ciberseguridad)
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Autenticación usando Secrets (No hardcodear credenciales)
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
        client = gspread.authorize(creds)

        # Nombre EXACTO de tu Google Sheet privado
        sheet = client.open("Base de Datos Salas Duoc").sheet1
        data = sheet.get_all_records()
        
        # Convertir a DataFrame y normalizar columnas a minúsculas
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.lower()
        return df

    except Exception as e:
        st.error(f"❌ Error crítico de seguridad al conectar con la base de datos: {e}")
        return pd.DataFrame()

# Cargar los datos una sola vez
df = cargar_datos_seguros()

# ==========================================
# 3. INTERFAZ SUPERIOR: NAVEGACIÓN Y BÚSQUEDA
# ==========================================

# Usamos columnas para colocar la navegación y el buscador en la misma línea
col_nav, col_bus = st.columns([6, 4]) # 60% Navegación, 40% Buscador

with col_nav:
    # Navegación horizontal replicando tu referencia
    seleccion_mapa = st.radio(
        "Navegación:",
        ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"],
        horizontal=True,
        label_visibility="collapsed" # Ocultamos la etiqueta para visual limpia
    )

with col_bus:
    query = st.text_input(
        "Buscador de salas:", 
        placeholder="Busca tu sala (ej: LC3)...",
        label_visibility="collapsed"
    )

st.markdown("---") # Línea divisoria

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN
# ==========================================
img_to_show = None

# Prioridad 1: Búsqueda de sala (si el usuario busca, ignora la navegación de arriba)
if query and not df.empty:
    q = query.strip().lower()
    
    # Búsqueda flexible en todas las columnas
    resultado = df[df.apply(lambda row: q in str(row.values).lower(), axis=1)]
    
    if not resultado.empty:
        res = resultado.iloc[0]
        
        # Extracción segura de datos normalizados
        sala_id = str(res.get('sala', 'N/A')).upper() # PA-LC3
        nombre_sala = res.get('nombre', 'Sala de clases')
        edificio_nom = res.get('edificio', 'Edificio') # Ej: EDIFICIO 1
        piso_num = res.get('piso', 'N/A')
        
        # Mensaje de éxito visual arriba
        st.markdown(f'<div class="success-text">✅ {sala_id} - {nombre_sala} encontrada en el **{edificio_nom}**, Piso {piso_num}</div>', unsafe_allow_html=True)

        # Diseño de Tarjeta de Información y Mapa (Columnas)
        col_info, col_mapa = st.columns([4, 6]) # 40% info, 60% mapa

        with col_info:
            st.markdown('<p class="info-recinto-title">Información del recinto seleccionado</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="big-font">{sala_id} - {nombre_sala}</p>', unsafe_allow_html=True)
            
            st.markdown(f'<p><span class="info-label">🏢 Edificio:</span> {edificio_nom}</p>', unsafe_allow_html=True)
            st.markdown(f'<p><span class="info-label">📍 Piso:</span> {piso_num}</p>', unsafe_allow_html=True)
            
            # Datos opcionales según tu Google Sheet
            tipo_recinto = res.get('tipo', '-')
            st.markdown(f'<p><span class="info-label">🏷️ Tipo:</span> {tipo_recinto}</p>', unsafe_allow_html=True)

            st.markdown("---")
            descripcion = res.get('descripcion', '-')
            st.markdown(f'<span class="info-label">📝 Descripción:</span><br>{descripcion}', unsafe_allow_html=True)

        with col_mapa:
            # --- LÓGICA DE MAPA PARA BÚSQUEDA ---
            # Limpiamos el texto del edificio: "EDIFICIO 1" -> "edificio1"
            nombre_archivo_edificio = edificio_nom.lower().replace(" ", "")
            # Aseguramos que sea "edificio1" y no "edificio" a secas
            if not any(char.isdigit() for char in nombre_archivo_edificio):
                # Si no tiene número, intentamos extraerlo del nombre de la sala si PA-LC3
                 if sala_id.startswith('PA-'):
                     nombre_archivo_edificio += sala_id.split('-')[1][2:] # Muy frágil, mejor limpiar base de datos
            
            img_to_show = f"imagenes/{nombre_archivo_edificio}.png"
            
            # Mostramos la imagen ocupando todo el ancho de su columna
            if os.path.exists(img_to_show):
                st.image(img_to_show, use_column_width=True)
            else:
                st.info(f"Falta subir la imagen del mapa a GitHub: {img_to_show}")

    else:
        st.warning(f"No se encontraron resultados para '{query}'")

# Prioridad 2: Navegación de botones superior (si no hay búsqueda activa)
else:
    col_vacia_izq, col_mapa_gen, col_vacia_der = st.columns([1, 8, 1]) # Centrar el mapa general

    with col_mapa_gen:
        if seleccion_mapa == "Inicio":
            st.markdown("<h3 style='text-align: center;'>Plano General de Sedes</h3>", unsafe_allow_html=True)
            img_to_show = "imagenes/general.png"
        else:
            # Replicamos la lógica: "Edificio 2" -> "edificio2.png"
            nombre_archivo_sel = seleccion_mapa.lower().replace(" ", "")
            st.markdown(f"<h3 style='text-align: center;'>Plano {seleccion_mapa}</h3>", unsafe_allow_html=True)
            img_to_show = f"imagenes/{nombre_archivo_sel}.png"
        
        # Mostrar el mapa (use_column_width=True para que ocupe todo su espacio centrado)
        if img_to_show and os.path.exists(img_to_show):
            st.image(img_to_show, use_column_width=True)
        elif img_to_show:
             st.info(f"Falta subir la imagen del mapa a GitHub: {img_to_show}")
