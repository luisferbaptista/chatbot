import os
import signal
import asyncio
import json
import tempfile
import shutil
import io
from typing import Optional, Dict, List
from datetime import datetime

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
import httpx  # pyright: ignore[reportMissingImports]
from google.oauth2 import service_account  # pyright: ignore[reportMissingImports]
from google.auth.transport.requests import Request as GoogleRequest  # pyright: ignore[reportMissingImports]

# Sistema de gestión de perfiles
try:
    from profile_manager import ProfileManager
    PROFILES_AVAILABLE = True
except ImportError:
    print("Profile management not available")
    PROFILES_AVAILABLE = False

# procesamiento de voz
try:
    import whisper
    from pydub import AudioSegment
    from gtts import gTTS
    VOICE_AVAILABLE = True
except ImportError as e:
    print(f"Voice processing not available: {e}")
    VOICE_AVAILABLE = False

# procesamiento de excel y graficos
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.io import to_image
    import io
    import base64
    EXCEL_CHARTS_AVAILABLE = True
except ImportError as e:
    print(f"Excel and chart processing not available: {e}")
    EXCEL_CHARTS_AVAILABLE = False

import requests

# cargar .env early so environment variables are available
try:
    load_dotenv()
except Exception:
    # ignorar errores de carga de .env; usar variables de entorno directamente
    pass
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# leer token desde entorno para seguridad. Puedes establecer TELEGRAM_BOT_TOKEN en tu shell
# or use a .env file during development.
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    # fallback: mantener token hard-coded como último recurso (no recomendado)
    TOKEN = "8035861851:AAFim2hjCQr0Mk56RwNoTpkeVhiONTnHPGA"

# almacenamiento de memoria para conversaciones
CONVERSATION_MEMORY: Dict[int, List[Dict]] = {}
MEMORY_FILE = "conversation_memory.json"
MAX_MEMORY_ENTRIES = 20  # máximo de turnos de conversación para mantener por chat

# gestión de perfiles del bot
if PROFILES_AVAILABLE:
    PROFILE_MANAGER = ProfileManager()
else:
    PROFILE_MANAGER = None

# configuración de procesamiento de voz
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
AUDIO_RESPONSE_ENABLED = os.getenv("AUDIO_RESPONSE_ENABLED", "true").lower() == "true"
WHISPER_MODEL = None  # se cargará en el primer uso


def load_memory():
    """Load conversation memory from file"""
    global CONVERSATION_MEMORY
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                CONVERSATION_MEMORY = json.load(f)
    except Exception as e:
        print(f"Error loading memory: {e}")
        CONVERSATION_MEMORY = {}

