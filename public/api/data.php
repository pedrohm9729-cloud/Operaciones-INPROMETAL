<?php
// Configuración de la sesión - Segura, HttpOnly, SameSite=Lax
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Lax');
ini_set('session.use_only_cookies', 1);
if ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') || 
    (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https')) {
    ini_set('session.cookie_secure', 1);
}
session_start();

// Agregar security headers
require_once 'security_headers.php';

header('Content-Type: application/json');

// CORS Whitelist - Solo dominios autorizados
$allowed_origins = [
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://ops.inprometal.com',
    'https://www.ops.inprometal.com'
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins, true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Access-Control-Allow-Credentials: true');
}

if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'No autorizado. Inicie sesión.']);
    exit;
}

$config_file = __DIR__ . '/coda_config.php';
if (!file_exists($config_file)) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Falta el archivo de configuración coda_config.php.']);
    exit;
}
require_once $config_file;

$cache_file = __DIR__ . '/coda_cache.json';
$cache_ttl = 20; // 20 segundos

if (file_exists($cache_file) && (time() - filemtime($cache_file) < $cache_ttl)) {
    $cache_data = json_decode(file_get_contents($cache_file), true);
    if ($cache_data) {
        echo json_encode($cache_data);
        exit;
    }
}

// Mapeo de tablas de Coda
$coda_tables = [
    'OT' => 'grid-VHR5pyPjro',
    'Facturas' => 'grid-N21RY9yG8B',
    'GasCom' => 'grid-MRbFDU4dvf',
    'Personal' => 'grid-DCcym1iQsr',
    'Deudas' => 'grid-tfHsKPLQsr'
];

// Consulta en paralelo usando curl_multi
$mh = curl_multi_init();
$curls = [];

foreach ($coda_tables as $key => $table_id) {
    $url = "https://coda.io/apis/v1/docs/" . CODA_DOC_ID . "/tables/" . $table_id . "/rows?valueFormat=simple&limit=500";
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . CODA_API_KEY
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 12);
    curl_multi_add_handle($mh, $ch);
    $curls[$key] = $ch;
}

$running = null;
do {
    curl_multi_exec($mh, $running);
} while ($running > 0);

$data = [];
$errors = [];

foreach ($curls as $key => $ch) {
    $response = curl_multi_getcontent($ch);
    $info = curl_getinfo($ch);
    curl_multi_remove_handle($mh, $ch);
    curl_close($ch);
    
    if ($info['http_code'] == 200) {
        $json = json_decode($response, true);
        $data[$key] = $json['items'] ?? [];
    } else {
        $errors[$key] = "Error HTTP " . $info['http_code'];
        $data[$key] = [];
    }
}
curl_multi_close($mh);

$last_sync = '';
$ultima_txt = dirname(__DIR__, 2) . '/ultima_ejecucion.txt';
if (file_exists($ultima_txt)) {
    $last_sync = trim(file_get_contents($ultima_txt));
} else {
    $ultima_txt_alt = __DIR__ . '/ultima_ejecucion.txt';
    if (file_exists($ultima_txt_alt)) {
        $last_sync = trim(file_get_contents($ultima_txt_alt));
    } else {
        $last_sync = 'Sincronizado vía PC';
    }
}

$response_payload = [
    'success' => true,
    'last_sync' => $last_sync,
    'data' => $data,
    'errors' => $errors
];

// Guardar en caché de forma atómica para evitar colisiones
file_put_contents_safe($cache_file, json_encode($response_payload));

echo json_encode($response_payload);

function file_put_contents_safe($filepath, $content) {
    $temp = tempnam(dirname($filepath), 'temp');
    if ($temp !== false && file_put_contents($temp, $content) !== false) {
        if (rename($temp, $filepath)) {
            chmod($filepath, 0644);
            return true;
        }
        unlink($temp);
    }
    return file_put_contents($filepath, $content) !== false;
}
