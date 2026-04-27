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
    
    div.stButton > button {
        border-radius: 15px;
        background-color: #f8f9fa;
        color: #444;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #e9ecef;
        padding: 4px 12px;
        height: auto;
    }
    div.stButton > button:hover {
        border-color: #004680;
        color: #004680;
        background-color: #eef6ff;
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
cat_cols = st.columns([1, 1, 1, 1.2, 1.2, 1.2, 3])
with cat_cols[0]: st.button("📖 Salas", on_click=cambiar_busqueda, args=("Salas",))
with cat_cols[1]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[2]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[3]: st.button("💡 Punto Estudiantil", on_click=cambiar_busqueda, args=("Punto Estudiantil",))
with cat_cols[4]: 
    # UNICO CAMBIO: Se actualizó el argumento a "BIBLIOTECA"
    st.button("📚 Biblioteca", on_click=cambiar_busqueda, args=("BIBLIOTECA",))
with cat_cols[5]: 
    st.button("☕ Alimentación", on_click=cambiar_busqueda, args=("ALIMENTACIÓN",))

st.markdown("---")

# ==========================================
# 4. LÓGICA DE VISUALIZACIÓN MULTI-RESULTADO
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
                st.image("imagenes/general.jpg", use_container_width=True, caption="Ubicación General")
        
        else:
            res = resultados.iloc[0]
            edificio_valor = str(res.get('edificio', ''))
            st.markdown(f'<div class="success-text">✅ Encontrado: **{res.get("nombre", "").upper()}**</div>', unsafe_allow_html=True)
            
            col_info, col_mapa = st.columns([4, 6])
            with col_info:
                st.markdown("### Detalles de Ubicación")
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
