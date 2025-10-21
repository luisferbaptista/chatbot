# 🤖 Sistema Completo de Gestión del Chatbot

## 🔐 Sistema de Autenticación

### Acceso Seguro
El sistema ahora cuenta con autenticación obligatoria mediante usuario y contraseña.

#### Credenciales por Defecto
```
Usuario: admin
Contraseña: admin123
```

**⚠️ IMPORTANTE:** Cambia la contraseña después del primer acceso.

### Cambiar Contraseña

#### Opción 1: Desde la terminal
```bash
python change_password.py
```

#### Opción 2: Editar el archivo `auth_config.json`
```json
{
  "users": {
    "admin": {
      "password": "TU_NUEVA_CONTRASEÑA_HASHEADA",
      "role": "admin"
    }
  }
}
```

### Crear Nuevos Usuarios

Ejecuta:
```bash
python change_password.py
```

E ingresa un nombre de usuario que no existe. El script te preguntará si deseas crearlo.

### Timeout de Sesión

Por defecto, la sesión expira después de 60 minutos de inactividad. Puedes cambiar esto en `auth_config.json`:

```json
{
  "settings": {
    "session_timeout_minutes": 120
  }
}
```

## 🔄 Sincronización en Tiempo Real

### ¿Cómo Funciona?

El sistema sincroniza automáticamente todos los cambios con el bot de Telegram:

1. **Modificas un perfil** → Se guarda en `bot_profiles.json`
2. **Sistema genera contexto** → Según el perfil activo
3. **Guarda en archivo** → `active_profile_context.txt`
4. **Bot lee contexto** → En cada conversación

### Sincronización Automática

Por defecto, la sincronización automática está **ACTIVADA**. Cada vez que:
- Crees un perfil
- Actives un perfil
- Edites contenido de una versión
- Agregues documentos
- Modifiques la base de conocimientos
- Agregues instrucciones/ejemplos/restricciones

**El contexto se sincroniza AUTOMÁTICAMENTE con el bot.**

### Sincronización Manual

Si desactivas la sincronización automática, puedes sincronizar manualmente:

1. Ve al **Sidebar** → **Sincronización**
2. Click en **"🔄 Sincronizar Manual"**

### Verificar Estado de Sincronización

En el sidebar verás:
- **Auto-sync en tiempo real**: ✅ (activado) o ⬜ (desactivado)
- **Última sync**: Hora de la última sincronización

## 📋 Flujo de Trabajo Completo

### 1. Iniciar Sistema

```bash
# Terminal 1: Iniciar el bot de Telegram
python bot.py

# Terminal 2: Iniciar aplicación de gestión
streamlit run bot_training_app.py
# o
start_training_app.bat
```

### 2. Login

1. Abre la aplicación en `http://localhost:8501`
2. Ingresa credenciales (admin/admin123)
3. Accede al sistema

### 3. Crear y Configurar Perfil

#### Paso 1: Crear Perfil
1. **"📊 Perfiles"** → **"📝 Crear Perfil"**
2. Completa:
   - Nombre: "Asistente Personal"
   - Descripción: "Ayudante para tareas diarias"
   - Tipo: asistente

#### Paso 2: Configurar Contenido
1. **"📝 Editor de Versiones"**
2. Selecciona tu perfil
3. Edita:
   - **System Prompt**: Comportamiento base
   - **Contexto**: Información de fondo
   - **Tono**: amigable, profesional, etc.
   - **Idioma**: español, inglés, etc.

#### Paso 3: Agregar Instrucciones
1. Pestaña **"Instrucciones"**
2. Agrega reglas para el bot:
   - "Siempre saludar cordialmente"
   - "Ofrecer ayuda adicional"
   - "Mantener respuestas concisas"

#### Paso 4: Agregar Ejemplos
1. Pestaña **"Ejemplos"**
2. Agrega conversaciones de ejemplo

