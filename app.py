import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página (Título en la pestaña y Layout)
st.set_page_config(page_title="GALACTIC BET ANALYTICS", layout="wide")

# 2. CSS para el estilo Futurista (Centrado, fuentes neón y fondo oscuro)
st.markdown("""
    <style>
    /* Centrar todo el contenido */
    .main {
        text-align: center;
    }
    /* Estilo para el Título Principal */
    .titulo-futurista {
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0px;
    }
    /* Estilo para el Subtítulo */
    .subtitulo {
        color: #ffffff;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 30px;
        opacity: 0.8;
    }
    /* Estilo para las tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: rgba(0, 242, 255, 0.05);
        border: 1px solid #00f2ff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 5px rgba(0, 242, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Título Centrado y Futurista
st.markdown('<p class="titulo-futurista">GALACTIC BET ANALYTICS</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">AI-DRIVEN SPORTS FORECASTING PLATFORM</p>', unsafe_allow_html=True)

# --- AQUÍ VA TU LÓGICA DE CONEXIÓN A GOOGLE SHEETS ---
# (Usa el mismo código que ya tenías para leer el CSV de Google Sheets)
sheet_url = "TU_URL_DE_GOOGLE_SHEETS_AQUÍ" # <--- No olvides poner tu link
df = pd.read_csv(sheet_url)

# 4. Diseño en Columnas para que se vea ordenado (Radar de Mercado)
st.markdown("### 🛰️ RADAR DE MERCADO")
col1, col2, col3 = st.columns(3)

# Ejemplo de métricas (cámbialas por tus columnas reales del DF)
with col1:
    st.metric(label="EV+ PROMEDIO", value="+19.3%", delta="High Value")
with col2:
    st.metric(label="PICKS DETECTADOS", value="12", delta="Active")
with col3:
    st.metric(label="FIABILIDAD SISTEMA", value="88%", delta="Optimal")

# 5. Gráfico de Valor (Futurista con Plotly)
st.markdown("### 📈 MÉTRICAS DE VALOR POR PARTIDO")
fig = px.bar(df, x='Equipo', y='EV+', 
             title="Análisis de Valor Esperado",
             template="plotly_dark", 
             color_continuous_scale="Viridis")

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font_color="#00f2ff"
)

st.plotly_chart(fig, use_container_width=True)

# 6. Tabla de Datos (Estilo Limpio)
st.markdown("### 📋 PANEL DE PREDICCIONES")
st.dataframe(df.style.highlight_max(axis=0, color='#002b36'), use_container_width=True)
st.divider()
st.markdown("**© 2026 GALACTIC ANALYTICS | Desarollado por Torvi Analytics**")

