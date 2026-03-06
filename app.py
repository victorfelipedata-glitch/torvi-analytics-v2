# Importo las librerías que necesito
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore

# Configuro mi página
st.set_page_config(page_title="GALACTIC BET ANALYTICS", layout="wide")

# CSS para ocultar botones por defecto
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .main { background-color: #050814; }
    
    .titulo-futurista {
        font-family: 'Orbitron', sans-serif; color: #00f2ff;
        text-shadow: 0 0 5px #00f2ff, 0 0 15px #00f2ff, 0 0 30px #008cff;
        font-size: 4rem; font-weight: 900; text-align: center; margin-bottom: 0px; padding-top: 10px;
    }
    .subtitulo {
        color: #b3cce6; font-family: 'Orbitron', sans-serif; font-size: 1.2rem;
        text-align: center; letter-spacing: 4px; margin-bottom: 40px;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #0a1128, #000000); border: 1px solid #00f2ff;
        border-radius: 10px; padding: 20px; text-align: center;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.1); transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px); box-shadow: 0 0 25px rgba(0, 242, 255, 0.6);
    }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); margin: 30px 0; }
    
    div.stButton > button:first-child {
        background-color: #0a1128; color: #00f2ff; border: 1px solid #00f2ff; font-family: 'Orbitron', sans-serif;
    }
    div.stButton > button:first-child:hover {
        background-color: #00f2ff; color: #050814; box-shadow: 0 0 15px #00f2ff;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="titulo-futurista">GALACTIC BET</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE ANÁLISIS EV+ AVANZADO</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ==========================================
# 🔗 CONEXIÓN A MI BASE DE DATOS FIREBASE
# ==========================================
# Verifico si ya me conecté a Firebase para no conectarme dos veces y causar un error
if not firebase_admin._apps:
    # Leo mi llave secreta de la bóveda de Streamlit y la convierto a diccionario
    dict_claves = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(dict_claves)
    firebase_admin.initialize_app(cred)

# Abro el canal de comunicación con Firestore
db = firestore.client()

# Función para encriptar contraseñas (NUNCA guardo contraseñas en texto plano)
def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 🔐 MI SISTEMA DE SEGURIDAD VIP (LOGIN / REGISTRO)
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    col_vacia1, col_centro, col_vacia2 = st.columns([1, 2, 1])
    with col_centro:
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>🔐 TERMINAL DE ACCESO</h3>", unsafe_allow_html=True)
        
        # Creo dos pestañas para separar Login y Registro
        tab_login, tab_registro = st.tabs(["🚀 INICIAR SESIÓN", "📝 REGISTRARSE"])
        
        with tab_login:
            with st.form("form_login"):
                correo_login = st.text_input("📧 Correo Electrónico:")
                pass_login = st.text_input("🔑 Contraseña:", type="password")
                btn_login = st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True)
                
                if btn_login:
                    if correo_login and pass_login:
                        # Busco el documento del usuario en mi colección de Firebase
                        usuario_ref = db.collection('usuarios').document(correo_login).get()
                        
                        if usuario_ref.exists: # Si el usuario existe, verifico la contraseña
                            datos_usuario = usuario_ref.to_dict()
                            pass_encriptada = encriptar_password(pass_login)
                            
                            if datos_usuario['password'] == pass_encriptada:
                                st.session_state['autenticado'] = True
                                st.rerun() # Acceso concedido, recargo la página
                            else:
                                st.error("❌ Contraseña incorrecta.")
                        else:
                            st.error("❌ Este correo no está registrado en el sistema.")
                    else:
                        st.warning("⚠️ Ingresa tu correo y contraseña.")

        with tab_registro:
            with st.form("form_registro"):
                st.info("Crea una cuenta para acceder a mis pronósticos.")
                correo_nuevo = st.text_input("📧 Correo Electrónico:")
                pass_nueva = st.text_input("🔑 Crea una Contraseña:", type="password")
                pass_confirmar = st.text_input("🔑 Confirma tu Contraseña:", type="password")
                btn_registro = st.form_submit_button("CREAR CUENTA NUEVA", use_container_width=True)
                
                if btn_registro:
                    if correo_nuevo and pass_nueva and pass_confirmar:
                        if pass_nueva == pass_confirmar:
                            # Reviso que no me intenten clonar un correo
                            usuario_ref = db.collection('usuarios').document(correo_nuevo).get()
                            if usuario_ref.exists:
                                st.error("⚠️ Este correo ya tiene una cuenta. Ve a Iniciar Sesión.")
                            else:
                                # Guardo al usuario en mi Firebase
                                db.collection('usuarios').document(correo_nuevo).set({
                                    'correo': correo_nuevo,
                                    'password': encriptar_password(pass_nueva), # La guardo encriptada
                                    'rol': 'usuario_vip'
                                })
                                st.success("🎉 ¡Cuenta creada con éxito! Ve a la pestaña de Iniciar Sesión.")
                        else:
                            st.error("❌ Las contraseñas no coinciden.")
                    else:
                        st.warning("⚠️ Llena todos los campos para registrarte.")
    st.stop() # Detengo el sistema para que nadie vea la tabla sin entrar

# ==========================================
# 🚀 MI CÓDIGO PRINCIPAL (Solo se carga si entraron)
# ==========================================
sheet_url = f"https://docs.google.com/spreadsheets/d/12lDBRn6nXm4yvzjHhqL6w2FbCw8FPS1dYt5BoZYuP4w/export?format=csv&_={int(time.time())}"

