# 🚨 ERROR DE SINCRONIZACIÓN - REPORTE Y SOLUCIÓN

**Titulo:** "Error de conexión con el script de sincronización"  
**Descripción:** Al clickear "Sincronizar Gmail a Coda", falla con error de conexión  
**Causa Raíz:** API keys vacías en gastos_bancarios.py  
**Status:** ✅ CORREGIDO

---

## 🔴 EL ERROR

```
Sincronización Gmail a Coda
"Descargando correos bancarios de BCP y BBVA..."
"Error de conexión con el script de sincronización."
```

---

## 🔍 ANÁLISIS

El archivo `gastos_bancarios.py` intenta obtener API keys de archivos que no existen:

```python
# ❌ ANTES (INCORRECTO):

# Línea 23 - Hardcoded Windows Path:
CARPETA = os.path.join('C:', os.sep, 'GastosHV')  # ❌ NO existe en producción

# Línea 34-39 - GEMINI_API_KEY vacía:
_gk = os.path.join(CARPETA, 'gemini_key.txt')
if os.path.exists(_gk):  # ❌ Archivo no existe
    GEMINI_API_KEY = f.read().strip()
else:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # = ''

# Línea 43-48 - CODA_API_KEY vacía:
_ck = os.path.join(CARPETA, 'coda_key.txt')
if os.path.exists(_ck):  # ❌ Archivo no existe
    CODA_API_KEY = f.read().strip()
else:
    CODA_API_KEY = ''  # ❌ Siempre vacía!
```

**Resultado:**
- GEMINI_API_KEY = '' (vacío)
- CODA_API_KEY = '' (vacío)
- Script intenta conectar con keys vacíos
- APIs rechazasin credenciales
- Error: "Error de conexión"

---

## ✅ SOLUCIÓN IMPLEMENTADA

Actualizar `gastos_bancarios.py` para usar variables de entorno:

```python
# ✅ DESPUÉS (CORRECTO):

# Carpeta dinámica (NO hardcoded):
CARPETA = os.path.dirname(os.path.abspath(__file__))

# GEMINI_API_KEY desde entorno:
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no configurada")

# CODA_API_KEY desde entorno:
CODA_API_KEY = os.environ.get('CODA_API_KEY', '').strip()
if not CODA_API_KEY:
    raise ValueError("CODA_API_KEY no configurada")

# CODA_DOC_ID desde entorno (con default):
CODA_DOC_ID = os.environ.get('CODA_DOC_ID', 'vjnLYcbb8p').strip()
```

---

## 📋 CAMBIOS

**Archivo:** `gastos_bancarios.py`
**Líneas:** 16-50
**Commit:** `b8bcc33`

### Qué cambió:
1. ✅ Quitar hardcoded `'C:/GastosHV'`
2. ✅ Usar directorio actual dinámicamente
3. ✅ Obtener GEMINI_API_KEY de `os.environ`
4. ✅ Obtener CODA_API_KEY de `os.environ`
5. ✅ Obtener CODA_DOC_ID de `os.environ`
6. ✅ Fallar explícitamente si faltan keys

---

## 🧪 CÓMO PROBAR

### Local:

```bash
# 1. Asegurar que .env está configurado
cat .env
# CODA_API_KEY=tu_key_real
# GEMINI_API_KEY=tu_key_real
# CODA_DOC_ID=vjnLYcbb8p

# 2. Inicia server Python
python3 server.py

# 3. En navegador: http://localhost:5000
# 4. Clickea "Sincronizar Gmail a Coda"
# 5. RESULTADO ESPERADO:
# ✅ Se inicia sincronización
# ✅ Ve logs de ejecución
# ✅ Completa sin error
```

### En Hostinger:

```bash
# 1. Asegurar que .env está en Hostinger
ssh tu_usuario@ops.inprometal.com
cat /ruta/a/.env
# DEBE tener CODA_API_KEY y GEMINI_API_KEY

# 2. Pull cambios
git pull origin claude/gallant-ramanujan-KZyWu

# 3. En navegador: https://ops.inprometal.com
# 4. Clickea "Sincronizar Gmail a Coda"
# 5. DEBE FUNCIONAR sin error
```

---

## 🔒 SEGURIDAD

Esta corrección también:
- ✅ Elimina hardcoded paths (información disclosure)
- ✅ Usa variables de entorno seguras
- ✅ Falla explícitamente si faltan credenciales
- ✅ Sigue el mismo patrón que server.py

---

## 📊 IMPACTO

| Función | Antes | Después |
|---------|-------|---------|
| Sincronización Gmail | ❌ Error | ✅ Funcional |
| Lectura API keys | ❌ Archivos no encontrados | ✅ Variables de entorno |
| Manejo de errores | ❌ Error silencioso | ✅ Error explícito |
| Seguridad | ❌ Hardcoded paths | ✅ Dinámico |

---

## ✨ RESUMEN

**Problema:** gastos_bancarios.py buscaba API keys en archivos que no existen

**Solución:** Usar variables de entorno como lo hace server.py

**Commit:** `b8bcc33`

**Status:** ✅ LISTO PARA DESPLEGAR

---

**NOTA:** Asegúrate que tu `.env` en Hostinger tiene:
```
CODA_API_KEY=tu_key_real
GEMINI_API_KEY=tu_key_real
CODA_DOC_ID=vjnLYcbb8p
```

Si faltan, la sincronización volverá a fallar con error más claro.
