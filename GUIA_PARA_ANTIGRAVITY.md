# 📋 GUÍA TÉCNICA PARA ANTIGRAVITY - CONFIGURACIÓN DE CODA

**Objetivo:** Hacer que la aplicación cargue datos de Coda correctamente

**Status Actual:** Código ya está fijo. Falta solo configuración de API keys.

---

## 🎯 RESUMEN EJECUTIVO

1. El error **"Error de conexión con el script de sincronización"** fue causado por:
   - Bug en `app.js` línea 1238 (EventSource con opción inválida) → **YA FIJO**
   - Falta archivo `coda_config.php` → **YA CREADO**
   - Falta archivo `.env` con API keys → **TÚ LO HACES**

2. Cambios ya hecho:
   - ✅ Fijo EventSource en app.js
   - ✅ Creé coda_config.php que carga variables de entorno
   - ✅ Creé SETUP_GUIA_PASO_A_PASO.md con instrucciones

3. **Lo que necesitas hacer:** Crear `.env` con 2 tokens

**Tiempo estimado:** 10 minutos

---

## 🚀 PASOS DETALLADOS

### PASO 1: Ubicarse en la carpeta del proyecto

```bash
cd /home/user/Operaciones-INPROMETAL
```

Verificar que existen estos archivos:
```bash
ls -la .env.template public/api/coda_config.php SETUP_GUIA_PASO_A_PASO.md
```

Debe mostrar:
```
-rw-r--r-- .env.template
-rw-r--r-- public/api/coda_config.php
-rw-r--r-- SETUP_GUIA_PASO_A_PASO.md
```

---

### PASO 2: Crear archivo `.env` desde plantilla

```bash
cp .env.template .env
```

Verificar que se creó:
```bash
ls -la .env
```

Debe mostrar:
```
-rw-r--r-- .env
```

---

### PASO 3: Obtener CODA_API_KEY

#### 3.1 En navegador web

1. Abrir: **https://coda.io/account/settings#apiTokens**
2. Si no está logueado, hacer login
3. Buscar sección "API Tokens"
4. Copiar el token completo (empieza con `d-` seguido de caracteres)
5. **Guardar en un notepad** (lo necesitarás en el paso siguiente)

**Nota:** El token es sensible. Trata como contraseña.

#### 3.2 Editar `.env` e insertar el token

```bash
nano .env
```

Se abre editor de texto. Buscar la línea:
```
CODA_API_KEY=tu_coda_api_key_aqui_ejemplo_d-abc123xyz789
```

Reemplazar `tu_coda_api_key_aqui_ejemplo_d-abc123xyz789` con tu token real.

Ejemplo real (FICTICIO):
```
CODA_API_KEY=d-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

**Guardar el archivo:**
- Presionar: `Ctrl + X`
- Presionar: `Y` (Yes)
- Presionar: `Enter`

---

### PASO 4: Obtener GEMINI_API_KEY (OPCIONAL pero recomendado)

#### 4.1 En navegador web

1. Abrir: **https://aistudio.google.com/app/apikey**
2. Clic en **"Create API Key"**
3. Seleccionar **"Create new API key in Google Cloud Project"**
4. Copiar la clave generada
5. **Guardar en un notepad**

#### 4.2 Editar `.env` e insertar la clave

```bash
nano .env
```

Buscar:
```
GEMINI_API_KEY=tu_gemini_api_key_aqui_ejemplo_AIza...
```

Reemplazar con tu clave real. Ejemplo (FICTICIO):
```
GEMINI_API_KEY=AIzaSyDxxxxxYourKeyHerexxxxx_1234567890
```

**Guardar:**
- `Ctrl + X`
- `Y`
- `Enter`

---

### PASO 5: Verificar que `.env` está correctamente configurado

Ejecutar este comando:

```bash
grep -E "^CODA_API_KEY=d-|^GEMINI_API_KEY=AIza" .env
```

**Debe mostrar algo como:**
```
CODA_API_KEY=d-abc123xyz...
GEMINI_API_KEY=AIza...
```

Si NO muestra nada → significa que las claves no se guardaron correctamente. Repetir paso 3 y 4.

---

### PASO 6: Probar que `coda_config.php` carga correctamente

```bash
php -r "require 'public/api/coda_config.php'; 
echo 'Status: OK' . PHP_EOL; 
echo 'CODA_API_KEY configurado: ' . (defined('CODA_API_KEY') ? 'SI' : 'NO') . PHP_EOL; 
echo 'CODA_DOC_ID: ' . (defined('CODA_DOC_ID') ? CODA_DOC_ID : 'NO') . PHP_EOL;"
```

**Debe mostrar:**
```
Status: OK
CODA_API_KEY configurado: SI
CODA_DOC_ID: vjnLYcbb8p
```

**Si muestra error:**
- Si dice "CODA_API_KEY no está configurada" → volver al paso 3, verificar que `.env` tiene el valor
- Si dice "file not found" → verificar que estás en la carpeta correcta

---

### PASO 7: Reiniciar servidor Python

Detener el servidor actual:
- Presionar `Ctrl + C` en la terminal donde corre `server.py`

Esperar 2 segundos.

Reiniciar:
```bash
python3 server.py
```

Debe mostrar (después de algunos segundos):
```
 * Running on http://127.0.0.1:5000