def save_memory():
    """Save conversation memory to file"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(CONVERSATION_MEMORY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def get_chat_memory(chat_id: int) -> List[Dict]:
    """Get conversation history for a chat"""
    return CONVERSATION_MEMORY.get(chat_id, [])

def add_to_memory(chat_id: int, role: str, content: str):
    """Add a message to conversation memory"""
    if chat_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[chat_id] = []
    
    CONVERSATION_MEMORY[chat_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # mantener solo el último MAX_MEMORY_ENTRIES
    if len(CONVERSATION_MEMORY[chat_id]) > MAX_MEMORY_ENTRIES:
        CONVERSATION_MEMORY[chat_id] = CONVERSATION_MEMORY[chat_id][-MAX_MEMORY_ENTRIES:]
    
    save_memory()

def clear_memory(chat_id: int):
    """Clear conversation memory for a chat"""
    if chat_id in CONVERSATION_MEMORY:
        del CONVERSATION_MEMORY[chat_id]
        save_memory()

def load_whisper_model():
    """Load Whisper model on first use"""
    global WHISPER_MODEL
    if not VOICE_AVAILABLE:
        raise Exception("Voice processing not available")
    if WHISPER_MODEL is None:
        print(f"Loading Whisper model: {WHISPER_MODEL_NAME}")
        WHISPER_MODEL = whisper.load_model(WHISPER_MODEL_NAME)
        print("Whisper model loaded successfully")
    return WHISPER_MODEL

async def download_voice_file(file_id: str, file_path: str, bot_token: str):
    """Download voice file from Telegram"""
    try:
        # Get file info from Telegram
        file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        response = requests.get(file_info_url)
        file_info = response.json()
        
        if not file_info.get("ok"):
            raise Exception(f"Failed to get file info: {file_info}")
        
        # Download the file
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info['result']['file_path']}"
        file_response = requests.get(file_url)
        
        with open(file_path, 'wb') as f:
            f.write(file_response.content)
        
        return True
    except Exception as e:
        print(f"Error downloading voice file: {e}")
        return False

def convert_audio_format(input_path: str, output_path: str):
    """Convert OGG to WAV using FFmpeg directly"""
    if not VOICE_AVAILABLE:
        raise Exception("Voice processing not available")
    try:
        # intentar con pydub primero
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Pydub conversion failed: {e}")
        # fallback: usar FFmpeg directamente
        try:
            import subprocess
            import os
            
            # buscar FFmpeg en el directorio del proyecto
            ffmpeg_path = None
            for root, dirs, files in os.walk("."):
                if "ffmpeg.exe" in files:
                    ffmpeg_path = os.path.join(root, "ffmpeg.exe")
                    break
            
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                # usar FFmpeg para convertir
                cmd = [ffmpeg_path, "-i", input_path, "-acodec", "pcm_s16le", "-ar", "16000", output_path, "-y"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                else:
                    print(f"FFmpeg conversion failed: {result.stderr}")
            
            # último recurso: copiar archivo directamente
            import shutil
            shutil.copy2(input_path, output_path)
            return True
            
        except Exception as e2:
            print(f"All conversion methods failed: {e2}")
            return False

def transcribe_audio(audio_path: str, language_hint: str = None):
    """Transcribe audio using multiple methods"""
    if not VOICE_AVAILABLE:
        raise Exception("Voice processing not available")
    
    # intentar con Whisper primero si está disponible
    try:
        model = load_whisper_model()
        
        # transcribir con detección de idioma
        result = model.transcribe(audio_path, language=language_hint)
        
        text = result["text"].strip()
        detected_language = result.get("language", "unknown")
        
        return text, detected_language
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        
        # fallback: intentar con Google Speech Recognition
        try:
            import speech_recognition as sr
            
            r = sr.Recognizer()
            
            # determinar idioma para Google Speech Recognition
            if language_hint:
                if language_hint.startswith('es'):
                    lang = 'es-ES'
                elif language_hint.startswith('en'):
                    lang = 'en-US'
                else:
                    lang = 'es-ES'  # por defecto a español
            else:
                lang = 'es-ES'  # por defecto a español
            
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            
            text = r.recognize_google(audio, language=lang)
            detected_language = lang
            
            return text, detected_language
            
        except Exception as e2:
            print(f"Google Speech Recognition also failed: {e2}")
            
            # último recurso: devolver un mensaje de placeholder
            return "No pude transcribir el audio. Por favor, intenta enviar un mensaje de texto.", "es"

# funciones de procesamiento de excel y graficos
def read_excel_file(file_source):
    """
    Read Excel file and return dataframes and sheet info with robust error handling
    Args:
        file_source: Can be a file path (str) or BytesIO object
    """
    if not EXCEL_CHARTS_AVAILABLE:
        raise Exception("Excel processing not available")
    
    try:
        # múltiples intentos con diferentes motores y parámetros
        engines_to_try = ['openpyxl', 'xlrd']
        read_params = [
            {},  # parámetros por defecto
            {'na_values': ['', 'N/A', 'NULL', 'null']},  # manejar valores vacíos
            {'keep_default_na': False},  # no convertir a NaN
        ]
        
        for engine in engines_to_try:
            for params in read_params:
                try:
                    # Usar context manager para asegurar que el archivo se cierre automáticamente
                    with pd.ExcelFile(file_source, engine=engine) as excel_file:
                        sheets_info = {}
                        
                        for sheet_name in excel_file.sheet_names:
                            try:
                                # leer con los parámetros actuales
                                df = pd.read_excel(excel_file, sheet_name=sheet_name, **params)
                                
                                # limpiar el dataframe
                                df = df.dropna(how='all')  # remover filas completamente vacías
                                
                                # Limpiar columnas sin nombre solo si existen
                                unnamed_cols = [col for col in df.columns if isinstance(col, str) and col.startswith('Unnamed')]
                                if unnamed_cols:
                                    df = df.drop(columns=unnamed_cols)
                                
                                # Intentar convertir columnas a numérico cuando sea posible
                                for col in df.columns:
                                    try:
                                        # Intentar conversión a numérico (sin el errors='ignore' deprecado)
                                        df[col] = pd.to_numeric(df[col])
                                    except (ValueError, TypeError):
                                        # Si falla, mantener la columna como está
                                        pass
                                
                                if not df.empty:
                                    # Información de columnas numéricas
                                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                    print(f"Sheet '{sheet_name}': {len(numeric_cols)} numeric columns found: {numeric_cols[:5]}")
                                    
                                    sheets_info[sheet_name] = {
                                        'dataframe': df,
                                        'columns': list(df.columns),
                                        'shape': df.shape,
                                        'dtypes': df.dtypes.to_dict()
                                    }
                            except Exception as e:
                                print(f"Error reading sheet {sheet_name} with {engine}: {e}")
                                continue
                        
                        if sheets_info:
                            print(f"Successfully read Excel file using {engine} engine")
                            return sheets_info
                        
                except Exception as e:
                    print(f"Failed to read with {engine}: {e}")
                    continue
        
        # si todos los métodos fallan
        raise Exception("Could not read Excel file with any available method")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def get_comprehensive_data_analysis(df: pd.DataFrame) -> dict:
    """
    Realiza un análisis completo de un DataFrame y retorna información útil
    """
    if not EXCEL_CHARTS_AVAILABLE:
        return {}
    
    try:
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_names': list(df.columns),
            'numeric_columns': [],
            'text_columns': [],
            'date_columns': [],
            'statistics': {},
            'sample_data': {},
            'data_quality': {}
        }
        
        # Analizar cada columna
        for col in df.columns:
            col_data = df[col]
            
            # Detectar tipo de columna
            if pd.api.types.is_numeric_dtype(col_data):
                analysis['numeric_columns'].append(col)
                # Estadísticas para columnas numéricas
                analysis['statistics'][col] = {
                    'count': int(col_data.count()),
                    'mean': float(col_data.mean()) if col_data.count() > 0 else 0,
                    'median': float(col_data.median()) if col_data.count() > 0 else 0,
                    'std': float(col_data.std()) if col_data.count() > 1 else 0,
                    'min': float(col_data.min()) if col_data.count() > 0 else 0,
                    'max': float(col_data.max()) if col_data.count() > 0 else 0,
                    'sum': float(col_data.sum()) if col_data.count() > 0 else 0
                }
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                analysis['date_columns'].append(col)
            else:
                analysis['text_columns'].append(col)
                # Info para columnas de texto
                unique_count = col_data.nunique()
                analysis['statistics'][col] = {
                    'unique_values': int(unique_count),
                    'most_common': str(col_data.mode()[0]) if len(col_data.mode()) > 0 else 'N/A'
                }
            
            # Muestra de datos (primeros 3 valores no nulos)
            sample = col_data.dropna().head(3).tolist()
            analysis['sample_data'][col] = [str(x) for x in sample]
            
            # Calidad de datos
            null_count = col_data.isnull().sum()
            analysis['data_quality'][col] = {
                'null_count': int(null_count),
                'null_percentage': float(null_count / len(col_data) * 100) if len(col_data) > 0 else 0
            }
        
        return analysis
    
    except Exception as e:
        print(f"Error in comprehensive analysis: {e}")
        return {}

def analyze_data_for_chart(df: pd.DataFrame, chart_type: str = "auto"):
    """Analyze dataframe to determine best chart type and data"""
    if not EXCEL_CHARTS_AVAILABLE:
        raise Exception("Chart processing not available")
    
    try:
        # obtener columnas numéricas
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        analysis = {
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'suggested_chart': chart_type
        }
        
        # sugerir tipo de gráfico automáticamente basado en los datos
        if chart_type == "auto":
            if len(numeric_cols) >= 2:
                analysis['suggested_chart'] = "scatter"
            elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                analysis['suggested_chart'] = "bar"
            elif len(numeric_cols) >= 1:
                analysis['suggested_chart'] = "line"
            else:
                analysis['suggested_chart'] = "bar"
        
        return analysis
    except Exception as e:
        print(f"Error analyzing data: {e}")
        return None

def create_matplotlib_chart(df: pd.DataFrame, chart_type: str, title: str = "Gráfico"):
    """Create matplotlib chart and return image bytes"""
    if not EXCEL_CHARTS_AVAILABLE:
        raise Exception("Chart processing not available")
    
    try:
        plt.figure(figsize=(12, 8))
        plt.style.use('default')
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if chart_type.lower() == "bar" and len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # gráfico de barras: categórico vs numérico
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            plt.bar(df[cat_col], df[num_col], color='skyblue', edgecolor='navy', alpha=0.7)
            plt.xlabel(cat_col)
            plt.ylabel(num_col)
            plt.xticks(rotation=45)
            
        elif chart_type.lower() == "line" and len(numeric_cols) >= 1:
            # gráfico de línea
            if len(numeric_cols) >= 2:
                plt.plot(df[numeric_cols[0]], df[numeric_cols[1]], marker='o', linewidth=2, markersize=6)
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
            else:
                plt.plot(df[numeric_cols[0]], marker='o', linewidth=2, markersize=6)
                plt.xlabel('Índice')
                plt.ylabel(numeric_cols[0])
                
        elif chart_type.lower() == "scatter" and len(numeric_cols) >= 2:
            # gráfico de dispersión
            plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.7, s=50)
            plt.xlabel(numeric_cols[0])
            plt.ylabel(numeric_cols[1])
            
        elif chart_type.lower() == "histogram" and len(numeric_cols) >= 1:
            # histograma
            plt.hist(df[numeric_cols[0]], bins=20, alpha=0.7, color='skyblue', edgecolor='navy')
            plt.xlabel(numeric_cols[0])
            plt.ylabel('Frecuencia')
            
        elif chart_type.lower() == "pie" and len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # gráfico de torta
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            plt.pie(df[num_col], labels=df[cat_col], autopct='%1.1f%%', startangle=90)
            
        else:
            # por defecto: gráfico de barras simple
            if len(numeric_cols) >= 1:
                plt.bar(range(len(df)), df[numeric_cols[0]], color='skyblue', edgecolor='navy', alpha=0.7)
                plt.xlabel('Índice')
                plt.ylabel(numeric_cols[0])
        
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # guardar en bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        plt.close()
        return img_buffer.getvalue()
        
    except Exception as e:
        print(f"Error creating matplotlib chart: {e}")
        return None

def create_plotly_chart(df: pd.DataFrame, chart_type: str, title: str = "Gráfico"):
    """Create plotly chart and return image bytes"""
    if not EXCEL_CHARTS_AVAILABLE:
        raise Exception("Chart processing not available")
    
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if chart_type.lower() == "bar" and len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # Bar chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            fig = px.bar(df, x=cat_col, y=num_col, title=title)
            
        elif chart_type.lower() == "line" and len(numeric_cols) >= 1:
            # Line chart
            if len(numeric_cols) >= 2:
                fig = px.line(df, x=numeric_cols[0], y=numeric_cols[1], title=title)
            else:
                fig = px.line(df, y=numeric_cols[0], title=title)
                
        elif chart_type.lower() == "scatter" and len(numeric_cols) >= 2:
            # Scatter plot
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=title)
            
        elif chart_type.lower() == "histogram" and len(numeric_cols) >= 1:
            # Histogram
            fig = px.histogram(df, x=numeric_cols[0], title=title)
            
        elif chart_type.lower() == "pie" and len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # Pie chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            fig = px.pie(df, names=cat_col, values=num_col, title=title)
            
        else:
            # por defecto: gráfico de barras simple
            if len(numeric_cols) >= 1:
                fig = px.bar(df, y=numeric_cols[0], title=title)
        
        # actualizar layout
        fig.update_layout(
            font=dict(size=12),
            title_font_size=16,
            showlegend=True
        )
        
        # convertir a bytes de imagen
        img_bytes = to_image(fig, format="png", width=1200, height=800, scale=2)
        return img_bytes
        
    except Exception as e:
        print(f"Error creating plotly chart: {e}")
        return None

def detect_chart_type_from_text(text: str):
    """Detect the most appropriate chart type from user text with advanced options"""
    text_lower = text.lower()
    
    # detección de tipo de gráfico avanzado
    chart_mappings = {
        # Basic charts
        'pie': ['pie', 'circular', 'torta', 'pastel', 'circular', 'proporción', 'porcentaje'],
        'bar': ['bar', 'barras', 'barra', 'columnas', 'comparar', 'comparación'],
        'line': ['line', 'línea', 'linea', 'tendencia', 'evolución', 'tiempo', 'cronológico'],
        'scatter': ['scatter', 'dispersión', 'dispersion', 'puntos', 'correlación', 'relación'],
        'area': ['area', 'área', 'superficie', 'relleno'],
        
        # Advanced charts
        'heatmap': ['heatmap', 'calor', 'mapa_calor', 'matriz', 'tabla_calor'],
        'treemap': ['treemap', 'mapa_arbol', 'jerarquía', 'jerárquico', 'árbol'],
        'sunburst': ['sunburst', 'sol', 'radial', 'circular_jerarquico'],
        'funnel': ['funnel', 'embudo', 'proceso', 'conversión', 'embudo_conversión'],
        'waterfall': ['waterfall', 'cascada', 'puente', 'puente_financiero'],
        'sankey': ['sankey', 'flujo', 'diagrama_flujo', 'flujo_datos', 'sankey_diagram'],
        
        # Statistical charts
        'box': ['box', 'caja', 'boxplot', 'distribución', 'cuartiles'],
        'violin': ['violin', 'violín', 'violinplot', 'densidad'],
        'histogram': ['histogram', 'histograma', 'frecuencia', 'distribución_frecuencia'],
        
        # 3D and advanced visualizations
        '3d': ['3d', 'tridimensional', '3d_scatter', 'espacial'],
        'surface': ['surface', 'superficie', '3d_surface', 'terreno'],
        'contour': ['contour', 'contorno', 'curvas_nivel', 'isobaras'],
        'density': ['density', 'densidad', 'mapa_densidad', 'concentración'],
        
        # Polar and circular charts
        'polar': ['polar', 'polar_chart', 'coordenadas_polares'],
        'radar': ['radar', 'radar_chart', 'araña', 'web', 'estrella'],
        
        # Financial charts
        'candlestick': ['candlestick', 'vela', 'velas', 'financiero', 'bolsa'],
        'gauge': ['gauge', 'medidor', 'velocímetro', 'indicador_circular'],
        'indicator': ['indicator', 'indicador', 'kpi', 'métrica'],
        
        # Flow and process charts
        'timeline': ['timeline', 'linea_tiempo', 'cronología', 'eventos'],
        'parallel': ['parallel', 'paralelo', 'coordenadas_paralelas'],
        'icicle': ['icicle', 'carámbano', 'rectángulos_jerárquicos'],
        
        # Geographic charts
        'map': ['map', 'mapa', 'geográfico', 'ubicación', 'coordenadas'],
        'choropleth': ['choropleth', 'coropleta', 'mapa_coropleta', 'regiones'],
        
        # Bubble and advanced scatter
        'bubble': ['bubble', 'burbuja', 'bubble_chart', 'tamaño_variable']
    }
    
    # puntuar cada tipo de gráfico basado en las palabras clave encontradas
    chart_scores = {}
    for chart_type, keywords in chart_mappings.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            chart_scores[chart_type] = score
    
    # devolver el tipo de gráfico con la puntuación más alta, o por defecto a torta
    if chart_scores:
        best_chart = max(chart_scores, key=chart_scores.get)
        return best_chart
    
    # fallback por defecto basado en las características de los datos
    if any(word in text_lower for word in ['tiempo', 'año', 'mes', 'día', 'cronológico']):
        return 'line'
    elif any(word in text_lower for word in ['comparar', 'comparación', 'vs', 'versus']):
        return 'bar'
    elif any(word in text_lower for word in ['proporción', 'porcentaje', 'distribución']):
        return 'pie'
    elif any(word in text_lower for word in ['correlación', 'relación', 'patrón']):
        return 'scatter'
    else:
        return 'pie'  # fallback por defecto a torta

def generate_chart_from_excel(file_path: str, chart_type: str = "auto", sheet_name: str = None, title: str = None):
    """Generate chart from Excel file"""
    if not EXCEL_CHARTS_AVAILABLE:
        return None, "❌ Funcionalidad de gráficos no disponible. Error con las dependencias."
    
    try:
        # leer archivo Excel
        sheets_info = read_excel_file(file_path)
        if not sheets_info:
            return None, "❌ Error leyendo el archivo Excel"
        
        # seleccionar hoja
        if sheet_name and sheet_name in sheets_info:
            selected_sheet = sheet_name
        else:
            # usar primera hoja
            selected_sheet = list(sheets_info.keys())[0]
        
        df = sheets_info[selected_sheet]['dataframe']
        
        # generar título si no se proporciona
        if not title:
            title = f"Gráfico de {selected_sheet} - {chart_type.title()}"
        
        # crear gráfico (prefer plotly para mejor calidad)
        chart_bytes = create_plotly_chart(df, chart_type, title)
        if not chart_bytes:
            chart_bytes = create_matplotlib_chart(df, chart_type, title)
        
        if not chart_bytes:
            return None, "❌ Error generando el gráfico"
        
        return chart_bytes, f"✅ Gráfico generado desde {selected_sheet}"
        
    except Exception as e:
        return None, f"❌ Error procesando archivo Excel: {e}"

# funciones de análisis matemático
def perform_mathematical_analysis(df: pd.DataFrame, analysis_type: str, column_name: str = None, column2_name: str = None):
    """Perform mathematical analysis on dataframe columns"""
    if not EXCEL_CHARTS_AVAILABLE:
        return None, "❌ Funcionalidad de análisis matemático no disponible"
    
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return None, "❌ No se encontraron columnas numéricas para análisis"
        
        # usar columna especificada o primera columna numérica
        if column_name and column_name in numeric_cols:
            target_col = column_name
        elif column_name and column_name in df.columns:
            return None, f"❌ La columna '{column_name}' no es numérica. Columnas numéricas disponibles: {', '.join(numeric_cols)}"
        else:
            target_col = numeric_cols[0]
        
        if analysis_type.lower() in ['suma', 'sum', 'total']:
            result = df[target_col].sum()
            return f"📊 **Suma de '{target_col}': {result:,.2f}**", None
            
        elif analysis_type.lower() in ['promedio', 'average', 'mean']:
            result = df[target_col].mean()
            return f"📊 **Promedio de '{target_col}': {result:,.2f}**", None
            
        elif analysis_type.lower() in ['mediana', 'median']:
            result = df[target_col].median()
            return f"📊 **Mediana de '{target_col}': {result:,.2f}**", None
            
        elif analysis_type.lower() in ['minimo', 'min', 'mínimo']:
            result = df[target_col].min()
            return f"📊 **Mínimo de '{target_col}': {result:,.2f}**", None
            
        elif analysis_type.lower() in ['maximo', 'max', 'máximo']:
            result = df[target_col].max()
            return f"📊 **Máximo de '{target_col}': {result:,.2f}**", None
            
        elif analysis_type.lower() in ['estadisticas', 'stats', 'estadísticas', 'descriptivo']:
            stats = df[target_col].describe()
            result = f"📊 **Estadísticas descriptivas de '{target_col}':**\n"
            result += f"• Conteo: {stats['count']:.0f}\n"
            result += f"• Media: {stats['mean']:.2f}\n"
            result += f"• Desviación estándar: {stats['std']:.2f}\n"
            result += f"• Mínimo: {stats['min']:.2f}\n"
            result += f"• 25%: {stats['25%']:.2f}\n"
            result += f"• Mediana: {stats['50%']:.2f}\n"
            result += f"• 75%: {stats['75%']:.2f}\n"
            result += f"• Máximo: {stats['max']:.2f}"
            return result, None
            
        elif analysis_type.lower() in ['correlacion', 'correlation', 'correlación']:
            if column2_name and column2_name in numeric_cols:
                corr = df[target_col].corr(df[column2_name])
                return f"📊 **Correlación entre '{target_col}' y '{column2_name}': {corr:.4f}**", None
            elif len(numeric_cols) >= 2:
                # mostrar matriz de correlación para todas las columnas numéricas
                corr_matrix = df[numeric_cols].corr()
                result = f"📊 **Matriz de correlación:**\n"
                for i, col1 in enumerate(numeric_cols):
                    for j, col2 in enumerate(numeric_cols):
                        if i < j:  # solo mostrar el triángulo superior
                            corr_val = corr_matrix.loc[col1, col2]
                            result += f"• {col1} ↔ {col2}: {corr_val:.4f}\n"
                return result, None
            else:
                return None, "❌ Se necesitan al menos 2 columnas numéricas para calcular correlación"
                
        elif analysis_type.lower() in ['conteo', 'count']:
            result = df[target_col].count()
            return f"📊 **Conteo de '{target_col}': {result} valores no nulos**", None
            
        elif analysis_type.lower() in ['desviacion', 'std', 'desviación']:
            result = df[target_col].std()
            return f"📊 **Desviación estándar de '{target_col}': {result:.2f}**", None
            
        elif analysis_type.lower() in ['varianza', 'variance']:
            result = df[target_col].var()
            return f"📊 **Varianza de '{target_col}': {result:.2f}**", None
            
        else:
            return None, f"❌ Tipo de análisis '{analysis_type}' no reconocido. Tipos disponibles: suma, promedio, mediana, mínimo, máximo, estadísticas, correlación, conteo, desviación, varianza"
            
    except Exception as e:
        return None, f"❌ Error en análisis matemático: {e}"

def detect_mathematical_request(text: str):
    """Detect if user is requesting mathematical analysis"""
    text_lower = text.lower()
    
    math_keywords = [
        'suma', 'sum', 'total', 'sumar',
        'promedio', 'average', 'mean', 'media',
        'mediana', 'median',
        'minimo', 'min', 'mínimo', 'menor',
        'maximo', 'max', 'máximo', 'mayor',
        'estadisticas', 'stats', 'estadísticas', 'descriptivo',
        'correlacion', 'correlation', 'correlación',
        'conteo', 'count', 'contar',
        'desviacion', 'std', 'desviación',
        'varianza', 'variance',
        'calcula', 'calculate', 'calcular',
        'analiza', 'analyze', 'análisis'
    ]
    
    return any(keyword in text_lower for keyword in math_keywords)

def extract_column_names(text: str, available_columns: list):
    """Extract column names from user text"""
    text_lower = text.lower()
    found_columns = []
    
    for col in available_columns:
        col_lower = col.lower()
        if col_lower in text_lower or col in text:
            found_columns.append(col)
    
    return found_columns

def extract_data_from_text(text: str):
    """Extract numerical data and categories from descriptive text"""
    import re
    
    # patrones comunes para la extracción de datos
    patterns = [
        # Pattern: "X personas, Y de ellas..."
        r'(\d+)\s*(?:personas?|gente|individuos?|elementos?)',
        # Pattern: "X de ellas cumplen en Y"
        r'(\d+)\s*(?:de ellas|de los|de las)?\s*(?:cumplen|nacen|están|son|tienen|pertenecen)\s*(?:en|a|del|de)\s*([^,\n]+)',
        # Pattern: "X en Y"
        r'(\d+)\s*(?:en|de|del|para)\s*([^,\n]+)',
        # Pattern: "Y: X"
        r'([^:\d]+):\s*(\d+)',
        # Pattern: "X Y" (number followed by category)
        r'(\d+)\s+([a-zA-ZáéíóúñüÁÉÍÓÚÑÜ\s]+?)(?:\s*,\s*|\s*\.\s*|\s*$|\s*y\s*)',
    ]
    
    extracted_data = {}
    text_lower = text.lower()
    
    # Look for total count
    total_match = re.search(r'(\d+)\s*(?:personas?|gente|individuos?|elementos?|total)', text_lower)
    total_count = int(total_match.group(1)) if total_match else None
    
    # extraer categorías y sus conteos  
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match) == 2:
                count_str, category = match
                try:
                    count = int(count_str.strip())
                    category = category.strip()
                    
                    # limpiar nombre de categoría
                    category = re.sub(r'\s+', ' ', category)  # remover espacios extra  
                    category = category.strip('.,;:')  # remover puntuación
                    
                    if category and count > 0:
                        extracted_data[category] = count
                except ValueError:
                    continue
    
    # si tenemos un total, calcular "otros" o el resto
    if total_count and extracted_data:
        calculated_total = sum(extracted_data.values())
        if calculated_total < total_count:
            remaining = total_count - calculated_total
            if remaining > 0:
                extracted_data['Otros'] = remaining
    
    return extracted_data, total_count

def create_chart_from_text_data(data: dict, chart_type: str = "pie", title: str = "Gráfico de Datos"):
    """Create a chart from extracted text data with advanced chart types"""
    if not EXCEL_CHARTS_AVAILABLE:
        return None, "❌ Funcionalidad de gráficos no disponible"
    
    try:
        if not data:
            return None, "❌ No se pudieron extraer datos del texto"
        
        # convertir a pandas DataFrame
        df = pd.DataFrame(list(data.items()), columns=['Categoría', 'Valor'])
        
        # crear gráfico basado en el tipo
        chart_type_lower = chart_type.lower()
        
        if chart_type_lower in ['pie', 'circular', 'torta', 'pastel']:
            fig = px.pie(df, values='Valor', names='Categoría', title=title)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
        elif chart_type_lower in ['bar', 'barras', 'barra']:
            fig = px.bar(df, x='Categoría', y='Valor', title=title)
            fig.update_layout(xaxis_tickangle=-45)
            
        elif chart_type_lower in ['column', 'columna']:
            fig = px.bar(df, x='Categoría', y='Valor', title=title, orientation='v')
            
        elif chart_type_lower in ['line', 'línea', 'linea', 'tendencia']:
            fig = px.line(df, x='Categoría', y='Valor', title=title, markers=True)
            
        elif chart_type_lower in ['scatter', 'dispersión', 'dispersion', 'puntos']:
            fig = px.scatter(df, x='Categoría', y='Valor', title=title, size='Valor')
            
        elif chart_type_lower in ['area', 'área', 'area_chart']:
            fig = px.area(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['funnel', 'embudo', 'embudo']:
            fig = px.funnel(df, x='Valor', y='Categoría', title=title)
            
        elif chart_type_lower in ['sunburst', 'sol', 'sunburst_chart']:
            # crear datos jerárquicos para sunburst
            fig = px.sunburst(df, path=['Categoría'], values='Valor', title=title)
            
        elif chart_type_lower in ['treemap', 'mapa_arbol', 'treemap_chart']:
            fig = px.treemap(df, path=['Categoría'], values='Valor', title=title)
            
        elif chart_type_lower in ['waterfall', 'cascada', 'waterfall_chart']:
            fig = px.waterfall(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['box', 'caja', 'boxplot']:
            fig = px.box(df, y='Valor', title=title)
            
        elif chart_type_lower in ['violin', 'violín', 'violinplot']:
            fig = px.violin(df, y='Valor', title=title)
            
        elif chart_type_lower in ['histogram', 'histograma']:
            fig = px.histogram(df, x='Valor', title=title)
            
        elif chart_type_lower in ['heatmap', 'calor', 'mapa_calor']:
            # crear datos de mapa de calor
            heatmap_data = df.pivot_table(values='Valor', index='Categoría', columns='Categoría', fill_value=0)
            fig = px.imshow(heatmap_data, title=title, color_continuous_scale='Viridis')
            
        elif chart_type_lower in ['polar', 'polar_chart']:
            fig = px.bar_polar(df, r='Valor', theta='Categoría', title=title)
            
        elif chart_type_lower in ['radar', 'radar_chart']:
            fig = px.line_polar(df, r='Valor', theta='Categoría', line_close=True, title=title)
            
        elif chart_type_lower in ['sankey', 'sankey_diagram']:
            # crear diagrama de Sankey usando go.Sankey
            import plotly.graph_objects as go
            
            # crear datos de flujo simple
            sources = [0, 1, 2] if len(df) >= 3 else list(range(len(df)))
            targets = [len(df)] * len(sources)
            values = df['Valor'].tolist()
            labels = df['Categoría'].tolist() + ['Proceso Central']
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="lightblue"
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values
                )
            )])
            fig.update_layout(title_text=title)
            
        elif chart_type_lower in ['candlestick', 'vela', 'candlestick_chart']:
            # crear gráfico de velas usando go.Candlestick
            import plotly.graph_objects as go
            
            # crear datos sintéticos OHLC
            fig = go.Figure(data=[go.Candlestick(
                x=df['Categoría'],
                open=df['Valor'] * 0.95,
                high=df['Valor'] * 1.05,
                low=df['Valor'] * 0.9,
                close=df['Valor']
            )])
            fig.update_layout(title_text=title)
            
        elif chart_type_lower in ['density', 'densidad', 'density_chart']:
            # crear mapa de calor de densidad
            fig = px.imshow([[df['Valor'].iloc[i] for i in range(len(df))]], title=title, color_continuous_scale='Viridis')
            
        elif chart_type_lower in ['contour', 'contorno', 'contour_chart']:
                # crear gráfico de contorno
            fig = px.density_contour(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['surface', 'superficie', 'surface_chart']:
            # crear gráfico de superficie 3D
            fig = px.scatter_3d(df, x='Categoría', y='Valor', z='Valor', title=title)
            
        elif chart_type_lower in ['3d', '3d_scatter', 'tridimensional']:
            fig = px.scatter_3d(df, x='Categoría', y='Valor', z='Valor', title=title)
            
        elif chart_type_lower in ['bubble', 'burbuja', 'bubble_chart']:
            fig = px.scatter(df, x='Categoría', y='Valor', size='Valor', title=title)
            
        elif chart_type_lower in ['gauge', 'medidor', 'gauge_chart']:
            # crear gráfico de medidor usando go.Indicator
            import plotly.graph_objects as go
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=df['Valor'].sum(),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': title},
                gauge={'axis': {'range': [None, df['Valor'].max() * 1.2]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, df['Valor'].max() * 0.5], 'color': "lightgray"},
                           {'range': [df['Valor'].max() * 0.5, df['Valor'].max()], 'color': "gray"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': df['Valor'].max() * 0.9}}))
            
        elif chart_type_lower in ['indicator', 'indicador', 'indicator_chart']:
            # crear gráfico de indicador usando go.Indicator
            import plotly.graph_objects as go
            
            fig = go.Figure(go.Indicator(
                mode="number+delta",
                value=df['Valor'].sum(),
                title={'text': title},
                delta={'reference': df['Valor'].mean()}
            ))
            
        elif chart_type_lower in ['icicle', 'carámbano', 'icicle_chart']:
            # crear gráfico de carámbano (fallback a treemap)
            fig = px.treemap(df, path=['Categoría'], values='Valor', title=title)
            
        elif chart_type_lower in ['parallel', 'paralelo', 'parallel_chart']:
            # crear coordenadas paralelas (fallback a gráfico de línea)
            fig = px.line(df, x='Categoría', y='Valor', title=title, markers=True)
            
        elif chart_type_lower in ['parallel_categories', 'categorias_paralelas']:
            # crear categorías paralelas (fallback a gráfico de barras)
            fig = px.bar(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['timeline', 'linea_tiempo', 'timeline_chart']:
            # crear línea de tiempo (fallback a gráfico de barras)
            fig = px.bar(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['map', 'mapa', 'map_chart']:
            # crear mapa (fallback a gráfico de dispersión)
            fig = px.scatter(df, x='Categoría', y='Valor', title=title)
            
        elif chart_type_lower in ['choropleth', 'coropleta', 'choropleth_chart']:
            # crear choropleth (fallback a gráfico de barras)
            fig = px.bar(df, x='Categoría', y='Valor', title=title)
            
        else:
            # por defecto: gráfico de torta
            fig = px.pie(df, values='Valor', names='Categoría', title=title)
            fig.update_traces(textposition='inside', textinfo='percent+label')
        
        # personalizar layout
        fig.update_layout(
            title_font_size=16,
            font_size=12,
            showlegend=True,
            height=600,
            width=800
        )
        
        # convertir a bytes de imagen
        chart_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        
        return chart_bytes, f"✅ Gráfico {chart_type} generado desde texto"
        
    except Exception as e:
        return None, f"❌ Error generando gráfico {chart_type}: {e}"

def detect_chart_request_from_text(text: str):
    """Detect if user is requesting a chart from descriptive text"""
    text_lower = text.lower()
    
    # palabras clave que indican solicitud de gráfico
    chart_keywords = [
        'gráfico', 'grafico', 'gráfica', 'grafica', 'chart', 'diagrama',
        'crea', 'crear', 'genera', 'generar', 'haz', 'hacer',
        'muestra', 'mostrar', 'visualiza', 'visualizar',
        'personas', 'gente', 'individuos', 'elementos',
        'cumplen', 'nacen', 'están', 'pertenecen'
    ]
    
    # verificar patrones de datos numéricos
    import re
    has_numbers = bool(re.search(r'\d+', text))
    has_categories = any(word in text_lower for word in ['diciembre', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'mes', 'año', 'día'])
    
    return any(keyword in text_lower for keyword in chart_keywords) and has_numbers and has_categories

# funciones de análisis de datos avanzado y procesamiento
def analyze_data_with_gemini(text_data: str, chat_id: int, api_url: str, api_key: str):
    """Use Gemini to analyze and structure data for better chart generation"""
    try:
        # primero intentar un análisis simple sin Gemini
        simple_analysis = simple_data_analysis(text_data)
        if simple_analysis:
            return simple_analysis
        
        # si el análisis simple falla, intentar con Gemini
        analysis_prompt = f"""
