# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Mapa Duoc UC", layout="wide", initial_sidebar_state="collapsed")

# Definimos la ruta de la imagen que está en tu carpeta de GitHub
# Si tu imagen se llama 'sede.jpg' y está en la carpeta 'imagenes', la ruta es:
img_path = "imagenes/image_f20e58.jpg" 

st.markdown(f"""
    <style>
    /* Contenedor principal del encabezado con imagen local */
    .header-container {{
        background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("app/static/{img_path}");
        background-size: cover;
        background-position: center;
        padding: 60px 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        text-align: left;
    }}
    
    /* Título blanco con sombra para legibilidad */
    .header-container h1 {{
        color: white !important;
        font-size: 50px !important;
        font-weight: bold !important;
        margin: 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
    }}

    /* Estilo de los botones sobre la imagen */
    div.stButton > button {{
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.95);
        color: #1a1a1a;
        font-weight: 700;
        border: none;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }}
    
    /* Estilo para los radio buttons (Inicio, Edificio 1, etc) */
    .stRadio > label {{ 
        color: white !important; 
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}
    </style>
    
    <div class="header-container">
        <h1>Mapa Duoc UC</h1>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. INTERFAZ SUPERIOR (Radio y Buscador)
# ==========================================
col_nav, col_bus = st.columns([6, 4])
with col_nav:
    seleccion_mapa = st.radio("Navegación:", ["Inicio", "Edificio 1", "Edificio 2", "Edificio 3"], 
                              horizontal=True, label_visibility="collapsed", on_change=limpiar_todo)

with col_bus:
    st.text_input("Buscador:", placeholder="Busca tu sala...", label_visibility="collapsed", key="busqueda_sala")

# Botones de categorías (Redistribuidos para el nuevo diseño)
cat_cols = st.columns([1, 1, 1.2, 1.2, 1.2, 4])
with cat_cols[0]: st.button("🚻 Baños", on_click=cambiar_busqueda, args=("Baño",))
with cat_cols[1]: st.button("🎓 CASE", on_click=cambiar_busqueda, args=("CASE",))
with cat_cols[2]: st.button("💡 Punto Estudiantil", on_click=cambiar_busqueda, args=("PUNTO ESTUDIANTIL",))
with cat_cols[3]: st.button("📚 Biblioteca", on_click=cambiar_busqueda, args=("BIBLIOTECA",))
with cat_cols[4]: st.button("☕ Alimentación", on_click=cambiar_busqueda, args=("ALIMENTACIÓN",))

st.markdown("---")
