# 🤖 Sistema de Gestión y Entrenamiento del Chatbot

## 📋 Descripción

Aplicación web completa para gestionar, entrenar y configurar el chatbot de Telegram. Permite crear múltiples perfiles con diferentes personalidades y versiones, gestionar documentos, contexto y base de conocimientos.

## ✨ Características

### 🎯 Gestión de Perfiles
- Crear múltiples perfiles (Asistente, Desarrollo, Soporte, Ventas, etc.)
- Activar/desactivar perfiles globalmente
- Exportar e importar perfiles
- Tipos de perfil: general, asistente, desarrollo, soporte, ventas, educación, personalizado

### 📝 Sistema de Versionamiento
- Crear múltiples versiones de cada perfil
- Activar versiones específicas
- Eliminar versiones (excepto la activa)
- Copiar contenido entre versiones
- Historial completo de cambios

### 📚 Gestión de Documentos
- Cargar documentos de texto (.txt, .md)
- Agregar manuales, FAQs, guías, políticas
- Organizar por tipo de documento
- Eliminar y modificar documentos

### 🧠 Base de Conocimientos
- Agregar pares clave-valor
- Información estructurada
- Fácil acceso y modificación
- Versionamiento de conocimientos

### 📄 Configuración de Contenido
- **System Prompt**: Define el comportamiento base
- **Contexto General**: Información de fondo
- **Instrucciones**: Lista de directrices
- **Ejemplos**: Casos de uso y conversaciones ejemplo
- **Restricciones**: Limitaciones y prohibiciones
- **Tono**: profesional, amigable, formal, casual, técnico, empático
- **Idioma**: español, inglés, portugués, francés, alemán, italiano

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install streamlit>=1.28.0
```

O desde requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
streamlit run bot_training_app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📖 Uso

### Crear un Nuevo Perfil

1. Ve a la sección **"📊 Perfiles"**
2. Pestaña **"📝 Crear Perfil"**
3. Completa:
   - Nombre del perfil
   - Descripción
   - Tipo de perfil
4. Click en **"✅ Crear Perfil"**

### Editar una Versión

1. Ve a **"📝 Editor de Versiones"**
2. Selecciona el perfil y versión
3. Edita en las pestañas:
   - **Contenido Principal**: System prompt, contexto, tono, idioma
   - **Instrucciones**: Directrices para el bot
   - **Ejemplos**: Ejemplos de conversaciones
   - **Restricciones**: Lo que NO debe hacer

### Agregar Documentos

1. Ve a **"📚 Documentos"**
2. Selecciona perfil y versión
3. Pestaña **"➕ Agregar Documento"**
4. Completa nombre, tipo y contenido
5. O carga un archivo .txt o .md

### Gestionar Conocimientos

1. Ve a **"🧠 Base de Conocimientos"**
2. Agrega pares clave-valor
3. Ejemplo:
   - Clave: `horario_atencion`
   - Valor: `Lunes a Viernes de 9:00 a 18:00`

### Activar un Perfil

1. Ve a **"📊 Perfiles" → "📋 Listar Perfiles"**
2. Encuentra tu perfil
3. Click en **"🎯 Activar"**

El perfil activo se usará automáticamente en el bot.

## 🔄 Integración con el Bot

El bot de Telegram lee automáticamente el contexto del perfil activo. Cuando cambias un perfil:

1. El sistema genera el contexto completo
2. El bot lo incluye en cada conversación
3. Gemini responde según el perfil configurado

### Sincronización

El contexto se sincroniza automáticamente. También puedes:

1. Ir a **"⚙️ Configuración" → "🔄 Sincronización"**
2. Click en **"🔄 Sincronizar Ahora"**
3. Ver vista previa del contexto en **"👁️ Vista Previa"**

## 📊 Estructura de Datos

### Archivo de Perfiles

Los perfiles se guardan en `bot_profiles.json`:

```json
{
  "profiles": {
    "Nombre del Perfil": {
      "id": "abc123",
      "name": "Nombre del Perfil",
      "description": "Descripción",
      "type": "asistente",
      "active_version": 1,
      "versions": {
        "1": {
          "version": 1,
          "system_prompt": "...",
          "context": "...",
          "documents": [],
          "knowledge_base": {},
          "instructions": [],
          "examples": [],
          "restrictions": [],
          "tone": "profesional",
          "language": "español"
        }
      }
    }
  },
  "active_profile": "Nombre del Perfil",
  "metadata": {...}
}
```

## 🎨 Interfaz

### Dashboard (🏠)
- Métricas generales
- Perfiles recientes
- Estado del sistema

### Perfiles (📊)
- Crear nuevos perfiles
- Listar y gestionar existentes
- Importar/exportar

### Editor de Versiones (📝)
- Editar contenido de versiones
- Gestionar instrucciones, ejemplos y restricciones
- Activar/eliminar versiones

### Documentos (📚)
- Cargar y gestionar documentos
- Visualizar contenido
- Organizar por tipo

### Base de Conocimientos (🧠)
- Agregar información estructurada
- Gestionar pares clave-valor
- Búsqueda y edición

### Configuración (⚙️)
- Ver configuración general
- Vista previa del contexto
- Sincronización manual

## 💡 Ejemplos de Uso

### Ejemplo 1: Asistente Médico

```
Perfil: Asistente Médico
Tipo: asistente
System Prompt: "Eres un asistente médico profesional..."
Contexto: "Trabajas en un hospital general..."
Instrucciones:
- Siempre pedir datos del paciente
- Mantener confidencialidad
- Derivar casos urgentes
Tono: profesional
Idioma: español
```

### Ejemplo 2: Soporte Técnico

```
Perfil: Soporte TI
Tipo: soporte
System Prompt: "Eres un técnico de soporte..."
Documentos:
- Manual de producto
- FAQ técnicas
- Políticas de garantía
Knowledge Base:
- horario_soporte: "24/7"
- tiempo_respuesta: "< 2 horas"
```

### Ejemplo 3: Agente de Ventas

```
Perfil: Vendedor
Tipo: ventas
Tono: amigable
Ejemplos:
- "Usuario: ¿Cuánto cuesta? Bot: Tenemos..."
Restricciones:
- No dar descuentos sin autorización
- No hacer promesas de entrega
```

## 🔧 Personalización

### Agregar Nuevos Tipos de Perfil

Edita `bot_training_app.py` línea ~129:

```python
profile_type = st.selectbox(
    "Tipo de Perfil",
    ["general", "asistente", "tu_nuevo_tipo", ...]
)
```

### Agregar Nuevos Tonos

Edita `bot_training_app.py` línea ~378:

```python
tone = st.selectbox(
    "Tono de Comunicación",
    ["profesional", "amigable", "tu_nuevo_tono", ...]
)
```

## 🔒 Seguridad

- Los perfiles se guardan localmente en archivos JSON
- No se envía información sensible a servicios externos
- Backups recomendados del archivo `bot_profiles.json`

## 📝 Mejores Prácticas

1. **Versionamiento**: Crea una nueva versión antes de hacer cambios grandes
2. **Descripción**: Documenta bien cada perfil y versión
3. **Pruebas**: Prueba cada perfil antes de activarlo
4. **Backup**: Exporta perfiles importantes regularmente
5. **Contexto**: Mantén el contexto conciso y relevante
6. **Documentos**: Organiza documentos por tipo
7. **Knowledge Base**: Usa claves descriptivas y valores claros

## 🐛 Solución de Problemas

### La aplicación no inicia
```bash
# Verificar instalación de Streamlit
pip install --upgrade streamlit

# Ejecutar de nuevo
streamlit run bot_training_app.py
```

### Cambios no se reflejan en el bot
1. Verifica que el perfil esté activo
2. Sincroniza manualmente en Configuración
3. Reinicia el bot de Telegram

### Error al cargar perfiles
1. Verifica que `bot_profiles.json` no esté corrupto
2. Haz backup y elimina el archivo
3. La app creará uno nuevo

## 📈 Próximas Características

- [ ] Historial de cambios detallado
- [ ] Búsqueda avanzada en documentos
- [ ] Importar desde múltiples formatos (PDF, DOCX)
- [ ] Colaboración multi-usuario
- [ ] API REST para gestión programática
- [ ] Métricas de uso por perfil
- [ ] A/B testing de versiones
- [ ] Backup automático

## 🤝 Contribuciones

Para mejorar esta aplicación:

1. Reporta bugs y sugerencias
2. Propón nuevas características
3. Comparte tus perfiles de ejemplo

## 📄 Licencia

Este sistema es parte del proyecto de Chatbot con Gemini.

---

**¿Necesitas ayuda?** Revisa la documentación o contacta al equipo de desarrollo.