Analiza los siguientes datos y proporciona un análisis estructurado:

DATOS: {text_data}

Por favor proporciona:
1. TIPO DE DATOS: ¿Qué tipo de información contienen estos datos?
2. CATEGORÍAS IDENTIFICADAS: Lista las categorías principales encontradas
3. VALORES NUMÉRICOS: Extrae todos los números y sus categorías correspondientes. Si hay porcentajes solicitados, calcúlalos.
4. TIPO DE GRÁFICO RECOMENDADO: ¿Qué tipo de gráfico sería más apropiado?
5. TÍTULO SUGERIDO: Propón un título descriptivo para el gráfico
6. ANÁLISIS: ¿Qué patrones o tendencias observas? Incluye cálculos de porcentajes si se solicitan.

IMPORTANTE: Si se solicitan porcentajes, calcúlalos correctamente. Por ejemplo:
- Si hay 50 personas totales y 33 son niños: niños = 33/50 = 66%, niñas = 17/50 = 34%

Formato de respuesta:
TIPO: [tipo de datos]
CATEGORÍAS: [lista de categorías]
VALORES: [categoría: valor, categoría: valor, ...]
GRÁFICO: [tipo recomendado]
TÍTULO: [título sugerido]
ANÁLISIS: [análisis de patrones con cálculos de porcentajes]
"""
        
        # usar solicitud HTTP sincrónica en lugar de función asíncrona
        import requests
        import json
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # preparar payload basado en el formato de URL de la API
        if "generateContent" in api_url:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": analysis_prompt}
                        ]
                    }
                ]
            }
        else:
            payload = {
                "instances": [
                    {
                        "content": analysis_prompt
                    }
                ]
            }
        
        # hacer solicitud sincrónica
        response = requests.post(
            f"{api_url}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # parsear respuesta basado en el formato de API
            if "candidates" in result and len(result["candidates"]) > 0:
                if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                    response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    response_text = str(result["candidates"][0])
            elif "predictions" in result and len(result["predictions"]) > 0:
                response_text = str(result["predictions"][0])
            else:
                response_text = str(result)
            
            return parse_gemini_analysis(response_text)
        else:
            print(f"Error calling Gemini: Request failed with status {response.status_code}: {response.text}")
            return None
        
    except Exception as e:
        print(f"Error analyzing data with Gemini: {e}")
        return None

def simple_data_analysis(text_data: str):
    """Simple data analysis without Gemini for basic cases"""
    try:
        import re
        
        # buscar patrones comunes
        text_lower = text_data.lower()
        
        # patrón 1: "Hay X personas, Y son A y el resto son B"
        pattern1 = r'hay\s+(\d+)\s+(\w+),\s*(\d+)\s+son\s+(\w+)\s+y\s+el\s+resto\s+son\s+(\w+)'
        match1 = re.search(pattern1, text_lower)
        
        if match1:
            total = int(match1.group(1))
            category1_count = int(match1.group(3))
            category1_name = match1.group(4)
            category2_name = match1.group(5)
            category2_count = total - category1_count
            
            # calcular porcentajes
            cat1_percent = (category1_count / total) * 100
            cat2_percent = (category2_count / total) * 100
            
            analysis = {
                'data_type': 'Distribución demográfica',
                'categories': [category1_name, category2_name],
                'values': {
                    category1_name: category1_count,
                    category2_name: category2_count
                },
                'chart_type': 'pie',
                'title': f'Distribución de {category1_name} y {category2_name}',
                'analysis': f'De las {total} personas totales:\n- {category1_name}: {category1_count} personas ({cat1_percent:.1f}%)\n- {category2_name}: {category2_count} personas ({cat2_percent:.1f}%)'
            }
            return analysis
        
        # patrón 2: "X personas, Y son A y Z son B"
        pattern2 = r'(\d+)\s+(\w+),\s*(\d+)\s+son\s+(\w+)\s+y\s+(\d+)\s+son\s+(\w+)'
        match2 = re.search(pattern2, text_lower)
        
        if match2:
            total = int(match2.group(1))
            category1_count = int(match2.group(3))
            category1_name = match2.group(4)
            category2_count = int(match2.group(5))
            category2_name = match2.group(6)
            
            # calcular porcentajes
            cat1_percent = (category1_count / total) * 100
            cat2_percent = (category2_count / total) * 100
            
            analysis = {
                'data_type': 'Distribución demográfica',
                'categories': [category1_name, category2_name],
                'values': {
                    category1_name: category1_count,
                    category2_name: category2_count
                },
                'chart_type': 'pie',
                'title': f'Distribución de {category1_name} y {category2_name}',
                'analysis': f'De las {total} personas totales:\n- {category1_name}: {category1_count} personas ({cat1_percent:.1f}%)\n- {category2_name}: {category2_count} personas ({cat2_percent:.1f}%)'
            }
            return analysis
        
        # patrón 3: "X son A y Y son B"
        pattern3 = r'(\d+)\s+son\s+(\w+)\s+y\s+(\d+)\s+son\s+(\w+)'
        match3 = re.search(pattern3, text_lower)
        
        if match3:
            category1_count = int(match3.group(1))
            category1_name = match3.group(2)
            category2_count = int(match3.group(3))
            category2_name = match3.group(4)
            total = category1_count + category2_count
            
            # calcular porcentajes
            cat1_percent = (category1_count / total) * 100
            cat2_percent = (category2_count / total) * 100
            
            analysis = {
                'data_type': 'Distribución demográfica',
                'categories': [category1_name, category2_name],
                'values': {
                    category1_name: category1_count,
                    category2_name: category2_count
                },
                'chart_type': 'pie',
                'title': f'Distribución de {category1_name} y {category2_name}',
                'analysis': f'Total: {total} personas\n- {category1_name}: {category1_count} personas ({cat1_percent:.1f}%)\n- {category2_name}: {category2_count} personas ({cat2_percent:.1f}%)'
            }
            return analysis
        
        return None
        
    except Exception as e:
        print(f"Error in simple data analysis: {e}")
        return None

def parse_gemini_analysis(response: str):
    """Parse Gemini's structured analysis response"""
    try:
        analysis = {
            'data_type': 'Datos generales',
            'categories': [],
            'values': {},
            'chart_type': 'pie',
            'title': 'Gráfico de Datos',
            'analysis': 'Análisis no disponible'
        }
        
        # depuración: imprimir la respuesta para ver qué obtenemos
        print(f"Gemini response: {response}")
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TIPO:'):
                analysis['data_type'] = line.replace('TIPO:', '').strip()
            elif line.startswith('CATEGORÍAS:'):
                categories_text = line.replace('CATEGORÍAS:', '').strip()
                analysis['categories'] = [cat.strip() for cat in categories_text.split(',') if cat.strip()]
            elif line.startswith('VALORES:'):
                values_text = line.replace('VALORES:', '').strip()
                for pair in values_text.split(','):
                    if ':' in pair:
                        cat, val = pair.split(':', 1)
                        try:
                            # extraer valor numérico del texto
                            import re
                            numbers = re.findall(r'\d+\.?\d*', val.strip())
                            if numbers:
                                analysis['values'][cat.strip()] = float(numbers[0])
                        except ValueError:
                            continue
            elif line.startswith('GRÁFICO:'):
                chart_type = line.replace('GRÁFICO:', '').strip().lower()
                if 'barras' in chart_type or 'bar' in chart_type:
                    analysis['chart_type'] = 'bar'
                elif 'circular' in chart_type or 'pie' in chart_type:
                    analysis['chart_type'] = 'pie'
                else:
                    analysis['chart_type'] = 'pie'
            elif line.startswith('TÍTULO:'):
                analysis['title'] = line.replace('TÍTULO:', '').strip()
            elif line.startswith('ANÁLISIS:'):
                analysis['analysis'] = line.replace('ANÁLISIS:', '').strip()
        
        # si no se extrajeron valores, intentar extraerlos del texto de análisis
        if not analysis['values']:
            import re
            # Look for patterns like "33 niños", "17 niñas", etc.
            numbers = re.findall(r'(\d+)\s+(\w+)', response)
            for number, category in numbers:
                analysis['values'][category] = float(number)
        
        # si aún no se extrajeron valores, intentar extraerlos del texto original
        if not analysis['values']:
            import re
            # buscar patrones como "33 son niños", "17 son niñas", etc.
            patterns = [
                r'(\d+)\s+son\s+(\w+)',
                r'(\d+)\s+(\w+)',
                r'(\d+)\s+de\s+ellas\s+(\w+)',
                r'(\d+)\s+(\w+)\s+y\s+(\d+)\s+(\w+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        number, category = match
                        analysis['values'][category] = float(number)
                    elif len(match) == 4:
                        # manejar patrón "X niños y Y niñas"
                        num1, cat1, num2, cat2 = match
                        analysis['values'][cat1] = float(num1)
                        analysis['values'][cat2] = float(num2)
        
        print(f"Parsed analysis: {analysis}")
        return analysis
        
    except Exception as e:
        print(f"Error parsing Gemini analysis: {e}")
        return None

def store_analyzed_data(chat_id: int, data_type: str, categories: list, values: dict, analysis: str, chart_type: str = "pie", title: str = "Gráfico de Datos"):
    """Store analyzed data in user's context for future reference"""
    try:
        # cargar almacenamiento de datos existente
        storage_file = f"user_data_{chat_id}.json"
        if os.path.exists(storage_file):
            with open(storage_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        else:
            user_data = {'datasets': [], 'analyses': []}
        
        # agregar nuevo conjunto de datos
        dataset = {
            'timestamp': datetime.now().isoformat(),
            'data_type': data_type,
            'categories': categories,
            'values': values,
            'analysis': analysis,
            'chart_type': chart_type,
            'title': title
        }
        
        user_data['datasets'].append(dataset)
        
        # mantener solo los últimos 10 conjuntos de datos
        if len(user_data['datasets']) > 10:
            user_data['datasets'] = user_data['datasets'][-10:]
        
        # guardar datos actualizados
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error storing analyzed data: {e}")
        return False

def get_last_analyzed_data(chat_id: int):
    """Get the last analyzed data for a user"""
    try:
        storage_file = f"user_data_{chat_id}.json"
        if os.path.exists(storage_file):
            with open(storage_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                datasets = user_data.get('datasets', [])
                if datasets:
                    return datasets[-1]  # devolver último conjunto de datos
        return None
    except Exception as e:
        print(f"Error getting last analyzed data: {e}")
        return None

def get_stored_datasets(chat_id: int):
    """Retrieve stored datasets for user"""
    try:
        storage_file = f"user_data_{chat_id}.json"
        if os.path.exists(storage_file):
            with open(storage_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                return user_data.get('datasets', [])
        return []
    except Exception as e:
        print(f"Error retrieving stored datasets: {e}")
        return []

def create_flow_diagram(data: dict, title: str = "Diagrama de Flujo"):
    """Create a flow diagram using Sankey or flow visualization"""
    if not EXCEL_CHARTS_AVAILABLE:
        return None, "❌ Funcionalidad de gráficos no disponible"
    
    try:
        import plotly.graph_objects as go
        
        # convertir datos a formato de flujo
        categories = list(data.keys())
        values = list(data.values())
        
        # crear datos de flujo para Sankey
        sources = []
        targets = []
        values_flow = []
        
        # crear un flujo simple desde cada categoría a un nodo central
        for i, (category, value) in enumerate(data.items()):
            sources.append(i)
            targets.append(len(categories))  # nodo central
            values_flow.append(value)
        
        # agregar etiquetas
        labels = categories + ['Proceso Central']
        
        # crear diagrama de Sankey usando go.Sankey
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color="blue"
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values_flow
            )
        )])
        
        fig.update_layout(
            title_text=title,
            title_font_size=16,
            font_size=12,
            height=600,
            width=800
        )
        
        chart_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        return chart_bytes, f"✅ Diagrama de flujo generado"
        
    except Exception as e:
        return None, f"❌ Error generando diagrama de flujo: {e}"

