import os
import base64
import re
import quopri
import json
import time
import sys
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ================================================================
#  CONFIGURACION
# ================================================================
SCOPES           = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Carpeta de trabajo - Usar directorio actual, no hardcoded Windows path
CARPETA = os.path.dirname(os.path.abspath(__file__))

CREDENCIALES     = os.path.join(CARPETA, 'credentials.json')
TOKEN            = os.path.join(CARPETA, 'token.json')
ULTIMA_EJECUCION = os.path.join(CARPETA, 'ultima_ejecucion.txt')
MAX_CORREOS      = 150   # max por ejecucion para respetar quota Gemini

# GEMINI_API_KEY desde variables de entorno (NO archivo)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no configurada. Define en .env o variables de entorno.")

GEMINI_URL = ('https://generativelanguage.googleapis.com/v1beta/models/'
              'gemini-2.5-flash:generateContent?key=' + GEMINI_API_KEY)

# CODA_API_KEY desde variables de entorno (NO archivo)
CODA_API_KEY = os.environ.get('CODA_API_KEY', '').strip()
if not CODA_API_KEY:
    raise ValueError("CODA_API_KEY no configurada. Define en .env o variables de entorno.")

CODA_DOC_ID = os.environ.get('CODA_DOC_ID', 'vjnLYcbb8p').strip()
CODA_TABLE_ID = 'grid-MRbFDU4dvf'
SPREADSHEET_ID = '1DMQxVc5l7l3kjVRRLmeRhhkvbHyTLPQAkii1Kf_Avpc'

# Columnas Coda
CODA_COLS = {
    'fecha':        'c-61ofsG_OBR',
    'concepto':     'c-481d5xGLOy',
    'moneda':       'c-vXwEqLyp9Z',
    'destinatario': 'c-NWRsEkGrw0',
    'tipo':         'c-a5uK5BPAlq',
    'cuenta':       'c-Mc636KqnOm',
    'cantidad':     'c-EeFbBKh7Ln',
    'monto':        'c-cYVuEll05n',
    'categoria':    'c-wYCNse9QsV',
    'subcategoria': 'c-cJFDputTU7',
}
CODA_LINK_COL = None

# ================================================================
#  EMPRESAS Y TITULARES
# ================================================================
EMPRESAS = {
    'HV_DESARROLLO': {
        'nombre_comercial': 'INPROMETAL',
        'razon_social': 'H & V Desarrollo Y Fabricacion De Proyectos Metalmecanicos S.A.C.',
        'tipo': 'TALLER_METALMECANICO',
        'color_excel': '1F4E79',
        'alias': ['h & v', 'h&v', 'h &amp; v', 'inprometal',
                  'desarrollo y fabricacion', 'metalmecanicos', 'fabricacion de proyectos'],
    },
    'ALMA_CULINARIA': {
        'nombre_comercial': 'MUHU CAFETERIA',
        'razon_social': 'Alma Culinaria S.A.C.',
        'tipo': 'CAFETERIA',
        'color_excel': '375623',
        'alias': ['alma culinaria', 'alma culina', 'muhu cafeteria', 'muhu'],
    },
    'PEDRO_HENRIQUEZ': {
        'nombre_comercial': 'Pedro Henriquez',
        'razon_social': 'Pedro Antonio Henriquez Sebastiano',
        'tipo': 'PERSONA_NATURAL',
        'color_excel': '7B3F00',
        'alias': ['pedro antonio', 'pedro henriquez', 'sebastiano henriquez'],
    },
    'SANDRA_MAGALLANES': {
        'nombre_comercial': 'Sandra Magallanes',
        'razon_social': 'Sandra Magallanes',
        'tipo': 'PERSONA_NATURAL',
        'color_excel': '4B0082',
        'alias': ['sandra magallanes', 'sandra thamara', 'magallanes champi', 'magallanes ascencios'],
    },
}

HOJAS_CONFIG = {k: v['color_excel'] for k, v in EMPRESAS.items()}
HOJAS_CONFIG['NO IDENTIFICADO'] = '5A5A5A'

ENCABEZADOS = [
    'Fecha', 'Banco', 'Canal', 'Monto', 'Moneda',
    'Titular', 'Destinatario', 'Concepto', 'Referencia',
    'Categoria', 'Subcategoria', 'Confianza', 'Estado',
    'ID_Mensaje', 'Motivo de Omisión', 'OT', 'Enlace Correo',
]

# Categorias por empresa
CATEGORIAS_POR_EMPRESA = {
    'HV_DESARROLLO': {
        'Materiales e Insumos': ['Materiales Metalicos', 'Consumibles de Proceso',
                                 'Pinturas y Acabados', 'Perneria y Fijaciones', 'Ferreteria General'],
        'Equipos y Herramientas': ['Herramientas Manuales', 'Equipos y Maquinaria',
                                   'Repuestos y Mantenimiento', 'Calibracion y Certificacion', 'Capacitacion'],
        'Seguridad':      ['EPPS', 'Uniformes'],
        'Personal':       ['Planilla', 'Adelantos y Prestamos'],
        'Operaciones':    ['Servicios de Fabricacion Externa', 'Logistica y Transporte',
                           'Alquiler de Equipos', 'Combustible'],
        'Administracion': ['Servicios Basicos', 'Honorarios Profesionales', 'Alquiler Local',
                           'Marketing y Ventas', 'Utiles de Oficina', 'Comisiones',
                           'Pago de Compra de Facturas'],
        'Financiero':     ['Comisiones Bancarias', 'Intereses y Cargos', 'Transferencia Interna', 'Impuestos'],
        'Otro':           ['Otro'],
    },
    'ALMA_CULINARIA': {
        'Materiales e Insumos': ['Alimentos y Bebidas', 'Consumibles de Cafe',
                                 'Empaques y Presentacion', 'Ferreteria General'],
        'Equipos y Herramientas': ['Equipos de Cocina', 'Repuestos y Mantenimiento',
                                   'Calibracion y Certificacion', 'Capacitacion'],
        'Seguridad':      ['EPPS', 'Uniformes'],
        'Personal':       ['Planilla', 'Adelantos y Prestamos'],
        'Operaciones':    ['Logistica y Transporte', 'Combustible', 'Servicios de Terceros'],
        'Administracion': ['Servicios Basicos', 'Honorarios Profesionales', 'Alquiler Local',
                           'Marketing y Ventas', 'Utiles de Oficina', 'Comisiones',
                           'Pago de Compra de Facturas'],
        'Financiero':     ['Comisiones Bancarias', 'Intereses y Cargos', 'Transferencia Interna', 'Impuestos'],
        'Otro':           ['Otro'],
    },
}
# Personas naturales usan las mismas cats que HV_DESARROLLO
CATEGORIAS_POR_EMPRESA['PEDRO_HENRIQUEZ']   = CATEGORIAS_POR_EMPRESA['HV_DESARROLLO']
CATEGORIAS_POR_EMPRESA['SANDRA_MAGALLANES'] = CATEGORIAS_POR_EMPRESA['HV_DESARROLLO']
# Alias global para compatibilidad
CATEGORIAS = CATEGORIAS_POR_EMPRESA['HV_DESARROLLO']

