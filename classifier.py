"""
Módulo de clasificación de días
Analiza y clasifica días de trading según múltiples métricas
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import CLASIFICACION, MIN_DIAS_ANALISIS, DECIMALES_PORCENTAJE


class DayClassifier:
    """
    Clasificador inteligente de días de trading
    """
    
    def __init__(self, df):
        """
        Inicializa el clasificador
        
        Args:
            df: DataFrame con datos procesados (de ingestion.py)
        """
        self.df = df.copy()
        self.stats_diarias = None
        self.clasificaciones = None
        self.percentiles = None
        
    def calcular_estadisticas_diarias(self):
        """
        Calcula métricas agregadas por día
        
        Returns:
            DataFrame con estadísticas diarias
        """
        stats = self.df.groupby('fecha').agg({
            'high': 'max',
            'low': 'min',
            'open': 'first',
            'close': 'last',
            'volume': 'sum',
            'rango': 'sum',  # Suma de rangos de todas las velas
            'datetime': 'count'  # Cantidad de velas en el día
        }).rename(columns={'datetime': 'num_velas'})
        
        # Calcular métricas adicionales
        stats['rango_diario'] = stats['high'] - stats['low']
        stats['cambio_diario'] = stats['close'] - stats['open']
        stats['cambio_pct'] = (stats['cambio_diario'] / stats['open']) * 100
        stats['direccion'] = stats['cambio_diario'].apply(
            lambda x: 'ALCISTA' if x > 0 else ('BAJISTA' if x < 0 else 'NEUTRO')
        )
        
        # Calcular volatilidad (desviación estándar de los cierres intradiarios)
        volatilidad = self.df.groupby('fecha')['close'].std()
        stats['volatilidad'] = volatilidad
        
        # Agregar día de la semana
        stats['dia_semana'] = pd.to_datetime(stats.index).day_name()
        
        self.stats_diarias = stats
        
        print(f"✓ Calculadas estadísticas para {len(stats)} días")
        return stats
    
    def calcular_percentiles(self, metrica='rango_diario'):
        """
        Calcula percentiles para clasificación adaptativa
        
        Args:
            metrica: columna a usar para clasificar ('rango_diario', 'volatilidad', etc.)
            
        Returns:
            dict con percentiles calculados
        """
        if self.stats_diarias is None:
            self.calcular_estadisticas_diarias()
        
        valores = self.stats_diarias[metrica]
        
        self.percentiles = {
            'p33': np.percentile(valores, 33.33),
            'p50': np.percentile(valores, 50),
            'p67': np.percentile(valores, 66.67),
            'p75': np.percentile(valores, 75),
            'p90': np.percentile(valores, 90),
            'min': valores.min(),
            'max': valores.max(),
            'mean': valores.mean(),
            'std': valores.std()
        }
        
        print(f"\n{'Percentiles de ' + metrica + ':'}")
        print(f"  Mínimo: {self.percentiles['min']:.2f}")
        print(f"  P33 (límite LATERAL): {self.percentiles['p33']:.2f}")
        print(f"  P50 (mediana): {self.percentiles['p50']:.2f}")
        print(f"  P67 (límite FUERTE): {self.percentiles['p67']:.2f}")
        print(f"  P90: {self.percentiles['p90']:.2f}")
        print(f"  Máximo: {self.percentiles['max']:.2f}")
        print(f"  Media: {self.percentiles['mean']:.2f} ± {self.percentiles['std']:.2f}")
        
        return self.percentiles
    
    def clasificar_dias(self, metrica='rango_diario'):
        """
        Clasifica días en FUERTE, INTERMEDIO, LATERAL usando percentiles
        
        Args:
            metrica: métrica para clasificar
            
        Returns:
            DataFrame con clasificaciones
        """
        if self.stats_diarias is None:
            self.calcular_estadisticas_diarias()
        
        if self.percentiles is None:
            self.calcular_percentiles(metrica)
        
        # Función de clasificación
        def clasificar(valor):
            if valor >= self.percentiles['p67']:
                return 'FUERTE'
            elif valor >= self.percentiles['p33']:
                return 'INTERMEDIO'
            else:
                return 'LATERAL'
        
        # Aplicar clasificación
        self.stats_diarias['clasificacion'] = self.stats_diarias[metrica].apply(clasificar)
        
        # Asegurar que dia_semana esté en las clasificaciones (para visualizaciones)
        if 'dia_semana' not in self.stats_diarias.columns:
            self.stats_diarias['dia_semana'] = pd.to_datetime(self.stats_diarias.index).day_name()
        
        # Detectar outliers (días extremos)
        umbral_outlier = self.percentiles['mean'] + (2 * self.percentiles['std'])
        self.stats_diarias['es_outlier'] = self.stats_diarias[metrica] > umbral_outlier
        
        # Guardar clasificaciones
        self.clasificaciones = self.stats_diarias.copy()
        
        print(f"\n✓ Días clasificados según {metrica}")
        return self.clasificaciones
    
    def analizar_por_dia_semana(self):
        """
        Analiza distribución de clasificaciones por día de semana
        
        Returns:
            DataFrame con análisis por día de semana
        """
        if self.clasificaciones is None:
            self.clasificar_dias()
        
        # Pivot table: día_semana vs clasificación
        analisis = pd.crosstab(
            self.clasificaciones['dia_semana'],
            self.clasificaciones['clasificacion']
        )
        
        # Ordenar días de la semana correctamente
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        analisis = analisis.reindex(orden_dias, fill_value=0)
        
        # Calcular totales y porcentajes
        analisis['TOTAL'] = analisis.sum(axis=1)
        
        # Agregar porcentaje de días fuertes por día de semana
        analisis['%_FUERTE'] = (analisis['FUERTE'] / analisis['TOTAL'] * 100).round(1)
        analisis['%_LATERAL'] = (analisis['LATERAL'] / analisis['TOTAL'] * 100).round(1)
        
        return analisis
    
    def detectar_rachas(self):
        """
        Detecta rachas consecutivas (ej: 3 días fuertes seguidos)
        
        Returns:
            DataFrame con rachas detectadas
        """
        if self.clasificaciones is None:
            self.clasificar_dias()
        
        # Ordenar por fecha y resetear índice para trabajar con fecha como columna
        df_sorted = self.clasificaciones.sort_index().reset_index()
        
        # Detectar cambios en clasificación
        df_sorted['cambio_clase'] = df_sorted['clasificacion'] != df_sorted['clasificacion'].shift(1)
        df_sorted['grupo_racha'] = df_sorted['cambio_clase'].cumsum()
        
        # Agrupar rachas
        rachas = df_sorted.groupby('grupo_racha').agg({
            'clasificacion': 'first',
            'fecha': ['first', 'last', 'count']
        })
        
        rachas.columns = ['tipo', 'fecha_inicio', 'fecha_fin', 'duracion']
        
        # Filtrar rachas significativas (3+ días)
        rachas_significativas = rachas[rachas['duracion'] >= 3].copy()
        
        return rachas_significativas
    
    def analizar_sesiones_por_tipo_dia(self):
        """
        Analiza qué sesión es más fuerte según el tipo de día
        
        Returns:
            DataFrame con promedios de rango por sesión y tipo de día
        """
        if self.clasificaciones is None:
            self.clasificar_dias()
        
        # Merge con datos originales para tener sesiones
        df_con_clase = self.df.merge(
            self.clasificaciones[['clasificacion']], 
            left_on='fecha', 
            right_index=True,
            how='left'
        )
        
        # Calcular rango promedio por sesión y clasificación
        analisis = df_con_clase.groupby(['clasificacion', 'sesion'])['rango'].agg([
            'mean', 'sum', 'count'
        ]).round(2)
        
        analisis.columns = ['rango_promedio', 'rango_total', 'num_velas']
        
        return analisis
    
    def generar_reporte_completo(self):
        """
        Genera reporte completo de clasificación
        
        Returns:
            str: reporte formateado
        """
        if self.clasificaciones is None:
            self.clasificar_dias()
        
        reporte = []
        reporte.append("=" * 70)
        reporte.append("REPORTE DE CLASIFICACIÓN DE DÍAS")
        reporte.append("=" * 70)
        reporte.append("")
        
        # 1. Resumen general
        total_dias = len(self.clasificaciones)
        conteo = self.clasificaciones['clasificacion'].value_counts()
        
        reporte.append("RESUMEN GENERAL")
        reporte.append("-" * 70)
        reporte.append(f"Total de días analizados: {total_dias}")
        reporte.append("")
        reporte.append("Distribución:")
        for clase in ['FUERTE', 'INTERMEDIO', 'LATERAL']:
            count = conteo.get(clase, 0)
            pct = (count / total_dias * 100)
            reporte.append(f"  {clase:12} : {count:2} días ({pct:5.1f}%)")
        
        # Outliers
        num_outliers = self.clasificaciones['es_outlier'].sum()
        if num_outliers > 0:
            reporte.append(f"\n  Días outliers (extremos): {num_outliers}")
        
        reporte.append("")
        
        # 2. Análisis por día de semana
        reporte.append("ANÁLISIS POR DÍA DE SEMANA")
        reporte.append("-" * 70)
        analisis_semana = self.analizar_por_dia_semana()
        
        dias_esp = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes'}
        
        for dia_en, dia_es in dias_esp.items():
            if dia_en in analisis_semana.index:
                row = analisis_semana.loc[dia_en]
                f = row.get('FUERTE', 0)
                i = row.get('INTERMEDIO', 0)
                l = row.get('LATERAL', 0)
                total = row['TOTAL']
                pct_f = row['%_FUERTE']
                
                reporte.append(f"{dia_es:10} | F:{f:2} I:{i:2} L:{l:2} | Total:{total:2} | Fuertes:{pct_f:4.1f}%")
        
        reporte.append("")
        
        # 3. Top 5 días más fuertes
        reporte.append("TOP 5 DÍAS MÁS FUERTES")
        reporte.append("-" * 70)
        top5 = self.clasificaciones.nlargest(5, 'rango_diario')
        
        for idx, row in top5.iterrows():
            fecha = idx
            rango = row['rango_diario']
            direccion = row['direccion']
            cambio = row['cambio_pct']
            reporte.append(f"{fecha} | Rango: {rango:7.2f} | {direccion:8} ({cambio:+.2f}%)")
        
        reporte.append("")
        
        # 4. Rachas significativas
        rachas = self.detectar_rachas()
        if len(rachas) > 0:
            reporte.append("RACHAS SIGNIFICATIVAS (3+ días consecutivos)")
            reporte.append("-" * 70)
            for idx, row in rachas.iterrows():
                tipo = row['tipo']
                duracion = row['duracion']
                inicio = row['fecha_inicio']
                fin = row['fecha_fin']
                reporte.append(f"{tipo:12} : {duracion} días ({inicio} → {fin})")
            reporte.append("")
        
        # 5. Estadísticas de rangos diarios
        reporte.append("ESTADÍSTICAS DE RANGOS DIARIOS")
        reporte.append("-" * 70)
        reporte.append(f"Rango promedio: {self.percentiles['mean']:.2f} puntos")
        reporte.append(f"Rango mediano:  {self.percentiles['p50']:.2f} puntos")
        reporte.append(f"Desv. estándar: {self.percentiles['std']:.2f} puntos")
        reporte.append(f"Rango mínimo:   {self.percentiles['min']:.2f} puntos")
        reporte.append(f"Rango máximo:   {self.percentiles['max']:.2f} puntos")
        
        reporte.append("")
        reporte.append("=" * 70)
        
        return "\n".join(reporte)
    
    def exportar_clasificaciones(self, nombre_archivo="clasificaciones.txt"):
        """
        Exporta clasificaciones a TXT con formato tabular
        
        Args:
            nombre_archivo: nombre del archivo de salida
        """
        if self.clasificaciones is None:
            self.clasificar_dias()
        
        from config import OUTPUTS_DIR
        ruta = OUTPUTS_DIR / nombre_archivo
        
        # Preparar datos para exportar
        export_df = self.clasificaciones[[
            'dia_semana', 'clasificacion', 'rango_diario', 
            'cambio_diario', 'cambio_pct', 'direccion',
            'volatilidad', 'volume', 'es_outlier'
        ]].copy()
        
        # Exportar como texto formateado
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("CLASIFICACIONES DIARIAS - EXPORTACIÓN COMPLETA\n")
            f.write("=" * 100 + "\n\n")
            
            # Escribir datos tabulares
            f.write(export_df.to_string())
            f.write("\n\n" + "=" * 100 + "\n")
        
        print(f"✓ Clasificaciones exportadas a: {ruta}")
        
        # También guardar versión CSV por si acaso
        ruta_csv = OUTPUTS_DIR / nombre_archivo.replace('.txt', '.csv')
        export_df.to_csv(ruta_csv, index=True)
        print(f"✓ Versión CSV guardada en: {ruta_csv}")


# ==============================================
# FUNCIONES HELPER
# ==============================================

def analizar_archivo(archivo_parquet, mostrar_reporte=True, exportar=True):
    """
    Función helper para análisis rápido de un archivo
    
    Args:
        archivo_parquet: ruta al archivo procesado
        mostrar_reporte: si mostrar reporte en consola
        exportar: si exportar resultados a CSV
        
    Returns:
        DayClassifier con análisis completo
    """
    from src.ingestion import cargar_datos_procesados
    
    # Cargar datos
    df = cargar_datos_procesados(archivo_parquet)
    if df is None:
        return None
    
    # Crear clasificador
    classifier = DayClassifier(df)
    
    # Ejecutar análisis
    classifier.calcular_estadisticas_diarias()
    classifier.calcular_percentiles()
    classifier.clasificar_dias()
    
    # Mostrar reporte
    if mostrar_reporte:
        print("\n" + classifier.generar_reporte_completo())
    
    # Exportar
    if exportar:
        classifier.exportar_clasificaciones()
    
    return classifier


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el clasificador
    """
    # Analizar archivo procesado
    classifier = analizar_archivo(
        "MNQ 03-26.Last_processed.parquet",
        mostrar_reporte=True,
        exportar=True
    )
    
    if classifier:
        print("\n✓ Análisis de clasificación completado")
        
        # Análisis adicional de sesiones
        print("\n" + "="*70)
        print("ANÁLISIS DE SESIONES POR TIPO DE DÍA")
        print("="*70)
        sesiones = classifier.analizar_sesiones_por_tipo_dia()
        print(sesiones)