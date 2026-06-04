import os
import sys
import json
import time
import secrets
import hashlib
import threading
import subprocess
import http.server
import http.cookies
import socketserver
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Asegurar que el directorio de este script está en el path
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
if DIRECTORIO_ACTUAL not in sys.path:
    sys.path.append(DIRECTORIO_ACTUAL)

# Cargar API Keys desde variables de entorno (OBLIGATORIO)
CODA_API_KEY = os.environ.get('CODA_API_KEY', '').strip()
if not CODA_API_KEY:
    raise ValueError("CODA_API_KEY no configurada. Define en .env o variables de entorno.")

# Cargar Coda Doc ID desde variables de entorno
CODA_DOC_ID = os.environ.get('CODA_DOC_ID', '').strip()
if not CODA_DOC_ID:
    raise ValueError("CODA_DOC_ID no configurada en variables de entorno o .env")

# Intentar importar la función de autenticación básica de Gmail
try:
    from gastos_bancarios import autenticar
except ImportError:
    autenticar = None

PORT = int(os.environ.get('PORT', 5000))
PUBLIC_DIR = os.path.join(DIRECTORIO_ACTUAL, 'public')

# Archivo de Autenticación
AUTH_FILE = os.path.join(DIRECTORIO_ACTUAL, 'dashboard_auth.json')
SESIONES_ACTIVAS = {}  # Cambiar a dict para almacenar metadatos

# Rate Limiting para Login (máx 5 intentos por IP en 15 minutos)
RATE_LIMIT_LOGIN = {}
RATE_LIMIT_WINDOW = 900  # 15 minutos
MAX_LOGIN_ATTEMPTS = 5

# CSRF Tokens (asociados con sesiones)
CSRF_TOKENS = {}

# ==========================================================================
#  MAPEO DE TABLAS Y COLUMNAS (BACKEND-ONLY — nunca se exponen al cliente)
# ==========================================================================
CODA_TABLES = {
    'OT':       'grid-VHR5pyPjro',
    'Facturas': 'grid-N21RY9yG8B',
    'GasCom':   'grid-MRbFDU4dvf',
    'Personal': 'grid-DCcym1iQsr'
}

CODA_COLS = {
    'OT': {
        'codigo':       'c-pc5YuBXn96',
        'cliente':      'c-NKAKLScE0S',
        'estado':       'c-REo1Oizg0Y',
        'descripcion':  'c-hzJTUN6TGN',
        'precio_venta': 'c-r8UDJ5yyO2',
        'gastos':       'c-_XJ4HM6uby',
        'utilidad':     'c-6ywH8DA-ch',
        'fecha_inicio': 'c-3M9ac5NCTz',
        'fecha_entrega':'c-jWLKhW3vP9'
    },
    'Facturas': {
        'factura':       'c-JIV9w_1NWC',
        'cliente':       'c-q-6MtqAzZF',
        'monto':         'c-yFLHJCQPjq',
        'moneda':        'c-NHbA6tg43O',
        'estado':        'c-DzL5A7cfoh',
        'atraso':        'c-nCJ_HemjMC',
        'fecha_pago':    'c-w_xJeGpdz5',
        'fecha_emision': 'c-40nbQz-lkR',
        'ot':            'c-66AcWwCRS9'
    },
    'GasCom': {
        'fecha':        'c-61ofsG_OBR',
        'proveedor':    'c-NWRsEkGrw0',
        'monto':        'c-cYVuEll05n',
        'moneda':       'c-vXwEqLyp9Z',
        'concepto':     'c-481d5xGLOy',
        'categoria':    'c-wYCNse9QsV',
        'subcategoria': 'c-cJFDputTU7',
        'ot':           'c-VQAnY2FKEn',
        'cantidad':     'c-EeFbBKh7Ln'
    },
    'Personal': {
        'nombre':    'c-oZyrOfYoCD',
        'dni':       'c-L-ty03t3qT',
        'direccion': 'c-KbIEZZ_hS8',
        'celular':   'c-uoRQV9tLRA',
        'edad':      'c-pDPpvo92jx',
        'bcp':       'c-bYKecv_8AY',
        'bbva':      'c-rgm_mztIeA'
    }
}

