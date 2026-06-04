# ❓ PREGUNTAS PARA REVISIÓN TÉCNICA POR OTRA IA

**Contexto:** Estoy rediseñando una app web de operaciones (Python + PHP → Python unificado)

---

## 🎯 PREGUNTAS PRINCIPALES (Lee esto a otra IA)

### 1. **¿Debería usar FastAPI, Flask o Django?**

**Mi situación:**
- App pequeña para 1-2 usuarios solo
- Necesito conectar a Coda API y Google Sheets
- Necesito seguridad robusta (CSRF, rate limiting, XSS prevention)
- Solo es un API REST + frontend estático

**Pregunta:** ¿Cuál framework es mejor considerando que tendré máximo 50-100 peticiones/día?

---

### 2. **¿Coda + Google Sheets es suficiente como "database"?**

**Mi situación:**
- Coda como BD principal (OT, Facturas, Gastos, Personal) ~500 filas total
- Google Sheets como reportería adicional
- Necesito actualizar datos en tiempo real
- Límite de Coda: 500 peticiones/minuto

**Preguntas:**
- ¿O debería usar PostgreSQL desde el inicio?
- ¿Un caché de 20 segundos es apropiado?
- ¿Cuáles son los límites reales de escala de Coda?

---

### 3. **¿Es realista mi timeline de 16 horas?**

**Mi plan:**
- Fase 1 (4h): Setup FastAPI + Autenticación
- Fase 2 (6h): Clientes Coda + Sheets
- Fase 3 (4h): Seguridad completa + testing
- Fase 4 (2h): Docker + deploy

**Pregunta:** ¿Es realista o me falta algo?

---

### 4. **¿Qué tan excesivas son mis medidas de seguridad?**

**Lo que implementé:**
- CSRF tokens por sesión
- Rate limiting: 5 intentos/15 min
- Session timeout: 30 minutos
- DOMPurify en chat
- CORS whitelist
- PBKDF2 para contraseñas

**Pregunta:** ¿Es overkill para un solo usuario accediendo información sensible de su empresa?

---

### 5. **¿Debería agregar 2FA ahora o después?**

**Mi pensamiento:**
- Solo 1-2 usuarios
- Información sensible (finanzas)
- Quizá innecesario inicialmente

**Pregunta:** ¿Riesgo real de no tenerlo? ¿Cuándo debería implementarlo?

---

### 6. **¿Redis vs Caché en memoria?**

**Mi situación:**
- Desarrollo: localhost
- Producción: VPS o Heroku barato

**Opciones:**
- A) Redis ($10/mes)
- B) Python dict en memoria (gratis, pierde datos en restart)
- C) Archivos JSON (gratis, lento)

**Pregunta:** ¿Qué recomiendas considerando que tengo ~50 usuarios/día máximo?

---

### 7. **¿Necesito API Gateway?**

**Alternativas:**
- A) FastAPI solo (simple)
- B) FastAPI + API Gateway tipo Kong (complejo pero profesional)

**Pregunta:** ¿Para este proyecto (1-2 usuarios, pequeño volumen), ¿vale la pena la complejidad?

---

### 8. **¿Debería usar JWT o Session Cookies?**

**Mi contexto:**
- Solo frontend web (no apps móviles)
- No necesito múltiples dispositivos
- No necesito logout en otros dispositivos

**Pregunta:** ¿Session cookies simples son suficientes o debería usar JWT?

---

### 9. **¿Cómo manejo los secretos en Producción?**

**Mis opciones:**
- A) Variables de entorno en VPS
- B) Heroku Config Vars (si uso Heroku)
- C) AWS Secrets Manager (probablemente overkill)
- D) Archivo .env encriptado (no recomendado)

**Pregunta:** ¿Cuál es la forma más segura y simple para producción?

---

### 10. **¿Debería usar contenedores (Docker)?**

**Mi debate:**
- Docker agrega complejidad
- Pero facilita deploy reproducible

**Pregunta:** ¿Para un solo servidor VPS con 1-2 usuarios, ¿es necesario Docker?

---

## 🏗️ PREGUNTAS SOBRE ARQUITECTURA

### 11. **¿Separar frontend y backend o servir juntos?**

**Opciones:**
- A) FastAPI sirve archivos estáticos (index.html, app.js)
- B) Frontend separado (Node.js dev server)
- C) Backend + CDN (más complejo)

**Pregunta:** ¿Cuál es mejor para mantener/desplegar?

---

### 12. **¿Hacer CRUD en Coda o cachear y guardar en BD local?**

**Mi situación:**
- Cambios poco frecuentes (usuario agrega ~1-2 registros/día)
- Necesito auditoría de cambios

