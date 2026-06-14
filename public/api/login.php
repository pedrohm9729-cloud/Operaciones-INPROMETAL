<?php
// Configuración de la sesión - Segura, HttpOnly, SameSite=Strict
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Strict');
ini_set('session.use_only_cookies', 1);

// Si no es localhost, habilitar secure cookies
if (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') {
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
    'https://operaciones.inprometal.com',
    'https://www.operaciones.inprometal.com'
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins, true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Access-Control-Allow-Credentials: true');
}
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Cookie');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Método no permitido.']);
    exit;
}

// Cargar la configuración (claves e inicio de sesión)
$config_file = __DIR__ . '/coda_config.php';
if (!file_exists($config_file)) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Falta el archivo de configuración coda_config.php.']);
    exit;
}

require_once $config_file;

// Obtener datos del JSON de entrada
$input = file_get_contents('php://input');
$data = json_decode($input, true);

$username = isset($data['username']) ? trim($data['username']) : '';
$password = isset($data['password']) ? $data['password'] : '';

if (empty($username) || empty($password)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Usuario y contraseña requeridos.']);
    exit;
}

// Validar credenciales
$expected_username = defined('DASHBOARD_USERNAME') ? DASHBOARD_USERNAME : 'admin';
$expected_hash = defined('DASHBOARD_PASSWORD_HASH') ? DASHBOARD_PASSWORD_HASH : '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'; // sha256 de admin

$input_hash = hash('sha256', $password);

if ($username === $expected_username && hash_equals($expected_hash, $input_hash)) {
    $_SESSION['authenticated'] = true;
    $_SESSION['user'] = $username;
    $_SESSION['last_activity'] = time();

    // SEGURIDAD: Generar y devolver CSRF token
    $csrf_token = bin2hex(random_bytes(32));
    $_SESSION['csrf_token'] = $csrf_token;

    echo json_encode([
        'success' => true,
        'csrf_token' => $csrf_token  // ✅ DEVOLVER CSRF TOKEN
    ]);
} else {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'Usuario o contraseña incorrectos.']);
}
