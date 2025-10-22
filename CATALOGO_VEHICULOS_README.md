# 🚗 Sistema de Catálogo de Vehículos

## 📋 Descripción

El sistema ahora incluye una funcionalidad especializada para importar catálogos completos de vehículos desde archivos CSV. Esta funcionalidad crea automáticamente un perfil de bot optimizado para ventas de vehículos con toda la información técnica organizada.

## ✨ Características Principales

### 1. Importación Automática de Catálogo
- Lee archivos CSV con información de vehículos
- Crea un perfil completo automáticamente
- Organiza cada vehículo en la base de conocimientos
- Genera índices de búsqueda rápida
- Incluye instrucciones de ventas pre-configuradas

### 2. Información Completa por Vehículo

Cada vehículo importado incluye:

| Categoría | Campos |
|-----------|--------|
| **Identificación** | ID, Marca, Modelo, Año, Versión |
| **Diseño** | Tipo de Carrocería, Puertas, Asientos, Colores |
| **Motor** | Modelo Motor, Potencia (HP), Cilindrada |
| **Transmisión** | Tipo de Transmisión |
| **Capacidades** | Combustible (litros) |
| **Ruedas** | Neumáticos (medida) |
| **Equipamiento** | Equipamiento Destacado |
| **Multimedia** | Link a Foto/Imagen |

### 3. Contenido Generado Automáticamente

El perfil creado incluye:

#### ✅ System Prompt Especializado
```
Eres un experto asesor de ventas de vehículos. Tienes conocimiento completo 
del catálogo de vehículos disponibles y puedes ayudar a los clientes a encontrar 
el vehículo perfecto según sus necesidades, presupuesto y preferencias.
```

#### ✅ Base de Conocimientos
- Cada vehículo como entrada individual
- Formato organizado y fácil de leer
- Información completa y estructurada

#### ✅ Documentos Auxiliares
1. **Resumen del Catálogo**: Lista de todos los vehículos agrupados por marca
2. **Índice de Búsqueda**: Vehículos organizados por tipo de carrocería y transmisión

#### ✅ Instrucciones de Ventas
- Identificación de necesidades del cliente
- Recomendación basada en el catálogo
- Comparación de modelos
- Presentación de características

#### ✅ Ejemplos de Conversación
- Consultas sobre disponibilidad
- Búsqueda por tipo de vehículo
- Verificación de especificaciones

#### ✅ Restricciones
- No inventar información no presente en el catálogo
- Siempre verificar antes de responder
- Dirigir al cliente a ventas para finalizar

## 🚀 Cómo Usar

### Paso 1: Preparar el CSV

Crea un archivo CSV con las siguientes columnas:

```csv
id,marca,modelo,año,tipo_carroceria,transmision,capacidad_combustible_lt,
colores,modelo_motor,potencia_hp,cilindrada,neumaticos,puertas,asientos,
version,equipamiento_destacado,link_foto
```

**Ejemplo de fila:**
```csv
VEH001,Toyota,Corolla,2024,Sedan,Automática,50,"Blanco, Negro, Plata",
2.0L DOHC,168,1998 cc,215/55R17,4,5,XLE Premium,
"ABS, Airbags, A/C, Cámara",https://ejemplo.com/foto.jpg
```

### Paso 2: Importar en la Aplicación

1. Abre `bot_training_app.py`
2. Ve a **🎯 Perfiles Múltiples**
3. Selecciona el tab **🚗 Catálogo Vehículos**
4. Sube tu archivo CSV
5. (Opcional) Especifica un nombre para el perfil
6. Haz clic en **🚗 Importar Catálogo de Vehículos**

### Paso 3: Activar el Perfil

#### Opción A: Activación Directa
- Después de importar, haz clic en "🎯 Activar este perfil ahora"

#### Opción B: Activación Manual
1. Ve al tab **🎯 Gestión de Activos**
2. Selecciona el perfil creado
3. Asigna una prioridad
4. Activa el perfil

### Paso 4: Probar el Bot

Prueba preguntando al bot:
- "¿Qué vehículos tienen disponibles?"
- "Busco un SUV familiar"
- "¿El Corolla viene en color rojo?"
- "¿Cuáles son las especificaciones del CR-V?"
- "Compara el F-150 con el Silverado"

## 📝 Formato del CSV

