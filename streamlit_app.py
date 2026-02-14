"""
Aplicación Streamlit - Sistema de Análisis de Trading
Interfaz gráfica profesional para análisis de contratos de futuros
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Importar módulos propios
from src.ingestion import DataIngestion
from src.classifier import DayClassifier
from src.analytics import SessionAnalytics
from src.predictor import TradingPredictor
from src.visualizer import TradingVisualizer

# Configuración de la página
st.set_page_config(
    page_title="Trading Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
def load_css():
    """Carga estilos CSS personalizados"""
    st.markdown("""
    <style>
    /* Tema general */
    .main {
        padding: 2rem;
    }
    
    /* Headers personalizados */
    h1 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #374151;
        font-weight: 600;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    h3 {
        color: #4b5563;
        font-weight: 500;
    }
    
    /* Cards de métricas */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div[data-testid="metric-container"] label {
        color: white !important;
        font-weight: 600;
    }
    
    div[data-testid="metric-container"] div {
        color: white !important;
    }
    
    /* Botones */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Upload area */
    .uploadedFile {
        background-color: #f9fafb;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Tablas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Success/Warning/Error boxes */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
    }
    
    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        .main {
            background-color: #1f2937;
        }
        h1, h2, h3 {
            color: #f9fafb;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar session state
def init_session_state():
    """Inicializa variables de sesión"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'classifier' not in st.session_state:
        st.session_state.classifier = None
    if 'analytics' not in st.session_state:
        st.session_state.analytics = None
    if 'predictor' not in st.session_state:
        st.session_state.predictor = None
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = None
    if 'archivo_nombre' not in st.session_state:
        st.session_state.archivo_nombre = None
    if 'procesado' not in st.session_state:
        st.session_state.procesado = False
    if 'tema' not in st.session_state:
        st.session_state.tema = 'claro'
    if 'comparador' not in st.session_state:
        st.session_state.comparador = None
    if 'comparacion_lista' not in st.session_state:
        st.session_state.comparacion_lista = False

def sidebar():
    """Renderiza el sidebar con controles"""
    with st.sidebar:
        st.markdown("# 📊 Trading Analytics")
        st.markdown("---")
        
        # Upload de archivo
        st.markdown("### 📁 Cargar Datos")
        uploaded_file = st.file_uploader(
            "Sube tu archivo .txt de NinjaTrader",
            type=['txt'],
            help="Archivo con datos OHLCV de 1 minuto"
        )
        
        if uploaded_file is not None:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            st.session_state.archivo_nombre = uploaded_file.name
            
            # Botón para procesar
            if st.button("🚀 Analizar", type="primary", use_container_width=True):
                procesar_archivo(tmp_path)
        
        st.markdown("---")
        
        # Glosario
        with st.expander("📖 Glosario"):
            st.markdown("""
            **Rango Diario:** Diferencia entre High y Low del día
            
            **Clasificación:**
            - 🟢 **FUERTE:** Top 33% de movimiento
            - 🟡 **INTERMEDIO:** Medio 33%
            - 🔴 **LATERAL:** Bottom 33%
            
            **Volatilidad:** Desviación estándar de precios intradiarios
            
            **Outlier:** Día con volatilidad extrema (>2σ)
            
            **Correlación:** Medida de relación entre sesiones (-1 a +1)
            
            **Sesiones (Hora de Nueva York - ET):**
            - 🌏 **ASIA:** 7:00 PM - 4:00 AM ET
            - 🇪🇺 **EUROPA:** 3:00 AM - 12:00 PM ET
            - 🇺🇸 **NY:** 9:30 AM - 5:00 PM ET
            
            *Los horarios se ajustan automáticamente según DST*
            """)
        
        # Info
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #6b7280; font-size: 0.85em;'>
            <p><b>Trading Analytics Pro</b></p>
            <p>v1.0 - Sistema de análisis estadístico</p>
        </div>
        """, unsafe_allow_html=True)

