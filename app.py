import streamlit as st
import pandas as pd
from streamlit_google_auth import Authenticate

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mapa Institucional Duoc UC", page_icon="📍")

# --- 2. INICIALIZACIÓN DE AUTENTICACIÓN ---
# Usamos los nombres de argumentos estándar para máxima compatibilidad
auth = Authenticate(
    client_id=st.secrets["google_oauth"]["client_id"],
    client_secret=st.secrets["google_oauth"]["client_secret"],
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
    cookie_name="google_auth_cookie",
    key=st.secrets["google_oauth"]["cookie_key"],
    cookie_expiry_days=1
)

# Verificar autenticidad al cargar
auth.check_authenticity()

# --- 3. LÓGICA DE CONTROL DE ACCESO ---
if not st.session_state.get('connected', False):
    # PANTALLA PÚBLICA DE LOGIN
    st.title("📍 Mapa Institucional Duoc UC")
    st.markdown("---")
    st.info("Bienvenido. Para acceder al buscador de salas, por favor inicia sesión con tu cuenta institucional.")
    
    # Este botón redirigirá a la página oficial de Google para pedir mail y clave
    auth.login()

else:
    # --- 4. ÁREA PRIVADA (Usuario ya autenticado por Google) ---
    user_info = st.session_state.get('user_info', {})
    user_email = user_info.get('email', '')

    # VALIDACIÓN ESTRICTA DE DOMINIO INSTITUCIONAL
    if not user_email.endswith("@duocuc.cl"):
        st.error(f"🚫 Acceso denegado. El correo **{user_email}** no está autorizado.")
        st.warning("Solo se permiten cuentas institucionales (@duocuc.cl).")
        if st.button("Intentar con otra cuenta"):
            auth.logout()
            st.rerun()
    else:
        # --- 5. APLICACIÓN PRINCIPAL (Acceso concedido) ---
        st.sidebar.success(f"Sesión activa: {user_info.get('name')}")
        if st.sidebar.button("Cerrar Sesión"):
            auth.logout()
            st.rerun()

        st.title("🔍 Buscador de Salas y Dependencias")
        
        # Conexión a Google Sheets usando el ID de los secretos
        @st.cache_data(ttl=600)
        def load_data():
            # Construimos la URL para descargar como CSV
            sheet_id = st.secrets["gsheet_id"]
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
            return pd.read_csv(url)

        try:
            df = load_data()
            
            busqueda = st.text_input("¿Qué sala o dependencia buscas?", placeholder="Ej: Sala 402, Casino, Biblioteca...")
            
            if busqueda:
                # Filtrado inteligente en todas las columnas
                mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
                resultados = df[mask]
                
                if not resultados.empty:
                    st.subheader("Resultados encontrados:")
                    st.dataframe(resultados, use_container_width=True)
                else:
                    st.error("No se encontraron resultados para esa búsqueda.")
            else:
                st.write("Ingresa un término arriba para ver la ubicación.")

        except Exception as e:
            st.error("Error técnico: No se pudo cargar la base de datos.")
            st.info("Asegúrate de que el ID del Google Sheet en los Secrets sea correcto y que la hoja sea 'Pública para cualquier persona con el enlace'.")
