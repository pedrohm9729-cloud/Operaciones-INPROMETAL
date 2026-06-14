# 🔴 DIAGNÓSTICO COMPLETO: Error de Sincronización Persistente

**Estado:** IDENTIFICADO Y SOLUCIONABLE  
**Fecha:** 2026-06-07  
**Responsables:** Auditoría de Código / Antigravity  

---

## 📊 RESUMEN EJECUTIVO

El error **"Error de conexión con el script de sincronización"** persiste porque **faltan 2 archivos CRÍTICOS**:

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `.env` | Variables de entorno (CODA_API_KEY, GEMINI_API_KEY) | ❌ NO EXISTE |
| `credentials.json` | Credenciales de Google OAuth para Gmail | ❌ NO EXISTE |
| `token.json` | Token de acceso de Google (generado por OAuth) | ❌ NO EXISTE |

**Sin estos archivos, gastos_bancarios.py FALLA inmediatamente.**

---

## 🔴 CAUSA RAÍZ DEL ERROR

### Cadena de Fallos:

```
1. Usuario clickea "Sincronizar Gmail a Coda"
   ↓
2. server.py ejecuta: python gastos_bancarios.py --non-interactive
   ↓
3. gastos_bancarios.py intenta cargar GEMINI_API_KEY:
   GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
   if not GEMINI_API_KEY:
       raise ValueError("GEMINI_API_KEY no configurada...")
   ↓
4. Como NO EXISTE .env → GEMINI_API_KEY está vacío
   ↓
5. ❌ FALLA: ValueError: GEMINI_API_KEY no configurada
   ↓
6. server.py captura la excepción:
   except Exception as e:
       self.wfile.write(f"data: [ERROR] {error_msg}\n\n")
   ↓
7. Frontend recibe: "Error de conexión con el script de sincronización"
```

### Problema Secundario (aún sin resolver):

Incluso si existiera `.env`, el script fallaría en autenticación de Gmail:

```python
# gastos_bancarios.py línea 243:
if os.path.exists(TOKEN):
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

# Si token.json NO existe (y NUNCA lo hizo):
else:
    flow = InstalledAppFlow.from_client_secrets_file(CREDENCIALES, SCOPES)
    # ❌ FALLA: credentials.json NO EXISTE
    creds = flow.run_local_server(port=0)
    # ❌ FALLA ADICIONAL: En Hostinger (headless), no hay navegador
```

---

## 🔍 VERIFICACIÓN DE ARCHIVOS FALTANTES

### Archivos que DEBEN existir:

```bash
# 1. .env (variables de entorno)
ls -la /home/user/Operaciones-INPROMETAL/.env
# ❌ NO EXISTE

# 2. credentials.json (credenciales de Google)
find /home/user/Operaciones-INPROMETAL -name credentials.json
# ❌ NO EXISTE

# 3. token.json (token de acceso)
find /home/user/Operaciones-INPROMETAL -name token.json
# ❌ NO EXISTE
```

### Lo que SÍ existe:

```bash
✅ .env.example (template - necesita ser copiado a .env)
✅ gastos_bancarios.py (código que ejecuta la sincronización)
✅ server.py (que ejecuta gastos_bancarios.py)
✅ REPORTE_ERROR_SINCRONIZACION.md (documenta los cambios a variables de entorno)
```

---

## ✅ SOLUCIÓN (3 PASOS)

### PASO 1: Crear archivo `.env`

```bash
cd /home/user/Operaciones-INPROMETAL

# Copiar template:
cp .env.example .env

# Editar con valores REALES:
nano .env
```

**Contenido necesario en .env:**

```env
# API KEYS (obtener del dashboard Coda y Google Cloud)
CODA_API_KEY=tu_coda_api_key_real_aqui
CODA_DOC_ID=vjnLYcbb8p
GEMINI_API_KEY=tu_gemini_api_key_real_aqui

# Resto de configuración
PORT=5000
ENVIRONMENT=development
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_WINDOW=900
DEBUG=false
```

**¿De dónde obtener las keys?**

- **CODA_API_KEY**: 
  - Ir a https://coda.io/account/settings#apiTokens
  - Copiar el token API

- **GEMINI_API_KEY**:
  - Ir a https://aistudio.google.com/app/apikey
  - Crear API key (Google Cloud Console)
  - Copiar el token

- **CODA_DOC_ID**:
  - Está en la URL: https://coda.io/d/{CODA_DOC_ID}/...
  - Valor actual: `vjnLYcbb8p`

### PASO 2: Obtener credenciales de Google OAuth

**OPCIÓN A: Si tienes acceso a interfaz gráfica (máquina local)**

1. Descargar `credentials.json`:
   - Google Cloud Console → Crear proyecto
   - OAuth 2.0 → Crear credenciales (Desktop App)
   - Descargar JSON
   - Guardar en `/home/user/Operaciones-INPROMETAL/credentials.json`

2. Ejecutar gastos_bancarios.py en LOCAL:
   ```bash
   python3 gastos_bancarios.py
   # Se abrirá navegador, autorizar acceso a Gmail
   # Se genera automáticamente token.json
   ```

3. Copiar `token.json` generado a Hostinger:
   ```bash
   scp token.json usuario@ops.inprometal.com:~/operaciones-inprometal/
   scp credentials.json usuario@ops.inprometal.com:~/operaciones-inprometal/
   ```