# ================================================================
#  HELPERS
# ================================================================
def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def formatear_ot_para_excel(ot_coda):
    if not ot_coda:
        return ""
    # Si tiene formato OT-YY-NNNN, ej: OT-26-0025 -> 2026-OT-25
    m = re.match(r'^OT-(\d{2})-(\d+)$', ot_coda)
    if m:
        yy, nnnn = m.groups()
        num = str(int(nnnn))
        return f"20{yy}-OT-{num}"
    return ot_coda

def obtener_ots_coda():
    if not CODA_API_KEY:
        print("  [!] CODA API KEY no configurada, no se cargarán OTs.")
        return []
    
    print("Conectando con Coda para cargar base de datos de OTs...")
    url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/grid-VHR5pyPjro/rows?valueFormat=simple&limit=250'
    req = urllib.request.Request(
        url,
        headers={'Authorization': 'Bearer ' + CODA_API_KEY}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ots = []
            for item in data.get('items', []):
                cells = item.get('values', {})
                ot = cells.get('c-pc5YuBXn96')
                if ot:
                    ots.append(ot)
            print(f"Se cargaron {len(ots)} OTs desde Coda.\n")
            return ots
    except Exception as e:
        print("  [!] Error al cargar OTs de Coda: " + str(e))
        return []

def obtener_columna_enlace_coda():
    if not CODA_API_KEY:
        return None
    print("Buscando columna de enlace de correo en Coda...")
    url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{CODA_TABLE_ID}/columns'
    req = urllib.request.Request(
        url,
        headers={'Authorization': 'Bearer ' + CODA_API_KEY}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get('items', []):
                nombre = item.get('name', '').lower()
                # Buscar coincidencias como "enlace correo", "link correo", "link del correo", "correo" (pero no "creado por" o "cuenta")
                # Excluir explícitamente "cuenta", "creado por", "tipo de movimiento" para evitar falsos positivos con "correo"
                if any(x in nombre for x in ["enlace", "link"]):
                    print(f"  [+] Detectada columna de enlace en Coda: '{item.get('name')}' (ID: {item.get('id')})")
                    return item.get('id')
                if "correo" in nombre and not any(x in nombre for x in ["creado", "cuenta", "proveedor"]):
                    print(f"  [+] Detectada columna de enlace en Coda: '{item.get('name')}' (ID: {item.get('id')})")
                    return item.get('id')
            print("  [-] No se detectó ninguna columna de enlace específica en Coda (se concatenará al concepto).")
            return None
    except Exception as e:
        print("  [!] Error al listar columnas de Coda: " + str(e))
        return None

def leer_ultima_ejecucion():
    if not os.path.exists(ULTIMA_EJECUCION):
        return None
    with open(ULTIMA_EJECUCION, 'r', encoding='utf-8') as f:
        c = f.read().strip()
    return c if c else None

def guardar_ultima_ejecucion(fecha_str=None):
    if not fecha_str:
        fecha_str = datetime.now(timezone.utc).strftime('%Y/%m/%d')
    else:
        try:
            # Parse, restar 1 dia para evitar problemas de granularidad y asegurar que no perdemos correos del mismo dia
            dt = datetime.strptime(fecha_str.replace('/', '-'), '%Y-%m-%d')
            fecha_str = (dt - timedelta(days=1)).strftime('%Y/%m/%d')
        except Exception:
            fecha_str = fecha_str.replace('-', '/')
    with open(ULTIMA_EJECUCION, 'w', encoding='utf-8') as f:
        f.write(fecha_str)

def autenticar():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Si falla por cambio de scopes u otro motivo, forzar flujo nuevo
                if os.path.exists(TOKEN):
                    try:
                        os.remove(TOKEN)
                    except Exception:
                        pass
                flow = InstalledAppFlow.from_client_secrets_file(CREDENCIALES, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENCIALES, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
    return creds

# ================================================================
#  PARSEO HTML → TEXTO LIMPIO
# ================================================================
def html_tabla_a_texto(html):
    html = re.sub(r'<head[^>]*>.*?</head>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<tr[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<t[dh][^>]*>', ' | ', html, flags=re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

def _decodificar_parte(part):
    data = part['body'].get('data', '')
    if not data:
        return ''
    raw = base64.urlsafe_b64decode(data)
    transfer_enc = ''
    for h in part.get('headers', []):
        if h['name'].lower() == 'content-transfer-encoding':
            transfer_enc = h['value'].lower()
    charset = 'utf-8'
    ct = next((h['value'] for h in part.get('headers', [])
               if h['name'].lower() == 'content-type'), '')
    m = re.search(r'charset=["\']?([\w-]+)', ct, re.IGNORECASE)
    if m:
        charset = m.group(1)
    if transfer_enc == 'quoted-printable':
        raw = quopri.decodestring(raw)
    return raw.decode(charset, errors='replace')

def obtener_texto(mensaje):
    textos_plain = []
    textos_html  = []

    def procesar(parts):
        for part in parts:
            mime = part.get('mimeType', '')
            if mime == 'text/plain':
                t = _decodificar_parte(part)
                if t.strip():
                    textos_plain.append(t)
            elif mime == 'text/html':
                h = _decodificar_parte(part)
                if h.strip():
                    textos_html.append(html_tabla_a_texto(h))
            elif 'multipart' in mime:
                procesar(part.get('parts', []))

    payload = mensaje['payload']
    if 'parts' in payload:
        procesar(payload['parts'])
    else:
        data = payload['body'].get('data', '')
        if data:
            raw = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            if '<html' in raw.lower() or '<body' in raw.lower():
                return html_tabla_a_texto(raw)
            return raw

    return '\n'.join(textos_plain) if textos_plain else '\n'.join(textos_html)

# ================================================================
#  GEMINI: EXTRACCION + CATEGORIZACION EN UNA SOLA LLAMADA
# ================================================================
PROMPT_TEMPLATE = """Eres un asistente financiero experto en Perú. Lee este correo bancario COMPLETO y responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown.

ENTIDADES DEL CLIENTE:
- H & V Desarrollo Y Fabricacion De Proyectos Metalmecanicos S.A.C. / INPROMETAL → codigo: HV_DESARROLLO
- Alma Culinaria S.A.C. / MUHU CAFETERIA → codigo: ALMA_CULINARIA
- Pedro Antonio Henriquez Sebastiano (persona natural) → codigo: PEDRO_HENRIQUEZ
- Sandra Magallanes (persona natural) → codigo: SANDRA_MAGALLANES

CATEGORÍAS Y SUBCATEGORÍAS VÁLIDAS:
{cats}

ÓRDENES DE TRABAJO (OT) VÁLIDAS:
{lista_ots}

REGLAS DE CATEGORIZACIÓN:
- Comisiones, intereses bancarios → Financiero / Comisiones Bancarias o Intereses y Cargos
- Transferencias entre cuentas propias → Financiero / Transferencia Interna
- EPPs, guantes, cascos, botas → Seguridad / EPPS
- Uniformes, ropa de trabajo → Seguridad / Uniformes
- Acero, plancha, tubo, perfil, varilla → Materiales e Insumos / Materiales Metalicos
- Discos de corte, electrodos, gas → Materiales e Insumos / Consumibles de Proceso
- Pernos, tuercas, remaches → Materiales e Insumos / Perneria y Fijaciones
- Pintura, anticorrosivo, thinner → Materiales e Insumos / Pinturas y Acabados
- Ferretería general → Materiales e Insumos / Ferreteria General
- Servicios externos, subcontrato → Operaciones / Servicios de Fabricacion Externa
- Transporte, flete, delivery → Operaciones / Logistica y Transporte
- Planilla, sueldo → Personal / Planilla
- Adelantos, préstamos a trabajadores → Personal / Adelantos y Prestamos
- Servicios básicos (luz, agua, internet) → Administracion / Servicios Basicos
- Honorarios, consultores → Administracion / Honorarios Profesionales
- Si el destinatario es persona desconocida sin concepto y monto < 1000 → Personal / Adelantos y Prestamos
- Revisa con especial atención el campo 'Mensaje' o 'Concepto' que figura en el correo, ya que ahí el usuario suele escribir la descripción real del gasto (ej. 'transporte', 'caballete', etc.). Usa esa información para clasificar la categoría y subcategoría adecuadas.
- Si el destinatario es una persona desconocida pero el correo contiene un concepto o mensaje indicando el tipo de gasto (ej. 'transporte', 'flete', 'compra de pernos', 'pintura', 'caballete', etc.), debes categorizarlo según dicho concepto y NO como 'Adelantos y Prestamos'.
- En operaciones de 'Pago de servicios' (como cuotas de préstamos, pago de luz, agua, telefonía, etc., donde figura una 'Empresa' y un 'Titular del servicio'), el destinatario real del pago debe ser obligatoriamente la 'Empresa' prestadora del servicio (ej. 'MIBANCO', 'ENEL', 'SEDAPAL') y NO el titular del servicio.
- Si no hay suficiente información → Otro / Otro con confianza 0.40

REGLAS PARA ORDEN DE TRABAJO (OT):
- Analiza el texto del correo, concepto, asunto o comentarios para identificar si menciona alguna Orden de Trabajo (OT).
- A veces se escribe de forma abreviada, ej: "OT 25", "OT25", "OT-25", "OT 0025", "OT025".
- Si se menciona "OT X" (ej. "OT 25") y la fecha del correo es del año 2026, esto corresponde a "OT-26-0025" de la lista de OTs válidas. Si es del año 2025, corresponde a "OT-25-0025".
- Si identificas una OT que corresponde a la lista de OTs válidas, escribe su código exacto en el campo "ot" (ej. "OT-26-0025").
- Si no hay ninguna OT en el correo o no coincide con la lista, escribe null en el campo "ot".

CONFIANZA:
- 0.85-1.00: categorización segura con datos claros
- 0.70-0.84: categorización probable, marcar para revisión
- < 0.70: categorización incierta, requiere revisión manual

FORMATO DE RESPUESTA (JSON exacto):
{{
  "banco": "BCP|BBVA|INTERBANK|DESCONOCIDO",
  "fecha": "YYYY-MM-DD",
  "monto": 0.00,
  "moneda": "Soles|Dolares",
  "titular": "nombre completo del dueño de la cuenta",
  "empresa_codigo": "HV_DESARROLLO|ALMA_CULINARIA|PEDRO_HENRIQUEZ|SANDRA_MAGALLANES|DESCONOCIDA",
  "destinatario": "nombre de quien recibió el pago",
  "concepto": "mensaje o descripción, null si no hay",
  "referencia": "número de operación",
  "canal": "movil|web|ventanilla|cajero|tarjeta|yape|plin|desconocido",
  "categoria": "categoria valida",
  "subcategoria": "subcategoria valida",
  "ot": "codigo exacto de la OT de la lista (ej: OT-26-0025) o null",
  "confianza": 0.00,
  "nota": "explicacion breve si confianza < 0.85 o null"
}}

FECHA DE ENVÍO DEL CORREO: {fecha_envio}
Nota importante sobre la fecha: Si el correo no especifica una fecha de operación distinta en el cuerpo del mensaje, la fecha de la transacción DEBE ser obligatoriamente la fecha de envío del correo ({fecha_envio}). No uses la fecha actual de hoy bajo ninguna circunstancia.

CORREO A PROCESAR:
{texto}"""

def _llamar_gemini(prompt):
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 8192,
            'responseMimeType': 'application/json'
        }
    }).encode('utf-8')
    
    max_intentos = 3
    for intento in range(1, max_intentos + 1):
        try:
            req = urllib.request.Request(
                GEMINI_URL, data=body,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except urllib.error.HTTPError as e:
            es_quota = e.code == 429 or '429' in str(e) or 'quota' in str(e).lower() or 'RESOURCE_EXHAUSTED' in str(e)
            if es_quota:
                if intento < max_intentos:
                    espera = 30 * intento
                    print(f'  [Intento {intento}/{max_intentos}] Cuota excedida. Esperando {espera} segundos...')
                    time.sleep(espera)
                    continue
                else:
                    print('  GEMINI QUOTA AGOTADA - correo marcado como MANUAL')
                    return None
            print('  GEMINI ERROR: ' + str(e))
            return None
        except Exception as e:
            es_quota = '429' in str(e) or 'quota' in str(e).lower() or 'RESOURCE_EXHAUSTED' in str(e)
            if es_quota:
                if intento < max_intentos:
                    espera = 30 * intento
                    print(f'  [Intento {intento}/{max_intentos}] Cuota excedida. Esperando {espera} segundos...')
                    time.sleep(espera)
                    continue
                else:
                    print('  GEMINI QUOTA AGOTADA - correo marcado como MANUAL')
                    return None
            print('  GEMINI ERROR: ' + str(e))
            return None
    return None

def _cats_texto(empresa_codigo):
    cats = CATEGORIAS_POR_EMPRESA.get(empresa_codigo, CATEGORIAS_POR_EMPRESA['HV_DESARROLLO'])
    return '\n'.join(f'  - {cat}: {chr(44).join(subs)}' for cat, subs in cats.items())

def procesar_con_gemini(texto, fecha_fallback, lista_ots, empresa_hint='HV_DESARROLLO'):
    """Una sola llamada Gemini: extrae datos + categoriza + confianza + OT."""
    if not GEMINI_API_KEY:
        return _resultado_vacio(fecha_fallback)

    texto_corto = texto[:3000]
    ots_str = ", ".join(lista_ots) if lista_ots else "Ninguna disponible"
    prompt = PROMPT_TEMPLATE.format(
        cats=_cats_texto(empresa_hint),
        lista_ots=ots_str,
        fecha_envio=fecha_fallback,
        texto=texto_corto
    )
    respuesta = _llamar_gemini(prompt)
    
    if not respuesta:
        return _resultado_vacio(fecha_fallback)

    # Limpiar posible markdown
    respuesta = re.sub(r'^```json\s*', '', respuesta, flags=re.MULTILINE)
    respuesta = re.sub(r'^```\s*', '', respuesta, flags=re.MULTILINE)
    respuesta = respuesta.strip()

    try:
        d = json.loads(respuesta)
    except Exception:
        # Intentar extraer JSON del texto
        m = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(0))
            except Exception:
                return _resultado_vacio(fecha_fallback)
        else:
            return _resultado_vacio(fecha_fallback)

    # Validar y normalizar
    if not d.get('fecha'):
        d['fecha'] = fecha_fallback
    d['monto'] = safe_float(d.get('monto', 0.0))
    confianza = safe_float(d.get('confianza', 0.5))
    d['confianza'] = confianza

    # Estado según confianza
    if confianza >= 0.85:
        d['estado'] = 'OK'
    elif confianza >= 0.70:
        d['estado'] = 'REVISAR'
    else:
        d['estado'] = 'MANUAL'

    # Validar categoria/subcategoria segun la empresa
    empresa_cats = CATEGORIAS_POR_EMPRESA.get(empresa_hint, CATEGORIAS_POR_EMPRESA['HV_DESARROLLO'])
    cat = d.get('categoria', 'Otro')
    sub = d.get('subcategoria', 'Otro')
    if cat not in empresa_cats:
        cat, sub = 'Otro', 'Otro'
    elif sub not in empresa_cats[cat]:
        sub = empresa_cats[cat][0]
    d['categoria']    = cat
    d['subcategoria'] = sub

    # OT
    d['ot'] = d.get('ot') if d.get('ot') in lista_ots else None

    return d

def _resultado_vacio(fecha_fallback):
    return {
        'banco': 'DESCONOCIDO', 'fecha': fecha_fallback, 'monto': 0.0,
        'moneda': 'Soles', 'titular': '', 'empresa_codigo': 'DESCONOCIDA',
        'destinatario': '', 'concepto': None, 'referencia': '',
        'canal': 'desconocido', 'categoria': 'Otro', 'subcategoria': 'Otro',
        'ot': None, 'confianza': 0.0, 'estado': 'MANUAL', 'nota': 'Sin respuesta de Gemini',
    }

# ================================================================
#  DETECCION DE TITULAR (backup si Gemini no lo detecta)
# ================================================================
def detectar_titular_fallback(texto, empresa_codigo_gemini):
    """Usa el resultado de Gemini si es válido, sino busca keywords en EMPRESAS."""
    if empresa_codigo_gemini in EMPRESAS:
        return empresa_codigo_gemini, True
    combined = texto[:600].lower()
    for clave, info in EMPRESAS.items():
        for alias in info['alias']:
            if alias in combined:
                return clave, True
    return 'NO IDENTIFICADO', False

def obtener_xml_attachment_id(service, msg):
    payload = msg.get('payload', {})
    parts = payload.get('parts', [])
    def search_xml(parts_list):
        for p in parts_list:
            mime = p.get('mimeType', '')
            filename = p.get('filename', '')
            body = p.get('body', {})
            att_id = body.get('attachmentId', '')
            if att_id and (mime == 'application/xml' or filename.lower().endswith('.xml')):
                if not filename.startswith('R-'):
                    return att_id
        for p in parts_list:
            mime = p.get('mimeType', '')
            filename = p.get('filename', '')
            body = p.get('body', {})
            att_id = body.get('attachmentId', '')
            if att_id and (mime == 'application/xml' or filename.lower().endswith('.xml')):
                return att_id
            if 'parts' in p:
                res = search_xml(p['parts'])
                if res:
                    return res
        return None
    return search_xml(parts)

def obtener_titular_de_xml(xml_text):
    start = xml_text.find('AccountingCustomerParty')
    if start == -1:
        return None
    sub = xml_text[start:start+2000]
    m = re.search(r'RegistrationName\s*>\s*(.*?)\s*<\s*/', sub)
    if not m:
        m = re.search(r'RegistrationName>(.*?)</', sub)
    if m:
        name = m.group(1).strip()
        name = name.replace('&amp;', '&')
        return name
    return None

def detectar_titular_completo(service, msg, texto, empresa_codigo_gemini):
    # 1. Intentar con el fallback normal (body/subject o Gemini)
    titular, es_explicito = detectar_titular_fallback(texto, empresa_codigo_gemini)
    if titular != 'NO IDENTIFICADO':
        return titular, es_explicito
        
    # 2. Si no se identificó, intentar buscar en la cabecera 'To' del correo
    try:
        headers = msg.get('payload', {}).get('headers', [])
        to_val = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
        if to_val:
            titular_to, _ = detectar_titular_fallback(to_val, '')
            if titular_to != 'NO IDENTIFICADO':
                print(f"  [+] Titular identificado mediante cabecera 'To': {titular_to} (Destinatario: '{to_val}')")
                return titular_to, True
    except Exception as e:
        print(f"  [!] Error al analizar cabecera 'To': {e}")

    # 3. Si sigue sin identificarse, intentar buscar en los adjuntos XML
    try:
        att_id = obtener_xml_attachment_id(service, msg)
        if att_id:
            att = service.users().messages().attachments().get(
                userId='me', messageId=msg['id'], id=att_id
            ).execute()
            data = att.get('data', '')
            if data:
                xml_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                reg_name = obtener_titular_de_xml(xml_text)
                if reg_name:
                    titular_xml, _ = detectar_titular_fallback(reg_name, '')
                    if titular_xml != 'NO IDENTIFICADO':
                        print(f"  [+] Titular identificado mediante XML adjunto: {titular_xml} (Cliente: '{reg_name}')")
                        return titular_xml, True
    except Exception as e:
        print(f"  [!] Error al analizar XML adjunto: {e}")
        
    return 'NO IDENTIFICADO', False

def crear_hoja_revisar(sheets_service, pendientes):
    """Crea/actualiza pestaña REVISAR con filas de baja confianza en Sheets."""
    nombre = 'REVISAR'
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        if nombre not in existing_sheets:
            body = {'requests': [{'addSheet': {'properties': {'title': nombre}}}]}
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    except Exception as e:
        print("  [!] Error al preparar pestaña REVISAR en Sheets: " + str(e))
        return

    # Limpiar contenido anterior
    try:
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{nombre}'!A:J"
        ).execute()
    except Exception as e:
        print("  [!] Error al limpiar pestaña REVISAR: " + str(e))

    # Escribir encabezados y filas
    enc = ['Fecha','Banco','Empresa','Monto','Destinatario','Concepto',
           'Categoria Propuesta','Subcategoria Propuesta','Confianza','Nota']
    values = [enc]
    for r in pendientes:
        values.append([
            r.get('fecha',''), r.get('banco',''), r.get('empresa',''),
            r.get('monto',0), r.get('destinatario',''), r.get('concepto','') or '',
            r.get('categoria',''), r.get('subcategoria',''),
            f"{int(safe_float(r.get('confianza',0))*100)}%", r.get('nota',''),
        ])
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{nombre}'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
    except Exception as e:
        print("  [!] Error al escribir pendientes en REVISAR: " + str(e))