```

---

### PASO 8: Probar la aplicación

#### 8.1 Abrir en navegador

Abrir: **http://localhost:5000**

#### 8.2 Loginearse

- Username: (el que hayas configurado)
- Password: (la que hayas configurado)

Clic "Iniciar Sesión"

#### 8.3 Verificar que aparecen datos

En el dashboard deben aparecer:
- [ ] Tabla "OT" con órdenes de trabajo
- [ ] Tabla "Facturas" con facturas
- [ ] Tabla "GasCom" con gastos comerciales
- [ ] Tabla "Personal" con personal

Si aparecen datos → **ÉXITO! ✅**

Si no aparecen datos → ver sección "Solución de Problemas" abajo.

---

### PASO 9 (OPCIONAL): Probar botón de Sincronización

En la parte superior del dashboard, hay botón "📧 Sincronizar Gmail a Coda"

Clic en el botón → debe mostrar:
```
Iniciando canal de comunicación en vivo...
La base de datos de Coda está conectada correctamente.
Nota: La sincronización de correos y gastos bancarios se ejecuta de forma local...
[DONE] Proceso finalizado con éxito.
```

Si funciona → **ÉXITO! ✅**

---

## ✅ CHECKLIST FINAL

Marcar cada paso completado:

- [ ] `cd /home/user/Operaciones-INPROMETAL`
- [ ] `cp .env.template .env`
- [ ] Obtuve CODA_API_KEY de https://coda.io/account/settings#apiTokens
- [ ] Edité `.env` y guardé CODA_API_KEY
- [ ] Obtuve GEMINI_API_KEY de https://aistudio.google.com/app/apikey
- [ ] Edité `.env` y guardé GEMINI_API_KEY
- [ ] Ejecuté comando de verificación `grep -E "^CODA_API_KEY=|^GEMINI_API_KEY=" .env`
- [ ] Ejecuté test de PHP: `php -r "require 'public/api/coda_config.php'..."`
- [ ] Reinicié servidor Python con `python3 server.py`
- [ ] Abrí http://localhost:5000 en navegador
- [ ] Me logueé
- [ ] Aparecen datos de Coda en las tablas ✅

Si todos están marcados → **CONFIGURACIÓN COMPLETA**

---

## ❌ SOLUCIÓN DE PROBLEMAS

### Problema: "No aparecen datos en las tablas"

**Causa más probable:** CODA_API_KEY no está correcto

**Solución:**
```bash
# 1. Verificar que .env existe
test -f .env && echo "✅ .env existe" || echo "❌ .env no existe"

# 2. Verificar que tiene contenido
cat .env | head -30