def procesar_archivo(ruta_archivo):
    """Procesa el archivo cargado y ejecuta todo el pipeline"""
    
    with st.spinner("⏳ Procesando datos..."):
        # Paso 1: Ingestion
        try:
            parser = DataIngestion(ruta_archivo)
            df = parser.procesar(guardar=False, mostrar_resumen=False)
            
            if df is None:
                st.error("❌ Error al procesar el archivo")
                return
            
            st.session_state.df = df
            
        except Exception as e:
            st.error(f"❌ Error en ingestion: {str(e)}")
            return
    
    with st.spinner("📊 Clasificando días..."):
        # Paso 2: Clasificación
        try:
            classifier = DayClassifier(df)
            classifier.calcular_estadisticas_diarias()
            classifier.calcular_percentiles()
            classifier.clasificar_dias()
            
            st.session_state.classifier = classifier
            
        except Exception as e:
            st.error(f"❌ Error en clasificación: {str(e)}")
            return
    
    with st.spinner("🌏 Analizando sesiones..."):
        # Paso 3: Analytics
        try:
            analytics = SessionAnalytics(df, classifier.clasificaciones)
            analytics.calcular_estadisticas_por_sesion()
            analytics.analizar_distribucion_sesiones()
            analytics.identificar_sesion_dominante()
            analytics.detectar_correlacion_sesiones()
            analytics.analizar_sesiones_por_tipo_dia()
            
            st.session_state.analytics = analytics
            
        except Exception as e:
            st.error(f"❌ Error en analytics: {str(e)}")
            return
    
    with st.spinner("🎯 Generando predicciones..."):
        # Paso 4: Predictor
        try:
            predictor = TradingPredictor(df, classifier.clasificaciones, analytics.stats_sesiones)
            predictor.analizar_patrones_dia_semana()
            predictor.analizar_patron_sesion_previa()
            predictor.analizar_rachas()
            predictor.generar_reglas_probabilisticas()
            
            st.session_state.predictor = predictor
            
        except Exception as e:
            st.error(f"❌ Error en predictor: {str(e)}")
            return
    
    with st.spinner("📈 Creando visualizaciones..."):
        # Paso 5: Visualizaciones
        try:
            visualizer = TradingVisualizer(
                df,
                classifier.clasificaciones,
                analytics.stats_sesiones,
                st.session_state.archivo_nombre.replace('.txt', '')
            )
            
            st.session_state.visualizer = visualizer
            
        except Exception as e:
            st.warning(f"⚠️ No se pudieron crear visualizaciones: {str(e)}")
    
    st.session_state.procesado = True
    st.success("✅ Análisis completado exitosamente!")

