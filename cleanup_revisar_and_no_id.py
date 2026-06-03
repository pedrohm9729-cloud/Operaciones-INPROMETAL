import os
import sys
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
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # 1. Move Row from NO IDENTIFICADO to SANDRA_MAGALLANES
    print("Moviendo fila de Sandra de NO IDENTIFICADO a SANDRA_MAGALLANES...")
    res_no_id = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="'NO IDENTIFICADO'!A:Q"
    ).execute()
    rows_no_id = res_no_id.get('values', [])
    
    target_row = None
    new_rows_no_id = []
    
    for r in rows_no_id:
        if len(r) > 13 and r[13] == '19c4f5387147b090':
            target_row = r
            print(f"  Fila encontrada: {r[:8]}")
        else:
            new_rows_no_id.append(r)
            
    if target_row:
        # Append to SANDRA_MAGALLANES
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="'SANDRA_MAGALLANES'!A:Q",
            valueInputOption='USER_ENTERED',
            body={'values': [target_row]}
        ).execute()
        print("  [+] Fila agregada a SANDRA_MAGALLANES.")
        
        # Update NO IDENTIFICADO (clearing first)
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range="'NO IDENTIFICADO'!A:Q"
        ).execute()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="'NO IDENTIFICADO'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': new_rows_no_id}
        ).execute()
        print("  [+] NO IDENTIFICADO actualizado.")
        
    # 2. Clean REVISAR sheet
    print("\nLimpiando pestaña REVISAR de filas duplicadas o cabeceras...")
    res_rev = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="'REVISAR'!A:J"
    ).execute()
    rows_rev = res_rev.get('values', [])
    
    cleaned_rev = []
    for r in rows_rev:
        # Skip literal header row written as data (if it matches headers in lower case)
        if len(r) > 0 and r[0].lower() == 'fecha' and r[1].lower() == 'banco' and len(cleaned_rev) > 0:
            print(f"  [-] Removiendo fila de cabecera duplicada: {r}")
            continue
        cleaned_rev.append(r)
        
    if len(cleaned_rev) != len(rows_rev):
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range="'REVISAR'!A:J"
        ).execute()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="'REVISAR'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': cleaned_rev}
        ).execute()
        print("  [+] REVISAR actualizado y limpio.")
        
    print("\nProceso completado!")

if __name__ == '__main__':
    main()
