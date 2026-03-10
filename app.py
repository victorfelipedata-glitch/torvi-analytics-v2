import streamlit as st
import pandas as pd
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="QUASAR | Predictive Analytics", layout="wide")

# --- CSS: ESTILO FINTECH / QUASAR ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #050510; font-family: 'Inter', sans-serif; background-image: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050510 60%); background-attachment: fixed;}
    
    .titulo-axiom { font-family: 'Inter', sans-serif; color: #E2E8F0; font-size: 3.5rem; font-weight: 800; text-align: center; margin-bottom: -15px; letter-spacing: 2px; text-shadow: 0 0 20px rgba(188, 19, 254, 0.5);}
    .titulo-axiom span { color: #bc13fe; }
    .subtitulo { color: #00f2ff; font-family: 'JetBrains Mono', monospace; text-align: center; letter-spacing: 3px; margin-bottom: 30px; font-size: 0.9rem; text-transform: uppercase; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);}
    
    .pick-card { background-color: rgba(17, 24, 39, 0.8); backdrop-filter: blur(10px); border: 1px solid rgba(188, 19, 254, 0.3); border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #00f2ff; transition: transform 0.2s; }
    .pick-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 242, 255, 0.2); }
    .pick-card.vip { border-left: 4px solid #F59E0B; background: linear-gradient(145deg, rgba(17,24,39,0.9), rgba(26,21,0,0.9)); border: 1px solid rgba(245, 158, 11, 0.5); }
    
    .pick-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 15px; }
    .pick-title { font-size: 1.2rem; font-weight: 600; color: #F8FAFC; margin: 0; }
    .pick-ev { background-color: rgba(188, 19, 254, 0.2); color: #bc13fe; padding: 4px 10px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.9rem; border: 1px solid #bc13fe;}
    
    .pick-stats { display: flex; gap: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #94A3B8; margin-bottom: 15px;}
    .stat-box { background: rgba(0,0,0,0.4); padding: 10px 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }
    .stat-box span { display: block; font-size: 0.7rem; color: #64748B; text-transform: uppercase; margin-bottom: 3px;}
    .stat-val { color: #E2E8F0; font-weight: 700; font-size: 1.1rem; }
    
    .kelly-box { background: rgba(0, 242, 255, 0.1); border: 1px solid rgba(0, 242, 255, 0.3); color: #00f2ff; padding: 10px; border-radius: 8px; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; margin-bottom: 15px;}
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(255,255,255,0.05); border-radius: 8px 8px 0 0; color: #94A3B8; padding: 10px 20px; font-weight: 600; border: none; transition: 0.3s; }
    .stTabs [aria-selected="true"] { background-color: rgba(188, 19, 254, 0.2) !important; color: white !important; border-bottom: 2px solid #bc13fe !important; }
    
    div[data-testid="stMetric"] { background-color: rgba(0,0,0,0.5); border: 1px solid rgba(188, 19, 254, 0.3); border-radius: 10px; padding: 15px; box-shadow: none; backdrop-filter: blur(5px);}
    
    .stNumberInput input { background-color: rgba(0,0,0,0.5) !important; color: #00f2ff !important; border: 1px solid rgba(0, 242, 255, 0.3) !important; font-weight: bold; font-family: 'JetBrains Mono'; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A FIREBASE ---
try:
    if not firebase_admin._apps:
        dict_claves = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(dict_claves)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception:
    st.error("Error conectando a los servidores.")
    st.stop()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- SESIÓN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'
if 'user_email' not in st.session_state: st.session_state['user_email'] = ''

st.markdown('<p class="titulo-axiom">QUASAR <span>ANALYTICS</span></p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">NÚCLEO GALÁCTICO ACTIVO | VISIÓN PREDICTIVA</p>', unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(10px); padding: 30px; border-radius: 16px; border: 1px solid rgba(188, 19, 254, 0.4); box-shadow: 0 0 20px rgba(188,19,254,0.1);'>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INICIAR SESIÓN", "CREAR CUENTA"])
        with t1:
            with st.form("f_login"):
                u = st.text_input("Correo:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("CONECTAR AL NÚCLEO", use_container_width=True):
                    if u.strip(): 
                        try:
                            res = db.collection('usuarios').document(u).get()
                            if res.exists and res.to_dict().get('password') == encriptar_password(p):
                                st.session_state['autenticado'] = True
                                st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                                st.session_state['user_email'] = u
                                st.rerun()
                            else: st.error("Fallo de autenticación.")
                        except Exception: st.error("Error de red galáctica.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARSE", use_container_width=True):
                    if un.strip() and pn.strip():
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bankroll': 1000.0})
                        st.success("Cuenta creada. Inicia sesión.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- BLINDAJE DE SEGURIDAD ---
user_email = st.session_state.get('user_email', '').strip()
if not user_email:
    st.session_state['autenticado'] = False
    st.rerun()

# --- DATOS DEL USUARIO Y PORTAFOLIO ---
base_bankroll = 1000.0
mis_picks_dict = {}

try:
    user_doc = db.collection('usuarios').document(user_email).get()
    if user_doc.exists:
        base_bankroll = float(user_doc.to_dict().get('bankroll', 1000.0))
        
    mis_picks_refs = db.collection('usuarios').document(user_email).collection('portafolio').stream()
    mis_picks_dict = {doc.id: doc.to_dict() for doc in mis_picks_refs}
except Exception:
    pass

# --- CARGA DE PRONÓSTICOS GLOBALES ---
data = []
try:
    docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
    for d in docs:
        item = d.to_dict()
        if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
        data.append(item)
except Exception:
    pass

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR LIMPIO ---
st.sidebar.markdown(f"<h3 style='color: #00f2ff; font-family: Inter; text-shadow: 0 0 5px #00f2ff;'>👤 {user_email.split('@')[0]}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='color: #bc13fe; font-family: JetBrains Mono; font-size: 0.8rem;'>RANGO: {st.session_state['user_rol'].upper()}</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Desconectar del Núcleo", use_container_width=True):
    st.session_state['autenticado'] = False
    st.session_state['user_email'] = ''
    st.rerun()

# --- FUNCIONES MATEMÁTICAS ---
def calcular_kelly(ev_pct, cuota, bankroll):
    if cuota <= 1 or ev_pct <= 0: return 0.0, 0.0
    p = (ev_pct / 100) + (1 / cuota) 
    b = cuota - 1
    kelly_frac = (p * b - (1 - p)) / b
    quarter_kelly = max(0, kelly_frac * 0.25)
    pct_final = min(quarter_kelly, 0.05) 
    inversion = bankroll * pct_final
    return inversion, pct_final * 100

# --- BOTÓN DE ACTUALIZAR PRINCIPAL (SIEMPRE VISIBLE) ---
col_vacia, col_btn, col_vacia2 = st.columns([1, 2, 1])
with col_btn:
    if st.button("🔄 SINCRONIZAR DATOS DEL QUASAR", use_container_width=True, type="primary"):
        st.toast("Captando ondas gravitacionales del mercado...", icon="🛰️")
        time.sleep(0.5)
        st.rerun()

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 10px;'>", unsafe_allow_html=True)

if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_normales = df_activos[~df_activos['partido'].str.contains("Parlay", case=False, na=False)]
    df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False, na=False)]

    m1, m2, m3 = st.columns(3)
    max_ev_actual = df_activos['ev'].max() if not df_activos.empty else 0
    m1.metric("🔥 MAYOR VENTAJA", f"{max_ev_actual}%")
    m2.metric("🎯 EN EL RADAR", len(df_activos))
    m3.metric("🏦 MI CAPITAL (BANK)", f"${base_bankroll:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tabs = ["📡 RADAR QUASAR", "💎 PARLAY VIP", "💼 PORTAFOLIO", "⚙️ PERFIL & LAB"]
    if st.session_state['user_rol'] == 'admin': tabs.append("👑 CONSOLA ADMIN")
    paneles = st.tabs(tabs)
    
    # === PESTAÑA 1: RADAR (MERCADO GLOBAL) ===
    with paneles[0]:
        if not df_normales.empty:
            
            # --- NUEVO: DOBLE VISUALIZACIÓN INTERACTIVA ---
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                st.markdown("<p style='text-align: center; color: #bc13fe; font-family: Orbitron;'>TERMODINÁMICA DEL MERCADO (EV+)</p>", unsafe_allow_html=True)
                # Velocímetro (Gauge Chart) para el Max EV
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = max_ev_actual,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    number = {'suffix': "%", 'font': {'color': '#00f2ff'}},
                    gauge = {
                        'axis': {'range': [None, 30], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.5)"},
                        'bar': {'color': "#bc13fe"},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 2,
                        'bordercolor': "rgba(188, 19, 254, 0.3)",
                        'steps': [
                            {'range': [0, 5], 'color': "rgba(239, 68, 68, 0.2)"},
                            {'range': [5, 15], 'color': "rgba(245, 158, 11, 0.2)"},
                            {'range': [15, 30], 'color': "rgba(16, 185, 129, 0.2)"}],
                    }
                ))
                fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col_graph2:
                st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron;'>MAPA DE DISPERSIÓN 3D</p>", unsafe_allow_html=True)
                # Scatter Plot original que te gustó
                df_chart = df_normales.copy()
                df_chart['cuota'] = pd.to_numeric(df_chart['cuota'])
                df_chart['prob_real'] = pd.to_numeric(df_chart['prob_real'])
                df_chart['ev'] = pd.to_numeric(df_chart['ev'])
                
                fig = px.scatter(df_chart, x="cuota", y="prob_real", size="ev", color="ev",
                                 hover_name="partido", hover_data=["mercado", "ev"],
                                 color_continuous_scale="Purp", size_max=35,
                                 labels={"cuota": "Cuota", "prob_real": "Prob. Real %"})
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', height=220, margin=dict(l=10, r=10, t=10, b=10))
                fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                st.plotly_chart(fig, use_container_width=True)
                
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-bottom: 30px;'>", unsafe_allow_html=True)

            # Lista de Picks
            for i, r in df_normales.iterrows():
                pid = r['id']
                inv_recomendada, pct_bank = calcular_kelly(r.get('ev',0), r.get('cuota',1.01), base_bankroll)
                
                st.markdown(f"""
                <div class="pick-card">
                    <div class="pick-header">
                        <h3 class="pick-title">{str(r.get('partido','')).replace('[SENCILLA]','')}</h3>
                        <span class="pick-ev">EV+ {r.get('ev',0)}%</span>
                    </div>
                    <p style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 15px;">🎯 {r.get('mercado','')}</p>
                    <div class="pick-stats">
                        <div class="stat-box"><span>Cuota</span><div class="stat-val">{r.get('cuota',0)}</div></div>
                        <div class="stat-box"><span>Prob. Casa</span><div class="stat-val">{r.get('prob_casa',0)}%</div></div>
                        <div class="stat-box"><span>Prob. Real</span><div class="stat-val" style="color:#bc13fe;">{r.get('prob_real',0)}%</div></div>
                    </div>
                    <div class="kelly-box">
                        💡 <b>Fórmula Quasar:</b> Invertir el <b>{pct_bank:.1f}%</b> de tu Bankroll (${inv_recomendada:.2f})
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">{r.get('analisis','')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if pid in mis_picks_dict:
                    st.success(f"✅ Alineado en Portafolio (Inversión: ${mis_picks_dict[pid].get('stake', 0):.2f})")
                else:
                    c_input, c_btn = st.columns([1, 2])
                    with c_input:
                        monto_elegido = st.number_input("Tu Inversión ($):", min_value=0.0, value=float(inv_recomendada), step=10.0, key=f"in_{pid}")
                    with c_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📥 Incorporar a mi Portafolio", key=f"add_{pid}"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(pid).set({
                                    'pick_id': pid, 'stake': monto_elegido, 'fecha': datetime.now()
                                })
                                st.rerun()
                            except Exception: st.error("Error al guardar.")
                st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 30px;'>", unsafe_allow_html=True)
        else:
            st.info("El Quasar está escaneando los mercados. Sin anomalías detectadas por ahora.")

    # === PESTAÑA 2: PARLAY VIP ===
    with paneles[1]:
        if not df_parlays.empty:
            for i, r in df_parlays.iterrows():
                pid = r['id']
                inv_recomendada, pct_bank = calcular_kelly(r.get('ev',0), r.get('cuota',1.01), base_bankroll)
                
                st.markdown(f"""
                <div class="pick-card vip">
                    <div class="pick-header">
                        <h3 class="pick-title" style="color:#F59E0B;">👑 {str(r.get('partido','')).replace('[PARLAY]','').strip()}</h3>
                        <span class="pick-ev" style="background:rgba(245,158,11,0.1); color:#F59E0B; border-color: #F59E0B;">EV+ {r.get('ev',0)}%</span>
                    </div>
                    <p style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 15px;">🎯 {r.get('mercado','')}</p>
                    <div class="pick-stats">
                        <div class="stat-box" style="border-color:rgba(245,158,11,0.3); background: rgba(0,0,0,0.6);">
                            <span>Momio Combinado</span>
                            <div class="stat-val" style="color:#F59E0B;">{r.get('cuota',0)}</div>
                        </div>
                    </div>
                    <div class="kelly-box" style="background:rgba(245,158,11,0.05); border-color:rgba(245,158,11,0.5); color:#FCD34D;">
                        💡 <b>Sugerencia Quasar:</b> Inversión de ${inv_recomendada:.2f}
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">{r.get('analisis','')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if pid in mis_picks_dict:
                    st.success(f"✅ Combinada Activa (Inversión: ${mis_picks_dict[pid].get('stake', 0):.2f})")
                else:
                    c_input, c_btn = st.columns([1, 2])
                    with c_input:
                        monto_elegido = st.number_input("Tu Inversión ($):", min_value=0.0, value=float(inv_recomendada), step=10.0, key=f"in_p_{pid}")
                    with c_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📥 Seguir Combinada", key=f"add_p_{pid}"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(pid).set({
                                    'pick_id': pid, 'stake': monto_elegido, 'fecha': datetime.now()
                                })
                                st.rerun()
                            except Exception: st.error("Error al guardar.")
                st.markdown("<hr style='border-color: rgba(245,158,11,0.1); margin-top: 30px;'>", unsafe_allow_html=True)
        else:
            st.info("El algoritmo está procesando la combinada estelar de hoy...")

    # === PESTAÑA 3: MI PORTAFOLIO ===
    with paneles[2]:
        st.markdown("<h3 style='color: #E2E8F0; font-family: Inter;'>Mis Posiciones Activas</h3>", unsafe_allow_html=True)
        
        mis_picks_completos = []
        for pid, pdata in mis_picks_dict.items():
            info_global = df[df['id'] == pid]
            if not info_global.empty:
                pick_info = info_global.iloc[0].to_dict()
                pick_info['mi_stake'] = pdata.get('stake', 0)
                mis_picks_completos.append(pick_info)
                
        df_mi_portafolio = pd.DataFrame(mis_picks_completos)
        
        if not df_mi_portafolio.empty:
            activos_mios = df_mi_portafolio[df_mi_portafolio['estatus'] == 'PENDIENTE']
            resueltos_mios = df_mi_portafolio[df_mi_portafolio['estatus'] != 'PENDIENTE']
            
            if not activos_mios.empty:
                for i, r in activos_mios.iterrows():
                    c_info, c_del = st.columns([5, 1])
                    with c_info:
                        st.markdown(f"""
                        <div style="background:rgba(15,23,42,0.8); padding:15px; border-radius:8px; border-left:3px solid #00f2ff; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="color:#E2E8F0; font-weight:bold;">{r.get('partido','')}</span><br>
                                <span style="color:#64748B; font-size:0.8rem;">{r.get('mercado','')} | Cuota {r.get('cuota',0)}</span>
                            </div>
                            <div style="text-align:right;">
                                <span style="color:#94A3B8; font-size:0.8rem;">Invertido</span><br>
                                <span style="color:#10B981; font-weight:bold; font-family:JetBrains Mono;">${r.get('mi_stake',0):.2f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_del:
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{r['id']}", help="Eliminar de mi portafolio"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(r['id']).delete()
                                st.rerun()
                            except Exception: st.error("Error al borrar.")
            else: st.write("No tienes fondos en riesgo en este momento.")
            
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'><h3 style='color: #E2E8F0; font-family: Inter;'>Historial de Desempeño</h3>", unsafe_allow_html=True)
            if not resueltos_mios.empty:
                mis_ganadas = len(resueltos_mios[resueltos_mios['estatus'] == 'GANADA'])
                mis_perdidas = len(resueltos_mios[resueltos_mios['estatus'] == 'PERDIDA'])
                mi_wr = (mis_ganadas/(mis_ganadas+mis_perdidas))*100 if (mis_ganadas+mis_perdidas)>0 else 0
                
                # --- NUEVA GRÁFICA: DONUT DE WINRATE ---
                col_w1, col_w2 = st.columns([1, 2])
                with col_w1:
                    st.metric("✅ ACIERTOS", mis_ganadas)
                    st.metric("❌ FALLOS", mis_perdidas)
                    st.metric("📈 WIN RATE", f"{mi_wr:.1f}%")
                
                with col_w2:
                    labels = ['Aciertos', 'Fallos']
                    values = [mis_ganadas, mis_perdidas]
                    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, 
                                          marker_colors=['#10B981', '#EF4444'])])
                    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                          margin=dict(t=0, b=0, l=0, r=0), height=200, showlegend=False)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                for i, r in resueltos_mios.iterrows():
                    color = "#10B981" if r['estatus'] == 'GANADA' else "#EF4444"
                    icon = "✅" if r['estatus'] == 'GANADA' else "❌"
                    st.markdown(f"""
                    <div style="background:rgba(15,23,42,0.5); padding:10px 15px; border-radius:8px; border-left:3px solid {color}; margin-bottom:5px;">
                        <span style="color:#E2E8F0; font-size:0.9rem;">{icon} {r.get('partido','')} ({r.get('mercado','')})</span>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.write("Tu historial está vacío.")
        else:
            st.info("Ve a la pestaña RADAR y añade pronósticos a tu portafolio.")

    # === PESTAÑA 4: PERFIL & LAB ===
    with paneles[3]:
        c_p1, c_p2 = st.columns(2)
        
        with c_p1:
            st.markdown("<div class='pick-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #00f2ff; font-family: Inter;'>⚙️ Configuración de Capital</h3>", unsafe_allow_html=True)
            st.write("Quasar utiliza la fórmula Quarter-Kelly (max 5%) para la gestión de tu Bankroll.")
            with st.form("form_bank"):
                nuevo_b = st.number_input("Mi Bankroll Actual ($):", value=base_bankroll, step=50.0)
                if st.form_submit_button("Actualizar Parámetros", use_container_width=True):
                    try:
                        db.collection('usuarios').document(user_email).update({'bankroll': nuevo_b})
                        st.success("Bankroll calibrado.")
                        time.sleep(1)
                        st.rerun()
                    except Exception: st.error("Error guardando el bankroll.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_p2:
            st.markdown("<div class='pick-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #bc13fe; font-family: Inter;'>🧮 Laboratorio de Cuotas</h3>", unsafe_allow_html=True)
            st.write("Convierte la ilusión de la casa de apuestas en probabilidad matemática:")
            cuota_test = st.number_input("Ingresa un momio (Decimal):", value=1.90, step=0.01)
            prob_impl = (1 / cuota_test) * 100 if cuota_test > 0 else 0
            st.markdown(f"<h2 style='color: #00f2ff; text-align: center;'>{prob_impl:.1f}%</h2>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #E2E8F0;'>🧠 El Motor de Quasar</h4>", unsafe_allow_html=True)
        st.write("Para encontrar el Valor Esperado (EV+), nuestro algoritmo de núcleo procesa la siguiente desigualdad matemática:")
        st.latex(r"EV+ = \left( P_{real} \cdot \text{Cuota} \right) - 1 > 0")
        st.write("Donde $P_{real}$ es la probabilidad dictada por nuestros modelos predictivos, desnudando el margen de error del corredor.")

    # === PESTAÑA 5: ADMIN ===
    if st.session_state['user_rol'] == 'admin':
        with paneles[4]:
            st.markdown("<h3 style='color: #00f2ff;'>Centro de Comando Quasar</h3>", unsafe_allow_html=True)
            st.write("Cierra los eventos activos aquí. Esto actualizará los portafolios y las gráficas WinRate de todos los usuarios.")
            if not df_activos.empty:
                for i, r in df_activos.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"{r.get('partido','')} - {r.get('mercado','')}")
                    if cb.button("✅ Hit", key=f"ad_w_{r['id']}"):
                        try:
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        except Exception: pass
                    if cc.button("❌ Miss", key=f"ad_l_{r['id']}"):
                        try:
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
                        except Exception: pass
            else: st.write("El universo de apuestas está en calma.")
            
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'><h3 style='color: #bc13fe;'>Inyectar Nueva Señal</h3>", unsafe_allow_html=True)
            with st.form("form_admin_nuevo"):
                c1, c2 = st.columns(2)
                p_partido = c1.text_input("Encuentro (Usa 'Parlay' para VIP):")
                p_mercado = c2.text_input("Mercado Seleccionado:")
                n1, n2, n3, n4 = st.columns(4)
                p_cuota = n1.number_input("Cuota Final:", value=1.90, step=0.01)
                p_casa = n2.number_input("Prob. Implícita Casa %:", value=50.0)
                p_real = n3.number_input("Prob. Real Quasar %:", value=60.0)
                p_ev = n4.number_input("Ventaja EV+ %:", value=10.0)
                p_ana = st.text_area("Justificación Táctica/Matemática:")
                
                if st.form_submit_button("Transmitir al Radar"):
                    try:
                        p_id = f"{int(time.time())}"
                        db.collection('pronosticos').document(p_id).set({
                            'id': p_id, 'partido': p_partido, 'mercado': p_mercado, 'cuota': p_cuota,
                            'prob_casa': p_casa, 'prob_real': p_real, 'ev': p_ev, 'analisis': p_ana, 
                            'estatus': 'PENDIENTE', 'fecha': datetime.now()
                        })
                        st.success("Señal transmitida a toda la red.")
                        time.sleep(1)
                        st.rerun()
                    except Exception: st.error("Fallo de inyección de datos.")

else:
    st.info("Conectado al núcleo de Quasar Analytics. Esperando anomalías en los mercados...")
