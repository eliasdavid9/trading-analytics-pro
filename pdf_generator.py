"""
Módulo generador de PDF profesional
Crea reportes completos en formato PDF con diseño profesional
"""

import io
from pathlib import Path
from datetime import datetime
import sys

# Importar ReportLab
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, Frame, PageTemplate
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠ ReportLab no está instalado. Ejecutá: pip install reportlab")

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import OUTPUTS_DIR


class PDFGenerator:
    """
    Generador de reportes PDF profesionales
    """
    
    def __init__(self, clasificaciones, analytics, predictor, visualizer, nombre_contrato):
        """
        Inicializa el generador de PDF
        
        Args:
            clasificaciones: DataFrame con clasificaciones de días
            analytics: SessionAnalytics con análisis de sesiones
            predictor: TradingPredictor con reglas probabilísticas
            visualizer: TradingVisualizer con gráficos
            nombre_contrato: nombre del contrato analizado
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab no está disponible")
        
        self.clasificaciones = clasificaciones
        self.analytics = analytics
        self.predictor = predictor
        self.visualizer = visualizer
        self.nombre_contrato = nombre_contrato
        self.elementos = []
        self.estilos = getSampleStyleSheet()
        
        # Crear estilos personalizados
        self._crear_estilos()
    
    def _crear_estilos(self):
        """Crea estilos personalizados para el PDF"""
        
        # Título principal
        self.estilos.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.estilos['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.estilos.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.estilos['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#374151'),
            spaceAfter=20,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=2,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=5
        ))
        
        # Sección
        self.estilos.add(ParagraphStyle(
            name='Seccion',
            parent=self.estilos['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        self.estilos.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.estilos['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Insight (destacado)
        self.estilos.add(ParagraphStyle(
            name='Insight',
            parent=self.estilos['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#059669'),
            spaceAfter=8,
            fontName='Helvetica-Bold',
            leftIndent=20,
            bulletIndent=10
        ))
    
    def _agregar_portada(self):
        """Crea la portada del reporte"""
        
        # Espaciado superior
        self.elementos.append(Spacer(1, 2*inch))
        
        # Título principal
        titulo = Paragraph(
            f"REPORTE DE ANÁLISIS<br/>DE TRADING",
            self.estilos['TituloPrincipal']
        )
        self.elementos.append(titulo)
        self.elementos.append(Spacer(1, 0.3*inch))
        
        # Contrato
        contrato = Paragraph(
            f"<b>Contrato:</b> {self.nombre_contrato}",
            ParagraphStyle(
                'ContratoStyle',
                parent=self.estilos['Normal'],
                fontSize=16,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#667eea')
            )
        )
        self.elementos.append(contrato)
        self.elementos.append(Spacer(1, 1*inch))
        
        # Info del reporte
        fecha_generacion = datetime.now().strftime('%d de %B de %Y - %H:%M')
        meses_es = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
            'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
            'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
            'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        for en, es in meses_es.items():
            fecha_generacion = fecha_generacion.replace(en, es)
        
        info_data = [
            ['<b>Fecha de Generación:</b>', fecha_generacion],
            ['<b>Total de Días Analizados:</b>', str(len(self.clasificaciones))],
            ['<b>Rango de Fechas:</b>', f"{self.clasificaciones.index.min()} → {self.clasificaciones.index.max()}"],
            ['<b>Sistema:</b>', 'Trading Analytics Pro v1.0']
        ]
        
        info_tabla = Table(info_data, colWidths=[2.5*inch, 3*inch])
        info_tabla.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.elementos.append(info_tabla)
        self.elementos.append(Spacer(1, 1.5*inch))
        
        # Disclaimer
        disclaimer = Paragraph(
            "<i>Este reporte contiene análisis estadístico de datos históricos. "
            "No constituye asesoramiento financiero. El trading de futuros conlleva riesgos.</i>",
            ParagraphStyle(
                'Disclaimer',
                parent=self.estilos['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#6b7280'),
                leftIndent=1*inch,
                rightIndent=1*inch
            )
        )
        self.elementos.append(disclaimer)
        
        # Page break
        self.elementos.append(PageBreak())
    
    def _agregar_resumen_ejecutivo(self):
        """Agrega sección de resumen ejecutivo"""
        
        self.elementos.append(Paragraph("RESUMEN EJECUTIVO", self.estilos['Subtitulo']))
        self.elementos.append(Spacer(1, 0.2*inch))
        
        # Métricas principales
        total_dias = len(self.clasificaciones)
        dias_fuertes = (self.clasificaciones['clasificacion'] == 'FUERTE').sum()
        dias_intermedios = (self.clasificaciones['clasificacion'] == 'INTERMEDIO').sum()
        dias_laterales = (self.clasificaciones['clasificacion'] == 'LATERAL').sum()
        outliers = self.clasificaciones['es_outlier'].sum()
        rango_promedio = self.clasificaciones['rango_diario'].mean()
        rango_max = self.clasificaciones['rango_diario'].max()
        
        metricas_data = [
            ['<b>Métrica</b>', '<b>Valor</b>', '<b>Porcentaje</b>'],
            ['Total de Días', str(total_dias), '100%'],
            ['Días Fuertes', str(dias_fuertes), f"{(dias_fuertes/total_dias*100):.1f}%"],
            ['Días Intermedios', str(dias_intermedios), f"{(dias_intermedios/total_dias*100):.1f}%"],
            ['Días Laterales', str(dias_laterales), f"{(dias_laterales/total_dias*100):.1f}%"],
            ['Días Outliers', str(outliers), f"{(outliers/total_dias*100):.1f}%"],
            ['Rango Promedio', f"{rango_promedio:.1f} pts", '-'],
            ['Rango Máximo', f"{rango_max:.1f} pts", '-'],
        ]
        
        metricas_tabla = Table(metricas_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        metricas_tabla.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.elementos.append(metricas_tabla)
        self.elementos.append(Spacer(1, 0.3*inch))
        
        # Insights clave
        self.elementos.append(Paragraph("Insights Clave", self.estilos['Seccion']))
        
        # Mejor día
        import pandas as pd
        analisis_semana = pd.crosstab(
            self.clasificaciones['dia_semana'],
            self.clasificaciones['clasificacion'],
            normalize='index'
        ) * 100
        
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        analisis_semana = analisis_semana.reindex(orden_dias, fill_value=0)
        
        if 'FUERTE' in analisis_semana.columns:
            mejor_dia = analisis_semana['FUERTE'].idxmax()
            mejor_pct = analisis_semana.loc[mejor_dia, 'FUERTE']
            
            dias_esp = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes'
            }
            mejor_dia_esp = dias_esp.get(mejor_dia, mejor_dia)
            
            self.elementos.append(Paragraph(
                f"• <b>Mejor día para trading:</b> {mejor_dia_esp} ({mejor_pct:.1f}% días fuertes)",
                self.estilos['Insight']
            ))
        
        # Sesión dominante
        dominantes = self.analytics.identificar_sesion_dominante()
        sesion_top = dominantes['sesion_dominante'].value_counts().idxmax()
        sesion_pct = (dominantes['sesion_dominante'].value_counts()[sesion_top] / len(dominantes) * 100)
        
        self.elementos.append(Paragraph(
            f"• <b>Sesión más dominante:</b> {sesion_top} ({sesion_pct:.1f}% de los días)",
            self.estilos['Insight']
        ))
        
        # Correlación más fuerte
        if self.analytics.correlaciones:
            max_corr = max(self.analytics.correlaciones.items(), key=lambda x: abs(x[1]))
            self.elementos.append(Paragraph(
                f"• <b>Correlación más fuerte:</b> {max_corr[0]} = {max_corr[1]:+.3f}",
                self.estilos['Insight']
            ))
        
        if outliers > 0:
            self.elementos.append(Paragraph(
                f"• <b>Días con volatilidad extrema:</b> {outliers} outliers detectados",
                self.estilos['Insight']
            ))
        
        self.elementos.append(PageBreak())
    
    def _agregar_clasificacion(self):
        """Agrega sección de clasificación de días"""
        
        self.elementos.append(Paragraph("CLASIFICACIÓN DE DÍAS", self.estilos['Subtitulo']))
        self.elementos.append(Spacer(1, 0.1*inch))
        
        # Explicación
        explicacion = Paragraph(
            "Los días se clasifican según su rango diario usando percentiles adaptativos. "
            "Esta metodología se ajusta automáticamente al instrumento y período analizado.",
            self.estilos['TextoNormal']
        )
        self.elementos.append(explicacion)
        self.elementos.append(Spacer(1, 0.15*inch))
        
        # Criterios
        self.elementos.append(Paragraph("Criterios de Clasificación", self.estilos['Seccion']))
        
        p33 = self.clasificaciones['rango_diario'].quantile(0.33)
        p67 = self.clasificaciones['rango_diario'].quantile(0.67)
        
        criterios = [
            f"• <b>FUERTE:</b> Rango ≥ {p67:.1f} puntos (top 33%)",
            f"• <b>INTERMEDIO:</b> Rango entre {p33:.1f} y {p67:.1f} puntos (medio 33%)",
            f"• <b>LATERAL:</b> Rango < {p33:.1f} puntos (bottom 33%)"
        ]
        
        for criterio in criterios:
            self.elementos.append(Paragraph(criterio, self.estilos['TextoNormal']))
        
        self.elementos.append(Spacer(1, 0.2*inch))
        
        # Top 5 días más fuertes
        self.elementos.append(Paragraph("Top 5 Días Más Fuertes", self.estilos['Seccion']))
        
        top5 = self.clasificaciones.nlargest(5, 'rango_diario')
        
        top5_data = [['<b>Fecha</b>', '<b>Rango</b>', '<b>Cambio %</b>', '<b>Dirección</b>']]
        for fecha, row in top5.iterrows():
            top5_data.append([
                str(fecha),
                f"{row['rango_diario']:.1f} pts",
                f"{row['cambio_pct']:+.2f}%",
                row['direccion']
            ])
        
        top5_tabla = Table(top5_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        top5_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        self.elementos.append(top5_tabla)
        self.elementos.append(PageBreak())
    
    def _agregar_graficos(self):
        """Agrega gráficos al PDF"""
        
        self.elementos.append(Paragraph("VISUALIZACIONES", self.estilos['Subtitulo']))
        self.elementos.append(Spacer(1, 0.2*inch))
        
        # Crear gráficos y exportar como imágenes
        import tempfile
        
        try:
            # Heatmap
            self.elementos.append(Paragraph("Volatilidad por Día y Sesión", self.estilos['Seccion']))
            fig1 = self.visualizer.crear_heatmap_semana_sesion()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig1.write_image(tmp.name, width=700, height=400)
                img1 = Image(tmp.name, width=6*inch, height=3.5*inch)
                self.elementos.append(img1)
            
            self.elementos.append(Spacer(1, 0.3*inch))
            
            # Distribución
            self.elementos.append(Paragraph("Distribución de Rangos Diarios", self.estilos['Seccion']))
            fig2 = self.visualizer.crear_distribucion_rangos()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig2.write_image(tmp.name, width=700, height=400)
                img2 = Image(tmp.name, width=6*inch, height=3.5*inch)
                self.elementos.append(img2)
            
            self.elementos.append(PageBreak())
            
            # Timeline
            self.elementos.append(Paragraph("Timeline de Clasificaciones", self.estilos['Seccion']))
            fig3 = self.visualizer.crear_timeline_clasificaciones()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig3.write_image(tmp.name, width=700, height=400)
                img3 = Image(tmp.name, width=6*inch, height=3.5*inch)
                self.elementos.append(img3)
            
        except Exception as e:
            # Si falla la exportación de imágenes (falta kaleido)
            self.elementos.append(Paragraph(
                f"⚠ No se pudieron exportar gráficos: {str(e)}",
                self.estilos['TextoNormal']
            ))
            self.elementos.append(Paragraph(
                "Tip: Instalá kaleido para exportar gráficos: pip install kaleido",
                self.estilos['TextoNormal']
            ))
        
        self.elementos.append(PageBreak())
    
    def _agregar_predictor(self):
        """Agrega sección de predicciones"""
        
        self.elementos.append(Paragraph("REGLAS PROBABILÍSTICAS", self.estilos['Subtitulo']))
        self.elementos.append(Spacer(1, 0.2*inch))
        
        if self.predictor.reglas_probabilisticas:
            for i, regla in enumerate(self.predictor.reglas_probabilisticas[:10], 1):  # Max 10 reglas
                # Título de la regla
                self.elementos.append(Paragraph(
                    f"{i}. {regla['tipo']}: {regla['condicion']}",
                    self.estilos['Seccion']
                ))
                
                # Detalles
                detalles = [
                    f"<b>Predicción:</b> {regla['prediccion']}",
                    f"<b>Probabilidad:</b> {regla['probabilidad']:.1f}% (Confianza: {regla['confianza']})",
                    f"<b>Táctica:</b> {regla['tactica']}"
                ]
                
                for detalle in detalles:
                    self.elementos.append(Paragraph(detalle, self.estilos['TextoNormal']))
                
                self.elementos.append(Spacer(1, 0.15*inch))
        
        else:
            self.elementos.append(Paragraph(
                "No se generaron reglas probabilísticas suficientes.",
                self.estilos['TextoNormal']
            ))
    
    def generar_pdf(self, nombre_archivo=None):
        """
        Genera el PDF completo
        
        Args:
            nombre_archivo: nombre del archivo PDF (sin extensión)
            
        Returns:
            str: ruta del archivo generado
        """
        if nombre_archivo is None:
            nombre_archivo = f"reporte_{self.nombre_contrato.replace(' ', '_')}"
        
        ruta_pdf = OUTPUTS_DIR / f"{nombre_archivo}.pdf"
        
        # Crear documento
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Construir contenido
        print("\n" + "="*70)
        print("GENERANDO PDF PROFESIONAL")
        print("="*70)
        
        print("  • Creando portada...")
        self._agregar_portada()
        
        print("  • Generando resumen ejecutivo...")
        self._agregar_resumen_ejecutivo()
        
        print("  • Agregando clasificación de días...")
        self._agregar_clasificacion()
        
        print("  • Exportando gráficos...")
        self._agregar_graficos()
        
        print("  • Incluyendo reglas probabilísticas...")
        self._agregar_predictor()
        
        # Construir PDF
        doc.build(self.elementos)
        
        print(f"\n✓ PDF generado: {ruta_pdf}")
        return str(ruta_pdf)


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def generar_pdf_completo(clasificaciones, analytics, predictor, visualizer, nombre_contrato):
    """
    Genera PDF completo con todos los análisis
    
    Args:
        clasificaciones: DataFrame con clasificaciones
        analytics: SessionAnalytics
        predictor: TradingPredictor
        visualizer: TradingVisualizer
        nombre_contrato: nombre del contrato
        
    Returns:
        str: ruta del PDF generado
    """
    generator = PDFGenerator(clasificaciones, analytics, predictor, visualizer, nombre_contrato)
    return generator.generar_pdf()


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el generador
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    from src.analytics import SessionAnalytics
    from src.predictor import TradingPredictor
    from src.visualizer import TradingVisualizer
    
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
        analytics.detectar_correlacion_sesiones()
        
        # Predictor
        predictor = TradingPredictor(df, classifier.clasificaciones, analytics.stats_sesiones)
        predictor.analizar_patrones_dia_semana()
        predictor.analizar_patron_sesion_previa()
        predictor.analizar_rachas()
        predictor.generar_reglas_probabilisticas()
        
        # Visualizer
        visualizer = TradingVisualizer(df, classifier.clasificaciones, analytics.stats_sesiones, "MNQ 03-26")
        
        # Generar PDF
        pdf_path = generar_pdf_completo(
            classifier.clasificaciones,
            analytics,
            predictor,
            visualizer,
            "MNQ 03-26"
        )
        
        print(f"\n✓ PDF disponible en: {pdf_path}")
