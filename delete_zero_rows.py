import os
import sys
import json
import time

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = gastos_bancarios.SPREADSHEET_ID

def safe_float(val):
    try:
        return float(str(val).replace(',', ''))
    except Exception:
        return 0.0

def main():
    creds = gastos_bancarios.autenticar()
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # Get all sheets
    metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_names = [s['properties']['title'] for s in metadata.get('sheets', [])]
    
    for name in sheet_names:
        if name == 'REVISAR':
            continue
            
        print(f"\nLimpiando pestaña: {name}")
        res = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{name}'!A:Q"
        ).execute()
        rows = res.get('values', [])
        if len(rows) <= 1:
            print("  Pestaña vacía o solo encabezados.")
            continue
            
        header = rows[0]
        cleaned_rows = [header]
        removed_count = 0
        
        for r_idx, row in enumerate(rows[1:], start=2):
            if len(row) < 4:
                cleaned_rows.append(row)
                continue
                
            monto = safe_float(row[3])
            estado = row[12] if len(row) > 12 else ''
            concepto = row[7] if len(row) > 7 else ''
            
            # Identify non-monetary 0-amount rows to remove
            is_non_monetary_zero = (monto == 0.0 and (
                estado == 'OMITIDO' or 
                "clave de internet" in concepto.lower() or 
                "estado de cuenta" in concepto.lower() or 
                "clave" in concepto.lower()
            ))
            
            if is_non_monetary_zero:
                print(f"  [-] Removiendo fila {r_idx}: {concepto[:50]}")
                removed_count += 1
            else:
                cleaned_rows.append(row)
                
        if removed_count > 0:
            print(f"  -> Removidas {removed_count} filas. Actualizando pestaña en Sheets...")
            # Clear sheet contents first
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{name}'!A:Q"
            ).execute()
            
            # Update sheet with cleaned rows
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{name}'!A1",
                valueInputOption='USER_ENTERED',
                body={'values': cleaned_rows}
            ).execute()
            print("  [+] Pestaña actualizada con éxito!")
            time.sleep(2)
        else:
            print("  No se encontraron filas con monto 0 para remover.")

if __name__ == '__main__':
    main()