**OPCIÓN B: Usar Service Account (recomendado para servidores)**

1. Google Cloud Console → Crear Service Account
2. Descargar JSON → guardar como `credentials.json`
3. Modificar gastos_bancarios.py para usar service account:

```python
# ANTES (OAuth interactivo):
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(CREDENCIALES, SCOPES)

# DESPUÉS (Service Account):
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file(
    CREDENCIALES,
    scopes=SCOPES
)
# NO necesita flujo interactivo, funciona en headless
```

---

## 🔐 SEGURIDAD: Gestión de Secretos en Producción

### Local (desarrollo):
✅ Guardar `.env` en `.gitignore` (YA ESTÁ)
✅ Guardar `credentials.json` en `.gitignore` (NECESITA SER AGREGADO)
✅ Guardar `token.json` en `.gitignore` (NECESITA SER AGREGADO)

### Hostinger (producción):
⚠️ **NO** subir `.env` a GitHub
⚠️ **NO** subir `credentials.json` a GitHub
⚠️ **NO** subir `token.json` a GitHub

**En su lugar:**
1. Subir archivos manualmente vía SFTP
2. O usar variables de entorno del sistema Hostinger
3. O usar AWS Secrets Manager / Google Cloud Secret Manager

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Para Antigravity (o quien despliegue):

- [ ] **PASO 1:** Crear `.env` en `/home/user/Operaciones-INPROMETAL/`
  - [ ] Llenar CODA_API_KEY (real)
  - [ ] Llenar GEMINI_API_KEY (real)
  - [ ] Llenar CODA_DOC_ID (default: vjnLYcbb8p)

- [ ] **PASO 2:** Obtener credenciales de Google
  - [ ] Descargar `credentials.json` de Google Cloud Console
  - [ ] Guardar en `/home/user/Operaciones-INPROMETAL/`
  - [ ] Opción A: Generar `token.json` en máquina local
  - [ ] Opción B: Usar Service Account (modificar código)

- [ ] **PASO 3:** En Hostinger
  - [ ] Subir `.env` vía SFTP
  - [ ] Subir `credentials.json` vía SFTP
  - [ ] Subir `token.json` vía SFTP (si Opción A) O usar Service Account

- [ ] **PASO 4:** Probar sincronización
  - [ ] SSH: `ssh usuario@ops.inprometal.com`
  - [ ] Verificar archivos: `ls -la ~/operaciones-inprometal/.env credentials.json token.json`
  - [ ] Probar script: `python3 gastos_bancarios.py --non-interactive`
  - [ ] En navegador: Clickear "Sincronizar Gmail a Coda"
  - [ ] ✅ Debe funcionar SIN errores

---

## 🔧 CONFIGURACIÓN DE .gitignore

Agregar si NO está (evitar subir secretos):

```bash
# En .gitignore:
.env
.env.local
.env.*.local
credentials.json
token.json
*.pyc
__pycache__/
```

**Verificar que está agregado:**

```bash
grep -E "\.env|credentials|token" /home/user/Operaciones-INPROMETAL/.gitignore
# Debe mostrar estas líneas
```

---

## 📞 PRÓXIMAS ACCIONES

### INMEDIATAMENTE:
1. **Crear `.env`** con CODA_API_KEY y GEMINI_API_KEY
2. **Obtener `credentials.json`** de Google Cloud Console
3. **Desplegar cambios** a Hostinger

### ENTONCES:
- Error desaparecerá
- Sincronización funcionará
- Dashboard mostrará datos de Gmail correctamente

### SI AÚN FALLA:
- Revisar logs: `tail -100 /var/log/php-errors.log`
- Revisar logs de Python: `python3 gastos_bancarios.py` (debug)
- Verificar conectividad a Gmail: `curl -I https://www.googleapis.com`
- Verificar conectividad a Coda: `curl -I https://coda.io`

---

## 📊 ESTADO ACTUAL vs ESPERADO

| Componente | Antes | Ahora | Esperado |
|-----------|-------|-------|----------|
| **gastos_bancarios.py** | Usa hardcoded paths + archivos no existen | ✅ Usa variables de entorno | ✅ Variables de entorno |
| **CODA_API_KEY** | Vacío (hardcoded '') | ❌ Vacío (no existe .env) | ✅ Configurado en .env |
| **GEMINI_API_KEY** | Vacío (archivos no existen) | ❌ Vacío (no existe .env) | ✅ Configurado en .env |
| **credentials.json** | N/A | ❌ No existe | ✅ Existe (Google OAuth) |
| **token.json** | N/A | ❌ No existe | ✅ Existe (generado por OAuth) |
| **Sincronización** | ❌ Falla siempre | ❌ Falla: GEMINI_API_KEY vacío | ✅ Funciona |

---

## 📚 REFERENCIAS

- Google OAuth Flow: https://developers.google.com/identity/protocols/oauth2
- Service Account: https://cloud.google.com/docs/authentication/application-default-credentials
- Coda API: https://coda.io/developers/apis/stable
- Gemini API: https://ai.google.dev/tutorials/python_quickstart

---

**Conclusión:** El código está CORRECTO. Los archivos FALTAN. Deplegar `.env` y `credentials.json` resolverá el problema.