### Columnas Obligatorias

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id` | String | Identificador único | VEH001 |
| `marca` | String | Marca del vehículo | Toyota |
| `modelo` | String | Modelo | Corolla |
| `año` | String/Int | Año del modelo | 2024 |
| `tipo_carroceria` | String | Tipo | Sedan, SUV, Pickup |
| `transmision` | String | Tipo de transmisión | Automática, Manual |
| `capacidad_combustible_lt` | Number | Capacidad en litros | 50 |
| `colores` | String | Colores (separados por coma) | Blanco, Negro, Rojo |
| `modelo_motor` | String | Modelo del motor | 2.0L DOHC |
| `potencia_hp` | Number | Potencia en caballos | 168 |
| `cilindrada` | String | Cilindrada | 1998 cc |
| `neumaticos` | String | Medida de neumáticos | 215/55R17 |
| `puertas` | Number | Número de puertas | 4 |
| `asientos` | Number | Número de asientos | 5 |
| `version` | String | Versión del modelo | XLE Premium |
| `equipamiento_destacado` | String | Equipamiento (separado por coma) | ABS, Airbags, A/C |
| `link_foto` | String | URL de imagen | https://... |

### Notas sobre el Formato

✅ **Encoding**: Usa UTF-8 siempre
✅ **Separadores**: Coma (`,`) para separar campos
✅ **Texto con comas**: Usa comillas dobles (`"Blanco, Negro, Rojo"`)
✅ **Orden**: Las columnas pueden estar en cualquier orden
✅ **Valores faltantes**: Se reemplazarán por 'N/A'

## 💡 Ejemplo Completo

Ver archivo: `ejemplo_catalogo_vehiculos.csv` (incluido en el proyecto)

Este archivo contiene 10 vehículos de ejemplo de diferentes marcas:
- Toyota Corolla
- Honda CR-V
- Ford F-150
- Chevrolet Silverado
- Nissan Kicks
- Mazda CX-5
- Hyundai Tucson
- Volkswagen Jetta
- Kia Sportage
- Jeep Wrangler

## 🎯 Casos de Uso

### Caso 1: Catálogo Completo de Concesionario

**Escenario**: Tienes 100+ vehículos en inventario

**Solución**:
1. Exporta tu inventario desde el sistema de gestión
2. Mapea las columnas al formato requerido
3. Importa el CSV completo
4. Activa el perfil con prioridad alta
5. Combina con perfiles de empresa y ventas

**Resultado**: Bot que conoce todo el inventario y puede asesorar a clientes

### Caso 2: Catálogo por Categoría

**Escenario**: Manejas diferentes líneas (sedans, SUVs, pickups)

**Solución**:
1. Crea un CSV por categoría
2. Importa cada uno como perfil separado
3. Activa según la conversación:
   - Prioridad 1: Catálogo general
   - Prioridad 2: Catálogo específico (SUVs)
   - Prioridad 3: Información de la empresa

**Resultado**: Especialización dinámica según el tipo de cliente

### Caso 3: Actualización Mensual

**Escenario**: El catálogo cambia mensualmente

**Solución**:
1. Mantén un CSV maestro actualizado
2. Cada mes, importa como nuevo perfil
3. Desactiva el perfil anterior
4. Activa el nuevo
5. Mantén histórico si es necesario

**Resultado**: Catálogo siempre actualizado sin perder versiones anteriores

### Caso 4: Multi-Marca

**Escenario**: Vendes varias marcas

**Solución**:
1. CSV general con todas las marcas
2. O CSVs separados por marca
3. Combina perfiles según el cliente:
   - Cliente interesado en Toyota → Activa perfil Toyota
   - Cliente indeciso → Activa todos los perfiles

**Resultado**: Flexibilidad para diferentes estrategias de venta

## 🔧 Combinación con Otros Perfiles

El catálogo de vehículos funciona excelentemente con:

### Prioridad Recomendada:

1. **Prioridad 1**: Perfil de Empresa/Marca (ej: "Que es invertropoli")
2. **Prioridad 2**: Catálogo de Vehículos
3. **Prioridad 3**: Perfil de Ventas (ej: "Asistente de Ventas")
4. **Prioridad 4**: Perfil de Soporte (para post-venta)

**Resultado**: Bot completo que combina identidad de marca, conocimiento de productos, técnicas de venta y soporte.

## 📊 Visualización de Datos

El perfil generado incluye visualización organizada:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗 Toyota Corolla 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INFORMACIÓN GENERAL:
• ID: VEH001
• Marca: Toyota
• Modelo: Corolla
• Año: 2024
• Versión: XLE Premium
• Tipo de Carrocería: Sedan

🔧 ESPECIFICACIONES TÉCNICAS:
• Motor: 2.0L DOHC
• Potencia: 168 HP
• Cilindrada: 1998 cc
• Transmisión: Automática
• Capacidad de Combustible: 50 litros

🚙 CARACTERÍSTICAS:
• Puertas: 4
• Asientos: 5
• Neumáticos: 215/55R17

🎨 COLORES DISPONIBLES:
Blanco, Negro, Plata, Azul

⭐ EQUIPAMIENTO DESTACADO:
ABS, 8 airbags, A/C automático...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🛠️ Troubleshooting

### Error: "No se encontraron vehículos en el CSV"
**Solución**: Verifica que el archivo tenga datos más allá del header

### Error de encoding
**Solución**: Guarda el CSV como UTF-8 en Excel o tu editor

### Columnas faltantes
**Solución**: No es crítico, se usará 'N/A'. Descarga la plantilla para referencia

### No se importa correctamente
**Solución**: Verifica que las comillas en campos con comas estén correctas

## 📞 Tips y Mejores Prácticas

1. **Usa IDs únicos**: Facilita la actualización posterior
2. **Sé descriptivo en equipamiento**: Incluye todo lo relevante
3. **URLs de fotos válidas**: Verifica que los links funcionen
4. **Colores completos**: Lista todos los colores disponibles
5. **Especificaciones técnicas**: Sé preciso con números y unidades
6. **Versiones claras**: Diferencia bien entre versiones del mismo modelo
7. **Actualiza regularmente**: Mantén el catálogo sincronizado con inventario
8. **Prueba antes**: Importa un CSV pequeño primero para validar

## 🎓 Recursos

- **Plantilla CSV**: Descargable desde la interfaz
- **Archivo de Ejemplo**: `ejemplo_catalogo_vehiculos.csv`
- **Documentación General**: `PERFILES_MULTIPLES_README.md`
- **Sistema Completo**: `SISTEMA_COMPLETO.md`

---

**Versión**: 2.0.0  
**Última Actualización**: Octubre 2025  
**Característica**: Importación de Catálogo de Vehículos desde CSV

