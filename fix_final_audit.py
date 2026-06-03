import os
import sys
import base64
import json
import time

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = gastos_bancarios.SPREADSHEET_ID

def main():
    creds = gastos_bancarios.autenticar()
    service = build('gmail', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    lista_ots = gastos_bancarios.obtener_ots_coda()
    
    # 5 targets to fix
    targets = [
        {
            'sheet': 'HV_DESARROLLO',
            'row_index': 31,
            'msg_id': '19c6e2fdbe83d52f'
        },
        {
            'sheet': 'HV_DESARROLLO',
            'row_index': 59,
            'msg_id': '19cc6043a19f72af'
        },
        {
            'sheet': 'HV_DESARROLLO',
            'row_index': 65,
            'msg_id': '19cd36f00df9caae',
            'force_informative': True # 0.0 state of account
        },
        {
            'sheet': 'ALMA_CULINARIA',
            'row_index': 10,
            'msg_id': '19cf7ea739c3ff6d'
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
            # 1. Fetch email
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload'].get('headers', [])
            asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            texto = gastos_bancarios.obtener_texto(msg)
            
            internal_ms = int(msg.get('internalDate', 0))
            fecha_fallback = (time.strftime('%Y-%m-%d', time.gmtime(internal_ms / 1000.0)) if internal_ms 
                              else '2026-06-01')
            
            # Pre-detect owner for hints
            empresa_hint, _ = gastos_bancarios.detectar_titular_completo(service, msg, texto, '')
            
            # 2. Process with Gemini
            print("Llamando a Gemini...")
            texto_completo = f"ASUNTO: {asunto}\n\nCUERPO:\n{texto}"
            
            if t.get('force_informative'):
                # For the state of account, we can generate a clean informative record directly or query Gemini
                d = gastos_bancarios.procesar_con_gemini(texto_completo, fecha_fallback, lista_ots, empresa_hint)
                d['monto'] = 0.0
                d['estado'] = 'OK'
                d['nota'] = "Constancia de envío de estado de cuenta, operación no monetaria."
            else:
                d = gastos_bancarios.procesar_con_gemini(texto_completo, fecha_fallback, lista_ots, empresa_hint)
            
            monto_val = gastos_bancarios.safe_float(d.get('monto', 0))
            confianza_val = gastos_bancarios.safe_float(d.get('confianza', 0))
            
            if d.get('nota') == 'Sin respuesta de Gemini' or (not t.get('force_informative') and monto_val <= 0):
                print(f"[-] Gemini falló o retornó monto <= 0: {d}")
                continue
                
            titular, es_explicito = gastos_bancarios.detectar_titular_completo(service, msg, texto, d.get('empresa_codigo', ''))
            
            confianza_pct = f"{int(confianza_val * 100)}%"
            gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
            
            # Prepare row data
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
                d.get('categoria', ''),
                d.get('subcategoria', ''),
                confianza_pct,
                d.get('estado', 'OK'),
                msg_id,
                d.get('nota', '') or '',
                d.get('ot') or '',
                gmail_link
            ]
            
            print(f"Escribiendo en Google Sheets pestaña '{sheet}', fila {r_idx}...")
            print(f"  Datos: {row_data[:8]}...")
            
            # Update row in Google Sheets
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{sheet}'!A{r_idx}:Q{r_idx}",
                valueInputOption='USER_ENTERED',
                body={'values': [row_data]}
            ).execute()
            
            # Send to Coda if eligible
            if titular == 'HV_DESARROLLO' and not t.get('force_informative'):
                print("Enviando a Coda...")
                gastos_bancarios.enviar_a_coda(d, titular, es_explicito, msg_id)
                
            print("[+] Completado con éxito!")
            time.sleep(5) # Pause to avoid hitting rate limits
            
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == '__main__':
    main()