def create_advanced_analysis(data: dict, analysis_type: str, title: str = "Análisis Avanzado"):
    """Create advanced statistical analysis and visualizations"""
    if not EXCEL_CHARTS_AVAILABLE:
        return None, "❌ Funcionalidad de gráficos no disponible"
    
    try:
        df = pd.DataFrame(list(data.items()), columns=['Categoría', 'Valor'])
        
        if analysis_type == 'correlation_matrix':
            # crear matriz de correlación
            corr_data = df.pivot_table(values='Valor', index='Categoría', columns='Categoría', fill_value=0)
            fig = px.imshow(corr_data, title=f"{title} - Matriz de Correlación", color_continuous_scale='RdBu')
            
        elif analysis_type == 'distribution_analysis':
            # crear análisis de distribución
            fig = px.histogram(df, x='Valor', title=f"{title} - Análisis de Distribución", nbins=10)
            
        elif analysis_type == 'outlier_detection':
            # crear gráfico de caja para detección de outliers
            fig = px.box(df, y='Valor', title=f"{title} - Detección de Outliers")
            
        elif analysis_type == 'trend_analysis':
            # crear análisis de tendencia
            fig = px.line(df, x='Categoría', y='Valor', title=f"{title} - Análisis de Tendencia", markers=True)
            
        elif analysis_type == 'comparative_analysis':
            # crear análisis comparativo
            fig = px.bar(df, x='Categoría', y='Valor', title=f"{title} - Análisis Comparativo")
            
        else:
            # por defecto: gráfico de torta
            fig = px.pie(df, values='Valor', names='Categoría', title=f"{title} - Análisis General")
        
        fig.update_layout(
            title_font_size=16,
            font_size=12,
            height=600,
            width=800
        )
        
        chart_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        return chart_bytes, f"✅ Análisis {analysis_type} generado"
        
    except Exception as e:
        return None, f"❌ Error generando análisis {analysis_type}: {e}"

