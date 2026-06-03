import os
import sys
import base64
import json
import time
import re
import urllib.request
import urllib.error

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = gastos_bancarios.SPREADSHEET_ID

def llamar_gemini_directo(prompt):
    url = gastos_bancarios.GEMINI_URL
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 8192,
            'responseMimeType': 'application/json'
        }
    }).encode('utf-8')
    
    max_intentos = 5
    for intento in range(1, max_intentos + 1):
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_data = resp.read()
                data = json.loads(raw_data.decode('utf-8'))
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except urllib.error.HTTPError as e:
            print(f"  [Attempt {intento}/{max_intentos}] HTTPError: {e.code} - {e.reason}")
            if e.code == 429 or '429' in str(e) or 'quota' in str(e).lower():
                espera = 15 * intento
                print(f"  Rate limited. Sleeping {espera}s...")
                time.sleep(espera)
                continue
            else:
                try:
                    print("  Error body:", e.read().decode('utf-8'))
                except Exception:
                    pass
                return None
        except Exception as e:
            print(f"  [Attempt {intento}/{max_intentos}] Exception: {e}")
            time.sleep(5)
            continue
    return None

def main():
    creds = gastos_bancarios.autenticar()
    service = build('gmail', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    lista_ots = gastos_bancarios.obtener_ots_coda()
    
    targets = [
        {
            'sheet': 'HV_DESARROLLO',
            'row_index': 31,
            'msg_id': '19c6e2fdbe83d52f'
        },
        {
            'sheet': 'PEDRO_HENRIQUEZ',
            'row_index': 26,
            'msg_id': '19c69a7619ad3f95'
        }
    ]
    
    for t in targets:
        sheet = t['sheet']
        r_idx = t['row_index']
        msg_id = t['msg_id']
        
        print(f"\n================================ {sheet} | Row: {r_idx} | ID: {msg_id} ================================")
        try:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload'].get('headers', [])
            asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            texto = gastos_bancarios.obtener_texto(msg)
            
            internal_ms = int(msg.get('internalDate', 0))
            fecha_fallback = (time.strftime('%Y-%m-%d', time.gmtime(internal_ms / 1000.0)) if internal_ms 
                              else '2026-06-01')
            
            empresa_hint, _ = gastos_bancarios.detectar_titular_completo(service, msg, texto, '')
            
            texto_completo = f"ASUNTO: {asunto}\n\nCUERPO:\n{texto}"
            texto_corto = texto_completo[:3000]
            ots_str = ", ".join(lista_ots) if lista_ots else "Ninguna disponible"
            prompt = gastos_bancarios.PROMPT_TEMPLATE.format(
                cats=gastos_bancarios._cats_texto(empresa_hint),
                lista_ots=ots_str,
                fecha_envio=fecha_fallback,
                texto=texto_corto
            )
            
            print("Llamando a Gemini...")
            resp_text = llamar_gemini_directo(prompt)
            if not resp_text:
                print("[-] No se obtuvo respuesta de Gemini.")
                continue
                
            resp_text = re.sub(r'^```json\s*', '', resp_text, flags=re.MULTILINE)
            resp_text = re.sub(r'^```\s*', '', resp_text, flags=re.MULTILINE)
            resp_text = resp_text.strip()
            
            try:
                d = json.loads(resp_text)
            except Exception as je:
                print(f"[-] Error parsing JSON: {je}")
                m = re.search(r'\{.*\}', resp_text, re.DOTALL)
                if m:
                    try:
                        d = json.loads(m.group(0))
                    except Exception:
                        continue
                else:
                    continue
            
            monto_val = gastos_bancarios.safe_float(d.get('monto', 0))
            confianza_val = gastos_bancarios.safe_float(d.get('confianza', 0.5))
            
            # Normalize state
            if confianza_val >= 0.85:
                d['estado'] = 'OK'
            elif confianza_val >= 0.70:
                d['estado'] = 'REVISAR'
            else:
                d['estado'] = 'MANUAL'
                
            titular, es_explicito = gastos_bancarios.detectar_titular_completo(service, msg, texto, d.get('empresa_codigo', ''))
            
            confianza_pct = f"{int(confianza_val * 100)}%"
            gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
            
            row_data = [
                d.get('fecha', fecha_fallback),
                d.get('banco', 'DESCONOCIDO'),
                d.get('canal', 'desconocido'),
                monto_val,
                d.get('moneda', 'Soles'),
                titular,
                d.get('destinatario', ''),
                d.get('concepto', '') or '',
                d.get('referencia', ''),
                d.get('categoria', 'Otro'),
                d.get('subcategoria', 'Otro'),
                confianza_pct,
                d.get('estado', 'OK'),
                msg_id,
                d.get('nota', '') or '',
                d.get('ot') or '',
                gmail_link
            ]
            
            print(f"Escribiendo en Sheets pestaña '{sheet}', fila {r_idx}...")
            print(f"  Datos: {row_data[:8]}...")
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{sheet}'!A{r_idx}:Q{r_idx}",
                valueInputOption='USER_ENTERED',
                body={'values': [row_data]}
            ).execute()
            
            if titular == 'HV_DESARROLLO':
                print("Enviando a Coda...")
                gastos_bancarios.enviar_a_coda(d, titular, es_explicito, msg_id)
                
            print("[+] Completado con éxito!")
            time.sleep(5)
            
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == '__main__':
    main()
