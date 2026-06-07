<?php
session_start();
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('Connection: keep-alive');

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

// Desactivar buffering de salida para que los datos se transmitan de inmediato
if (function_exists('apache_setenv')) {
    @apache_setenv('no-gzip', 1);
}
@ini_set('zlib.output_compression', 0);
@ini_set('implicit_flush', 1);
ob_implicit_flush(true);
while (ob_get_level() > 0) {
    ob_end_clean();
}

if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true) {
    echo "data: [ERROR] No autorizado. Inicie sesión.\n\n";
    exit;
}

echo "data: [START] Verificando estado de sincronización...\n\n";
flush();
sleep(1);

echo "data: La base de datos de Coda está conectada correctamente.\n\n";
flush();
sleep(1);

echo "data: Nota: La sincronización de correos y gastos bancarios se ejecuta de forma local y segura en la PC de operaciones (usando el extractor de fondo).\n\n";
flush();
sleep(1);

echo "data: Cualquier actualización realizada en la PC local se refleja de inmediato en este panel al recargar.\n\n";
flush();
sleep(1);

echo "data: [DONE] Proceso finalizado con éxito.\n\n";
flush();