**Opciones:**
- A) Escribir directo en Coda (más simple)
- B) Guardar en PostgreSQL local + sincronizar (más complejo)

**Pregunta:** ¿Cuál es mejor para auditoria y rendimiento?

---

### 13. **¿Qué sí necesito de las auditorías de logs?**

**Actual plan:**
```
[✓] Usuario login
[✓] Usuario logout
[✓] CSRF inválido
[✓] Rate limit excedido
[?] Cada petición de API
[?] Cambios en datos
```

**Pregunta:** ¿Qué nivel de detalle es realista para una app pequeña?

---

### 14. **¿Cómo pruebo la seguridad sin expertos?**

**Mi herramientas:**
- pytest para unit tests
- test_security.py (10 tests automatizados)
- OWASP ZAP (escaneo gratuito)

**Pregunta:** ¿Hay algo más que deba hacer antes de producción?

---

### 15. **¿Qué pasaría si Coda o Sheets se caen?**

**Mi plan:**
- Caché de 20 segundos (datos parcialmente disponibles)
- No hay sincronización offline

**Pregunta:** ¿Debería tener backup/fallback? ¿O es aceptable el downtime?

---

## 💼 PREGUNTAS SOBRE NEGOCIO

### 16. **¿Debería cobrar por esto o mantenerlo privado?**

**Mis opciones:**
- A) Solo para mí (privado, sin monetizar)
- B) Venderlo a otros talleres metalmecánicos
- C) SaaS (software as service con suscripción)

**Pregunta:** ¿Cómo debería pensar en escalabilidad?

---

### 17. **¿Cuál es el costo real anual?**

**Desglose:**
- Coda API: $50/mes
- Google Sheets: Gratis
- Gemini API: $5-10/mes
- VPS: $5-20/mes
- Otros: ¿?

**Pregunta:** ¿Me falta algo en el presupuesto?

---

### 18. **¿Debería usar una plataforma no-code en lugar de código?**

**Alternativas:**
- A) Metabase (BI tool gratuito)
- B) Looker (Google)
- C) Tableau (caro)
- D) Mi código personalizado

**Pregunta:** ¿Vale la pena programar o debería usar una herramienta lista?

---

## 📋 CÓMO PRESENTAR ESTO A OTRA IA

**Copiar y pegar esto:**

```
Contexto: Estoy rediseñando una app web de operaciones de una empresa 
metalmecánica (solo para mí/mi gerente para tomar decisiones).

Situación actual:
- Backend mixto: Python + PHP (vulnerable)
- Fuentes de datos: Coda API + Google Sheets
- Usuario: 1-2 personas, ~50 peticiones/día
- Dato sensible: Información financiera de la empresa

Propuesta: Unificar todo a Python con FastAPI

He identificado estas decisiones clave (en orden de importancia):
1. FastAPI vs Flask vs Django - ¿cuál?
2. Coda + Sheets suficiente o PostgreSQL desde inicio?
3. 16 horas realista para implementación?
4. ¿Medidas de seguridad son excesivas o insuficientes?
5. 2FA ahora o después?

¿Puedes revisar mi propuesta arquitectónica y darme feedback?

[Adjuntar: PROPUESTA_ARQUITECTURA.md]
```

---

## 🎯 RESUMEN DE DECISIONES PENDIENTES

| Decisión | Opciones | Mi preferencia | Necesita revisión |
|----------|----------|---|---|
| Framework backend | FastAPI / Flask / Django | **FastAPI** | ✅ |
| BD principal | Coda+Sheets / PostgreSQL | **Coda+Sheets** | ✅ |
| Cache | Memory / Redis / JSON | **Memory (dev), Redis (prod)** | ✅ |
| Autenticación | JWT / Sessions | **Sessions** | ✅ |
| 2FA | Ahora / Después | **Después** | ✅ |
| Secretos | Env vars / Secrets Manager | **Env vars** | ✅ |
| Docker | Sí / No | **Sí** | ✅ |
| Testing seguridad | pytest / OWASP ZAP | **Ambos** | ⚠️ Inseguro |

---

## 💡 NOTA IMPORTANTE

**Por favor indica a quien revise:**

> "Este es un proyecto real de una pequeña empresa. No es hipotético. 
> La retroalimentación debe balancear:
> - Seguridad robusta (datos sensibles)
> - Simplicidad de mantener (solo 1 dev)
> - Practicidad de presupuesto (~$100/mes máximo)
> - Probabilidad realista de completar (16 horas)"

---

**Documento preparado:** 2026-06-04
**Para:** Solicitud de revisión técnica a otra IA/experto
**Adjuntar:** PROPUESTA_ARQUITECTURA.md
