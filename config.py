"""
Configuración centralizada del sistema de análisis de trading
"""

from pathlib import Path
from datetime import datetime
import pytz

# ==============================================
# RUTAS DEL PROYECTO
# ==============================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SRC_DIR = BASE_DIR / "src"
OUTPUTS_DIR = BASE_DIR / "outputs"

# ==============================================
# CONFIGURACIÓN DE ZONA HORARIA
# ==============================================
# Zona horaria en la que están los datos exportados de NinjaTrader
# Opciones comunes:
# - "America/Argentina/Buenos_Aires" (UTC-3)
# - "America/New_York" (ET - Eastern Time)
# - "UTC" (Hora universal)
# - "Europe/London", "Asia/Tokyo", etc.
ZONA_HORARIA_DATOS = "America/Argentina/Buenos_Aires"

# Zona horaria de referencia para clasificación de sesiones (siempre NY)
ZONA_HORARIA_REFERENCIA = "America/New_York"

# ==============================================
# DETECCIÓN AUTOMÁTICA DE DST (Daylight Saving Time)
# ==============================================

def _es_dst_usa(fecha):
    """
    Determina si una fecha está en horario de verano (DST) de EEUU
    
    Args:
        fecha: datetime object
        
    Returns:
        bool: True si está en DST, False si no
    
    Reglas DST de EEUU:
    - Comienza: Segundo domingo de Marzo a las 2:00 AM
    - Termina: Primer domingo de Noviembre a las 2:00 AM
    """
    año = fecha.year
    mes = fecha.month
    dia = fecha.day
    
    # Fuera de la ventana posible de DST
    if mes < 3 or mes > 11:
        return False
    if mes > 3 and mes < 11:
        return True
    
    # Calcular segundo domingo de Marzo
    primer_dia_marzo = datetime(año, 3, 1)
    dias_hasta_domingo = (6 - primer_dia_marzo.weekday()) % 7
    primer_domingo_marzo = 1 + dias_hasta_domingo
    segundo_domingo_marzo = primer_domingo_marzo + 7
    
    # Calcular primer domingo de Noviembre
    primer_dia_nov = datetime(año, 11, 1)
    dias_hasta_domingo_nov = (6 - primer_dia_nov.weekday()) % 7
    primer_domingo_nov = 1 + dias_hasta_domingo_nov
    
    # Determinar si estamos en DST
    if mes == 3:
        return dia >= segundo_domingo_marzo
    elif mes == 11:
        return dia < primer_domingo_nov
    
    return True  # Abril-Octubre

def obtener_horarios_sesion_et(fecha=None):
    """
    Obtiene los horarios de sesión en hora de Nueva York (ET)
    
    Args:
        fecha: datetime object (default: fecha actual)
        
    Returns:
        dict: horarios de sesión en ET
    """
    if fecha is None:
        fecha = datetime.now()
    
    # Horarios de sesiones de futuros en hora de Nueva York (ET)
    # Estos son los horarios REALES del mercado
    horarios = {
        "ASIA": {
            "inicio": "19:00",  # 7:00 PM ET
            "fin": "04:00",     # 4:00 AM ET (día siguiente)
            "descripcion": "Sesión asiática (Sydney, Tokyo, Hong Kong)"
        },
        "EUROPA": {
            "inicio": "03:00",  # 3:00 AM ET
            "fin": "12:00",     # 12:00 PM ET
            "descripcion": "Sesión europea (Frankfurt, London)"
        },
        "NY": {
            "inicio": "09:30",  # 9:30 AM ET (apertura de bolsa)
            "fin": "17:00",     # 5:00 PM ET (cierre de bolsa)
            "descripcion": "Sesión americana (New York)"
        }
    }
    
    return horarios

# ==============================================
# PARÁMETROS DE SESIONES (horarios en ET - hora de Nueva York)
# ==============================================
# IMPORTANTE: Estos horarios se ajustan automáticamente según DST
# La función obtener_horarios_sesion_et() se usa en ingestion.py
SESIONES = obtener_horarios_sesion_et()

# ==============================================
# CLASIFICACIÓN DE DÍAS
# ==============================================
# Percentiles para clasificar la fuerza del día
CLASIFICACION = {
    "FUERTE": {
        "percentil_min": 66.67,  # Top 33% de días
        "descripcion": "Día con movimiento significativo"
    },
    "INTERMEDIO": {
        "percentil_min": 33.33,
        "percentil_max": 66.67,  # Medio 33%
        "descripcion": "Día con movimiento moderado"
    },
    "LATERAL": {
        "percentil_max": 33.33,  # Bottom 33%
        "descripcion": "Día con poco movimiento"
    }
}

# Métrica para clasificar días (opciones: 'rango_diario', 'volatilidad', 'atr')
METRICA_CLASIFICACION = 'rango_diario'

# ==============================================
# PARÁMETROS DE ANÁLISIS
# ==============================================
# Ventana para cálculos de volatilidad/ATR
VENTANA_ATR = 14

# Mínimo de días requeridos para generar estadísticas confiables
MIN_DIAS_ANALISIS = 20

# ==============================================
# FORMATO DE DATOS
# ==============================================
# Formato de entrada esperado en archivos raw
FORMATO_ENTRADA = {
    "separador": ";",
    "columnas": ["datetime", "open", "high", "low", "close", "volume"],
    "formato_fecha": "%Y%m%d %H%M%S"
}

# Decimales para redondeo en reportes
DECIMALES_PRECIO = 2
DECIMALES_PORCENTAJE = 2

# ==============================================
# VALIDACIONES
# ==============================================
# Verificaciones de integridad de datos
VALIDACIONES = {
    "precio_min": 1000,      # Precio mínimo razonable para MNQ
    "precio_max": 50000,     # Precio máximo razonable para MNQ
    "volumen_min": 0,        # Volumen mínimo aceptable
    "check_high_low": True,  # Verificar que High >= Low
    "check_ohlc": True       # Verificar que High/Low contengan Open/Close
}

# ==============================================
# REPORTES
# ==============================================
REPORTES = {
    "incluir_fecha_generacion": True,
    "incluir_metadata": True,
    "formato_salida": "txt"  # Opciones: txt, csv, json
}