def tab_overview():
    """Tab de resumen ejecutivo"""
    st.markdown("## 📊 Resumen Ejecutivo")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    classifier = st.session_state.classifier
    analytics = st.session_state.analytics
    df = st.session_state.df
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Días",
            f"{len(classifier.clasificaciones)}"
        )
    
    with col2:
        dias_fuertes = (classifier.clasificaciones['clasificacion'] == 'FUERTE').sum()
        pct_fuertes = (dias_fuertes / len(classifier.clasificaciones)) * 100
        st.metric(
            "Días Fuertes",
            f"{dias_fuertes}",
            f"{pct_fuertes:.1f}%"
        )
    
    with col3:
        rango_promedio = classifier.clasificaciones['rango_diario'].mean()
        st.metric(
            "Rango Promedio",
            f"{rango_promedio:.1f} pts"
        )
    
    with col4:
        outliers = classifier.clasificaciones['es_outlier'].sum()
        st.metric(
            "Días Outliers",
            f"{outliers}"
        )
    
    st.markdown("---")
    
    # Insights clave
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔑 Insights Clave")
        
        # Mejor día de semana
        analisis_semana = classifier.analizar_por_dia_semana()
        mejor_dia = analisis_semana['%_FUERTE'].idxmax()
        mejor_pct = analisis_semana.loc[mejor_dia, '%_FUERTE']
        
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        mejor_dia_esp = dias_esp.get(mejor_dia, mejor_dia)
        
        st.success(f"**Mejor día para trading:** {mejor_dia_esp} ({mejor_pct:.1f}% días fuertes)")
        
        # Sesión dominante
        dominantes = analytics.identificar_sesion_dominante()
        sesion_top = dominantes['sesion_dominante'].value_counts().idxmax()
        sesion_pct = (dominantes['sesion_dominante'].value_counts()[sesion_top] / len(dominantes) * 100)
        
        st.info(f"**Sesión dominante:** {sesion_top} ({sesion_pct:.1f}% de los días)")
        
        # Correlación más fuerte
        if analytics.correlaciones:
            max_corr = max(analytics.correlaciones.items(), key=lambda x: abs(x[1]))
            st.warning(f"**Correlación más fuerte:** {max_corr[0]} = {max_corr[1]:+.3f}")
    
    with col2:
        st.markdown("### 📈 Distribución de Días")
        
        # Gráfico de pie
        conteo = classifier.clasificaciones['clasificacion'].value_counts()
        
        fig_data = {
            'Clasificación': conteo.index.tolist(),
            'Cantidad': conteo.values.tolist()
        }
        
        st.bar_chart(conteo)
    
    st.markdown("---")
    
    # Top 5 días más fuertes
    st.markdown("### 🏆 Top 5 Días Más Fuertes")
    
    top5 = classifier.clasificaciones.nlargest(5, 'rango_diario')[
        ['rango_diario', 'cambio_pct', 'direccion', 'volatilidad']
    ]
    
    st.dataframe(
        top5.style.format({
            'rango_diario': '{:.2f}',
            'cambio_pct': '{:+.2f}%',
            'volatilidad': '{:.2f}'
        }),
        use_container_width=True
    )

def tab_clasificacion():
    """Tab de clasificación de días"""
    st.markdown("## 📅 Clasificación de Días")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    classifier = st.session_state.classifier
    
    # Mostrar tabla completa
    st.markdown("### 📋 Tabla Completa de Clasificaciones")
    
    df_display = classifier.clasificaciones[[
        'dia_semana', 'clasificacion', 'rango_diario', 
        'cambio_pct', 'direccion', 'volatilidad', 'es_outlier'
    ]].copy()
    
    # Aplicar formato
    st.dataframe(
        df_display.style.format({
            'rango_diario': '{:.2f}',
            'cambio_pct': '{:+.2f}%',
            'volatilidad': '{:.2f}'
        }).background_gradient(subset=['rango_diario'], cmap='RdYlGn'),
        use_container_width=True,
        height=400
    )
    
    # Análisis por día de semana
    st.markdown("### 📊 Análisis por Día de Semana")
    
    analisis_semana = classifier.analizar_por_dia_semana()
    st.dataframe(analisis_semana, use_container_width=True)
    
    # Rachas detectadas
    st.markdown("### 🔁 Rachas Detectadas (3+ días consecutivos)")
    
    rachas = classifier.detectar_rachas()
    
    if len(rachas) > 0:
        st.dataframe(rachas, use_container_width=True)
    else:
        st.info("No se detectaron rachas significativas")

