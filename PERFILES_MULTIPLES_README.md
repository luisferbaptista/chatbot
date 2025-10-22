# 🎯 Sistema de Perfiles Múltiples con Prioridades

## 📋 Descripción General

El sistema de chatbot ahora soporta **múltiples perfiles activos simultáneamente** con gestión de **prioridades jerárquicas** y **importación/exportación CSV**.

## ✨ Nuevas Funcionalidades

### 1. 🎯 Múltiples Perfiles Activos

Ahora puedes activar varios perfiles al mismo tiempo, cada uno con su propia prioridad:

- **Prioridad 1**: Perfil principal (mayor prioridad)
- **Prioridad 2, 3, 4...**: Perfiles complementarios que extienden el contexto

#### Cómo funciona:

1. Ve a la sección **🎯 Perfiles Múltiples** en la aplicación de entrenamiento
2. Selecciona un perfil para activar
3. Asigna una prioridad (1 = mayor prioridad)
4. Haz clic en "🎯 Activar Perfil"

#### Gestión de Prioridades:

- Los perfiles se combinan jerárquicamente según su prioridad
- El perfil con prioridad 1 define el `system_prompt` principal
- Los demás perfiles complementan con sus instrucciones, conocimientos y restricciones
- Puedes ajustar las prioridades en cualquier momento desde la interfaz

### 2. 📥📤 Importación/Exportación CSV

#### Exportar Perfiles a CSV:

##### Exportar un Perfil Individual:
1. Ve a **🎯 Perfiles Múltiples > 📤 Exportar CSV**
2. Selecciona el perfil que deseas exportar
3. Especifica el nombre del archivo CSV
4. Haz clic en "📤 Exportar a CSV"
5. Descarga el archivo generado

##### Exportar Todos los Perfiles:
1. Ve a **🎯 Perfiles Múltiples > 📤 Exportar CSV**
2. En la sección "Exportar Todos los Perfiles"
3. Especifica el nombre del archivo CSV consolidado
4. Haz clic en "📤 Exportar Todos a CSV"
5. Descarga el archivo generado

#### Importar Perfiles desde CSV:

1. Ve a **🎯 Perfiles Múltiples > 📥 Importar CSV**
2. Descarga la plantilla CSV si aún no tienes un archivo
3. Edita el CSV con los datos de tu perfil
4. Sube el archivo CSV
5. Haz clic en "📥 Importar Perfil desde CSV"

### 3. 📊 Formato CSV

#### Estructura del CSV Individual:

El archivo CSV debe tener dos columnas: `Campo` y `Valor`

```csv
Campo,Valor
profile_name,Mi Asistente Virtual
profile_description,Asistente especializado en atención al cliente
profile_type,asistente
system_prompt,Eres un asistente amigable y profesional
context,Contexto general sobre la empresa y productos
tone,profesional
language,español
instructions,Instrucción 1|Instrucción 2|Instrucción 3
examples,Ejemplo conversación 1||Ejemplo conversación 2
restrictions,Restricción 1|Restricción 2
knowledge_base,horario=Lunes-Viernes 9-17|email=contacto@empresa.com
documents,Manual::Contenido del manual||FAQ::Preguntas frecuentes
```

#### Separadores Especiales:

- **Instrucciones**: separadas por `|`
- **Ejemplos**: separados por `||`
- **Restricciones**: separadas por `|`
- **Base de Conocimientos**: formato `key1=value1|key2=value2`
- **Documentos**: formato `nombre1::contenido1||nombre2::contenido2`

### 4. 🔄 Sincronización Automática

El sistema sincroniza automáticamente el contexto combinado de todos los perfiles activos:

- **Auto-sync**: Sincronización automática en tiempo real (puede deshabilitarse)
- **Sincronización Manual**: Botón para forzar sincronización
- **Archivo de Contexto**: Se guarda en `active_profile_context.txt`
- **Estado de Sincronización**: Visible en el sidebar con timestamp

## 🚀 Casos de Uso

### Caso 1: Chatbot Multi-Especializado

Activa múltiples perfiles para crear un chatbot que combine diferentes especialidades:

1. **Prioridad 1**: Perfil base "Asistente General" (comportamiento principal)
2. **Prioridad 2**: Perfil "Conocimiento Técnico" (información técnica)
3. **Prioridad 3**: Perfil "Atención al Cliente" (políticas y procedimientos)

### Caso 2: Perfiles por Departamento

Combina perfiles de diferentes departamentos:

1. **Prioridad 1**: "Ventas" (perfil principal)
2. **Prioridad 2**: "Soporte Técnico" (información adicional)
3. **Prioridad 3**: "Recursos Humanos" (políticas internas)

