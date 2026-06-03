import os
import sys
import base64
import json
import urllib.request
import urllib.error

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    creds = gastos_bancarios.autenticar()
    service = build('gmail', 'v1', credentials=creds)
    lista_ots = gastos_bancarios.obtener_ots_coda()
    
    mids = ['19c6e2fdbe83d52f', '19c69a7619ad3f95']
    for mid in mids:
        print(f"\nMESSAGE: {mid}")
        msg = service.users().messages().get(userId='me', id=mid, format='full').execute()
        headers = msg['payload'].get('headers', [])
        asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        texto = gastos_bancarios.obtener_texto(msg)
        
        empresa_hint, _ = gastos_bancarios.detectar_titular_completo(service, msg, texto, '')
        texto_completo = f"ASUNTO: {asunto}\n\nCUERPO:\n{texto}"
        prompt = gastos_bancarios.PROMPT_TEMPLATE.format(
            cats=gastos_bancarios._cats_texto(empresa_hint),
            lista_ots=", ".join(lista_ots),
            fecha_envio="2026-06-01",
            texto=texto_completo[:3000]
        )
        
        # Request
        body = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.1,
                'maxOutputTokens': 2048,
                'responseMimeType': 'application/json'
            }
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                gastos_bancarios.GEMINI_URL, data=body,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode('utf-8')
                print("RAW RESPONSE:")
                print(raw)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
