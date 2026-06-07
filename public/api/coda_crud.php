// Configuración de la sesión - Segura, HttpOnly, SameSite=Lax
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Lax');
ini_set('session.use_only_cookies', 1);
if ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') || 
    (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https')) {
    ini_set('session.cookie_secure', 1);
}
session_start();
header('Content-Type: application/json');

// CORS Whitelist - Solo dominios autorizados
$allowed_origins = [
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://ops.inprometal.com',
    'https://www.ops.inprometal.com',
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

if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'No autorizado. Inicie sesión.']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Método no permitido.']);
    exit;
}

$config_file = __DIR__ . '/coda_config.php';
if (!file_exists($config_file)) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Falta el archivo de configuración coda_config.php.']);
    exit;
}
require_once $config_file;

// Mapeo de tablas de Coda
$coda_tables = [
    'OT' => 'grid-VHR5pyPjro',
    'Facturas' => 'grid-N21RY9yG8B',
    'GasCom' => 'grid-MRbFDU4dvf',
    'Personal' => 'grid-DCcym1iQsr'
];

$coda_cols = [
    'OT' => [
        'codigo' => 'c-pc5YuBXn96',
        'cliente' => 'c-NKAKLScE0S',
        'estado' => 'c-REo1Oizg0Y',
        'descripcion' => 'c-hzJTUN6TGN',
        'precio_venta' => 'c-r8UDJ5yyO2',
        'gastos' => 'c-_XJ4HM6uby',
        'utilidad' => 'c-6ywH8DA-ch',
        'fecha_inicio' => 'c-3M9ac5NCTz',
        'fecha_entrega'=> 'c-jWLKhW3vP9'
    ],
    'Facturas' => [
        'factura' => 'c-JIV9w_1NWC',
        'cliente' => 'c-q-6MtqAzZF',
        'monto' => 'c-yFLHJCQPjq',
        'moneda' => 'c-NHbA6tg43O',
        'estado' => 'c-DzL5A7cfoh',
        'atraso' => 'c-nCJ_HemjMC',
        'fecha_pago' => 'c-w_xJeGpdz5',
        'fecha_emision' => 'c-40nbQz-lkR',
        'ot' => 'c-66AcWwCRS9'
    ],
    'GasCom' => [
        'fecha' => 'c-61ofsG_OBR',
        'proveedor' => 'c-NWRsEkGrw0',
        'monto' => 'c-cYVuEll05n',
        'moneda' => 'c-vXwEqLyp9Z',
        'concepto' => 'c-481d5xGLOy',
        'categoria' => 'c-wYCNse9QsV',
        'subcategoria' => 'c-cJFDputTU7',
        'ot' => 'c-VQAnY2FKEn',
        'cantidad' => 'c-EeFbBKh7Ln'
    ],
    'Personal' => [
        'nombre' => 'c-oZyrOfYoCD',
        'dni' => 'c-L-ty03t3qT',
        'direccion' => 'c-KbIEZZ_hS8',
        'celular' => 'c-uoRQV9tLRA',
        'edad' => 'c-pDPpvo92jx',
        'bcp' => 'c-bYKecv_8AY',
        'bbva' => 'c-rgm_mztIeA'
    ]
];

$required_cols = [
    'OT' => ['codigo', 'cliente', 'estado', 'precio_venta'],
    'Facturas' => ['factura', 'cliente', 'monto', 'moneda', 'estado'],
    'GasCom' => ['fecha', 'proveedor', 'monto', 'moneda', 'categoria', 'concepto'],
    'Personal' => ['nombre', 'dni']
];

$input = file_get_contents('php://input');
$params = json_decode($input, true);

$action = isset($_GET['action']) ? $_GET['action'] : '';

function invalidar_cache() {
    $cache_file = __DIR__ . '/coda_cache.json';
    if (file_exists($cache_file)) {
        @unlink($cache_file);
    }
}

function resolver_columnas($table_name, $abstract_cells) {
    global $coda_cols;
    if (!isset($coda_cols[$table_name])) {
        return [null, "Tabla desconocida: $table_name"];
    }
    
    $cols = $coda_cols[$table_name];
    $resolved = [];
    
    foreach ($abstract_cells as $cell) {
        $key = $cell['key'] ?? '';
        $value = $cell['value'] ?? null;
        
        if (!isset($cols[$key])) {
            return [null, "Columna desconocida '$key' para tabla '$table_name'"];
        }
        
        // Validar numéricos
        if (in_array($key, ['precio_venta', 'monto', 'edad']) && $value === null) {
            return [null, "El campo '$key' no puede ser nulo."];
        }
        
        // Validar strings no vacíos
        if (is_string($value) && trim($value) === '' && in_array($key, ['codigo', 'cliente', 'factura', 'nombre', 'dni', 'proveedor', 'concepto'])) {
            return [null, "El campo '$key' no puede estar vacío."];
        }
        
        $resolved[] = [
            'column' => $cols[$key],
            'value' => $value
        ];
    }
    return [$resolved, null];
}