def guardar_log(nuevos, duplicados, omitidos, pendientes, detalles_omitidos=None):
    log = os.path.join(CARPETA, 'procesamiento_log.txt')
    lineas = [
        f"\n{'='*50}",
        f"EJECUCION: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Nuevos: {nuevos} | Duplicados: {duplicados} | Omitidos: {omitidos} | Para revisar: {len(pendientes)}",
    ]
    for r in pendientes:
        lineas.append(f"  REVISAR: {r.get('monto')} | {r.get('destinatario')} | {int(safe_float(r.get('confianza',0))*100)}%")
    if detalles_omitidos:
        lineas.append("  Detalles de Omitidos:")
        for asu, mot in detalles_omitidos:
            lineas.append(f"    - {asu}: {mot}")
    with open(log, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lineas) + '\n')

# ================================================================
#  GOOGLE SHEETS DATABASE
# ================================================================
SHEETS_CACHE = {}

def cargar_datos_sheets(sheets_service):
    global SHEETS_CACHE
    print("Cargando datos existentes de Google Sheets para verificación de duplicados...")
    ranges = [f"'{nombre}'!A:Q" for nombre in HOJAS_CONFIG]
    try:
        res = sheets_service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID,
            ranges=ranges
        ).execute()
        value_ranges = res.get('valueRanges', [])
        for r, nombre in zip(value_ranges, HOJAS_CONFIG):
            SHEETS_CACHE[nombre] = r.get('values', [])
        print("Datos de Google Sheets cargados correctamente.")
    except Exception as e:
        print("  [!] Error al cargar datos de Google Sheets: " + str(e))
        for nombre in HOJAS_CONFIG:
            SHEETS_CACHE[nombre] = []