# Columnas que son obligatorias para creación de registros (validación backend)
REQUIRED_COLS = {
    'OT':       ['codigo', 'cliente', 'estado', 'precio_venta'],
    'Facturas': ['factura', 'cliente', 'monto', 'moneda', 'estado'],
    'GasCom':   ['fecha', 'proveedor', 'monto', 'moneda', 'categoria', 'concepto'],
    'Personal': ['nombre', 'dni']
}

# ==========================================================================
#  CACHÉ EN MEMORIA + BLOQUEO DE SINCRONIZACIÓN
# ==========================================================================
CACHE_DATA = None
CACHE_TIMESTAMP = 0
CACHE_TTL = 20  # segundos

SYNC_LOCK = threading.Lock()
IS_SYNCING = False

def invalidar_cache():
    global CACHE_DATA, CACHE_TIMESTAMP
    CACHE_DATA = None
    CACHE_TIMESTAMP = 0

# ==========================================================================
#  RATE LIMITING HELPER
# ==========================================================================
def verificar_rate_limit(ip_addr, max_attempts=MAX_LOGIN_ATTEMPTS, window=RATE_LIMIT_WINDOW):
    """Retorna (permitido: bool, mensaje: str)"""
    ahora = time.time()
    if ip_addr not in RATE_LIMIT_LOGIN:
        RATE_LIMIT_LOGIN[ip_addr] = []

    # Limpiar intentos viejos
    RATE_LIMIT_LOGIN[ip_addr] = [t for t in RATE_LIMIT_LOGIN[ip_addr] if ahora - t < window]

    if len(RATE_LIMIT_LOGIN[ip_addr]) >= max_attempts:
        return False, f"Demasiados intentos. Intenta en {window//60} minutos."

    RATE_LIMIT_LOGIN[ip_addr].append(ahora)
    return True, ""

# ==========================================================================
#  CSRF TOKEN HELPERS
# ==========================================================================
def generar_csrf_token():
    """Genera un token CSRF único"""
    return secrets.token_urlsafe(32)

def validar_csrf_token(session_id, csrf_token):
    """Valida si el token CSRF es válido para la sesión"""
    return CSRF_TOKENS.get(session_id) == csrf_token

