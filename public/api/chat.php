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

$input = file_get_contents('php://input');
$params = json_decode($input, true);
$query = isset($params['message']) ? trim($params['message']) : '';

if (empty($query)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'La pregunta no puede estar vacía.']);
    exit;
}

// 1. Obtener los datos operativos de Coda
$cache_file = __DIR__ . '/coda_cache.json';
$coda_data = null;

if (file_exists($cache_file)) {
    $cache_content = json_decode(file_get_contents($cache_file), true);
    if ($cache_content && isset($cache_content['data'])) {
        $coda_data = $cache_content['data'];
    }
}

if (!$coda_data) {
    // Si no hay caché, hacer el fetch directo (código análogo al de data.php)
    $coda_tables = [
        'OT' => 'grid-VHR5pyPjro',
        'Facturas' => 'grid-N21RY9yG8B',
        'GasCom' => 'grid-MRbFDU4dvf',
        'Personal' => 'grid-DCcym1iQsr'
    ];
    
    $mh = curl_multi_init();
    $curls = [];
    
    foreach ($coda_tables as $key => $table_id) {
        $url = "https://coda.io/apis/v1/docs/" . CODA_DOC_ID . "/tables/" . $table_id . "/rows?valueFormat=simple&limit=500";
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Authorization: Bearer ' . CODA_API_KEY]);
        curl_setopt($ch, CURLOPT_TIMEOUT, 12);
        curl_multi_add_handle($mh, $ch);
        $curls[$key] = $ch;
    }
    
    $running = null;
    do {
        curl_multi_exec($mh, $running);
    } while ($running > 0);
    
    $coda_data = [];
    foreach ($curls as $key => $ch) {
        $response = curl_multi_getcontent($ch);
        $info = curl_getinfo($ch);
        curl_multi_remove_handle($mh, $ch);
        curl_close($ch);
        if ($info['http_code'] == 200) {
            $json = json_decode($response, true);
            $coda_data[$key] = $json['items'] ?? [];
        } else {
            $coda_data[$key] = [];
        }
    }
    curl_multi_close($mh);
    
    // Actualizar caché
    $cache_payload = [
        'success' => true,
        'last_sync' => 'Sincronizado vía Chat',
        'data' => $coda_data
    ];
    file_put_contents($cache_file, json_encode($cache_payload));
}

// 2. Mapear datos a claves legibles
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

function map_rows($rows, $mapping) {
    $result = [];
    foreach ($rows as $row) {
        $values = $row['values'] ?? [];
        $mapped = [];
        foreach ($mapping as $key => $col_id) {
            $mapped[$key] = $values[$col_id] ?? null;
        }
        $result[] = $mapped;
    }
    return $result;
}

$ot_mapped       = map_rows($coda_data['OT'] ?? [], $coda_cols['OT']);
$facturas_mapped = map_rows($coda_data['Facturas'] ?? [], $coda_cols['Facturas']);
$gascom_mapped   = map_rows($coda_data['GasCom'] ?? [], $coda_cols['GasCom']);
$personal_mapped = map_rows($coda_data['Personal'] ?? [], $coda_cols['Personal']);

// 3. Crear el prompt con los datos en formato JSON compacto
$data_context = json_encode([
    'OrdenesDeTrabajo' => $ot_mapped,
    'Facturas'         => $facturas_mapped,
    'GastosComerciales'=> $gascom_mapped,
    'Personal'         => $personal_mapped
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

$system_prompt = "Eres \"Inprometal AI\", el asistente inteligente oficial del Centro de Operaciones (OPS) de la empresa metalmecánica INPROMETAL.\n"
               . "Tienes acceso en tiempo real a los siguientes datos operativos extraídos de la base de datos Coda:\n\n"
               . "1. Órdenes de Trabajo (OT) - Códigos, clientes, estados (PENDIENTE, COMPLETADO), precios de venta, gastos y utilidades.\n"
               . "2. Facturas - Códigos de factura, montos, moneda (USD o PEN), estados (EMITIDA, COBRADA, ANULADA), fechas de emisión y pago.\n"
               . "3. Gastos - Pagos a proveedores con montos, fechas, categorías (Fierros, Consumibles, etc.) y OTs asociadas.\n"
               . "4. Personal - Nombres, DNI, datos de contacto y cuentas bancarias (BCP, BBVA) para depósitos.\n\n"
               . "Tu objetivo es responder de forma clara, directa, precisa y profesional en español. Utiliza negritas, listas o tablas Markdown para estructurar la información si es apropiado.\n"
               . "Si el usuario te pide sumas, totales, promedios o márgenes, realiza los cálculos matemáticos basándote estrictamente en los datos provistos.\n"
               . "Si no encuentras información relevante para responder la pregunta, indícalo de forma cortés.\n\n"
               . "CONTEXTO DE DATOS DE CODA:\n"
               . "```json\n" . $data_context . "\n```";

$full_prompt = $system_prompt . "\n\nPregunta del usuario: " . $query;

// 4. Llamar al API de Gemini
$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . GEMINI_API_KEY;

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'contents' => [
        ['parts' => [['text' => $full_prompt]]]
    ],
    'generationConfig' => [
        'temperature' => 0.2,
        'maxOutputTokens' => 2048
    ]
]));

$resp = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code == 200) {
    $json = json_decode($resp, true);
    $text_response = $json['candidates'][0]['content']['parts'][0]['text'] ?? 'No se pudo generar una respuesta.';
    echo json_encode(['success' => true, 'response' => $text_response]);
} else {
    http_response_code($http_code);
    echo json_encode(['success' => false, 'error' => 'Error al comunicarse con la IA de Gemini: ' . $resp]);
}
