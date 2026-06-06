# 🔐 GUÍA DE SEGURIDAD Y MEJORES PRÁCTICAS - OPERACIONES INPROMETAL

## 📌 ÍNDICE
1. [Configuración Inicial](#configuración-inicial)
2. [Manejo de Secretos](#manejo-de-secretos)
3. [Autenticación y Sesiones](#autenticación-y-sesiones)
4. [Protección CSRF](#protección-csrf)
5. [Validación de Entrada](#validación-de-entrada)
6. [Prevención de XSS](#prevención-de-xss)
7. [Logging y Auditoría](#logging-y-auditoría)
8. [Despliegue Seguro](#despliegue-seguro)

---

## 🚀 Configuración Inicial

### 1. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar con valores reales
nano .env
```

**Variables requeridas:**
- `CODA_API_KEY`: Token de autenticación de Coda (obtener en https://coda.io/account)
- `GEMINI_API_KEY`: Token de API de Google Gemini (obtener en console.cloud.google.com)
- `ALLOWED_ORIGINS`: Lista de dominios permitidos para CORS

### 2. Instalar Dependencias

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Iniciar el Servidor

```bash
python3 server.py
# El servidor se iniciará en http://localhost:5000
```

---

## 🔑 Manejo de Secretos

### ✅ CORRECTO: Usar Variables de Entorno

```python
# server.py
CODA_API_KEY = os.environ.get('CODA_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not CODA_API_KEY:
    raise ValueError("CODA_API_KEY no configurada en variables de entorno")
```

### ❌ INCORRECTO: Hardcoded o Archivos sin Protección

```python
# MAL - Nunca hagas esto
CODA_API_KEY = "sk-abc123def456"  # Visible en Git
with open('keys.txt') as f:
    API_KEY = f.read()  # Archivo sin gitignore
```

### 📋 Checklist de Secretos

- [ ] Todas las claves API están en `.env`
- [ ] `.env` está en `.gitignore`
- [ ] Archivos `coda_key.txt`, `gemini_key.txt` están gitignored
- [ ] No hay contraseñas en comentarios de código
- [ ] Las credenciales se reclaman de variable de entorno, no hardcoded

---

## 🔐 Autenticación y Sesiones

### Formato de Sesión Almacenada

```python
SESIONES_ACTIVAS = {
    'token_session_id': {
        'username': 'admin',
        'created_at': 1686840000,
        'last_activity': 1686840300,
        'ip': '192.168.1.100'
    }
}
```

### Validación de Sesión

```python
def es_sesion_valida(self):
    token = self.obtener_session_id()
    if token not in SESIONES_ACTIVAS:
        return False

    session_data = SESIONES_ACTIVAS[token]
    # Timeout: 30 minutos
    if time.time() - session_data.get('created_at') > 1800:
        del SESIONES_ACTIVAS[token]
        return False

    # Actualizar último acceso
    SESIONES_ACTIVAS[token]['last_activity'] = time.time()
    return True
```

### Cambiar Contraseña del Admin

1. **Acceder al archivo de autenticación:**
   ```bash
   cat dashboard_auth.json
   ```

2. **Generar nuevo hash de contraseña:**
   ```python
   import hashlib
   import secrets
   from server import hash_password_pbkdf2

   new_password = "mi_nueva_contraseña_segura"
   salt, pwd_hash = hash_password_pbkdf2(new_password)
   print(f"Salt: {salt}")
   print(f"Hash: {pwd_hash}")
   ```

3. **Actualizar archivo:**
   ```bash
   # dashboard_auth.json
   {
       "username": "admin",
       "salt": "<nuevo_salt>",
       "password_hash": "<nuevo_hash>",
       "scheme": "pbkdf2_sha256"
   }
   ```

---

## 🛡️ Protección CSRF

### Cómo Funciona

1. **Login:** Backend genera `csrf_token` y lo devuelve al cliente
2. **Cliente:** Almacena token en `sessionStorage`
3. **Peticiones Protegidas:** Cliente envía token en header `X-CSRF-Token`
4. **Backend:** Valida token antes de procesar petición

### En Frontend (JavaScript)

```javascript
// Cargar token después de login
const csrfToken = sessionStorage.getItem('csrf_token');

// Enviar en peticiones POST/PUT/DELETE
fetch('/api/coda/add', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken  // ← OBLIGATORIO
    },
    body: JSON.stringify({...})
});
```

### En Backend (Python)

```python
def do_POST(self):
    session_id = self.obtener_session_id()
    csrf_token = self.headers.get('X-CSRF-Token', '')

    if not validar_csrf_token(session_id, csrf_token):
        self.enviar_json(403, {'error': 'Token CSRF inválido'})
        return
    # Procesar petición
```

---

## ✅ Validación de Entrada

### En Backend (Python)

```python
def resolver_columnas(table_name, abstract_cells):
    """Valida y resuelve celdas antes de enviar a Coda"""
    for cell in abstract_cells:
        key = cell.get('key')
        value = cell.get('value')

        # Validar campo existe
        if key not in CODA_COLS[table_name]:
            return None, f"Columna desconocida: {key}"

        # Validar que números no sean NaN
        if isinstance(value, float) and value != value:  # NaN
            return None, f"Valor inválido (NaN) en: {key}"

        # Validar strings no vacíos
        if isinstance(value, str) and not value.strip():
            return None, f"Campo vacío: {key}"

    return resolved_cells, None
```

### En Frontend (JavaScript)

```javascript
// Validar entrada antes de enviar
const codigo = document.getElementById('ot-code').value.trim();
const precio = parseFloat(document.getElementById('ot-price').value);

if (!codigo) {
    alert('El código no puede estar vacío');
    return;
}

if (isNaN(precio) || precio < 0) {
    alert('El precio debe ser un número >= 0');
    return;
}

// Si pasa validación, enviar al servidor
```

---

## 🚫 Prevención de XSS

### ✅ CORRECTO: Usar DOMPurify

```javascript
// Sanitizar HTML antes de renderizar
if (sender === 'bot') {
    const formattedHTML = formatMarkdown(text);
    bubbleDiv.innerHTML = DOMPurify.sanitize(formattedHTML, {
        ALLOWED_TAGS: ['strong', 'em', 'br', 'table', 'tr', 'th', 'td'],
        ALLOWED_ATTR: []
    });
} else {
    bubbleDiv.textContent = text;  // Para mensajes del usuario
}
```

### ❌ INCORRECTO: innerHTML sin sanitizar

```javascript
// MAL - Permite inyección de scripts
bubbleDiv.innerHTML = userInput;  // ❌ XSS vulnerability!
```

### Cargar DOMPurify desde CDN

```html
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"
        integrity="sha384-+b/zV1a8XjLyK1Bsi3aJ/t8mflSVy4U4HZzFu/WLOltdH5IDVJ0y7y3F7ZJjrJl8O"
        crossorigin="anonymous"></script>
```

---

## 📝 Logging y Auditoría

### Registrar Eventos Importantes

```python
# En handle_api_login
print(f"[✓] Inicio de sesión exitoso para usuario: {username} desde IP: {client_ip}")

# En handle_api_coda_add
print(f"[✓] Registro agregado en tabla: {table_name} por usuario: {username}")

# En handle_api_logout
print(f"[✓] Cierre de sesión para usuario: {username}")
```

### Monitorear Eventos Sospechosos

```python
# Rate limiting excedido
print(f"[!] Rate limit excedido para IP: {client_ip}")

# CSRF inválido
print(f"[!] Token CSRF inválido desde IP: {client_ip}")

# Credenciales inválidas
print(f"[!] Intento de login fallido para usuario: {username} desde IP: {client_ip}")
```

### Guardar Logs en Archivo

```python
import logging

logging.basicConfig(
    filename='/var/log/operaciones-inprometal/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info(f"Inicio de sesión: {username}")
```

---

## 🚀 Despliegue Seguro

### En Producción

#### 1. Usar HTTPS Obligatorio

```python
# En server.py
if ENVIRONMENT != 'development':
    # Redirigir HTTP a HTTPS
    if 'X-Forwarded-Proto' not in self.headers or self.headers['X-Forwarded-Proto'] != 'https':
        self.redirigir_a_login()
```

#### 2. Configurar Certificados SSL

```bash
# Usar Let's Encrypt
sudo certbot certonly --standalone -d operaciones.inprometal.com

# Especificar en servidor
PORT_HTTPS = 443
SSL_CERT = '/etc/letsencrypt/live/operaciones.inprometal.com/fullchain.pem'
SSL_KEY = '/etc/letsencrypt/live/operaciones.inprometal.com/privkey.pem'
```

#### 3. Usar Reverse Proxy (Nginx/Apache)

```nginx
# /etc/nginx/sites-available/operaciones-inprometal

server {
    listen 443 ssl http2;
    server_name operaciones.inprometal.com;

    ssl_certificate /etc/letsencrypt/live/operaciones.inprometal.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/operaciones.inprometal.com/privkey.pem;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 4. Usar Gestor de Secretos

```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name operaciones-inprometal-api-keys \
    --secret-string '{"CODA_API_KEY":"...","GEMINI_API_KEY":"..."}'

# En Python
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='operaciones-inprometal-api-keys')
```

#### 5. Usar Docker + Kubernetes

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
```

```bash
# Ejecutar
docker build -t operaciones-inprometal .
docker run -e CODA_API_KEY=... -e GEMINI_API_KEY=... -p 5000:5000 operaciones-inprometal
```

---

## 🔍 Auditoría de Seguridad Periódica

### Semanal
- [ ] Revisar logs de login fallidos
- [ ] Verificar patrones de rate limiting activados
- [ ] Revisar cambios de credenciales

### Mensual
- [ ] Ejecutar análisis de dependencias (`pip audit`)
- [ ] Revisar permisos de archivos
- [ ] Auditar acceso de usuarios

### Trimestral
- [ ] Análisis de vulnerabilidades completo (OWASP ZAP)
- [ ] Penetration testing simulado
- [ ] Revisión de cambios de código en seguridad

---

## 📚 Referencias Externas

- [OWASP Top 10 2023](https://owasp.org/Top10/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Versión:** 1.0
**Última actualización:** 2026-06-04
**Próxima revisión:** 2026-06-11