def preparar_google_sheets(sheets_service):
    print("Preparando estructura de Google Sheets...")
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets_info = spreadsheet.get('sheets', [])
        existing_sheets = [s['properties']['title'] for s in sheets_info]
    except Exception as e:
        print("  [!] Error al conectar con Google Sheets (verifica el SPREADSHEET_ID): " + str(e))
        raise e

    requests = []
    for nombre in HOJAS_CONFIG:
        if nombre not in existing_sheets:
            print(f"  Creando pestaña nueva: {nombre}")
            requests.append({
                'addSheet': {
                    'properties': {
                        'title': nombre
                    }
                  }
            })
    
    if requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        # Recargar hojas existentes
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets_info = spreadsheet.get('sheets', [])
        existing_sheets = [s['properties']['title'] for s in sheets_info]

    # Eliminar Hoja 1 o Sheet1 si existen y hay otras pestañas creadas
    default_names = ["Hoja 1", "Sheet1"]
    delete_requests = []
    for s in sheets_info:
        title = s['properties']['title']
        sheet_id = s['properties']['sheetId']
        if title in default_names and len(existing_sheets) > 1:
            print(f"  Eliminando pestaña por defecto vacía: {title}")
            delete_requests.append({'deleteSheet': {'sheetId': sheet_id}})
    
    if delete_requests:
        try:
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': delete_requests}
            ).execute()
        except Exception as e:
            print(f"  [!] No se pudo eliminar la pestaña por defecto: {e}")

    # Verificar / escribir encabezados en cada hoja
    for nombre in HOJAS_CONFIG:
        res = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{nombre}'!A1:Q1"
        ).execute()
        primera_fila = res.get('values', [])
        if not primera_fila or primera_fila[0] != ENCABEZADOS:
            print(f"  Escribiendo encabezados en: {nombre}")
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{nombre}'!A1",
                valueInputOption='USER_ENTERED',
                body={'values': [ENCABEZADOS]}
            ).execute()

