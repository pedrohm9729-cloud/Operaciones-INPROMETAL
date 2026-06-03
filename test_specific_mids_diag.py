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

def llamar_gemini_diagnostico(prompt):
    url = gastos_bancarios.GEMINI_URL
    print(f"Calling Gemini at URL: {url.split('key=')[0]}key=...")
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
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
            data = json.loads(raw_data.decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            print("SUCCESS! Raw response text:")
            print(text)
            return text
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        try:
            print("Error body:", e.read().decode('utf-8'))
        except Exception as re:
            print("Could not read error body:", re)
    except Exception as e:
        print(f"General Exception: {e}")
    return None

def main():
    creds = gastos_bancarios.autenticar()
    service = build('gmail', 'v1', credentials=creds)
    
    lista_ots = gastos_bancarios.obtener_ots_coda()
    
    failed_mids = [
        '19c6e2fdbe83d52f',
        '19cc6043a19f72af',
        '19cd36f00df9caae',
        '19cf7ea739c3ff6d',
        '19c69a7619ad3f95'
    ]
    
    for mid in failed_mids:
        print(f"\n================================ MESSAGE ID: {mid} ================================")
        try:
            msg = service.users().messages().get(userId='me', id=mid, format='full').execute()
            headers = msg['payload'].get('headers', [])
            asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            texto = gastos_bancarios.obtener_texto(msg)
            
            # Pre-detect owner for hints
            empresa_hint, _ = gastos_bancarios.detectar_titular_completo(service, msg, texto, '')
            print(f"Empresa Hint: {empresa_hint}")
            
            texto_completo = f"ASUNTO: {asunto}\n\nCUERPO:\n{texto}"
            texto_corto = texto_completo[:3000]
            ots_str = ", ".join(lista_ots) if lista_ots else "Ninguna disponible"
            prompt = gastos_bancarios.PROMPT_TEMPLATE.format(
                cats=gastos_bancarios._cats_texto(empresa_hint),
                lista_ots=ots_str,
                fecha_envio="2026-06-01",
                texto=texto_corto
            )
            
            print(f"Prompt length: {len(prompt)}")
            llamar_gemini_diagnostico(prompt)
            
        except Exception as e:
            print(f"Outer Error: {e}")

if __name__ == '__main__':
    main()