#### Paso 5: Agregar Restricciones
1. Pestaña **"Restricciones"**
2. Define lo que NO debe hacer:
   - "No dar información médica"
   - "No procesar datos sensibles"

### 4. Agregar Documentos

1. **"📚 Documentos"**
2. Selecciona perfil y versión
3. **"➕ Agregar Documento"**
4. Carga:
   - Manuales
   - FAQs
   - Guías
   - Políticas

**El bot tendrá acceso a TODO este contenido.**

### 5. Base de Conocimientos

1. **"🧠 Base de Conocimientos"**
2. Agrega información estructurada:
   - `horario_atencion`: "Lunes a Viernes 9-18"
   - `telefono_soporte`: "+52 55 1234 5678"
   - `email_contacto`: "contacto@empresa.com"

### 6. Activar Perfil

1. **"📊 Perfiles"** → **"📋 Listar Perfiles"**
2. Encuentra tu perfil
3. Click **"🎯 Activar"**

**✅ Sincronización automática se ejecuta.**

### 7. Probar en Telegram

1. Abre tu bot en Telegram
2. Envía un mensaje
3. **El bot responderá según el perfil activo**

## 🎯 Casos de Uso

### Caso 1: Soporte Técnico 24/7

```
Perfil: Soporte TI
System Prompt: "Eres un técnico de soporte nivel 2..."

Documentos:
- Manual de troubleshooting
- FAQ de problemas comunes
- Guía de escalamiento

Knowledge Base:
- nivel_1: "Problemas de software"
- nivel_2: "Problemas de hardware"
- escalamiento: "support@empresa.com"

Instrucciones:
- Pedir detalles antes de dar soluciones
- Ofrecer pasos numerados
- Crear ticket si es necesario

Tono: profesional
```

**Resultado:** Bot que resuelve problemas técnicos consultando manuales internos.

### Caso 2: Asistente de Ventas

```
Perfil: Vendedor
System Prompt: "Eres un agente de ventas amigable..."

Knowledge Base:
- precio_producto_a: "$299"
- precio_producto_b: "$499"
- descuento_maximo: "15%"
- tiempo_entrega: "3-5 días hábiles"

Ejemplos:
"Usuario: ¿Cuánto cuesta el producto A?
Bot: El producto A tiene un precio de $299. 
     ¿Te gustaría conocer las opciones de pago?"

Restricciones:
- No ofrecer descuentos mayores a 15%
- No prometer entregas en menos de 3 días

Tono: amigable
```

**Resultado:** Bot que vende productos con información precisa.

### Caso 3: Profesor de Idiomas

```
Perfil: Profesor de Inglés
System Prompt: "Eres un profesor paciente de inglés..."

Documentos:
- Gramática básica
- Lista de verbos irregulares
- Frases comunes

Instrucciones:
- Corregir errores gentilmente
- Dar ejemplos de uso
- Practicar con diálogos

Restricciones:
- No dar respuestas directas a tareas
- Guiar con preguntas

Tono: empático
```

**Resultado:** Bot que enseña idiomas paso a paso.

## 📊 Archivos del Sistema

### Archivos de Configuración

```
📁 Proyecto/
├── 🔐 auth_config.json          # Usuarios y contraseñas
├── 📊 bot_profiles.json         # Todos los perfiles
├── 💾 conversation_memory.json  # Historial del bot
├── 🔄 active_profile_context.txt # Contexto sincronizado
└── ✅ sync_status.json           # Estado de sincronización
```

### Archivos Python

```
📁 Proyecto/
├── 🤖 bot.py                     # Bot de Telegram
├── 🎨 bot_training_app.py        # App de gestión (Streamlit)
├── 🔧 profile_manager.py         # Gestor de perfiles
└── 🔑 change_password.py         # Cambio de contraseñas
```

## 🔒 Seguridad

### Contraseñas
- Almacenadas con hash SHA-256
- No se guardan en texto plano
- Timeout automático de sesión

