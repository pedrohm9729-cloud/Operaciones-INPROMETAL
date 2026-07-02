<?php
// =============================================================================
// CONFIGURACIÓN DE CODA - Carga variables de entorno
// =============================================================================

// Cargar variables desde .env si existe (usando método simple)
$env_file = dirname(__DIR__, 2) . '/.env';
if (file_exists($env_file)) {
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        // Ignorar comentarios
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        // Parsear KEY=VALUE
        if (strpos($line, '=') !== false) {
            [$key, $value] = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            // Quitar comillas si existen
            if ((strpos($value, '"') === 0 && strrpos($value, '"') === strlen($value) - 1) ||
                (strpos($value, "'") === 0 && strrpos($value, "'") === strlen($value) - 1)) {
                $value = substr($value, 1, -1);
            }
            // Establecer en $_ENV y como constante si es CODA_*
            $_ENV[$key] = $value;
            if (getenv($key) === false) {
                putenv("$key=$value");
            }
        }
    }
}

// Obtener valores de variables de entorno (con fallbacks)
$coda_api_key = getenv('CODA_API_KEY') ?: $_ENV['CODA_API_KEY'] ?? '';
$coda_doc_id = getenv('CODA_DOC_ID') ?: $_ENV['CODA_DOC_ID'] ?? 'vjnLYcbb8p';

// Validar que tenemos la API key
if (empty($coda_api_key)) {
    http_response_code(500);
    die(json_encode([
        'success' => false,
        'error' => 'CODA_API_KEY no está configurada. Verifica que .env existe y contiene CODA_API_KEY=tu_clave_aqui',
        'solution' => 'Crear .env: cp .env.template .env, luego editar y rellenar CODA_API_KEY desde https://coda.io/account/settings#apiTokens'
    ]));
}

// Definir constantes globales para que data.php las use
define('CODA_API_KEY', $coda_api_key);
define('CODA_DOC_ID', $coda_doc_id);
