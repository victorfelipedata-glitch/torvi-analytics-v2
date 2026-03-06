import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página (Ancho total y barra lateral abierta)
st.set_page_config(page_title="GALACTIC BET ANALYTICS", layout="wide", initial_sidebar_state="expanded")

# 2. CSS SÚPER FUTURISTA (Efectos Neón y Hover)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .main { background-color: #050814; } /* Fondo azul ultra oscuro */
    
    /* Título Neón Brillante */
    .titulo-futurista {
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff;
        text-shadow: 0 0 5px #00f2ff, 0 0 15px #00f2ff, 0 0 30px #008cff;
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 10px;
        letter-spacing: 2px;
    }
    .subtitulo {
        color: #b3cce6;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        text-align: center;
        letter-spacing: 4px;
        margin-bottom: 40px;
    }
    
    /* Tarjetas de Métricas con brillo al pasar el mouse */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #0a1128, #000000);
        border: 1px solid #00f2ff;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.6);
    }
    
    /* Divisores Láser */
    hr { 
        border: 0; 
        height: 2px; 
        background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); 
        margin: 30px 0; 
        box-shadow: 0 0 10px #00f2ff;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="titulo-futurista">GALACTIC BET</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE ANÁLISIS EV+ AVANZADO</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# 3. DATOS DE TU GOOGLE SHEETS
sheet_url = "https://docs.google.com/spreadsheets/d/12lDBRn6nXm4yvzjHhqL6w2FbCw8FPS1dYt5BoZYuP4w/export?format=csv"

try:
    df = pd.read_csv(sheet_url)
    
    # Limpiamos el % del EV+ para que las gráficas no fallen
    if 'EV+' in df.columns and df['EV+'].dtype == 'object':
        df['EV+'] = df['EV+'].str.replace('%', '').astype(float)

    # 4. CONSOLA DE MANDO (Barra Lateral)
    st.sidebar.markdown("<h2 style='text-align: center; font-family: Orbitron; color: #00f2ff;'>📟 CONSOLA</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    equipo_filtro = st.sidebar.text_input("🔍 Buscar Equipo o Partido:")
    
    # Filtrar el dataframe si escribes algo
    if equipo_filtro:
        df = df[df['PARTIDO'].str.contains(equipo_filtro, case=False, na=False)]

    # 5. TARJETAS DE MÉTRICAS (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        val_max = df['EV+'].max() if not df.empty and 'EV+' in df.columns else 0
        st.metric("🔥 MÁXIMO EV+", f"{val_max}%")
    with col2:
        st.metric("🎯 PICKS ACTIVOS", len(df))
    with col3:
        st.metric("⚡ SISTEMA", "EN LÍNEA")
    with col4:
        st.metric("🛡️ FIABILIDAD", "ALTA")

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. GRÁFICA CORREGIDA (Horizontal y muy legible)
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>📊 ESCÁNER DE VALOR (EV+)</h3>", unsafe_allow_html=True)
    if not df.empty and 'PARTIDO' in df.columns and 'EV+' in df.columns:
        fig = px.bar(df, x='EV+', y='PARTIDO', 
                     orientation='h',
                     color='EV+',
                     text='EV+',
                     color_continuous_scale="PuBuGn",
                     template="plotly_dark")
        # Mostrar el porcentaje por fuera de la barra
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Orbitron", color="#00f2ff"),
            xaxis_title="Valor Esperado (EV+ %)",
            yaxis_title="",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para graficar con ese filtro.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 7. EL NUEVO DESGLOSE DE ANÁLISIS (¡Adiós textos cortados!)
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>🧠 DESGLOSE TÁCTICO DE PICKS</h3>", unsafe_allow_html=True)
    
    if not df.empty:
        # Creamos un acordeón (expander) por cada partido
        for index, row in df.iterrows():
            partido = row.get('PARTIDO', 'Desconocido')
            mercado = row.get('MERCADO', 'N/A')
            cuota = row.get('CUOTA CASA', 'N/A')
            ev = row.get('EV+', 0)
            analisis = row.get('ANALISIS', 'Sin análisis registrado aún.')
            estatus = str(row.get('ESTATUS', ''))
            
            # Icono dinámico según el estatus
            icon = "🟢" if "Stal" in estatus else "🔥"
            
            with st.expander(f"{icon} {partido}  |  MERCADO: {mercado}  |  CUOTA: {cuota}  |  EV+: {ev}%"):
                st.markdown(f"""
                <div style='background-color: #0a1128; padding: 20px; border-left: 4px solid #00f2ff; border-radius: 0 10px 10px 0;'>
                    <h4 style='color: #bc13fe; margin-top: 0;'>📝 Análisis del Algoritmo:</h4>
                    <p style='color: #ffffff; font-size: 1.1rem; line-height: 1.6;'>{analisis}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No hay picks en el radar en este momento.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 8. BOTÓN PARA DESCARGAR EL EXCEL
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ DESCARGAR BASE DE DATOS DE PICKS (CSV)",
        data=csv,
        file_name='galactic_picks.csv',
        mime='text/csv',
    )

except Exception as e:
    st.error(f"Error crítico en el sistema central: {e}")

# 9. FOOTER DE AUTOR
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; opacity: 0.8;'>© 2026 GALACTIC ANALYTICS | Desarrollado por Torvi Analytics</p>", unsafe_allow_html=True)