def tab_sesiones():
    """Tab de análisis de sesiones"""
    st.markdown("## 🌏 Análisis de Sesiones")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    analytics = st.session_state.analytics
    
    # Distribución de sesiones
    st.markdown("### 📊 Distribución de Rangos por Sesión")
    
    dist = analytics.analizar_distribucion_sesiones()
    st.dataframe(dist, use_container_width=True)
    
    # Sesiones por tipo de día
    st.markdown("### 🎯 Sesiones por Tipo de Día")
    
    por_tipo = analytics.analizar_sesiones_por_tipo_dia()
    if por_tipo is not None:
        st.dataframe(por_tipo, use_container_width=True)
    
    # Correlaciones
    st.markdown("### 🔗 Correlaciones entre Sesiones")
    
    col1, col2, col3 = st.columns(3)
    
    if analytics.correlaciones:
        for i, (clave, valor) in enumerate(analytics.correlaciones.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                delta_color = "normal" if abs(valor) < 0.5 else "inverse"
                st.metric(
                    clave,
                    f"{valor:+.3f}",
                    delta_color=delta_color
                )

def tab_predictor():
    """Tab de predicciones"""
    st.markdown("## 🎯 Motor Predictivo")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    predictor = st.session_state.predictor
    
    # Mostrar reglas
    st.markdown("### 📋 Reglas Probabilísticas")
    
    if predictor.reglas_probabilisticas:
        for regla in predictor.reglas_probabilisticas:
            with st.expander(f"**{regla['tipo']}** | {regla['condicion']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Predicción:** {regla['prediccion']}")
                    st.markdown(f"**Táctica:** {regla['tactica']}")
                
                with col2:
                    st.metric("Probabilidad", f"{regla['probabilidad']:.1f}%")
                    st.metric("Confianza", regla['confianza'])
    else:
        st.warning("No se generaron reglas probabilísticas")

def tab_visualizaciones():
    """Tab de visualizaciones interactivas"""
    st.markdown("## 📈 Visualizaciones Interactivas")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    visualizer = st.session_state.visualizer
    
    # Crear todas las figuras
    st.markdown("### 🔥 Heatmap Día-Sesión")
    fig1 = visualizer.crear_heatmap_semana_sesion()
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Distribución de Rangos")
    fig2 = visualizer.crear_distribucion_rangos()
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📉 Timeline de Clasificaciones")
    fig3 = visualizer.crear_timeline_clasificaciones()
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Correlación entre Sesiones")
    fig4 = visualizer.crear_correlacion_sesiones()
    st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Clasificaciones por Día")
    fig5 = visualizer.crear_barras_clasificacion_dia()
    st.plotly_chart(fig5, use_container_width=True)

def tab_comparacion():
    """Tab de comparación multi-contrato"""
    st.markdown("## 🔀 Comparación de Contratos")
    
    st.info("👈 Sube dos archivos .txt en el sidebar para comparar contratos")
    
    # Upload de segundo archivo
    st.markdown("### 📁 Cargar Segundo Contrato")
    
    uploaded_file_2 = st.file_uploader(
        "Sube el segundo archivo .txt para comparar",
        type=['txt'],
        key='file_2',
        help="Archivo con datos OHLCV de 1 minuto del segundo contrato"
    )
    
    if uploaded_file_2 is not None and st.session_state.procesado:
        if st.button("🔀 Comparar Contratos", type="primary", use_container_width=True):
            
            # Guardar archivo temporalmente
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                tmp_file.write(uploaded_file_2.getvalue())
                tmp_path_2 = tmp_file.name
            
            with st.spinner("⏳ Procesando segundo contrato..."):
                # Procesar segundo archivo
                try:
                    from src.ingestion import DataIngestion
                    from src.classifier import DayClassifier
                    
                    parser_2 = DataIngestion(tmp_path_2)
                    df_2 = parser_2.procesar(guardar=False, mostrar_resumen=False)
                    
                    if df_2 is None:
                        st.error("❌ Error al procesar segundo archivo")
                        return
                    
                    # Clasificar segundo contrato
                    classifier_2 = DayClassifier(df_2)
                    classifier_2.calcular_estadisticas_diarias()
                    classifier_2.calcular_percentiles()
                    classifier_2.clasificar_dias()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
            
            with st.spinner("📊 Generando comparación..."):
                try:
                    from src.multi_contract import MultiContractComparison
                    
                    # Preparar datos
                    contratos_data = {
                        st.session_state.archivo_nombre.replace('.txt', ''): {
                            'df': st.session_state.df,
                            'clasificaciones': st.session_state.classifier.clasificaciones
                        },
                        uploaded_file_2.name.replace('.txt', ''): {
                            'df': df_2,
                            'clasificaciones': classifier_2.clasificaciones
                        }
                    }
                    
                    # Crear comparador
                    comparador = MultiContractComparison(contratos_data)
                    comparador.calcular_metricas_comparativas()
                    comparador.calcular_ratios()
                    
                    # Guardar en session state
                    st.session_state.comparador = comparador
                    st.session_state.comparacion_lista = True
                    
                    st.success("✅ Comparación completada!")
                    
                except Exception as e:
                    st.error(f"❌ Error en comparación: {str(e)}")
                    return
    
    # Mostrar resultados si hay comparación
    if hasattr(st.session_state, 'comparacion_lista') and st.session_state.comparacion_lista:
        comparador = st.session_state.comparador
        
        st.markdown("---")
        
        # Métricas comparativas
        st.markdown("### 📊 Métricas Comparativas")
        
        comparacion_df = comparador.comparacion
        
        # Formatear para display
        display_df = comparacion_df[[
            'total_dias', 'rango_promedio', 'pct_dias_fuertes', 
            'volatilidad_promedio', 'volumen_promedio', 'outliers'
        ]].copy()
        
        display_df.columns = [
            'Días', 'Rango Prom.', '% Fuertes', 
            'Volatilidad', 'Volumen Prom.', 'Outliers'
        ]
        
        st.dataframe(
            display_df.style.format({
                'Rango Prom.': '{:.1f}',
                '% Fuertes': '{:.1f}%',
                'Volatilidad': '{:.2f}',
                'Volumen Prom.': '{:,.0f}'
            }).background_gradient(subset=['Rango Prom.'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Ratios y recomendaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Ratios")
            
            if comparador.ratios:
                st.info(f"**Volatilidad:** {comparador.ratios['volatilidad']['interpretacion']}")
                st.info(f"**Volumen:** {comparador.ratios['volumen']['interpretacion']}")
                
                dif_fuertes = comparador.ratios['dias_fuertes']['diferencia']
                st.info(f"**Diferencia días fuertes:** {dif_fuertes:.1f} puntos porcentuales")
        
        with col2:
            st.markdown("### 🎯 Recomendaciones")
            
            mas_volatil = comparacion_df['rango_promedio'].idxmax()
            mas_consistente = comparacion_df['outliers'].idxmin()
            mayor_volumen = comparacion_df['volumen_promedio'].idxmax()
            
            st.success(f"**Mayor movimiento:** {mas_volatil}")
            st.warning(f"**Más consistente:** {mas_consistente}")
            st.info(f"**Mejor liquidez:** {mayor_volumen}")
        
        st.markdown("---")
        
        # Gráficos
        st.markdown("### 📊 Gráficos Comparativos")
        
        # Gráfico comparativo
        fig1 = comparador.crear_grafico_comparativo()
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("---")
        
        # Overlay temporal
        st.markdown("### 📉 Evolución Temporal")
        
        fig2 = comparador.crear_grafico_overlay()
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        
        # Correlación
        correlacion = comparador.calcular_correlacion_temporal()
        if correlacion:
            st.metric(
                "Correlación Temporal",
                f"{correlacion:+.3f}",
                help="Mide qué tan similares se mueven los contratos (-1 a +1)"
            )
            
            if abs(correlacion) > 0.7:
                st.success("✓ Los contratos se mueven de forma muy similar")
            elif abs(correlacion) > 0.4:
                st.warning("~ Los contratos tienen correlación moderada")
            else:
                st.info("○ Los contratos se mueven de forma independiente")


def main():
    """Función principal"""
    
    # Cargar CSS
    load_css()
    
    # Inicializar estado
    init_session_state()
    
    # Sidebar
    sidebar()
    
    # Header principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3em; margin: 0;'>📊 Trading Analytics Pro</h1>
        <p style='font-size: 1.2em; color: #6b7280;'>Sistema profesional de análisis estadístico para futuros</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "📅 Clasificación",
        "🌏 Sesiones",
        "🎯 Predictor",
        "📈 Visualizaciones",
        "🔀 Comparar"
    ])
    
    with tab1:
        tab_overview()
    
    with tab2:
        tab_clasificacion()
    
    with tab3:
        tab_sesiones()
    
    with tab4:
        tab_predictor()
    
    with tab5:
        tab_visualizaciones()
    
    with tab6:
        tab_comparacion()

if __name__ == "__main__":
    main()