def es_mensaje_duplicado(msg_id):
    if not msg_id:
        return False
    for values in SHEETS_CACHE.values():
        for row in values:
            if len(row) > 13 and str(row[13]) == str(msg_id):
                return True
    return False

def guardar_fila(sheets_service, d, titular, msg_id):
    confianza_pct = f"{int(safe_float(d.get('confianza', 0.0)) * 100)}%"
    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}" if msg_id else ""
    row_data = [
        d.get('fecha', ''),
        d.get('banco', ''),
        d.get('canal', ''),
        d.get('monto', 0),
        d.get('moneda', 'Soles'),
        d.get('titular', titular),
        d.get('destinatario', ''),
        d.get('concepto', '') or '',
        d.get('referencia', ''),
        d.get('categoria', ''),
        d.get('subcategoria', ''),
        confianza_pct,
        d.get('estado', ''),
        msg_id,
        d.get('nota', '') or '',
        d.get('ot') or '',
        gmail_link,
    ]
    try:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{titular}'!A:Q",
            valueInputOption='USER_ENTERED',
            body={'values': [row_data]}
        ).execute()
        if titular in SHEETS_CACHE:
            SHEETS_CACHE[titular].append(row_data)
    except Exception as e:
        print(f"  [!] Error al escribir en Google Sheets ({titular}): " + str(e))