# 3. Verificar que CODA_API_KEY está presente
grep "^CODA_API_KEY=" .env

# 4. Si está vacío o falta, editar nuevamente
nano .env
# Y rellenar CODA_API_KEY nuevamente
```

---

### Problema: "CODA_API_KEY no está configurada" (al ejecutar test PHP)

**Causa:** `.env` no tiene el valor configurado correctamente

**Solución:**

1. Verificar contenido de `.env`:
```bash
cat .env
```

2. Buscar la línea `CODA_API_KEY=`. Debe tener un valor después del `=`

3. Si está vacía (ej: `CODA_API_KEY=`), editar nuevamente:
```bash
nano .env
```

4. Asegurar que la línea sea:
```
CODA_API_KEY=d-1a2b3c4d5e6f7g8h...
```
(sin espacios, sin comillas, sin comentarios)

5. Guardar y volver a ejecutar el test PHP

---

### Problema: "Error al conectar a Coda" (código 401)

**Causa:** CODA_API_KEY es inválido o expiró

**Solución:**

1. Ir nuevamente a: https://coda.io/account/settings#apiTokens
2. Verificar que el token que copiaste es el correcto
3. Si cambió, actualizar en `.env`
4. Reiniciar servidor Python
5. Probar nuevamente

---

### Problema: "Archivo no encontrado: coda_config.php"

**Causa:** PHP no encuentra el archivo

**Solución:**

1. Verificar que estás en la carpeta correcta:
```bash
pwd
# Debe mostrar: /home/user/Operaciones-INPROMETAL
```

2. Verificar que el archivo existe:
```bash
ls -la public/api/coda_config.php
# Debe mostrar el archivo
```

3. Si no existe, está en `.gitignore` y necesita ser restaurado:
```bash
git checkout public/api/coda_config.php
```

---

### Problema: "Sintaxis inválida en PHP"

```bash
# Ejecutar este comando para verificar sintaxis
php -l public/api/coda_config.php
```

**Debe mostrar:**
```
No syntax errors detected in public/api/coda_config.php
```

Si muestra error → contactar al desarrollador (hay bug en el código).

---

## 📊 ARCHIVOS INVOLUCRADOS

| Archivo | Función | Cambios |
|---------|---------|---------|
| `.env` | Configuración sensible (API keys) | **TÚ LO CREAS** |
| `public/api/coda_config.php` | Carga variables de `.env` | Creado (ya en git) |
| `public/api/data.php` | Requiere coda_config.php y usa CODA_API_KEY | No cambió |
| `public/app.js` | Llamadas a sync.php | Se fijó EventSource |
| `public/api/sync.php` | Devuelve status de sincronización | No cambió |
| `.gitignore` | Excluye archivos sensibles | Se permitió coda_config.php |

---

## 🔗 REFERENCIAS

**API Documentation:**
- Coda API: https://coda.io/developers/apis/v1
- Gemini API: https://ai.google.dev/

**Ubicaciones de keys:**
- CODA_API_KEY: https://coda.io/account/settings#apiTokens
- GEMINI_API_KEY: https://aistudio.google.com/app/apikey
- CODA_DOC_ID: En la URL de tu documento Coda

---

## 🆘 SI ALGO SIGUE SIN FUNCIONAR

Enviar al desarrollador:

1. Output de: `grep -E "^CODA_API_KEY=|^GEMINI_API_KEY=" .env` (sin mostrar los tokens completos, solo primeros 10 caracteres)
2. Output de: `php -r "require 'public/api/coda_config.php'; echo 'CODA_API_KEY: ' . (defined('CODA_API_KEY') ? 'OK' : 'NO') . PHP_EOL;"`
3. Output del navegador (abrir DevTools con F12, ir a Console, copiar cualquier error rojo)
4. Timestamp exacto del error
5. URL donde ocurre el error

---

**Versión:** 1.0  
**Última actualización:** 2026-07-02  
**Contacto:** Para preguntas técnicas, revisar SETUP_GUIA_PASO_A_PASO.md
