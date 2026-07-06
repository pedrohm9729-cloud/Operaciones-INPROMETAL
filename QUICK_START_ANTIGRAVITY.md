# ⚡ QUICK START - 3 PASOS EN 5 MINUTOS

## El Problema (YA FIJO)
Datos de Coda no cargaban → Error de conexión en sync

**Causa:** Falta `.env` con API keys

**Solución:** Crear `.env` y configurar 2 tokens

---

## ✅ Los 3 Pasos

### PASO 1: Crear .env
```bash
cd /home/user/Operaciones-INPROMETAL
cp .env.template .env
```

### PASO 2: Obtener CODA_API_KEY
1. Ir a: https://coda.io/account/settings#apiTokens
2. Copiar token (empieza con `d-`)
3. Ejecutar:
```bash
nano .env
```
4. Buscar línea `CODA_API_KEY=` y pegar el token
5. Guardar: Ctrl+X, Y, Enter

### PASO 3: Obtener GEMINI_API_KEY
1. Ir a: https://aistudio.google.com/app/apikey
2. Clic "Create API Key"
3. Copiar clave
4. En `.env` (comando `nano .env`), buscar `GEMINI_API_KEY=` y pegar
5. Guardar: Ctrl+X, Y, Enter

---

## 🧪 Verificar

```bash
php -r "require 'public/api/coda_config.php'; echo 'OK';"
```

Si muestra `OK` → ✅ Listo

---

## 🚀 Reiniciar y Probar

```bash
# En otra terminal:
python3 server.py

# En navegador:
http://localhost:5000
```

**Debe mostrar datos de Coda en las tablas** ✅

---

## 📁 Más Info

- Guía completa: `GUIA_PARA_ANTIGRAVITY.md`
- Guía detallada: `SETUP_GUIA_PASO_A_PASO.md`
- Script automático: `bash CONFIGURAR_ENV_RAPIDO.sh`

---

**¿Duda?** Ver `GUIA_PARA_ANTIGRAVITY.md` sección "Solución de Problemas"
