# 🚀 GUÍA DE CONFIGURACIÓN - OPERACIONES INPROMETAL

**Status Actual:** ❌ Aplicación NO está funcionando (falta .env con API keys)

---

## 📋 CHECKLIST DE CONFIGURACIÓN

### PASO 1: Crear archivo `.env` ✅ CRÍTICO

```bash
cd /home/user/Operaciones-INPROMETAL
cp .env.template .env
```

### PASO 2: Obtener CODA_API_KEY 🔑 REQUERIDO

**¿Por qué?** Para que la aplicación lea datos de tu base de datos Coda

**Pasos:**
1. Abrir: https://coda.io/account/settings#apiTokens
2. Copiar el "API token" (empieza con `d-`)
3. Editar el archivo `.env`:
   ```bash
   nano .env
   ```
4. Buscar la línea `CODA_API_KEY=` y reemplazar con tu token:
   ```
   CODA_API_KEY=d-abc123xyz789...
   ```
5. Guardar (Ctrl+X, Y, Enter)

**Verificar:** Después de guardar, ejecutar:
```bash
grep CODA_API_KEY .env
```
Debe mostrar tu token (no vacío).

---

### PASO 3: Obtener GEMINI_API_KEY 🤖 RECOMENDADO

**¿Por qué?** Para la categorización automática de gastos

**Pasos:**
1. Abrir: https://aistudio.google.com/app/apikey
2. Clic "Create API Key"
3. Seleccionar "Create new API key in Google Cloud Project"
4. Copiar la clave
5. Editar `.env` y pegar en `GEMINI_API_KEY=`:
   ```
   GEMINI_API_KEY=AIza...
   ```

**Nota:** Si no configuras GEMINI_API_KEY, la sincronización de Gmail funcionará pero sin categorización automática.

---

### PASO 4: Verificar CODA_DOC_ID (opcional)

**¿Dónde obtenerlo?** De tu URL de Coda:
```
https://coda.io/d/[ESTE_ID]/...
```

Ej: Si tu URL es `https://coda.io/d/vjnLYcbb8p/Operaciones/...`
Entonces `CODA_DOC_ID=vjnLYcbb8p`

En `.env` ya debe estar correcto (predeterminado = `vjnLYcbb8p`). Si es diferente, actualizar:
```
CODA_DOC_ID=tu_document_id_aqui
```

---

### PASO 5: Configurar Gmail Sync (OPCIONAL - solo si quieres sincronizar correos)

**Nota:** La sincronización funciona SIN esto. Gmail sync es un "bonus feature".

Si quieres activarlo:

#### 5a. Obtener `credentials.json`
1. Abrir: https://console.cloud.google.com
2. Crear proyecto (o usar existente)
3. APIs & Services → Credentials
4. Crear OAuth 2.0 Client ID (tipo: Desktop Application)
5. Descargar JSON
6. Guardar como `credentials.json` en `/home/user/Operaciones-INPROMETAL/`

#### 5b. Generar `token.json`
```bash
cd /home/user/Operaciones-INPROMETAL
python3 gastos_bancarios.py
```
- Se abre navegador
- Autorizar acceso a Gmail
- Se crea automáticamente `token.json`

---

## ✅ VERIFICACIÓN FINAL

Después de completar los pasos 1-3, ejecutar:

```bash
cd /home/user/Operaciones-INPROMETAL
php -r "
require_once 'public/api/coda_config.php';
echo 'CODA_API_KEY: ' . (defined('CODA_API_KEY') ? '✅ Configurado' : '❌ NO configurado') . PHP_EOL;
echo 'CODA_DOC_ID: ' . (defined('CODA_DOC_ID') ? CODA_DOC_ID : '❌ NO configurado') . PHP_EOL;
"
```

Debe mostrar:
```
CODA_API_KEY: ✅ Configurado
CODA_DOC_ID: vjnLYcbb8p
```

---

## 🧪 PROBAR LA APLICACIÓN

1. Reiniciar servidor Python:
   ```bash
   # Ctrl+C si está corriendo
   # Luego:
   python3 server.py
   ```

2. Abrir en navegador:
   ```
   http://localhost:5000
   ```

3. Loginearse con credenciales

4. **Debe mostrar datos de Coda en las tablas** (OT, Facturas, etc.)

Si aún no hay datos → revisar sección "Solución de Problemas" abajo.

---

## ❌ SOLUCIÓN DE PROBLEMAS

### Problema: "Error de conexión con el script de sincronización"
**Causa:** Faltan environment variables o son inválidos
**Solución:** Verificar pasos 1-3 arriba, reiniciar servidor

### Problema: "CODA_API_KEY no configurada"
**Causa:** .env existe pero CODA_API_KEY está vacío
**Solución:** 
```bash
cat .env | grep CODA_API_KEY
```
Debe mostrar un valor (no vacío). Si está vacío, editar `.env` y rellenar.

### Problema: "No puedo acceder a Coda" (error 401)
**Causa:** CODA_API_KEY es inválido o expiró
**Solución:** Obtener nuevo token de https://coda.io/account/settings#apiTokens

### Problema: Los datos no se actualizan
**Nota:** La aplicación cachea datos por 20 segundos
**Solución:** Esperar 20 segundos o actualizar navegador (F5)

### Problema: Tabla está vacía en Coda
**Causa:** La tabla en Coda está vacía o tiene nombre diferente
**Solución:** Verificar que existen las tablas: OT, Facturas, GasCom, Personal

---

## 📞 CONTACTO Y SOPORTE

Si después de seguir estos pasos algo no funciona:

1. Revisar logs:
   ```bash
   tail -50 /tmp/operaciones-inprometal.log
   ```

2. Ejecutar test de conectividad:
   ```bash
   curl -I https://coda.io
   curl -I https://www.googleapis.com
   ```

3. Verificar que `coda_config.php` se cargó:
   ```bash
   php -l public/api/coda_config.php
   ```
   Debe mostrar "No syntax errors"

---

## 📊 RESUMEN DE ARCHIVOS

| Archivo | Status | Acción |
|---------|--------|--------|
| `.env` | ❌ NO EXISTE | Crear desde .env.template, rellenar API keys |
| `credentials.json` | ❌ OPCIONAL | Obtener de Google Cloud si quieres Gmail sync |
| `token.json` | ❌ AUTO-GENERADO | Se crea ejecutando gastos_bancarios.py |
| `public/api/coda_config.php` | ✅ CREADO | Carga variables de .env |

---

## 🎯 PRÓXIMO PASO

**Ejecutar AHORA:**
```bash
cp .env.template .env
nano .env
# Rellenar CODA_API_KEY con tu token desde https://coda.io/account/settings#apiTokens
# Rellenar GEMINI_API_KEY con tu token desde https://aistudio.google.com/app/apikey
# Guardar (Ctrl+X, Y, Enter)
```

Luego reportar:
- ✅ Si los datos de Coda aparecen en la aplicación
- ❌ Si algo no funciona (incluir mensaje de error exacto)