def detect_analysis_type_from_text(text: str):
    """Detect the type of analysis requested from user text"""
    text_lower = text.lower()
    
    analysis_mappings = {
        'correlation_matrix': ['correlación', 'matriz', 'relación', 'correlacion'],
        'distribution_analysis': ['distribución', 'distribucion', 'frecuencia', 'histograma'],
        'outlier_detection': ['outliers', 'valores_atípicos', 'anómalos', 'extremos'],
        'trend_analysis': ['tendencia', 'evolución', 'cambio', 'progresión'],
        'comparative_analysis': ['comparar', 'comparación', 'vs', 'versus'],
        'flow_diagram': ['flujo', 'proceso', 'diagrama_flujo', 'sankey'],
        'heatmap': ['calor', 'mapa_calor', 'heatmap', 'matriz'],
        'treemap': ['jerarquía', 'jerarquico', 'árbol', 'treemap'],
        'sunburst': ['radial', 'sol', 'sunburst', 'circular_jerarquico']
    }
    
    for analysis_type, keywords in analysis_mappings.items():
        if any(keyword in text_lower for keyword in keywords):
            return analysis_type
    
    return 'comparative_analysis'  # Default

def enhance_chart_with_analysis(chart_bytes: bytes, analysis: dict, extracted_data: dict):
    """Enhance chart with analysis insights"""
    if not EXCEL_CHARTS_AVAILABLE:
        return chart_bytes
    
    try:
        # convertir bytes de imagen a DataFrame para mejorar
        df = pd.DataFrame(list(extracted_data.items()), columns=['Categoría', 'Valor'])
        
        # crear gráfico mejorado con análisis
        if analysis['chart_type'] == 'pie':
            fig = px.pie(df, values='Valor', names='Categoría', title=analysis['title'])
            fig.update_traces(textposition='inside', textinfo='percent+label')
        else:
            fig = px.bar(df, x='Categoría', y='Valor', title=analysis['title'])
            fig.update_layout(xaxis_tickangle=-45)
        
        # agregar análisis como anotación
        if analysis['analysis'] and analysis['analysis'] != 'Análisis no disponible':
            fig.add_annotation(
                text=f"Análisis: {analysis['analysis']}",
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                showarrow=False,
                font=dict(size=10, color="gray"),
                align="center"
            )
        
        # layout mejorado
        fig.update_layout(
            title_font_size=16,
            font_size=12,
            showlegend=True,
            height=600,  # aumentar altura para análisis
            width=800,   # aumentar ancho
            margin=dict(b=100)  # margen inferior para texto de análisis
        )
        
        # convertir de nuevo a bytes de imagen
        enhanced_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        return enhanced_bytes
        
    except Exception as e:
        print(f"Error enhancing chart: {e}")
        return chart_bytes

def generate_audio_response(text: str, language: str = "es"):
    """Generate audio response using gTTS"""
    if not VOICE_AVAILABLE:
        raise Exception("Voice processing not available")
    try:
        # mapear códigos de idioma
        lang_map = {
            "es": "es",  # Spanish
            "en": "en",  # English
            "spanish": "es",
            "english": "en"
        }
        
        gtts_lang = lang_map.get(language.lower(), "es")
        
        # generar audio
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        
        # guardar en archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        
        return temp_file.name
    except Exception as e:
        print(f"Error generating audio response: {e}")
        return None

# comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_to_memory(chat_id, "system", "Bot started")
    await update.message.reply_text("¡Hola! Soy tu bot de Telegram con memoria. Puedo recordar nuestra conversación. Usa /help para ver comandos disponibles.")


# comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Comandos disponibles:\n"
        "/start - Comienza la conversación\n"
        "/help - Mostrar esta ayuda\n"
        "/echo <texto> - El bot devuelve el texto provisto\n"
        "/clear - Limpiar historial de conversación\n"
        "/memory - Ver historial de conversación\n"
        "/audiolimit - Ver límite actual de caracteres para audio\n"
        "/setaudiolimit <número> - Cambiar límite de caracteres para audio\n"
        "/charthelp - Ayuda para generación de gráficos\n"
        "/analyze [datos] - Analizar datos con IA sin generar gráfico\n"
        "/creargrafica - Crear gráfico basado en análisis previo\n"
        "/datahistory - Ver historial de análisis de datos\n"
        "/cleardata - Limpiar historial de datos\n"
        "🎤 Envía un mensaje de voz y recibirás transcripción + respuesta en audio" if VOICE_AVAILABLE else "🎤 Funcionalidad de voz temporalmente deshabilitada" + "\n"
        "📊 Envía un archivo Excel (.xlsx) para generar gráficos y análisis matemáticos" if EXCEL_CHARTS_AVAILABLE else "📊 Funcionalidad de Excel temporalmente deshabilitada" + "\n"
        "📈 Escribe datos descriptivos para generar gráficos automáticamente" if EXCEL_CHARTS_AVAILABLE else ""
    )
    await update.message.reply_text(help_text)

async def chart_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for chart generation functionality"""
    if not EXCEL_CHARTS_AVAILABLE:
        await update.message.reply_text("❌ Funcionalidad de gráficos no disponible.")
        return
    
    help_text = """
📊 **Generación de Gráficos y Análisis Matemático Avanzado**

**🧠 Análisis Inteligente con IA:**
• Gemini analiza automáticamente tus datos
• Identifica patrones y tendencias
• Recomienda el mejor tipo de gráfico
• Genera títulos descriptivos
• Almacena análisis para referencia futura

**📈 Comandos Disponibles:**
• `/analyze [datos]` - Analizar datos sin generar gráfico
• `/creargrafica` - Crear gráfico basado en análisis previo
• `/datahistory` - Ver historial de análisis
• `/cleardata` - Limpiar historial de datos

**📊 Tipos de Gráficos Disponibles:**

**🔵 Gráficos Básicos:**
• **Barras** - Para comparar categorías
• **Circular/Pie** - Para mostrar proporciones
• **Línea** - Para mostrar tendencias
• **Dispersión** - Para mostrar correlaciones
• **Área** - Para mostrar acumulación

**🔥 Gráficos Avanzados:**
• **Heatmap** - Mapa de calor para matrices
• **Treemap** - Mapa de árbol jerárquico
• **Sunburst** - Gráfico radial jerárquico
• **Funnel** - Embudo de conversión
• **Waterfall** - Cascada financiera
• **Sankey** - Diagrama de flujo

**📈 Gráficos Estadísticos:**
• **Box Plot** - Distribución y cuartiles
• **Violín** - Distribución de densidad
• **Histograma** - Distribución de frecuencias
• **Density** - Mapa de densidad

**🌐 Visualizaciones 3D:**
• **3D Scatter** - Dispersión tridimensional
• **Surface** - Superficie 3D
• **Contour** - Curvas de nivel
• **3D Surface** - Terreno 3D

**🎯 Gráficos Especializados:**
• **Polar** - Coordenadas polares
• **Radar** - Gráfico de araña
• **Candlestick** - Velas financieras
• **Gauge** - Medidor circular
• **Indicator** - Indicador KPI
• **Timeline** - Línea de tiempo
• **Bubble** - Gráfico de burbujas

**🗺️ Gráficos Geográficos:**
• **Map** - Mapa de dispersión
• **Choropleth** - Mapa coroplético

**🔢 Análisis Matemático Disponible:**
• **Suma** - `suma de [columna]` o `total de [columna]`
• **Promedio** - `promedio de [columna]` o `media de [columna]`
• **Mediana** - `mediana de [columna]`
• **Mínimo/Máximo** - `mínimo de [columna]` o `máximo de [columna]`
• **Estadísticas** - `estadísticas de [columna]` (completo)
• **Correlación** - `correlación entre [columna1] y [columna2]`
• **Conteo** - `conteo de [columna]`
• **Desviación estándar** - `desviación de [columna]`
• **Varianza** - `varianza de [columna]`

**💡 Ejemplos de Solicitudes Avanzadas:**
• "Hay 50 personas, 30 cumplen en diciembre y 15 en enero, crea un mapa de calor"
• "En mi empresa: 25 empleados en ventas, 15 en marketing, 10 en IT, haz un treemap"
• "Ventas por mes: enero 100, febrero 150, marzo 200, crea un diagrama de flujo"
• "Distribución de edades: 20-30 años: 40 personas, 30-40 años: 30 personas, haz un radar"
• "Datos financieros: crea velas japonesas"
• "Proceso de conversión: crea un embudo"
• "Datos geográficos: crea un mapa coroplético"

**🎯 Características Avanzadas:**
• Análisis automático de patrones con Gemini
• Almacenamiento inteligente de datos
• Gráficos mejorados con insights de IA
• Recomendaciones personalizadas de visualización
• Historial completo de análisis realizados
• Detección automática del tipo de gráfico más apropiado
• Soporte para más de 25 tipos de gráficos diferentes

**🔄 Flujo de Trabajo Recomendado:**
1. **Analizar datos:** `/analyze Hay 50 personas, 33 son niños y el resto son niñas`
2. **Crear gráfico:** `/creargrafica` (usa el análisis previo automáticamente)
3. **Ver historial:** `/datahistory` (revisar análisis anteriores)