### Datos
- Almacenados localmente
- Sin conexiones externas
- Backup recomendado de `bot_profiles.json`

### Mejores Prácticas

1. **Cambia la contraseña por defecto**
2. **Haz backups regulares** de `bot_profiles.json`
3. **No compartas credenciales**
4. **Cierra sesión** al terminar
5. **Exporta perfiles** importantes

## 🛠️ Administración

### Backup de Perfiles

```bash
# Manual
Copiar bot_profiles.json a ubicación segura

# O usar exportación desde la app
Perfiles → Importar/Exportar → Exportar
```

### Restaurar Perfiles

```bash
# Manual
Reemplazar bot_profiles.json con backup

# O usar importación desde la app  
Perfiles → Importar/Exportar → Importar
```

### Reset del Sistema

```bash
# Eliminar todos los perfiles
Eliminar bot_profiles.json

# Eliminar credenciales
Eliminar auth_config.json

# Limpiar contexto
Eliminar active_profile_context.txt
Eliminar sync_status.json
```

## 🚨 Solución de Problemas

### El bot no responde según el perfil

**Solución:**
1. Verifica que el perfil esté activado (✅ en el sidebar)
2. Click en **"🔄 Sincronizar Manual"**
3. Reinicia el bot: `python bot.py`

### No puedo iniciar sesión

**Solución:**
```bash
# Resetear contraseña
python change_password.py
```

### La sincronización no funciona

**Solución:**
1. Verifica que **"Auto-sync en tiempo real"** esté ✅
2. Verifica que exista `active_profile_context.txt`
3. Revisa permisos de escritura en el directorio

### Error al cargar perfiles

**Solución:**
1. Verifica que `bot_profiles.json` no esté corrupto
2. Haz backup y elimina el archivo
3. La app creará uno nuevo al iniciar

## 📈 Métricas y Monitoreo

### Dashboard
- Total de perfiles creados
- Perfil activo actual
- Total de versiones
- Última modificación

### Estado de Sincronización
- Última sincronización (hora exacta)
- Perfil sincronizado
- Tamaño del contexto

## 🎓 Tutoriales Rápidos

### Tutorial 1: Crear tu Primer Perfil (5 minutos)

1. Login → admin/admin123
2. Perfiles → Crear Perfil
3. Nombre: "Mi Asistente"
4. Click "Crear Perfil"
5. Editor de Versiones → Selecciona "Mi Asistente"
6. System Prompt: "Eres un asistente útil"
7. Guardar Cambios
8. Perfiles → Listar → Activar
9. ¡Listo! Prueba en Telegram

### Tutorial 2: Agregar Documentación (3 minutos)

1. Documentos → Selecciona perfil
2. Agregar Documento
3. Nombre: "Manual de Usuario"
4. Tipo: manual
5. Contenido: Pega tu manual
6. Agregar
7. Auto-sync sincroniza automáticamente
8. ¡El bot ya conoce el manual!

### Tutorial 3: Base de Conocimientos (2 minutos)

1. Base de Conocimientos → Selecciona perfil
2. Clave: `horario`
3. Valor: `Lunes a Viernes 9-18`
4. Agregar
5. Auto-sync sincroniza
6. Pregunta al bot: "¿Cuál es el horario?"

## 📞 Soporte

Para problemas o sugerencias:
- Revisa este documento
- Verifica los logs del bot
- Contacta al equipo de desarrollo

---

## ✅ Checklist de Implementación

- [x] Sistema de autenticación con login/password
- [x] Sincronización en tiempo real automática
- [x] Gestión completa de perfiles
- [x] Sistema de versionamiento
- [x] Carga de documentos
- [x] Base de conocimientos
- [x] Exportar/importar perfiles
- [x] Dashboard con métricas
- [x] Cambio de contraseñas
- [x] Timeout de sesión
- [x] Integración con bot de Telegram

**Sistema 100% funcional y listo para producción.** 🚀