### Caso 3: Importación Masiva desde Excel

1. Crea múltiples perfiles en Excel/Google Sheets
2. Exporta como CSV
3. Importa todos los perfiles de una vez
4. Activa los que necesites con sus prioridades

## 📝 Métodos Nuevos en ProfileManager

### Gestión de Múltiples Perfiles:

```python
# Agregar perfil activo con prioridad
pm.add_active_profile(profile_name: str, priority: int) -> bool

# Remover perfil activo
pm.remove_active_profile(profile_name: str) -> bool

# Obtener todos los perfiles activos
pm.get_active_profiles() -> List[Dict]

# Cambiar prioridad de un perfil
pm.set_profile_priority(profile_name: str, new_priority: int) -> bool

# Desactivar todos los perfiles
pm.clear_active_profiles()

# Obtener contexto combinado
pm.get_multi_profile_context() -> str
```

### Importación/Exportación CSV:

```python
# Exportar perfil a CSV
pm.export_profile_to_csv(profile_name: str, csv_path: str) -> bool

# Importar perfil desde CSV
pm.import_profile_from_csv(csv_path: str) -> Optional[str]

# Exportar todos los perfiles a CSV consolidado
pm.export_all_profiles_to_csv(csv_path: str) -> bool
```

## 🔧 Retrocompatibilidad

El sistema mantiene **total retrocompatibilidad** con la versión anterior:

- Si no hay múltiples perfiles activos, funciona exactamente como antes
- El campo `active_profile` se mantiene para compatibilidad
- Los métodos antiguos siguen funcionando
- `get_active_profile_context()` sigue disponible

## 📊 Dashboard Actualizado

El Dashboard ahora muestra:

- **Sidebar**: Lista de todos los perfiles activos con sus prioridades
- **Emojis de Prioridad**: 🥇 (1), 🥈 (2), 🥉 (3), 🔹 (resto)
- **Estado de Sincronización**: Información sobre el modo multi-perfil
- **Botón de Desactivación**: Desactiva todos los perfiles de una vez

## 🎨 Interfaz de Usuario

### Nueva Sección: "🎯 Perfiles Múltiples"

Esta sección incluye tres pestañas:

1. **🎯 Gestión de Activos**: Activar, desactivar y ajustar prioridades
2. **📤 Exportar CSV**: Exportar perfiles individuales o todos
3. **📥 Importar CSV**: Importar perfiles desde archivos CSV

### Características de la Interfaz:

- **Drag-and-drop**: Sube archivos CSV fácilmente
- **Descarga de Plantilla**: Plantilla CSV pre-configurada
- **Vista Previa**: Visualiza el contexto combinado antes de sincronizar
- **Estadísticas**: Métricas sobre caracteres, palabras y perfiles activos

## 🔐 Seguridad

- Validación de datos en importación CSV
- Nombres duplicados se manejan automáticamente (sufijos _1, _2, etc.)
- Archivos temporales se eliminan después de importar
- Sincronización controlada con confirmación

## 💡 Tips y Mejores Prácticas

1. **Organiza por Prioridad**: Asigna prioridad 1 al perfil más importante
2. **Exporta Backups**: Exporta tus perfiles periódicamente como backup
3. **Usa CSV para Templates**: Crea plantillas de perfiles en CSV para reutilizar
4. **Prueba el Contexto**: Revisa la vista previa antes de activar en producción
5. **Sincroniza Manualmente**: Para cambios críticos, sincroniza manualmente
6. **Documenta Prioridades**: Mantén un registro de qué perfil tiene qué prioridad

## 🐛 Solución de Problemas

### El contexto no se actualiza:
- Verifica que el auto-sync esté activado
- Haz clic en "Sincronizar Ahora" manualmente
- Revisa el archivo `sync_status.json`

### Error al importar CSV:
- Verifica el formato del archivo
- Asegúrate de usar UTF-8 como encoding
- Descarga la plantilla como referencia

### Perfiles duplicados:
- El sistema agrega sufijos automáticamente (_1, _2, etc.)
- Renombra el perfil después de importar si es necesario

## 📞 Soporte

Para más información o reportar problemas:
- Revisa la documentación en `DISEÑO_MEJORADO.md`
- Consulta `SISTEMA_COMPLETO.md` para arquitectura
- Contacta al desarrollador: Luis Baptista

---

**Versión**: 2.0.0  
**Fecha**: Octubre 2025  
**Características Principales**: Multi-perfil, Prioridades, CSV  

