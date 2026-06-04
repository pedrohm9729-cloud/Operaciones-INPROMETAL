# 🔑 GUÍA DE CONFIGURACIÓN DE KEYS Y CREDENCIALES

## ⚠️ CRÍTICO: Lee esto ANTES de desplegar a producción

---

## 🔐 Variables de Entorno Requeridas

Todas estas deben estar configuradas en tu `.env` o en variables del sistema:

### **1. CODA_API_KEY** (REQUERIDA)
```
¿Dónde obtenerla?
1. Ve a https://coda.io/account
2. Scroll a "API tokens"
3. Crea un nuevo token
4. Cópialo a tu .env

CODA_API_KEY=sk_...
```

### **2. CODA_DOC_ID** (REQUERIDA)
```
¿Dónde obtenerla?
1. Abre tu documento Coda en el navegador
2. La URL es: https://coda.io/d/[DOCUMENT_ID]
3. Ejemplo: https://coda.io/d/vjnLYcbb8p
4. Copia: vjnLYcbb8p

CODA_DOC_ID=vjnLYcbb8p
```

### **3. GEMINI_API_KEY** (REQUERIDA si usas chat IA)
```
¿Dónde obtenerla?
1. Ve a https://console.cloud.google.com
2. Crea un proyecto
3. Habilita "Generative Language API"
4. Crea credenciales (API Key)
5. Cópialo a .env

GEMINI_API_KEY=AIza...
```

---

## ✅ Checklist: ¿Tengo todo configurado?

- [ ] `.env` creado (copié de `.env.example`)
- [ ] `CODA_API_KEY` tiene valor real (no vacío)
- [ ] `CODA_DOC_ID` tiene valor real (tu document ID)
- [ ] `GEMINI_API_KEY` tiene valor real (si usas chat)
- [ ] `.env` está en `.gitignore` (NO en git)
- [ ] `coda_key.txt` eliminado (ya no se usa)

---

## 🚨 Errores Comunes

### Error 1: "CODA_API_KEY no configurada"
```
Significa: La variable de entorno no está cargada

Solución:
1. Verifica que .env existe en la raíz del proyecto
2. Verifica que contiene: CODA_API_KEY=tu_key
3. Reinicia el servidor: python3 server.py
```

### Error 2: "CODA_DOC_ID no configurada"
```
Significa: Falta CODA_DOC_ID en .env

Solución:
1. Abre tu documento Coda
2. Copia el ID de la URL
3. Agrega a .env: CODA_DOC_ID=vjnLYcbb8p
```

### Error 3: "Falta el archivo de configuración coda_config.php"
```
Significa: En Hostinger falta coda_config.php

Solución:
1. Crea manualmente: /public/api/coda_config.php
2. Contenido:
   <?php
   define('CODA_API_KEY', getenv('CODA_API_KEY'));
   define('GEMINI_API_KEY', getenv('GEMINI_API_KEY'));
   define('CODA_DOC_ID', getenv('CODA_DOC_ID'));
   ?>
3. NO commits este archivo
```

---

## 🏪 En Hostinger: ¿Cómo configurar variables de entorno?

### Opción 1: Archivo .env (Recomendado)
```bash
# SSH a Hostinger
ssh tu_usuario@tu_dominio.com
cd public_html/operaciones-inprometal

# Crear .env
nano .env

# Pegar contenido:
CODA_API_KEY=tu_key_real
CODA_DOC_ID=vjnLYcbb8p
GEMINI_API_KEY=tu_key_real

# Guardar (Ctrl+X, Y, Enter)
```

### Opción 2: Variables de sistema (Si Hostinger lo permite)
```bash
# En panel de Hostinger:
Dashboard → Environment → Variables
CODA_API_KEY = tu_key_real
CODA_DOC_ID = vjnLYcbb8p
GEMINI_API_KEY = tu_key_real
```

### Opción 3: coda_config.php (Para PHP)
```bash
# Crear archivo en Hostinger:
/public_html/operaciones-inprometal/public/api/coda_config.php

Contenido:
<?php
define('CODA_API_KEY', getenv('CODA_API_KEY'));
define('GEMINI_API_KEY', getenv('GEMINI_API_KEY'));
define('CODA_DOC_ID', getenv('CODA_DOC_ID'));
?>
```

---

## 🔒 Seguridad: Qué NO hacer

```
❌ NO hagas esto:
1. No copies .env a GitHub
2. No escribas keys en el código
3. No compartas .env por email
4. No dejes keys en comentarios
5. No publicites tus IDs de Coda

✅ HAZLO así:
1. Archivo .env local (nunca en git)
2. Keys en variables de entorno
3. Coda_config.php sin compartir
4. .env y coda_config.php en .gitignore
5. Regenera keys si accidentalmente se exponen
```

---

## 📋 Estructura Final esperada

```
Tu proyecto en Hostinger:
/public_html/operaciones-inprometal/
├── .env                    ← AQUÍ VAN LAS KEYS (NO en git)
├── server.py
├── public/
│   ├── api/
│   │   ├── coda_config.php  ← AQUÍ TAMBIÉN (NO en git)
│   │   ├── login.php
│   │   └── chat.php
│   ├── app.js
│   └── index.html
└── ...
```

---

## ✔️ Testing: ¿Está todo bien configurado?

```bash
# En tu máquina local:
python3 server.py

# Si ves:
"Pasarela Coda CRUD iniciada exitosamente"
✅ KEYS ESTÁN BIEN

# Si ves:
"ValueError: CODA_API_KEY no configurada"
❌ FALTA CONFIGURAR .env
```

---

**Versión:** 1.0
**Fecha:** 2026-06-04
**Importante:** Revisa esto ANTES de publicar a producción