function execute_coda_request($url, $method, $data = null) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . CODA_API_KEY,
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 12);
    
    if ($data !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    return [$response, $http_code];
}

switch ($action) {
    case 'add':
        $table_name = $params['table'] ?? '';
        $abstract_cells = $params['cells'] ?? [];
        
        if (empty($table_name) || empty($abstract_cells)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Faltan campos obligatorios.']);
            exit;
        }
        
        if (!isset($coda_tables[$table_name])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => "Tabla desconocida: $table_name"]);
            exit;
        }
        
        // Validar obligatorios
        $provided_keys = array_column($abstract_cells, 'key');
        foreach ($required_cols[$table_name] ?? [] as $req_key) {
            if (!in_array($req_key, $provided_keys)) {
                http_response_code(400);
                echo json_encode(['success' => false, 'error' => "Campo obligatorio faltante: '$req_key'"]);
                exit;
            }
        }
        
        list($resolved_cells, $err) = resolver_columnas($table_name, $abstract_cells);
        if ($err) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => $err]);
            exit;
        }
        
        $table_id = $coda_tables[$table_name];
        $url = "https://coda.io/apis/v1/docs/" . CODA_DOC_ID . "/tables/" . $table_id . "/rows";
        $payload = ['rows' => [['cells' => $resolved_cells]]];
        
        list($resp, $code) = execute_coda_request($url, 'POST', $payload);
        if ($code >= 200 && $code < 300) {
            invalidar_cache();
            echo json_encode(['success' => true, 'result' => json_decode($resp, true)]);
        } else {
            http_response_code($code);
            echo json_encode(['success' => false, 'error' => 'Error de Coda API: ' . $resp]);
        }
        break;
        
    case 'update':
        $table_name = $params['table'] ?? '';
        $row_id = $params['row_id'] ?? '';
        $abstract_cells = $params['cells'] ?? [];
        
        if (empty($table_name) || empty($row_id) || empty($abstract_cells)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Faltan campos obligatorios.']);
            exit;
        }
        
        if (!isset($coda_tables[$table_name])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => "Tabla desconocida: $table_name"]);
            exit;
        }
        
        list($resolved_cells, $err) = resolver_columnas($table_name, $abstract_cells);
        if ($err) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => $err]);
            exit;
        }
        
        $table_id = $coda_tables[$table_name];
        $url = "https://coda.io/apis/v1/docs/" . CODA_DOC_ID . "/tables/" . $table_id . "/rows/" . $row_id;
        $payload = ['row' => ['cells' => $resolved_cells]];
        
        list($resp, $code) = execute_coda_request($url, 'PUT', $payload);
        if ($code >= 200 && $code < 300) {
            invalidar_cache();
            echo json_encode(['success' => true, 'result' => json_decode($resp, true)]);
        } else {
            http_response_code($code);
            echo json_encode(['success' => false, 'error' => 'Error de Coda API: ' . $resp]);
        }
        break;
        
    case 'delete':
        $table_name = $params['table'] ?? '';
        $row_id = $params['row_id'] ?? '';
        
        if (empty($table_name) || empty($row_id)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Faltan campos obligatorios.']);
            exit;
        }
        
        if (!isset($coda_tables[$table_name])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => "Tabla desconocida: $table_name"]);
            exit;
        }
        
        $table_id = $coda_tables[$table_name];
        $url = "https://coda.io/apis/v1/docs/" . CODA_DOC_ID . "/tables/" . $table_id . "/rows/" . $row_id;
        
        list($resp, $code) = execute_coda_request($url, 'DELETE');
        if ($code >= 200 && $code < 300) {
            invalidar_cache();
            echo json_encode(['success' => true, 'result' => json_decode($resp, true)]);
        } else {
            http_response_code($code);
            echo json_encode(['success' => false, 'error' => 'Error de Coda API: ' . $resp]);
        }
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'Acción no válida o no especificada.']);
        break;
}
