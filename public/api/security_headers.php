<?php
// ==========================================================================
// Security Headers - Incluir en TODOS los endpoints PHP
// ==========================================================================

function set_security_headers() {
    // Prevenir MIME type sniffing
    header('X-Content-Type-Options: nosniff');

    // Prevenir clickjacking
    header('X-Frame-Options: DENY');

    // Prevenir XSS (legacy, obsoleto en navegadores modernos pero útil para compatibilidad)
    header('X-XSS-Protection: 1; mode=block');

    // Referrer Policy (no enviar referer a sitios externos)
    header('Referrer-Policy: strict-origin-when-cross-origin');

    // Content Security Policy (prevenir inline scripts y external scripts no autorizados)
    header("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';");

    // Strict Transport Security (si usa HTTPS en producción)
    if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
        header('Strict-Transport-Security: max-age=31536000; includeSubDomains');
    }
}

// Llamar al inicio de cada script
set_security_headers();
