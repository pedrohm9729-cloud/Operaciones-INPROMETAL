#!/bin/bash
# ============================================================================
# SCRIPT RÁPIDO PARA ANTIGRAVITY - Configurar .env en 2 minutos
# ============================================================================
# Uso: bash CONFIGURAR_ENV_RAPIDO.sh

echo "🚀 CONFIGURADOR RÁPIDO DE .env"
echo "=============================="
echo ""

cd /home/user/Operaciones-INPROMETAL

# Paso 1: Crear .env
echo "📝 Paso 1: Creando .env desde plantilla..."
if [ -f .env ]; then
    echo "   ⚠️  .env ya existe. Haciendo backup..."
    cp .env .env.backup.$(date +%s)
fi
cp .env.template .env
echo "   ✅ Hecho"
echo ""

# Paso 2: Mostrar instrucciones para obtener keys
echo "🔑 Paso 2: Obtener API Keys"
echo "=============================="
echo ""
echo "A) CODA_API_KEY (OBLIGATORIO):"
echo "   1. Abrir: https://coda.io/account/settings#apiTokens"
echo "   2. Copiar el token (empieza con d-)"
echo "   3. Pegar cuando se pida"
echo ""
echo "B) GEMINI_API_KEY (RECOMENDADO):"
echo "   1. Abrir: https://aistudio.google.com/app/apikey"
echo "   2. Copiar la API key"
echo "   3. Pegar cuando se pida"
echo ""

read -p "Presiona ENTER para continuar..." dummy

# Paso 3: Solicitar keys interactivamente
echo ""
echo "📋 Ingresando valores..."
echo ""

read -p "Ingresa CODA_API_KEY (empieza con d-): " CODA_KEY
if [ -z "$CODA_KEY" ]; then
    echo "❌ Error: CODA_API_KEY es obligatoria"
    exit 1
fi

read -p "Ingresa GEMINI_API_KEY (opcional, presiona ENTER para saltar): " GEMINI_KEY

# Paso 4: Actualizar .env
echo ""
echo "💾 Actualizando .env..."

# Crear archivo temporal
temp_file=$(mktemp)

# Copiar .env y reemplazar valores
while IFS= read -r line; do
    if [[ $line =~ ^CODA_API_KEY= ]]; then
        echo "CODA_API_KEY=$CODA_KEY" >> "$temp_file"
    elif [[ $line =~ ^GEMINI_API_KEY= ]] && [ -n "$GEMINI_KEY" ]; then
        echo "GEMINI_API_KEY=$GEMINI_KEY" >> "$temp_file"
    else
        echo "$line" >> "$temp_file"
    fi
done < .env

mv "$temp_file" .env
echo "✅ Actualizado"
echo ""

# Paso 5: Verificar
echo "🔍 Verificando configuración..."
echo ""
grep "^CODA_API_KEY=" .env && echo "✅ CODA_API_KEY configurado"
grep "^GEMINI_API_KEY=" .env && echo "✅ GEMINI_API_KEY configurado"
grep "^CODA_DOC_ID=" .env
echo ""

# Paso 6: Test PHP
echo "🧪 Probando que coda_config.php carga correctamente..."
php -r "require 'public/api/coda_config.php';
echo '✅ Status: OK' . PHP_EOL;
echo '✅ CODA_API_KEY: Configurado' . PHP_EOL;
echo '✅ CODA_DOC_ID: ' . CODA_DOC_ID . PHP_EOL;" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ CONFIGURACIÓN COMPLETA"
    echo ""
    echo "PRÓXIMOS PASOS:"
    echo "1. Reiniciar servidor Python: Ctrl+C en server.py, luego python3 server.py"
    echo "2. Abrir http://localhost:5000"
    echo "3. Verificar que aparecen datos de Coda en las tablas"
else
    echo ""
    echo "❌ Error en configuración. Revisar .env manualmente:"
    echo "   nano .env"
    exit 1
fi