# ==========================================================================
#  HELPERS DE AUTENTICACIÓN (PBKDF2 con sal por usuario)
# ==========================================================================
def hash_password_pbkdf2(password, salt=None):
    """Retorna (salt_hex, hash_hex). Si salt=None genera uno nuevo."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 260000)
    return salt, dk.hex()

def inicializar_autenticacion():
    """Genera credenciales seguras por defecto si no existen."""
    if not os.path.exists(AUTH_FILE):
        password_tmp = secrets.token_urlsafe(12)
        salt, pwd_hash = hash_password_pbkdf2(password_tmp)
        config = {
            'username': 'admin',
            'salt': salt,
            'password_hash': pwd_hash,
            'scheme': 'pbkdf2_sha256'
        }
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        # Escribir contraseña temporal en archivo de texto plano (primer inicio)
        primer_inicio_path = os.path.join(DIRECTORIO_ACTUAL, 'primer_inicio.txt')
        with open(primer_inicio_path, 'w', encoding='utf-8') as f:
            f.write(f"INPROMETAL Dashboard - Primer Inicio\n")
            f.write(f"Usuario: admin\n")
            f.write(f"Contraseña temporal: {password_tmp}\n")
            f.write(f"Cambia esta contraseña después de iniciar sesión.\n")
        print(f"\n[!] PRIMER INICIO — Credenciales en: primer_inicio.txt\n")
    else:
        print("Archivo de credenciales 'dashboard_auth.json' cargado.")

def validar_credenciales(username, password):
    if not os.path.exists(AUTH_FILE):
        return False
    try:
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if config.get('username') != username:
            return False
        scheme = config.get('scheme', 'sha256')
        if scheme == 'pbkdf2_sha256':
            salt = config.get('salt', '')
            _, computed = hash_password_pbkdf2(password, salt)
            return secrets.compare_digest(computed, config.get('password_hash', ''))
        else:
            # Compatibilidad legado (sha256 sin sal)
            legacy_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return secrets.compare_digest(legacy_hash, config.get('password_hash', ''))
    except Exception as e:
        print(f"Error al leer credenciales: {e}")
        return False

# ==========================================================================
#  HELPERS DE CODA API
# ==========================================================================
def cargar_tabla_coda(table_id):
    """Obtiene todas las filas de una tabla de Coda en formato simple."""
    if not CODA_API_KEY:
        print("  [!] Error: CODA_API_KEY no configurada.")
        return []
    url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{table_id}/rows?valueFormat=simple&limit=500'
    req = urllib.request.Request(
        url,
        headers={'Authorization': 'Bearer ' + CODA_API_KEY}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('items', [])
    except Exception as e:
        print(f"  [!] Error al conectar con tabla {table_id} de Coda: {e}")
        return []

def resolver_columnas(table_name, abstract_cells):
    """
    Convierte celdas con claves abstractas (p.ej. 'codigo') a IDs reales de Coda.
    Valida tipos básicos: evita enviar NaN/None en campos numéricos.
    Retorna (cells_resueltas, error_str|None)
    """
    cols = CODA_COLS.get(table_name)
    if not cols:
        return None, f"Tabla desconocida: {table_name}"
    
    resolved = []
    for cell in abstract_cells:
        key = cell.get('key')
        value = cell.get('value')
        if key not in cols:
            return None, f"Columna desconocida '{key}' para tabla '{table_name}'"
        # Validar que los números no sean NaN/None
        if isinstance(value, float) and (value != value):  # NaN check
            return None, f"Valor inválido (NaN) para columna '{key}'"
        if value is None and key in ['precio_venta', 'monto', 'edad']:
            return None, f"El campo '{key}' no puede ser nulo."
        # Validar strings no vacíos para claves obligatorias
        if isinstance(value, str) and value.strip() == '' and key in ['codigo', 'cliente', 'factura', 'nombre', 'dni', 'proveedor', 'concepto']:
            return None, f"El campo '{key}' no puede estar vacío."
        resolved.append({'column': cols[key], 'value': value})
    
    return resolved, None

# ==========================================================================
#  HTTP REQUEST HANDLER PROTEGIDO (CODA INTERACTIVE GATEWAY)
# ==========================================================================
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def obtener_session_id(self):
        cookie_header = self.headers.get('Cookie', '')
        if not cookie_header:
            return None
        cookie = http.cookies.SimpleCookie(cookie_header)
        if 'session_id' in cookie:
            return cookie['session_id'].value
        return None

    def es_sesion_valida(self):
        token = self.obtener_session_id()
        if token not in SESIONES_ACTIVAS:
            return False

        # Validar timeout (30 minutos)
        session_data = SESIONES_ACTIVAS[token]
        if time.time() - session_data.get('created_at', 0) > 1800:  # 30 min
            del SESIONES_ACTIVAS[token]
            return False

        # Actualizar último acceso
        SESIONES_ACTIVAS[token]['last_activity'] = time.time()
        return True

    def validar_csrf(self):
        """Validación de CSRF tolerante a subdominios del mismo dominio o localhost."""
        host = self.headers.get('Host', '').split(':')[0]
        origin = self.headers.get('Origin', '')
        referer = self.headers.get('Referer', '')
        
        def obtener_dominio_principal(url_o_host):
            if not url_o_host:
                return ''
            clean = url_o_host.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
            parts = clean.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return clean

        host_domain = obtener_dominio_principal(host)
        
        if origin:
            origin_domain = obtener_dominio_principal(origin)
            return host_domain == origin_domain or 'localhost' in origin or '127.0.0.1' in origin or origin_domain == ''
            
        if referer:
            referer_domain = obtener_dominio_principal(referer)
            return host_domain == referer_domain or 'localhost' in referer or '127.0.0.1' in referer or referer_domain == ''
            
        return 'localhost' in host or '127.0.0.1' in host

    def redirigir_a_login(self):
        self.send_response(302)
        self.send_header('Location', '/login.html')
        self.end_headers()

    def enviar_cabeceras_cors(self):
        origin = self.headers.get('Origin')
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')

    def do_OPTIONS(self):
        self.send_response(200)
        self.enviar_cabeceras_cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def enviar_no_autorizado(self):
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.enviar_cabeceras_cors()
        self.end_headers()
        self.wfile.write(json.dumps({
            'success': False,
            'error': 'No autorizado. Inicie sesión.'
        }).encode('utf-8'))

    def enviar_json(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.enviar_cabeceras_cors()
        self.end_headers()
        self.wfile.write(body)

    def leer_body_json(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(content_length).decode('utf-8')
        return json.loads(raw)

    def do_GET(self):
        rutas_publicas = [
            '/login.html', '/login.js', '/style.css',
            '/favicon.ico', '/api/status'
        ]
        if self.path in rutas_publicas or self.path.startswith('/login.html'):
            super().do_GET()
            return

        if not self.es_sesion_valida():
            if self.path.startswith('/api/'):
                self.enviar_no_autorizado()
            else:
                self.redirigir_a_login()
            return

        if self.path == '/api/data':
            self.handle_api_data()
        elif self.path == '/api/sync':
            self.handle_api_sync()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/login':
            self.handle_api_login()
            return

        if not self.es_sesion_valida():
            self.enviar_no_autorizado()
            return

        # Verificación CSRF para todas las rutas protegidas
        session_id = self.obtener_session_id()
        csrf_token = self.headers.get('X-CSRF-Token', '')

        if not csrf_token or not validar_csrf_token(session_id, csrf_token):
            self.enviar_json(403, {'success': False, 'error': 'Token CSRF inválido.'})
            return

        if self.path == '/api/logout':
            self.handle_api_logout()
        elif self.path == '/api/coda/add':
            self.handle_api_coda_add()
        elif self.path == '/api/coda/update':
            self.handle_api_coda_update()
        elif self.path == '/api/coda/delete':
            self.handle_api_coda_delete()
        else:
            self.send_error(404, "Endpoint no encontrado")

    # ==========================================================================
    #  API HANDLERS
    # ==========================================================================
    def handle_api_login(self):
        try:
            # Rate limiting por IP
            client_ip = self.client_address[0]
            permitido, msg_rate = verificar_rate_limit(client_ip)
            if not permitido:
                self.enviar_json(429, {'success': False, 'error': msg_rate})
                print(f"[!] Rate limit excedido para IP: {client_ip}")
                return

            params = self.leer_body_json()
            username = params.get('username', '').strip()
            password = params.get('password', '')

            if validar_credenciales(username, password):
                token = secrets.token_hex(32)
                csrf_token = generar_csrf_token()

                # Guardar sesión con metadatos
                SESIONES_ACTIVAS[token] = {
                    'username': username,
                    'created_at': time.time(),
                    'last_activity': time.time(),
                    'ip': client_ip
                }
                CSRF_TOKENS[token] = csrf_token

                is_local = 'localhost' in self.headers.get('Host', '') or '127.0.0.1' in self.headers.get('Host', '')
                cookie = http.cookies.SimpleCookie()
                cookie['session_id'] = token
                cookie['session_id']['path'] = '/'
                cookie['session_id']['httponly'] = True
                cookie['session_id']['samesite'] = 'Strict'
                cookie['session_id']['max-age'] = 86400
                if not is_local:
                    cookie['session_id']['secure'] = True

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.enviar_cabeceras_cors()
                self.send_header('Set-Cookie', cookie.output(header='').strip())
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'csrf_token': csrf_token}).encode('utf-8'))
                print(f"[✓] Inicio de sesión exitoso para usuario: {username} desde IP: {client_ip}")
            else:
                self.enviar_json(401, {'success': False, 'error': 'Usuario o contraseña incorrectos.'})
        except Exception as e:
            self.enviar_json(500, {'success': False, 'error': str(e)})

    def handle_api_logout(self):
        token = self.obtener_session_id()
        if token in SESIONES_ACTIVAS:
            username = SESIONES_ACTIVAS[token].get('username', 'unknown')
            del SESIONES_ACTIVAS[token]
        if token in CSRF_TOKENS:
            del CSRF_TOKENS[token]

        cookie = http.cookies.SimpleCookie()
        cookie['session_id'] = ''
        cookie['session_id']['path'] = '/'
        cookie['session_id']['httponly'] = True
        cookie['session_id']['samesite'] = 'Strict'
        cookie['session_id']['max-age'] = 0

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.enviar_cabeceras_cors()
        self.send_header('Set-Cookie', cookie.output(header='').strip())
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    def handle_api_data(self):
        """Descarga todas las tablas de Coda con caché en memoria y carga paralela."""
        global CACHE_DATA, CACHE_TIMESTAMP
        try:
            ahora = time.time()
            if CACHE_DATA and (ahora - CACHE_TIMESTAMP < CACHE_TTL):
                print("Sirviendo datos desde caché del servidor.")
                self.enviar_json(200, CACHE_DATA)
                return

            print("Cargando datos en paralelo desde Coda...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                fut_ots     = executor.submit(cargar_tabla_coda, CODA_TABLES['OT'])
                fut_fac     = executor.submit(cargar_tabla_coda, CODA_TABLES['Facturas'])
                fut_gas     = executor.submit(cargar_tabla_coda, CODA_TABLES['GasCom'])
                fut_per     = executor.submit(cargar_tabla_coda, CODA_TABLES['Personal'])
                ots         = fut_ots.result()
                facturas    = fut_fac.result()
                gascom      = fut_gas.result()
                personal    = fut_per.result()

            last_sync = ""
            ultima_txt = os.path.join(DIRECTORIO_ACTUAL, 'ultima_ejecucion.txt')
            if os.path.exists(ultima_txt):
                with open(ultima_txt, 'r', encoding='utf-8') as f:
                    last_sync = f.read().strip()

            CACHE_DATA = {
                'success': True,
                'last_sync': last_sync,
                'data': {
                    'OT':       ots,
                    'Facturas': facturas,
                    'GasCom':   gascom,
                    'Personal': personal
                }
            }
            CACHE_TIMESTAMP = ahora

            self.enviar_json(200, CACHE_DATA)
            print("Datos de Coda cargados y servidos.")

        except Exception as e:
            print(f"Error en /api/data: {e}")
            self.enviar_json(500, {'success': False, 'error': str(e)})

    # ==========================================================================
    #  CODA CRUD ENDPOINTS — Reciben claves abstractas, resuelven IDs en backend
    # ==========================================================================
    def handle_api_coda_add(self):
        """
        Body esperado: { "table": "OT", "cells": [{"key": "codigo", "value": "OT-26-0001"}, ...] }
        """
        try:
            params = self.leer_body_json()
            table_name = params.get('table')
            abstract_cells = params.get('cells', [])

            if not table_name or not abstract_cells:
                self.enviar_json(400, {'success': False, 'error': 'Faltan campos obligatorios.'})
                return

            table_id = CODA_TABLES.get(table_name)
            if not table_id:
                self.enviar_json(400, {'success': False, 'error': f'Tabla desconocida: {table_name}'})
                return

            # Validar campos obligatorios
            provided_keys = {c.get('key') for c in abstract_cells}
            for req_key in REQUIRED_COLS.get(table_name, []):
                if req_key not in provided_keys:
                    self.enviar_json(400, {'success': False, 'error': f"Campo obligatorio faltante: '{req_key}'"})
                    return

            resolved_cells, err = resolver_columnas(table_name, abstract_cells)
            if err:
                self.enviar_json(400, {'success': False, 'error': err})
                return

            body_coda = json.dumps({'rows': [{'cells': resolved_cells}]}).encode('utf-8')
            url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{table_id}/rows'
            req = urllib.request.Request(
                url, data=body_coda,
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + CODA_API_KEY},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                invalidar_cache()
                self.enviar_json(200, {'success': True, 'result': resp_data})
                print(f"Registro agregado en Coda tabla: {table_name}")

        except Exception as e:
            print(f"Error al agregar en Coda: {e}")
            self.enviar_json(500, {'success': False, 'error': str(e)})

    def handle_api_coda_update(self):
        """
        Body esperado: { "table": "OT", "row_id": "i-xxx", "cells": [{"key": "estado", "value": "COMPLETADO"}] }
        """
        try:
            params = self.leer_body_json()
            table_name = params.get('table')
            row_id     = params.get('row_id')
            abstract_cells = params.get('cells', [])

            if not table_name or not row_id or not abstract_cells:
                self.enviar_json(400, {'success': False, 'error': 'Faltan campos obligatorios.'})
                return

            table_id = CODA_TABLES.get(table_name)
            if not table_id:
                self.enviar_json(400, {'success': False, 'error': f'Tabla desconocida: {table_name}'})
                return

            resolved_cells, err = resolver_columnas(table_name, abstract_cells)
            if err:
                self.enviar_json(400, {'success': False, 'error': err})
                return

            body_coda = json.dumps({'row': {'cells': resolved_cells}}).encode('utf-8')
            url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{table_id}/rows/{row_id}'
            req = urllib.request.Request(
                url, data=body_coda,
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + CODA_API_KEY},
                method='PUT'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                invalidar_cache()
                self.enviar_json(200, {'success': True, 'result': resp_data})
                print(f"Registro actualizado en Coda: {row_id} tabla {table_name}")

        except Exception as e:
            print(f"Error al actualizar en Coda: {e}")
            self.enviar_json(500, {'success': False, 'error': str(e)})

    def handle_api_coda_delete(self):
        """
        Body esperado: { "table": "OT", "row_id": "i-xxx" }
        """
        try:
            params = self.leer_body_json()
            table_name = params.get('table')
            row_id     = params.get('row_id')

            if not table_name or not row_id:
                self.enviar_json(400, {'success': False, 'error': 'Faltan campos obligatorios.'})
                return

            table_id = CODA_TABLES.get(table_name)
            if not table_id:
                self.enviar_json(400, {'success': False, 'error': f'Tabla desconocida: {table_name}'})
                return

            url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{table_id}/rows/{row_id}'
            req = urllib.request.Request(
                url,
                headers={'Authorization': 'Bearer ' + CODA_API_KEY},
                method='DELETE'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                invalidar_cache()
                self.enviar_json(200, {'success': True, 'result': resp_data})
                print(f"Registro eliminado de Coda: {row_id} tabla {table_name}")

        except Exception as e:
            print(f"Error al eliminar en Coda: {e}")
            self.enviar_json(500, {'success': False, 'error': str(e)})

    def handle_api_sync(self):
        """Sincronización de Gmail con bloqueo para evitar ejecuciones concurrentes."""
        global IS_SYNCING

        with SYNC_LOCK:
            if IS_SYNCING:
                self.send_response(429)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write('Error: Ya hay una sincronización en curso. Por favor espere.'.encode('utf-8'))
                return
            IS_SYNCING = True

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        print("Iniciando sincronización de correos desde la web...")

        # Detectar Python dinámicamente (NO hardcoded paths)
        import shutil
        python_exe = shutil.which('python') or shutil.which('python3') or sys.executable

        script_path = os.path.join(DIRECTORIO_ACTUAL, 'gastos_bancarios.py')
        if not os.path.isfile(script_path):
            self.wfile.write(f"data: [ERROR] Script no encontrado: {script_path}\n\n".encode('utf-8'))
            self.wfile.flush()
            with SYNC_LOCK:
                IS_SYNCING = False
            return

        cmd = [python_exe, script_path, '--non-interactive']

        try:
            env = os.environ.copy()

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=DIRECTORIO_ACTUAL,
                env=env
            )

            self.wfile.write("data: [START] Iniciando extractor de gastos en segundo plano...\n\n".encode('utf-8'))
            self.wfile.flush()

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                line_clean = line.strip('\r\n')
                self.wfile.write(f"data: {line_clean}\n\n".encode('utf-8'))
                self.wfile.flush()

            process.wait()
            code = process.returncode
            self.wfile.write(f"data: [DONE] Proceso finalizado con código: {code}\n\n".encode('utf-8'))
            self.wfile.flush()
            invalidar_cache()
            print(f"Sincronización terminada con código {code}.")

        except Exception as e:
            error_msg = f"Error al ejecutar script de sincronización: {str(e)}"
            print(error_msg)
            self.wfile.write(f"data: [ERROR] {error_msg}\n\n".encode('utf-8'))
            self.wfile.flush()
        finally:
            with SYNC_LOCK:
                IS_SYNCING = False

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run():
    inicializar_autenticacion()
    if not os.path.exists(PUBLIC_DIR):
        os.makedirs(PUBLIC_DIR)
        print(f"Directorio creado: {PUBLIC_DIR}")

    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, DashboardHandler)
    print(f"\n=======================================================")
    print(f" Pasarela Coda CRUD iniciada exitosamente")
    print(f" Dirección local: http://localhost:{PORT}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    run()
