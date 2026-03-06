import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="GALACTIC BET ANALYTICS", layout="wide")

# 2. CSS Futurista y Centrado (Sin cambios, esto no da error)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #0e1117; }
    .titulo-futurista {
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 20px;
    }
    .subtitulo {
        color: #ffffff;
        font-size: 1.1rem;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 30px;
        opacity: 0.7;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(0, 242, 255, 0.05);
        border: 1px solid #00f2ff;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }
    h3 { text-align: center; color: #00f2ff; font-family: 'Orbitron', sans-serif; margin-top: 40px !important; }
    hr { border: 0; height: 1px; background: linear-gradient(to right, transparent, #00f2ff, transparent); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. Encabezado
st.markdown('<p class="titulo-futurista">GALACTIC BET ANALYTICS</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">AI-DRIVEN SPORTS FORECASTING PLATFORM</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# 4. Datos (Tu link corregido)
sheet_url = "https://docs.google.com/spreadsheets/d/12lDBRn6nXm4yvzjHhqL6w2FbCw8FPS1dYt5BoZYuP4w/export?format=csv"

try:
    df = pd.read_csv(sheet_url)
    
    # Limpiamos los datos por si vienen con símbolos
    if 'EV+' in df.columns and df['EV+'].dtype == 'object':
        df['EV+'] = df['EV+'].str.replace('%', '').astype(float)

    # 5. Métricas (EN LÍNEA)
    col1, col2, col3 = st.columns(3)
    with col1:
        val_max = df['EV+'].max() if 'EV+' in df.columns else 0
        st.metric(label="MÁXIMO EV+", value=f"{val_max}%")
    with col2:
        st.metric(label="PARTIDOS", value=len(df))
    with col3:
        st.metric(label="ESTATUS", value="EN LÍNEA")

    # 6. Tabla de Datos (La forma más segura de mostrar info en 3.14)
    st.markdown("### 🛰️ PANEL DE CONTROL DE PICKS")
    st.dataframe(df, use_container_width=True)

    # 7. Gráfico Simple (Solo si Altair carga, si no, se salta)
    try:
        st.markdown("### 📊 RADAR DE VALOR")
        st.bar_chart(data=df, x='PARTIDO', y='EV+')
    except:
        st.info("Visualización gráfica limitada en esta versión de sistema.")

except Exception as e:
    st.error(f"Error de conexión: {e}")

# 8. Tu Firma
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff;'>© 2026 GALACTIC ANALYTICS | Desarrollado por Torvi Analytics</p>", unsafe_allow_html=True)




