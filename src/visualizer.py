"""
Módulo de visualización
Genera gráficos interactivos profesionales para análisis de trading
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Importar Plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠ Plotly no está instalado. Ejecutá: pip install plotly")

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import OUTPUTS_DIR


class TradingVisualizer:
    """
    Generador de visualizaciones interactivas para análisis de trading
    """
    
    def __init__(self, df, clasificaciones, stats_sesiones, nombre_contrato=""):
        """
        Inicializa el visualizador
        
        Args:
            df: DataFrame con datos procesados
            clasificaciones: DataFrame con clasificaciones de días
            stats_sesiones: DataFrame con estadísticas de sesiones
            nombre_contrato: nombre del contrato (para títulos)
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly no está disponible. Instálalo con: pip install plotly")
        
        self.df = df
        self.clasificaciones = clasificaciones
        self.stats_sesiones = stats_sesiones
        self.nombre_contrato = nombre_contrato
        self.figuras = {}
        
        # Paleta de colores profesional
        self.colores = {
            'FUERTE': '#10b981',      # Verde
            'INTERMEDIO': '#f59e0b',  # Amarillo/Naranja
            'LATERAL': '#ef4444',     # Rojo
            'ASIA': '#3b82f6',        # Azul
            'EUROPA': '#8b5cf6',      # Púrpura
            'NY': '#ec4899',          # Rosa
            'fondo': '#ffffff',
            'grid': '#e5e7eb',
            'texto': '#1f2937'
        }
    
    def crear_heatmap_semana_sesion(self):
        """
        Crea heatmap de rango promedio por día de semana y sesión
        Muestra qué combinación día+sesión es más volátil
        
        Returns:
            plotly.graph_objects.Figure
        """
        # Preparar datos - agregar dia_semana desde el índice si no existe
        df_trabajo = self.df.copy()
        if 'dia_semana' not in df_trabajo.columns:
            df_trabajo['dia_semana'] = df_trabajo['datetime'].dt.day_name()
        
        # Calcular rango promedio por día de semana y sesión
        pivot_data = df_trabajo.groupby(['dia_semana', 'sesion'])['rango'].mean().reset_index()
        pivot_tabla = pivot_data.pivot(index='dia_semana', columns='sesion', values='rango')
        
        # Ordenar días correctamente
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        
        pivot_tabla = pivot_tabla.reindex(orden_dias)
        pivot_tabla.index = [dias_esp.get(d, d) for d in pivot_tabla.index]
        
        # Crear heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_tabla.values,
            x=pivot_tabla.columns,
            y=pivot_tabla.index,
            colorscale='RdYlGn',
            text=np.round(pivot_tabla.values, 1),
            texttemplate='%{text} pts',
            textfont={"size": 12},
            colorbar=dict(title="Rango<br>Promedio")
        ))
        
        fig.update_layout(
            title={
                'text': f'Volatilidad por Día y Sesión - {self.nombre_contrato}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.colores['texto']}
            },
            xaxis_title="Sesión",
            yaxis_title="Día de la Semana",
            font=dict(size=12, color=self.colores['texto']),
            plot_bgcolor=self.colores['fondo'],
            paper_bgcolor=self.colores['fondo'],
            height=500,
            hovermode='closest'
        )
        
        self.figuras['heatmap_semana'] = fig
        return fig
    
    def crear_distribucion_rangos(self):
        """
        Crea histograma de distribución de rangos diarios
        Con líneas marcando los percentiles de clasificación
        
        Returns:
            plotly.graph_objects.Figure
        """
        rangos = self.clasificaciones['rango_diario']
        
        # Calcular percentiles
        p33 = rangos.quantile(0.33)
        p67 = rangos.quantile(0.67)
        media = rangos.mean()
        
        # Crear histograma
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=rangos,
            nbinsx=30,
            name='Rangos diarios',
            marker_color='rgba(59, 130, 246, 0.7)',
            hovertemplate='Rango: %{x:.1f} pts<br>Frecuencia: %{y}<extra></extra>'
        ))
        
        # Líneas de percentiles
        fig.add_vline(
            x=p33, 
            line_dash="dash", 
            line_color=self.colores['LATERAL'],
            annotation_text="P33 (Límite Lateral)",
            annotation_position="top"
        )
        
        fig.add_vline(
            x=p67, 
            line_dash="dash", 
            line_color=self.colores['FUERTE'],
            annotation_text="P67 (Límite Fuerte)",
            annotation_position="top"
        )
        
        fig.add_vline(
            x=media,
            line_dash="dot",
            line_color=self.colores['texto'],
            annotation_text=f"Media: {media:.1f}",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            title={
                'text': f'Distribución de Rangos Diarios - {self.nombre_contrato}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.colores['texto']}
            },
            xaxis_title="Rango Diario (puntos)",
            yaxis_title="Frecuencia",
            font=dict(size=12, color=self.colores['texto']),
            plot_bgcolor=self.colores['fondo'],
            paper_bgcolor=self.colores['fondo'],
            showlegend=False,
            height=500
        )
        
        self.figuras['distribucion_rangos'] = fig
        return fig
    
    def crear_timeline_clasificaciones(self):
        """
        Crea timeline visual de clasificaciones día por día
        
        Returns:
            plotly.graph_objects.Figure
        """
        # Preparar datos
        df_timeline = self.clasificaciones.copy()
        df_timeline = df_timeline.sort_index()
        df_timeline['fecha_str'] = df_timeline.index.astype(str)
        
        # Mapeo de colores
        color_map = {
            'FUERTE': self.colores['FUERTE'],
            'INTERMEDIO': self.colores['INTERMEDIO'],
            'LATERAL': self.colores['LATERAL']
        }
        
        fig = go.Figure()
        
        # Crear scatter plot con colores por clasificación
        for clasificacion in ['LATERAL', 'INTERMEDIO', 'FUERTE']:
            datos = df_timeline[df_timeline['clasificacion'] == clasificacion]
            
            fig.add_trace(go.Scatter(
                x=datos.index,
                y=datos['rango_diario'],
                mode='markers+lines',
                name=clasificacion,
                marker=dict(
                    size=10,
                    color=color_map[clasificacion],
                    line=dict(width=1, color='white')
                ),
                line=dict(width=1, color=color_map[clasificacion]),
                hovertemplate=(
                    '<b>%{x|%Y-%m-%d}</b><br>' +
                    f'{clasificacion}<br>' +
                    'Rango: %{y:.1f} pts<br>' +
                    '<extra></extra>'
                )
            ))
        
        # Línea de tendencia
        z = np.polyfit(range(len(df_timeline)), df_timeline['rango_diario'], 2)
        p = np.poly1d(z)
        
        fig.add_trace(go.Scatter(
            x=df_timeline.index,
            y=p(range(len(df_timeline))),
            mode='lines',
            name='Tendencia',
            line=dict(dash='dash', color='gray', width=2),
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            title={
                'text': f'Timeline de Clasificaciones - {self.nombre_contrato}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.colores['texto']}
            },
            xaxis_title="Fecha",
            yaxis_title="Rango Diario (puntos)",
            font=dict(size=12, color=self.colores['texto']),
            plot_bgcolor=self.colores['fondo'],
            paper_bgcolor=self.colores['fondo'],
            hovermode='closest',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        self.figuras['timeline'] = fig
        return fig
    
    def crear_correlacion_sesiones(self):
        """
        Crea scatter plots mostrando correlación entre sesiones
        
        Returns:
            plotly.graph_objects.Figure
        """
        # Preparar datos
        pivot = self.stats_sesiones.reset_index().pivot(
            index='fecha',
            columns='sesion',
            values='rango_sesion'
        )
        
        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Asia vs Europa', 'Europa vs NY')
        )
        
        # Asia vs Europa
        if 'ASIA' in pivot.columns and 'EUROPA' in pivot.columns:
            # Eliminar NaN para tener misma longitud
            datos_ae = pivot[['ASIA', 'EUROPA']].dropna()
            
            if len(datos_ae) > 0:
                corr_ae = datos_ae['ASIA'].corr(datos_ae['EUROPA'])
                
                fig.add_trace(
                    go.Scatter(
                        x=datos_ae['ASIA'],
                        y=datos_ae['EUROPA'],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color=self.colores['ASIA'],
                            opacity=0.6
                        ),
                        name='Asia-Europa',
                        hovertemplate=(
                            'Asia: %{x:.1f}<br>' +
                            'Europa: %{y:.1f}<br>' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=1
                )
                
                # Línea de tendencia
                z = np.polyfit(datos_ae['ASIA'], datos_ae['EUROPA'], 1)
                p = np.poly1d(z)
                x_line = np.linspace(datos_ae['ASIA'].min(), datos_ae['ASIA'].max(), 100)
                
                fig.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=p(x_line),
                        mode='lines',
                        line=dict(dash='dash', color='red'),
                        name=f'Corr: {corr_ae:.2f}',
                        showlegend=False
                    ),
                    row=1, col=1
                )
                
                fig.add_annotation(
                    text=f'Correlación: {corr_ae:.3f}',
                    xref='x1', yref='y1',
                    x=datos_ae['ASIA'].max() * 0.95,
                    y=datos_ae['EUROPA'].min() * 1.1,
                    showarrow=False,
                    font=dict(size=12, color=self.colores['texto']),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor=self.colores['ASIA'],
                    borderwidth=2
                )
        
        # Europa vs NY
        if 'EUROPA' in pivot.columns and 'NY' in pivot.columns:
            # Eliminar NaN para tener misma longitud
            datos_en = pivot[['EUROPA', 'NY']].dropna()
            
            if len(datos_en) > 0:
                corr_en = datos_en['EUROPA'].corr(datos_en['NY'])
                
                fig.add_trace(
                    go.Scatter(
                        x=datos_en['EUROPA'],
                        y=datos_en['NY'],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color=self.colores['NY'],
                            opacity=0.6
                        ),
                        name='Europa-NY',
                        hovertemplate=(
                            'Europa: %{x:.1f}<br>' +
                            'NY: %{y:.1f}<br>' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=2
                )
                
                # Línea de tendencia
                z = np.polyfit(datos_en['EUROPA'], datos_en['NY'], 1)
                p = np.poly1d(z)
                x_line = np.linspace(datos_en['EUROPA'].min(), datos_en['EUROPA'].max(), 100)
                
                fig.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=p(x_line),
                        mode='lines',
                        line=dict(dash='dash', color='red'),
                        name=f'Corr: {corr_en:.2f}',
                        showlegend=False
                    ),
                    row=1, col=2
                )
                
                fig.add_annotation(
                    text=f'Correlación: {corr_en:.3f}',
                    xref='x2', yref='y2',
                    x=datos_en['EUROPA'].max() * 0.95,
                    y=datos_en['NY'].min() * 1.1,
                    showarrow=False,
                    font=dict(size=12, color=self.colores['texto']),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor=self.colores['NY'],
                    borderwidth=2
                )
        
        fig.update_xaxes(title_text="Asia (puntos)", row=1, col=1)
        fig.update_yaxes(title_text="Europa (puntos)", row=1, col=1)
        fig.update_xaxes(title_text="Europa (puntos)", row=1, col=2)
        fig.update_yaxes(title_text="NY (puntos)", row=1, col=2)
        
        fig.update_layout(
            title={
                'text': f'Correlación entre Sesiones - {self.nombre_contrato}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.colores['texto']}
            },
            font=dict(size=12, color=self.colores['texto']),
            plot_bgcolor=self.colores['fondo'],
            paper_bgcolor=self.colores['fondo'],
            height=500,
            showlegend=False
        )
        
        self.figuras['correlacion'] = fig
        return fig
    
    def crear_barras_clasificacion_dia(self):
        """
        Crea gráfico de barras apiladas: clasificación por día de semana
        
        Returns:
            plotly.graph_objects.Figure
        """
        # Preparar datos - asegurar que dia_semana existe
        clasificaciones_trabajo = self.clasificaciones.copy()
        if 'dia_semana' not in clasificaciones_trabajo.columns:
            clasificaciones_trabajo['dia_semana'] = pd.to_datetime(clasificaciones_trabajo.index).day_name()
        
        # Crear crosstab
        crosstab = pd.crosstab(
            clasificaciones_trabajo['dia_semana'],
            clasificaciones_trabajo['clasificacion']
        )
        
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        
        crosstab = crosstab.reindex(orden_dias, fill_value=0)
        crosstab.index = [dias_esp.get(d, d) for d in crosstab.index]
        
        fig = go.Figure()
        
        for clasificacion in ['LATERAL', 'INTERMEDIO', 'FUERTE']:
            if clasificacion in crosstab.columns:
                fig.add_trace(go.Bar(
                    name=clasificacion,
                    x=crosstab.index,
                    y=crosstab[clasificacion],
                    marker_color=self.colores[clasificacion],
                    hovertemplate=(
                        f'<b>{clasificacion}</b><br>' +
                        '%{x}<br>' +
                        'Cantidad: %{y}<br>' +
                        '<extra></extra>'
                    )
                ))
        
        fig.update_layout(
            title={
                'text': f'Distribución de Días por Clasificación - {self.nombre_contrato}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.colores['texto']}
            },
            xaxis_title="Día de la Semana",
            yaxis_title="Cantidad de Días",
            barmode='stack',
            font=dict(size=12, color=self.colores['texto']),
            plot_bgcolor=self.colores['fondo'],
            paper_bgcolor=self.colores['fondo'],
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        self.figuras['barras_dia'] = fig
        return fig
    
    def generar_dashboard_completo(self):
        """
        Genera un dashboard HTML interactivo con todos los gráficos
        
        Returns:
            str: ruta del archivo HTML generado
        """
        print("\n" + "="*70)
        print("GENERANDO DASHBOARD INTERACTIVO")
        print("="*70)
        
        # Crear todas las figuras
        print("  • Generando heatmap día-sesión...")
        self.crear_heatmap_semana_sesion()
        
        print("  • Generando distribución de rangos...")
        self.crear_distribucion_rangos()
        
        print("  • Generando timeline...")
        self.crear_timeline_clasificaciones()
        
        print("  • Generando correlaciones...")
        self.crear_correlacion_sesiones()
        
        print("  • Generando gráfico de barras...")
        self.crear_barras_clasificacion_dia()
        
        # Crear HTML con todas las figuras
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Análisis - {self.nombre_contrato}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f9fafb;
            color: #1f2937;
        }}
        .header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard de Análisis de Trading</h1>
            <p>Contrato: {self.nombre_contrato}</p>
        </div>
        
        <div class="chart-container">
            {self.figuras['heatmap_semana'].to_html(include_plotlyjs='cdn', full_html=False)}
        </div>
        
        <div class="chart-container">
            {self.figuras['barras_dia'].to_html(include_plotlyjs=False, full_html=False)}
        </div>
        
        <div class="chart-container">
            {self.figuras['distribucion_rangos'].to_html(include_plotlyjs=False, full_html=False)}
        </div>
        
        <div class="chart-container">
            {self.figuras['timeline'].to_html(include_plotlyjs=False, full_html=False)}
        </div>
        
        <div class="chart-container">
            {self.figuras['correlacion'].to_html(include_plotlyjs=False, full_html=False)}
        </div>
        
        <div class="footer">
            <p>Sistema de Análisis de Trading - Generado automáticamente</p>
            <p>Todos los gráficos son interactivos: hover para detalles, zoom, pan</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Guardar HTML
        nombre_archivo = f"dashboard_{self.nombre_contrato.replace(' ', '_')}.html"
        ruta_salida = OUTPUTS_DIR / nombre_archivo
        
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ Dashboard generado: {ruta_salida}")
        print("\n  TIP: Abrí el archivo HTML en tu navegador para ver los gráficos interactivos")
        
        return str(ruta_salida)


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def generar_visualizaciones_completas(df, clasificaciones, stats_sesiones, nombre_contrato=""):
    """
    Genera todas las visualizaciones y dashboard
    
    Args:
        df: DataFrame con datos procesados
        clasificaciones: DataFrame con clasificaciones
        stats_sesiones: DataFrame con stats de sesiones
        nombre_contrato: nombre del contrato
        
    Returns:
        TradingVisualizer con todas las figuras generadas
    """
    visualizer = TradingVisualizer(df, clasificaciones, stats_sesiones, nombre_contrato)
    visualizer.generar_dashboard_completo()
    
    return visualizer


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el visualizador
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    from src.analytics import SessionAnalytics
    
    # Cargar datos
    df = cargar_datos_procesados("MNQ 03-26.Last_processed.parquet")
    
    if df is not None:
        # Clasificar
        classifier = DayClassifier(df)
        classifier.calcular_estadisticas_diarias()
        classifier.clasificar_dias()
        
        # Analizar sesiones
        analytics = SessionAnalytics(df, classifier.clasificaciones)
        analytics.calcular_estadisticas_por_sesion()
        
        # Generar visualizaciones
        visualizer = generar_visualizaciones_completas(
            df,
            classifier.clasificaciones,
            analytics.stats_sesiones,
            "MNQ 03-26"
        )
        
        print("\n✓ Visualizaciones completadas")