try:
    df = pd.read_csv(sheet_url)
    if 'EV+' in df.columns and df['EV+'].dtype == 'object':
        df['EV+'] = df['EV+'].str.replace('%', '').astype(float)

    # Consola Lateral
    st.sidebar.markdown("<h2 style='text-align: center; font-family: Orbitron; color: #00f2ff;'>📟 CONSOLA</h2>", unsafe_allow_html=True)
    if st.sidebar.button("🔄 ACTUALIZAR DATOS EN VIVO", use_container_width=True):
        st.rerun()
        
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    mi_filtro = st.sidebar.text_input("🔍 Buscar Equipo o Partido:")
    
    # --- BOTÓN PARA CERRAR SESIÓN ---
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
        st.session_state['autenticado'] = False
        st.rerun()

    if mi_filtro:
        df = df[df['PARTIDO'].str.contains(mi_filtro, case=False, na=False) | df['MERCADO'].str.contains(mi_filtro, case=False, na=False)]

    # 1. TARJETAS DE MÉTRICAS
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        val_max = df['EV+'].max() if not df.empty and 'EV+' in df.columns else 0
        st.metric("🔥 MÁXIMO EV+", f"{val_max}%")
    with col2:
        st.metric("🎯 PICKS EN RADAR", len(df))
    with col3:
        st.metric("⚡ SISTEMA", "EN LÍNEA")
    with col4:
        st.metric("🛡️ FIABILIDAD", "ALTA")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. SECCIÓN DE BANKROLL
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>💰 CONTROL DE BANKROLL Y YIELD</h3>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bank_inicial = st.number_input("💵 Bank Inicial ($):", value=1000.0, step=100.0)
    with col_b2:
        stake_base = st.number_input("🪙 Stake Fijo ($):", value=50.0, step=10.0)
    
    if 'ESTATUS' in df.columns and 'CUOTA CASA' in df.columns:
        estatus_limpio = df['ESTATUS'].astype(str).str.lower()
        ganadas = df[estatus_limpio.str.contains('ganad|verde|win|aciert', na=False, regex=True)]
        perdidas = df[estatus_limpio.str.contains('perdid|rojo|loss|fall', na=False, regex=True)]
        
        ganancia_bruta = sum(stake_base * (float(cuota) - 1) for cuota in ganadas['CUOTA CASA'] if pd.notna(cuota))
        perdida_total = stake_base * len(perdidas)
        profit_neto = ganancia_bruta - perdida_total
        bank_actual = bank_inicial + profit_neto
        
        total_cerradas = len(ganadas) + len(perdidas)
        yield_roi = (profit_neto / (stake_base * total_cerradas)) * 100 if total_cerradas > 0 else 0

        met_col1, met_col2, met_col3, met_col4 = st.columns(4)
        with met_col1:
            st.metric("✅ ACERTADAS", len(ganadas))
        with met_col2:
            st.metric("❌ FALLADAS", len(perdidas))
        with met_col3:
            st.metric("📈 YIELD / ROI", f"{yield_roi:.2f}%")
        with met_col4:
            st.metric("🏦 BANK ACTUAL", f"${bank_actual:.2f}", delta=f"${profit_neto:.2f} Profit")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 3. GRÁFICA DE ESCÁNER DE VALOR
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>📊 ESCÁNER DE VALOR (EV+)</h3>", unsafe_allow_html=True)
    if not df.empty and 'MERCADO' in df.columns and 'EV+' in df.columns:
        fig = px.bar(df, x='EV+', y='MERCADO', orientation='h', color='EV+', text='EV+',
                     color_continuous_scale="PuBuGn", template="plotly_dark")
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Orbitron", color="#00f2ff"),
            xaxis_title="Valor Esperado (EV+ %)", yaxis_title="", showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    # 4. TABLA PRINCIPAL CRUDA
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>🛰️ BASE DE DATOS MAESTRA</h3>", unsafe_allow_html=True)
    df_mostrar = df.drop(columns=['ANALISIS']) if 'ANALISIS' in df.columns else df
    st.dataframe(df_mostrar, use_container_width=True, height=250)

    # 5. DESGLOSE TÁCTICO EXPANSIBLE
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>🧠 DESGLOSE TÁCTICO DE PICKS</h3>", unsafe_allow_html=True)
    if not df.empty:
        for index, row in df.iterrows():
            partido = row.get('PARTIDO', 'Desconocido')
            mercado = row.get('MERCADO', 'N/A')
            cuota = row.get('CUOTA CASA', 'N/A')
            ev = row.get('EV+', 0)
            analisis = row.get('ANALISIS', 'Sin análisis registrado.')
            estatus = str(row.get('ESTATUS', '')).upper()
            
            if any(palabra in estatus for palabra in ['GANAD', 'VERDE', 'WIN']): icon = "✅"
            elif any(palabra in estatus for palabra in ['PERDID', 'ROJO', 'LOSS']): icon = "❌"
            else: icon = "⏳"
            
            with st.expander(f"{icon} {partido}  |  MERCADO: {mercado}  |  CUOTA: {cuota}  |  ESTATUS: {estatus}"):
                st.markdown(f"""
                <div style='background-color: #0a1128; padding: 20px; border-left: 4px solid #00f2ff; border-radius: 0 10px 10px 0;'>
                    <p style='color: #ffffff; font-size: 1.1rem;'>{analisis}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="⬇️ DESCARGAR BASE DE DATOS", data=csv, file_name='galactic_picks.csv', mime='text/csv')

except Exception as e:
    st.warning("🛠️ **SISTEMA EN MANTENIMIENTO**")
    st.info("Nuestros algoritmos están siendo calibrados. Por favor, regresa en unos minutos.")
    print(f"⚠️ REPORTE DE ERROR PARA TORVI: {str(e)}")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; opacity: 0.8;'>© 2026 GALACTIC ANALYTICS | Desarrollado por Torvi Analytics</p>", unsafe_allow_html=True)