def es_duplicado(titular, referencia):
    if not referencia or titular not in SHEETS_CACHE:
        return False
    for row in SHEETS_CACHE[titular]:
        if len(row) > 8 and str(row[8]) == str(referencia):
            return True
    return False

# ================================================================
#  CODA
# ================================================================
def mapear_cuenta_coda(banco, moneda):
    if banco == 'BBVA' and moneda == 'Dolares':
        return 'CTA CTE BBVA DOLARES'
    if banco == 'BBVA':
        return 'CTA CTE BBVA SOLES'
    if banco == 'BCP' and moneda == 'Dolares':
        return 'CTA CTE BCP DOLARES'
    return 'CTA CTE BCP SOLES'

def normalizar_subcategoria_coda(sub):
    sin_espacio = ['Capacitacion', 'EPPS', 'Uniformes', 'Planilla', 'Otro']
    return sub if sub in sin_espacio else sub + ' '

def enviar_a_coda(d, titular, es_explicito, msg_id):
    """Solo envía a Coda si es HV_DESARROLLO detectado explícitamente."""
    if titular != 'HV_DESARROLLO' or not es_explicito:
        return
    if not CODA_API_KEY:
        return

    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}" if msg_id else ""

    # Determinar concepto (si no hay columna de link, lo concatenamos al concepto)
    concepto_val = d.get('concepto', '') or ''
    if not CODA_LINK_COL and gmail_link:
        if concepto_val:
            concepto_val = f"{concepto_val} (Link: {gmail_link})"
        else:
            concepto_val = f"Link: {gmail_link}"

    monto = safe_float(d.get('monto', 0))
    cells = [
        {'column': CODA_COLS['fecha'],        'value': d.get('fecha', '')},
        {'column': CODA_COLS['concepto'],     'value': concepto_val},
        {'column': CODA_COLS['moneda'],       'value': d.get('moneda', 'Soles')},
        {'column': CODA_COLS['destinatario'], 'value': d.get('destinatario', '')},
        {'column': CODA_COLS['tipo'],         'value': 'GASTO'},
        {'column': CODA_COLS['cuenta'],       'value': mapear_cuenta_coda(d.get('banco','BCP'), d.get('moneda','Soles'))},
        {'column': CODA_COLS['cantidad'],     'value': 1},
        {'column': CODA_COLS['monto'],        'value': monto},
        {'column': CODA_COLS['categoria'],    'value': d.get('categoria', '')},
        {'column': CODA_COLS['subcategoria'], 'value': normalizar_subcategoria_coda(d.get('subcategoria', ''))},
    ]
    if d.get('ot'):
        cells.append({'column': 'c-VQAnY2FKEn', 'value': d.get('ot')})

    if CODA_LINK_COL and gmail_link:
        cells.append({'column': CODA_LINK_COL, 'value': gmail_link})

    body = json.dumps({
        'rows': [{
            'cells': cells
        }]
    }).encode('utf-8')

    url = 'https://coda.io/apis/v1/docs/' + CODA_DOC_ID + '/tables/' + CODA_TABLE_ID + '/rows'
    try:
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + CODA_API_KEY},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=10)
        print('  CODA OK')
        time.sleep(0.5)
    except Exception as e:
        print('  CODA ERROR: ' + str(e))

