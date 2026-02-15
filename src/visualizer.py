"""
Módulo de visualización - Versión simplificada para Streamlit Cloud
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
    pio.templates.default = "plotly_dark"
except ImportError:
    PLOTLY_AVAILABLE = False

sys.path.append(str(Path(__file__).parent.parent))
from config import OUTPUTS_DIR


class TradingVisualizer:
    
    def __init__(self, df, clasificaciones, stats_sesiones, nombre_contrato=""):
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly no disponible")
        
        self.df = df
        self.clasificaciones = clasificaciones
        self.stats_sesiones = stats_sesiones
        self.nombre_contrato = nombre_contrato
        self.figuras = {}
        
        self.colores = {
            'FUERTE': '#10b981',
            'INTERMEDIO': '#f59e0b',
            'LATERAL': '#ef4444',
            'ASIA': '#3b82f6',
            'EUROPA': '#8b5cf6',
            'NY': '#ec4899'
        }
    
    def crear_heatmap_semana_sesion(self):
        df_trabajo = self.df.copy()
        if 'dia_semana' not in df_trabajo.columns:
            df_trabajo['dia_semana'] = df_trabajo['datetime'].dt.day_name()
        
        pivot_data = df_trabajo.groupby(['dia_semana', 'sesion'])['rango'].mean().reset_index()
        pivot_tabla = pivot_data.pivot(index='dia_semana', columns='sesion', values='rango')
        
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        
        pivot_tabla = pivot_tabla.reindex(orden_dias)
        pivot_tabla.index = [dias_esp.get(d, d) for d in pivot_tabla.index]
        
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=pivot_tabla.values,
            x=pivot_tabla.columns,
            y=pivot_tabla.index,
            colorscale='Viridis',
            text=np.round(pivot_tabla.values, 1),
            texttemplate='%{text} pts'
        ))
        
        fig.update_layout(
            title=f'Volatilidad por Día y Sesión - {self.nombre_contrato}',
            xaxis_title="Sesión",
            yaxis_title="Día",
            height=500
        )
        
        return fig
    
    def crear_distribucion_rangos(self):
        rangos = self.clasificaciones['rango_diario']
        p33 = rangos.quantile(0.33)
        p67 = rangos.quantile(0.67)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=rangos, nbinsx=30, marker_color='#8b5cf6'))
        fig.add_vline(x=p33, line_dash="dash", line_color='#ef4444', annotation_text="P33")
        fig.add_vline(x=p67, line_dash="dash", line_color='#10b981', annotation_text="P67")
        
        fig.update_layout(
            title=f'Distribución de Rangos - {self.nombre_contrato}',
            xaxis_title="Rango (pts)",
            yaxis_title="Frecuencia",
            height=500
        )
        
        return fig
    
    def crear_timeline_clasificaciones(self):
        df_timeline = self.clasificaciones.sort_index()
        
        fig = go.Figure()
        
        for clasificacion in ['LATERAL', 'INTERMEDIO', 'FUERTE']:
            datos = df_timeline[df_timeline['clasificacion'] == clasificacion]
            fig.add_trace(go.Scatter(
                x=datos.index,
                y=datos['rango_diario'],
                mode='markers+lines',
                name=clasificacion,
                marker_color=self.colores[clasificacion]
            ))
        
        fig.update_layout(
            title=f'Timeline - {self.nombre_contrato}',
            xaxis_title="Fecha",
            yaxis_title="Rango (pts)",
            height=500
        )
        
        return fig
    
    def crear_correlacion_sesiones(self):
        pivot = self.stats_sesiones.reset_index().pivot(
            index='fecha',
            columns='sesion',
            values='rango_sesion'
        )
        
        fig = make_subplots(rows=1, cols=2, subplot_titles=('Asia vs Europa', 'Europa vs NY'))
        
        if 'ASIA' in pivot.columns and 'EUROPA' in pivot.columns:
            datos = pivot[['ASIA', 'EUROPA']].dropna()
            if len(datos) > 0:
                fig.add_trace(
                    go.Scatter(x=datos['ASIA'], y=datos['EUROPA'], mode='markers', marker_color='#3b82f6'),
                    row=1, col=1
                )
        
        if 'EUROPA' in pivot.columns and 'NY' in pivot.columns:
            datos = pivot[['EUROPA', 'NY']].dropna()
            if len(datos) > 0:
                fig.add_trace(
                    go.Scatter(x=datos['EUROPA'], y=datos['NY'], mode='markers', marker_color='#ec4899'),
                    row=1, col=2
                )
        
        fig.update_layout(
            title=f'Correlación - {self.nombre_contrato}',
            height=500
        )
        
        return fig
    
    def crear_barras_clasificacion_dia(self):
        clasificaciones_trabajo = self.clasificaciones.copy()
        if 'dia_semana' not in clasificaciones_trabajo.columns:
            clasificaciones_trabajo['dia_semana'] = pd.to_datetime(clasificaciones_trabajo.index).day_name()
        
        crosstab = pd.crosstab(clasificaciones_trabajo['dia_semana'], clasificaciones_trabajo['clasificacion'])
        
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
                    marker_color=self.colores[clasificacion]
                ))
        
        fig.update_layout(
            title=f'Clasificación por Día - {self.nombre_contrato}',
            xaxis_title="Día",
            yaxis_title="Cantidad",
            barmode='stack',
            height=500
        )
        
        return fig
    
    def generar_dashboard_completo(self):
        print("\nGenerando dashboard...")
        
        self.crear_heatmap_semana_sesion()
        self.crear_distribucion_rangos()
        self.crear_timeline_clasificaciones()
        self.crear_correlacion_sesiones()
        self.crear_barras_clasificacion_dia()
        
        nombre_archivo = f"dashboard_{self.nombre_contrato.replace(' ', '_')}.html"
        ruta_salida = OUTPUTS_DIR / nombre_archivo
        
        print(f"Dashboard generado: {ruta_salida}")
        return str(ruta_salida)


def generar_visualizaciones_completas(df, clasificaciones, stats_sesiones, nombre_contrato=""):
    visualizer = TradingVisualizer(df, clasificaciones, stats_sesiones, nombre_contrato)
    visualizer.generar_dashboard_completo()
    return visualizer