**Notas:**
• El bot detecta automáticamente las columnas numéricas y categóricas
• Gemini analiza y estructura los datos para mejor visualización
• Los gráficos incluyen análisis de patrones integrado
• Todos los análisis se almacenan para referencia futura
• Puedes especificar el tipo de gráfico o dejar que el bot lo detecte automáticamente
"""
    
    await update.message.reply_text(help_text)

async def data_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's data analysis history"""
    chat_id = update.effective_chat.id
    
    try:
        datasets = get_stored_datasets(chat_id)
        
        if not datasets:
            await update.message.reply_text("📊 No tienes análisis de datos almacenados aún.\n\n💡 Envía datos descriptivos para generar gráficos y análisis.")
            return
        
        history_text = "📊 **Historial de Análisis de Datos:**\n\n"
        
        for i, dataset in enumerate(datasets[-5:], 1):  # Show last 5
            timestamp = dataset['timestamp'][:16].replace('T', ' ')
            history_text += f"**{i}. {dataset['data_type']}** ({timestamp})\n"
            history_text += f"• Categorías: {', '.join(dataset['categories'][:3])}{'...' if len(dataset['categories']) > 3 else ''}\n"
            history_text += f"• Análisis: {dataset['analysis'][:100]}{'...' if len(dataset['analysis']) > 100 else ''}\n\n"
        
        if len(datasets) > 5:
            history_text += f"... y {len(datasets) - 5} análisis más"
        
        await update.message.reply_text(history_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error obteniendo historial: {e}")

async def clear_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user's stored data analysis history"""
    chat_id = update.effective_chat.id
    
    try:
        storage_file = f"user_data_{chat_id}.json"
        if os.path.exists(storage_file):
            os.remove(storage_file)
            await update.message.reply_text("🗑️ Historial de análisis de datos eliminado exitosamente.")
        else:
            await update.message.reply_text("📊 No hay datos almacenados para eliminar.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error eliminando datos: {e}")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze text data without generating chart"""
    chat_id = update.effective_chat.id
    user_message = update.message.text.replace('/analyze', '').strip()
    
    if not user_message:
        await update.message.reply_text("📝 Usa: /analyze [datos para analizar]\n\nEjemplo: /analyze Hay 50 personas, 30 cumplen en diciembre y 15 en enero")
        return
    
    try:
        await update.message.reply_text("🧠 Analizando datos con IA avanzada...")
        
        # usar Gemini para analizar los datos
        gemini_url = os.getenv("GEMINI_API_URL")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if gemini_url and gemini_key:
            analysis = analyze_data_with_gemini(user_message, chat_id, gemini_url, gemini_key)
            
            if analysis:
                # almacenar los datos analizados con tipo de gráfico para uso posterior
                store_analyzed_data(
                    chat_id, 
                    analysis['data_type'], 
                    analysis['categories'], 
                    analysis['values'], 
                    analysis['analysis'],
                    analysis['chart_type'],
                    analysis['title']
                )
                
                analysis_text = f"🔍 **Análisis Detallado:**\n\n"
                analysis_text += f"📊 **Tipo de datos:** {analysis['data_type']}\n"
                analysis_text += f"🏷️ **Categorías identificadas:** {', '.join(analysis['categories'])}\n"
                analysis_text += f"📈 **Valores extraídos:**\n"
                
                for category, value in analysis['values'].items():
                    analysis_text += f"• {category}: {value}\n"
                
                analysis_text += f"\n🎯 **Gráfico recomendado:** {analysis['chart_type'].title()}\n"
                analysis_text += f"📝 **Título sugerido:** {analysis['title']}\n\n"
                analysis_text += f"🧠 **Análisis de patrones:**\n{analysis['analysis']}\n\n"
                analysis_text += f"💡 **Para crear el gráfico, usa:** `/creargrafica`"
                
                await update.message.reply_text(analysis_text)
            else:
                await update.message.reply_text("❌ No se pudo analizar los datos. Intenta con un formato más claro.")
        else:
            await update.message.reply_text("❌ Gemini no está configurado para análisis avanzado.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error en análisis: {e}")

async def create_chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create chart based on previous analysis"""
    chat_id = update.effective_chat.id
    
    try:
        # obtener los últimos datos analizados para este usuario
        last_analysis = get_last_analyzed_data(chat_id)
        
        if not last_analysis:
            await update.message.reply_text(
                "❌ No hay datos analizados previos.\n\n"
                "📝 **Pasos para crear un gráfico:**\n"
                "1. Usa `/analyze [tus datos]` para analizar los datos\n"
                "2. Luego usa `/creargrafica` para generar el gráfico\n\n"
                "**Ejemplo:**\n"
                "`/analyze Hay 50 personas, 33 son niños y el resto son niñas`\n"
                "`/creargrafica`"
            )
            return
        
        await update.message.reply_text("🎨 Generando gráfico basado en el análisis previo...")
        
        # Create chart using the stored analysis
        chart_bytes, message = create_chart_from_text_data(
            last_analysis['values'], 
            last_analysis['chart_type'], 
            last_analysis['title']
        )
        
        if chart_bytes:
            # enviar el gráfico como foto
            await update.message.reply_photo(
                photo=io.BytesIO(chart_bytes),
                caption=f"📊 **{last_analysis['title']}**\n\n"
                       f"📈 **Tipo:** {last_analysis['chart_type'].title()}\n"
                       f"📊 **Datos:** {last_analysis['data_type']}\n\n"
                       f"💡 **Análisis:**\n{last_analysis['analysis']}"
            )
            
            # agregar creación de gráfico a memoria
            add_to_memory(chat_id, "assistant", f"Gráfico creado: {last_analysis['title']} ({last_analysis['chart_type']})")
            
        else:
            await update.message.reply_text(message if message else "❌ Error generando el gráfico. Intenta analizar los datos nuevamente.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error creando gráfico: {e}")
        print(f"Error in create_chart_command: {e}")

# comando /echo
async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # join args provided after /echo
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Uso: /echo <texto>")
        return

    chat_id = update.effective_chat.id
    add_to_memory(chat_id, "user", text)

    gemini_url = os.getenv("GEMINI_API_URL")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_url and gemini_key:
        try:
            response_text = await query_gemini_with_memory(text, chat_id, gemini_url, gemini_key)
        except Exception as e:
            response_text = f"Error al llamar a Gemini: {e}"
    else:
        response_text = text

    add_to_memory(chat_id, "assistant", response_text)
    await update.message.reply_text(response_text)

# comando /clear
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    clear_memory(chat_id)
    await update.message.reply_text("✅ Historial de conversación limpiado.")

# comando /audio_limit
async def audio_limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current audio character limit"""
    MAX_AUDIO_CHARS = int(os.getenv("MAX_AUDIO_CHARS", "1000"))
    
    current_limit = MAX_AUDIO_CHARS
    limit_info = f"""
🎵 **Configuración de Límite de Audio**

📊 **Límite actual:** {current_limit} caracteres

⏱️ **Duración aproximada:** ~{current_limit // 10} segundos

🔧 **Para cambiar el límite:**
1. Edita el archivo `.env`
2. Cambia `MAX_AUDIO_CHARS=tu_valor`
3. Reinicia el bot

📋 **Valores recomendados:**
• 500 - Respuestas cortas (~30s)
• 1000 - Respuestas medianas (~1min) ⭐
• 2000 - Respuestas largas (~2min)
• 3000 - Respuestas muy largas (~3min)
• 5000 - Máximo técnico (~5min)

⚠️ **Nota:** Valores muy altos pueden causar problemas de calidad.
"""
    
    await update.message.reply_text(limit_info)

async def set_audio_limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set audio character limit"""
    if not context.args:
        await update.message.reply_text("❌ Uso: /setaudiolimit <número>\nEjemplo: /setaudiolimit 2000")
        return
    
    try:
        new_limit = int(context.args[0])
        
        if new_limit < 100:
            await update.message.reply_text("❌ El límite mínimo es 100 caracteres")
            return
        
        if new_limit > 5000:
            await update.message.reply_text("❌ El límite máximo es 5000 caracteres")
            return
        
        # actualizar archivo .env
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('MAX_AUDIO_CHARS='):
                    lines[i] = f'MAX_AUDIO_CHARS={new_limit}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'MAX_AUDIO_CHARS={new_limit}\n')
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            await update.message.reply_text(f"✅ Límite de audio cambiado a {new_limit} caracteres\n\n🔄 Reinicia el bot para aplicar el cambio.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error actualizando configuración: {e}")
            
    except ValueError:
        await update.message.reply_text("❌ Por favor ingresa un número válido")

async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    memory = get_chat_memory(chat_id)
    
    if not memory:
        await update.message.reply_text("No hay historial de conversación.")
        return
    
    memory_text = "📝 Historial de conversación:\n\n"
    for i, msg in enumerate(memory[-10:], 1):  # mostrar últimos 10 mensajes
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        memory_text += f"{i}. {role_emoji} {msg['role']}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}\n"
    
    await update.message.reply_text(memory_text)


# respuesta a cualquier mensaje de texto
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # agregar mensaje del usuario a memoria
    add_to_memory(chat_id, "user", user_message)

    # verificar si el usuario está solicitando análisis desde Excel cargado
    if EXCEL_CHARTS_AVAILABLE and 'excel_sheets' in context.user_data:
        chart_keywords = ['gráfico', 'grafico', 'gráfica', 'grafica', 'chart', 'diagrama', 'barras', 'barra', 'circular', 'pie', 'torta', 'pastel', 'línea', 'linea', 'line', 'tendencia', 'dispersión', 'dispersion', 'scatter', 'puntos', 'histograma', 'histogram']
        
        # verificar solicitudes de gráficos
        if any(keyword in user_message.lower() for keyword in chart_keywords):
            try:
                await update.message.reply_text("📊 Generando gráfico desde Excel...")
                
                # detectar tipo de gráfico
                chart_type = detect_chart_type_from_text(user_message)
                
                # obtener información de hojas desde contexto
                sheets_info = context.user_data['excel_sheets']
                file_name = context.user_data.get('excel_file_name', 'archivo')
                
                # usar primera hoja
                selected_sheet = list(sheets_info.keys())[0]
                df = sheets_info[selected_sheet]['dataframe']
                
                # generar título
                title = f"Gráfico de {selected_sheet} - {chart_type.title()}"
                
                # crear gráfico (preferir plotly para mejor calidad)
                chart_bytes = create_plotly_chart(df, chart_type, title)
                if not chart_bytes:
                    chart_bytes = create_matplotlib_chart(df, chart_type, title)
                
                if chart_bytes:
                    await update.message.reply_photo(
                        photo=io.BytesIO(chart_bytes),
                        caption=f"📊 Gráfico generado desde {file_name} - Hoja: {selected_sheet}"
                    )
                    add_to_memory(chat_id, "assistant", f"Gráfico {chart_type} generado desde Excel")
                    return
                else:
                    await update.message.reply_text("❌ Error generando el gráfico")
                    return
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Error generando gráfico: {e}")
                return
        
        # verificar solicitudes de análisis matemático
        elif detect_mathematical_request(user_message):
            try:
                await update.message.reply_text("🔢 Realizando análisis matemático...")
                
                # obtener información de hojas desde contexto
                sheets_info = context.user_data['excel_sheets']
                file_name = context.user_data.get('excel_file_name', 'archivo')
                
                # usar primera hoja
                selected_sheet = list(sheets_info.keys())[0]
                df = sheets_info[selected_sheet]['dataframe']
                
                # extraer tipo de análisis y nombres de columnas
                available_columns = list(df.columns)
                found_columns = extract_column_names(user_message, available_columns)
                
                # determinar tipo de análisis
                analysis_type = "estadísticas"  # Default
                if any(word in user_message.lower() for word in ['suma', 'sum', 'total']):
                    analysis_type = "suma"
                elif any(word in user_message.lower() for word in ['promedio', 'average', 'mean']):
                    analysis_type = "promedio"
                elif any(word in user_message.lower() for word in ['mediana', 'median']):
                    analysis_type = "mediana"
                elif any(word in user_message.lower() for word in ['minimo', 'min', 'mínimo']):
                    analysis_type = "minimo"
                elif any(word in user_message.lower() for word in ['maximo', 'max', 'máximo']):
                    analysis_type = "maximo"
                elif any(word in user_message.lower() for word in ['estadisticas', 'stats', 'estadísticas']):
                    analysis_type = "estadisticas"
                elif any(word in user_message.lower() for word in ['correlacion', 'correlation']):
                    analysis_type = "correlacion"
                elif any(word in user_message.lower() for word in ['conteo', 'count']):
                    analysis_type = "conteo"
                elif any(word in user_message.lower() for word in ['desviacion', 'std']):
                    analysis_type = "desviacion"
                elif any(word in user_message.lower() for word in ['varianza', 'variance']):
                    analysis_type = "varianza"
                
                # realizar análisis
                column_name = found_columns[0] if found_columns else None
                column2_name = found_columns[1] if len(found_columns) > 1 else None
                
                result, error = perform_mathematical_analysis(df, analysis_type, column_name, column2_name)
                
                if result:
                    await update.message.reply_text(f"📊 **Análisis matemático de {file_name}**\n\n{result}")
                    add_to_memory(chat_id, "assistant", f"Análisis matemático {analysis_type} realizado")
                    return
                else:
                    await update.message.reply_text(f"❌ {error}")
                    return
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Error en análisis matemático: {e}")
                return
    
    # verificar si el usuario está solicitando un gráfico desde texto descriptivo (no Excel)
    elif EXCEL_CHARTS_AVAILABLE and detect_chart_request_from_text(user_message):
        try:
            await update.message.reply_text("🧠 Analizando datos con IA avanzada...")
            
            # extraer datos desde texto
            extracted_data, total_count = extract_data_from_text(user_message)
            
            if not extracted_data:
                await update.message.reply_text("❌ No pude extraer datos numéricos del texto. Asegúrate de incluir números y categorías.")
                return
            
            # usar Gemini para analizar los datos
            gemini_url = os.getenv("GEMINI_API_URL")
            gemini_key = os.getenv("GEMINI_API_KEY")
            
            if gemini_url and gemini_key:
                await update.message.reply_text("🔍 Gemini está analizando los patrones de datos...")
                
                # analizar con Gemini
                analysis = analyze_data_with_gemini(user_message, chat_id, gemini_url, gemini_key)
                
                if analysis and analysis['values']:
                    # usar análisis de Gemini para mejor generación de gráfico
                    extracted_data = analysis['values']
                    chart_type = analysis['chart_type']
                    title = analysis['title']
                    
                    # almacenar los datos analizados
                    store_analyzed_data(
                        chat_id, 
                        analysis['data_type'], 
                        analysis['categories'], 
                        analysis['values'], 
                        analysis['analysis']
                    )
                    
                    await update.message.reply_text(f"✅ **Análisis completado:**\n\n📊 **Tipo de datos:** {analysis['data_type']}\n🎯 **Gráfico recomendado:** {chart_type.title()}\n📈 **Título:** {title}\n\n🔍 **Análisis de patrones:**\n{analysis['analysis']}")
                else:
                        # por defecto: gráfico de torta
                    chart_type = "pie"
                    title = f"Distribución de {total_count} elementos" if total_count else "Gráfico de Datos"
                    analysis = {'analysis': 'Análisis básico realizado'}
            else:
                # por defecto: gráfico de torta
                chart_type = "pie"
                title = f"Distribución de {total_count} elementos" if total_count else "Gráfico de Datos"
                analysis = {'analysis': 'Análisis básico realizado'}
            
            # verificar si el usuario desea análisis avanzado o diagramas de flujo
            analysis_type = detect_analysis_type_from_text(user_message)
            
            if analysis_type in ['flow_diagram', 'sankey']:
                await update.message.reply_text("🔄 Generando diagrama de flujo...")
                chart_bytes, message = create_flow_diagram(extracted_data, title)
            elif analysis_type in ['correlation_matrix', 'distribution_analysis', 'outlier_detection', 'trend_analysis', 'comparative_analysis']:
                await update.message.reply_text(f"📈 Generando análisis {analysis_type}...")
                chart_bytes, message = create_advanced_analysis(extracted_data, analysis_type, title)
            else:
                # crear gráfico mejorado
                await update.message.reply_text("📊 Generando gráfico mejorado...")
                chart_bytes, message = create_chart_from_text_data(extracted_data, chart_type, title)
            
            if chart_bytes:
                # mejorar gráfico con análisis
                enhanced_chart_bytes = enhance_chart_with_analysis(chart_bytes, analysis, extracted_data)
                
                # mostrar resumen de datos procesados
                data_summary = "📊 **Datos procesados:**\n"
                for category, value in extracted_data.items():
                    percentage = (value / sum(extracted_data.values())) * 100
                    data_summary += f"• {category}: {value} ({percentage:.1f}%)\n"
                
                await update.message.reply_text(data_summary)
                
                # enviar gráfico mejorado
                chart_caption = f"📊 {analysis_type.replace('_', ' ').title()} generado con análisis de IA" if analysis_type != 'pie' else "📊 Gráfico inteligente generado con análisis de IA"
                await update.message.reply_photo(
                    photo=io.BytesIO(enhanced_chart_bytes),
                    caption=chart_caption
                )
                add_to_memory(chat_id, "assistant", f"Análisis {analysis_type} generado con análisis avanzado de Gemini")
                return
            else:
                await update.message.reply_text(f"❌ {message}")
                return
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error en análisis avanzado: {e}")
            return

    # si Gemini está configurado, enviar mensaje del usuario a Gemini
    gemini_url = os.getenv("GEMINI_API_URL")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if gemini_url and gemini_key:
        try:
            response_text = await query_gemini_with_memory(user_message, chat_id, gemini_url, gemini_key)
        except Exception as e:
            response_text = f"Error al llamar a Gemini: {e}"
    else:
        response_text = f"Recibí tu mensaje: {user_message}"

    # agregar respuesta del asistente a memoria
    add_to_memory(chat_id, "assistant", response_text)
    await update.message.reply_text(response_text)


# manejador para mensajes de voz
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages: transcribe, process with Gemini, and respond with audio"""
    if not VOICE_AVAILABLE:
        await update.message.reply_text("❌ Funcionalidad de voz no disponible. Error con las dependencias de audio.")
        return
        
    chat_id = update.effective_chat.id
    voice = update.message.voice
    
    # enviar mensaje de procesamiento
    processing_msg = await update.message.reply_text("🎤 Procesando mensaje de voz...")
    
    try:
        # crear directorio temporal para procesamiento de audio
        with tempfile.TemporaryDirectory() as temp_dir:
            ogg_path = os.path.join(temp_dir, "voice.ogg")
            wav_path = os.path.join(temp_dir, "voice.wav")
            
            # descargar archivo de voz
            success = await download_voice_file(voice.file_id, ogg_path, TOKEN)
            if not success:
                await processing_msg.edit_text("❌ Error descargando el archivo de voz")
                return
            
            # convertir formato de audio OGG a WAV
            await processing_msg.edit_text("🎤 Convirtiendo formato de audio...")
            success = convert_audio_format(ogg_path, wav_path)
            if not success:
                await processing_msg.edit_text("❌ Error convirtiendo el audio. Intentando transcripción directa...")
                # intentar transcribir archivo de voz original OGG directamente
                wav_path = ogg_path
            
            # transcribir audio
            await processing_msg.edit_text("🎤 Transcribiendo audio...")
            transcription, detected_language = transcribe_audio(wav_path)
            
            if not transcription or transcription == "No pude transcribir el audio. Por favor, intenta enviar un mensaje de texto.":
                await processing_msg.edit_text("❌ Error transcribiendo el audio. Usando transcripción alternativa...")
                # intentar transcribir audio con Google Speech Recognition directamente
                try:
                    import speech_recognition as sr
                    r = sr.Recognizer()
                    with sr.AudioFile(wav_path) as source:
                        audio = r.record(source)
                    transcription = r.recognize_google(audio, language='es-ES')
                    detected_language = 'es-ES'
                except Exception as e:
                    await processing_msg.edit_text("❌ No pude transcribir el audio. Por favor, intenta enviar un mensaje de texto.")
                    return
            
            # agregar transcripción a memoria
            add_to_memory(chat_id, "user", f"[VOZ] {transcription}")
            
            # obtener respuesta de Gemini
            await processing_msg.edit_text("🤖 Generando respuesta...")
            gemini_url = os.getenv("GEMINI_API_URL")
            gemini_key = os.getenv("GEMINI_API_KEY")
            
            if gemini_url and gemini_key:
                try:
                    response_text = await query_gemini_with_memory(transcription, chat_id, gemini_url, gemini_key)
                except Exception as e:
                    response_text = f"Error al llamar a Gemini: {e}"
            else:
                response_text = f"Transcripción: {transcription}"
            
            # agregar respuesta a memoria
            add_to_memory(chat_id, "assistant", response_text)
            
            # enviar respuesta de texto
            await processing_msg.edit_text(f"📝 **Transcripción:** {transcription}\n\n🤖 **Respuesta:** {response_text}")
            
                # generar y enviar respuesta de audio si está habilitado
            MAX_AUDIO_CHARS = int(os.getenv("MAX_AUDIO_CHARS", "5000"))  # límite configurable
            if AUDIO_RESPONSE_ENABLED and len(response_text) < MAX_AUDIO_CHARS:
                try:
                    await processing_msg.edit_text(f"📝 **Transcripción:** {transcription}\n\n🤖 **Respuesta:** {response_text}\n\n🎵 Generando respuesta en audio...")
                    
                    audio_file = generate_audio_response(response_text, detected_language)
                    if audio_file:
                        with open(audio_file, 'rb') as audio:
                            await update.message.reply_voice(
                                voice=audio,
                                caption="🎵 Respuesta en audio"
                            )
                            # limpiar archivo de audio temporal
                        os.unlink(audio_file)
                    else:
                        await update.message.reply_text("⚠️ No se pudo generar respuesta en audio")
                except Exception as e:
                    print(f"Error generating audio response: {e}")
                    await update.message.reply_text("⚠️ Error generando respuesta en audio")
            else:
                if not AUDIO_RESPONSE_ENABLED:
                    await update.message.reply_text("ℹ️ Respuesta en audio deshabilitada")
                else:
                    await update.message.reply_text("ℹ️ Respuesta muy larga para audio")
                    
    except Exception as e:
        print(f"Error processing voice message: {e}")
        await processing_msg.edit_text(f"❌ Error procesando mensaje de voz: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Excel document uploads and generate charts with robust file handling"""
    if not EXCEL_CHARTS_AVAILABLE:
        await update.message.reply_text("❌ Funcionalidad de Excel y gráficos no disponible. Error con las dependencias.")
        return
    
    chat_id = update.effective_chat.id
    document = update.message.document
    
    # verificar si es un archivo Excel
    if not document.file_name.lower().endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Por favor envía un archivo Excel (.xlsx o .xls)")
        return
    
    # enviar mensaje de procesamiento
    processing_msg = await update.message.reply_text("📊 Descargando archivo Excel...")
    
    try:
        # Descargar archivo directamente en memoria (evita problemas de bloqueo de archivos en Windows)
        file = await context.bot.get_file(document.file_id)
        
        # Descargar como bytes
        file_bytes = await file.download_as_bytearray()
        
        # Crear objeto BytesIO para leer en memoria
        file_buffer = io.BytesIO(file_bytes)
        
        # leer archivo Excel directamente desde memoria
        await processing_msg.edit_text("📊 Leyendo archivo Excel...")
        
        sheets_info = read_excel_file(file_buffer)
        
        if not sheets_info:
            await processing_msg.edit_text(
                "❌ Error leyendo el archivo Excel.\n\n"
                "💡 **Posibles causas:**\n"
                "• El archivo está corrupto\n"
                "• El archivo está protegido con contraseña\n"
                "• El formato no es compatible\n\n"
                "🔧 **Soluciones:**\n"
                "• Guarda el archivo como nuevo Excel (.xlsx)\n"
                "• Elimina la protección de contraseña si tiene\n"
                "• Intenta con un archivo más simple"
            )
            return
        
        # Realizar análisis completo de cada hoja
        await processing_msg.edit_text("📊 Analizando datos...")
        
        detailed_analysis = {}
        sheets_summary = []
        
        for name, info in sheets_info.items():
            df = info['dataframe']
            
            # Análisis completo de esta hoja
            analysis = get_comprehensive_data_analysis(df)
            detailed_analysis[name] = analysis
            
            # Resumen para mostrar al usuario
            numeric_cols = len(analysis['numeric_columns'])
            text_cols = len(analysis['text_columns'])
            date_cols = len(analysis['date_columns'])
            
            # Mostrar columnas numéricas encontradas
            num_cols_text = ", ".join(analysis['numeric_columns'][:3])
            if len(analysis['numeric_columns']) > 3:
                num_cols_text += f" (y {len(analysis['numeric_columns']) - 3} más)"
            
            sheet_info = f"📄 **{name}**\n"
            sheet_info += f"   • {info['shape'][0]} filas × {info['shape'][1]} columnas\n"
            sheet_info += f"   • {numeric_cols} numéricas"
            if num_cols_text:
                sheet_info += f": {num_cols_text}"
            sheet_info += f"\n   • {text_cols} de texto, {date_cols} de fecha"
            
            sheets_summary.append(sheet_info)
        
        sheets_text = "\n\n".join(sheets_summary)
        
        # Mensaje detallado para el usuario
        response_msg = (
            f"✅ **Archivo Excel procesado exitosamente!**\n\n"
            f"📋 **Análisis de hojas:**\n\n{sheets_text}\n\n"
            f"💡 **¿Qué puedo hacer ahora?**\n\n"
            f"📊 **Gráficos:**\n"
            f"   • \"crea un gráfico de barras\"\n"
            f"   • \"gráfico de líneas con [columna]\"\n"
            f"   • \"gráfico de dispersión entre X y Y\"\n"
            f"   • \"histograma de [columna]\"\n\n"
            f"🔢 **Análisis matemático:**\n"
            f"   • \"calcula la suma de [columna]\"\n"
            f"   • \"promedio y mediana de [columna]\"\n"
            f"   • \"estadísticas completas de [columna]\"\n"
            f"   • \"correlación entre [columna1] y [columna2]\"\n\n"
            f"📈 **Análisis avanzado:**\n"
            f"   • \"muestra las 10 filas con mayor [columna]\"\n"
            f"   • \"agrupa por [columna] y suma [otra columna]\"\n"
            f"   • \"encuentra valores atípicos en [columna]\""
        )
        
        await processing_msg.edit_text(response_msg)
        
        # almacenar información del archivo en contexto para uso posterior
        context.user_data['excel_sheets'] = sheets_info
        context.user_data['excel_analysis'] = detailed_analysis
        context.user_data['excel_file_name'] = document.file_name
        
        # Crear contexto detallado para Gemini
        data_context = f"ARCHIVO EXCEL CARGADO: {document.file_name}\n\n"
        for sheet_name, analysis in detailed_analysis.items():
            data_context += f"HOJA: {sheet_name}\n"
            data_context += f"- Total de filas: {analysis['total_rows']}\n"
            data_context += f"- Columnas totales: {analysis['total_columns']}\n"
            
            if analysis['numeric_columns']:
                data_context += f"- Columnas numéricas: {', '.join(analysis['numeric_columns'])}\n"
                for col in analysis['numeric_columns']:
                    stats = analysis['statistics'].get(col, {})
                    data_context += f"  * {col}: promedio={stats.get('mean', 0):.2f}, min={stats.get('min', 0):.2f}, max={stats.get('max', 0):.2f}, suma={stats.get('sum', 0):.2f}\n"
            
            if analysis['text_columns']:
                data_context += f"- Columnas de texto: {', '.join(analysis['text_columns'])}\n"
            
            if analysis['date_columns']:
                data_context += f"- Columnas de fecha: {', '.join(analysis['date_columns'])}\n"
            
            data_context += "\n"
        
        # agregar a memoria la información del archivo con contexto completo
        add_to_memory(chat_id, "user", f"[EXCEL] Subí archivo: {document.file_name}")
        add_to_memory(chat_id, "assistant", data_context)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error processing Excel file: {error_msg}")
        
        # Mensaje de error más específico
        if "password" in error_msg.lower() or "encrypted" in error_msg.lower():
            await processing_msg.edit_text(
                "❌ **Error: Archivo protegido**\n\n"
                "El archivo está protegido con contraseña.\n\n"
                "🔧 **Solución:**\n"
                "1. Abre el archivo en Excel\n"
                "2. Ve a Archivo > Información > Proteger libro\n"
                "3. Elimina la contraseña\n"
                "4. Guarda el archivo\n"
                "5. Intenta subirlo de nuevo"
            )
        else:
            await processing_msg.edit_text(
                f"❌ **Error procesando archivo Excel**\n\n"
                f"**Detalles:** `{error_msg[:150]}`\n\n"
                "💡 **Sugerencias:**\n"
                "• Verifica que el archivo no esté corrupto\n"
                "• Asegúrate de que no esté protegido con contraseña\n"
                "• Intenta con un archivo más pequeño (< 10MB)\n"
                "• Guarda el archivo como nuevo Excel (.xlsx)\n"
                "• Asegúrate de que sea un archivo Excel válido\n\n"
                "🔄 Intenta de nuevo o contacta soporte si el problema persiste."
            )

async def query_gemini_with_memory(prompt: str, chat_id: int, api_url: str, api_key: str, timeout: Optional[float] = 15.0) -> str:
    """Send prompt with conversation history to Gemini API and return the text response."""
    # obtener historial de conversación
    memory = get_chat_memory(chat_id)
    
    # agregar información de fecha y hora actual
    import pytz
    import locale
    
    # establecer locale para nombres de día y mes en español
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        except:
            pass  # usar valor por defecto si locale en español no está disponible
    
    # obtener hora actual en zona horaria (ajustar zona horaria según sea necesario)
    tz = pytz.timezone('America/Mexico_City')  # Change to your timezone
    current_time = datetime.now(tz)
    
    # formatear fecha y hora
    day_name = current_time.strftime('%A')
    date_str = current_time.strftime('%d de %B de %Y')
    time_str = current_time.strftime('%H:%M:%S')
    
    # construir contexto de conversación con fecha y hora actual
    conversation_parts = []
    
    # agregar contexto del sistema con fecha y hora actual
    time_context = f"INFORMACIÓN DEL SISTEMA: Hoy es {day_name}, {date_str}. La hora actual es {time_str} ({tz.zone}). Usa esta información para responder preguntas sobre la fecha y hora actuales."
    conversation_parts.append({"text": f"system: {time_context}"})
    
    # agregar contexto del perfil activo si existe
    # Primero intentar leer desde archivo de sincronización (tiempo real)
    profile_context = ""
    if os.path.exists("active_profile_context.txt"):
        try:
            with open("active_profile_context.txt", 'r', encoding='utf-8') as f:
                profile_context = f.read().strip()
        except Exception as e:
            print(f"Error leyendo contexto sincronizado: {e}")
    
    # Si no existe archivo, usar PROFILE_MANAGER
    if not profile_context and PROFILE_MANAGER:
        profile_context = PROFILE_MANAGER.get_active_profile_context()
    
    # Agregar contexto si existe
    if profile_context:
        conversation_parts.append({"text": f"profile_context: {profile_context}"})
    
    for msg in memory:
        if msg["role"] in ["user", "assistant"]:
            conversation_parts.append({"text": f"{msg['role']}: {msg['content']}"})
    
    # agregar prompt actual
    conversation_parts.append({"text": f"user: {prompt}"})
    
    # unir contexto de conversación
    full_context = "\n".join([part["text"] for part in conversation_parts])
    
    return await query_gemini(full_context, api_url, api_key, timeout)

async def query_gemini(prompt: str, api_url: str, api_key: str, timeout: Optional[float] = 15.0) -> str:
    """Send prompt to Gemini API and return the text response.

    This expects the Gemini endpoint to accept a JSON payload like {"input": "..."}
    and return a JSON with a `text` field. Adjust the payload parsing if your API
    differs.
    """
    # preparar headers y url dependiendo de si la API key debe pasarse como parámetro de consulta (común para API keys) o como token Bearer.
    # passed as a query parameter (common for API keys) o como token Bearer.
    headers = {"Content-Type": "application/json"}
    url = api_url

    # si un archivo JSON de cuenta de servicio está disponible en el entorno, preferir token OAuth Bearer
    sa_path = os.getenv("GEMINI_SA_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and os.path.exists(sa_path):
        # obtener un token de acceso con scope cloud-platform
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(GoogleRequest())
        token = creds.token
        headers["Authorization"] = f"Bearer {token}"
        # no agregar API key cuando se usa OAuth
        url = api_url
    else:
        # si la api_url no incluye ya un parámetro de API key, adjuntarlo para
        # servicios que esperan ?key=API_KEY (por ejemplo, algunos puntos finales de Google cuando se usan API keys).
        if api_key:
            if "key=" not in api_url:
                sep = "&" if "?" in api_url else "?"
                url = f"{api_url}{sep}key={api_key}"
            else:
                url = api_url
        else:
            url = api_url

        # si la url no contiene un parámetro de API key y la api_key parece
        # un token (cadena larga), aún intentamos establecerlo como Bearer en el encabezado de Authorization
        # encabezado en caso de que el servicio espere OAuth Bearer.
        if api_key and "key=" not in url:
            headers["Authorization"] = f"Bearer {api_key}"

    # si la api_url no incluye ya un parámetro de API key, adjuntarlo para
    # servicios que esperan ?key=API_KEY (por ejemplo, algunos puntos finales de Google cuando se usan API keys).
    if api_key:
        if "key=" not in api_url:
            sep = "&" if "?" in api_url else "?"
            url = f"{api_url}{sep}key={api_key}"
        else:
            url = api_url
    else:
        # no se proporcionó api_key: nada que agregar
        url = api_url

    # si la url no contiene un parámetro de API key y la api_key parece
    # un token (cadena larga), aún intentamos establecerlo como Bearer en el encabezado de Authorization
    # encabezado en caso de que el servicio espere OAuth Bearer.
    if api_key and "key=" not in url:
        headers["Authorization"] = f"Bearer {api_key}"

    # elegir payloads dependiendo de la familia del punto final.
    is_generate_content = (":generateContent" in url) or ("generativelanguage.googleapis.com" in url)
    is_vertex_predict = (":predict" in url) or ("aiplatform.googleapis.com" in url)

    if is_generate_content:
        # Gemini APIs de lenguaje generativo esperan `contents`
        payload_candidates = [
            {"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
        ]
    elif is_vertex_predict:
        # Vertex AI Predict-style espera `instances` con un array `content`
        payload_candidates = [
            {"instances": [{"content": [{"role": "user", "parts": [{"text": prompt}]}]}]},
        ]
    else:
        # intentar un conjunto más amplio (excluyendo las variantes problemáticas `input`)
        payload_candidates = [
            {"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
            {"prompt": {"text": prompt}},
            {"instances": [{"content": prompt}]},
            {"instances": [{"content": [{"type": "text", "text": prompt}]}]},
        ]

    async with httpx.AsyncClient(timeout=timeout) as client:
        last_exc = None
        for payload in payload_candidates:
            try:
                r = await client.post(url, json=payload, headers=headers)
                # si es exitoso (2xx), parsear y devolver
                if 200 <= r.status_code < 300:
                    try:
                        data = r.json()
                    except Exception:
                        return r.text

                    # parsear varias formas comunes de respuesta
                    if isinstance(data, dict):
                        # texto directo
                        if "text" in data:
                            return data["text"]
                        # salida anidada.text
                        if "output" in data and isinstance(data["output"], dict) and "text" in data["output"]:
                            return data["output"]["text"]
                        # Gemini candidates[].content.parts[].text (candidatos de Gemini)
                        if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
                            cand0 = data["candidates"][0]
                            if isinstance(cand0, dict):
                                # algunos endpoints devuelven texto de nivel superior
                                if "text" in cand0:
                                    return cand0["text"]
                                # lenguaje generativo: content.parts
                                content = cand0.get("content")
                                if isinstance(content, dict):
                                    parts = content.get("parts")
                                    if isinstance(parts, list) and parts:
                                        part0 = parts[0]
                                        if isinstance(part0, dict) and "text" in part0:
                                            return part0["text"]
                        # fallback stringify si la estructura es desconocida
                        return str(data)
                    return r.text
                else:
                    # registrar cuerpo de error para depuración, pero intentar siguiente payload
                    last_exc = (r.status_code, r.text)
            except Exception as e:
                last_exc = e

        # si llegamos aquí, todos los payloads fallaron; proporcionar error útil
        if isinstance(last_exc, tuple):
            status, body = last_exc
            raise RuntimeError(f"Request failed with status {status}: {body}")
        raise RuntimeError(f"Request failed: {last_exc}")

    # intentar varias formas comunes de respuesta
    if isinstance(data, dict):
        # común: {"text": "..."}
        if "text" in data:
            return data["text"]
        # otra forma común: {"output": {"text": "..."}}
        if "output" in data and isinstance(data["output"], dict) and "text" in data["output"]:
            return data["output"]["text"]
        # si la API devuelve una lista de fragmentos
        if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
            first = data["candidates"][0]
            if isinstance(first, dict) and "text" in first:
                return first["text"]

    # fallback: stringify toda la respuesta
    return str(data)


def main():
    # cargar memoria existente al inicio
    load_memory()
    
    app = ApplicationBuilder().token(TOKEN).build()

    # registrar manejadores
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("echo", echo_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("audiolimit", audio_limit_command))
    app.add_handler(CommandHandler("setaudiolimit", set_audio_limit_command))
    app.add_handler(CommandHandler("charthelp", chart_help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("creargrafica", create_chart_command))
    app.add_handler(CommandHandler("datahistory", data_history_command))
    app.add_handler(CommandHandler("cleardata", clear_data_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot con memoria en ejecución... presiona Ctrl+C para detenerlo.")

    # manejar cierre ordenado en Windows/UNIX signals
    def _stop(signum, frame):
        print("Deteniendo bot...")
        save_memory()  # guardar memoria antes de cerrar
        app.stop()

    try:
        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
    except Exception:
        # el manejo de señales puede estar limitado en algunas plataformas, ignorar si falla
        pass

    app.run_polling()


if __name__ == "__main__":
    main()