# ================================================================
#  MAIN
# ================================================================
def main():
    print('=' * 60)
    print('   EXTRACTOR DE GASTOS BANCARIOS - H&V  (v3 - Gemini AI)')
    print('=' * 60)
    print('  Gemini API : ' + ('OK (' + GEMINI_API_KEY[:8] + '...)' if GEMINI_API_KEY else 'NO CONFIGURADA'))
    print('  Coda API   : ' + ('OK (' + CODA_API_KEY[:8] + '...)' if CODA_API_KEY else 'NO CONFIGURADA'))
    print(f'  Max correos: {MAX_CORREOS} por ejecucion')
    print()

    ultima = leer_ultima_ejecucion()
    if ultima:
        print('Ultima ejecucion : ' + ultima)
        filtro_fecha = ' after:' + ultima
    else:
        print('Primera ejecucion - leyendo todos los correos')
        filtro_fecha = ''

    print('\nConectando con Gmail y Google Sheets...')
    creds = autenticar()
    service = build('gmail', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    print('Servicios de Google conectados\n')

    query = (
        'from:(notificacionesbcp OR viabcp OR bbva) '
        'subject:(transferencia OR pago OR comprobante OR constancia OR realizaste OR operacion OR consumo OR yape OR yapeaste) '
        '-"Clave de Internet" -"Estado de Cuenta" -"clave de internet" -"estado de cuenta"'
        + filtro_fecha
    )

    print('Buscando correos bancarios...')
    # Solicitamos cabeceras paginando para no perder el inicio del historico en carpetas saturadas
    mensajes = []
    page_token = None
    while True:
        resultados = service.users().messages().list(
            userId='me', q=query, maxResults=500, pageToken=page_token).execute()
        mensajes.extend(resultados.get('messages', []))
        page_token = resultados.get('nextPageToken')
        if not page_token or len(mensajes) >= 1000:  # Limite de seguridad de 1000 cabeceras
            break
            
    if mensajes:
        # Reversamos para procesar en orden cronológico (del más antiguo al más nuevo)
        mensajes.reverse()
        total_acumulado = len(mensajes)
        # Tomamos solo la primera tanda de MAX_CORREOS (los más antiguos de los nuevos)
        mensajes = mensajes[:MAX_CORREOS]
        print(f'Encontrados: {total_acumulado} correos acumulados. Procesando los {len(mensajes)} más antiguos en esta tanda.\n')
    else:
        print('No hay correos nuevos.')
        if '--non-interactive' not in sys.argv:
            input('\nPresiona Enter para cerrar...')
        return

    lista_ots = obtener_ots_coda()
    global CODA_LINK_COL
    CODA_LINK_COL = obtener_columna_enlace_coda()
    preparar_google_sheets(sheets_service)
    cargar_datos_sheets(sheets_service)
    nuevos = duplicados = omitidos = 0
    detalles_omitidos = []
    pendientes_revisar = []
    ultima_fecha_procesada = None

    for i, msg in enumerate(mensajes):
        try:
            # === VERIFICACION DE DUPLICADO PRE-GEMINI (Ahorro de cuota y red) ===
            if es_mensaje_duplicado(msg['id']):
                duplicados += 1
                continue

            mensaje = service.users().messages().get(
                userId='me', id=msg['id'], format='full').execute()
            headers = mensaje['payload'].get('headers', [])
            asunto  = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

            texto = obtener_texto(mensaje)
            if not texto.strip():
                omitidos += 1
                motivo = "Cuerpo del correo vacío"
                detalles_omitidos.append((asunto[:50], motivo))
                
                # Escribir en Sheets como OMITIDO
                internal_ms = int(mensaje.get('internalDate', 0))
                fecha_fallback = (datetime.fromtimestamp(internal_ms / 1000, tz=timezone.utc)
                                  .strftime('%Y-%m-%d') if internal_ms
                                  else datetime.now(timezone.utc).strftime('%Y-%m-%d'))
                ultima_fecha_procesada = fecha_fallback
                d_empty = {
                    'fecha': fecha_fallback, 'banco': 'DESCONOCIDO', 'canal': 'desconocido',
                    'monto': 0, 'moneda': 'Soles', 'titular': '', 'destinatario': '',
                    'concepto': 'Cuerpo del correo vacío', 'referencia': '',
                    'categoria': 'Otro', 'subcategoria': 'Otro', 'confianza': 0.0,
                    'estado': 'OMITIDO', 'nota': motivo, 'ot': None
                }
                guardar_fila(sheets_service, d_empty, 'NO IDENTIFICADO', msg['id'])
                continue

            # Fecha fallback desde Gmail internalDate
            internal_ms = int(mensaje.get('internalDate', 0))
            fecha_fallback = (datetime.fromtimestamp(internal_ms / 1000, tz=timezone.utc)
                              .strftime('%Y-%m-%d') if internal_ms
                              else datetime.now(timezone.utc).strftime('%Y-%m-%d'))
            ultima_fecha_procesada = fecha_fallback

            # Pre-deteccion de empresa para dar hint a Gemini
            empresa_hint, _ = detectar_titular_completo(service, mensaje, texto, '')

            # === GEMINI: extrae + categoriza con categorias de la empresa ===
            print(f'  [{i+1}/{len(mensajes)}] Procesando: ' + asunto[:40] + '...')
            texto_completo = f"ASUNTO: {asunto}\n\nCUERPO:\n{texto}"
            d = procesar_con_gemini(texto_completo, fecha_fallback, lista_ots, empresa_hint)

            monto_val = safe_float(d.get('monto', 0))
            confianza_val = safe_float(d.get('confianza', 0))
            
            if not d.get('monto') or monto_val <= 0:
                omitidos += 1
                if (d.get('banco') == 'DESCONOCIDO' and confianza_val == 0.0) or d.get('nota') == 'Sin respuesta de Gemini':
                    motivo = "Sin respuesta Gemini / Falla / Quota"
                    print(f'\n  [!] ERROR CRITICO DE GEMINI (msg_id: {msg["id"]}). Deteniendo ejecucion para reintentar en la siguiente corrida sin avanzar watermark.')
                    break
                elif d.get('nota'):
                    motivo = f"Nota Gemini: {d.get('nota')}"
                else:
                    motivo = "Monto <= 0 o vacio"
                detalles_omitidos.append((asunto[:50], motivo))
                print(f'  Omitido: {asunto[:40]} | Motivo: {motivo}')
                
                # Escribir en Sheets como OMITIDO
                d['estado'] = 'OMITIDO'
                d['nota'] = motivo
                titular, _ = detectar_titular_completo(service, mensaje, texto, d.get('empresa_codigo', ''))
                if not es_duplicado(titular, d.get('referencia', '')):
                    guardar_fila(sheets_service, d, titular, msg['id'])
                continue

            # Determinar titular definitivo
            titular, es_explicito = detectar_titular_completo(service, mensaje, texto, d.get('empresa_codigo', ''))

            # Verificar duplicado
            if es_duplicado(titular, d.get('referencia', '')):
                duplicados += 1
                continue

            estado = d.get('estado', 'MANUAL')

            if estado == 'MANUAL':
                # Baja confianza: registrar para revision, enviar a Coda igualmente
                pendientes_revisar.append({
                    'fecha': d.get('fecha',''), 'banco': d.get('banco',''),
                    'empresa': EMPRESAS[titular]['nombre_comercial'] if titular in EMPRESAS else titular,
                    'monto': d.get('monto',0), 'destinatario': d.get('destinatario',''),
                    'concepto': d.get('concepto',''), 'categoria': d.get('categoria',''),
                    'subcategoria': d.get('subcategoria',''),
                    'confianza': d.get('confianza',0), 'nota': d.get('nota',''),
                })
                guardar_fila(sheets_service, d, titular, msg['id'])
                enviar_a_coda(d, titular, es_explicito, msg['id'])
                nuevos += 1
                print(f'  [!] REVISAR [{titular}] S/ {d.get("monto","?")} | '
                      f'{d.get("categoria","?")} | {int(safe_float(d.get("confianza",0))*100)}%')
            else:
                guardar_fila(sheets_service, d, titular, msg['id'])
                enviar_a_coda(d, titular, es_explicito, msg['id'])
                nuevos += 1
                estado_icon = 'OK' if estado == 'OK' else 'REV'
                print(f'  [{estado_icon}] [{d.get("banco","?")}][{titular}] '
                      f'S/ {d.get("monto","?")} | {d.get("categoria","?")} > {d.get("subcategoria","?")} '
                      f'| {int(safe_float(d.get("confianza",0))*100)}% | {str(d.get("destinatario",""))[:20]}')

        except Exception as e:
            print('  ERROR: ' + str(e))
            continue

    # Crear/actualizar hoja REVISAR si hay pendientes
    if pendientes_revisar:
        crear_hoja_revisar(sheets_service, pendientes_revisar)

    if ultima_fecha_procesada:
        guardar_ultima_ejecucion(ultima_fecha_procesada)
    guardar_log(nuevos, duplicados, omitidos, pendientes_revisar, detalles_omitidos)

    print('\n' + '=' * 60)
    print('  COMPLETADO')
    print('  Nuevos      : ' + str(nuevos))
    print('  Duplicados  : ' + str(duplicados))
    print('  Omitidos    : ' + str(omitidos))
    print('  Para revisar: ' + str(len(pendientes_revisar)))
    print('  Google Sheet: ' + SPREADSHEET_ID)
    print('=' * 60)
    if '--non-interactive' not in sys.argv:
        input('\nPresiona Enter para cerrar...')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print('\n===== ERROR FATAL =====')
        traceback.print_exc()
        print('=======================')
        if '--non-interactive' not in sys.argv:
            input('\nPresiona Enter para cerrar...')
