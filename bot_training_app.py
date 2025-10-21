"""
Aplicación de Gestión y Entrenamiento del Chatbot
Interfaz gráfica para gestionar perfiles, versiones, documentos y contexto
CON AUTENTICACIÓN Y SINCRONIZACIÓN EN TIEMPO REAL
"""

import streamlit as st
import os
from profile_manager import ProfileManager
from datetime import datetime
import json
import hashlib
import time

# Configuración de página
st.set_page_config(
    page_title="Gestión del Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== SISTEMA DE AUTENTICACIÓN =====
AUTH_FILE = "auth_config.json"

def load_auth_config():
    """Cargar configuración de autenticación"""
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "users": {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
        },
        "settings": {
            "session_timeout_minutes": 60,
            "max_login_attempts": 3
        }
    }

def save_auth_config(config):
    """Guardar configuración de autenticación"""
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """Hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """Verificar credenciales de usuario"""
    auth_config = load_auth_config()
    if username in auth_config["users"]:
        stored_password = auth_config["users"][username]["password"]
        # Verificar si la contraseña ya está hasheada
        if len(stored_password) == 64:  # SHA256 hash length
            return stored_password == hash_password(password)
        else:
            # Contraseña en texto plano (primera vez)
            return stored_password == password
    return False

def login_page():
    """Página de login mejorada"""
    # Determinar modo
    dark_mode = st.session_state.get('dark_mode', True)
    
    if dark_mode:
        bg_gradient = "linear-gradient(135deg, #1E2130 0%, #0E1117 100%)"
        border_color = "#2D3748"
        text_color = "#FFFFFF"
        text_muted = "#B8C1D9"
        info_bg = "linear-gradient(135deg, #00D9FF20, #FF006E20)"
        info_border = "#00D9FF"
    else:
        bg_gradient = "linear-gradient(135deg, #F7F9FC 0%, #FFFFFF 100%)"
        border_color = "#E2E8F0"
        text_color = "#1A202C"
        text_muted = "#4B5563"
        info_bg = "linear-gradient(135deg, #0066CC15, #FF174415)"
        info_border = "#0066CC"
    
    # CSS específico para login
    st.markdown(f"""
    <style>
        .login-header {{
            text-align: center;
            padding: 3rem 0 2rem 0;
        }}
        .login-title {{
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00D9FF, #FF006E);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            animation: pulse 2s ease-in-out infinite;
            line-height: 1.2;
        }}
        .login-subtitle {{
            font-size: 1.5rem;
            color: {text_muted};
            font-weight: 300;
            letter-spacing: 0.02em;
        }}
        .login-container {{
            max-width: 500px;
            margin: 2rem auto;
            padding: 3rem;
            background: {bg_gradient};
            border: 2px solid {border_color};
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 217, 255, 0.2);
        }}
        .login-icon {{
            font-size: 5rem;
            text-align: center;
            margin-bottom: 2rem;
            animation: float 3s ease-in-out infinite;
            line-height: 1;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        .info-card {{
            background: {info_bg};
            border: 2px solid {info_border};
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        .info-card h4 {{
            color: {text_color} !important;
            margin-top: 0;
            font-size: 1.1rem;
        }}
        .info-card p {{
            color: {text_muted} !important;
            margin: 0.5rem 0;
            line-height: 1.6;
        }}
        .info-card strong {{
            color: {text_color} !important;
        }}
        .info-card code {{
            background: rgba(0, 217, 255, 0.15);
            color: #00D9FF !important;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-weight: 600;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="login-header">
        <div class="login-title" style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
            <span style="font-size: 3rem;">🤖</span>
            <span>Sistema de Gestión</span>
        </div>
        <div class="login-subtitle">Chatbot Inteligente con IA</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-icon">🔐</div>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; font-weight: 700; margin-top: 0;">✨ Acceso Seguro</h3>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario", label_visibility="visible")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingrese su contraseña", label_visibility="visible")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("🔓 Iniciar Sesión", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    if verify_credentials(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.login_time = time.time()
                        st.success("✅ Acceso concedido. Bienvenido!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.warning("⚠️ Por favor complete todos los campos")
        
        st.markdown("""
        <div class="info-card">
            <h4 style="margin-top: 0;">📝 Credenciales por defecto</h4>
            <p><strong>Usuario:</strong> <code>admin</code></p>
            <p><strong>Contraseña:</strong> <code>admin123</code></p>
            <p style="margin-bottom: 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Cambia la contraseña después del primer acceso</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><p style='text-align: center; opacity: 0.5; font-size: 0.9rem;'>v2.0.0 | Bot Training Manager</p>", unsafe_allow_html=True)

def check_session():
    """Verificar si la sesión es válida"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return False
    
    # Verificar timeout de sesión
    if 'login_time' in st.session_state:
        auth_config = load_auth_config()
        timeout_minutes = auth_config["settings"]["session_timeout_minutes"]
        elapsed_time = (time.time() - st.session_state.login_time) / 60
        
        if elapsed_time > timeout_minutes:
            st.session_state.authenticated = False
            return False
    
    return True

def logout():
    """Cerrar sesión"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.login_time = None
    st.rerun()

def sync_context_to_bot():
    """Sincronizar contexto del perfil activo al bot EN TIEMPO REAL"""
    try:
        pm = st.session_state.profile_manager
        context = pm.get_active_profile_context()
        
        # Guardar contexto en archivo que el bot lee
        with open("active_profile_context.txt", 'w', encoding='utf-8') as f:
            f.write(context)
        
        # También actualizar timestamp de sincronización
        sync_info = {
            "last_sync": datetime.now().isoformat(),
            "profile": pm.profiles.get("active_profile"),
            "context_length": len(context)
        }
        
        with open("sync_status.json", 'w', encoding='utf-8') as f:
            json.dump(sync_info, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Error sincronizando: {e}")
        return False

# Inicializar session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'profile_manager' not in st.session_state:
    st.session_state.profile_manager = ProfileManager()

if 'current_profile' not in st.session_state:
    st.session_state.current_profile = None

if 'current_version' not in st.session_state:
    st.session_state.current_version = None

if 'auto_sync' not in st.session_state:
    st.session_state.auto_sync = True

# Verificar autenticación
if not check_session():
    login_page()
    st.stop()

pm = st.session_state.profile_manager

# Sistema de Tema (Modo Oscuro/Claro)
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Modo oscuro por defecto

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# CSS personalizado mejorado con modo oscuro
dark_mode = st.session_state.dark_mode

if dark_mode:
    # MODO OSCURO
    primary_color = "#00D9FF"
    secondary_color = "#FF006E"
    bg_color = "#0E1117"
    card_bg = "#1E2130"
    text_color = "#FFFFFF"
    text_secondary = "#B8C1D9"
    text_muted = "#6B7280"
    border_color = "#2D3748"
    success_color = "#00FF88"
    warning_color = "#FFB020"
    error_color = "#FF4757"
    hover_bg = "#262B3D"
else:
    # MODO CLARO
    primary_color = "#0066CC"
    secondary_color = "#FF1744"
    bg_color = "#FFFFFF"
    card_bg = "#F7F9FC"
    text_color = "#1A202C"
    text_secondary = "#4B5563"
    text_muted = "#9CA3AF"
    border_color = "#E2E8F0"
    success_color = "#00C853"
    warning_color = "#FF9800"
    error_color = "#F44336"
    hover_bg = "#F3F4F6"

st.markdown(f"""
<style>
    /* Variables CSS */
    :root {{
        --primary-color: {primary_color};
        --secondary-color: {secondary_color};
        --bg-color: {bg_color};
        --card-bg: {card_bg};
        --text-color: {text_color};
        --text-secondary: {text_secondary};
        --text-muted: {text_muted};
        --border-color: {border_color};
        --success-color: {success_color};
        --warning-color: {warning_color};
        --error-color: {error_color};
        --hover-bg: {hover_bg};
    }}
    
    /* Fondo principal */
    .stApp {{
        background: linear-gradient(135deg, {bg_color} 0%, {card_bg} 100%);
        color: {text_color};
    }}
    
    /* Sidebar personalizado */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {card_bg} 0%, {bg_color} 100%);
        border-right: 2px solid {border_color};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    
    /* Títulos mejorados */
    h1 {{
        color: {text_color} !important;
        font-weight: 800;
        background: linear-gradient(90deg, {primary_color}, {secondary_color});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }}
    
    h2 {{
        color: {text_color} !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }}
    
    h3, h4, h5, h6 {{
        color: {text_secondary} !important;
        font-weight: 600;
    }}
    
    /* Texto normal */
    p, span, div, label {{
        color: {text_color};
    }}
    
    /* Texto secundario */
    .stCaption, small {{
        color: {text_muted} !important;
    }}
    
    /* Botones mejorados */
    .stButton>button {{
        width: 100%;
        border-radius: 12px;
        border: 2px solid {primary_color};
        background: linear-gradient(135deg, {primary_color}15, {secondary_color}15);
        color: {text_color} !important;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-size: 1rem;
        line-height: 1.5;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 217, 255, 0.3);
        border-color: {secondary_color};
        background: linear-gradient(135deg, {primary_color}30, {secondary_color}30);
    }}
    
    .stButton>button:active {{
        transform: translateY(0px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    /* Emojis en botones */
    .stButton>button::before {{
        margin-right: 0.5rem;
    }}
    
    /* Tarjetas (Expanders) */
    .streamlit-expanderHeader {{
        background: {card_bg} !important;
        border-radius: 12px;
        border: 2px solid {border_color};
        color: {text_color} !important;
        font-weight: 600;
        padding: 1rem 1.25rem;
        transition: all 0.3s ease;
        font-size: 1rem;
    }}
    
    .streamlit-expanderHeader:hover {{
        border-color: {primary_color};
        background: {hover_bg} !important;
        box-shadow: 0 4px 12px rgba(0, 217, 255, 0.2);
    }}
    
    .streamlit-expanderContent {{
        background: {card_bg};
        border: 2px solid {border_color};
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 1.5rem;
    }}
    
    /* Input fields mejorados */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {{
        background: {card_bg} !important;
        border: 2px solid {border_color} !important;
        border-radius: 10px;
        color: {text_color} !important;
        transition: all 0.3s ease;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem;
    }}
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus {{
        border-color: {primary_color} !important;
        box-shadow: 0 0 0 3px {primary_color}30;
        background: {hover_bg} !important;
    }}
    
    /* Labels de inputs */
    .stTextInput>label,
    .stTextArea>label,
    .stSelectbox>label {{
        color: {text_secondary} !important;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }}
    
    /* Métricas mejoradas */
    [data-testid="stMetricValue"] {{
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {text_color};
        font-weight: 600;
        font-size: 1.1rem;
    }}
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {card_bg};
        border-radius: 12px;
        padding: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: {text_color};
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        color: white;
    }}
    
    /* Success/Warning/Error boxes mejoradas */
    .success-box {{
        padding: 1.25rem 1.75rem;
        border-radius: 14px;
        background: linear-gradient(135deg, {success_color}25, {success_color}12);
        border: 2px solid {success_color};
        border-left: 5px solid {success_color};
        color: {success_color} !important;
        font-weight: 600;
        box-shadow: 0 4px 16px {success_color}25;
        animation: slideIn 0.3s ease-out;
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    .success-box * {{
        color: {success_color} !important;
    }}
    
    .warning-box {{
        padding: 1.25rem 1.75rem;
        border-radius: 14px;
        background: linear-gradient(135deg, {warning_color}25, {warning_color}12);
        border: 2px solid {warning_color};
        border-left: 5px solid {warning_color};
        color: {warning_color} !important;
        font-weight: 600;
        box-shadow: 0 4px 16px {warning_color}25;
        animation: slideIn 0.3s ease-out;
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    .warning-box * {{
        color: {warning_color} !important;
    }}
    
    .info-box {{
        padding: 1.25rem 1.75rem;
        border-radius: 14px;
        background: linear-gradient(135deg, {primary_color}25, {primary_color}12);
        border: 2px solid {primary_color};
        border-left: 5px solid {primary_color};
        color: {primary_color} !important;
        font-weight: 600;
        box-shadow: 0 4px 16px {primary_color}25;
        animation: slideIn 0.3s ease-out;
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    .info-box * {{
        color: {primary_color} !important;
    }}
    
    .error-box {{
        padding: 1.25rem 1.75rem;
        border-radius: 14px;
        background: linear-gradient(135deg, {error_color}25, {error_color}12);
        border: 2px solid {error_color};
        border-left: 5px solid {error_color};
        color: {error_color} !important;
        font-weight: 600;
        box-shadow: 0 4px 16px {error_color}25;
        animation: slideIn 0.3s ease-out;
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    .error-box * {{
        color: {error_color} !important;
    }}
    
    /* Radio buttons mejorados */
    .stRadio > div {{
        background: {card_bg};
        padding: 1rem;
        border-radius: 12px;
        border: 2px solid {border_color};
    }}
    
    /* Checkbox mejorado */
    .stCheckbox {{
        background: {card_bg};
        padding: 0.5rem;
        border-radius: 8px;
    }}
    
    /* Form mejorado */
    [data-testid="stForm"] {{
        background: {card_bg};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }}
    
    /* Animaciones */
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes pulse {{
        0%, 100% {{
            opacity: 1;
        }}
        50% {{
            opacity: 0.7;
        }}
    }}
    
    /* Badge/Label personalizado */
    .badge {{
        display: inline-block;
        padding: 0.5rem 1.2rem;
        border-radius: 24px;
        font-size: 0.9rem;
        font-weight: 700;
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        color: white !important;
        box-shadow: 0 3px 10px rgba(0, 217, 255, 0.35);
        letter-spacing: 0.02em;
        text-align: center;
    }}
    
    .badge-success {{
        background: linear-gradient(135deg, {success_color}, {success_color}DD);
        box-shadow: 0 3px 10px rgba(0, 255, 136, 0.35);
    }}
    
    .badge-warning {{
        background: linear-gradient(135deg, {warning_color}, {warning_color}DD);
        box-shadow: 0 3px 10px rgba(255, 176, 32, 0.35);
    }}
    
    /* Card personalizada */
    .custom-card {{
        background: {card_bg};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .custom-card:hover {{
        border-color: {primary_color};
        box-shadow: 0 8px 24px rgba(0, 217, 255, 0.15);
        transform: translateY(-3px);
    }}
    
    .custom-card h1, 
    .custom-card h2,
    .custom-card h3 {{
        margin-top: 0;
        line-height: 1.3;
    }}
    
    .custom-card p {{
        margin: 0.5rem 0;
        line-height: 1.6;
    }}
    
    /* Emoji spacing */
    .custom-card h1::first-letter,
    .custom-card h2::first-letter,
    .custom-card h3::first-letter {{
        margin-right: 0.3em;
    }}
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {{
        width: 14px;
        height: 14px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {bg_color};
        border-radius: 10px;
        margin: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, {primary_color}, {secondary_color});
        border-radius: 10px;
        border: 3px solid {bg_color};
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, {secondary_color}, {primary_color});
        border: 2px solid {bg_color};
    }}
    
    /* Loading spinner */
    .stSpinner > div {{
        border-color: {primary_color} !important;
    }}
    
    /* Placeholders */
    input::placeholder,
    textarea::placeholder {{
        color: {text_muted} !important;
        opacity: 0.7;
    }}
    
    /* Selectbox dropdown */
    [data-baseweb="select"] {{
        background: {card_bg} !important;
    }}
    
    [data-baseweb="select"] > div {{
        background: {card_bg} !important;
        border-color: {border_color} !important;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        background: {card_bg};
        border: 2px dashed {border_color};
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {primary_color};
        background: {hover_bg};
    }}
    
    /* Code blocks */
    code {{
        background: {card_bg} !important;
        color: {primary_color} !important;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-size: 0.9em;
        border: 1px solid {border_color};
    }}
    
    pre {{
        background: {card_bg} !important;
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 1rem;
    }}
    
    pre code {{
        border: none;
        padding: 0;
    }}
    
    /* Divider */
    hr {{
        border: none;
        border-top: 2px solid {border_color};
        margin: 2rem 0;
        opacity: 0.5;
    }}
    
    /* Links */
    a {{
        color: {primary_color} !important;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.2s ease;
    }}
    
    a:hover {{
        color: {secondary_color} !important;
        text-decoration: underline;
    }}
    
    /* Tooltips */
    [data-testid="stTooltipIcon"] {{
        color: {text_muted} !important;
    }}
    
    /* Success/Info/Warning/Error messages de Streamlit */
    .stSuccess {{
        background: linear-gradient(135deg, {success_color}20, {success_color}10) !important;
        border-left: 5px solid {success_color} !important;
        color: {text_color} !important;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, {primary_color}20, {primary_color}10) !important;
        border-left: 5px solid {primary_color} !important;
        color: {text_color} !important;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, {warning_color}20, {warning_color}10) !important;
        border-left: 5px solid {warning_color} !important;
        color: {text_color} !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, {error_color}20, {error_color}10) !important;
        border-left: 5px solid {error_color} !important;
        color: {text_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# Título principal mejorado
st.markdown(f"""
<div style="text-align: center; padding: 1.5rem 0 1rem 0;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
        <span style="font-size: 3rem;">🤖</span>
        <span>Sistema de Gestión del Chatbot</span>
    </h1>
    <p style="font-size: 1.2rem; color: {text_secondary}; margin-top: 0; font-weight: 500;">
        ✨ Entrenamiento y configuración con IA avanzada
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Navegación
with st.sidebar:
    # Modo oscuro toggle
    col_theme1, col_theme2 = st.columns([3, 1])
    with col_theme1:
        theme_text = "🌙 Modo Oscuro" if dark_mode else "☀️ Modo Claro"
        st.markdown(f"### {theme_text}")
    with col_theme2:
        if st.button("🔄", key="theme_toggle", use_container_width=True, help="Cambiar tema"):
            toggle_theme()
            st.rerun()
    
    st.markdown("---")
    
    # Usuario autenticado
    st.markdown(f"""
    <div class="custom-card" style="text-align: center; padding: 1.25rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">👤</div>
        <h3 style="margin: 0; color: {text_color} !important; font-weight: 700;">{st.session_state.username}</h3>
        <p style="margin: 0.5rem 0 0 0; color: {text_muted}; font-size: 0.9rem;">🎖️ Administrador</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪  Cerrar Sesión", use_container_width=True, type="primary"):
        logout()
    
    st.markdown("---")
    
    st.markdown(f'<h2 style="color: {text_color}; font-size: 1.5rem; margin-bottom: 1rem;">📋 Navegación</h2>', unsafe_allow_html=True)
    page = st.radio(
        "Selecciona una sección",
        ["🏠  Dashboard", "📊  Perfiles", "📝  Editor de Versiones", 
         "📚  Documentos", "🧠  Base de Conocimientos", "⚙️  Configuración"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Perfil activo global
    st.markdown(f'<h3 style="color: {text_color}; font-size: 1.2rem; margin-bottom: 1rem;">🎯 Perfil Activo Global</h3>', unsafe_allow_html=True)
    active = pm.get_active_profile()
    if active:
        st.markdown(f"""
        <div class="success-box" style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.5rem;">✅</span>
                <div>
                    <strong>{active['name']}</strong><br>
                    <small>Versión: {active['active_version']}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄  Desactivar", use_container_width=True):
            pm.profiles["active_profile"] = None
            pm._save_profiles()
            if st.session_state.auto_sync:
                sync_context_to_bot()
            st.rerun()
    else:
        st.info("⚠️ Sin perfil activo")
    
    st.markdown("---")
    
    # Estado de sincronización
    st.markdown(f'<h3 style="color: {text_color}; font-size: 1.2rem; margin-bottom: 1rem;">🔄 Sincronización</h3>', unsafe_allow_html=True)
    auto_sync = st.checkbox("⚡ Auto-sync en tiempo real", value=st.session_state.auto_sync)
    st.session_state.auto_sync = auto_sync
    
    if os.path.exists("sync_status.json"):
        with open("sync_status.json", 'r') as f:
            sync_info = json.load(f)
        last_sync = datetime.fromisoformat(sync_info["last_sync"]).strftime("%H:%M:%S")
        st.caption(f"🕒 Última sync: {last_sync}")
    
    if st.button("🔄  Sincronizar Manual", use_container_width=True, type="secondary"):
        if sync_context_to_bot():
            st.success("✅ Sincronizado")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    st.caption("v2.0.0 - Bot Training Manager")

# ===== PÁGINA: DASHBOARD =====
if page == "🏠  Dashboard":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>📊</span><span>Dashboard General</span></h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Métricas mejoradas
    col1, col2, col3, col4 = st.columns(4)
    
    total_profiles = pm.profiles["metadata"]["total_profiles"]
    active_profile = pm.get_active_profile()
    
    with col1:
        st.markdown(f"""
        <div class="custom-card" style="text-align: center;">
            <p style="margin: 0; opacity: 0.7; font-size: 0.9rem;">Total Perfiles</p>
            <h1 style="margin: 0.5rem 0; font-size: 3rem;">{total_profiles}</h1>
            <p style="margin: 0; opacity: 0.6; font-size: 0.8rem;">📁 Configurados</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active_name = active_profile['name'] if active_profile else "Ninguno"
        badge_class = "badge-success" if active_profile else "badge-warning"
        st.markdown(f"""
        <div class="custom-card" style="text-align: center;">
            <p style="margin: 0; opacity: 0.7; font-size: 0.9rem;">Perfil Activo</p>
            <div style="margin: 1rem 0;">
                <span class="badge {badge_class}">{active_name[:15]}</span>
            </div>
            <p style="margin: 0; opacity: 0.6; font-size: 0.8rem;">🎯 En uso</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_versions = sum(len(p["versions"]) for p in pm.get_all_profiles().values()) if pm.get_all_profiles() else 0
        st.markdown(f"""
        <div class="custom-card" style="text-align: center;">
            <p style="margin: 0; opacity: 0.7; font-size: 0.9rem;">Total Versiones</p>
            <h1 style="margin: 0.5rem 0; font-size: 3rem;">{total_versions}</h1>
            <p style="margin: 0; opacity: 0.6; font-size: 0.8rem;">📝 Guardadas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        last_modified = pm.profiles["metadata"].get("last_modified", "N/A")
        if last_modified != "N/A":
            last_modified_dt = datetime.fromisoformat(last_modified)
            last_modified_str = last_modified_dt.strftime("%d/%m %H:%M")
        else:
            last_modified_str = "N/A"
        st.markdown(f"""
        <div class="custom-card" style="text-align: center;">
            <p style="margin: 0; opacity: 0.7; font-size: 0.9rem;">Última Modificación</p>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">{last_modified_str}</h2>
            <p style="margin: 0; opacity: 0.6; font-size: 0.8rem;">🕒 Actualizado</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Lista de perfiles
    st.subheader("📋 Perfiles Recientes")
    
    profiles = pm.get_all_profiles()
    if profiles:
        for profile_name, profile_data in list(profiles.items())[:5]:
            with st.expander(f"📁 {profile_name} ({profile_data['type']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Descripción:** {profile_data.get('description', 'Sin descripción')}")
                    st.write(f"**Versiones:** {len(profile_data['versions'])}")
                    st.write(f"**Versión Activa:** v{profile_data['active_version']}")
                with col2:
                    if st.button("✏️ Editar", key=f"edit_{profile_name}"):
                        st.session_state.current_profile = profile_name
                        st.session_state.current_version = profile_data['active_version']
                        st.info("Cambia a la pestaña 'Perfiles' para editar")
    else:
        st.info("No hay perfiles creados aún. ¡Crea tu primer perfil en la sección de Perfiles!")

# ===== PÁGINA: PERFILES =====
elif page == "📊  Perfiles":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>📊</span><span>Gestión de Perfiles</span></h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Crear Perfil", "📋 Listar Perfiles", "📥 Importar/Exportar"])
    
    # TAB: Crear Perfil
    with tab1:
        st.subheader("Crear Nuevo Perfil")
        
        with st.form("create_profile_form"):
            profile_name = st.text_input("Nombre del Perfil *", placeholder="ej: Asistente Médico")
            profile_desc = st.text_area("Descripción", placeholder="Describe el propósito de este perfil")
            profile_type = st.selectbox(
                "Tipo de Perfil",
                ["general", "asistente", "desarrollo", "soporte", "ventas", "educación", "personalizado"]
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                submitted = st.form_submit_button("✅ Crear Perfil", use_container_width=True)
            
            if submitted:
                if not profile_name:
                    st.error("❌ El nombre del perfil es obligatorio")
                else:
                    try:
                        pm.create_profile(profile_name, profile_desc, profile_type)
                        if st.session_state.auto_sync:
                            sync_context_to_bot()
                        st.success(f"✅ Perfil '{profile_name}' creado exitosamente")
                        st.balloons()
                    except ValueError as e:
                        st.error(f"❌ Error: {e}")
    
    # TAB: Listar Perfiles
    with tab2:
        st.subheader("Perfiles Existentes")
        
        profiles = pm.get_all_profiles()
        
        if not profiles:
            st.info("No hay perfiles creados aún")
        else:
            # Filtros
            col1, col2 = st.columns([3, 1])
            with col1:
                search = st.text_input("🔍 Buscar perfil", "")
            with col2:
                filter_type = st.selectbox("Filtrar por tipo", ["Todos"] + ["general", "asistente", "desarrollo", "soporte", "ventas", "educación", "personalizado"])
            
            # Filtrar perfiles
            filtered_profiles = profiles
            if search:
                filtered_profiles = {k: v for k, v in profiles.items() if search.lower() in k.lower()}
            if filter_type != "Todos":
                filtered_profiles = {k: v for k, v in filtered_profiles.items() if v['type'] == filter_type}
            
            for profile_name, profile_data in filtered_profiles.items():
                with st.expander(f"{'🟢' if pm.profiles['active_profile'] == profile_name else '⚪'} {profile_name}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**ID:** {profile_data['id']}")
                        st.write(f"**Tipo:** {profile_data['type']}")
                        st.write(f"**Descripción:** {profile_data.get('description', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Versiones:** {len(profile_data['versions'])}")
                        st.write(f"**Versión Activa:** v{profile_data['active_version']}")
                        created = datetime.fromisoformat(profile_data['created_at']).strftime("%d/%m/%Y %H:%M")
                        st.write(f"**Creado:** {created}")
                    
                    with col3:
                        if st.button("🎯 Activar", key=f"activate_{profile_name}", use_container_width=True):
                            pm.set_active_profile(profile_name)
                            if st.session_state.auto_sync:
                                sync_context_to_bot()
                            st.success(f"✅ Perfil '{profile_name}' activado y sincronizado")
                            st.rerun()
                        
                        if st.button("✏️ Editar", key=f"edit_prof_{profile_name}", use_container_width=True):
                            st.session_state.current_profile = profile_name
                            st.session_state.current_version = profile_data['active_version']
                            st.info("👉 Ve a la pestaña 'Editor de Versiones'")
                        
                        if st.button("🗑️ Eliminar", key=f"delete_{profile_name}", use_container_width=True):
                            if st.session_state.get(f"confirm_delete_{profile_name}"):
                                pm.delete_profile(profile_name)
                                st.success(f"✅ Perfil eliminado")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_delete_{profile_name}"] = True
                                st.warning("⚠️ Haz clic de nuevo para confirmar")
    
    # TAB: Importar/Exportar
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📤 Exportar Perfil")
            export_profile = st.selectbox("Selecciona perfil para exportar", list(pm.get_all_profiles().keys()) if pm.get_all_profiles() else [])
            
            if export_profile:
                export_filename = st.text_input("Nombre del archivo", f"{export_profile}.json")
                if st.button("📤 Exportar"):
                    try:
                        pm.export_profile(export_profile, export_filename)
                        st.success(f"✅ Perfil exportado a '{export_filename}'")
                        
                        # Ofrecer descarga
                        profile_data = pm.get_profile(export_profile)
                        st.download_button(
                            "⬇️ Descargar archivo",
                            json.dumps(profile_data, ensure_ascii=False, indent=2),
                            file_name=export_filename,
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"❌ Error exportando: {e}")
        
        with col2:
            st.subheader("📥 Importar Perfil")
            uploaded_file = st.file_uploader("Selecciona archivo JSON", type=['json'])
            
            if uploaded_file:
                if st.button("📥 Importar"):
                    try:
                        # Guardar temporalmente
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        
                        # Importar
                        imported_name = pm.import_profile(temp_path)
                        
                        # Limpiar archivo temporal
                        os.remove(temp_path)
                        
                        if imported_name:
                            st.success(f"✅ Perfil importado como '{imported_name}'")
                            st.balloons()
                        else:
                            st.error("❌ Error al importar el perfil")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

# ===== PÁGINA: EDITOR DE VERSIONES =====
elif page == "📝  Editor de Versiones":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>📝</span><span>Editor de Versiones</span></h2>', unsafe_allow_html=True)
    
    profiles = pm.get_all_profiles()
    
    if not profiles:
        st.warning("⚠️ No hay perfiles creados. Crea uno en la sección de Perfiles.")
    else:
        # Seleccionar perfil y versión
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "Selecciona Perfil",
                list(profiles.keys()),
                index=list(profiles.keys()).index(st.session_state.current_profile) if st.session_state.current_profile in profiles else 0
            )
        
        if selected_profile:
            profile_data = pm.get_profile(selected_profile)
            versions = list(profile_data["versions"].keys())
            
            with col2:
                selected_version = st.selectbox(
                    "Selecciona Versión",
                    versions,
                    index=versions.index(str(profile_data["active_version"]))
                )
            
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Nueva Versión", use_container_width=True):
                    new_v = pm.create_version(selected_profile)
                    st.success(f"✅ Versión {new_v} creada")
                    st.rerun()
            
            version_data = pm.get_version(selected_profile, int(selected_version))
            
            if version_data:
                st.markdown("---")
                
                # Tabs para diferentes secciones
                tab1, tab2, tab3, tab4 = st.tabs(["📄 Contenido Principal", "📋 Instrucciones", "💡 Ejemplos", "🚫 Restricciones"])
                
                # TAB: Contenido Principal
                with tab1:
                    with st.form("content_form"):
                        system_prompt = st.text_area(
                            "System Prompt",
                            value=version_data.get("system_prompt", ""),
                            height=150,
                            help="Prompt del sistema que define el comportamiento base del bot"
                        )
                        
                        context = st.text_area(
                            "Contexto General",
                            value=version_data.get("context", ""),
                            height=200,
                            help="Contexto general que el bot debe conocer"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            tone = st.selectbox(
                                "Tono de Comunicación",
                                ["profesional", "amigable", "formal", "casual", "técnico", "empático"],
                                index=["profesional", "amigable", "formal", "casual", "técnico", "empático"].index(version_data.get("tone", "profesional"))
                            )
                        
                        with col2:
                            language = st.selectbox(
                                "Idioma Principal",
                                ["español", "inglés", "portugués", "francés", "alemán", "italiano"],
                                index=["español", "inglés", "portugués", "francés", "alemán", "italiano"].index(version_data.get("language", "español"))
                            )
                        
                        if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                            pm.update_version_content(
                                selected_profile,
                                int(selected_version),
                                system_prompt=system_prompt,
                                context=context,
                                tone=tone,
                                language=language
                            )
                            if st.session_state.auto_sync:
                                sync_context_to_bot()
                            st.success("✅ Contenido actualizado y sincronizado")
                            st.rerun()
                
                # TAB: Instrucciones
                with tab2:
                    st.subheader("Instrucciones para el Bot")
                    
                    instructions = version_data.get("instructions", [])
                    
                    # Mostrar instrucciones existentes
                    for idx, instruction in enumerate(instructions):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.text(f"{idx + 1}. {instruction}")
                        with col2:
                            if st.button("🗑️", key=f"del_inst_{idx}"):
                                instructions.pop(idx)
                                pm.update_version_content(selected_profile, int(selected_version), instructions=instructions)
                                st.rerun()
                    
                    # Agregar nueva instrucción
                    new_instruction = st.text_input("Nueva instrucción")
                    if st.button("➕ Agregar Instrucción"):
                        if new_instruction:
                            instructions.append(new_instruction)
                            pm.update_version_content(selected_profile, int(selected_version), instructions=instructions)
                            st.success("✅ Instrucción agregada")
                            st.rerun()
                
                # TAB: Ejemplos
                with tab3:
                    st.subheader("Ejemplos de Conversación")
                    
                    examples = version_data.get("examples", [])
                    
                    for idx, example in enumerate(examples):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.text_area(f"Ejemplo {idx + 1}", value=example, height=80, disabled=True, key=f"ex_{idx}")
                        with col2:
                            st.write("")
                            st.write("")
                            if st.button("🗑️", key=f"del_ex_{idx}"):
                                examples.pop(idx)
                                pm.update_version_content(selected_profile, int(selected_version), examples=examples)
                                st.rerun()
                    
                    new_example = st.text_area("Nuevo ejemplo de conversación")
                    if st.button("➕ Agregar Ejemplo"):
                        if new_example:
                            examples.append(new_example)
                            pm.update_version_content(selected_profile, int(selected_version), examples=examples)
                            st.success("✅ Ejemplo agregado")
                            st.rerun()
                
                # TAB: Restricciones
                with tab4:
                    st.subheader("Restricciones y Limitaciones")
                    
                    restrictions = version_data.get("restrictions", [])
                    
                    for idx, restriction in enumerate(restrictions):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.text(f"• {restriction}")
                        with col2:
                            if st.button("🗑️", key=f"del_rest_{idx}"):
                                restrictions.pop(idx)
                                pm.update_version_content(selected_profile, int(selected_version), restrictions=restrictions)
                                st.rerun()
                    
                    new_restriction = st.text_input("Nueva restricción")
                    if st.button("➕ Agregar Restricción"):
                        if new_restriction:
                            restrictions.append(new_restriction)
                            pm.update_version_content(selected_profile, int(selected_version), restrictions=restrictions)
                            st.success("✅ Restricción agregada")
                            st.rerun()
                
                st.markdown("---")
                
                # Acciones de versión
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🎯 Activar esta versión", use_container_width=True):
                        pm.activate_version(selected_profile, int(selected_version))
                        st.success(f"✅ Versión {selected_version} activada")
                        st.rerun()
                
                with col2:
                    if int(selected_version) != profile_data["active_version"] and len(versions) > 1:
                        if st.button("🗑️ Eliminar versión", use_container_width=True):
                            try:
                                pm.delete_version(selected_profile, int(selected_version))
                                st.success("✅ Versión eliminada")
                                st.rerun()
                            except ValueError as e:
                                st.error(f"❌ {e}")

# ===== PÁGINA: DOCUMENTOS =====
elif page == "📚  Documentos":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>📚</span><span>Gestión de Documentos</span></h2>', unsafe_allow_html=True)
    
    profiles = pm.get_all_profiles()
    
    if not profiles:
        st.warning("⚠️ No hay perfiles creados")
    else:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            selected_profile = st.selectbox("Selecciona Perfil", list(profiles.keys()))
        
        if selected_profile:
            profile_data = pm.get_profile(selected_profile)
            versions = list(profile_data["versions"].keys())
            
            with col2:
                selected_version = st.selectbox("Selecciona Versión", versions)
            
            version_data = pm.get_version(selected_profile, int(selected_version))
            
            if version_data:
                tab1, tab2 = st.tabs(["📋 Documentos Existentes", "➕ Agregar Documento"])
                
                # TAB: Documentos existentes
                with tab1:
                    documents = version_data.get("documents", [])
                    
                    if not documents:
                        st.info("No hay documentos en esta versión")
                    else:
                        for idx, doc in enumerate(documents):
                            with st.expander(f"📄 {doc['name']}"):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**Tipo:** {doc['type']}")
                                    added = datetime.fromisoformat(doc['added_at']).strftime("%d/%m/%Y %H:%M")
                                    st.write(f"**Agregado:** {added}")
                                    st.text_area("Contenido", value=doc['content'], height=200, disabled=True, key=f"doc_{idx}")
                                
                                with col2:
                                    if st.button("🗑️ Eliminar", key=f"del_doc_{idx}"):
                                        pm.remove_document(selected_profile, int(selected_version), idx)
                                        st.success("✅ Documento eliminado")
                                        st.rerun()
                
                # TAB: Agregar documento
                with tab2:
                    with st.form("add_document_form"):
                        doc_name = st.text_input("Nombre del Documento")
                        doc_type = st.selectbox("Tipo", ["text", "manual", "FAQ", "guía", "política", "procedimiento"])
                        doc_content = st.text_area("Contenido del Documento", height=300)
                        
                        # Opción de cargar archivo
                        uploaded_doc = st.file_uploader("O cargar desde archivo (.txt, .md)", type=['txt', 'md'])
                        
                        if st.form_submit_button("➕ Agregar Documento"):
                            content = doc_content
                            
                            if uploaded_doc:
                                content = uploaded_doc.getvalue().decode('utf-8')
                            
                            if doc_name and content:
                                pm.add_document(selected_profile, int(selected_version), doc_name, content, doc_type)
                                st.success(f"✅ Documento '{doc_name}' agregado")
                                st.rerun()
                            else:
                                st.error("❌ Completa todos los campos")

# ===== PÁGINA: BASE DE CONOCIMIENTOS =====
elif page == "🧠  Base de Conocimientos":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>🧠</span><span>Base de Conocimientos</span></h2>', unsafe_allow_html=True)
    
    profiles = pm.get_all_profiles()
    
    if not profiles:
        st.warning("⚠️ No hay perfiles creados")
    else:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            selected_profile = st.selectbox("Selecciona Perfil", list(profiles.keys()))
        
        if selected_profile:
            profile_data = pm.get_profile(selected_profile)
            versions = list(profile_data["versions"].keys())
            
            with col2:
                selected_version = st.selectbox("Selecciona Versión", versions)
            
            version_data = pm.get_version(selected_profile, int(selected_version))
            
            if version_data:
                knowledge_base = version_data.get("knowledge_base", {})
                
                tab1, tab2 = st.tabs(["📖 Conocimientos Existentes", "➕ Agregar Conocimiento"])
                
                # TAB: Conocimientos existentes
                with tab1:
                    if not knowledge_base:
                        st.info("La base de conocimientos está vacía")
                    else:
                        for key, data in knowledge_base.items():
                            with st.expander(f"💡 {key}"):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**Valor:** {data['value']}")
                                    added = datetime.fromisoformat(data['added_at']).strftime("%d/%m/%Y %H:%M")
                                    st.write(f"**Agregado:** {added}")
                                
                                with col2:
                                    if st.button("🗑️ Eliminar", key=f"del_kb_{key}"):
                                        del knowledge_base[key]
                                        pm.update_version_content(selected_profile, int(selected_version), knowledge_base=knowledge_base)
                                        st.success("✅ Conocimiento eliminado")
                                        st.rerun()
                
                # TAB: Agregar conocimiento
                with tab2:
                    with st.form("add_knowledge_form"):
                        kb_key = st.text_input("Clave/Concepto", placeholder="ej: horario_atencion")
                        kb_value = st.text_area("Valor/Definición", placeholder="ej: Lunes a Viernes de 9:00 a 18:00")
                        
                        if st.form_submit_button("➕ Agregar Conocimiento"):
                            if kb_key and kb_value:
                                pm.add_to_knowledge_base(selected_profile, int(selected_version), kb_key, kb_value)
                                st.success(f"✅ Conocimiento '{kb_key}' agregado")
                                st.rerun()
                            else:
                                st.error("❌ Completa todos los campos")

# ===== PÁGINA: CONFIGURACIÓN =====
elif page == "⚙️  Configuración":
    st.markdown(f'<h2 style="color: {text_color}; display: flex; align-items: center; gap: 0.5rem;"><span>⚙️</span><span>Configuración del Sistema</span></h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔧 General", "👁️ Vista Previa", "🔄 Sincronización"])
    
    with tab1:
        st.subheader("Configuración General")
        
        # Archivo de perfiles
        st.write(f"**Archivo de perfiles:** `{pm.profiles_file}`")
        st.write(f"**Total de perfiles:** {pm.profiles['metadata']['total_profiles']}")
        
        created = datetime.fromisoformat(pm.profiles['metadata']['created_at']).strftime("%d/%m/%Y %H:%M")
        st.write(f"**Sistema creado:** {created}")
        
        modified = datetime.fromisoformat(pm.profiles['metadata']['last_modified']).strftime("%d/%m/%Y %H:%M")
        st.write(f"**Última modificación:** {modified}")
        
        st.markdown("---")
        
        if st.button("🔄 Recargar Perfiles desde Archivo"):
            st.session_state.profile_manager = ProfileManager()
            st.success("✅ Perfiles recargados")
            st.rerun()
        
        if st.button("💾 Forzar Guardado"):
            pm._save_profiles()
            st.success("✅ Perfiles guardados")
    
    with tab2:
        st.subheader("Vista Previa del Contexto Activo")
        
        context = pm.get_active_profile_context()
        
        if context:
            st.text_area("Contexto completo que se enviará al bot:", value=context, height=400)
            
            st.download_button(
                "⬇️ Descargar Contexto",
                context,
                file_name="bot_context.txt",
                mime="text/plain"
            )
        else:
            st.info("No hay perfil activo para mostrar")
    
    with tab3:
        st.subheader("Sincronización con el Bot")
        
        st.info("""
        El bot principal lee el contexto del perfil activo automáticamente.
        Asegúrate de:
        1. Activar un perfil antes de usar el bot
        2. Seleccionar la versión correcta
        3. Guardar todos los cambios antes de probar
        """)
        
        if st.button("🔄 Sincronizar Ahora"):
            context = pm.get_active_profile_context()
            # Guardar contexto en archivo que el bot pueda leer
            with open("active_profile_context.txt", 'w', encoding='utf-8') as f:
                f.write(context)
            st.success("✅ Contexto sincronizado con el bot")

# Footer
st.markdown("---")
st.caption("🤖 Sistema de Gestión del Chatbot | Desarrollado por Luis Baptista")

