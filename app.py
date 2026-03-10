import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid

# Configuro mi página
st.set_page_config(page_title="AXIOM DATA", layout="wide")

# Ligas Globales
LIGAS_FUTBOL = [
    "Champions League", "Europa League", "Conference League", 
    "Liga Inglesa", "Championship", "Liga Española", 
    "Liga Italiana", "Liga Alemana", "Liga Francesa", 
    "Liga Portuguesa", "Liga Países Bajos", "Liga MX", 
    "Liga Turca", "Liga Dinamarca", "Liga Grecia", "Liga Árabe", "Otra"
]

# CSS Estilo Galáctico
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1); border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.2) !important; border-bottom: 2px solid #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# Conexión Firebase
if not firebase_admin._apps:
    dict_claves = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(dict_claves)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Seguridad y Sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'

st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; padding: 20px; background: rgba(0,242,255,0.05); border-radius: 20px; border: 1px solid rgba(0,242,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>👋 ¡Hola de nuevo!</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b3cce6;'>Ingresa para ver el radar de valor.</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🚀 LOGIN", "📝 REGISTRO"])
        with t1:
            with st.form("f_login"):
                u = st.text_input("Correo electrónico:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("INICIAR SESIÓN", use_container_width=True):
                    u_limpio = u.strip()
                    if u_limpio: 
                        try:
                            res = db.collection('usuarios').document(u_limpio).get()
                            if res.exists and res.to_dict().get('password') == encriptar_password(p):
                                st.session_state['autenticado'] = True
                                st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                                st.rerun()
                            else: st.error("Credenciales incorrectas.")
                        except: st.error("Error al validar datos.")
                    else: st.warning("Ingresa tu correo.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME", use_container_width=True):
                    un_limpio = un.strip()
                    if un_limpio and pn:
                        db.collection('usuarios').document(un_limpio).set({'correo': un_limpio, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                        st.success("¡Cuenta creada!")
                    else: st.warning("Completa los campos.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- CARGA DE DATOS ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = []
for d in docs:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
    if 'id' not in item: item['id'] = str(uuid.uuid4()) 
    if 'deporte' not in item: item['deporte'] = 'Fútbol' 
    if 'liga' not in item: item['liga'] = 'Otra' 
    if 'tipo' not in item: item['tipo'] = 'Sencilla' # Identificador de Parlay
    data.append(item)

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'tipo', 'deporte', 'liga', 'partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'fecha'])

if not df.empty:
    df['ev'] = pd.to_numeric(df['ev'], errors='coerce').fillna(0)
    df['cuota'] = pd.to_numeric(df['cuota'], errors='coerce').fillna(0)
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

# --- SIDEBAR ---
st.sidebar.title("📟 CONSOLA")
st.sidebar.write(f"Usuario: {st.session_state['user_rol'].upper()}")
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.rerun()

# --- PANEL DE ADMIN (AHORA CON PARLAYS) ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ PANEL DE CONTROL (AGREGAR PRONÓSTICO)"):
        with st.form("nuevo_pick"):
            st.markdown("#### ⚙️ Configuración del Pronóstico")
            es_parlay = st.toggle("🔗 ¿Es una Combinada (Parlay)?")
            tipo_pick = "Combinada" if es_parlay else "Sencilla"
            
            c_cat1, c_cat2 = st.columns(2)
            deporte = c_cat1.selectbox("🏆 Deporte:", ["Fútbol", "NBA", "Mixto (Parlay)"])
            liga = c_cat2.selectbox("🌍 Liga / Torneo:", LIGAS_FUTBOL + ["Múltiples Ligas"]) if deporte in ["Fútbol", "Mixto (Parlay)"] else c_cat2.selectbox("🌍 Torneo:", ["Temporada Regular NBA", "Playoffs NBA"])
            
            st.markdown("#### 📝 Detalles de la Jugada")
            if es_parlay:
                partido = st.text_area("⚽/🏀 Partidos (Uno por línea):", placeholder="Ej:\nCity vs Liverpool\nLakers vs Bulls")
                mercado = st.text_area("🎯 Mercados (Uno por línea):", placeholder="Ej:\nCity ML\nLebron +25.5 Pts")
            else:
                c_a, c_b = st.columns(2)
                partido = c_a.text_input("⚽/🏀 Encuentro:", placeholder="Ej: Man City vs Liverpool")
                mercado = c_b.text_input("🎯 Mercado:", placeholder="Ej: +4.5 Tiros a Puerta")
            
            st.markdown("#### 🧮 Matemáticas")
            c_n1, c_n2, c_n3, c_n4 = st.columns(4)
            cuota = c_n1.number_input("📈 Cuota Total:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = c_n2.number_input("🏦 Prob. Casa %:", value=50.0)
            prob_real = c_n3.number_input("🎯 Prob. Real %:", value=60.0)
            ev_val = c_n4.number_input("🔥 EV+ %:", value=10.0)
            
            ana = st.text_area("🧠 Análisis Táctico:")
            if st.form_submit_button("🚀 PUBLICAR EN EL RADAR"):
                p_id = str(uuid.uuid4())
                db.collection('pronosticos').document(p_id).set({
                    'id': p_id, 'tipo': tipo_pick, 'deporte': deporte, 'liga': liga, 'partido': partido, 'mercado': mercado, 
                    'cuota': float(cuota), 'prob_casa': float(prob_casa), 'prob_real': float(prob_real), 'ev': float(ev_val),
                    'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("Publicado con éxito.")
                st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    # Filtros de estado
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas de la parte superior
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MÁXIMA VENTAJA", max_ev)
    m2.metric("🎯 PICKS ACTIVOS", len(df_activos))
    # Bankroll dinámico basado en historial
    ganancias = len(df_historial[df_historial['estatus'] == 'GANADA']) * 80 # Asumiendo ganancia promedio
    perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA']) * 100
    bank_total = 1000 + ganancias - perdidas
    m3.metric("🏦 MI CAPITAL (BANK)", f"${bank_total:,.2f}")
    
    # NUEVA ESTRUCTURA DE PESTAÑAS VIP
    tab_futbol, tab_parlay, tab_historial, tab_tools = st.tabs(["⚽ FÚTBOL", "💎 PARLAY DIARIO", "📈 RENDIMIENTO", "🧮 TOOLS"])
    
    with tab_futbol:
        if not df_activos.empty:
            st.markdown("<h4 style='color: #00f2ff; font-family: Orbitron;'>🛰️ RADAR DE SEÑALES</h4>", unsafe_allow_html=True)
            for i, r in df_activos.iterrows():
                # Limpiamos el título quitando [SENCILLA] o etiquetas raras
                titulo_limpio = r['partido'].replace("[SENCILLA] ", "").replace("[Otra] ", "")
                with st.expander(f"📍 {titulo_limpio} | {r['mercado']} | EV+: {r['ev']}%"):
                    st.markdown(f"<p style='color: #bc13fe; font-size: 0.85rem;'>PROB. REAL: {r.get('prob_real',0)}% | CUOTA: {r['cuota']}</p>", unsafe_allow_html=True)
                    st.info(r.get('analisis', 'Analizando datos tácticos...'))
                    if st.session_state['user_rol'] == 'admin':
                        ca, cb = st.columns(2)
                        if ca.button(f"✅ Ganó", key=f"w_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdió", key=f"l_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
        else:
            st.info("Buscando nuevas ventajas en las ligas europeas...")

    with tab_parlay:
        st.markdown("<div style='background: linear-gradient(45deg, #1a0b2e, #bc13fe33); padding: 20px; border-radius: 15px; border: 1px solid #bc13fe;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ffcc00; font-family: Orbitron;'>⭐ PARLAY VIP DEL DÍA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Esta sección solo es visible para miembros con acceso de alta ventaja.</p>", unsafe_allow_html=True)
        
        # Aquí puedes filtrar por picks que tengan la palabra "Parlay" en el nombre
        df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False)]
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                st.success(f"🚀 {p['mercado']} - Momio: {p['cuota']}")
                st.write(p['analisis'])
        else:
            st.markdown("<p style='text-align: center; opacity: 0.5;'>Cocinando la combinada de hoy... ⏳</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_historial:
        if not df_historial.empty:
            # Gráfica de crecimiento
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            st.markdown(f"### Win Rate Global: {wr:.1f}%")
            # Gráfica simple de barras por estatus
            resumen = df_historial.groupby('estatus').size().reset_index(name='cantidad')
            fig_h = px.pie(resumen, values='cantidad', names='estatus', color='estatus',
                           color_discrete_map={'GANADA': '#00ff00', 'PERDIDA': '#ff0000'},
                           hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("El historial se construye con tus aciertos.")

    with tab_tools:
        st.markdown("### 🧮 CALCULADORAS DE GESTIÓN")
        # Aquí pones el código de tus calculadoras de Kelly y Hedge que ya tienes
        st.write("Usa estas herramientas para proteger tu capital.")

else:
    st.info("Bienvenido a Axiom Data. Esperando actualización del radar...")
    
    # 🔥 PESTAÑAS (NUEVAS HERRAMIENTAS VIP) 🔥
    tab_futbol, tab_nba, tab_herramientas, tab_historial = st.tabs(["⚽ FÚTBOL", "🏀 NBA", "🧮 HERRAMIENTAS VIP", "📖 HISTORIAL Y DATA"])
    
    # --- ⚽ FÚTBOL ---
    with tab_futbol:
        df_futbol = df_activos[df_activos['deporte'].isin(['Fútbol', 'Mixto (Parlay)'])]
        if not df_futbol.empty:
            for i, r in df_futbol.iterrows():
                icono_tipo = "🔗 COMBINADA" if r.get('tipo') == 'Combinada' else "📌 SENCILLA"
                with st.expander(f"{icono_tipo} | {r.get('partido', '')} | EV+: {r.get('ev', 0)}%"):
                    st.markdown(f"<p style='color: #00f2ff; font-size: 0.8rem;'>🏆 {r.get('liga', '')} | 🎯 <b>Mercado:</b> {r.get('mercado', '')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #bc13fe; font-size: 0.9rem;'>📈 Cuota: {r.get('cuota')} | 🏦 Prob. Casa: {r.get('prob_casa',0)}% | 🎯 Prob. Real: {r.get('prob_real',0)}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', ''))
                    
                    if st.session_state['user_rol'] == 'admin':
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                        ca, cb, cc = st.columns([1,1,1])
                        if ca.button(f"✅ Ganada", key=f"w_f_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdida", key=f"l_f_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
                        if cc.button(f"🗑️ Borrar", key=f"del_f_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).delete()
                            st.rerun()
        else:
            st.info("No hay señales de fútbol activas.")

    # --- 🏀 NBA ---
    with tab_nba:
        df_nba = df_activos[df_activos['deporte'] == 'NBA']
        if not df_nba.empty:
            for i, r in df_nba.iterrows():
                with st.expander(f"🏀 {r.get('partido', '')} | {r.get('mercado', '')} | EV+: {r.get('ev', 0)}%"):
                    st.markdown(f"<p style='color: #ff9900; font-size: 0.9rem;'>🏦 Prob. Casa: {r.get('prob_casa',0)}% | 🎯 Prob. Real: {r.get('prob_real',0)}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', ''))
                    if st.session_state['user_rol'] == 'admin':
                        ca, cb, cc = st.columns([1,1,1])
                        if ca.button(f"✅ Ganada", key=f"w_n_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdida", key=f"l_n_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
                        if cc.button(f"🗑️ Borrar", key=f"del_n_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).delete()
                            st.rerun()
        else:
            st.info("Aún no inicia la cobertura de la duela.")

    # --- 🧮 HERRAMIENTAS VIP ---
    with tab_herramientas:
        st.markdown("### 🧮 Calculadora de Gestión de Bank (Criterio de Kelly)")
        st.write("Calcula matemáticamente el porcentaje exacto de tu capital que debes invertir basado en tu ventaja.")
        
        k_col1, k_col2, k_col3 = st.columns(3)
        k_bank = k_col1.number_input("🏦 Tu Bankroll ($):", value=1000.0, step=50.0)
        k_cuota = k_col2.number_input("📈 Cuota de la Apuesta:", value=1.90, step=0.01)
        k_prob = k_col3.number_input("🎯 Probabilidad Real (%):", value=60.0, step=1.0)
        
        if k_cuota > 1.0:
            p = k_prob / 100.0
            q = 1 - p
            b = k_cuota - 1
            f_star = (b * p - q) / b
            
            if f_star > 0:
                st.success(f"**Recomendación de Inversión:** Apostar el **{f_star*100:.2f}%** de tu bankroll (**${k_bank * f_star:.2f}**)")
            else:
                st.error("🚨 EV Negativo. El modelo matemático recomienda **NO APOSTAR**.")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🛡️ Calculadora de Cobertura (Hedge / Cashout)")
        st.write("Asegura ganancias cuando a tu combinada solo le falta un partido.")
        
        h_col1, h_col2, h_col3 = st.columns(3)
        h_inv = h_col1.number_input("💵 Inversión Inicial ($):", value=100.0, step=10.0)
        h_cuota_ini = h_col2.number_input("📈 Cuota de la Combinada:", value=3.50, step=0.1)
        h_cuota_contra = h_col3.number_input("⚖️ Cuota a la Contra (Actual):", value=2.10, step=0.1)
        
        if h_cuota_contra > 1.0:
            retorno_potencial = h_inv * h_cuota_ini
            hedge_ideal = retorno_potencial / h_cuota_contra
            ganancia_neta = retorno_potencial - h_inv - hedge_ideal
            
            st.info(f"**Estrategia Segura:** Apuesta **${hedge_ideal:.2f}** a la contra. Pase lo que pase, tu ganancia neta asegurada será de **${ganancia_neta:.2f}**.")

    # --- 📖 HISTORIAL Y DATA ---
    with tab_historial:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            # Gráfica de Rendimiento (ROI)
            st.markdown("#### 📈 Curva de Crecimiento del Capital")
            df_chart = df_historial.copy().sort_values('fecha')
            df_chart['profit'] = df_chart.apply(lambda x: (x['cuota'] - 1)*100 if x['estatus']=='GANADA' else -100, axis=1)
            df_chart['acumulado'] = df_chart['profit'].cumsum()
            
            fig_roi = px.line(df_chart, x='fecha', y='acumulado', title="Beneficio Acumulado (Asumiendo Flat Stake $100)", template="plotly_dark", markers=True)
            fig_roi.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_title="Beneficio Neto ($)", xaxis_title="Evolución en el Tiempo")
            fig_roi.update_traces(line_color='#00f2ff')
            st.plotly_chart(fig_roi, use_container_width=True)
            
            # Exportar a CSV
            csv = df_historial.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Descargar Historial Completo (CSV)", data=csv, file_name='historial_axiom.csv', mime='text/csv')
            
            st.markdown("<hr>", unsafe_allow_html=True)
            c_h1, c_h2, c_h3 = st.columns(3)
            c_h1.metric("✅ ACIERTOS", ganadas)
            c_h2.metric("❌ FALLOS", perdidas)
            c_h3.metric("📈 WIN RATE", f"{wr:.1f}%")
            
            for i, r in df_historial.iterrows():
                icon = "✅" if r['estatus'] == 'GANADA' else "❌"
                with st.expander(f"{icon} [{r.get('liga', 'General')}] {r.get('partido', '')}"):
                    st.write(f"Cuota: {r.get('cuota', 0)} | Ventaja: {r.get('ev', 0)}%")
                    if st.session_state['user_rol'] == 'admin':
                        if st.button("🔄 Revertir", key=f"rev_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                            st.rerun()
                        if st.button("🗑️ Borrar", key=f"del_h_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).delete()
                            st.rerun()
        else:
            st.info("El historial está vacío.")

else:
    st.info("Base de datos vacía.")

st.markdown("<br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)


