# 🔐 AUDITORÍA DE SEGURIDAD Y ARQUITECTURA - OPERACIONES INPROMETAL

## FECHA: 2026-06-04
## NIVEL: COMPLETO (Seguridad + Arquitectura)

---

## 📋 RESUMEN EJECUTIVO

El proyecto presenta **vulnerabilidades CRÍTICAS** que requieren corrección inmediata antes de producción. Se identificaron 18 issues, de los cuales:
- **5 CRÍTICOS** (Alto impacto, explotación fácil)
- **8 ALTOS** (Impacto moderado-alto, explotación posible)
- **5 MEDIOS** (Impacto bajo-moderado)

---

## 🔴 VULNERABILIDADES CRÍTICAS

### 1. **CORS Permisivo - Wildcard Origin**
**Ubicación:** `login.php:15`, `chat.php:4`
```php
header('Access-Control-Allow-Origin: ' . ($_SERVER['HTTP_ORIGIN'] ?? '*'));
```
**Riesgo:** Cualquier dominio puede acceder a los datos. El wildcard `*` con credenciales es CSRF attack.
**Impacto:** Robo de sesiones, datos, acceso no autorizado.
**Corrección:** Validar origin contra whitelist.

---

### 2. **Hardcoded Absolute Path Windows**
**Ubicación:** `server.py:609`
```python
python_exe = r"C:\Users\Phenmor\miniconda3\python.exe"
```
**Riesgo:** Exposición de estructura de directorios, usuario local, rutas del sistema.
**Impacto:** Information disclosure, facilita ataques posteriores.
**Corrección:** Usar variables de entorno o detectar dinámicamente.

---

### 3. **API Keys sin Encriptación**
**Ubicación:** `server.py:22-27` (CODA_API_KEY en variables de entorno o archivo plano)
**Riesgo:** Si alguien accede al servidor, obtiene las API keys de Coda/Gemini.
**Impacto:** Acceso no autorizado a APIs, exfiltración de datos.
**Corrección:** Usar gestión de secretos (env vars) + .gitignore.

---

### 4. **Validación CSRF Débil**
**Ubicación:** `server.py:246-271`
```python
def validar_csrf():
    return host_domain == origin_domain or 'localhost' in origin
```
**Riesgo:** Permite subdominios de cualquier dominio. No valida tokens CSRF.
**Impacto:** CSRF attacks en endpoints protegidos.
**Corrección:** Implementar CSRF tokens específicos por sesión.

---

### 5. **XSS en Chat - HTML sin Sanitizar**
**Ubicación:** `app.js:1185`
```javascript
bubbleDiv.innerHTML = formatMarkdown(text);
```
**Riesgo:** Respuestas de Gemini pueden contener scripts maliciosos.
**Impacto:** Ejecución de código malicioso en el navegador del usuario.
**Corrección:** Usar `textContent` o DOMPurify.

---

## 🟠 VULNERABILIDADES ALTAS

### 6. **Sin Rate Limiting en Login**
**Ubicación:** `server.py:366` (handle_api_login sin límites)
**Riesgo:** Fuerza bruta contra credenciales del admin.
**Corrección:** Implementar rate limiting con límite de intentos.

---

### 7. **Sesiones sin Timeout Explícito**
**Ubicación:** `server.py:42` (SESIONES_ACTIVAS es un set sin expiración)
**Riesgo:** Las sesiones nunca expiran automáticamente (max-age=86400 en cookie pero no en servidor).
**Corrección:** Implementar timeout de sesión en el servidor.

---

### 8. **Caché sin Invalidación Apropiada**
**Ubicación:** `server.py:110-115`
```python
CACHE_TTL = 20  # segundos
```
**Riesgo:** 20 segundos es muy poco para caché pero sin límite de tamaño.
**Corrección:** Limitar tamaño, añadir LRU eviction.

---

### 9. **Inyección Indirecta en Comandos del Sistema**
**Ubicación:** `server.py:614` (subprocess sin validación)
```python
cmd = [python_exe, script_path, '--non-interactive']
```
**Riesgo:** Aunque usa list(), el path del script podría ser manipulado.
**Corrección:** Validar ruta absoluta del script.

---

### 10. **Sin Validación de Tipos Estricta**
**Ubicación:** `app.js` (todo JSON se acepta sin validación)
**Riesgo:** Valores inesperados rompen el frontend o permiten inyecciones.
**Corrección:** Validar estructura con JSON Schema o zod.

---

### 11. **Datos Bancarios Expuestos en Frontend**
**Ubicación:** `app.js:715-716` (muestra cuentas BCP/BBVA)
**Riesgo:** Información sensible visible en código fuente.
**Corrección:** No mostrar números completos de cuentas.

---

### 12. **Sin Logging de Auditoría**
**Ubicación:** Ninguno (no hay registro de acciones)
**Riesgo:** No hay rastro de quién hizo qué, cuándo.
**Corrección:** Implementar audit log.

---

