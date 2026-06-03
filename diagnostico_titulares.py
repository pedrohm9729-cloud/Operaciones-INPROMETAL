"""
Script de diagnostico: lista asuntos y encabezado de cada correo bancario
para identificar como diferenciar titulares.
Corre este script y comparte el output.
"""
import os, base64, json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']
CARPETA      = os.path.join('C:', os.sep, 'GastosHV')
if not os.path.isdir(CARPETA):
    if '__file__' in globals():
        CARPETA = os.path.dirname(os.path.abspath(__file__))
    else:
        CARPETA = os.getcwd()
CREDENCIALES = os.path.join(CARPETA, 'credentials.json')
TOKEN        = os.path.join(CARPETA, 'token.json')

def autenticar():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENCIALES, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, 'w', encoding='utf-8') as t:
            t.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_text_snippet(mensaje):
    payload = mensaje['payload']
    # Intentar leer body directo
    data = payload.get('body', {}).get('data', '')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')[:400]
    # Intentar partes
    for part in payload.get('parts', []):
        if part.get('mimeType') == 'text/plain':
            d = part.get('body', {}).get('data', '')
            if d:
                return base64.urlsafe_b64decode(d).decode('utf-8', errors='replace')[:400]
    return ''

service = autenticar()
query = ('from:(notificacionesbcp OR viabcp OR bbva) '
         'subject:(transferencia OR pago OR comprobante OR constancia OR realizaste OR operacion OR consumo OR yape OR yapeaste)')

resultados = service.users().messages().list(userId='me', q=query, maxResults=80).execute()
mensajes   = resultados.get('messages', [])
print(f'Encontrados: {len(mensajes)} correos\n')
print('=' * 80)

vistos = set()
for msg in mensajes:
    mensaje = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
    headers = mensaje['payload'].get('headers', [])
    asunto  = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    to_hdr  = next((h['value'] for h in headers if h['name'] == 'To'), '')
    snippet = get_text_snippet(mensaje)

    # Mostrar solo asuntos unicos para no saturar
    clave = asunto[:60]
    if clave not in vistos:
        vistos.add(clave)
        # Extraer saludo (primera linea con "Hola")
        saludo = ''
        for linea in snippet.replace('\r', '').split('\n'):
            if 'hola' in linea.lower() or 'estimado' in linea.lower():
                saludo = linea.strip()[:100]
                break

        print(f'ASUNTO : {asunto[:70]}')
        print(f'TO     : {to_hdr[:60]}')
        print(f'SALUDO : {saludo}')
        print('-' * 80)

input('\nPresiona Enter para cerrar...')