### 13. **Sin Validación en Middleware**
**Ubicación:** `login.php:59` (hash_equals existe pero comparación básica)
**Riesgo:** Timing attacks posibles en comparación de contraseñas.
**Corrección:** Ya usa `secrets.compare_digest` en Python. PHP puede mejorar.

---

## 🟡 VULNERABILIDADES MEDIAS

### 14. **Falta Validación de JSON en Frontend**
**Ubicación:** `app.js:263-274`
```javascript
const resJson = await response.json();
```
**Riesgo:** Si API devuelve JSON malformado, la app falla silenciosamente.
**Corrección:** Try-catch y validación.

---

### 15. **Cache de Archivos en Navegador Activo**
**Ubicación:** Archivo estático (app.js, style.css)
**Riesgo:** Usuario ve versión vieja al actualizar.
**Corrección:** Agregar Cache-Control: no-cache.

---

### 16. **Error Messages Verbosos**
**Ubicación:** `server.py:460-461`
```python
except Exception as e:
    print(f"Error en /api/data: {e}")
```
**Riesgo:** Información sensible en logs/respuestas.
**Corrección:** Logs detallados internos, respuestas genéricas al cliente.

---

### 17. **No hay Restricción de IP**
**Ubicación:** Servidor abierto a cualquier IP.
**Riesgo:** Acceso desde cualquier lugar (sin control de red).
**Corrección:** Implementar allowlist de IPs si es infraestructura privada.

---

### 18. **Archivos Estáticos sin Integrity Checks**
**Ubicación:** CDNs/archivos no verificados.
**Riesgo:** Si CDN es comprometida, código malicioso se sirve.
**Corrección:** Usar SRI (Subresource Integrity) en scripts externos.

---

## 📊 MATRIZ DE RIESGO

| Severidad | Cantidad | Crítica | Requiere Corrección Inmediata |
|-----------|----------|---------|-------------------------------|
| CRÍTICA   | 5        | Alto    | ✅ SÍ                          |
| ALTA      | 8        | Medio   | ✅ SÍ                          |
| MEDIA     | 5        | Bajo    | ⚠️ Recomendado                |

---

## 🛠️ PLAN DE CORRECCIÓN

### Fase 1: CRÍTICAS (Implementación Inmediata)
1. ✅ Fijar CORS a whitelist
2. ✅ Remover hardcoded paths
3. ✅ Sanitizar XSS en chat
4. ✅ Implementar CSRF tokens
5. ✅ Proteger API keys

### Fase 2: ALTAS (Implementación 1-2 días)
1. ✅ Rate limiting en endpoints
2. ✅ Timeout de sesiones
3. ✅ Validación de entrada
4. ✅ Audit logging

### Fase 3: MEDIAS (Implementación 1 semana)
1. ✅ Validación JSON Schema
2. ✅ Cache headers
3. ✅ Enmascaramiento de errores
4. ✅ SRI en recursos externos

---

## 🎯 RECOMENDACIONES ARQUITECTÓNICAS

### 1. **Unificar Backend a una Sola Plataforma**
Actualmente mezcla Python + PHP:
- **Opción 1:** Migrar todo a Python + Flask/Django
- **Opción 2:** Migrar todo a PHP moderno (Symfony/Laravel)
- **Beneficio:** Seguridad consistente, mantenimiento más fácil

### 2. **Implementar API Gateway**
Centralizar autenticación, rate limiting, validación:
```
Cliente → API Gateway (seguridad) → Backend services
```

### 3. **Usar Base de Datos Apropiada**
Actualmente todo en Coda (spreadsheet):
- Implementar PostgreSQL/MongoDB para datos críticos
- Mantener Coda solo como reportería
- Ventaja: Mejor control de acceso, auditoría, constraints

### 4. **Estructura de Carpetas**
```
/home/user/Operaciones-INPROMETAL/
├── backend/
│   ├── api/
│   │   ├── auth.py
│   │   ├── data.py
│   │   └── chat.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── csrf.py
│   │   └── rate_limit.py
│   ├── models/
│   ├── config.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── .env.example
├── docker-compose.yml
└── README.md
```

### 5. **Usar Docker**
Aislar dependencias, simplificar deploy:
```dockerfile
FROM python:3.11
# Elimina necesidad de paths hardcoded
```

---

## 📝 CHECKLIST DE CORRECCIONES APLICADAS

- [ ] CORS whitelist configurado
- [ ] Hardcoded paths removidos
- [ ] XSS sanitizado en chat
- [ ] CSRF tokens implementados
- [ ] Rate limiting en endpoints
- [ ] Audit logging implementado
- [ ] Validación de entrada centralizada
- [ ] Sesiones con timeout
- [ ] API keys en variables de entorno
- [ ] Documentación de seguridad creada

---

## 📚 Referencias de Seguridad Usadas

- OWASP Top 10 2023
- CWE/SANS Top 25
- NIST Cybersecurity Framework
- OWASP Cheat Sheets

---

**Auditado por:** Security Architect
**Próxima revisión:** 2026-06-11
